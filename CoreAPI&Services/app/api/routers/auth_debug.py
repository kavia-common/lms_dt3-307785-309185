from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security.oidc import get_current_principal
from app.schemas.security import Principal

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/debug",
    summary="Auth debug endpoint (stub or real JWT)",
    description=(
        "When AUTH_STUB=true, returns the resolved stub Principal (can be overridden by headers). "
        "When AUTH_STUB=false, requires Authorization: Bearer <access_token> and returns the "
        "Principal derived from validated JWT claims."
    ),
    response_model=Principal,
    operation_id="getAuthDebugPrincipal",
)
async def auth_debug(principal: Principal = Depends(get_current_principal)) -> Principal:
    # PUBLIC_INTERFACE
    """Echo the current principal.

    Args:
        principal: Resolved current principal.

    Returns:
        Principal: The same principal payload, for debug/testing.
    """
    return principal
