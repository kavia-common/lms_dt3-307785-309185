from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security.oidc import get_current_principal
from app.schemas.security import Principal

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/debug",
    summary="Auth stub debug endpoint",
    description=(
        "When AUTH_STUB=true, returns the resolved stub Principal. "
        "When AUTH_STUB=false, returns 501 until real OIDC validation is implemented."
    ),
    response_model=Principal,
    operation_id="getAuthDebugPrincipal",
)
async def auth_debug(principal: Principal = Depends(get_current_principal)) -> Principal:
    # PUBLIC_INTERFACE
    """Echo the current principal (stub only).

    Args:
        principal: Resolved current principal.

    Returns:
        Principal: The same principal payload, for debug/testing.
    """
    return principal
