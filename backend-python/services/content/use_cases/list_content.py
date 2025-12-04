"""
List Content Use Case
"""

from typing import Tuple, List, Optional
from ..domain.content import Content
from ..domain.interfaces import IContentRepository


class ListContentUseCase:
    """List content with filters and pagination"""

    def __init__(self, content_repo: IContentRepository):
        self.content_repo = content_repo

    def execute(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[Content], int]:
        """
        List content with filters

        Args:
            organization_id: Organization ID for multi-tenant filtering
            skip: Offset for pagination (default 0)
            limit: Number of records (default 20)
            content_type: Filter by type (image/video/audio)
            is_active: Filter by active status
            tag_ids: Filter by tag IDs (content must have ALL specified tags)
            sort_by: Column to sort by
            sort_dir: Sort direction ('asc' or 'desc')

        Returns:
            Tuple of (content list, total count)
        """
        return self.content_repo.find_all(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            content_type=content_type,
            is_active=is_active,
            tag_ids=tag_ids,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
