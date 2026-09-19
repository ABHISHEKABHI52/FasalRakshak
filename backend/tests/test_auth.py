"""Authentication flow tests: register, login, /me, errors (docs/08 §1)."""

from app.core.config import Settings
from app.models.role import RoleName
from app.services.user_service import UserService
from tests.conftest import create_user_with_role

REGISTER_PAYLOAD = {
    "phone": "+919876543210",
    "password": "str0ng-passphrase",
    "full_name": "Ramesh Kumar",
    "preferred_language": "hi",
    "district": "Gaya",
    "state": "Bihar",
    "consent_ml_use": True,
}


async def test_register_creates_farmer(client, db):
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["roles"] == [RoleName.FARMER.value]
    assert body["user_id"]


async def test_register_duplicate_phone_conflict(client, db):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    assert resp.json()["code"] == "duplicate_phone"


async def test_register_invalid_phone_validation_error(client, db):
    bad = {**REGISTER_PAYLOAD, "phone": "12345"}
    resp = await client.post("/api/v1/auth/register", json=bad)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "validation_error"
    assert any(f["field"] == "phone" for f in body["details"]["fields"])


async def test_register_short_password_validation_error(client, db):
    bad = {**REGISTER_PAYLOAD, "password": "short"}
    resp = await client.post("/api/v1/auth/register", json=bad)
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


async def test_login_success_returns_token_and_user(client, db):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    # expires_in is the TTL in seconds, not an absolute timestamp (docs/08 §1).
    assert body["expires_in"] == Settings().access_token_expires_seconds
    assert body["user"]["phone"] == REGISTER_PAYLOAD["phone"]
    assert body["user"]["roles"] == [RoleName.FARMER.value]
    assert "fr_refresh" in resp.cookies


async def test_login_wrong_password_is_generic_401(client, db):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": "wrong-password"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "invalid_credentials"
    # Generic message: must not reveal which factor failed.
    assert "password" not in str(body["details"]).lower()


async def test_login_unknown_user_is_generic_401(client, db):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": "+919999000000", "password": "whatever-pass"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_me_with_token(client, db):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Ramesh Kumar"
    assert resp.json()["preferred_language"] == "hi"


async def test_me_without_token_unauthorized(client, db):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "unauthorized"


async def test_me_with_garbage_token_unauthorized(client, db):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


async def test_auth_endpoints_rate_limited(client, db):
    for _ in range(15):  # default limit is 10/min — exceed it
        await client.post("/api/v1/auth/login", json={"phone_or_email": "x", "password": "y"})
    resp = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919999000001", "password": "whatever-pass"}
    )
    assert resp.status_code == 429
    assert resp.json()["code"] == "rate_limited"


async def test_refresh_rotates_token(client, db):
    """Refresh must rotate the refresh token, issue a usable access token,
    and reject reuse of the superseded refresh token (docs/12 §1)."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": REGISTER_PAYLOAD["password"]},
    )
    old_refresh = login.cookies["fr_refresh"]

    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_refresh = refresh_resp.cookies["fr_refresh"]
    assert new_refresh and new_refresh != old_refresh  # rotation happened

    # The new access token authenticates.
    new_access = refresh_resp.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200
    assert me.json()["phone"] == REGISTER_PAYLOAD["phone"]

    # The superseded refresh token is revoked: reuse must fail.
    client.cookies.set("fr_refresh", old_refresh)
    reuse = await client.post("/api/v1/auth/refresh")
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "unauthorized"


async def test_refresh_without_cookie_unauthorized(client, db):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_audit_rows_written(client, db):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": REGISTER_PAYLOAD["password"]},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": REGISTER_PAYLOAD["phone"], "password": "wrong-password"},
    )
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    actions = (
        (await db.execute(select(AuditLog.action))).scalars().all()
    )
    assert "user.register" in actions
    assert "user.login" in actions
    assert "user.login_failed" in actions
