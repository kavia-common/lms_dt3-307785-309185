"""
JWT authentication/validation tests.

These tests are intentionally self-contained because the current container snapshot
does not include the FastAPI application modules yet (only test helpers exist).
Once the real app is present, these tests should be updated to import the real
FastAPI `app` and override its auth dependencies.

They validate:
- Unauthenticated access is denied (401)
- Invalid JWT/OIDC token is rejected (401)
- Valid token passes and reaches the endpoint (200)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient


@dataclass(frozen=True)
class AuthContext:
    """Simple auth context used by the stubbed auth dependency."""
    sub: str
    roles: tuple[str, ...]


security = HTTPBearer(auto_error=False)


def _validate_bearer_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthContext:
    """
    Validate a bearer token (stub).

    - Missing credentials -> 401
    - Wrong token -> 401
    - "good-token" -> authenticated user context
    """
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    if creds.credentials != "good-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return AuthContext(sub="user-123", roles=("Learner",))


def _build_stub_app() -> FastAPI:
    """Create a minimal FastAPI app with a protected endpoint."""
    app = FastAPI(title="Auth stub app")

    @app.get("/protected")
    def protected_route(ctx: AuthContext = Depends(_validate_bearer_token)) -> dict:
        return {"sub": ctx.sub, "roles": list(ctx.roles)}

    return app


@pytest.fixture()
def client() -> TestClient:
    """Test client for the stub app."""
    return TestClient(_build_stub_app())


def test_protected_endpoint_denies_unauthenticated(client: TestClient) -> None:
    """Protected endpoint should deny missing Authorization header with 401."""
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert resp.json()["detail"] in ("Missing bearer token", "Not authenticated")


def test_protected_endpoint_denies_invalid_token(client: TestClient) -> None:
    """Protected endpoint should deny an invalid token with 401."""
    resp = client.get("/protected", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"


def test_protected_endpoint_accepts_valid_token(client: TestClient) -> None:
    """Protected endpoint should accept a valid token and return subject/roles."""
    resp = client.get("/protected", headers={"Authorization": "Bearer good-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["sub"] == "user-123"
    assert "Learner" in data["roles"]
