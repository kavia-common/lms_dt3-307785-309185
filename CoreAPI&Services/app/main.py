"""
FastAPI application entrypoint for the DigitalT3 LMS Core API & Services.

This module wires together:
- Environment-based settings
- Structured logging
- Global error handling with standardized JSON responses
- Core routers (health/readiness)
- CORS middleware configuration

Run (example):
    uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.health import router as health_router
from app.core.config import get_settings
from app.core.db import register_mongo_lifecycle
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging

openapi_tags = [
    {
        "name": "Health",
        "description": "Service health and readiness probes for orchestration platforms.",
    },
]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="DigitalT3 LMS Core API & Services",
        description=(
            "Backend REST API for the DigitalT3 AI-enabled Learning Management System (LMS). "
            "This scaffold provides foundational endpoints, configuration, and operability hooks."
        ),
        version="0.1.0",
        openapi_tags=openapi_tags,
    )

    # CORS configuration (placeholder; env-driven). Keep permissive defaults OFF.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        max_age=settings.cors_max_age,
    )

    install_exception_handlers(app)

    # DB lifecycle hooks
    register_mongo_lifecycle(app, settings)

    # Routers
    app.include_router(health_router)

    return app


app = create_app()
