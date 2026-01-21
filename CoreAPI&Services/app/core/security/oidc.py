from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.security.roles import Role, from_str
from app.schemas.security import Principal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OIDCSettings:
    """OIDC configuration placeholders.

    These values are expected to come from environment-driven Settings.
    In a future milestone, they will be used for discovery/JWKS retrieval and JWT validation.
    """

    issuer: Optional[str]
    client_id: Optional[str]
    audience: Optional[str]
    jwks_uri: Optional[str]


class OIDCVerifier:
    """Placeholder verifier interface for OIDC/JWT processing.

    This is intentionally a stub. It documents the API we expect to need later.

    Future behavior (not implemented here):
    - Validate JWT signature against JWKS
    - Validate standard claims (iss, aud, exp, nbf)
    - Map roles/groups/claims to platform Role enum
    """

    # PUBLIC_INTERFACE
    def verify_and_parse(self, token: str) -> Principal:
        """Verify a bearer token and return a Principal.

        Args:
            token: Raw bearer token (JWT).

        Returns:
            Principal: Parsed principal with subject/email/roles.

        Raises:
            NotImplementedError: Until real validation is implemented.
        """
        raise NotImplementedError("OIDC token verification is not implemented yet.")

    # PUBLIC_INTERFACE
    def map_roles_from_claims(self, claims: Mapping[str, Any]) -> list[Role]:
        """Map token claims to platform roles.

        Args:
            claims: Decoded token claims.

        Returns:
            list[Role]: Mapped roles.

        Raises:
            NotImplementedError: Until real role mapping is implemented.
        """
        raise NotImplementedError("Role mapping from OIDC claims is not implemented yet.")


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
    - If AUTH_STUB=false: raises NotImplementedError until real OIDC is implemented.

    Args:
        request: FastAPI request.
        settings: Application settings.

    Returns:
        Principal: The resolved principal.

    Raises:
        HTTPException: 501 when auth is not implemented and stub is disabled.
    """
    if not settings.auth_stub:
        # Use a 501 so clients can clearly distinguish "not implemented" from "unauthorized".
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not implemented yet.",
        )

    subject = request.headers.get("x-auth-subject") or "stub-user"
    email = request.headers.get("x-auth-email")
    roles_header = request.headers.get("x-auth-roles")
    try:
        roles = _parse_roles_csv(roles_header) if roles_header else []
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return Principal(subject=subject, email=email, roles=roles)


# PUBLIC_INTERFACE
def get_oidc_settings(settings: Settings = Depends(get_settings)) -> OIDCSettings:
    """Expose OIDC settings placeholder via dependency injection."""
    return _settings_to_oidc(settings)
