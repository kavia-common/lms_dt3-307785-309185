from __future__ import annotations

from app.core.security.roles import Role

# Domain policy choices (can evolve into fine-grained policies later).
# - Read operations: Learner + above (plus Employee to match platform enum)
# - Write operations: Instructor + above

READ_ROLES = (Role.LEARNER, Role.EMPLOYEE, Role.INSTRUCTOR, Role.MANAGER, Role.ADMIN, Role.SUPERADMIN)
WRITE_ROLES = (Role.INSTRUCTOR, Role.MANAGER, Role.ADMIN, Role.SUPERADMIN)
ADMIN_ROLES = (Role.ADMIN, Role.SUPERADMIN)
