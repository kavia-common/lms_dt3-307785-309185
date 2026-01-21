from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ContentBase(BaseModel):
    """Shared content fields."""

    title: str = Field(..., min_length=1, description="Content title (e.g., course/module/lesson title).")
    slug: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe unique-ish slug for the content (kebab-case).",
    )


class ContentCreate(ContentBase):
    """Payload to create content."""

    pass


class ContentUpdate(BaseModel):
    """Payload to update content."""

    title: str | None = Field(default=None, min_length=1, description="Updated content title.")
    slug: str | None = Field(
        default=None,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Updated slug (kebab-case).",
    )


class ContentRead(ContentBase):
    """Content response model."""

    id: str = Field(..., description="Content identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the content was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the content was last updated.")
    deleted_at: datetime | None = Field(default=None, description="UTC timestamp when the content was soft-deleted.")


class ContentListResponse(BaseModel):
    """List content response envelope."""

    items: list[ContentRead] = Field(default_factory=list, description="List of content items.")
    total: int = Field(..., ge=0, description="Total number of matching content items (after filters).")
    skip: int = Field(default=0, ge=0, description="Number of items skipped (pagination offset).")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of items returned.")
