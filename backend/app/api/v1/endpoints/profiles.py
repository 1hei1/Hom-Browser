from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.crud import crud_profile
from app import models, schemas
from app.database import get_db
from math import ceil
import subprocess # For actual launching (later, for now just generate command)
import os # For environment variables
import shlex # For quoting command string for display
from datetime import datetime, timezone as dt_timezone # Ensure timezone aware for last_launch_time

router = APIRouter()

@router.post("/", response_model=schemas.Profile)
def create_profile_endpoint(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    # Potential: Check for duplicate name if necessary, or handle DB unique constraint error
    # existing_profile = db.query(models.Profile).filter(models.Profile.name == profile.name).first()
    # if existing_profile:
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
    db_profile = crud_profile.get_profile(db, profile_id=profile_id) # This now joinedloads custom_proxy
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update last_launch_time
    db_profile.last_launch_time = datetime.now(dt_timezone.utc)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    # Determine Chromium executable path
    # Priority: Environment Variable -> Default from crud_profile -> Developer fallback
    chromium_path_env = os.getenv("FINGERPRINT_CHROMIUM_PATH")
    chromium_path_crud_default = crud_profile.CHROMIUM_EXECUTABLE_PATH # Access the default from crud module

    chromium_path_to_use = chromium_path_env or chromium_path_crud_default

    if not os.path.exists(chromium_path_to_use) or not os.path.isfile(chromium_path_to_use):
        # Try a common relative path for development if the primary path fails
        # Assumes backend/main.py is the execution root for this relative path.
        # For a packaged app, this path needs to be more robust (e.g., using importlib.resources or similar)
        dev_fallback_path = os.path.join(os.getcwd(), "fingerprint-chromium", "chrome") # Example

        # Check if fingerprint-chromium directory exists in CWD (useful for local dev)
        local_fingerprint_chromium_dir = os.path.join(os.getcwd(), "fingerprint-chromium")
        if os.path.isdir(local_fingerprint_chromium_dir):
            # Try to find 'chrome' or 'fingerprint-chromium' executable inside it
            possible_executables = ["chrome", "fingerprint-chromium", "chromium"]
            for exec_name in possible_executables:
                potential_path = os.path.join(local_fingerprint_chromium_dir, exec_name)
                if os.path.exists(potential_path) and os.path.isfile(potential_path) and os.access(potential_path, os.X_OK):
                    chromium_path_to_use = potential_path
                    break
            else: # If loop finishes without finding an executable
                 return schemas.ProfileLaunchResponse(
                    message=f"Chromium executable not found in {local_fingerprint_chromium_dir} or configured path: {chromium_path_to_use}. Searched for {possible_executables}.",
                    profile_id=profile_id,
                    command=None
                )
        elif not (os.path.exists(chromium_path_to_use) and os.path.isfile(chromium_path_to_use)):
             return schemas.ProfileLaunchResponse(
                message=f"Chromium executable not found at configured path: {chromium_path_to_use}. Environment FINGERPRINT_CHROMIUM_PATH is not set or path is invalid. Default path in code is also invalid.",
                profile_id=profile_id,
                command=None
            )


    command_args = crud_profile.generate_chromium_command(db_profile, chromium_executable_path=chromium_path_to_use)
    command_str = ' '.join(shlex.quote(str(arg)) for arg in command_args)

    # Actual subprocess call (example, would need error handling, process management)
    # try:
    #     print(f"Attempting to launch: {command_args}")
    #     process = subprocess.Popen(command_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    #     return schemas.ProfileLaunchResponse(
    #         message=f"Browser for profile '{db_profile.name}' launched successfully with PID {process.pid}.",
    #         profile_id=profile_id,
    #         command=command_str
    #     )
    # except FileNotFoundError:
    #      return schemas.ProfileLaunchResponse(
    #         message=f"Chromium executable not found at effective path: {chromium_path_to_use}. Launch failed.",
    #         profile_id=profile_id,
    #         command=command_str
    #     )
    # except Exception as e:
    #     # Log the full error server-side
    #     print(f"Error launching browser for profile {profile_id}: {e}\nCommand: {command_str}")
    #     raise HTTPException(status_code=500, detail=f"Failed to launch browser: {str(e)}")

    print(f"Generated command for profile {profile_id}: {command_str}") # Log for server console
    return schemas.ProfileLaunchResponse(
        message=f"Browser launch command for profile '{db_profile.name}' generated. (Actual launch disabled in this version)",
        profile_id=profile_id,
        command=command_str
    )
