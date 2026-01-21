from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentBase(BaseModel):
    """Shared assessment fields."""

    title: str = Field(..., min_length=1, description="Assessment title (e.g., quiz/test name).")
    course_id: str | None = Field(
        default=None,
        description="Optional related course identifier (string form of ObjectId).",
    )
    module_id: str | None = Field(
        default=None,
        description="Optional related module identifier (string form of ObjectId).",
    )


class AssessmentCreate(AssessmentBase):
    """Payload to create an assessment."""

    pass


class AssessmentUpdate(BaseModel):
    """Payload to update an assessment."""

    title: str | None = Field(default=None, min_length=1, description="Updated assessment title.")
    course_id: str | None = Field(
        default=None, description="Updated related course identifier (string form of ObjectId)."
    )
    module_id: str | None = Field(
        default=None, description="Updated related module identifier (string form of ObjectId)."
    )


class AssessmentRead(AssessmentBase):
    """Assessment response model."""

    id: str = Field(..., description="Assessment identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the assessment was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the assessment was last updated.")
    deleted_at: datetime | None = Field(default=None, description="UTC timestamp when the assessment was soft-deleted.")


class AssessmentListResponse(BaseModel):
    """List assessments response envelope."""

    items: list[AssessmentRead] = Field(default_factory=list, description="List of assessments.")
    total: int = Field(..., ge=0, description="Total number of matching assessments (after filters).")
    skip: int = Field(default=0, ge=0, description="Number of items skipped (pagination offset).")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of items returned.")
