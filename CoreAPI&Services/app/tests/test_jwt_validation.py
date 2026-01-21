from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import clear_settings_cache
from app.main import create_app


def test_real_auth_mode_requires_bearer(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "false")
    # minimal config (won't be used because request is missing bearer)
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")
    monkeypatch.setenv("OIDC_JWKS_URI", "https://issuer.example/jwks")
    clear_settings_cache()

    app = create_app()
    client = TestClient(app)

    resp = client.get("/auth/debug")
    assert resp.status_code == 401
    assert "bearer" in (resp.headers.get("www-authenticate") or "").lower()


def test_real_auth_mode_uses_verifier(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "false")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")
    monkeypatch.setenv("OIDC_JWKS_URI", "https://issuer.example/jwks")
    monkeypatch.setenv("OIDC_AUDIENCE", "api://example")
    monkeypatch.setenv("OIDC_ALGORITHMS", "RS256")
    clear_settings_cache()

    # Patch the verification function to avoid JWKS / crypto.
    from app.schemas.security import Principal

    def _fake_verify(token: str, *, settings):
        assert token == "testtoken"
        return Principal(subject="sub-123", email="user@example.com", roles=[])

    monkeypatch.setattr("app.core.security.oidc.verify_access_token", _fake_verify)

    app = create_app()
    client = TestClient(app)

    resp = client.get("/auth/debug", headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["subject"] == "sub-123"
    assert payload["email"] == "user@example.com"
