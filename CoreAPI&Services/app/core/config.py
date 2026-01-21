from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    # URLs / misc placeholders
    site_url: str | None = Field(default=None, alias="SITE_URL")
    backend_url: str | None = Field(default=None, alias="BACKEND_URL")
    frontend_url: str | None = Field(default=None, alias="FRONTEND_URL")
    ws_url: str | None = Field(default=None, alias="WS_URL")

    request_timeout_ms: int = Field(default=30000, alias="REQUEST_TIMEOUT_MS")
    rate_limit_window_s: int = Field(default=60, alias="RATE_LIMIT_WINDOW_S")
    rate_limit_max: int = Field(default=100, alias="RATE_LIMIT_MAX")

    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
