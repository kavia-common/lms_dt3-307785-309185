"""FastAPI application entrypoint for CoreAPI&Services.

This module defines the `app` object used by Uvicorn/Gunicorn.

It intentionally keeps the surface minimal:
- Provides health probes: `/healthz` and `/readyz`
- Attempts to include optional domain routers if they exist (users/content/assessments)
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI


def _optional_include_router(app: FastAPI, import_path: str, prefix: str, tag: str) -> None:
    """Try to import and include a router module at runtime.

    The codebase snapshot for this container may not yet contain the router modules.
    This helper allows the app to boot even when routers are missing.

    Expected module interface:
      - module has attribute `router` which is an `APIRouter`.
    """
    try:
        module = __import__(import_path, fromlist=["router"])
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            app.include_router(router, prefix=prefix, tags=[tag])
    except Exception:
        # Safe no-op: missing routers should never prevent the service from starting.
        return


app = FastAPI(
    title="CoreAPI&Services",
)


# PUBLIC_INTERFACE
@app.get(
    "/healthz",
    summary="Liveness probe",
    description="Return 200 when the service process is running.",
    tags=["Health"],
)
def healthz() -> dict:
    """Liveness endpoint.

    Returns:
        Basic status payload used for container/platform liveness probing.
    """
    return {"status": "ok", "service": "coreapi"}


# PUBLIC_INTERFACE
@app.get(
    "/readyz",
    summary="Readiness probe",
    description="Return 200 when the service is ready to accept traffic.",
    tags=["Health"],
)
def readyz() -> dict:
    """Readiness endpoint.

    Note:
        This minimal implementation always returns ready. In later iterations, it
        should validate required dependencies (DB connectivity, external services).

    Returns:
        Basic status payload used for container/platform readiness probing.
    """
    return {"status": "ok", "service": "coreapi"}


# Optional routers (include if/when they exist)
_optional_include_router(app, "app.api.routers.users", prefix="/users", tag="Users")
_optional_include_router(app, "app.api.routers.content", prefix="/content", tag="Content")
_optional_include_router(app, "app.api.routers.assessments", prefix="/assessments", tag="Assessments")
