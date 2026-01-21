from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.core.mongo_utils import not_deleted_filter, serialize_mongo_doc, soft_delete_update, to_object_id
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentListResponse,
    AssessmentRead,
    AssessmentUpdate,
)


class AssessmentsService:
    """Assessments domain service backed by MongoDB."""

    collection_name = "assessments"
    _indexes_created: bool = False

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db

    async def _ensure_indexes(self) -> None:
        if self.__class__._indexes_created:
            return
        coll = self._db[self.collection_name]
        await coll.create_index([("course_id", ASCENDING), ("module_id", ASCENDING)], name="idx_course_module")
        await coll.create_index([("deleted_at", ASCENDING)], name="idx_deleted_at")
        await coll.create_index([("created_at", ASCENDING)], name="idx_created_at")
        self.__class__._indexes_created = True

    def _doc_to_read(self, doc: dict[str, Any]) -> AssessmentRead:
        return AssessmentRead.model_validate(serialize_mongo_doc(doc))

    # PUBLIC_INTERFACE
    async def create_assessment(self, payload: AssessmentCreate) -> AssessmentRead:
        """Create an assessment.

        Args:
            payload: AssessmentCreate payload.

        Returns:
            AssessmentRead: Created assessment.
        """
        await self._ensure_indexes()
        now = datetime.now(tz=timezone.utc)

        doc = {
            "title": payload.title,
            "course_id": payload.course_id,
            "module_id": payload.module_id,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        res = await self._db[self.collection_name].insert_one(doc)
        created = await self._db[self.collection_name].find_one({"_id": res.inserted_id})
        assert created is not None
        return self._doc_to_read(created)

    # PUBLIC_INTERFACE
    async def get_assessment(self, assessment_id: str) -> AssessmentRead:
        """Get an assessment by id.

        Args:
            assessment_id: Assessment identifier (ObjectId string).

        Returns:
            AssessmentRead: Assessment record.

        Raises:
            HTTPException: 404 if not found.
        """
        oid = to_object_id(assessment_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        doc = await self._db[self.collection_name].find_one({"_id": oid, **not_deleted_filter()})
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        return self._doc_to_read(doc)

    # PUBLIC_INTERFACE
    async def list_assessments(self, *, skip: int = 0, limit: int = 50) -> AssessmentListResponse:
        """List assessments with pagination.

        Args:
            skip: Offset.
            limit: Page size (max 200).

        Returns:
            AssessmentListResponse: Paginated list.
        """
        await self._ensure_indexes()
        limit = max(1, min(int(limit), 200))
        skip = max(0, int(skip))

        coll = self._db[self.collection_name]
        query = not_deleted_filter()

        total = await coll.count_documents(query)
        cursor = coll.find(query).sort("created_at", ASCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)

        return AssessmentListResponse(
            items=[self._doc_to_read(d) for d in docs],
            total=int(total),
            skip=skip,
            limit=limit,
        )

    # PUBLIC_INTERFACE
    async def update_assessment(self, assessment_id: str, payload: AssessmentUpdate) -> AssessmentRead:
        """Update an assessment.

        Args:
            assessment_id: Assessment identifier (ObjectId string).
            payload: Update payload.

        Returns:
            AssessmentRead: Updated assessment.

        Raises:
            HTTPException: 404 if not found.
        """
        await self._ensure_indexes()

        oid = to_object_id(assessment_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        updates: dict[str, Any] = {}
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.course_id is not None:
            updates["course_id"] = payload.course_id
        if payload.module_id is not None:
            updates["module_id"] = payload.module_id

        if not updates:
            return await self.get_assessment(assessment_id)

        now = datetime.now(tz=timezone.utc)
        updates["updated_at"] = now

        coll = self._db[self.collection_name]
        res = await coll.update_one({"_id": oid, **not_deleted_filter()}, {"$set": updates})
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        doc = await coll.find_one({"_id": oid})
        assert doc is not None
        return self._doc_to_read(doc)

    # PUBLIC_INTERFACE
    async def delete_assessment(self, assessment_id: str) -> dict[str, Any]:
        """Soft-delete an assessment.

        Args:
            assessment_id: Assessment identifier (ObjectId string).

        Returns:
            dict: Confirmation payload.

        Raises:
            HTTPException: 404 if not found.
        """
        await self._ensure_indexes()

        oid = to_object_id(assessment_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        now = datetime.now(tz=timezone.utc)
        coll = self._db[self.collection_name]
        res = await coll.update_one({"_id": oid, **not_deleted_filter()}, soft_delete_update(now))
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        return {"deleted": True, "id": assessment_id}
