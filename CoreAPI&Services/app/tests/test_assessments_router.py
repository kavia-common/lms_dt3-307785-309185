from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.routers.assessments import get_assessments_service
from app.main import create_app


def test_assessments_list_ok_with_pagination() -> None:
    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeAssessmentsService:
        async def list_assessments(self, *, skip: int = 0, limit: int = 50):
            return {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439013",
                        "title": "Quiz 1",
                        "course_id": "507f1f77bcf86cd799439099",
                        "module_id": None,
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "deleted_at": None,
                    }
                ],
                "total": 1,
                "skip": skip,
                "limit": limit,
            }

    app.dependency_overrides[get_assessments_service] = lambda: _FakeAssessmentsService()

    client = TestClient(app)
    resp = client.get("/assessments?skip=2&limit=3")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["skip"] == 2
    assert payload["limit"] == 3
    assert payload["items"][0]["title"] == "Quiz 1"


def test_assessments_create_returns_201() -> None:
    app = create_app()
    now = datetime.now(tz=timezone.utc)

    class _FakeAssessmentsService:
        async def create_assessment(self, payload):
            return {
                "id": "507f1f77bcf86cd799439013",
                "title": payload.title,
                "course_id": payload.course_id,
                "module_id": payload.module_id,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "deleted_at": None,
            }

    app.dependency_overrides[get_assessments_service] = lambda: _FakeAssessmentsService()

    client = TestClient(app)
    resp = client.post(
        "/assessments",
        json={"title": "Quiz 1", "course_id": "507f1f77bcf86cd799439099", "module_id": None},
    )
    assert resp.status_code == 201
    payload = resp.json()
    assert payload["title"] == "Quiz 1"
    assert payload["course_id"] == "507f1f77bcf86cd799439099"


def test_assessments_get_not_found() -> None:
    from fastapi import HTTPException, status

    app = create_app()

    class _FakeAssessmentsService:
        async def get_assessment(self, _assessment_id: str):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    app.dependency_overrides[get_assessments_service] = lambda: _FakeAssessmentsService()

    client = TestClient(app)
    resp = client.get("/assessments/507f1f77bcf86cd799439013")
    assert resp.status_code == 404
