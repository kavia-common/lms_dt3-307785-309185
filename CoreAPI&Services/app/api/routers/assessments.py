from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentListResponse,
    AssessmentRead,
    AssessmentUpdate,
)
from app.services.assessments import AssessmentsService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def get_assessments_service() -> AssessmentsService:
    """Dependency provider for AssessmentsService (placeholder DI)."""
    return AssessmentsService()


@router.get(
    "",
    summary="List assessments",
    description="List assessments (placeholder). No auth enforced yet.",
    response_model=AssessmentListResponse,
    operation_id="listAssessments",
)
async def list_assessments(
    service: AssessmentsService = Depends(get_assessments_service),
) -> AssessmentListResponse:
    # PUBLIC_INTERFACE
    """List assessments.

    Args:
        service: AssessmentsService dependency.

    Returns:
        AssessmentListResponse: Placeholder list payload.
    """
    return await service.list_assessments()


@router.get(
    "/{assessment_id}",
    summary="Get assessment by id",
    description="Fetch a single assessment (placeholder). No auth enforced yet.",
    response_model=AssessmentRead,
    operation_id="getAssessmentById",
)
async def get_assessment(
    assessment_id: str,
    service: AssessmentsService = Depends(get_assessments_service),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Get assessment by id.

    Args:
        assessment_id: Assessment identifier.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Placeholder assessment record.
    """
    return await service.get_assessment(assessment_id)


@router.post(
    "",
    summary="Create assessment",
    description="Create an assessment (placeholder). No auth enforced yet.",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createAssessment",
)
async def create_assessment(
    payload: AssessmentCreate,
    service: AssessmentsService = Depends(get_assessments_service),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Create an assessment.

    Args:
        payload: Assessment creation payload.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Created placeholder assessment record.
    """
    return await service.create_assessment(payload)


@router.put(
    "/{assessment_id}",
    summary="Update assessment",
    description="Update an assessment (placeholder). No auth enforced yet.",
    response_model=AssessmentRead,
    operation_id="updateAssessment",
)
async def update_assessment(
    assessment_id: str,
    payload: AssessmentUpdate,
    service: AssessmentsService = Depends(get_assessments_service),
) -> AssessmentRead:
    # PUBLIC_INTERFACE
    """Update an assessment.

    Args:
        assessment_id: Assessment identifier.
        payload: Assessment update payload.
        service: AssessmentsService dependency.

    Returns:
        AssessmentRead: Updated placeholder assessment record.
    """
    return await service.update_assessment(assessment_id, payload)


@router.delete(
    "/{assessment_id}",
    summary="Delete assessment",
    description="Delete an assessment (placeholder). No auth enforced yet.",
    operation_id="deleteAssessment",
)
async def delete_assessment(
    assessment_id: str,
    service: AssessmentsService = Depends(get_assessments_service),
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
