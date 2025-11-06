"""
Delete Tag Use Case
Business logic for deleting a tag
"""

from ..domain.interfaces import ITagRepository
from shared.errors import ValidationError, ConflictError, NotFoundError


class DeleteTagUseCase:
    """Delete a tag from an organization"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_id: int,
        organization_id: int,
        force: bool = False,
    ) -> dict:
        """
        Execute delete tag use case

        Args:
            tag_id: Tag ID to delete
            organization_id: Organization ID
            force: If False, check usage before deletion

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

        # Delete tag
        success = self.tag_repo.delete(tag_id, organization_id)

        if not success:
            raise ConflictError(
                f"Failed to delete tag with ID {tag_id}"
            )

        return {
            "success": True,
            "message": f"Tag '{tag.tag_name}' deleted successfully",
        }
