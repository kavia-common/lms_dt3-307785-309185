from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    name: str = Field(..., min_length=1, description="Display name for the user.")
    email: EmailStr = Field(..., description="Unique email address for the user.")


class UserCreate(UserBase):
    """Payload to create a user."""

    pass


class UserUpdate(BaseModel):
    """Payload to update a user."""

    name: str | None = Field(default=None, min_length=1, description="Updated display name for the user.")
    email: EmailStr | None = Field(default=None, description="Updated email for the user.")


class UserRead(UserBase):
    """User response model."""

    id: str = Field(..., description="User identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the user was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the user was last updated.")
    deleted_at: datetime | None = Field(default=None, description="UTC timestamp when the user was soft-deleted.")


class UserListResponse(BaseModel):
    """List users response envelope."""

    items: list[UserRead] = Field(default_factory=list, description="List of users.")
    total: int = Field(..., ge=0, description="Total number of matching users (after filters).")
    skip: int = Field(default=0, ge=0, description="Number of items skipped (pagination offset).")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of items returned.")
