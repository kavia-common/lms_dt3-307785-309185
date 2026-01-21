"""
Integration tests for app.main:app routers and RBAC behaviors.

These tests import the real FastAPI app (`app.main:app`) and assert:
- 401 when no Authorization token is provided (no overrides)
- 403 when authenticated principal lacks required role
- 200 when authenticated principal has sufficient role

We avoid external services by overriding `app.api.deps.get_current_principal` to
inject Principals with specific roles.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Principal, Role, get_current_principal
from app.main import app as fastapi_app


def _principal_with_roles(*roles: Role) -> Principal:
    """Create a minimal Principal for tests with the provided roles."""
    return Principal(
        sub="test-user",
        oid="test-user",
        email="test@example.com",
        roles=list(roles),
    )


def _override_principal(principal: Principal) -> Callable[[], Principal]:
    """Return a dependency override callable yielding the provided principal."""

    def _dep() -> Principal:
        return principal

    return _dep


@pytest.fixture()
def client() -> TestClient:
    """Create an isolated TestClient with dependency overrides cleared."""
    fastapi_app.dependency_overrides = {}
    return TestClient(fastapi_app)


@pytest.fixture()
def client_readonly() -> TestClient:
    """Client authenticated as a READ-only principal (LEARNER)."""
    fastapi_app.dependency_overrides = {}
    fastapi_app.dependency_overrides[get_current_principal] = _override_principal(
        _principal_with_roles(Role.LEARNER)
    )
    return TestClient(fastapi_app)


@pytest.fixture()
def client_admin() -> TestClient:
    """Client authenticated as an ADMIN principal."""
    fastapi_app.dependency_overrides = {}
    fastapi_app.dependency_overrides[get_current_principal] = _override_principal(
        _principal_with_roles(Role.ADMIN)
    )
    return TestClient(fastapi_app)


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/users/"),
        ("get", "/content/"),
        ("get", "/assessments/"),
    ],
)
def test_unauthenticated_requests_to_list_endpoints_return_401(
    client: TestClient, method: str, path: str
) -> None:
    """Unauthenticated access should be denied with 401 for list endpoints."""
    resp = getattr(client, method)(path)
    assert resp.status_code == 401


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/users/", {"name": "New User"}),
        ("post", "/content/", {"title": "New Content"}),
        ("post", "/assessments/", {"name": "New Assessment"}),
    ],
)
def test_readonly_principal_cannot_create_resources_returns_403(
    client_readonly: TestClient, method: str, path: str, body: Dict[str, Any]
) -> None:
    """READ-only (LEARNER) principal should be forbidden on WRITE endpoints."""
    resp = getattr(client_readonly, method)(path, json=body)
    assert resp.status_code == 403
    assert resp.json().get("detail") == "Forbidden"


@pytest.mark.parametrize(
    "path",
    [
        "/users/u1",
        "/content/c1",
        "/assessments/a1",
    ],
)
def test_readonly_principal_cannot_delete_resources_returns_403(
    client_readonly: TestClient, path: str
) -> None:
    """READ-only (LEARNER) principal should be forbidden on ADMIN delete endpoints."""
    resp = client_readonly.delete(path)
    assert resp.status_code == 403
    assert resp.json().get("detail") == "Forbidden"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/users/", None),
        ("get", "/content/", None),
        ("get", "/assessments/", None),
        ("post", "/users/", {"name": "Admin Created User"}),
        ("post", "/content/", {"title": "Admin Created Content"}),
        ("post", "/assessments/", {"name": "Admin Created Assessment"}),
        ("delete", "/users/u1", None),
        ("delete", "/content/c1", None),
        ("delete", "/assessments/a1", None),
    ],
)
def test_admin_principal_can_access_all_users_content_assessments_endpoints_returns_200(
    client_admin: TestClient,
    method: str,
    path: str,
    body: Optional[Dict[str, Any]],
) -> None:
    """ADMIN principal should be allowed for READ/WRITE/ADMIN endpoints."""
    if body is None:
        resp = getattr(client_admin, method)(path)
    else:
        resp = getattr(client_admin, method)(path, json=body)

    assert resp.status_code == 200
