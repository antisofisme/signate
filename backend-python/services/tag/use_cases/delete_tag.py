"""
Delete Tag Use Case
Business logic for deleting a tag (soft delete)
"""

from typing import Optional
from ..domain.interfaces import ITagRepository
from shared.errors import ValidationError, ConflictError, NotFoundError


class DeleteTagUseCase:
    """Delete a tag from an organization (soft delete)"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_id: int,
        organization_id: int,
        force: bool = False,
        deleted_by_id: Optional[int] = None,
    ) -> dict:
        """
        Execute delete tag use case (soft delete)

        Args:
            tag_id: Tag ID to delete
            organization_id: Organization ID
            force: If False, check usage before deletion
            deleted_by_id: User ID who deleted the tag (audit trail)

        Returns:
            Dictionary with success status and message

        Raises:
            AppError: If tag not found or has active usage
        """
        # Check if tag exists
        tag = self.tag_repo.find_by_id(tag_id, organization_id)
        if not tag:
            raise NotFoundError(
                f"Tag with ID {tag_id} not found"
            )

        # Business rule: Check usage before deletion (unless forced)
        if not force:
            usage = self.tag_repo.get_tag_usage_count(tag_id, organization_id)
            device_count = usage.get("device_count", 0)
            content_count = usage.get("content_count", 0)

            if device_count > 0 or content_count > 0:
                raise ConflictError(
                    f"Cannot delete tag '{tag.tag_name}'. "
                    f"It is currently used by {device_count} device(s) "
                    f"and {content_count} content item(s). "
                    f"Please remove tag assignments first or use force=true."
                )

        # Soft delete tag with audit tracking
        success = self.tag_repo.delete(tag_id, organization_id, deleted_by_id=deleted_by_id)

        if not success:
            raise ConflictError(
                f"Failed to delete tag with ID {tag_id}"
            )

        return {
            "success": True,
            "message": f"Tag '{tag.tag_name}' deleted successfully",
        }
