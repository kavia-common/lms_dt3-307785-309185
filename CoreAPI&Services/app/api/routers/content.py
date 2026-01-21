from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.schemas.content import ContentCreate, ContentListResponse, ContentRead, ContentUpdate
from app.services.content import ContentService

router = APIRouter(prefix="/content", tags=["Content"])


def get_content_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ContentService:
    """Dependency provider for ContentService (MongoDB-backed).

    This is intentionally declared as a FastAPI dependency callable so tests can
    override it via `app.dependency_overrides[get_content_service] = ...` without
    triggering MongoDB initialization.
    """
    return ContentService(db=db)


@router.get(
    "",
    summary="List content",
    description="List content items (placeholder). No auth enforced yet.",
    response_model=ContentListResponse,
    operation_id="listContent",
)
async def list_content(
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination page size."),
    service: ContentService = Depends(get_content_service),
) -> ContentListResponse:
    # PUBLIC_INTERFACE
    """List content items.

    Args:
        service: ContentService dependency.

    Returns:
        ContentListResponse: Placeholder list payload.
    """
    return await service.list_content(skip=skip, limit=limit)


@router.get(
    "/{content_id}",
    summary="Get content by id",
    description="Fetch a single content item (placeholder). No auth enforced yet.",
    response_model=ContentRead,
    operation_id="getContentById",
)
async def get_content(
    content_id: str, service: ContentService = Depends(get_content_service)
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Get content by id.

    Args:
        content_id: Content identifier.
        service: ContentService dependency.

    Returns:
        ContentRead: Placeholder content record.
    """
    return await service.get_content(content_id)


@router.post(
    "",
    summary="Create content",
    description="Create content (placeholder). No auth enforced yet.",
    response_model=ContentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createContent",
)
async def create_content(
    payload: ContentCreate,
    service: ContentService = Depends(get_content_service),
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Create content.

    Args:
        payload: Content creation payload.
        service: ContentService dependency.

    Returns:
        ContentRead: Created placeholder content record.
    """
    return await service.create_content(payload)


@router.put(
    "/{content_id}",
    summary="Update content",
    description="Update content (placeholder). No auth enforced yet.",
    response_model=ContentRead,
    operation_id="updateContent",
)
async def update_content(
    content_id: str,
    payload: ContentUpdate,
    service: ContentService = Depends(get_content_service),
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Update content.

    Args:
        content_id: Content identifier.
        payload: Content update payload.
        service: ContentService dependency.

    Returns:
        ContentRead: Updated placeholder content record.
    """
    return await service.update_content(content_id, payload)


@router.delete(
    "/{content_id}",
    summary="Delete content",
    description="Delete content (placeholder). No auth enforced yet.",
    operation_id="deleteContent",
)
async def delete_content(content_id: str, service: ContentService = Depends(get_content_service)) -> dict:
    # PUBLIC_INTERFACE
    """Delete content.

    Args:
        content_id: Content identifier.
        service: ContentService dependency.

    Returns:
        dict: Confirmation payload.
    """
    return await service.delete_content(content_id)
