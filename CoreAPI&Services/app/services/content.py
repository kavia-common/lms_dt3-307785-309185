from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.content import ContentCreate, ContentListResponse, ContentRead, ContentUpdate


class ContentService:
    """Service stub for Content domain.

    Note: This is a placeholder service that will later be backed by a repository/DB layer.
    """

    # PUBLIC_INTERFACE
    async def list_content(self) -> ContentListResponse:
        """List content items (placeholder).

        Returns:
            ContentListResponse: Placeholder list payload.
        """
        now = datetime.now(tz=timezone.utc)
        return ContentListResponse(
            items=[
                ContentRead(id="cnt_1", title="Placeholder Content", created_at=now, updated_at=now),
            ],
            total=1,
        )

    # PUBLIC_INTERFACE
    async def get_content(self, content_id: str) -> ContentRead:
        """Get a content item by id (placeholder).

        Args:
            content_id: Content identifier.

        Returns:
            ContentRead: Placeholder content record.
        """
        now = datetime.now(tz=timezone.utc)
        return ContentRead(id=content_id, title="Placeholder Content", created_at=now, updated_at=now)

    # PUBLIC_INTERFACE
    async def create_content(self, payload: ContentCreate) -> ContentRead:
        """Create content (placeholder).

        Args:
            payload: Content create payload.

        Returns:
            ContentRead: Created placeholder content record.
        """
        now = datetime.now(tz=timezone.utc)
        return ContentRead(id="cnt_new", title=payload.title, created_at=now, updated_at=now)

    # PUBLIC_INTERFACE
    async def update_content(self, content_id: str, payload: ContentUpdate) -> ContentRead:
        """Update content (placeholder).

        Args:
            content_id: Content identifier.
            payload: Content update payload.

        Returns:
            ContentRead: Updated placeholder content record.
        """
        now = datetime.now(tz=timezone.utc)
        return ContentRead(
            id=content_id,
            title=payload.title or "Placeholder Content",
            created_at=now,
            updated_at=now,
        )

    # PUBLIC_INTERFACE
    async def delete_content(self, content_id: str) -> dict:
        """Delete content (placeholder).

        Args:
            content_id: Content identifier.

        Returns:
            dict: Simple confirmation payload.
        """
        return {"deleted": True, "id": content_id}
