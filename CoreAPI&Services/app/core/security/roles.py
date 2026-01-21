from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Platform role enumeration used for RBAC.

    This list mirrors the platform roles described in the system brief and will be used
    for both API authorization policies and UI/route guards.
    """

    LEARNER = "Learner"
    EMPLOYEE = "Employee"
    INSTRUCTOR = "Instructor"
    MANAGER = "Manager"
    SUPERADMIN = "SuperAdmin"
    ADMIN = "Admin"


# PUBLIC_INTERFACE
def from_str(value: str) -> Role:
    """Parse a Role from a string.

    Accepts case-insensitive matches and supports a few common separators.

    Args:
        value: Role name string (e.g. "learner", "SuperAdmin", "super_admin").

    Returns:
        Role: Parsed Role.

    Raises:
        ValueError: If the role string does not match any known role.
    """
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError("Role string is empty")

    normalized_key = normalized.replace("-", "_").replace(" ", "_").upper()
    for role in Role:
        if role.name == normalized_key:
            return role
        if role.value.lower() == normalized.lower():
            return role

    raise ValueError(f"Unknown role: {value}")


# PUBLIC_INTERFACE
def list_all() -> list[Role]:
    """List all platform roles in a stable order."""
    return [
        Role.LEARNER,
        Role.EMPLOYEE,
        Role.INSTRUCTOR,
        Role.MANAGER,
        Role.SUPERADMIN,
        Role.ADMIN,
    ]
