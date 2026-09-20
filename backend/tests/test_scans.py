"""Phase 2 scan tests: creation, idempotency, ownership, lifecycle, history (docs/08 §3)."""

import uuid
from datetime import datetime, timezone

from app.models.role import RoleName
from tests.conftest import create_user_with_role


def _scan_payload(tree, plant_part: str = "leaf") -> dict:
    return {
        "field_id": tree["field"]["id"],
        "crop_cycle_id": tree["cycle"]["id"],
        "plant_part": plant_part,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "client_scan_uuid": str(uuid.uuid4()),
    }


async def test_scan_create_returns_pending_image(client, farmer, farm_tree):
    resp = await client.post(
        "/api/v1/scans", json=_scan_payload(farm_tree), headers=farmer["headers"]
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending_image"
    assert resp.json()["scan_id"]


async def test_scan_idempotency_returns_original_scan(client, farmer, farm_tree):
    """Same client_scan_uuid must NOT create a duplicate (docs/08 §3, FR-C3)."""
    payload = _scan_payload(farm_tree)
    first = await client.post("/api/v1/scans", json=payload, headers=farmer["headers"])
    assert first.status_code == 201

    replay = await client.post("/api/v1/scans", json=payload, headers=farmer["headers"])
    assert replay.status_code == 200  # replay, not a new resource
    assert replay.json()["scan_id"] == first.json()["scan_id"]

    history = (await client.get("/api/v1/scans", headers=farmer["headers"])).json()
    assert len(history["items"]) == 1  # exactly one scan exists


async def test_scan_idempotency_rejects_another_farmers_key_without_leaking(
    client, db, farmer, farm_tree
):
    """A client_scan_uuid owned by another farmer must be indistinguishable from unknown."""
    await create_user_with_role(db, "+919700000700", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919700000700", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    payload = _scan_payload(farm_tree)
    created = await client.post("/api/v1/scans", json=payload, headers=farmer["headers"])
    assert created.status_code == 201

    replay = await client.post("/api/v1/scans", json=payload, headers=intruder_headers)
    assert replay.status_code == 404  # never 200 with the victim's scan id


async def test_scan_ownership_protection_on_detail_and_history(client, db, farmer, farm_tree):
    await create_user_with_role(db, "+919700000800", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919700000800", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    scan_id = (
        await client.post(
            "/api/v1/scans", json=_scan_payload(farm_tree), headers=farmer["headers"]
        )
    ).json()["scan_id"]

    assert (await client.get(f"/api/v1/scans/{scan_id}", headers=intruder_headers)).status_code == 404
    assert (await client.get("/api/v1/scans", headers=intruder_headers)).json()["items"] == []


async def test_scan_rejects_cross_field_crop_cycle(client, farmer, farm_tree):
    """A crop cycle from another field must not be attachable to this scan."""
    other_field = (
        await client.post(
            "/api/v1/fields",
            json={"farm_id": farm_tree["farm"]["id"], "name": "Other Plot"},
            headers=farmer["headers"],
        )
    ).json()
    payload = _scan_payload(farm_tree)
    payload["field_id"] = other_field["id"]  # cycle belongs to a different field
    resp = await client.post("/api/v1/scans", json=payload, headers=farmer["headers"])
    assert resp.status_code == 409
    assert resp.json()["code"] == "cycle_field_mismatch"


async def test_scan_history_pagination(client, farmer, farm_tree):
    headers = farmer["headers"]
    for _ in range(3):
        resp = await client.post(
            "/api/v1/scans", json=_scan_payload(farm_tree), headers=headers
        )
        assert resp.status_code == 201

    page1 = (await client.get("/api/v1/scans?limit=2", headers=headers)).json()
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None

    page2 = (
        await client.get(
            f"/api/v1/scans?limit=2&cursor={page1['next_cursor']}", headers=headers
        )
    ).json()
    assert len(page2["items"]) == 1
    assert page2["next_cursor"] is None
    seen_ids = {item["id"] for item in page1["items"]} | {item["id"] for item in page2["items"]}
    assert len(seen_ids) == 3


async def test_scan_history_filter_by_field(client, farmer, farm_tree):
    headers = farmer["headers"]
    other_field = (
        await client.post(
            "/api/v1/fields",
            json={"farm_id": farm_tree["farm"]["id"], "name": "Filter Plot"},
            headers=headers,
        )
    ).json()
    other_cycle = (
        await client.post(
            "/api/v1/crop-cycles",
            json={
                "field_id": other_field["id"],
                "crop_id": farm_tree["tomato"]["id"],
                "sowing_date": "2026-02-01",
            },
            headers=headers,
        )
    ).json()
    await client.post("/api/v1/scans", json=_scan_payload(farm_tree), headers=headers)
    other_payload = _scan_payload(farm_tree)
    other_payload["field_id"] = other_field["id"]
    other_payload["crop_cycle_id"] = other_cycle["id"]
    other_scan = await client.post("/api/v1/scans", json=other_payload, headers=headers)
    assert other_scan.status_code == 201

    for_field = (
        await client.get(f"/api/v1/scans?field_id={other_field['id']}", headers=headers)
    ).json()["items"]
    assert len(for_field) == 1
    assert for_field[0]["field_id"] == other_field["id"]


async def test_scan_upload_accepted_image_runs_analysis(demo_analysis, client, farmer, farm_tree, good_test_image):
    """Accepted-quality image proceeds to deterministic demo analysis."""
    scan = await client.post("/api/v1/scans", json=_scan_payload(farm_tree), headers=farmer["headers"])
    scan_id = scan.json()["scan_id"]

    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"file": good_test_image},
        headers=farmer["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    # Quality gate must pass
    assert data["quality"]["category"] in ("good", "acceptable")
    # Analysis must run with the demo classifier
    assert data["analysis"]["model_name"] == "deterministic_demo_classifier"
    assert data["analysis"]["is_mock"] is False


async def test_scan_upload_rejected_image_blocks_analysis(demo_analysis, client, farmer, farm_tree, bad_test_image):
    """Rejected-quality image must NOT proceed to analysis."""
    scan = await client.post("/api/v1/scans", json=_scan_payload(farm_tree), headers=farmer["headers"])
    scan_id = scan.json()["scan_id"]

    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"file": bad_test_image},
        headers=farmer["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    # Quality gate must reject
    assert data["quality"]["usable"] is False
    # Analysis must NOT run
    assert data["analysis"]["status"] == "insufficient_evidence"
    assert data["analysis"]["model_name"] == "deterministic_demo_classifier"