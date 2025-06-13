import pytest
from sqlalchemy.orm import Session
from ....app import models, schemas, crud # Main crud module
from ....app.crud import crud_group, crud_proxy, crud_profile # Specific crud modules
import os
import shutil
import datetime
import shlex # For comparing command parts if needed

# Mock CHROMIUM_EXECUTABLE_PATH and USER_DATA_ROOT_DIR for tests
TEST_CHROMIUM_PATH = "/tmp/fake_chromium_test_exe" # More specific name
TEST_USER_DATA_ROOT = "./test_hom_browser_data_crud/user_data_dirs" # Distinct from other test user data

@pytest.fixture(autouse=True) # Apply to all tests in this module
def setup_test_environment(monkeypatch):
    # Ensure the path is absolute for consistency, or handle relative paths carefully
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    monkeypatch.setattr(crud.crud_profile, 'CHROMIUM_EXECUTABLE_PATH', abs_test_chromium_path)
    monkeypatch.setattr(crud.crud_profile, 'USER_DATA_ROOT_DIR', abs_test_user_data_root)

    # Clean up before and after each test (or session if preferred)
    if os.path.exists(abs_test_user_data_root):
        shutil.rmtree(abs_test_user_data_root)
    os.makedirs(abs_test_user_data_root, exist_ok=True)

    # Create dummy executable for tests that might check its existence via endpoint
    os.makedirs(os.path.dirname(abs_test_chromium_path), exist_ok=True)
    with open(abs_test_chromium_path, 'w') as f: f.write('#!/bin/sh\necho FAKE CHROMIUM "$@"')
    os.chmod(abs_test_chromium_path, 0o755)

    yield # Test runs here

    if os.path.exists(abs_test_user_data_root):
        shutil.rmtree(abs_test_user_data_root)
    if os.path.exists(abs_test_chromium_path):
        os.remove(abs_test_chromium_path)
    # Clean up parent dir if empty and it was created by this fixture
    try:
        if os.path.dirname(abs_test_chromium_path) != "/tmp": # Avoid deleting /tmp
             os.rmdir(os.path.dirname(abs_test_chromium_path))
    except OSError:
        pass # Directory not empty or other error, fine for cleanup


