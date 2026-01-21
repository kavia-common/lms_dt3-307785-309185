from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.core.mongo_utils import not_deleted_filter, serialize_mongo_doc, soft_delete_update, to_object_id
from app.schemas.users import UserCreate, UserListResponse, UserRead, UserUpdate


class UsersService:
    """Users domain service backed by MongoDB."""

    collection_name = "users"
    _indexes_created: bool = False

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db

    async def _ensure_indexes(self) -> None:
        # Idempotent, in-process best-effort (safe even if called multiple times).
        if self.__class__._indexes_created:
            return

        coll = self._db[self.collection_name]
        await coll.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
        await coll.create_index([("deleted_at", ASCENDING)], name="idx_deleted_at")
        await coll.create_index([("created_at", ASCENDING)], name="idx_created_at")
        self.__class__._indexes_created = True

    def _doc_to_read(self, doc: dict[str, Any]) -> UserRead:
        return UserRead.model_validate(serialize_mongo_doc(doc))

    # PUBLIC_INTERFACE
    async def create_user(self, payload: UserCreate) -> UserRead:
        """Create a user.

        Args:
            payload: UserCreate payload.

        Returns:
            UserRead: Created user.

        Raises:
            HTTPException: 409 if email already exists.
        """
        await self._ensure_indexes()
        now = datetime.now(tz=timezone.utc)
        doc = {
            "name": payload.name,
            "email": str(payload.email).lower(),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        try:
            res = await self._db[self.collection_name].insert_one(doc)
        except DuplicateKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from exc

        created = await self._db[self.collection_name].find_one({"_id": res.inserted_id})
        assert created is not None
        return self._doc_to_read(created)

    # PUBLIC_INTERFACE
    async def get_user(self, user_id: str) -> UserRead:
        """Get a user by id.

        Args:
            user_id: User identifier (ObjectId as string).

        Returns:
            UserRead: User record.

        Raises:
            HTTPException: 404 if not found.
        """
        oid = to_object_id(user_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        doc = await self._db[self.collection_name].find_one({"_id": oid, **not_deleted_filter()})
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return self._doc_to_read(doc)

    # PUBLIC_INTERFACE
    async def list_users(self, *, skip: int = 0, limit: int = 50) -> UserListResponse:
        """List users with pagination.

        Args:
            skip: Offset.
            limit: Page size (max 200).

        Returns:
            UserListResponse: Paginated list.
        """
        await self._ensure_indexes()
        limit = max(1, min(int(limit), 200))
        skip = max(0, int(skip))

        coll = self._db[self.collection_name]
        query = not_deleted_filter()

        total = await coll.count_documents(query)
        cursor = coll.find(query).sort("created_at", ASCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)

        return UserListResponse(
            items=[self._doc_to_read(d) for d in docs],
            total=int(total),
            skip=skip,
            limit=limit,
        )

    # PUBLIC_INTERFACE
    async def update_user(self, user_id: str, payload: UserUpdate) -> UserRead:
        """Update a user by id.

        Args:
            user_id: User identifier (ObjectId string).
            payload: Update payload.

        Returns:
            UserRead: Updated user.

        Raises:
            HTTPException: 404 if not found, 409 if email collides.
        """
        await self._ensure_indexes()

        oid = to_object_id(user_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.email is not None:
            updates["email"] = str(payload.email).lower()

        if not updates:
            # No-op update still returns current doc if it exists.
            return await self.get_user(user_id)

        now = datetime.now(tz=timezone.utc)
        updates["updated_at"] = now

        coll = self._db[self.collection_name]
        try:
            res = await coll.update_one(
                {"_id": oid, **not_deleted_filter()},
                {"$set": updates},
            )
        except DuplicateKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from exc

        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        doc = await coll.find_one({"_id": oid})
        assert doc is not None
        return self._doc_to_read(doc)

    # PUBLIC_INTERFACE
    async def delete_user(self, user_id: str) -> dict[str, Any]:
        """Soft-delete a user.

        Args:
            user_id: User identifier (ObjectId string).

        Returns:
            dict: Confirmation payload.

        Raises:
            HTTPException: 404 if not found.
        """
        await self._ensure_indexes()

        oid = to_object_id(user_id)
        if oid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        now = datetime.now(tz=timezone.utc)
        coll = self._db[self.collection_name]
        res = await coll.update_one({"_id": oid, **not_deleted_filter()}, soft_delete_update(now))
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        return {"deleted": True, "id": user_id}
