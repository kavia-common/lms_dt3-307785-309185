from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.main import create_app


def test_auth_debug_returns_principal_when_stub_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_STUB", "true")
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


def test_auth_debug_returns_501_when_stub_disabled(monkeypatch) -> None:
    # Ensure we explicitly disable for this test even if local env has it enabled.
    monkeypatch.setenv("AUTH_STUB", "false")
    app = create_app()
    client = TestClient(app)

    resp = client.get("/auth/debug")
    assert resp.status_code == 501
    assert "not implemented" in resp.json()["message"].lower() or "not implemented" in resp.json()[
        "message"
    ].lower()
