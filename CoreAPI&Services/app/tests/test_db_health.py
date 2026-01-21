from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_db_health_ok(monkeypatch) -> None:
    # Enable mongo in settings, but we will bypass real motor calls by mocking mongo_ping.
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DBNAME", "lms")
    monkeypatch.setenv("MONGODB_TLS", "false")

    async def _ok_ping(_app) -> None:
        return None

    monkeypatch.setattr("app.api.routers.health.mongo_ping", _ok_ping)

    app = create_app()
    client = TestClient(app)

    resp = client.get("/health/db")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["duration_ms"] >= 0
    assert payload["error"] is None


def test_db_health_failed(monkeypatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DBNAME", "lms")
    monkeypatch.setenv("MONGODB_TLS", "false")

    async def _fail_ping(_app) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr("app.api.routers.health.mongo_ping", _fail_ping)

    app = create_app()
    client = TestClient(app)

    resp = client.get("/health/db")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "failed"
    assert payload["duration_ms"] >= 0
    assert "db down" in (payload["error"] or "")
