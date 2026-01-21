from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.routers.users import get_users_service
from app.core.config import clear_settings_cache
from app.main import create_app


def test_users_list_requires_auth(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "false")
    # minimal config (won't be used because request is missing bearer)
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")
    monkeypatch.setenv("OIDC_JWKS_URI", "https://issuer.example/jwks")
    clear_settings_cache()

    app = create_app()

    # Avoid Mongo access: override the DB dependency and the service provider.
    from app.core.db import get_db
    from app.tests.test_helpers import override_db

    class _FakeDB:
        pass

    app.dependency_overrides[get_db] = override_db(_FakeDB())

    class _FakeUsersService:
        async def list_users(self, *, skip: int = 0, limit: int = 50):
            return {"items": [], "total": 0, "skip": skip, "limit": limit}

    app.dependency_overrides[get_users_service] = lambda: _FakeUsersService()

    client = TestClient(app)
    resp = client.get("/users")
    assert resp.status_code == 401
    assert "bearer" in (resp.headers.get("www-authenticate") or "").lower()


def test_users_list_forbidden_without_read_role(monkeypatch) -> None:
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

    # Stub principal with no roles -> should fail RBAC
    resp = client.get("/users", headers={"X-Auth-Subject": "u1", "X-Auth-Roles": ""})
    assert resp.status_code == 403


def test_users_list_allowed_with_learner_role(monkeypatch) -> None:
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

    resp = client.get("/users", headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Learner"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_users_delete_requires_admin(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "true")
    clear_settings_cache()
    app = create_app()

    class _FakeUsersService:
        async def delete_user(self, user_id: str):
            return {"deleted": True, "id": user_id}

    app.dependency_overrides[get_users_service] = lambda: _FakeUsersService()
    client = TestClient(app)

    # Instructor is not enough for delete (admin-only)
    resp = client.delete(
        "/users/507f1f77bcf86cd799439011",
        headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Instructor"},
    )
    assert resp.status_code == 403

    # Admin is enough
    resp2 = client.delete(
        "/users/507f1f77bcf86cd799439011",
        headers={"X-Auth-Subject": "u1", "X-Auth-Roles": "Admin"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["deleted"] is True
