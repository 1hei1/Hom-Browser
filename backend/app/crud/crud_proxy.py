from sqlalchemy.orm import Session, joinedload # joinedload is not used here currently
from typing import List, Optional
from app import models, schemas # Changed
from sqlalchemy import or_

def get_proxy(db: Session, proxy_id: int) -> Optional[models.Proxy]:
    return db.query(models.Proxy).filter(models.Proxy.id == proxy_id).first()

def get_proxies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[models.Proxy]:
    query = db.query(models.Proxy)
    if search:
        search_term = f"%{search}%"
        # Using or_ for case-insensitive search on multiple fields
        query = query.filter(
            or_(
                models.Proxy.name.ilike(search_term),
                models.Proxy.host.ilike(search_term),
                models.Proxy.type.ilike(search_term) # Added type to search
            )
        )
    # Consider adding a default sort order, e.g., by creation date or name
    return query.order_by(models.Proxy.created_at.desc()).offset(skip).limit(limit).all()

def count_proxies(db: Session, search: Optional[str] = None) -> int:
    query = db.query(models.Proxy.id) # Querying for ID is enough for count
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Proxy.name.ilike(search_term),
                models.Proxy.host.ilike(search_term),
                models.Proxy.type.ilike(search_term)
            )
        )
    return query.count()

def create_proxy(db: Session, proxy: schemas.ProxyCreate) -> models.Proxy:
    db_proxy = models.Proxy(**proxy.dict()) # Pydantic v1
    db.add(db_proxy)
    db.commit()
    db.refresh(db_proxy)
    return db_proxy

def update_proxy(db: Session, proxy_id: int, proxy_update: schemas.ProxyUpdate) -> Optional[models.Proxy]:
    db_proxy = get_proxy(db, proxy_id)
    if not db_proxy:
        return None

    update_data = proxy_update.dict(exclude_unset=True) # Pydantic v1
    for key, value in update_data.items():
        setattr(db_proxy, key, value)

    # db.add(db_proxy) # Not strictly necessary for updates on existing objects
    db.commit()
    db.refresh(db_proxy)
    return db_proxy

def delete_proxy(db: Session, proxy_id: int) -> Optional[models.Proxy]:
    db_proxy = get_proxy(db, proxy_id)
    if not db_proxy:
        return None

    # Deletion logic is handled by the endpoint, including usage checks.
    # If we reach here, it's assumed safe to delete or the check failed and this won't be called.

    db.delete(db_proxy)
    db.commit()
    return db_proxy # Returns the object's last state

def get_proxy_usage_count(db: Session, proxy_id: int) -> int:
    return db.query(models.Profile).filter(models.Profile.custom_proxy_id == proxy_id).count()
