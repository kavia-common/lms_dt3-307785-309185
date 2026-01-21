from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_users_list_returns_placeholder_structure(monkeypatch) -> None:
    app = create_app()
    client = TestClient(app)

    resp = client.get("/users")
    assert resp.status_code == 200

    payload = resp.json()
    assert "items" in payload
    assert "total" in payload
    assert isinstance(payload["items"], list)
    assert isinstance(payload["total"], int)

    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1
    first = payload["items"][0]
    assert set(first.keys()) >= {"id", "name", "created_at", "updated_at"}
