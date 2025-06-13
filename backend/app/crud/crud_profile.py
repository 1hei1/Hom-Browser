from sqlalchemy.orm import Session, joinedload
from .. import models, schemas
from fastapi import HTTPException
from typing import List, Optional, Type, TypeVar, Dict, Any # Added Dict, Any
from pydantic import BaseModel
import shlex # For safe command line argument construction
import os # For user_data_dir path construction

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Default path, should be configurable in a real app via environment variables or config file
CHROMIUM_EXECUTABLE_PATH = os.getenv("FINGERPRINT_CHROMIUM_PATH", "/path/to/fingerprint-chromium") # Example default
# Base directory for user data dirs, should be configurable
USER_DATA_ROOT_DIR = os.getenv("HOM_BROWSER_USER_DATA_ROOT", "./hom_browser_data/user_data_dirs")


def get_profile(db: Session, profile_id: int) -> Optional[models.Profile]:
    return db.query(models.Profile).options(joinedload(models.Profile.custom_proxy)).filter(models.Profile.id == profile_id).first()

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
    query = db.query(models.Profile.id)
    if group_id is not None:
        query = query.filter(models.Profile.group_id == group_id)
    if name:
        query = query.filter(models.Profile.name.contains(name))
    return query.count()

def create_profile(db: Session, profile: schemas.ProfileCreate) -> models.Profile:
    profile_data = profile.dict() # Pydantic v1
    # Fingerprint seed logic can be enhanced here if needed
    # e.g., if certain 'random' options are chosen in UI and seed is not provided, generate one.
    # For now, it's taken as is from the input.

    db_profile = models.Profile(**profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile(db: Session, profile_id: int, profile_update: schemas.ProfileUpdate) -> Optional[models.Profile]:
    db_profile = get_profile(db, profile_id) # get_profile now does joinedload for custom_proxy
    if not db_profile:
        return None

    update_data = profile_update.dict(exclude_unset=True) # Pydantic v1
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    # db.add(db_profile) # Not strictly necessary for updates
    db.commit()
    db.refresh(db_profile)
    return db_profile

def delete_profile(db: Session, profile_id: int) -> Optional[models.Profile]:
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None
    # Consider deleting the user_data_dir associated with the profile here or in a background task
    # user_data_dir = os.path.join(USER_DATA_ROOT_DIR, f"profile_{profile_id}")
    # if os.path.exists(user_data_dir):
    #     import shutil
    #     shutil.rmtree(user_data_dir) # This is a destructive operation!
    db.delete(db_profile)
    db.commit()
    return db_profile

def generate_chromium_command(profile: models.Profile, chromium_executable_path: Optional[str] = None) -> List[str]:
    """
    Generates the command list to launch fingerprint-chromium with a given profile.
    """
    exec_path = chromium_executable_path or CHROMIUM_EXECUTABLE_PATH
    args = [exec_path]

    # User Data Directory (CRITICAL for isolation)
    # Ensure the root directory exists
    try:
        os.makedirs(USER_DATA_ROOT_DIR, exist_ok=True)
        user_data_dir = os.path.join(USER_DATA_ROOT_DIR, f"profile_{profile.id}")
        args.append(f'--user-data-dir={user_data_dir}')
    except OSError as e:
        # Handle error in creating directory, e.g., log it or raise specific exception
        print(f"Error creating user data directory {USER_DATA_ROOT_DIR}: {e}")
        # Depending on policy, might want to raise an exception here to halt launch

    # Fingerprint Seed
    if profile.fingerprint_seed is not None: # Ensure it's not just None, but a valid integer
        args.append(f"--fingerprint={profile.fingerprint_seed}")

    # Operating System Platform
    if profile.os_platform:
        args.append(f"--fingerprint-platform={profile.os_platform}")

    # OS Version (if fingerprint-chromium supports a direct flag like --fingerprint-platform-version)
    # if profile.os_version:
    #     args.append(f"--fingerprint-platform-version={profile.os_version}")


    # Proxy Settings
    if profile.proxy_config_type == 'custom' and profile.custom_proxy_id and profile.custom_proxy:
        proxy_details = profile.custom_proxy # This is loaded via joinedload in get_profile
        if proxy_details: # Ensure custom_proxy object is actually loaded
            proxy_type_str = str(proxy_details.type).lower()
            proxy_url = f"{proxy_type_str}://{proxy_details.host}:{proxy_details.port}"
            args.append(f'--proxy-server={proxy_url}')
            # Note: fingerprint-chromium docs suggest --proxy-server doesn't support auth.
            # If proxy_details.username and proxy_details.password are set, they are ignored by this flag.
            # A more advanced setup might use a PAC file or an extension to handle authenticated proxies.
    elif profile.proxy_config_type == 'none':
        args.append('--no-proxy-server') # Standard Chromium flag for disabling proxy usage explicitly

    # Language related settings
    if profile.language:
        args.append(f"--lang={profile.language}")
    if profile.accept_language:
        args.append(f"--accept-lang={shlex.quote(profile.accept_language)}") # Quote if it can contain spaces/special chars

    # Timezone
    if profile.timezone:
        args.append(f"--timezone={profile.timezone}")

    # Browser Version (User-Agent component)
    if profile.browser_version: # This corresponds to --fingerprint-brand-version
        args.append(f"--fingerprint-brand-version={profile.browser_version}")
        # If 'browser_brand' (e.g. 'Edge', 'Brave') is a field, it would be:
        # if profile.browser_brand: args.append(f"--fingerprint-brand={profile.browser_brand}")

    # User-Agent (Direct Override)
    # if profile.user_agent_mode == 'custom' and profile.user_agent: # Assuming a mode field
    if profile.user_agent: # If a direct user_agent field exists and is filled
        args.append(f"--user-agent={shlex.quote(profile.user_agent)}")

    # Sec-CH-UA
    # if profile.sec_ch_ua_mode == 'custom' and profile.sec_ch_ua:
    if profile.sec_ch_ua:
         args.append(f"--sec-ch-ua={shlex.quote(profile.sec_ch_ua)}")


    # WebGL - assuming simple mode flags for now, or driven by --fingerprint seed
    # if profile.webgl_image_mode == 'noise': args.append('--webgl-noise') # Hypothetical
    if profile.webgl_vendor: # This is more specific, fingerprint-chromium might have flags like:
        args.append(f"--webgl-vendor-override={shlex.quote(profile.webgl_vendor)}") # Hypothetical
    if profile.webgl_renderer:
        args.append(f"--webgl-renderer-override={shlex.quote(profile.webgl_renderer)}") # Hypothetical


    # Hardware Concurrency (CPU cores)
    if profile.cpu_cores is not None: # Check for None explicitly if 0 is a valid value
        args.append(f"--fingerprint-hardware-concurrency={profile.cpu_cores}")

    # Device Memory (Not typically a direct flag, often part of overall fingerprint)
    # if profile.memory_gb: args.append(f"--device-memory={profile.memory_gb}") # Hypothetical

    # Do Not Track
    if profile.do_not_track:
        args.append("--enable-do-not-track") # Standard Chromium flag

    # Hardware Acceleration
    if profile.hardware_acceleration is False: # Explicitly False
        args.append("--disable-gpu")
    elif profile.hardware_acceleration is True: # Explicitly True
        args.append("--enable-gpu") # Or ensure --disable-gpu is not present. Explicit enable is safer.

    # Port Scan Protection (Example from blueprint, maps to --disable-non-proxied-udp)
    if profile.port_scan_protection is True: # If True in DB, then add the disable flag
        args.append("--disable-non-proxied-udp")
    # If False in DB, do not add the flag (meaning UDP traffic is not restricted by this flag)

    # Custom Launch Parameters from UI
    if profile.custom_launch_parameters:
        # shlex.split is good for parsing shell-like command strings
        try:
            args.extend(shlex.split(profile.custom_launch_parameters))
        except ValueError as e:
            print(f"Warning: Could not parse custom launch parameters for profile {profile.id}: {e}")
            # Optionally, append as a single block if shlex fails, though this might be wrong.
            # args.append(profile.custom_launch_parameters)


    # Startup Homepage (must be last if it's a URL without a flag)
    # Ensure it's a valid URL and not mistaken for a flag
    if profile.startup_homepage and not profile.startup_homepage.startswith('-') and "://" in profile.startup_homepage:
        args.append(profile.startup_homepage)

    return args
