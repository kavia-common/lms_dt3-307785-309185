from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.services.assessments import AssessmentsService
from app.services.content import ContentService
from app.services.users import UsersService

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


async def _get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError(
            "MongoDB is not configured. Set MONGODB_URI (and optionally MONGODB_DBNAME, MONGODB_TLS)."
        )
    client = AsyncIOMotorClient(settings.mongodb_uri, tls=settings.mongodb_tls)
    return client.get_database(settings.mongodb_dbname)


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes used by the services so upserts are stable and fast."""
    # We use the same index definitions as the domain services. These are idempotent.
    await UsersService(db)._ensure_indexes()
    await ContentService(db)._ensure_indexes()
    await AssessmentsService(db)._ensure_indexes()


async def _upsert_user(db: AsyncIOMotorDatabase, *, email: str, name: str, seed_tag: str) -> None:
    """Upsert a user by unique email (idempotent)."""
    now = _utcnow()
    await db[UsersService.collection_name].update_one(
        {"email": email.lower()},
        {
            "$setOnInsert": {
                "created_at": now,
            },
            "$set": {
                "name": name,
                "email": email.lower(),
                "updated_at": now,
                "deleted_at": None,
                "seed_tag": seed_tag,
            },
        },
        upsert=True,
    )


async def _upsert_content(db: AsyncIOMotorDatabase, *, slug: str, title: str, seed_tag: str) -> None:
    """Upsert content by slug (idempotent)."""
    now = _utcnow()
    await db[ContentService.collection_name].update_one(
        {"slug": slug},
        {
            "$setOnInsert": {"created_at": now},
            "$set": {
                "title": title,
                "slug": slug,
                "updated_at": now,
                "deleted_at": None,
                "seed_tag": seed_tag,
            },
        },
        upsert=True,
    )


async def _upsert_assessment(
    db: AsyncIOMotorDatabase,
    *,
    title: str,
    course_id: str | None,
    module_id: str | None,
    seed_tag: str,
) -> None:
    """
    Upsert assessment by stable composite key.

    There is no unique index for assessments, so we enforce idempotency by using a deterministic
    filter key (seed_tag + title + course_id + module_id).
    """
    now = _utcnow()
    await db[AssessmentsService.collection_name].update_one(
        {
            "seed_tag": seed_tag,
            "title": title,
            "course_id": course_id,
            "module_id": module_id,
        },
        {
            "$setOnInsert": {"created_at": now},
            "$set": {
                "title": title,
                "course_id": course_id,
                "module_id": module_id,
                "updated_at": now,
                "deleted_at": None,
                "seed_tag": seed_tag,
            },
        },
        upsert=True,
    )


async def _counts(db: AsyncIOMotorDatabase, *, seed_tag: str) -> dict[str, Any]:
    """Return counts by collection, including total and seeded totals."""
    users_total = await db[UsersService.collection_name].count_documents({})
    users_seeded = await db[UsersService.collection_name].count_documents({"seed_tag": seed_tag})

    content_total = await db[ContentService.collection_name].count_documents({})
    content_seeded = await db[ContentService.collection_name].count_documents({"seed_tag": seed_tag})

    assessments_total = await db[AssessmentsService.collection_name].count_documents({})
    assessments_seeded = await db[AssessmentsService.collection_name].count_documents(
        {"seed_tag": seed_tag}
    )

    return {
        "users": {"total": int(users_total), "seeded": int(users_seeded)},
        "content": {"total": int(content_total), "seeded": int(content_seeded)},
        "assessments": {"total": int(assessments_total), "seeded": int(assessments_seeded)},
    }


# PUBLIC_INTERFACE
async def seed() -> dict[str, Any]:
    """Seed MongoDB with minimal sample data for sanity-checking API endpoints.

    Inserts/updates:
    - Users (upsert by unique `email`)
    - Content (upsert by `slug`)
    - Assessments (upsert by deterministic filter with seed_tag)

    Returns:
        dict[str, Any]: Counts per collection (total + seeded).
    """
    seed_tag = "sample_seed_v1"

    db = await _get_db()
    await _ensure_indexes(db)

    # Users: respect uniq_email by upserting with unique emails.
    await _upsert_user(db, email="alice@example.com", name="Alice Example", seed_tag=seed_tag)
    await _upsert_user(db, email="bob@example.com", name="Bob Example", seed_tag=seed_tag)
    await _upsert_user(db, email="instructor@example.com", name="Instructor Example", seed_tag=seed_tag)

    # Content: use index-respecting slugs (kebab-case).
    await _upsert_content(db, slug="intro-to-digitalt3", title="Intro to DigitalT3", seed_tag=seed_tag)
    await _upsert_content(db, slug="lms-basics", title="LMS Basics", seed_tag=seed_tag)
    await _upsert_content(db, slug="assessment-101", title="Assessment 101", seed_tag=seed_tag)

    # Assessments: minimal sample records tied to simple string ids (not enforced yet).
    await _upsert_assessment(
        db,
        title="Quiz: Intro to DigitalT3",
        course_id="intro-to-digitalt3",
        module_id=None,
        seed_tag=seed_tag,
    )
    await _upsert_assessment(
        db,
        title="Quiz: LMS Basics",
        course_id="lms-basics",
        module_id=None,
        seed_tag=seed_tag,
    )

    counts = await _counts(db, seed_tag=seed_tag)
    logger.info("Seed complete", extra={"seed_tag": seed_tag, "counts": counts})
    return {"seed_tag": seed_tag, "counts": counts}


async def _main_async() -> None:
    result = await seed()
    # Print a concise confirmation for CLI usage.
    print("Seed complete")
    print(f"seed_tag={result['seed_tag']}")
    print("counts:")
    for k, v in result["counts"].items():
        print(f"  {k}: total={v['total']} seeded={v['seeded']}")


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
