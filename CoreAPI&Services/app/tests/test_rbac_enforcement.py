"""
RBAC enforcement tests.

These tests are self-contained because the current container snapshot does not
include the real FastAPI app/routers yet.

They validate:
- A protected admin/users endpoint denies authenticated-but-unauthorized users (403)
- The same endpoint allows users with the required role (200)

Once the real app is present, replace the stub app with imports from the actual
application and use `app.dependency_overrides` + `override_db()` as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient


@dataclass(frozen=True)
class AuthContext:
    """Auth context containing identity and roles/claims."""
    sub: str
    roles: tuple[str, ...]


security = HTTPBearer(auto_error=False)


def _auth_from_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthContext:
    """
    Authenticate and return context based on token (stub mapping).

    Token mapping:
    - "learner-token" -> roles: ["Learner"]
    - "admin-token" -> roles: ["Admin"]
    """
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = creds.credentials
    if token == "learner-token":
        return AuthContext(sub="learner-1", roles=("Learner",))
    if token == "admin-token":
        return AuthContext(sub="admin-1", roles=("Admin",))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_roles(required: Sequence[str]):
    """Factory returning a dependency that enforces at least one required role."""

    def _enforce(ctx: AuthContext = Depends(_auth_from_token)) -> AuthContext:
        if not any(role in ctx.roles for role in required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return ctx

    return _enforce


def _build_stub_app() -> FastAPI:
    """Create a minimal FastAPI app with an RBAC-protected endpoint."""
    app = FastAPI(title="RBAC stub app")

    @app.get("/admin/users")
    def list_users(_: AuthContext = Depends(require_roles(["Admin", "Super Admin"]))) -> dict:
        # Minimal response to prove access control.
        return {"users": [{"id": "u1"}, {"id": "u2"}]}

    return app


@pytest.fixture()
def client() -> TestClient:
    """Test client for the stub RBAC app."""
    return TestClient(_build_stub_app())


def test_users_list_denies_unauthenticated(client: TestClient) -> None:
    """Admin users list should deny missing token."""
    resp = client.get("/admin/users")
    assert resp.status_code == 401


def test_users_list_denies_non_admin_role(client: TestClient) -> None:
    """Admin users list should return 403 when authenticated but lacks role."""
    resp = client.get("/admin/users", headers={"Authorization": "Bearer learner-token"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Forbidden"


def test_users_list_allows_admin_role(client: TestClient) -> None:
    """Admin users list should allow Admin role."""
    resp = client.get("/admin/users", headers={"Authorization": "Bearer admin-token"})
    assert resp.status_code == 200
    body = resp.json()
    assert "users" in body
    assert isinstance(body["users"], list)
    assert len(body["users"]) == 2
