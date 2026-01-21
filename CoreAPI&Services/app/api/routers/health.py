from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health/ready response payload."""

    status: str = Field(..., description="Service status. Typically 'ok'.")
    service: str = Field(..., description="Service identifier.")


@router.get(
    "/healthz",
    summary="Liveness probe",
    description="Basic liveness check to confirm the process is running.",
    response_model=HealthResponse,
    operation_id="getHealthz",
)
async def healthz() -> HealthResponse:
    # PUBLIC_INTERFACE
    """Liveness endpoint.

    Returns:
        HealthResponse: status payload for orchestration liveness probes.
    """
    return HealthResponse(status="ok", service="coreapi")


@router.get(
    "/readyz",
    summary="Readiness probe",
    description=(
        "Basic readiness check. For now it returns ok. "
        "Later it can include DB connectivity checks, migrations, etc."
    ),
    response_model=HealthResponse,
    operation_id="getReadyz",
)
async def readyz() -> HealthResponse:
    # PUBLIC_INTERFACE
    """Readiness endpoint.

    Returns:
        HealthResponse: status payload for orchestration readiness probes.
    """
    # TODO(db): add MongoDB connectivity check once DB client is introduced
    return HealthResponse(status="ok", service="coreapi")
