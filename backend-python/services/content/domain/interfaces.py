"""
Content Repository Interface
Contract for content data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from .content import Content


class IContentRepository(ABC):
    """Content repository interface"""

    @abstractmethod
    def create(self, content: Content) -> Content:
        """
        Create new content

        Args:
            content: Content entity to create

        Returns:
            Created content with ID
        """
        pass

    @abstractmethod
    def find_by_id(self, content_id: int, organization_id: int) -> Optional[Content]:
        """
        Find content by ID (organization-scoped)

        Args:
            content_id: Content ID
            organization_id: Organization ID (for multi-tenant isolation)

        Returns:
            Content entity or None if not found
        """
        pass

    @abstractmethod
    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Content], int]:
        """
        List content with filters (organization-scoped)

        Args:
            organization_id: Organization ID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            content_type: Filter by type ('image', 'video', 'audio')
            is_active: Filter by active status

        Returns:
            Tuple of (content list, total count)
        """
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str, organization_id: int) -> Optional[Content]:
        """
        Find content by file hash (deduplication check)

        Args:
            file_hash: SHA256 hash of file
            organization_id: Organization ID

        Returns:
            Content entity or None if not found
        """
        pass

    @abstractmethod
    def update(self, content: Content) -> Content:
        """
        Update content metadata

        Args:
            content: Content entity with updated values

        Returns:
            Updated content entity
        """
        pass

    @abstractmethod
    def soft_delete(self, content_id: int, organization_id: int) -> bool:
        """
        Soft delete content (set deleted_at timestamp)

        Args:
            content_id: Content ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def find_deleted_content(self, days: int = 30) -> List[Content]:
        """
        Find soft-deleted content older than specified days
        (for cleanup task)

        Args:
            days: Number of days threshold

        Returns:
            List of deleted content
        """
        pass

    @abstractmethod
    def hard_delete(self, content_id: int) -> bool:
        """
        Permanently delete content from database
        (for cleanup task)

        Args:
            content_id: Content ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def get_storage_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for organization

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with statistics:
            {
                'total_files': int,
                'total_size_bytes': int,
                'by_type': {
                    'image': {'count': int, 'size_bytes': int},
                    'video': {'count': int, 'size_bytes': int},
                    'audio': {'count': int, 'size_bytes': int}
                }
            }
        """
        pass

    @abstractmethod
    def update_transcoding_status(
        self,
        content_id: int,
        status: str,
        job_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update transcoding status

        Args:
            content_id: Content ID
            status: Transcoding status ('processing', 'completed', 'failed')
            job_id: Celery job ID
            error: Error message (if failed)

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    def update_hls_info(
        self,
        content_id: int,
        master_playlist_path: str,
        master_playlist_url: str,
        variants: Dict[str, Any]
    ) -> bool:
        """
        Update HLS transcoding information

        Args:
            content_id: Content ID
            master_playlist_path: Path to master.m3u8
            master_playlist_url: URL to master.m3u8
            variants: HLS variants information

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    def update_thumbnail(
        self,
        content_id: int,
        thumbnail_path: str,
        thumbnail_url: str
    ) -> bool:
        """
        Update thumbnail information

        Args:
            content_id: Content ID
            thumbnail_path: Path to thumbnail file
            thumbnail_url: URL to thumbnail

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    def find_duplicates_with_usage(self, organization_id: int) -> List[Dict[str, Any]]:
        """
        Find duplicate files (same hash) with their usage info.

        Args:
            organization_id: Organization ID

        Returns:
            List of duplicate groups with content and usage info
        """
        pass
