"""
Shared pytest helpers for FastAPI tests.

This module is intentionally lightweight and dependency-free so it can be imported
from any test module without pulling in application internals.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional


def _maybe_await(value: Any) -> Any:
    """Await a value if it is awaitable, otherwise return as-is."""
    if inspect.isawaitable(value):
        return value
    return value


def _get_close_callable(db: Any) -> Optional[Callable[[], Any]]:
    """Return a close/cleanup callable on the db object, if any."""
    for attr in ("aclose", "close", "disconnect", "shutdown"):
        fn = getattr(db, attr, None)
        if callable(fn):
            return fn
    return None


def _resolve_db(db_or_factory: Any) -> Any:
    """Resolve the DB instance from either a DB instance or a factory/callable."""
    if callable(db_or_factory):
        return db_or_factory()
    return db_or_factory


# PUBLIC_INTERFACE
def override_db(db_or_factory: Any) -> Callable[[], Any]:
    """
    Create a FastAPI dependency override for a DB dependency.

    The returned callable is suitable for assigning into `app.dependency_overrides`:

        app.dependency_overrides[get_db] = override_db(fake_db)

    Behavior:
    - Accepts either a DB instance or a factory callable (sync or async).
    - Returns an async generator dependency (yield-style), compatible with both
      sync and async original dependencies.
    - After yielding, it attempts to clean up the DB object by calling one of:
      `aclose()`, `close()`, `disconnect()`, or `shutdown()` if present.
      Async close methods are awaited.

    Args:
        db_or_factory: A fake/stub DB instance OR a factory that returns one.
                       The factory may be sync or async.

    Returns:
        A callable dependency override (async generator function) that yields the DB.
    """

    async def _override() -> Any:
        db = _resolve_db(db_or_factory)
        if inspect.isawaitable(db):
            db = await db

        try:
            yield db
        finally:
            close_fn = _get_close_callable(db)
            if close_fn is None:
                return

            result = close_fn()
            if inspect.isawaitable(result):
                await result

    return _override
