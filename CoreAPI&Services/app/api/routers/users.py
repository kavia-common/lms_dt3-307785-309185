from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import require_roles
from app.api.security_policies import ADMIN_ROLES, READ_ROLES, WRITE_ROLES
from app.core.db import get_db
from app.schemas.security import Principal
from app.schemas.users import UserCreate, UserListResponse, UserRead, UserUpdate
from app.services.users import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


def get_users_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> UsersService:
    """Dependency provider for UsersService (MongoDB-backed).

    This is intentionally declared as a FastAPI dependency callable so tests can
    override it via `app.dependency_overrides[get_users_service] = ...` without
    triggering MongoDB initialization.
    """
    return UsersService(db=db)


@router.get(
    "",
    summary="List users",
    description="List users. Requires authenticated user with a read role.",
    response_model=UserListResponse,
    operation_id="listUsers",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination page size."),
    service: UsersService = Depends(get_users_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> UserListResponse:
    # PUBLIC_INTERFACE
    """List users.

    Args:
        service: UsersService dependency.

    Returns:
        UserListResponse: Paginated users list.
    """
    return await service.list_users(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    summary="Get user by id",
    description="Fetch a single user by id. Requires authenticated user with a read role.",
    response_model=UserRead,
    operation_id="getUserById",
)
async def get_user(
    user_id: str,
    service: UsersService = Depends(get_users_service),
    _principal: Principal = Depends(require_roles(*READ_ROLES)),
) -> UserRead:
    # PUBLIC_INTERFACE
    """Get a user by id.

    Args:
        user_id: User identifier.
        service: UsersService dependency.

    Returns:
        UserRead: User record.
    """
    return await service.get_user(user_id)


@router.post(
    "",
    summary="Create user",
    description="Create a user. Requires authenticated user with a write role.",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUser",
)
async def create_user(
    payload: UserCreate,
    service: UsersService = Depends(get_users_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> UserRead:
    # PUBLIC_INTERFACE
    """Create a user.

    Args:
        payload: User creation payload.
        service: UsersService dependency.

    Returns:
        UserRead: Created user record.
    """
    return await service.create_user(payload)


@router.put(
    "/{user_id}",
    summary="Update user",
    description="Update a user. Requires authenticated user with a write role.",
    response_model=UserRead,
    operation_id="updateUser",
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    service: UsersService = Depends(get_users_service),
    _principal: Principal = Depends(require_roles(*WRITE_ROLES)),
) -> UserRead:
    # PUBLIC_INTERFACE
    """Update a user.

    Args:
        user_id: User identifier.
        payload: User update payload.
        service: UsersService dependency.

    Returns:
        UserRead: Updated user record.
    """
    return await service.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    summary="Delete user",
    description="Soft-delete a user. Requires authenticated admin role.",
    operation_id="deleteUser",
)
async def delete_user(
    user_id: str,
    service: UsersService = Depends(get_users_service),
    _principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
) -> dict:
    # PUBLIC_INTERFACE
    """Delete a user.

    Args:
        user_id: User identifier.
        service: UsersService dependency.

    Returns:
        dict: Confirmation payload.
    """
    return await service.delete_user(user_id)
