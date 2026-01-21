from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import require_roles
from app.api.security_policies import ADMIN_ROLES, READ_ROLES, WRITE_ROLES
from app.core.db import get_db
from app.schemas.content import ContentCreate, ContentListResponse, ContentRead, ContentUpdate
from app.schemas.security import Principal
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
    description="List content items. Requires authenticated user with a read role.",
    response_model=ContentListResponse,
    operation_id="listContent",
)
async def list_content(
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination page size."),
    service: ContentService = Depends(get_content_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> ContentListResponse:
    # PUBLIC_INTERFACE
    """List content items.

    Args:
        service: ContentService dependency.

    Returns:
        ContentListResponse: Paginated list payload.
    """
    return await service.list_content(skip=skip, limit=limit)


@router.get(
    "/{content_id}",
    summary="Get content by id",
    description="Fetch a single content item. Requires authenticated user with a read role.",
    response_model=ContentRead,
    operation_id="getContentById",
)
async def get_content(
    content_id: str,
    service: ContentService = Depends(get_content_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Get content by id.

    Args:
        content_id: Content identifier.
        service: ContentService dependency.

    Returns:
        ContentRead: Content record.
    """
    return await service.get_content(content_id)


@router.post(
    "",
    summary="Create content",
    description="Create content. Requires authenticated user with a write role.",
    response_model=ContentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createContent",
)
async def create_content(
    payload: ContentCreate,
    service: ContentService = Depends(get_content_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Create content.

    Args:
        payload: Content creation payload.
        service: ContentService dependency.

    Returns:
        ContentRead: Created content record.
    """
    return await service.create_content(payload)


@router.put(
    "/{content_id}",
    summary="Update content",
    description="Update content. Requires authenticated user with a write role.",
    response_model=ContentRead,
    operation_id="updateContent",
)
async def update_content(
    content_id: str,
    payload: ContentUpdate,
    service: ContentService = Depends(get_content_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> ContentRead:
    # PUBLIC_INTERFACE
    """Update content.

    Args:
        content_id: Content identifier.
        payload: Content update payload.
        service: ContentService dependency.

    Returns:
        ContentRead: Updated content record.
    """
    return await service.update_content(content_id, payload)


@router.delete(
    "/{content_id}",
    summary="Delete content",
    description="Soft-delete content. Requires authenticated admin role.",
    operation_id="deleteContent",
)
async def delete_content(
    content_id: str,
    service: ContentService = Depends(get_content_service),
    _principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
) -> dict:
    # PUBLIC_INTERFACE
    """Delete content.

    Args:
        content_id: Content identifier.
        service: ContentService dependency.

    Returns:
        dict: Confirmation payload.
    """
    return await service.delete_content(content_id)
