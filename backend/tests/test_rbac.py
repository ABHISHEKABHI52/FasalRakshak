"""RBAC tests (docs/03 §2) + database connectivity (docs/08 §10)."""

import pytest
from sqlalchemy import text

from app.models.role import RoleName
from tests.conftest import create_user_with_role, role_count


async def test_database_connection_select_1(db):
    result = await db.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


async def test_five_system_roles_seeded(db):
    assert await role_count(db) == 5


async def test_rbac_denies_farmer_on_admin_endpoint(client, db):
    await create_user_with_role(db, "+919876500001", RoleName.FARMER)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919876500001", "password": "password123"}
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "forbidden"
    assert body["details"]["required_roles"] == ["ADMIN"]


async def test_rbac_allows_admin_on_admin_endpoint(client, db):
    await create_user_with_role(db, "+919876500002", RoleName.ADMIN)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": "+919876500002", "password": "password123"}
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_rbac_requires_authentication(client, db):
    resp = await client.get("/api/v1/admin/ping")
    assert resp.status_code == 401


@pytest.mark.parametrize(
    ("role", "phone"),
    [
        (RoleName.EXTENSION_WORKER, "+919876510001"),
        (RoleName.EXPERT, "+919876510002"),
        (RoleName.OFFICER, "+919876510003"),
    ],
)
async def test_rbac_denies_every_non_admin_role_on_admin_endpoint(client, db, role, phone):
    """All five roles are enforced: FARMER/EXTENSION_WORKER/EXPERT/OFFICER are denied, ADMIN allowed."""
    await create_user_with_role(db, phone, role)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": phone, "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["details"]["required_roles"] == ["ADMIN"]


@pytest.mark.parametrize(
    ("role", "phone"),
    [
        (RoleName.FARMER, "+919876520001"),
        (RoleName.EXTENSION_WORKER, "+919876520002"),
        (RoleName.EXPERT, "+919876520003"),
        (RoleName.OFFICER, "+919876520004"),
        (RoleName.ADMIN, "+919876520005"),
    ],
)
async def test_every_role_receives_its_role_in_profile(client, db, role, phone):
    """Role assignment survives the full round trip: JWT -> /me."""
    await create_user_with_role(db, phone, role)
    login = await client.post(
        "/api/v1/auth/login", json={"phone_or_email": phone, "password": "password123"}
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["roles"] == [role.value]
