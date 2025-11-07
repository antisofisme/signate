"""
Get Content Tags Use Case
Business logic for retrieving tags assigned to a content item
"""

from typing import List
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag


class GetContentTagsUseCase:
    """Get all tags assigned to a content item"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(self, content_id: int, organization_id: int) -> List[Tag]:
        """
        Get all tags for a content item

        Returns:
            List of Tag entities
        """
        try:
            tags = self.tag_repo.get_content_tags(content_id, organization_id)
            return tags

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Failed to get content tags: {str(e)}")
