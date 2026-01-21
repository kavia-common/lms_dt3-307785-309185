from __future__ import annotations

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.db import mongo_ping

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health/ready response payload."""

    status: str = Field(..., description="Service status. Typically 'ok'.")
    service: str = Field(..., description="Service identifier.")


class DbHealthResponse(BaseModel):
    """MongoDB connectivity health payload."""

    status: str = Field(..., description="Database connectivity status: 'ok' or 'failed'.")
    duration_ms: float = Field(..., description="Time taken to perform the check in milliseconds.")
    error: str | None = Field(default=None, description="Optional error message when status=failed.")


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
    return HealthResponse(status="ok", service="coreapi")


@router.get(
    "/health/db",
    summary="MongoDB connectivity health check",
    description=(
        "Performs a MongoDB ping (db.command({ ping: 1 })) to verify DB connectivity. "
        "Returns status, duration, and optional error message."
    ),
    response_model=DbHealthResponse,
    operation_id="getMongoDbHealth",
)
async def health_db(request: Request) -> DbHealthResponse:
    # PUBLIC_INTERFACE
    """MongoDB connectivity endpoint.

    This endpoint requires MongoDB client to be configured and initialized on app startup.

    Args:
        request: FastAPI request (used to access app instance/state).

    Returns:
        DbHealthResponse: DB connectivity status payload.
    """
    started = time.perf_counter()
    try:
        await mongo_ping(request.app)
        duration_ms = (time.perf_counter() - started) * 1000.0
        return DbHealthResponse(status="ok", duration_ms=duration_ms, error=None)
    except Exception as exc:  # noqa: BLE001 - we want to surface any connection/init error
        duration_ms = (time.perf_counter() - started) * 1000.0
        return DbHealthResponse(status="failed", duration_ms=duration_ms, error=str(exc))
