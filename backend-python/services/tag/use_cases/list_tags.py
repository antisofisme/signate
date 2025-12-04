"""
List Tags Use Case
Business logic for listing all tags in an organization
"""

from typing import List, Optional
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
        sort_dir: Optional[str] = None,
    ) -> List[Tag]:
        """
        Execute list tags use case

        Args:
            organization_id: Organization ID
            sort_by: Sort by column (tag_name, created_at, content_count, device_count)
                     or legacy format (newest, oldest, name_asc, name_desc)
            sort_dir: Sort direction (asc, desc) - only used with standard sort_by values

        Returns:
            List of Tag entities

        Raises:
            ValueError: If sort_by or sort_dir is invalid
        """
        # Standard sortable columns
        standard_sorts = ["tag_name", "created_at", "content_count", "device_count"]
        # Legacy sort values
        legacy_sorts = ["newest", "oldest", "name_asc", "name_desc"]

        # Validate sort_dir if provided
        if sort_dir is not None:
            if sort_dir not in ["asc", "desc"]:
                raise ValueError("Invalid sort_dir value. Must be 'asc' or 'desc'")
            # When sort_dir is provided, sort_by should be a standard column
            if sort_by not in standard_sorts:
                # Map legacy sort_by to standard if sort_dir is provided
                if sort_by in legacy_sorts:
                    # Ignore legacy value, use default
                    sort_by = "created_at"
        else:
            # Legacy format - validate sort_by
            if sort_by not in legacy_sorts and sort_by not in standard_sorts:
                raise ValueError(
                    f"Invalid sort_by value. Must be one of: {', '.join(legacy_sorts + standard_sorts)}"
                )

        # Get all tags for organization with specified sorting
        tags = self.tag_repo.find_all(organization_id, sort_by, sort_dir)

        return tags
