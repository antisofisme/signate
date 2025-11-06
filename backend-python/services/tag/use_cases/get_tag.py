"""
Get Tag Use Case
Business logic for retrieving a single tag with usage statistics
"""

from typing import Optional
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag
from shared.errors import ValidationError, ConflictError, NotFoundError


class GetTagUseCase:
    """Get a single tag by ID within an organization"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_id: int,
        organization_id: int,
        include_usage: bool = False,
    ) -> dict:
        """
        Execute get tag use case

        Args:
            tag_id: Tag ID
            organization_id: Organization ID
            include_usage: Whether to include usage statistics

        Returns:
            Dictionary containing tag entity and optional usage stats

        Raises:
            AppError: If tag not found
        """
        # Find tag by ID
        tag = self.tag_repo.find_by_id(tag_id, organization_id)

        if not tag:
            raise NotFoundError(
                f"Tag with ID {tag_id} not found"
            )

        result = {
            "tag": tag,
        }

        # Include usage statistics if requested
        if include_usage:
            usage = self.tag_repo.get_tag_usage_count(tag_id, organization_id)
            result["usage"] = usage

        return result
