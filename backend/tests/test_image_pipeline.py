"""Image upload pipeline tests: validation, quality gate, analysis contract.

Covers docs/03 AC-01/AC-03, docs/08 §3 upload contract, docs/12 §3 upload safety.
"""

import io
import uuid
from datetime import datetime, timezone

from PIL import Image

from tests.conftest import make_image_bytes


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scan_payload(tree, client_uuid: uuid.UUID | None = None) -> dict:
    return {
        "field_id": tree["field"]["id"],
        "crop_cycle_id": tree["cycle"]["id"],
        "plant_part": "leaf",
        "captured_at": _now_iso(),
        "client_scan_uuid": str(client_uuid or uuid.uuid4()),
    }


async def _create_scan(client, farmer, tree) -> str:
    resp = await client.post(
        "/api/v1/scans", json=_scan_payload(tree), headers=farmer["headers"]
    )
    assert resp.status_code == 201
    return resp.json()["scan_id"]


# ---------- upload validation (docs/12 §3) ----------


async def test_valid_image_upload_completes_with_insufficient_evidence(client, farmer, farm_tree):
    """Default Phase 2 behaviour: pipeline completes with honest INSUFFICIENT_EVIDENCE."""
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("leaf.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["image_id"]
    assert body["quality"]["category"] == "good"
    assert body["quality"]["usable"] is True
    assert body["analysis"]["status"] == "insufficient_evidence"  # first-class outcome
    assert body["analysis"]["is_mock"] is False
    assert body["analysis"]["primary_label_code"] is None  # never a fabricated disease

    detail = (await client.get(f"/api/v1/scans/{scan_id}", headers=farmer["headers"])).json()
    assert detail["status"] == "completed"
    assert detail["quality"]["quality_score"] >= 80
    assert detail["analysis"]["model_name"] == "unavailable"
    assert "Phase 3" in (detail["analysis"]["note"] or "")  # honest wording, no fake AI


async def test_unusable_image_returns_422_and_never_runs_analysis(client, farmer, farm_tree):
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("dark.jpg", make_image_bytes("dark"), "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "quality_unusable"
    assert "too_dark" in body["details"]["reasons"]
    assert body["details"]["quality_score"] < 40

    detail = (await client.get(f"/api/v1/scans/{scan_id}", headers=farmer["headers"])).json()
    assert detail["status"] == "quality_rejected"  # explicit failure state
    assert detail["status_reason"] == "image_quality_unusable"
    assert detail["analysis"]["status"] == "insufficient_evidence"
    assert detail["analysis"]["primary_label_code"] is None
    assert detail["analysis"]["is_mock"] is False


async def test_low_resolution_image_rejected_with_retake_guidance(client, farmer, farm_tree):
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("tiny.jpg", make_image_bytes("low_res"), "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 422
    hints = [item["hint"] for item in resp.json()["details"]["reasons_detail"]]
    assert any("closer" in (hint or "") for hint in hints)  # actionable guidance


async def test_upload_rejects_non_image_content(client, farmer, farm_tree):
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("payload.jpg", b"MZ\x90\x00 this is not an image", "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 415
    assert resp.json()["code"] == "unsupported_media"


async def test_upload_rejects_oversized_payload(client, farmer, farm_tree):
    """Oversized bodies are rejected with 413 — via the documented override hook."""
    from app.api.deps import get_max_upload_bytes
    from app.main import app

    app.dependency_overrides[get_max_upload_bytes] = lambda: 1000
    try:
        scan_id = await _create_scan(client, farmer, farm_tree)
        big = make_image_bytes("good") + b"\x00" * 2000  # >1000 bytes of a valid image
        resp = await client.post(
            f"/api/v1/scans/{scan_id}/image",
            files={"image": ("big.jpg", big, "image/jpeg")},
            headers=farmer["headers"],
        )
        assert resp.status_code == 413
        assert resp.json()["code"] == "payload_too_large"
    finally:
        app.dependency_overrides.pop(get_max_upload_bytes, None)


async def test_upload_rejects_corrupted_image(client, farmer, farm_tree):
    raw = make_image_bytes("good")
    corrupted = raw[: len(raw) // 2]  # truncated JPEG
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("corrupt.jpg", corrupted, "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code in (400, 422)
    assert resp.json()["code"] in {"invalid_image", "quality_unusable"}


async def test_upload_ownership_protection(client, db, farmer, farm_tree):
    from app.models.role import RoleName
    from tests.conftest import create_user_with_role

    await create_user_with_role(db, "+919700000900", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919700000900", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("leaf.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=intruder_headers,
    )
    assert resp.status_code == 404


async def test_image_download_requires_ownership(client, farmer, farm_tree):
    scan_id = await _create_scan(client, farmer, farm_tree)
    await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("leaf.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=farmer["headers"],
    )
    resp = await client.get(f"/api/v1/scans/{scan_id}/image", headers=farmer["headers"])
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    Image.open(io.BytesIO(resp.content)).verify()  # stored file is a readable image


# ---------- analysis contract + integration ----------


async def test_mock_analysis_is_clearly_labelled_and_produces_diagnosis(
    client, farmer, farm_tree, mock_analysis
):
    """The deterministic TEST double must be flagged is_mock — never sold as real AI."""
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("leaf.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["analysis"]["status"] == "diagnosed"
    assert body["analysis"]["is_mock"] is True
    assert body["analysis"]["primary_label_code"] == "test_disease"

    detail = (await client.get(f"/api/v1/scans/{scan_id}", headers=farmer["headers"])).json()
    assert detail["analysis"]["is_mock"] is True
    assert detail["analysis"]["note"] and "NOT a real model prediction" in detail["analysis"]["note"]


async def test_full_farmer_flow_integration(client, farmer, farm_tree, mock_analysis):
    """farmer → farm → field → crop → cycle → scan → image → quality → outcome → history."""
    headers = farmer["headers"]
    scan_id = await _create_scan(client, farmer, farm_tree)
    await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("leaf.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=headers,
    )

    history = (await client.get("/api/v1/scans", headers=headers)).json()
    assert history["items"][0]["id"] == scan_id
    assert history["items"][0]["status"] == "completed"
    assert history["items"][0]["quality"] is not None
    assert history["items"][0]["analysis"]["status"] == "diagnosed"

    replay = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("again.jpg", make_image_bytes("good"), "image/jpeg")},
        headers=headers,
    )
    assert replay.status_code == 409
    assert replay.json()["code"] == "image_already_accepted"


async def test_blurry_image_proceeds_with_warning(client, farmer, farm_tree, mock_analysis):
    """docs/00 §16: a blurred but informative image proceeds with a visible warning."""
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("blurry.jpg", make_image_bytes("blurry"), "image/jpeg")},
        headers=farmer["headers"],
    )
    body = resp.json()
    assert resp.status_code == 202
    assert body["quality"]["usable"] is True  # enough evidence remains to continue
    assert "blurry" in [reason["code"] for reason in body["quality"]["reasons"]]


async def test_upload_rejects_executable_disguised_as_jpeg(client, farmer, farm_tree):
    """Filename extension is never trusted — magic bytes decide (docs/12 §3)."""
    scan_id = await _create_scan(client, farmer, farm_tree)
    resp = await client.post(
        f"/api/v1/scans/{scan_id}/image",
        files={"image": ("innocent.jpg", b"#!/bin/sh\necho pwned\n", "image/jpeg")},
        headers=farmer["headers"],
    )
    assert resp.status_code == 415