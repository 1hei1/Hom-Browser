from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas # Changed

def get_group(db: Session, group_id: int) -> Optional[models.Group]:
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_group_by_name(db: Session, name: str) -> Optional[models.Group]:
    return db.query(models.Group).filter(models.Group.name == name).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100) -> List[models.Group]:
    return db.query(models.Group).order_by(models.Group.name).offset(skip).limit(limit).all()

def count_groups(db: Session) -> int:
    return db.query(models.Group).count()

def create_group(db: Session, group: schemas.GroupCreate) -> models.Group:
    db_group = models.Group(name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def update_group(db: Session, group_id: int, group_update: schemas.GroupUpdate) -> Optional[models.Group]:
    db_group = get_group(db, group_id)
    if not db_group:
        return None

    update_data = group_update.model_dump(exclude_unset=True) # Pydantic v2

    if 'name' in update_data and update_data['name'] != db_group.name:
        # Check if new name already exists for another group
        existing_group_with_new_name = get_group_by_name(db, update_data['name'])
        if existing_group_with_new_name and existing_group_with_new_name.id != group_id:
            # This condition should be handled by the endpoint to raise HTTPException
            # For now, crud returns the group, endpoint should check.
            # Or, this function could raise a specific exception.
            # Let's assume endpoint handles the HTTP exception for clarity.
             pass # The endpoint will check this and raise HTTP 400
        db_group.name = update_data['name']

    # Only commit if there are changes to commit, though SQLAlchemy handles no-op commits fine.
    # db.add(db_group) # Not strictly necessary if only changing attributes on an existing object
    db.commit()
    db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int) -> Optional[models.Group]:
    db_group = get_group(db, group_id)
    if not db_group:
        return None

    # Unassign profiles from this group before deleting
    # This ensures foreign key constraints are respected if on_delete='SET NULL' is not used,
    # or simply good practice.
    db.query(models.Profile).filter(models.Profile.group_id == group_id).update({"group_id": None}, synchronize_session='fetch')

    db.delete(db_group)
    db.commit()
    # The db_group object becomes detached after deletion.
    # Returning it is fine for its data, but it's no longer in the session.
    return db_group
