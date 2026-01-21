from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: str = Field(..., description="A short, machine-readable error code.")
    message: str = Field(..., description="A human-readable error message.")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional structured details for debugging."
    )
    request_id: Optional[str] = Field(default=None, description="Optional request correlation ID.")


def _request_id_from_headers(request: Request) -> str | None:
    # Common correlation header names; extend later as needed.
    return request.headers.get("x-request-id") or request.headers.get("x-correlation-id")


def install_exception_handlers(app: FastAPI) -> None:
    """Install global exception handlers for standardized JSON error responses."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        payload = ErrorResponse(
            error="http_error",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
            request_id=_request_id_from_headers(request),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", extra={"path": str(request.url.path)})
        payload = ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred.",
            details=None,
            request_id=_request_id_from_headers(request),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())
