from __future__ import annotations

from functools import lru_cache
import json
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Prevent pydantic-settings from JSON-decoding complex env values (e.g. List[str])
        # before our `mode="before"` validators run.
        enable_decoding=False,
    )

    app_env: str = Field(default="development", alias="APP_ENV")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=3001, alias="PORT")
    trust_proxy: bool = Field(default=False, alias="TRUST_PROXY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    # "auto" => json in production, console otherwise
    log_format: str = Field(default="auto", alias="LOG_FORMAT")

    # CORS
    allowed_origins: List[str] = Field(default_factory=list, alias="ALLOWED_ORIGINS")
    allowed_headers: List[str] = Field(
        default_factory=lambda: ["Content-Type", "Authorization", "X-Requested-With"],
        alias="ALLOWED_HEADERS",
    )
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        alias="ALLOWED_METHODS",
    )
    cors_max_age: int = Field(default=3600, alias="CORS_MAX_AGE")

    # Database (MongoDB)
    mongodb_uri: str | None = Field(default=None, alias="MONGODB_URI")
    mongodb_dbname: str = Field(default="lms", alias="MONGODB_DBNAME")
    mongodb_tls: bool = Field(default=False, alias="MONGODB_TLS")

    # Auth / OIDC scaffolding
    # NOTE: Default True to keep dev/tests working until real OIDC validation is implemented.
    auth_stub: bool = Field(default=True, alias="AUTH_STUB")

    oidc_issuer: Optional[str] = Field(default=None, alias="OIDC_ISSUER")
    oidc_client_id: Optional[str] = Field(default=None, alias="OIDC_CLIENT_ID")
    oidc_audience: Optional[str] = Field(default=None, alias="OIDC_AUDIENCE")
    oidc_jwks_uri: Optional[str] = Field(default=None, alias="OIDC_JWKS_URI")

    # URLs / misc placeholders
    site_url: str | None = Field(default=None, alias="SITE_URL")
    backend_url: str | None = Field(default=None, alias="BACKEND_URL")
    frontend_url: str | None = Field(default=None, alias="FRONTEND_URL")
    ws_url: str | None = Field(default=None, alias="WS_URL")

    request_timeout_ms: int = Field(default=30000, alias="REQUEST_TIMEOUT_MS")
    rate_limit_window_s: int = Field(default=60, alias="RATE_LIMIT_WINDOW_S")
    rate_limit_max: int = Field(default=100, alias="RATE_LIMIT_MAX")

    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")

    @staticmethod
    def _parse_list_env(value: Any) -> list[str]:
        """Parse list-ish env var values.

        Supports:
        - JSON arrays: '["https://a.com","https://b.com"]'
        - CSV: 'https://a.com, https://b.com'
        - Python lists (already-parsed): ['a', 'b']
        """
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, tuple):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            # Prefer JSON array when it looks like JSON, but fall back to CSV for tests/.env usage.
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(v).strip() for v in parsed if str(v).strip()]
                except json.JSONDecodeError:
                    # Fall through to CSV parsing (safe default for common .env patterns).
                    pass
            return [p.strip() for p in raw.split(",") if p.strip()]
        # Last resort: coerce to string and treat as a single item.
        return [str(value).strip()] if str(value).strip() else []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _validate_allowed_origins(cls, v: Any) -> list[str]:
        return cls._parse_list_env(v)

    @field_validator("allowed_headers", mode="before")
    @classmethod
    def _validate_allowed_headers(cls, v: Any) -> list[str]:
        return cls._parse_list_env(v)

    @field_validator("allowed_methods", mode="before")
    @classmethod
    def _validate_allowed_methods(cls, v: Any) -> list[str]:
        return cls._parse_list_env(v)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance.

    Notes:
        This function is cached for performance in production, but tests may need to change
        environment variables between app instances. For that, use `clear_settings_cache()`.
    """
    return Settings()


# PUBLIC_INTERFACE
def clear_settings_cache() -> None:
    """Clear the cached Settings instance.

    This is primarily intended for tests where environment variables are monkeypatched
    between test cases and we need `get_settings()` to reflect the new values.
    """
    get_settings.cache_clear()
