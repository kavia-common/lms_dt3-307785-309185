from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.routers.users import get_users_service
from app.core.config import clear_settings_cache
from app.main import create_app


def test_users_list_ok_with_pagination(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "true")
    clear_settings_cache()

    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeUsersService:
        async def list_users(self, *, skip: int = 0, limit: int = 50):
            return {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "name": "Alice",
                        "email": "alice@example.com",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "deleted_at": None,
                    }
                ],
                "total": 1,
                "skip": skip,
                "limit": limit,
            }

    app.dependency_overrides[get_users_service] = lambda: _FakeUsersService()

    client = TestClient(app)
    resp = client.get(
        "/users?skip=5&limit=10",
        headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Learner"},
    )
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["total"] == 1
    assert payload["skip"] == 5
    assert payload["limit"] == 10
    assert len(payload["items"]) == 1
    assert payload["items"][0]["email"] == "alice@example.com"


def test_users_create_returns_201(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "true")
    clear_settings_cache()

    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeUsersService:
        async def create_user(self, payload):
            return {
                "id": "507f1f77bcf86cd799439011",
                "name": payload.name,
                "email": payload.email,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "deleted_at": None,
            }

    app.dependency_overrides[get_users_service] = lambda: _FakeUsersService()

    client = TestClient(app)
    resp = client.post(
        "/users",
        json={"name": "Bob", "email": "bob@example.com"},
        headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Instructor"},
    )
    assert resp.status_code == 201
    payload = resp.json()
    assert payload["name"] == "Bob"
    assert payload["email"] == "bob@example.com"
    assert "id" in payload


def test_users_get_not_found(monkeypatch) -> None:
    from fastapi import HTTPException, status

    monkeypatch.setenv("AUTH_STUB", "true")
    clear_settings_cache()

    app = create_app()

    class _FakeUsersService:
        async def get_user(self, _user_id: str):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    app.dependency_overrides[get_users_service] = lambda: _FakeUsersService()

    client = TestClient(app)
    resp = client.get(
        "/users/507f1f77bcf86cd799439011",
        headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Learner"},
    )
    assert resp.status_code == 404
