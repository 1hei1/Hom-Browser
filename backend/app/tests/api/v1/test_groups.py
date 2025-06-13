from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ....app import schemas, models # Adjusted import for consistency
from ....app.crud import crud_profile # To create profiles for group count testing

def test_create_group(client: TestClient, db_session: Session):
    group_data = {"name": "Test Group Alpha"}
    response = client.post("/api/v1/groups/", json=group_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == group_data["name"]
    assert "id" in data
    assert data["profile_count"] == 0 # New group should have 0 profiles

    db_group = db_session.query(models.Group).filter(models.Group.id == data["id"]).first()
    assert db_group is not None
    assert db_group.name == group_data["name"]

def test_create_group_duplicate_name(client: TestClient, db_session: Session):
    group_data = {"name": "Unique Group Name"}
    client.post("/api/v1/groups/", json=group_data) # Create first time
    response = client.post("/api/v1/groups/", json=group_data) # Attempt to create again
    assert response.status_code == 400, response.text
    assert "Group name already exists" in response.json()["detail"]

def test_read_groups(client: TestClient, db_session: Session):
    group1_data = {"name": "Group X"}
    group2_data = {"name": "Group Y"}
    g1_res_data = client.post("/api/v1/groups/", json=group1_data).json()
    client.post("/api/v1/groups/", json=group2_data).json()

    # Create a profile and assign to group 1
    # Ensure ProfileCreate schema has all required fields, or they have defaults
    profile_data_dict = {"name": "Profile in Group X", "group_id": g1_res_data['id']}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit() # Commit direct CRUD operations if session is not auto-committing via client

    response = client.get("/api/v1/groups/?sort_by=name&sort_order=asc") # Added sort for consistent order
    assert response.status_code == 200, response.text
    data = response.json()
    assert "items" in data
    assert "total" in data
    # Total can be >=2 due to test isolation with session-level fixtures,
    # but rollback per test should keep it clean.
    assert data["total"] >= 2

    found_group_x = False
    found_group_y = False
    for item in data["items"]:
        if item["name"] == "Group X":
            found_group_x = True
            assert item["profile_count"] == 1
        if item["name"] == "Group Y":
            found_group_y = True
            assert item["profile_count"] == 0
    assert found_group_x
    assert found_group_y

def test_read_group(client: TestClient, db_session: Session):
    group_data = {"name": "Specific Group"}
    create_response = client.post("/api/v1/groups/", json=group_data)
    group_id = create_response.json()["id"]

    # Create a profile and assign to this group
    profile_data_dict1 = {"name": "Profile in Specific Group", "group_id": group_id}
    profile_create_schema1 = schemas.ProfileCreate(**profile_data_dict1)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema1)

    profile_data_dict2 = {"name": "Profile 2 in Specific Group", "group_id": group_id}
    profile_create_schema2 = schemas.ProfileCreate(**profile_data_dict2)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema2)
    db_session.commit()

    response = client.get(f"/api/v1/groups/{group_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == group_data["name"]
    assert data["id"] == group_id
    assert data["profile_count"] == 2

def test_read_group_not_found(client: TestClient):
    response = client.get("/api/v1/groups/99999") # Non-existent ID
    assert response.status_code == 404

def test_update_group(client: TestClient, db_session: Session):
    group_data = {"name": "Group to Update"}
    create_response = client.post("/api/v1/groups/", json=group_data)
    group_id = create_response.json()["id"]

    update_data = {"name": "Updated Group Name"}
    response = client.put(f"/api/v1/groups/{group_id}", json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["id"] == group_id

    db_group = db_session.query(models.Group).filter(models.Group.id == group_id).first()
    assert db_group is not None
    assert db_group.name == update_data["name"]

def test_update_group_name_conflict(client: TestClient, db_session: Session):
    client.post("/api/v1/groups/", json={"name": "Existing Name"})
    group_to_update_res = client.post("/api/v1/groups/", json={"name": "Original Name For Update"})
    group_to_update_id = group_to_update_res.json()['id']

    update_data = {"name": "Existing Name"}
    response = client.put(f"/api/v1/groups/{group_to_update_id}", json=update_data)
    assert response.status_code == 400, response.text
    assert "Group name already exists" in response.json()["detail"]

def test_update_group_not_found(client: TestClient):
    update_data = {"name": "Non Existent Group Update"}
    response = client.put("/api/v1/groups/99999", json=update_data)
    assert response.status_code == 404

def test_delete_group(client: TestClient, db_session: Session):
    group_data = {"name": "Group to Delete"}
    create_response = client.post("/api/v1/groups/", json=group_data)
    group_id = create_response.json()["id"]

    # Create a profile and assign it to this group
    profile_data_dict = {"name": "Profile in Group to Delete", "group_id": group_id}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    profile_db = crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit() # Commit direct CRUD operations
    assert profile_db.group_id == group_id

    response = client.delete(f"/api/v1/groups/{group_id}")
    assert response.status_code == 200, response.text

    db_group = db_session.query(models.Group).filter(models.Group.id == group_id).first()
    assert db_group is None

    # Verify the profile's group_id is now None
    db_session.refresh(profile_db)
    assert profile_db.group_id is None

def test_delete_group_not_found(client: TestClient):
    response = client.delete("/api/v1/groups/99999")
    assert response.status_code == 404
