"""Phase 2 domain tests: farms + fields CRUD with server-side ownership (docs/08 §2, docs/12 §6)."""

import uuid

from app.models.role import RoleName
from tests.conftest import create_user_with_role

INTRUDER_PHONE = "+919700000200"


async def _intruder_headers(client, db, phone: str = INTRUDER_PHONE):
    await create_user_with_role(db, phone, RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": phone, "password": "password123"}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_farmer_can_create_list_and_get_farm(client, farmer):
    headers = farmer["headers"]
    created = await client.post(
        "/api/v1/farms", json={"name": "My Farm", "district": "Gaya"}, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["field_count"] == 0

    listed = await client.get("/api/v1/farms", headers=headers)
    assert listed.status_code == 200
    assert [farm["name"] for farm in listed.json()] == ["My Farm"]

    fetched = await client.get(f"/api/v1/farms/{created.json()['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "My Farm"


async def test_farm_update_and_archive(client, farmer):
    headers = farmer["headers"]
    farm_id = (
        await client.post("/api/v1/farms", json={"name": "Old Name"}, headers=headers)
    ).json()["id"]

    updated = await client.patch(
        f"/api/v1/farms/{farm_id}", json={"name": "New Name"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "New Name"

    assert (await client.delete(f"/api/v1/farms/{farm_id}", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/farms", headers=headers)).json() == []


async def test_farm_ownership_protection(client, db, farmer):
    """Another farmer's farm returns 404 — never 403 (docs/12 §6: no enumeration)."""
    intruder_headers = await _intruder_headers(client, db)
    farm_id = (
        await client.post("/api/v1/farms", json={"name": "Not Yours"}, headers=farmer["headers"])
    ).json()["id"]

    assert (await client.get(f"/api/v1/farms/{farm_id}", headers=intruder_headers)).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/farms/{farm_id}", json={"name": "Hacked"}, headers=intruder_headers
        )
    ).status_code == 404
    assert (await client.delete(f"/api/v1/farms/{farm_id}", headers=intruder_headers)).status_code == 404
    assert (await client.get("/api/v1/farms", headers=intruder_headers)).json() == []


async def test_farms_require_authentication(client):
    assert (await client.get("/api/v1/farms")).status_code == 401


# ---------- fields ----------


async def test_field_create_list_get_update_archive(client, farmer, farm_tree):
    headers = farmer["headers"]
    farm_id = farm_tree["farm"]["id"]
    field = await client.post(
        "/api/v1/fields",
        json={"farm_id": farm_id, "name": "East Plot", "location": {"lat": 24.8, "lng": 85.1}},
        headers=headers,
    )
    assert field.status_code == 201
    body = field.json()
    assert body["location"] == {"lat": 24.8, "lng": 85.1}  # round-trip through storage

    listed = (await client.get(f"/api/v1/fields?farm_id={farm_id}", headers=headers)).json()
    assert [f["name"] for f in listed] == ["North Plot", "East Plot"]

    assert (await client.get(f"/api/v1/fields/{body['id']}", headers=headers)).status_code == 200

    updated = await client.patch(
        f"/api/v1/fields/{body['id']}", json={"name": "Renamed"}, headers=headers
    )
    assert updated.json()["name"] == "Renamed"

    assert (await client.delete(f"/api/v1/fields/{body['id']}", headers=headers)).status_code == 204
    listed = (await client.get(f"/api/v1/fields?farm_id={farm_id}", headers=headers)).json()
    assert [f["name"] for f in listed] == ["North Plot"]


async def test_field_rejects_farm_not_owned(client, db, farmer):
    intruder_headers = await _intruder_headers(client, db, "+919700000300")
    victims_farm = (
        await client.post("/api/v1/farms", json={"name": "Victim Farm"}, headers=farmer["headers"])
    ).json()["id"]

    resp = await client.post(
        "/api/v1/fields",
        json={"farm_id": victims_farm, "name": "Sneaky Field"},
        headers=intruder_headers,
    )
    assert resp.status_code == 404


async def test_field_ownership_protection_on_read(client, db, farmer, farm_tree):
    intruder_headers = await _intruder_headers(client, db, "+919700000400")
    field_id = farm_tree["field"]["id"]
    farm_id = farm_tree["farm"]["id"]
    assert (await client.get(f"/api/v1/fields/{field_id}", headers=intruder_headers)).status_code == 404
    assert (
        await client.get(f"/api/v1/fields?farm_id={farm_id}", headers=intruder_headers)
    ).status_code == 404


async def test_field_validation_rejects_bad_location(client, farmer):
    resp = await client.post(
        "/api/v1/fields",
        json={
            "farm_id": str(uuid.uuid4()),
            "name": "Bad Location",
            "location": {"lat": 123.0, "lng": 85.0},
        },
        headers=farmer["headers"],
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"