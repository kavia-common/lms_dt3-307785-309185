from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings

logger = logging.getLogger(__name__)

_CLIENT_ATTR = "mongodb_client"
_DB_ATTR = "mongodb_db"


def _is_enabled(settings: Settings) -> bool:
    """Return True if MongoDB is configured (URI present)."""
    return bool(settings.mongodb_uri)


# PUBLIC_INTERFACE
def get_db(request: Request) -> AsyncIOMotorDatabase:
    """FastAPI dependency to fetch the configured MongoDB database handle.

    IMPORTANT: This must accept a `Request` (not `FastAPI`) so FastAPI can inject it
    as a dependency via `Depends(get_db)`.

    This requires MongoDB to be enabled/configured and the app to have run startup.

    Args:
        request: Current request object (used to access `request.app.state`).

    Returns:
        AsyncIOMotorDatabase: Motor database reference.

    Raises:
        RuntimeError: If MongoDB is not configured or startup was not executed.
    """
    db: Optional[AsyncIOMotorDatabase] = getattr(request.app.state, _DB_ATTR, None)
    if db is None:
        raise RuntimeError("MongoDB is not initialized on app.state")
    return db


# PUBLIC_INTERFACE
async def mongo_ping(app: FastAPI) -> None:
    """Ping MongoDB to verify connectivity.

    Args:
        app: FastAPI application instance.

    Raises:
        Exception: Any exception from Motor/PyMongo when connectivity fails.
    """
    # `mongo_ping` is not a dependency; keep it `FastAPI`-based.
    db: Optional[AsyncIOMotorDatabase] = getattr(app.state, _DB_ATTR, None)
    if db is None:
        raise RuntimeError("MongoDB is not initialized on app.state")
    # Mongo ping command: { ping: 1 }
    await db.command({"ping": 1})


# PUBLIC_INTERFACE
def register_mongo_lifecycle(app: FastAPI, settings: Settings) -> None:
    """Register MongoDB client startup/shutdown lifecycle hooks on the FastAPI app.

    This function is safe to call even when MongoDB is not configured (no-op).

    Args:
        app: FastAPI application instance to attach lifecycle handlers to.
        settings: Application settings containing MongoDB configuration.
    """

    @app.on_event("startup")
    async def _startup_mongo() -> None:
        if not _is_enabled(settings):
            logger.info("MongoDB disabled (MONGODB_URI not set)")
            setattr(app.state, _CLIENT_ATTR, None)
            setattr(app.state, _DB_ATTR, None)
            return

        logger.info(
            "Initializing MongoDB client",
            extra={
                "mongodb_dbname": settings.mongodb_dbname,
                "mongodb_tls": settings.mongodb_tls,
            },
        )
        client = AsyncIOMotorClient(settings.mongodb_uri, tls=settings.mongodb_tls)
        db = client.get_database(settings.mongodb_dbname)

        setattr(app.state, _CLIENT_ATTR, client)
        setattr(app.state, _DB_ATTR, db)

    @app.on_event("shutdown")
    async def _shutdown_mongo() -> None:
        client: Optional[AsyncIOMotorClient] = getattr(app.state, _CLIENT_ATTR, None)
        if client is not None:
            logger.info("Closing MongoDB client")
            client.close()
        setattr(app.state, _CLIENT_ATTR, None)
        setattr(app.state, _DB_ATTR, None)
