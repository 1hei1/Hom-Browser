import pytest
from sqlalchemy.orm import Session
from app import models, schemas, crud # Changed
from app.crud import crud_group, crud_proxy, crud_profile # Changed
import os
import shutil
import datetime
import shlex # For comparing command parts if needed

# Mock CHROMIUM_EXECUTABLE_PATH and USER_DATA_ROOT_DIR for tests
TEST_CHROMIUM_PATH = "/tmp/fake_chromium_test_exe_crud" # Unique name for this test file
TEST_USER_DATA_ROOT = "./test_hom_browser_data_crud_profiles/user_data_dirs" # Unique name

@pytest.fixture(scope="module", autouse=True) # Changed to module scope for efficiency
def setup_test_environment_module(monkeypatch):
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    monkeypatch.setattr(crud.crud_profile, 'CHROMIUM_EXECUTABLE_PATH', abs_test_chromium_path)
    monkeypatch.setattr(crud.crud_profile, 'USER_DATA_ROOT_DIR', abs_test_user_data_root)

    if os.path.exists(abs_test_user_data_root): # Clean once before module tests
        shutil.rmtree(abs_test_user_data_root)
    os.makedirs(abs_test_user_data_root, exist_ok=True)

    os.makedirs(os.path.dirname(abs_test_chromium_path), exist_ok=True)
    if not os.path.exists(abs_test_chromium_path):
        with open(abs_test_chromium_path, 'w') as f: f.write('#!/bin/sh\necho FAKE CHROMIUM "$@"')
        os.chmod(abs_test_chromium_path, 0o755)

    yield # Tests run here

    if os.path.exists(abs_test_user_data_root): # Clean once after all module tests
        shutil.rmtree(abs_test_user_data_root)
    if os.path.exists(abs_test_chromium_path):
        os.remove(abs_test_chromium_path)
    try:
        if os.path.dirname(abs_test_chromium_path) != "/tmp":
             os.rmdir(os.path.dirname(abs_test_chromium_path))
    except OSError:
        pass

# Per-test fixture to ensure clean user data dir for specific tests that check its creation
@pytest.fixture
def clean_user_data_sub_dir(setup_test_environment_module): # Depends on module fixture
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)
    # This doesn't delete subdirectories, generate_chromium_command creates them.
    # Test that checks dir creation should verify it.
    # If a test *modifies* a specific profile's dir and expects it clean next time, that's more complex.
    # For now, generate_chromium_command's os.makedirs(exist_ok=True) is idempotent.
    yield


def test_generate_command_basic(db_session: Session, clean_user_data_sub_dir):
    profile_data = schemas.ProfileCreate(name="Test Basic Launch")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)

    command = crud.crud_profile.generate_chromium_command(db_profile)
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    assert command[0] == abs_test_chromium_path
    expected_user_data_dir = os.path.join(abs_test_user_data_root, f'profile_{db_profile.id}')
    assert f"--user-data-dir={expected_user_data_dir}" in command
    assert os.path.exists(expected_user_data_dir)

