"""
List Tags Use Case
Business logic for listing all tags in an organization
"""

from typing import List
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag


class ListTagsUseCase:
    """List all tags within an organization"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        organization_id: int,
        sort_by: str = "newest",
    ) -> List[Tag]:
        """
        Execute list tags use case

        Args:
            organization_id: Organization ID
            sort_by: Sort order (newest, oldest, name_asc, name_desc)

        Returns:
            List of Tag entities

        Raises:
            ValueError: If sort_by is invalid
        """
        # Validate sort_by parameter
        valid_sorts = ["newest", "oldest", "name_asc", "name_desc"]
        if sort_by not in valid_sorts:
            raise ValueError(
                f"Invalid sort_by value. Must be one of: {', '.join(valid_sorts)}"
            )

        # Get all tags for organization with specified sorting
        tags = self.tag_repo.find_all(organization_id, sort_by)

        return tags
