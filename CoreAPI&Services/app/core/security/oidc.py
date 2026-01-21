from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.security.jwt import verify_access_token
from app.core.security.roles import Role, from_str
from app.schemas.security import Principal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OIDCSettings:
    """OIDC configuration resolved from environment-driven Settings.

    Notes:
        These values are used for JWT signature verification against JWKS when AUTH_STUB=false.
    """

    issuer: Optional[str]
    client_id: Optional[str]
    audience: Optional[str]
    jwks_uri: Optional[str]


def _settings_to_oidc(settings: Settings) -> OIDCSettings:
    return OIDCSettings(
        issuer=settings.oidc_issuer,
        client_id=settings.oidc_client_id,
        audience=settings.oidc_audience,
        jwks_uri=settings.oidc_jwks_uri,
    )


def _parse_roles_csv(csv_value: str | None) -> list[Role]:
    if not csv_value:
        return []
    parts = [p.strip() for p in csv_value.split(",")]
    roles: list[Role] = []
    for p in parts:
        if not p:
            continue
        roles.append(from_str(p))
    return roles


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer":
        return None
    return token or None


# PUBLIC_INTERFACE
def get_current_principal(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Resolve the current request principal.

    Behavior:
    - If AUTH_STUB=true: returns a deterministic stub Principal.
      Optionally reads stub values from headers (for dev/testing):
        - X-Auth-Subject
        - X-Auth-Email
        - X-Auth-Roles (comma-separated)
    - If AUTH_STUB=false: requires a valid Authorization: Bearer <token> header and performs
      JWT verification against OIDC JWKS.

    Args:
        request: FastAPI request (used for headers).
        settings: Application settings.

    Returns:
        Principal: The resolved principal.

    Raises:
        HTTPException: 401 if bearer token is missing/invalid in real-auth mode.
        HTTPException: 400 if stub role parsing fails.
    """
    if settings.auth_stub:
        subject = request.headers.get("x-auth-subject") or "stub-user"
        email = request.headers.get("x-auth-email")
        roles_header = request.headers.get("x-auth-roles")
        try:
            roles = _parse_roles_csv(roles_header) if roles_header else []
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

        return Principal(subject=subject, email=email, roles=roles)

    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_access_token(token, settings=settings)


# PUBLIC_INTERFACE
def get_oidc_settings(settings: Settings = Depends(get_settings)) -> OIDCSettings:
    """Expose OIDC settings via dependency injection."""
    return _settings_to_oidc(settings)
