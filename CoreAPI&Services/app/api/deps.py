from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Iterable

from fastapi import Depends, HTTPException, status

from app.core.security.oidc import get_current_principal
from app.core.security.roles import Role
from app.schemas.security import Principal


# PUBLIC_INTERFACE
def get_current_user(principal: Principal = Depends(get_current_principal)) -> Principal:
    """Return the current authenticated principal.

    This is a semantic alias for `get_current_principal`, suitable for routers.

    Args:
        principal: Resolved Principal.

    Returns:
        Principal: Current principal.
    """
    return principal


# PUBLIC_INTERFACE
def require_roles(*required: Role) -> Callable[[Principal], Principal]:
    """Return a dependency that enforces role-based access control.

    Semantics:
        - Deny-by-default when no principal (handled upstream).
        - If `required` is empty, only authentication is required.
        - If principal has ANY of the required roles, access is allowed.

    Args:
        required: One or more Roles that satisfy authorization.

    Returns:
        A FastAPI dependency callable that returns Principal when authorized.

    Raises:
        HTTPException: 403 when authenticated but not authorized.
    """

    def _dep(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not required:
            return principal

        principal_roles = set(principal.roles or [])
        if any(r in principal_roles for r in required):
            return principal

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role for this operation.",
        )

    return _dep


# Convenience typing alias for endpoints
CurrentUser = Annotated[Principal, Depends(get_current_user)]
