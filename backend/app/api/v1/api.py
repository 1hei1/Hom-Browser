from fastapi import APIRouter
from app.api.v1.endpoints import profiles, groups, proxies, plugins # Changed

api_router = APIRouter()
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(proxies.router, prefix="/proxies", tags=["proxies"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"]) # Add plugins router
# Other routers for etc. will be added here
