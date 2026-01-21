from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from bson import ObjectId
from pymongo.errors import InvalidId


# PUBLIC_INTERFACE
def to_object_id(value: str) -> ObjectId | None:
    """Convert a string to a BSON ObjectId.

    Args:
        value: String representation of ObjectId.

    Returns:
        ObjectId | None: Parsed ObjectId, or None if invalid/empty.
    """
    if not value:
        return None
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


# PUBLIC_INTERFACE
def serialize_mongo_doc(doc: Mapping[str, Any]) -> dict[str, Any]:
    """Serialize a MongoDB document for JSON/Pydantic responses.

    - Converts `_id` -> `id` as `str`
    - Converts ObjectId values anywhere in the document to `str`
    - Leaves datetime values untouched (FastAPI/Pydantic will serialize)

    Args:
        doc: MongoDB document.

    Returns:
        dict[str, Any]: JSON-friendly dict.
    """

    def _convert(v: Any) -> Any:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, dict):
            return {k: _convert(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_convert(x) for x in v]
        return v

    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return {k: _convert(v) for k, v in out.items()}


# PUBLIC_INTERFACE
def not_deleted_filter() -> dict[str, Any]:
    """Filter to exclude soft-deleted documents."""
    return {"deleted_at": None}


# PUBLIC_INTERFACE
def soft_delete_update(now: datetime) -> dict[str, Any]:
    """Mongo update payload to soft-delete a document."""
    return {"$set": {"deleted_at": now, "updated_at": now}}