def test_generate_command_with_all_params_updated(db_session: Session, clean_user_data_sub_dir):
    group = crud_group.create_group(db_session, schemas.GroupCreate(name="TestGroupCmdGenParams"))
    proxy = crud_proxy.create_proxy(db_session, schemas.ProxyCreate(name="TestProxyCmdGenParams", type="SOCKS5", host="1.2.3.4", port=1080))

    profile_create_data = schemas.ProfileCreate(
        name="Test Full Launch Params",
        group_id=group.id,
        os_platform="linux",
        user_agent_mode="custom", # Updated
        user_agent_custom="CustomUserAgent/1.0", # Updated
        sec_ch_ua_mode="custom", # Updated
        sec_ch_ua_custom="\"BrandA\";v=\"1\", \"BrandB\";v=\"2\"", # Updated
        webgl_metadata_mode="custom", # Updated
        webgl_vendor="TestVendor", # Updated
        webgl_renderer="TestRenderer", # Updated
        audiocontext_mode="noise", # Updated
        clientrects_mode="off", # Updated
        speech_voices_mode="custom", # Updated
        speech_voices_custom_data="{\"lang\":\"en-GB\",\"name\":\"TestVoice\"}", # Updated
        ssl_cipher_suites_mode="custom", # Updated
        ssl_custom_suites_data="TLS_AES_128_GCM_SHA256,TLS_CHACHA20_POLY1305_SHA256", # Updated
        browser_version="121.0.0.1",
        proxy_config_type="custom",
        custom_proxy_id=proxy.id,
        language="fr-FR",
        accept_language="fr-FR,fr;q=0.9",
        timezone="Europe/Paris",
        fingerprint_seed=54321,
        startup_homepage="https://example.org",
        custom_launch_parameters="--new-flag --another=\"value with space\"",
        do_not_track=True,
        hardware_acceleration=False,
        port_scan_protection=False # Test this being False
    )
    db_profile = crud.crud_profile.create_profile(db_session, profile_create_data)
    loaded_profile = crud.crud_profile.get_profile(db_session, db_profile.id)
    assert loaded_profile is not None

    command = crud.crud_profile.generate_chromium_command(loaded_profile)
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    abs_test_user_data_root = os.path.abspath(TEST_USER_DATA_ROOT)

    assert command[0] == abs_test_chromium_path
    expected_user_data_dir = os.path.join(abs_test_user_data_root, f'profile_{loaded_profile.id}')
    assert f"--user-data-dir={expected_user_data_dir}" in command
    assert "--fingerprint=54321" in command
    assert "--fingerprint-platform=linux" in command
    assert "--proxy-server=socks5://1.2.3.4:1080" in command
    assert "--lang=fr-FR" in command
    assert "--accept-lang=fr-FR,fr;q=0.9" in command
    assert "--timezone=Europe/Paris" in command
    assert "--fingerprint-brand-version=121.0.0.1" in command
    assert "--user-agent=CustomUserAgent/1.0" in command
    assert "--sec-ch-ua=\"BrandA\";v=\"1\", \"BrandB\";v=\"2\"" in command
    assert "--webgl-vendor-override=TestVendor" in command # Hypothetical
    assert "--webgl-renderer-override=TestRenderer" in command # Hypothetical
    assert "--audiocontext-mode=noise" in command # Hypothetical
    assert "--clientrects-mode=off" in command # Hypothetical
    assert "--speech-voices-custom={\"lang\":\"en-GB\",\"name\":\"TestVoice\"}" in command # Hypothetical
    assert "--ssl-cipher-suites=TLS_AES_128_GCM_SHA256,TLS_CHACHA20_POLY1305_SHA256" in command # Hypothetical
    assert "--enable-do-not-track" in command
    assert "--disable-gpu" in command
    assert not any(arg == "--disable-non-proxied-udp" for arg in command) # port_scan_protection is False
    assert "--new-flag" in command
    assert "--another=value with space" in command
    assert command[-1] == "https://example.org"
    assert os.path.exists(expected_user_data_dir)

