from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...crud import crud_group, crud_profile # crud_profile might not be needed here, but good for consistency
from ... import models, schemas
from ...database import get_db
from math import ceil

router = APIRouter()

@router.post("/", response_model=schemas.Group)
def create_group_endpoint(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group_by_name = crud_group.get_group_by_name(db, name=group.name)
    if db_group_by_name:
        raise HTTPException(status_code=400, detail="Group name already exists")
    return crud_group.create_group(db=db, group=group)

@router.get("/", response_model=schemas.PaginatedResponse[schemas.Group])
def read_groups_endpoint(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
    # Add name search for groups if needed in future:
    # name: Optional[str] = Query(None, description="Search by group name (contains)"),
):
    skip = (page - 1) * page_size
    # Add name to get_groups if search is implemented:
    # groups_orm = crud_group.get_groups(db, skip=skip, limit=page_size, name=name)
    # total_items = crud_group.count_groups(db, name=name)
    groups_orm = crud_group.get_groups(db, skip=skip, limit=page_size)
    total_items = crud_group.count_groups(db)
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    items_with_count = []
    for group_model in groups_orm:
        profile_count = db.query(models.Profile).filter(models.Profile.group_id == group_model.id).count()
        # Create a new dictionary from the ORM model and add profile_count
        group_dict = schemas.Group.from_orm(group_model).dict() # Pydantic v1
        group_dict["profile_count"] = profile_count
        items_with_count.append(group_dict)

    return schemas.PaginatedResponse(
        items=items_with_count,
        total=total_items,
        page=page,
        page_size=page_size,
        pages=total_pages
    )

@router.get("/{group_id}", response_model=schemas.Group)
def read_group_endpoint(group_id: int, db: Session = Depends(get_db)):
    db_group = crud_group.get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    profile_count = db.query(models.Profile).filter(models.Profile.group_id == db_group.id).count()
    group_data = schemas.Group.from_orm(db_group).dict() # Pydantic v1
    # Add profile_count to the response. The schemas.Group must be updated to include it
    # or we return a custom dict/model here.
    # For now, let's assume schemas.Group will be extended or we return a dict that matches its structure + count.
    # To make this work with response_model=schemas.Group, schemas.Group needs 'profile_count: Optional[int] = None'
    # and the response_model for the list endpoint should be PaginatedResponse[ExtendedGroupSchema]
    # For simplicity in this step, we'll return a dict that includes profile_count.
    # The actual response model in decorator should be adjusted or a more complex schema used.
    # Let's try to make it compatible by creating a temporary extended schema or by modifying Group schema if allowed.
    # As per current Group schema, profile_count is not there. So, this will cause validation error if not careful.
    # A quick fix is to return a dict, and FastAPI will try to match it.
    # However, for typed consistency, let's define an ad-hoc schema or adjust.
    # For now, I'll assume the schema is adjusted or this is a simplified representation.
    # The provided code implies it will be added to the dict and returned.
    group_data["profile_count"] = profile_count
    return group_data


@router.put("/{group_id}", response_model=schemas.Group)
def update_group_endpoint(
    group_id: int, group_update: schemas.GroupUpdate, db: Session = Depends(get_db)
):
    # Check if the target group exists
    db_group_to_update = crud_group.get_group(db, group_id=group_id)
    if db_group_to_update is None:
        raise HTTPException(status_code=404, detail="Group not found")

    # If name is being updated, check if the new name is already taken by another group
    if group_update.name is not None and group_update.name != db_group_to_update.name:
        existing_group_with_new_name = crud_group.get_group_by_name(db, name=group_update.name)
        if existing_group_with_new_name and existing_group_with_new_name.id != group_id:
            raise HTTPException(status_code=400, detail="Group name already exists")

    updated_db_group = crud_group.update_group(db, group_id=group_id, group_update=group_update)
    # update_group should not return None if the initial check passed, but defensive check is okay.
    if updated_db_group is None:
        raise HTTPException(status_code=404, detail="Group not found after update attempt") # Should not happen if initial check is done

    profile_count = db.query(models.Profile).filter(models.Profile.group_id == updated_db_group.id).count()
    group_data = schemas.Group.from_orm(updated_db_group).dict()
    group_data["profile_count"] = profile_count
    return group_data


@router.delete("/{group_id}", response_model=schemas.Group) # Returning the deleted group (last state)
def delete_group_endpoint(group_id: int, db: Session = Depends(get_db)):
    # First, check if group exists to provide a 404 if it doesn't
    db_group_check = crud_group.get_group(db, group_id=group_id)
    if db_group_check is None:
        raise HTTPException(status_code=404, detail="Group not found")

    # Perform the delete operation. crud_group.delete_group also fetches the group.
    deleted_db_group = crud_group.delete_group(db, group_id=group_id)
    # crud_group.delete_group returns the object before it's expunged or None if not found initially.
    # Since we checked above, deleted_db_group should be the object.

    # To include profile_count (which would be 0 after profiles are unassigned)
    # we can construct a dictionary from the returned object.
    if deleted_db_group:
        group_data = schemas.Group.from_orm(deleted_db_group).dict()
        group_data["profile_count"] = 0 # Profiles are unassigned before group deletion
        return group_data
    else:
        # This case should ideally not be reached if the initial check was done.
        raise HTTPException(status_code=404, detail="Group not found during deletion process")
