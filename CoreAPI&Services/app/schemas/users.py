from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Shared user fields."""

    name: str = Field(..., description="Display name for the user.")


class UserCreate(UserBase):
    """Payload to create a user."""

    pass


class UserUpdate(BaseModel):
    """Payload to update a user."""

    name: str | None = Field(default=None, description="Updated display name for the user.")


class UserRead(UserBase):
    """User response model."""

    id: str = Field(..., description="User identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the user was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the user was last updated.")


class UserListResponse(BaseModel):
    """List users response envelope."""

    items: list[UserRead] = Field(default_factory=list, description="List of users.")
    total: int = Field(..., description="Total number of users returned (placeholder).")
