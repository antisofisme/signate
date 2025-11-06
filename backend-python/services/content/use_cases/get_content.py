"""
Get Content Use Case
"""

from typing import Optional
from ..domain.content import Content
from ..domain.interfaces import IContentRepository


class GetContentUseCase:
    """Get single content by ID"""

    def __init__(self, content_repo: IContentRepository):
        self.content_repo = content_repo

    def execute(self, content_id: int, organization_id: int) -> Optional[Content]:
        """
        Get content by ID (organization-scoped)

        Args:
            content_id: Content ID to retrieve
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Content entity

        Raises:
            ValueError: If content not found
        """
        content = self.content_repo.find_by_id(content_id, organization_id)

        if not content:
            raise ValueError(f"Content {content_id} not found")

        return content
