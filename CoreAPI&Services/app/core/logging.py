from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.core.config import Settings


class _ConsoleFormatter(logging.Formatter):
    """Human-friendly console formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        if record.exc_info:
            return base
        return base


class _SimpleJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter with stable keys and ISO timestamps."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault(
            "timestamp",
            datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
        )
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("message", record.getMessage())


def _should_use_json(settings: Settings) -> bool:
    if settings.log_format.lower() == "json":
        return True
    if settings.log_format.lower() == "console":
        return False
    # auto
    return settings.app_env.lower() in {"production", "prod"}


def configure_logging(settings: Settings) -> None:
    """Configure Python logging globally for the service."""
    root = logging.getLogger()
    # Clear existing handlers to avoid duplicate logs in uvicorn reload environments
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)

    if _should_use_json(settings):
        handler.setFormatter(_SimpleJsonFormatter())
    else:
        handler.setFormatter(
            _ConsoleFormatter(fmt="%(asctime)s %(levelname)s %(name)s - %(message)s")
        )

    root.addHandler(handler)

    # Make uvicorn's access logs consistent
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True

    # Optional: reduce noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)


def log_json(level: int, message: str, **fields: Any) -> None:
    """Helper to emit a single structured log entry even in console mode."""
    payload = {"message": message, **fields}
    logging.getLogger("app").log(level, json.dumps(payload))
