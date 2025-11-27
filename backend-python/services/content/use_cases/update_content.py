"""
Update Content Use Case
Business logic for updating content metadata
"""

from typing import Optional
from ..domain.content import Content
from ..domain.interfaces import IContentRepository


class UpdateContentUseCase:
    """Update content metadata"""

    def __init__(self, content_repo: IContentRepository):
        self.content_repo = content_repo

    def execute(
        self,
        content_id: int,
        organization_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        duration: Optional[int] = None,
        is_active: Optional[bool] = None,
        updated_by_id: Optional[int] = None
    ) -> Content:
        """
        Update content metadata

        Args:
            content_id: Content ID to update
            organization_id: Organization ID for ownership check
            title: New title (optional)
            description: New description (optional)
            duration: New duration in seconds (optional)
            is_active: New active status (optional)
            updated_by_id: User ID who updated the content (audit trail)

        Returns:
            Updated Content entity

        Raises:
            ValueError: If content not found or access denied
        """

        # Get existing content
        content = self.content_repo.find_by_id(content_id)

        if not content:
            raise ValueError(f"Content with ID {content_id} not found")

        # Check organization ownership
        if content.organization_id != organization_id:
            raise ValueError("Access denied: Content belongs to different organization")

        # Update only provided fields
        if title is not None:
            content.title = title

        if description is not None:
            content.description = description

        if duration is not None:
            if duration < 1 or duration > 86400:
                raise ValueError("Duration must be between 1 and 86400 seconds")
            content.duration = duration

        if is_active is not None:
            content.is_active = is_active

        # Validate and save
        content.__post_init__()
        updated_content = self.content_repo.update(content, updated_by_id=updated_by_id)

        return updated_content
