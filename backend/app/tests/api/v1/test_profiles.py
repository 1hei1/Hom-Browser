from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import schemas # Changed
from app import models # Changed
from app.crud import crud_profile # Changed

# Note: Tests should ideally rely on the client fixture which uses a db_session with rollback.
# Direct use of db_session is for verifying data persistence if not using the client for all actions.

def test_create_profile(client: TestClient, db_session: Session):
    profile_data = {
        "name": "Test Profile 1",
        "os_platform": "windows",
        "browser_version": "100.0.1.0",
        "notes": "A test profile"
        # Add other required fields from ProfileCreate if any, or ensure defaults are handled
    }
    response = client.post("/api/v1/profiles/", json=profile_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == profile_data["name"]
    assert data["os_platform"] == profile_data["os_platform"]
    assert "id" in data

    # Verify in DB
    db_profile = db_session.query(models.Profile).filter(models.Profile.id == data["id"]).first()
    assert db_profile is not None
    assert db_profile.name == profile_data["name"]

def test_read_profiles(client: TestClient, db_session: Session):
    # Create a profile first to ensure there's data
    profile_data = {"name": "Test Profile For Listing", "os_platform": "linux"}
    # Use client to create, ensuring it goes through the API and uses the same session context if test needs it
    created_response = client.post("/api/v1/profiles/", json=profile_data)
    assert created_response.status_code == 201

    response = client.get("/api/v1/profiles/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "items" in data
    assert "total" in data

    found = False
    for item in data["items"]:
        if item["name"] == profile_data["name"]:
            found = True
            break
    assert found, "Created profile not found in list"

def test_read_profile(client: TestClient, db_session: Session):
    profile_data = {"name": "Test Profile Specific", "os_platform": "macos"}
    create_response = client.post("/api/v1/profiles/", json=profile_data)
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.get(f"/api/v1/profiles/{profile_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == profile_data["name"]
    assert data["id"] == profile_id

def test_read_profile_not_found(client: TestClient):
    response = client.get("/api/v1/profiles/99999") # Non-existent ID
    assert response.status_code == 404

def test_update_profile(client: TestClient, db_session: Session):
    profile_data = {"name": "Profile to Update", "notes": "Original note"}
    create_response = client.post("/api/v1/profiles/", json=profile_data)
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    update_data = {"name": "Updated Profile Name", "notes": "Updated note"}
    response = client.put(f"/api/v1/profiles/{profile_id}", json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["notes"] == update_data["notes"]
    assert data["id"] == profile_id

    # Verify in DB
    db_profile = db_session.query(models.Profile).filter(models.Profile.id == profile_id).first()
    assert db_profile is not None
    assert db_profile.name == update_data["name"]
    assert db_profile.notes == update_data["notes"]

def test_update_profile_not_found(client: TestClient):
    update_data = {"name": "Non Existent"}
    response = client.put("/api/v1/profiles/99999", json=update_data) # Non-existent ID
    assert response.status_code == 404

def test_delete_profile(client: TestClient, db_session: Session):
    profile_data = {"name": "Profile to Delete"}
    create_response = client.post("/api/v1/profiles/", json=profile_data)
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/profiles/{profile_id}")
    assert response.status_code == 200, response.text # FastAPI returns 200 OK with response body

    # Verify in DB
    db_profile = db_session.query(models.Profile).filter(models.Profile.id == profile_id).first()
    assert db_profile is None

def test_delete_profile_not_found(client: TestClient):
    response = client.delete("/api/v1/profiles/99999") # Non-existent ID
    assert response.status_code == 404

def test_read_profiles_pagination_and_filter(client: TestClient, db_session: Session):
    # Create some profiles
    client.post("/api/v1/profiles/", json={"name": "Alpha Profile", "group_id": 1, "os_platform": "windows"})
    client.post("/api/v1/profiles/", json={"name": "Beta Profile", "group_id": 2, "os_platform": "linux"})
    client.post("/api/v1/profiles/", json={"name": "Alpha Another", "group_id": 1, "os_platform": "macos"})

    # Test pagination
    response_page1 = client.get("/api/v1/profiles/?page=1&page_size=2&sort_by=name&sort_order=asc")
    assert response_page1.status_code == 200
    data_page1 = response_page1.json()
    assert len(data_page1["items"]) == 2
    assert data_page1["total"] == 3
    assert data_page1["page"] == 1
    assert data_page1["pages"] == 2
    assert data_page1["items"][0]["name"] == "Alpha Another" # Sorted by name
    assert data_page1["items"][1]["name"] == "Alpha Profile"

    response_page2 = client.get("/api/v1/profiles/?page=2&page_size=2&sort_by=name&sort_order=asc")
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    assert len(data_page2["items"]) == 1
    assert data_page2["items"][0]["name"] == "Beta Profile"


    # Test filtering by name
    response_name_filter = client.get("/api/v1/profiles/?name=Alpha")
    assert response_name_filter.status_code == 200
    data_name_filter = response_name_filter.json()
    assert data_name_filter["total"] == 2 # Alpha Profile, Alpha Another
    for item in data_name_filter["items"]:
        assert "Alpha" in item["name"]

    # Test filtering by group_id
    response_group_filter = client.get("/api/v1/profiles/?group_id=1")
    assert response_group_filter.status_code == 200
    data_group_filter = response_group_filter.json()
    assert data_group_filter["total"] == 2 # Alpha Profile, Alpha Another
    for item in data_group_filter["items"]:
        assert item["group_id"] == 1
