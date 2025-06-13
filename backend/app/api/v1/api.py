from fastapi import APIRouter
from .endpoints import profiles, groups # Add groups

api_router = APIRouter()
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"]) # Add groups router
# Other routers for proxies, plugins, etc. will be added here
