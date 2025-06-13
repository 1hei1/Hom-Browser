from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import List, Optional # Added Optional for notes in helper
from app import schemas, models # Changed
from app.crud import crud_proxy, crud_profile # Changed

def create_proxy_in_db(db_session: Session, name: str, type: str = "HTTP", host: str = "127.0.0.1", port: int = 8080, notes: Optional[str] = None) -> models.Proxy:
    proxy_create = schemas.ProxyCreate(name=name, type=type, host=host, port=port, notes=notes)
    return crud_proxy.create_proxy(db=db_session, proxy=proxy_create)

def test_create_proxy(client: TestClient, db_session: Session):
    proxy_data = {"name": "Test Proxy 1", "type": "SOCKS5", "host": "proxy.example.com", "port": 1080, "notes": "SOCKS5 proxy"}
    response = client.post("/api/v1/proxies/", json=proxy_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == proxy_data["name"]
    assert data["host"] == proxy_data["host"]
    assert data["port"] == proxy_data["port"]
    assert data["type"] == proxy_data["type"]
    assert data["notes"] == proxy_data["notes"]
    assert data["usage_count"] == 0
    assert "id" in data

    db_proxy = db_session.query(models.Proxy).filter(models.Proxy.id == data["id"]).first()
    assert db_proxy is not None
    assert db_proxy.name == proxy_data["name"]

def test_read_proxies(client: TestClient, db_session: Session):
    create_proxy_in_db(db_session, name="Proxy Alpha", host="1.1.1.1")
    p2 = create_proxy_in_db(db_session, name="Proxy Beta", host="2.2.2.2", port=8888)

    # Create a profile using Proxy Beta
    # Ensure ProfileCreate has all required fields or defaults
    profile_data_dict = {"name":"Profile Using Beta Proxy", "custom_proxy_id":p2.id, "proxy_config_type":"custom"}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit()

    response = client.get("/api/v1/proxies/?sort_by=name&sort_order=asc") # Added sort
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    found_alpha = False
    found_beta = False
    for item in data["items"]:
        if item["name"] == "Proxy Alpha":
            found_alpha = True
            assert item["usage_count"] == 0
        if item["name"] == "Proxy Beta":
            found_beta = True
            assert item["usage_count"] == 1
    assert found_alpha
    assert found_beta

def test_read_proxies_search(client: TestClient, db_session: Session):
    create_proxy_in_db(db_session, name="SearchMeHTTP", type="HTTP", host="search.http.com")
    create_proxy_in_db(db_session, name="SearchMeSOCKS", type="SOCKS5", host="search.socks.com")
    create_proxy_in_db(db_session, name="AnotherOne", type="HTTP", host="another.com")
    db_session.commit()

    response = client.get("/api/v1/proxies/?search=SearchMe")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2, f"Expected 2, got {data['total']}. Items: {data['items']}"
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert "SearchMe" in item["name"]

    response_host = client.get("/api/v1/proxies/?search=search.http.com")
    assert response_host.status_code == 200
    data_host = response_host.json()
    assert data_host["total"] == 1
    assert data_host["items"][0]["name"] == "SearchMeHTTP"

    response_type = client.get("/api/v1/proxies/?search=SOCKS5")
    assert response_type.status_code == 200
    data_type = response_type.json()
    assert data_type["total"] == 1
    assert data_type["items"][0]["name"] == "SearchMeSOCKS"


def test_read_proxy(client: TestClient, db_session: Session):
    proxy = create_proxy_in_db(db_session, name="Specific Proxy")
    profile_data_dict = {"name":"Profile Using Specific Proxy", "custom_proxy_id":proxy.id, "proxy_config_type":"custom"}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit()

    response = client.get(f"/api/v1/proxies/{proxy.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Specific Proxy"
    assert data["id"] == proxy.id
    assert data["usage_count"] == 1

def test_read_proxy_not_found(client: TestClient):
    response = client.get("/api/v1/proxies/99999")
    assert response.status_code == 404

def test_update_proxy(client: TestClient, db_session: Session):
    proxy = create_proxy_in_db(db_session, name="Proxy to Update", host="original.host.com")
    db_session.commit()
    update_data = {"name": "Updated Proxy Name", "host": "updated.host.com", "port": 9090, "type": "SOCKS5"}

    response = client.put(f"/api/v1/proxies/{proxy.id}", json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["host"] == update_data["host"]
    assert data["port"] == update_data["port"]
    assert data["type"] == update_data["type"]


    db_proxy = db_session.query(models.Proxy).filter(models.Proxy.id == proxy.id).first()
    assert db_proxy is not None
    assert db_proxy.name == update_data["name"]
    assert db_proxy.host == update_data["host"]
    assert db_proxy.type == update_data["type"]

def test_update_proxy_not_found(client: TestClient):
    update_data = {"name": "Non Existent"}
    response = client.put("/api/v1/proxies/99999", json=update_data)
    assert response.status_code == 404

def test_delete_proxy_success(client: TestClient, db_session: Session):
    proxy = create_proxy_in_db(db_session, name="Proxy to Delete")
    db_session.commit()
    response = client.delete(f"/api/v1/proxies/{proxy.id}")
    assert response.status_code == 200, response.text

    db_proxy_check = db_session.query(models.Proxy).filter(models.Proxy.id == proxy.id).first()
    assert db_proxy_check is None

def test_delete_proxy_in_use(client: TestClient, db_session: Session):
    proxy = create_proxy_in_db(db_session, name="Used Proxy")
    profile_data_dict = {"name":"Profile Using Used Proxy", "custom_proxy_id":proxy.id, "proxy_config_type":"custom"}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit()

    response = client.delete(f"/api/v1/proxies/{proxy.id}")
    assert response.status_code == 409, response.text
    data = response.json()
    assert "Proxy is currently used by 1 profile(s)" in data["detail"]

    db_proxy_check = db_session.query(models.Proxy).filter(models.Proxy.id == proxy.id).first()
    assert db_proxy_check is not None

def test_delete_proxy_not_found(client: TestClient):
    response = client.delete("/api/v1/proxies/99999")
    assert response.status_code == 404

def test_batch_delete_proxies(client: TestClient, db_session: Session):
    p1 = create_proxy_in_db(db_session, name="BatchDelete 1")
    p2 = create_proxy_in_db(db_session, name="BatchDelete 2 Used")
    p3 = create_proxy_in_db(db_session, name="BatchDelete 3")
    db_session.commit()


    profile_data_dict = {"name":"Profile Using BatchDelete 2", "custom_proxy_id":p2.id, "proxy_config_type":"custom"}
    profile_create_schema = schemas.ProfileCreate(**profile_data_dict)
    crud_profile.create_profile(db=db_session, profile=profile_create_schema)
    db_session.commit()

    payload = {"ids": [p1.id, p2.id, p3.id, 9999]} # 9999 is a non-existent ID
    response = client.post("/api/v1/proxies/batch-delete", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["deleted_count"] == 2
    assert len(data["errors"]) == 2

    error_ids = {err['id'] for err in data['errors']}
    assert p2.id in error_ids
    assert 9999 in error_ids

    assert db_session.query(models.Proxy).filter(models.Proxy.id == p1.id).first() is None
    assert db_session.query(models.Proxy).filter(models.Proxy.id == p2.id).first() is not None
    assert db_session.query(models.Proxy).filter(models.Proxy.id == p3.id).first() is None
    # No need to check for 9999 in DB as it was never there.

    # Check error messages
    for err in data["errors"]:
        if err['id'] == p2.id:
            assert "Proxy is used by 1 profile(s)" in err['error']
        if err['id'] == 9999:
            assert "Proxy not found" in err['error']