def test_generate_command_basic(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test Basic Launch")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    # No commit needed if create_profile commits, which it does.

    command = crud.crud_profile.generate_chromium_command(db_profile)
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    assert command[0] == abs_test_chromium_path
    expected_user_data_dir = os.path.join(abs_test_user_data_root, f'profile_{db_profile.id}')
    assert f"--user-data-dir={expected_user_data_dir}" in command
    assert os.path.exists(expected_user_data_dir) # Command generation creates this dir

def test_generate_command_with_all_essential_params(db_session: Session):
    group = crud_group.create_group(db_session, schemas.GroupCreate(name="TestGroupCmdGen"))
    proxy = crud_proxy.create_proxy(db_session, schemas.ProxyCreate(name="TestProxyCmdGen", type="SOCKS5", host="1.2.3.4", port=1080))
    # No commit needed if create_xxx commits.

    profile_create_data = schemas.ProfileCreate(
        name="Test Full Launch",
        group_id=group.id,
        os_platform="linux",
        user_agent="TestAgent/1.0", # Added for testing
        sec_ch_ua="\"TestBrand\";v=\"1\"", # Added for testing
        browser_version="120.0.0.0",
        proxy_config_type="custom",
        custom_proxy_id=proxy.id,
        language="en-GB",
        accept_language="en-GB,en;q=0.9",
        timezone="Europe/London",
        fingerprint_seed=12345,
        startup_homepage="https://example.com",
        custom_launch_parameters="--no-first-run --disable-extensions --some-flag=\"with spaces\"",
        do_not_track=True, # Added
        hardware_acceleration=False, # Added
        port_scan_protection=True # Added
    )
    db_profile = crud.crud_profile.create_profile(db_session, profile_create_data)

    loaded_profile = crud.crud_profile.get_profile(db_session, db_profile.id) # Fetches with relationships
    assert loaded_profile is not None

    command = crud.crud_profile.generate_chromium_command(loaded_profile)
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    assert command[0] == abs_test_chromium_path
    expected_user_data_dir = os.path.join(abs_test_user_data_root, f'profile_{loaded_profile.id}')
    assert f"--user-data-dir={expected_user_data_dir}" in command
    assert "--fingerprint=12345" in command
    assert "--fingerprint-platform=linux" in command
    assert "--proxy-server=socks5://1.2.3.4:1080" in command
    assert "--lang=en-GB" in command
    assert "--accept-lang=en-GB,en;q=0.9" in command
    assert "--timezone=Europe/London" in command
    assert "--fingerprint-brand-version=120.0.0.0" in command
    assert "--user-agent=TestAgent/1.0" in command
    assert "--sec-ch-ua=\"TestBrand\";v=\"1\"" in command
    assert "--enable-do-not-track" in command
    assert "--disable-gpu" in command
    assert "--disable-non-proxied-udp" in command # port_scan_protection = True
    assert "--no-first-run" in command
    assert "--disable-extensions" in command
    assert "--some-flag=with spaces" in command # Check shlex.split behavior
    assert command[-1] == "https://example.com"
    assert os.path.exists(expected_user_data_dir)

def test_generate_command_no_proxy_flag(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test No Proxy", proxy_config_type="none")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert "--no-proxy-server" in command
    assert not any(arg.startswith("--proxy-server") for arg in command)


def test_generate_command_default_proxy_no_flag(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test Default Proxy", proxy_config_type="default")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert not any(arg.startswith("--proxy-server") for arg in command)
    assert "--no-proxy-server" not in command


def test_launch_endpoint_returns_command(client: TestClient, db_session: Session):
    # setup_test_environment fixture already creates TEST_CHROMIUM_PATH
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)

    profile_create_data = schemas.ProfileCreate(name="Test Launch Endpoint", os_platform="windows", language="de-DE")
    create_response = client.post("/api/v1/profiles/", json=profile_create_data.dict()) # Pydantic v1
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.post(f"/api/v1/profiles/{profile_id}/launch")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["profile_id"] == profile_id
    assert "command" in data and data["command"] is not None

    # shlex.split to compare args robustly if command is a string
    returned_command_args = shlex.split(data["command"])

    assert returned_command_args[0] == abs_test_chromium_path
    assert any(arg.startswith(f"--user-data-dir=") for arg in returned_command_args)
    assert "--fingerprint-platform=windows" in returned_command_args
    assert "--lang=de-DE" in returned_command_args
    assert "Browser launch command for profile" in data["message"]

    db_profile_reloaded = crud.crud_profile.get_profile(db_session, profile_id) # Fetch again to get updated last_launch_time
    assert db_profile_reloaded is not None
    assert db_profile_reloaded.last_launch_time is not None
    # Ensure it's a datetime object before comparison
    assert isinstance(db_profile_reloaded.last_launch_time, datetime.datetime)
    assert (datetime.datetime.now(datetime.timezone.utc) - db_profile_reloaded.last_launch_time).total_seconds() < 10 # Increased tolerance


def test_launch_endpoint_chromium_not_found(client: TestClient, db_session: Session, monkeypatch):
    # This test needs to ensure the executable is NOT found by the endpoint
    non_existent_path = "/completely/non/existent/path/to/chromium"
    monkeypatch.setattr(crud.crud_profile, 'CHROMIUM_EXECUTABLE_PATH', non_existent_path)

    # Also patch os.path.exists to simulate it not being found in dev fallback paths
    original_os_path_exists = os.path.exists
    def mock_os_path_exists(path):
        if path == non_existent_path: # For the initial check in endpoint
            return False
        if "fingerprint-chromium" in path and "chrome" in path : # For dev fallback check
            return False
        return original_os_path_exists(path) # Allow other exists calls (e.g. for user_data_dir)
    monkeypatch.setattr(os.path, 'exists', mock_os_path_exists)

    profile_create_data = schemas.ProfileCreate(name="Test Launch No Executable")
    create_response = client.post("/api/v1/profiles/", json=profile_create_data.dict()) # Pydantic v1
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.post(f"/api/v1/profiles/{profile_id}/launch")
    assert response.status_code == 200 # Endpoint handles this by returning error in message
    data = response.json()
    assert data["command"] is None # No command if executable is not found
    assert "Chromium executable not found" in data["message"]
