from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.crud import crud_proxy
from app import models, schemas
from app.database import get_db
from math import ceil

router = APIRouter()

@router.post("", response_model=schemas.Proxy) # Changed path from "/" to ""
def create_proxy_endpoint(proxy: schemas.ProxyCreate, db: Session = Depends(get_db)):
    # One might add a check here:
    # existing_proxy = db.query(models.Proxy).filter(models.Proxy.host == proxy.host, models.Proxy.port == proxy.port, models.Proxy.type == proxy.type).first()
    # if existing_proxy:
    #     raise HTTPException(status_code=400, detail="Proxy with this host, port, and type already exists")
    return crud_proxy.create_proxy(db=db, proxy=proxy)

@router.get("", response_model=schemas.PaginatedResponse[schemas.Proxy]) # Changed path from "/" to ""
def read_proxies_endpoint(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=1000, description="Items per page"), # Changed le to 1000
    search: Optional[str] = Query(None, description="Search by proxy name, host, or type")
):
    skip = (page - 1) * page_size
    proxies_orm = crud_proxy.get_proxies(db, skip=skip, limit=page_size, search=search)
    total_items = crud_proxy.count_proxies(db, search=search)
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    items_with_count = []
    for proxy_model in proxies_orm:
        usage_count = crud_proxy.get_proxy_usage_count(db, proxy_id=proxy_model.id)
        proxy_dict = schemas.Proxy.from_orm(proxy_model).model_dump() # Pydantic v2
        proxy_dict['usage_count'] = usage_count
        items_with_count.append(proxy_dict)

    return schemas.PaginatedResponse(
        items=items_with_count,
        total=total_items,
        page=page,
        page_size=page_size,
        pages=total_pages
    )

@router.get("/{proxy_id}", response_model=schemas.Proxy)
def read_proxy_endpoint(proxy_id: int, db: Session = Depends(get_db)):
    db_proxy = crud_proxy.get_proxy(db, proxy_id=proxy_id)
    if db_proxy is None:
        raise HTTPException(status_code=404, detail="Proxy not found")

    proxy_data = schemas.Proxy.from_orm(db_proxy).model_dump() # Pydantic v2
    proxy_data['usage_count'] = crud_proxy.get_proxy_usage_count(db, proxy_id=proxy_id)
    return proxy_data

@router.put("/{proxy_id}", response_model=schemas.Proxy)
def update_proxy_endpoint(
    proxy_id: int, proxy_update: schemas.ProxyUpdate, db: Session = Depends(get_db)
):
    # Check if proxy exists first
    existing_proxy = crud_proxy.get_proxy(db, proxy_id=proxy_id)
    if not existing_proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    # Optional: Check for duplicate proxy if critical fields (host, port, type) are updated
    # This would be more complex as proxy_update can be partial.
    # For now, assuming direct update or DB unique constraints handle this.

    updated_db_proxy = crud_proxy.update_proxy(db, proxy_id=proxy_id, proxy_update=proxy_update)
    # crud_proxy.update_proxy should not return None if the initial check passed.
    if updated_db_proxy is None:
        raise HTTPException(status_code=404, detail="Proxy not found after update attempt")

    proxy_data = schemas.Proxy.from_orm(updated_db_proxy).model_dump() # Pydantic v2
    proxy_data['usage_count'] = crud_proxy.get_proxy_usage_count(db, proxy_id=proxy_id) # Use original proxy_id
    return proxy_data

@router.delete("/{proxy_id}", response_model=schemas.Proxy)
def delete_proxy_endpoint(proxy_id: int, db: Session = Depends(get_db)):
    # Check if proxy exists first
    db_proxy_check = crud_proxy.get_proxy(db, proxy_id=proxy_id)
    if db_proxy_check is None:
        raise HTTPException(status_code=404, detail="Proxy not found")

    usage_count = crud_proxy.get_proxy_usage_count(db, proxy_id=proxy_id)
    if usage_count > 0:
        raise HTTPException(status_code=409, detail=f"Proxy is currently used by {usage_count} profile(s) and cannot be deleted. Please unassign it first.")

    deleted_db_proxy = crud_proxy.delete_proxy(db, proxy_id=proxy_id)
    # crud_proxy.delete_proxy returns the object before it's expunged.
    if deleted_db_proxy is None: # Should not happen if initial check passed
         raise HTTPException(status_code=404, detail="Proxy became not found during deletion")

    proxy_data = schemas.Proxy.from_orm(deleted_db_proxy).model_dump() # Pydantic v2
    proxy_data['usage_count'] = 0 # Since it's deleted, usage is effectively 0 for this response
    return proxy_data


@router.post("/batch-delete", summary="Batch delete proxies", response_model=schemas.BatchDeleteResponse) # Added response_model
async def batch_delete_proxies_endpoint(payload: schemas.BatchDeletePayload, db: Session = Depends(get_db)):
    deleted_count = 0
    errors = []
    for proxy_id in payload.ids:
        proxy_to_check = crud_proxy.get_proxy(db, proxy_id=proxy_id)
        if not proxy_to_check:
            errors.append({'id': proxy_id, 'error': 'Proxy not found.'})
            continue # Skip to next ID

        usage_count = crud_proxy.get_proxy_usage_count(db, proxy_id=proxy_id)
        if usage_count > 0:
            errors.append({'id': proxy_id, 'error': f'Proxy is used by {usage_count} profile(s).'})
            continue

        deleted_proxy = crud_proxy.delete_proxy(db, proxy_id=proxy_id)
        if deleted_proxy:
            deleted_count += 1
        # No else needed here for 'not found' as it's checked above

    return schemas.BatchDeleteResponse(
        message=f"Batch delete operation completed. {deleted_count} proxies deleted.",
        deleted_count=deleted_count,
        errors=errors
    )
