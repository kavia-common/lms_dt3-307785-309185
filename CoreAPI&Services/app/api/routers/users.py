"""Users API router.

This router demonstrates RBAC enforcement using:
- `app.api.deps.require_roles`
- Role groups from `app.api.security_policies`

Endpoints are intentionally minimal and database-free to keep startup reliable.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.api.deps import Principal, require_roles
from app.api.security_policies import ADMIN_ROLES, READ_ROLES, WRITE_ROLES

router = APIRouter()


# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List users (RBAC: READ_ROLES)",
    description="Returns a minimal list of users. Requires any role in READ_ROLES.",
)
def list_users(_: Principal = Depends(require_roles(READ_ROLES))) -> Dict[str, Any]:
    """List users.

    Security:
        Requires at least one role in READ_ROLES.

    Returns:
        Minimal payload with a static user list.
    """
    return {"users": [{"id": "u1"}, {"id": "u2"}]}


# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Create user (RBAC: WRITE_ROLES)",
    description="Creates a user (echo stub). Requires any role in WRITE_ROLES.",
)
def create_user(
    payload: Dict[str, Any],
    _: Principal = Depends(require_roles(WRITE_ROLES)),
) -> Dict[str, Any]:
    """Create a user (stub).

    Security:
        Requires at least one role in WRITE_ROLES.

    Args:
        payload: Arbitrary JSON payload representing a user.

    Returns:
        Echo payload with a fake id.
    """
    return {"created": True, "user": {"id": "new-user", **payload}}


# PUBLIC_INTERFACE
@router.delete(
    "/{user_id}",
    summary="Delete user (RBAC: ADMIN_ROLES)",
    description="Deletes a user (stub). Requires any role in ADMIN_ROLES.",
)
def delete_user(user_id: str, _: Principal = Depends(require_roles(ADMIN_ROLES))) -> Dict[str, Any]:
    """Delete a user (stub).

    Security:
        Requires at least one role in ADMIN_ROLES.

    Args:
        user_id: User identifier.

    Returns:
        Confirmation payload.
    """
    return {"deleted": True, "user_id": user_id}
