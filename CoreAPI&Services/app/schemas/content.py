from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ContentBase(BaseModel):
    """Shared content fields."""

    title: str = Field(..., description="Content title (e.g., course/module/lesson title).")


class ContentCreate(ContentBase):
    """Payload to create content."""

    pass


class ContentUpdate(BaseModel):
    """Payload to update content."""

    title: str | None = Field(default=None, description="Updated content title.")


class ContentRead(ContentBase):
    """Content response model."""

    id: str = Field(..., description="Content identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the content was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the content was last updated.")


class ContentListResponse(BaseModel):
    """List content response envelope."""

    items: list[ContentRead] = Field(default_factory=list, description="List of content items.")
    total: int = Field(..., description="Total number of content items returned (placeholder).")
