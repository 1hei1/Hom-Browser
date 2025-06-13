from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..crud import crud_profile # Corrected import
from .. import models, schemas # Corrected import
from ..database import get_db # Corrected import
from math import ceil

router = APIRouter()

@router.post("/", response_model=schemas.Profile)
def create_profile_endpoint(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    # Check for duplicate name if necessary, or handle DB unique constraint error
    # db_profile_by_name = db.query(models.Profile).filter(models.Profile.name == profile.name).first()
    # if db_profile_by_name:
    #     raise HTTPException(status_code=400, detail="Profile name already registered")
    return crud_profile.create_profile(db=db, profile=profile)

@router.get("/", response_model=schemas.PaginatedResponse[schemas.ProfileSimple])
def read_profiles_endpoint(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    name: Optional[str] = Query(None, description="Search by profile name (contains)"),
    sort_by: Optional[str] = Query('created_at', description="Field to sort by (e.g., 'name', 'created_at', 'last_launch_time')"),
    sort_order: Optional[str] = Query('desc', description="Sort order ('asc' or 'desc')")
):
    skip = (page - 1) * page_size
    profiles_orm = crud_profile.get_profiles(db, skip=skip, limit=page_size, group_id=group_id, name=name, sort_by=sort_by, sort_order=sort_order)
    total_items = crud_profile.count_profiles(db, group_id=group_id, name=name)
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    # Convert ORM objects to Pydantic schemas for the response
    profiles_simple = [schemas.ProfileSimple.from_orm(p) for p in profiles_orm]

    return schemas.PaginatedResponse(
        items=profiles_simple,
        total=total_items,
        page=page,
        page_size=page_size,
        pages=total_pages
    )

@router.get("/{profile_id}", response_model=schemas.Profile)
def read_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    db_profile = crud_profile.get_profile(db, profile_id=profile_id)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile

@router.put("/{profile_id}", response_model=schemas.Profile)
def update_profile_endpoint(
    profile_id: int, profile_update: schemas.ProfileUpdate, db: Session = Depends(get_db)
):
    db_profile = crud_profile.update_profile(db, profile_id=profile_id, profile_update=profile_update)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile

@router.delete("/{profile_id}", response_model=schemas.Profile)
def delete_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    db_profile = crud_profile.delete_profile(db, profile_id=profile_id)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile

@router.post("/batch", summary="Batch operations on profiles", response_model=dict)
async def batch_update_profiles_endpoint():
    raise HTTPException(status_code=501, detail="Batch operations not yet implemented")

@router.post("/{profile_id}/launch", response_model=schemas.ProfileLaunchResponse, summary="Launch a browser profile")
async def launch_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    db_profile = crud_profile.get_profile(db, profile_id=profile_id)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    raise HTTPException(status_code=501, detail="Launch functionality not yet implemented")
