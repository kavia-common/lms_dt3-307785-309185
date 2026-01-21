from __future__ import annotations

import asyncio
import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.services.assessments import AssessmentsService
from app.services.content import ContentService
from app.services.users import UsersService

logger = logging.getLogger(__name__)


async def _get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError(
            "MongoDB is not configured. Set MONGODB_URI (and optionally MONGODB_DBNAME, MONGODB_TLS)."
        )
    client = AsyncIOMotorClient(settings.mongodb_uri, tls=settings.mongodb_tls)
    return client.get_database(settings.mongodb_dbname)


async def _counts(db: AsyncIOMotorDatabase, *, seed_tag: str) -> dict[str, Any]:
    users_seeded = await db[UsersService.collection_name].count_documents({"seed_tag": seed_tag})
    content_seeded = await db[ContentService.collection_name].count_documents({"seed_tag": seed_tag})
    assessments_seeded = await db[AssessmentsService.collection_name].count_documents({"seed_tag": seed_tag})
    return {
        "users_seeded": int(users_seeded),
        "content_seeded": int(content_seeded),
        "assessments_seeded": int(assessments_seeded),
    }


# PUBLIC_INTERFACE
async def clear_seeded() -> dict[str, Any]:
    """Remove previously seeded sample data from MongoDB (without dropping indexes).

    This script only removes documents created by our seed script (identified by `seed_tag`).
    It does not truncate collections, and it does not drop any collections/indexes.

    Returns:
        dict[str, Any]: Deleted counts per collection.
    """
    seed_tag = "sample_seed_v1"
    db = await _get_db()

    # Delete only seeded docs. Keep indexes and non-seeded data intact.
    users_res = await db[UsersService.collection_name].delete_many({"seed_tag": seed_tag})
    content_res = await db[ContentService.collection_name].delete_many({"seed_tag": seed_tag})
    assessments_res = await db[AssessmentsService.collection_name].delete_many({"seed_tag": seed_tag})

    deleted = {
        "seed_tag": seed_tag,
        "deleted": {
            "users": int(users_res.deleted_count),
            "content": int(content_res.deleted_count),
            "assessments": int(assessments_res.deleted_count),
        },
    }
    logger.info("Clear seeded complete", extra=deleted)
    return deleted


async def _main_async() -> None:
    before = await _counts(await _get_db(), seed_tag="sample_seed_v1")
    result = await clear_seeded()
    print("Clear seeded complete")
    print(f"seed_tag={result['seed_tag']}")
    print("deleted:")
    for k, v in result["deleted"].items():
        print(f"  {k}: {v}")
    print("seeded before clear:")
    for k, v in before.items():
        print(f"  {k}: {v}")


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
