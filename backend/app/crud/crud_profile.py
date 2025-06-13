from sqlalchemy.orm import Session
from .. import models
from .. import schemas # Explicit import
from fastapi import HTTPException
from typing import List, Optional, Type, TypeVar
from pydantic import BaseModel
# from ..models import Profile # Already available via models.Profile

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

def get_profile(db: Session, profile_id: int) -> Optional[models.Profile]:
    return db.query(models.Profile).filter(models.Profile.id == profile_id).first()

def get_profiles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    group_id: Optional[int] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = 'desc'
) -> List[models.Profile]:
    query = db.query(models.Profile)

    if group_id is not None:
        query = query.filter(models.Profile.group_id == group_id)
    if name:
        query = query.filter(models.Profile.name.contains(name))

    if sort_by:
        column = getattr(models.Profile, sort_by, None)
        if column:
            if sort_order == 'asc':
                query = query.order_by(column.asc())
            else:
                query = query.order_by(column.desc())
        else:
            # Default sort if sort_by is invalid
            query = query.order_by(models.Profile.created_at.desc())
    else:
        query = query.order_by(models.Profile.created_at.desc())

    return query.offset(skip).limit(limit).all()

def count_profiles(
    db: Session,
    group_id: Optional[int] = None,
    name: Optional[str] = None
) -> int:
    query = db.query(models.Profile)
    if group_id is not None:
        query = query.filter(models.Profile.group_id == group_id)
    if name:
        query = query.filter(models.Profile.name.contains(name))
    return query.count()

def create_profile(db: Session, profile: schemas.ProfileCreate) -> models.Profile:
    db_profile = models.Profile(**profile.dict()) # Pydantic v1
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile(db: Session, profile_id: int, profile_update: schemas.ProfileUpdate) -> Optional[models.Profile]:
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None

    update_data = profile_update.dict(exclude_unset=True) # Pydantic v1
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def delete_profile(db: Session, profile_id: int) -> Optional[models.Profile]:
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None
    db.delete(db_profile)
    db.commit()
    return db_profile
