"""Assessments API router.

This router demonstrates RBAC enforcement using:
- `app.api.deps.require_roles`
- Role groups from `app.api.security_policies`

Endpoints are intentionally minimal and database-free to keep startup reliable.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_roles
from app.api.security_policies import ADMIN_ROLES, READ_ROLES, WRITE_ROLES

router = APIRouter()


# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List assessments (RBAC: READ_ROLES)",
    description="Returns a minimal list of assessments. Requires any role in READ_ROLES.",
)
def list_assessments(_: CurrentUser = Depends(require_roles(READ_ROLES))) -> Dict[str, Any]:
    """List assessments.

    Security:
        Requires at least one role in READ_ROLES.

    Returns:
        Minimal payload with a static assessment list.
    """
    return {"assessments": [{"id": "a1", "name": "Quiz 1"}, {"id": "a2", "name": "Final"}]}


# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Create assessment (RBAC: WRITE_ROLES)",
    description="Creates an assessment (echo stub). Requires any role in WRITE_ROLES.",
)
def create_assessment(
    payload: Dict[str, Any],
    _: CurrentUser = Depends(require_roles(WRITE_ROLES)),
) -> Dict[str, Any]:
    """Create an assessment (stub).

    Security:
        Requires at least one role in WRITE_ROLES.

    Args:
        payload: Arbitrary JSON payload representing an assessment.

    Returns:
        Echo payload with a fake id.
    """
    return {"created": True, "assessment": {"id": "new-assessment", **payload}}


# PUBLIC_INTERFACE
@router.delete(
    "/{assessment_id}",
    summary="Delete assessment (RBAC: ADMIN_ROLES)",
    description="Deletes an assessment (stub). Requires any role in ADMIN_ROLES.",
)
def delete_assessment(
    assessment_id: str, _: CurrentUser = Depends(require_roles(ADMIN_ROLES))
) -> Dict[str, Any]:
    """Delete an assessment (stub).

    Security:
        Requires at least one role in ADMIN_ROLES.

    Args:
        assessment_id: Assessment identifier.

    Returns:
        Confirmation payload.
    """
    return {"deleted": True, "assessment_id": assessment_id}
