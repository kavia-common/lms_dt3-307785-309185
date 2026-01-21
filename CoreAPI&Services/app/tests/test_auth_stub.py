from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import clear_settings_cache
from app.main import create_app


def test_auth_debug_returns_principal_when_stub_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "true")
    clear_settings_cache()
    app = create_app()
    client = TestClient(app)

    resp = client.get(
        "/auth/debug",
        headers={
            "X-Auth-Subject": "user-123",
            "X-Auth-Email": "user@example.com",
            "X-Auth-Roles": "Learner,Admin",
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["subject"] == "user-123"
    assert payload["email"] == "user@example.com"
    assert set(payload["roles"]) == {"Learner", "Admin"}


def test_auth_debug_requires_bearer_when_stub_disabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "false")
    # Provide minimal required OIDC config for real auth mode (even though request is missing bearer)
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")
    monkeypatch.setenv("OIDC_JWKS_URI", "https://issuer.example/jwks")
    clear_settings_cache()

    app = create_app()
    client = TestClient(app)

    resp = client.get("/auth/debug")
    assert resp.status_code == 401
    assert "bearer" in (resp.headers.get("www-authenticate") or "").lower()