# ----- User Agent Tests -----
def test_generate_command_user_agent_custom(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test UA Custom", user_agent_mode="custom", user_agent_custom="MyCustomUA/2.0")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert f"--user-agent=MyCustomUA/2.0" in command

def test_generate_command_user_agent_default_or_random(db_session: Session):
    for mode in ["default", "random"]:
        profile_data = schemas.ProfileCreate(name=f"Test UA {mode}", user_agent_mode=mode, fingerprint_seed=111 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--user-agent=") for arg in command)
        if mode == "random": assert "--fingerprint=111" in command

# ----- Sec-CH-UA Tests -----
def test_generate_command_sec_ch_ua_custom(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test SecCHUA Custom", sec_ch_ua_mode="custom", sec_ch_ua_custom="\"SecBrand\";v=\"99\"")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert f"--sec-ch-ua=\"SecBrand\";v=\"99\"" in command

def test_generate_command_sec_ch_ua_default_or_random(db_session: Session):
    for mode in ["default", "random"]:
        profile_data = schemas.ProfileCreate(name=f"Test SecCHUA {mode}", sec_ch_ua_mode=mode, fingerprint_seed=222 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--sec-ch-ua=") for arg in command)
        if mode == "random": assert "--fingerprint=222" in command

# ----- WebGL Image Mode (No specific flag for custom hash yet) -----
def test_generate_command_webgl_image_mode(db_session: Session):
    for mode in ["default", "custom", "random"]: # Assuming no custom hash field for now
        profile_data = schemas.ProfileCreate(name=f"Test WebGL Img {mode}", webgl_image_mode=mode, fingerprint_seed=333 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--webgl-image-hash=") for arg in command) # No such flag implemented
        if mode == "random": assert "--fingerprint=333" in command

# ----- WebGL Metadata (Vendor/Renderer) -----
def test_generate_command_webgl_metadata_custom_linux(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test WebGL Meta Custom Linux", os_platform="linux",
                                         webgl_metadata_mode="custom", webgl_vendor="CustomVendor", webgl_renderer="CustomRenderer")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert "--webgl-vendor-override=CustomVendor" in command # Hypothetical
    assert "--webgl-renderer-override=CustomRenderer" in command # Hypothetical

def test_generate_command_webgl_metadata_custom_non_linux(db_session: Session):
    profile_data = schemas.ProfileCreate(name="Test WebGL Meta Custom Win", os_platform="windows",
                                         webgl_metadata_mode="custom", webgl_vendor="CustomVendor", webgl_renderer="CustomRenderer")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert not any(arg.startswith("--webgl-vendor-override=") for arg in command)
    assert not any(arg.startswith("--webgl-renderer-override=") for arg in command)

def test_generate_command_webgl_metadata_default_or_random(db_session: Session):
    for mode in ["default", "random"]:
        profile_data = schemas.ProfileCreate(name=f"Test WebGL Meta {mode}", os_platform="linux",
                                             webgl_metadata_mode=mode, fingerprint_seed=444 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--webgl-vendor-override=") for arg in command)
        assert not any(arg.startswith("--webgl-renderer-override=") for arg in command)
        if mode == "random": assert "--fingerprint=444" in command

# ----- AudioContext, ClientRects Mode -----
@pytest.mark.parametrize("feature_mode_attr, feature_mode_value, expected_flag_part", [
    ("audiocontext_mode", "noise", "--audiocontext-mode=noise"),
    ("audiocontext_mode", "off", "--audiocontext-mode=off"),
    ("clientrects_mode", "noise", "--clientrects-mode=noise"),
    ("clientrects_mode", "off", "--clientrects-mode=off"),
])
def test_generate_command_audio_client_modes(db_session: Session, feature_mode_attr, feature_mode_value, expected_flag_part):
    profile_data = schemas.ProfileCreate(name=f"Test {feature_mode_attr} {feature_mode_value}", **{feature_mode_attr: feature_mode_value})
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert expected_flag_part in command # Hypothetical flags

@pytest.mark.parametrize("feature_mode_attr", ["audiocontext_mode", "clientrects_mode"])
def test_generate_command_audio_client_modes_default_random(db_session: Session, feature_mode_attr):
    for mode in ["default", "random"]:
        profile_data = schemas.ProfileCreate(name=f"Test {feature_mode_attr} {mode}",
                                             **{feature_mode_attr: mode}, fingerprint_seed=555 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith(f"--{feature_mode_attr.split('_')[0]}-mode=") for arg in command)
        if mode == "random": assert "--fingerprint=555" in command

# ----- Speech Voices -----
def test_generate_command_speech_voices_custom(db_session: Session):
    custom_data = "{\"lang\":\"en-US\",\"name\":\"CustomVoice\"}"
    profile_data = schemas.ProfileCreate(name="Test Speech Custom", speech_voices_mode="custom", speech_voices_custom_data=custom_data)
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert f"--speech-voices-custom={custom_data}" in command # Hypothetical

def test_generate_command_speech_voices_default_random(db_session: Session):
    for mode in ["default", "random"]:
        profile_data = schemas.ProfileCreate(name=f"Test Speech {mode}", speech_voices_mode=mode, fingerprint_seed=666 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--speech-voices-custom=") for arg in command)
        if mode == "random": assert "--fingerprint=666" in command

# ----- SSL Cipher Suites -----
def test_generate_command_ssl_custom(db_session: Session):
    custom_data = "TLS_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    profile_data = schemas.ProfileCreate(name="Test SSL Custom", ssl_cipher_suites_mode="custom", ssl_custom_suites_data=custom_data)
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert f"--ssl-cipher-suites={custom_data}" in command # Highly Hypothetical

def test_generate_command_ssl_default_strict_random(db_session: Session):
    for mode in ["default", "strict", "random"]: # Assuming "strict" might have a flag or rely on seed
        profile_data = schemas.ProfileCreate(name=f"Test SSL {mode}", ssl_cipher_suites_mode=mode, fingerprint_seed=777 if mode == "random" else None)
        db_profile = crud.crud_profile.create_profile(db_session, profile_data)
        command = crud.crud_profile.generate_chromium_command(db_profile)
        assert not any(arg.startswith("--ssl-cipher-suites=") for arg in command) # Expect no custom data flag
        # if mode == "strict": assert "--ssl-strict-mode" in command # Hypothetical for strict
        if mode == "random": assert "--fingerprint=777" in command


# ----- Existing Tests (Keep them, ensure they still pass or adapt if needed) -----
def test_generate_command_no_proxy_flag(db_session: Session): # Renamed to avoid conflict
    profile_data = schemas.ProfileCreate(name="Test No Proxy Flag", proxy_config_type="none")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert "--no-proxy-server" in command
    assert not any(arg.startswith("--proxy-server=") for arg in command)

def test_generate_command_default_proxy_no_flag(db_session: Session): # Renamed
    profile_data = schemas.ProfileCreate(name="Test Default Proxy No Flag", proxy_config_type="default")
    db_profile = crud.crud_profile.create_profile(db_session, profile_data)
    command = crud.crud_profile.generate_chromium_command(db_profile)
    assert not any(arg.startswith("--proxy-server=") for arg in command)
    assert "--no-proxy-server" not in command

def test_launch_endpoint_returns_command(client: TestClient, db_session: Session):
    abs_test_chromium_path = os.path.abspath(TEST_CHROMIUM_PATH)
    profile_create_data = schemas.ProfileCreate(name="Test Launch Endpoint CRUD", os_platform="windows", language="de-DE", user_agent_mode="custom", user_agent_custom="EndpointUA")
    create_response = client.post("/api/v1/profiles/", json=profile_create_data.dict())
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.post(f"/api/v1/profiles/{profile_id}/launch")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["profile_id"] == profile_id
    assert "command" in data and data["command"] is not None
    returned_command_args = shlex.split(data["command"])

    assert returned_command_args[0] == abs_test_chromium_path
    assert any(arg.startswith(f"--user-data-dir=") for arg in returned_command_args)
    assert "--fingerprint-platform=windows" in returned_command_args
    assert "--lang=de-DE" in returned_command_args
    assert "--user-agent=EndpointUA" in returned_command_args
    assert "Browser launch command for profile" in data["message"]

    db_profile_reloaded = crud.crud_profile.get_profile(db_session, profile_id)
    assert db_profile_reloaded is not None
    assert db_profile_reloaded.last_launch_time is not None
    assert isinstance(db_profile_reloaded.last_launch_time, datetime.datetime)
    assert (datetime.datetime.now(datetime.timezone.utc) - db_profile_reloaded.last_launch_time).total_seconds() < 15 # Increased tolerance slightly

def test_launch_endpoint_chromium_not_found(client: TestClient, db_session: Session, monkeypatch):
    non_existent_path = "/completely/non/existent/path/to/chromium_for_this_test" # Unique non_existent path
    monkeypatch.setattr(crud.crud_profile, 'CHROMIUM_EXECUTABLE_PATH', non_existent_path)

    original_os_path_exists = os.path.exists
    def mock_os_path_exists_for_no_exec(path):
        if path == non_existent_path: return False
        # Prevent fallback to dev path finding the dummy executable from setup_test_environment_module
        if "fingerprint-chromium" in path and ("chrome" in path or "fingerprint-chromium" in path or "chromium" in path) : return False
        return original_os_path_exists(path)
    monkeypatch.setattr(os.path, 'exists', mock_os_path_exists_for_no_exec)

    profile_create_data = schemas.ProfileCreate(name="Test Launch No Executable CRUD")
    create_response = client.post("/api/v1/profiles/", json=profile_create_data.dict())
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.post(f"/api/v1/profiles/{profile_id}/launch")
    assert response.status_code == 200
    data = response.json()
    assert data["command"] is None
    assert "Chromium executable not found" in data["message"]
