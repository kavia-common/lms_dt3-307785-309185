from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import create_app


def test_content_list_ok_with_pagination(monkeypatch) -> None:
    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeContentService:
        async def list_content(self, *, skip: int = 0, limit: int = 50):
            return {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439012",
                        "title": "Intro",
                        "slug": "intro",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "deleted_at": None,
                    }
                ],
                "total": 1,
                "skip": skip,
                "limit": limit,
            }

    monkeypatch.setattr(
        "app.api.routers.content.get_content_service", lambda _request: _FakeContentService()
    )

    client = TestClient(app)
    resp = client.get("/content?skip=0&limit=1")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["slug"] == "intro"


def test_content_create_returns_201(monkeypatch) -> None:
    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeContentService:
        async def create_content(self, payload):
            return {
                "id": "507f1f77bcf86cd799439012",
                "title": payload.title,
                "slug": payload.slug,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "deleted_at": None,
            }

    monkeypatch.setattr(
        "app.api.routers.content.get_content_service", lambda _request: _FakeContentService()
    )

    client = TestClient(app)
    resp = client.post("/content", json={"title": "Intro", "slug": "intro"})
    assert resp.status_code == 201
    payload = resp.json()
    assert payload["slug"] == "intro"


def test_content_get_not_found(monkeypatch) -> None:
    from fastapi import HTTPException, status

    app = create_app()

    class _FakeContentService:
        async def get_content(self, _content_id: str):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found.")

    monkeypatch.setattr(
        "app.api.routers.content.get_content_service", lambda _request: _FakeContentService()
    )

    client = TestClient(app)
    resp = client.get("/content/507f1f77bcf86cd799439012")
    assert resp.status_code == 404
