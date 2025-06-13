from fastapi import FastAPI
from app import models # Corrected import path from previous step
from app.database import engine # Corrected import path from previous step
from app.api.v1.api import api_router # New import

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="homBrowser API",
    description="API for managing homBrowser profiles and fingerprinting.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json" # Set OpenAPI URL
)

@app.get("/")
async def root():
    return {"message": "Welcome to homBrowser Backend"}

app.include_router(api_router, prefix="/api/v1") # Include the v1 router
