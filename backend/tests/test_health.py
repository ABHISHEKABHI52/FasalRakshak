"""Health + readiness endpoint tests (docs/08 §10)."""


async def test_health_ok(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "FasalRakshak"


async def test_ready_reports_database(client):
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert resp.json()["db"] is True


async def test_request_id_header_echoed(client):
    resp = await client.get("/api/v1/health", headers={"X-Request-ID": "test-req-1"})
    assert resp.headers.get("X-Request-ID") == "test-req-1"


async def test_unknown_route_returns_stable_error_shape(client):
    resp = await client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "not_found"
    assert "message_key" in body


async def test_ready_returns_503_when_database_unavailable(client, monkeypatch):
    """Readiness must reflect the real dependency state — never a hard-coded True."""
    from app.api.v1 import health as health_module

    async def _unavailable() -> bool:
        return False

    monkeypatch.setattr(health_module, "check_database_connection", _unavailable)
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 503
    assert resp.json()["db"] is False


async def test_error_responses_do_not_leak_internals(monkeypatch):
    """Unexpected failures return a generic envelope, never a stack trace.

    Starlette's ServerErrorMiddleware always re-raises after sending the error
    response (for server-side logging), and httpx's ASGITransport re-raises app
    exceptions by default. A real HTTP client only sees the response, so the
    re-raise is disabled here to assert the actual client-visible contract.
    """
    from httpx import ASGITransport, AsyncClient

    from app.api.v1 import health as health_module
    from app.main import app

    async def _boom() -> bool:
        raise RuntimeError("secret-database-dsn-and-traceback")

    monkeypatch.setattr(health_module, "check_database_connection", _boom)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as raw_client:
        resp = await raw_client.get("/api/v1/ready")
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "internal_error"
    assert body["message_key"] == "errors.internal_error"
    assert "secret-database-dsn" not in resp.text
    assert "Traceback" not in resp.text
