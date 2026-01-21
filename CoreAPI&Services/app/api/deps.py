"""Authentication and authorization dependencies for the API layer.

This module provides minimal, production-aligned scaffolding to keep the service
importable and functional even when upstream security integrations (OIDC/JWT
validation) are not yet present in the source snapshot.

Key exports:
- get_current_user: returns the authenticated Principal (401 if unauthenticated)
- require_roles: dependency factory enforcing that the Principal has at least one
  required role (403 otherwise)
- CurrentUser: typing alias for injecting the current Principal via Depends

Notes:
- If `schemas.security.Principal` exists, it will be used.
- If `app.core.security.oidc.get_current_principal` exists, it will be used.
- Otherwise, we provide minimal fallbacks suitable for local/dev validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable, Iterable, List, Optional, Sequence, TypeVar, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Attempt to import Role and Principal from compiled/real modules if present.
try:
    # Prefer canonical Role enum if the project provides it.
    from app.core.security.roles import Role  # type: ignore
except Exception:  # pragma: no cover - fallback when module absent
    from enum import Enum

    class Role(str, Enum):
        """Fallback role enum used when the canonical Role is not available."""

        LEARNER = "LEARNER"
        EMPLOYEE = "EMPLOYEE"
        INSTRUCTOR = "INSTRUCTOR"
        MANAGER = "MANAGER"
        ADMIN = "ADMIN"
        SUPER_ADMIN = "SUPER_ADMIN"


try:
    # Prefer canonical Principal schema if provided by the project.
    from app.schemas.security import Principal as Principal  # type: ignore
except Exception:  # pragma: no cover - fallback when module absent

    @dataclass(frozen=True)
    class Principal:
        """Authenticated principal (user) extracted from an OIDC/JWT token.

        Fields are intentionally aligned with typical OIDC claims and compiled artifacts:
        - sub/oid: stable subject/object id
        - email/upi: optional identifiers
        - roles: list of Role values
        """

        sub: str
        oid: str
        email: Optional[str] = None
        upi: Optional[str] = None
        roles: List[Role] = None  # type: ignore[assignment]

        def __post_init__(self) -> None:
            # Ensure roles is always a list.
            if self.roles is None:
                object.__setattr__(self, "roles", [])


# Try to import the real OIDC helper; fallback to a tiny stub.
try:
    from app.core.security.oidc import get_current_principal as get_current_principal  # type: ignore
except Exception:  # pragma: no cover - fallback when module absent
    _bearer = HTTPBearer(auto_error=False)

    # PUBLIC_INTERFACE
    async def get_current_principal(
        creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    ) -> Principal:
        """Extract and validate a bearer token, returning a Principal.

        Fallback behavior (when real OIDC validation is not present):
        - Missing Authorization -> 401
        - Token == "valid" -> returns a dummy Principal with ADMIN role
        - Otherwise -> 401

        This is intentionally minimal to keep the service bootable and to make RBAC
        protections visible in routes.
        """
        if creds is None or not creds.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )

        token = creds.credentials
        if token != "valid":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return Principal(
            sub="user-123",
            oid="user-123",
            email="user@example.com",
            roles=[Role.ADMIN],
        )


# PUBLIC_INTERFACE
async def get_current_user(principal: Principal = Depends(get_current_principal)) -> Principal:
    """Return the authenticated current user principal.

    Args:
        principal: The validated Principal returned by `get_current_principal`.

    Returns:
        The same Principal, for injection into routes.

    Raises:
        HTTPException(401): If authentication fails in upstream dependency.
    """
    return principal


TPrincipal = TypeVar("TPrincipal", bound=Principal)


# PUBLIC_INTERFACE
def require_roles(required_roles: Iterable[Role]) -> Callable[[Principal], Principal]:
    """Factory creating a dependency that enforces RBAC role membership.

    The dependency ensures the current principal has *any* of the required roles.

    Args:
        required_roles: Iterable of Role values allowed to access a route.

    Returns:
        A dependency callable suitable for use with `Depends(...)` that yields the
        authenticated Principal on success.

    Raises:
        HTTPException(403): When authenticated principal lacks required roles.
    """
    required: Sequence[Role] = tuple(required_roles)

    async def _enforce(user: Principal = Depends(get_current_user)) -> Principal:
        user_roles = getattr(user, "roles", []) or []
        # Compare by enum identity; also support string roles if upstream provides them.
        user_role_strings = {str(r) for r in user_roles}
        required_strings = {str(r) for r in required}

        if not (user_role_strings & required_strings):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _enforce


# PUBLIC_INTERFACE
CurrentUser = Annotated[Principal, Depends(get_current_user)]
