from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import httpx
import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.security.roles import Role, from_str
from app.schemas.security import Principal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JWKSConfig:
    """Resolved JWKS configuration derived from Settings."""

    issuer: str
    audience: str | None
    jwks_uri: str
    algorithms: list[str]


class _JWKSCache:
    """Small in-process cache for PyJWKClient instances.

    Notes:
        This is intentionally simple (per-process cache). It avoids repeated JWK downloads
        on every request while still supporting key rotation via PyJWKClient.
    """

    def __init__(self) -> None:
        self._by_uri: dict[str, PyJWKClient] = {}

    def get(self, jwks_uri: str) -> PyJWKClient:
        if jwks_uri not in self._by_uri:
            self._by_uri[jwks_uri] = PyJWKClient(jwks_uri)
        return self._by_uri[jwks_uri]

    def clear(self) -> None:
        self._by_uri.clear()


_JWKS_CACHE = _JWKSCache()


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    if isinstance(value, tuple):
        return [str(x) for x in value if str(x)]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if str(x)]
            except json.JSONDecodeError:
                pass
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [str(value)]


def _resolve_jwks_config(settings: Settings) -> JWKSConfig:
    issuer = (settings.oidc_issuer or "").strip()
    jwks_uri = (settings.oidc_jwks_uri or "").strip()
    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC_ISSUER is required when AUTH_STUB=false.",
        )
    if not jwks_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC_JWKS_URI is required when AUTH_STUB=false.",
        )

    algs = _coerce_list(settings.oidc_algorithms) or ["RS256"]
    audience = (settings.oidc_audience or "").strip() or None
    return JWKSConfig(issuer=issuer, audience=audience, jwks_uri=jwks_uri, algorithms=algs)


def _extract_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer":
        return None
    return token or None


def _roles_from_claims(claims: Mapping[str, Any]) -> list[Role]:
    """Extract platform roles from common OIDC claim shapes.

    Supported:
        - roles: ["Learner","Admin"] or "Learner,Admin"
        - role: "Learner"
        - groups: ["Admin","Manager"] or "Admin,Manager"
        - scope/scp: space-separated (e.g., "roles:Admin roles:Learner") - best-effort
    """
    roles: list[Role] = []

    def _consume(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            # Allow CSV or single
            candidates = []
            if "," in value:
                candidates = [p.strip() for p in value.split(",") if p.strip()]
            else:
                candidates = [value.strip()] if value.strip() else []
            for c in candidates:
                roles.append(from_str(c))
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                if item is None:
                    continue
                s = str(item).strip()
                if not s:
                    continue
                roles.append(from_str(s))
            return

    # Direct role claims
    _consume(claims.get("roles"))
    _consume(claims.get("role"))
    _consume(claims.get("groups"))

    # Scope-like claims (best-effort role extraction)
    scope_val = claims.get("scope") or claims.get("scp")
    if isinstance(scope_val, str) and scope_val.strip():
        for part in scope_val.split():
            # allow "role:Admin" / "roles:Admin"
            if ":" in part:
                k, v = part.split(":", 1)
                if k.lower() in {"role", "roles"} and v.strip():
                    try:
                        roles.append(from_str(v.strip()))
                    except ValueError:
                        # ignore non-role scopes
                        pass

    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[Role] = []
    for r in roles:
        if r.value in seen:
            continue
        seen.add(r.value)
        out.append(r)
    return out


def _principal_from_claims(claims: Mapping[str, Any]) -> Principal:
    subject = str(claims.get("sub") or claims.get("oid") or claims.get("user_id") or "").strip()
    if not subject:
        # Subject is required for platform semantics; treat missing subject as invalid token.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required subject claim (sub).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = claims.get("email") or claims.get("preferred_username") or claims.get("upn")
    email_str = str(email).strip() if email is not None and str(email).strip() else None
    roles = _roles_from_claims(claims)
    return Principal(subject=subject, email=email_str, roles=roles)


# PUBLIC_INTERFACE
def clear_jwks_cache() -> None:
    """Clear in-process JWKS client cache (test helper)."""
    _JWKS_CACHE.clear()


# PUBLIC_INTERFACE
def verify_access_token(token: str, *, settings: Settings) -> Principal:
    """Verify an OIDC access token (JWT) using issuer JWKS.

    Validates:
        - Signature via JWKS (kid-aware)
        - exp/nbf (PyJWT defaults verify exp; we also enable nbf)
        - issuer (iss)
        - audience (aud) when OIDC_AUDIENCE is set

    Args:
        token: Raw JWT string.
        settings: Application settings (OIDC_ISSUER, OIDC_JWKS_URI, OIDC_AUDIENCE, OIDC_ALGORITHMS).

    Returns:
        Principal: Parsed principal with subject/email/roles.

    Raises:
        HTTPException: 401 when token is missing/invalid/expired.
        HTTPException: 500 when server config is missing (issuer/jwks).
    """
    cfg = _resolve_jwks_config(settings)
    try:
        jwk_client = _JWKS_CACHE.get(cfg.jwks_uri)
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        # Audience validation is optional (some providers put api://... or client id)
        decode_kwargs: dict[str, Any] = {
            "key": signing_key.key,
            "algorithms": cfg.algorithms,
            "issuer": cfg.issuer,
            "options": {"verify_exp": True, "verify_nbf": True},
        }
        if cfg.audience is not None:
            decode_kwargs["audience"] = cfg.audience
        else:
            decode_kwargs["options"]["verify_aud"] = False

        claims = jwt.decode(token, **decode_kwargs)
        if not isinstance(claims, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token claims are not a JSON object.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return _principal_from_claims(claims)
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected token verification error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# PUBLIC_INTERFACE
def fetch_oidc_jwks_uri_from_issuer(issuer: str, *, timeout_s: float = 5.0) -> str:
    """Fetch JWKS URI from OIDC discovery endpoint.

    Note:
        Not currently used automatically; kept as a helper for future improvements.

    Args:
        issuer: OIDC issuer URL.
        timeout_s: HTTP timeout.

    Returns:
        str: JWKS URI.

    Raises:
        RuntimeError: If discovery fails or response is missing jwks_uri.
    """
    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
        jwks_uri = data.get("jwks_uri")
        if not jwks_uri:
            raise RuntimeError("OIDC discovery response missing jwks_uri")
        return str(jwks_uri)


# PUBLIC_INTERFACE
def unix_time() -> int:
    """Return current unix time (seconds). Test helper."""
    return int(time.time())
