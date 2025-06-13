from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from app import models
from app.database import engine
from app.api.v1.api import api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="homBrowser API",
    description="API for managing homBrowser profiles and fingerprinting.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json"
)

# CORS Middleware Configuration
origins = [
    "http://localhost",         # Common base for localhost
    "http://localhost:5173",    # Default Vite dev server port (used by this project's frontend)
    "http://localhost:5174",    # Another common Vite port
    "http://localhost:3000",    # Common React dev server port (just in case for other projects)
    # Add other origins if needed, e.g., your production frontend URL when deployed
    # "https://your.production.frontend.domain",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True, # Allows cookies to be included in requests (important for auth later)
    allow_methods=["*"],    # Allows all standard methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],    # Allows all headers (e.g., Content-Type, Authorization)
)

@app.get("/")
async def root():
    return {"message": "Welcome to homBrowser Backend"}

app.include_router(api_router, prefix="/api/v1")
