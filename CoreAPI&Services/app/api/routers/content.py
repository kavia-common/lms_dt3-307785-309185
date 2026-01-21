"""Content API router.

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
    summary="List content (RBAC: READ_ROLES)",
    description="Returns a minimal list of content items. Requires any role in READ_ROLES.",
)
def list_content(_: Principal = Depends(require_roles(READ_ROLES))) -> Dict[str, Any]:
    """List content items.

    Security:
        Requires at least one role in READ_ROLES.

    Returns:
        Minimal payload with a static content list.
    """
    return {"items": [{"id": "c1", "title": "Intro"}, {"id": "c2", "title": "Module 1"}]}


# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Create content (RBAC: WRITE_ROLES)",
    description="Creates a content item (echo stub). Requires any role in WRITE_ROLES.",
)
def create_content(
    payload: Dict[str, Any],
    _: Principal = Depends(require_roles(WRITE_ROLES)),
) -> Dict[str, Any]:
    """Create a content item (stub).

    Security:
        Requires at least one role in WRITE_ROLES.

    Args:
        payload: Arbitrary JSON payload representing a content item.

    Returns:
        Echo payload with a fake id.
    """
    return {"created": True, "item": {"id": "new-content", **payload}}


# PUBLIC_INTERFACE
@router.delete(
    "/{item_id}",
    summary="Delete content (RBAC: ADMIN_ROLES)",
    description="Deletes a content item (stub). Requires any role in ADMIN_ROLES.",
)
def delete_content(item_id: str, _: Principal = Depends(require_roles(ADMIN_ROLES))) -> Dict[str, Any]:
    """Delete a content item (stub).

    Security:
        Requires at least one role in ADMIN_ROLES.

    Args:
        item_id: Content identifier.

    Returns:
        Confirmation payload.
    """
    return {"deleted": True, "item_id": item_id}
