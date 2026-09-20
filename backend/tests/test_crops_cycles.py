"""Phase 2 domain tests: crop catalogue + crop cycles (docs/08 §2)."""

import uuid

from app.models.role import RoleName
from tests.conftest import create_user_with_role


async def test_crop_catalogue_lists_documented_mvp_crops(client, farmer):
    crops = (await client.get("/api/v1/crops", headers=farmer["headers"])).json()
    codes = {crop["code"] for crop in crops}
    assert codes == {"tomato", "potato", "cotton"}
    for crop in crops:
        assert crop["is_supported"] is True
        assert crop["name_hi"]  # localized names present
        assert crop["stage_model"]["seedling_max_days"] > 0


async def test_crop_cycle_create_get_list_update(client, farmer, farm_tree):
    headers = farmer["headers"]
    field_id = farm_tree["field"]["id"]
    tomato_id = farm_tree["tomato"]["id"]

    created = await client.post(
        "/api/v1/crop-cycles",
        json={"field_id": field_id, "crop_id": tomato_id, "sowing_date": "2026-02-01"},
        headers=headers,
    )
    assert created.status_code == 201
    cycle = created.json()
    assert cycle["crop_code"] == "tomato"
    assert cycle["status"] == "active"
    assert cycle["current_stage"] in {"seedling", "vegetative", "flowering", "fruiting", "maturity"}
    assert cycle["stage_updated_at"] is not None  # derived server-side

    fetched = (await client.get(f"/api/v1/crop-cycles/{cycle['id']}", headers=headers)).json()
    assert fetched["id"] == cycle["id"]

    listed = (await client.get(f"/api/v1/crop-cycles?field_id={field_id}", headers=headers)).json()
    assert len(listed) == 2  # farm_tree cycle + this one

    updated = await client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}",
        json={"status": "completed", "expected_harvest_date": "2026-06-01"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"


async def test_crop_cycle_rejects_field_not_owned(client, db, farmer, farm_tree):
    await create_user_with_role(db, "+919700000500", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919700000500", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.post(
        "/api/v1/crop-cycles",
        json={
            "field_id": farm_tree["field"]["id"],
            "crop_id": farm_tree["tomato"]["id"],
            "sowing_date": "2026-02-01",
        },
        headers=intruder_headers,
    )
    assert resp.status_code == 404


async def test_crop_cycle_rejects_unknown_crop(client, farmer, farm_tree):
    resp = await client.post(
        "/api/v1/crop-cycles",
        json={
            "field_id": farm_tree["field"]["id"],
            "crop_id": str(uuid.uuid4()),
            "sowing_date": "2026-02-01",
        },
        headers=farmer["headers"],
    )
    assert resp.status_code == 404


async def test_crop_cycle_rejects_future_sowing(client, farmer, farm_tree):
    resp = await client.post(
        "/api/v1/crop-cycles",
        json={
            "field_id": farm_tree["field"]["id"],
            "crop_id": farm_tree["tomato"]["id"],
            "sowing_date": "2099-01-01",
        },
        headers=farmer["headers"],
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


async def test_crop_cycle_ownership_protection_on_read(client, db, farmer, farm_tree):
    await create_user_with_role(db, "+919700000600", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919700000600", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    cycle_id = farm_tree["cycle"]["id"]
    assert (
        await client.get(f"/api/v1/crop-cycles/{cycle_id}", headers=intruder_headers)
    ).status_code == 404
    field_id = farm_tree["field"]["id"]
    assert (
        await client.get(f"/api/v1/crop-cycles?field_id={field_id}", headers=intruder_headers)
    ).status_code == 404