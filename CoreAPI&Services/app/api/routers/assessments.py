from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import require_roles
from app.api.security_policies import ADMIN_ROLES, READ_ROLES, WRITE_ROLES
from app.core.db import get_db
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentListResponse,
    AssessmentRead,
    AssessmentUpdate,
)
from app.schemas.security import Principal
from app.services.assessments import AssessmentsService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def get_assessments_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AssessmentsService:
    """Dependency provider for AssessmentsService (MongoDB-backed).

    This is intentionally declared as a FastAPI dependency callable so tests can
    override it via `app.dependency_overrides[get_assessments_service] = ...` without
    triggering MongoDB initialization.
    """
    return AssessmentsService(db=db)


@router.get(
    "",
    summary="List assessments",
    description="List assessments. Requires authenticated user with a read role.",
    response_model=AssessmentListResponse,
    operation_id="listAssessments",
)
async def list_assessments(
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination page size."),
    service: AssessmentsService = Depends(get_assessments_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> AssessmentListResponse:
    # PUBLIC_INTERFACE
    """List assessments.

    Args:
        service: AssessmentsService dependency.

    Returns:
        AssessmentListResponse: Paginated list payload.
    """
    return await service.list_assessments(skip=skip, limit=limit)


@router.get(
    "/{assessment_id}",
    summary="Get assessment by id",
    description="Fetch a single assessment. Requires authenticated user with a read role.",
    response_model=AssessmentRead,
    operation_id="getAssessmentById",
)
async def get_assessment(
    assessment_id: str,
    service: AssessmentsService = Depends(get_assessments_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Get assessment by id.

    Args:
        assessment_id: Assessment identifier.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Assessment record.
    """
    return await service.get_assessment(assessment_id)


@router.post(
    "",
    summary="Create assessment",
    description="Create an assessment. Requires authenticated user with a write role.",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createAssessment",
)
async def create_assessment(
    payload: AssessmentCreate,
    service: AssessmentsService = Depends(get_assessments_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Create an assessment.

    Args:
        payload: Assessment creation payload.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Created assessment record.
    """
    return await service.create_assessment(payload)


@router.put(
    "/{assessment_id}",
    summary="Update assessment",
    description="Update an assessment. Requires authenticated user with a write role.",
    response_model=AssessmentRead,
    operation_id="updateAssessment",
)
async def update_assessment(
    assessment_id: str,
    payload: AssessmentUpdate,
    service: AssessmentsService = Depends(get_assessments_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Update an assessment.

    Args:
        assessment_id: Assessment identifier.
        payload: Assessment update payload.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Updated assessment record.
    """
    return await service.update_assessment(assessment_id, payload)


@router.delete(
    "/{assessment_id}",
    summary="Delete assessment",
    description="Soft-delete an assessment. Requires authenticated admin role.",
    operation_id="deleteAssessment",
)
async def delete_assessment(
    assessment_id: str,
    service: AssessmentsService = Depends(get_assessments_service),
    _principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
) -> dict:
    # PUBLIC_INTERFACE
    """Delete an assessment.

    Args:
        assessment_id: Assessment identifier.
        service: AssessmentsService dependency.

    Returns:
        dict: Confirmation payload.
    """
    return await service.delete_assessment(assessment_id)
