from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.users import UserCreate, UserListResponse, UserRead, UserUpdate


class UsersService:
    """Service stub for Users domain.

    Note: This is a placeholder service that will later be backed by a repository/DB layer.
    """

    # PUBLIC_INTERFACE
    async def list_users(self) -> UserListResponse:
        """List users (placeholder).

        Returns:
            UserListResponse: Placeholder list payload.
        """
        now = datetime.now(tz=timezone.utc)
        return UserListResponse(
            items=[
                UserRead(id="usr_1", name="Placeholder User", created_at=now, updated_at=now),
            ],
            total=1,
        )

    # PUBLIC_INTERFACE
    async def get_user(self, user_id: str) -> UserRead:
        """Get a user by id (placeholder).

        Args:
            user_id: User identifier.

        Returns:
            UserRead: Placeholder user record.
        """
        now = datetime.now(tz=timezone.utc)
        return UserRead(id=user_id, name="Placeholder User", created_at=now, updated_at=now)

    # PUBLIC_INTERFACE
    async def create_user(self, payload: UserCreate) -> UserRead:
        """Create a user (placeholder).

        Args:
            payload: User create payload.

        Returns:
            UserRead: Created placeholder user record.
        """
        now = datetime.now(tz=timezone.utc)
        return UserRead(id="usr_new", name=payload.name, created_at=now, updated_at=now)

    # PUBLIC_INTERFACE
    async def update_user(self, user_id: str, payload: UserUpdate) -> UserRead:
        """Update a user (placeholder).

        Args:
            user_id: User identifier.
            payload: User update payload.

        Returns:
            UserRead: Updated placeholder user record.
        """
        now = datetime.now(tz=timezone.utc)
        return UserRead(
            id=user_id,
            name=payload.name or "Placeholder User",
            created_at=now,
            updated_at=now,
        )

    # PUBLIC_INTERFACE
    async def delete_user(self, user_id: str) -> dict:
        """Delete a user (placeholder).

        Args:
            user_id: User identifier.

        Returns:
            dict: Simple confirmation payload.
        """
        return {"deleted": True, "id": user_id}
