from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentBase(BaseModel):
    """Shared assessment fields."""

    title: str = Field(..., description="Assessment title (e.g., quiz/test name).")


class AssessmentCreate(AssessmentBase):
    """Payload to create an assessment."""

    pass


class AssessmentUpdate(BaseModel):
    """Payload to update an assessment."""

    title: str | None = Field(default=None, description="Updated assessment title.")


class AssessmentRead(AssessmentBase):
    """Assessment response model."""

    id: str = Field(..., description="Assessment identifier.")
    created_at: datetime = Field(..., description="UTC timestamp when the assessment was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the assessment was last updated.")


class AssessmentListResponse(BaseModel):
    """List assessments response envelope."""

    items: list[AssessmentRead] = Field(default_factory=list, description="List of assessments.")
    total: int = Field(..., description="Total number of assessments returned (placeholder).")
