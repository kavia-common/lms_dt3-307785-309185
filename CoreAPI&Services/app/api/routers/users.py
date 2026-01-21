from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
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
    description="List users (placeholder). No auth enforced yet.",
    response_model=UserListResponse,
    operation_id="listUsers",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination page size."),
    service: UsersService = Depends(get_users_service),
) -> UserListResponse:
    # PUBLIC_INTERFACE
    """List users.

    Args:
        service: UsersService dependency.

    Returns:
        UserListResponse: Placeholder list payload.
    """
    return await service.list_users(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    summary="Get user by id",
    description="Fetch a single user (placeholder). No auth enforced yet.",
    response_model=UserRead,
    operation_id="getUserById",
)
async def get_user(user_id: str, service: UsersService = Depends(get_users_service)) -> UserRead:
    # PUBLIC_INTERFACE
    """Get a user by id.

    Args:
        user_id: User identifier.
        service: UsersService dependency.

    Returns:
        UserRead: Placeholder user record.
    """
    return await service.get_user(user_id)


@router.post(
    "",
    summary="Create user",
    description="Create a user (placeholder). No auth enforced yet.",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUser",
)
async def create_user(
    payload: UserCreate,
    service: UsersService = Depends(get_users_service),
) -> UserRead:
    # PUBLIC_INTERFACE
    """Create a user.

    Args:
        payload: User creation payload.
        service: UsersService dependency.

    Returns:
        UserRead: Created placeholder user record.
    """
    return await service.create_user(payload)


@router.put(
    "/{user_id}",
    summary="Update user",
    description="Update a user (placeholder). No auth enforced yet.",
    response_model=UserRead,
    operation_id="updateUser",
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    service: UsersService = Depends(get_users_service),
) -> UserRead:
    # PUBLIC_INTERFACE
    """Update a user.

    Args:
        user_id: User identifier.
        payload: User update payload.
        service: UsersService dependency.

    Returns:
        UserRead: Updated placeholder user record.
    """
    return await service.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    summary="Delete user",
    description="Delete a user (placeholder). No auth enforced yet.",
    operation_id="deleteUser",
)
async def delete_user(user_id: str, service: UsersService = Depends(get_users_service)) -> dict:
    # PUBLIC_INTERFACE
    """Delete a user.

    Args:
        user_id: User identifier.
        service: UsersService dependency.

    Returns:
        dict: Confirmation payload.
    """
    return await service.delete_user(user_id)
