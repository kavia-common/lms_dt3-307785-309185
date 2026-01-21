from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.security.roles import Role


class Principal(BaseModel):
    """Represents the authenticated principal (user/service) making a request.

    In the full implementation, this would be derived from a validated OIDC/JWT token
    and mapped to platform roles.
    """

    subject: str = Field(..., description="Stable subject identifier (e.g., OIDC sub).")
    roles: list[Role] = Field(default_factory=list, description="Mapped platform roles.")
    email: str | None = Field(default=None, description="Optional email claim (if present).")
