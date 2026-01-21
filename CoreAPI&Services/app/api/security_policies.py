"""Centralized RBAC policy groupings.

This module defines role group constants that can be reused by routers and services
to enforce consistent, deny-by-default access control.

The constants are composed from the Role enum used by `app.api.deps.require_roles`.
"""

from __future__ import annotations

from typing import FrozenSet

try:
    from app.core.security.roles import Role  # type: ignore
except Exception:  # pragma: no cover
    # Keep compatible with deps.py fallback.
    from enum import Enum

    class Role(str, Enum):
        """Fallback role enum used when canonical Role is not available."""

        LEARNER = "LEARNER"
        EMPLOYEE = "EMPLOYEE"
        INSTRUCTOR = "INSTRUCTOR"
        MANAGER = "MANAGER"
        ADMIN = "ADMIN"
        SUPER_ADMIN = "SUPER_ADMIN"


# Roles allowed to read most resources (broad).
READ_ROLES: FrozenSet[Role] = frozenset(
    {
        Role.LEARNER,
        Role.EMPLOYEE,
        Role.INSTRUCTOR,
        Role.MANAGER,
        Role.ADMIN,
        Role.SUPER_ADMIN,
    }
)

# Roles allowed to create/update resources (more restricted).
WRITE_ROLES: FrozenSet[Role] = frozenset(
    {
        Role.INSTRUCTOR,
        Role.MANAGER,
        Role.ADMIN,
        Role.SUPER_ADMIN,
    }
)

# Roles allowed to perform destructive/admin actions.
ADMIN_ROLES: FrozenSet[Role] = frozenset(
    {
        Role.ADMIN,
        Role.SUPER_ADMIN,
    }
)
