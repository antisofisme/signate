"""
Playlist Repository Interfaces
Contracts for data access layer
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from .playlist import Playlist, PlaylistContent, PlaylistAssignment


class IPlaylistRepository(ABC):
    """Playlist repository interface"""

    # ========== Playlist CRUD ==========

    @abstractmethod
    def create(self, playlist: Playlist) -> Playlist:
        """Create new playlist"""
        pass

    @abstractmethod
    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Playlist], int]:
        """Find all playlists with pagination and filters"""
        pass

    @abstractmethod
    def find_by_id(self, playlist_id: int, organization_id: int) -> Optional[Playlist]:
        """Find playlist by ID (with organization filter)"""
        pass

    @abstractmethod
    def find_by_name(self, name: str, organization_id: int) -> Optional[Playlist]:
        """Find playlist by name (with organization filter, excludes soft-deleted)"""
        pass

    @abstractmethod
    def update(self, playlist: Playlist) -> Playlist:
        """Update playlist"""
        pass

    @abstractmethod
    def delete(self, playlist_id: int, organization_id: int, soft: bool = False) -> bool:
        """Delete playlist (soft or hard)"""
        pass

    # ========== Content Management ==========

    @abstractmethod
    def get_playlist_contents(
        self,
        playlist_id: int,
        organization_id: int
    ) -> List[PlaylistContent]:
        """Get all content items in playlist (ordered)"""
        pass

    @abstractmethod
    def add_contents_to_playlist(
        self,
        playlist_id: int,
        content_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Bulk add content to playlist
        Returns: {added: int, skipped_missing: [], skipped_duplicate: []}
        """
        pass

    @abstractmethod
    def remove_content_from_playlist(
        self,
        playlist_content_id: int,
        playlist_id: int,
        organization_id: int
    ) -> bool:
        """Remove content item from playlist"""
        pass

    @abstractmethod
    def reorder_playlist_contents(
        self,
        playlist_id: int,
        content_items: List[Dict[str, Any]],
        organization_id: int
    ) -> int:
        """
        Bulk reorder content items
        content_items: [{"id": 1, "order_index": 0, "duration": 30}, ...]
        Returns: number of updated items
        """
        pass

    # ========== Device/Tag Assignments ==========

    @abstractmethod
    def get_playlist_assignments(
        self,
        playlist_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Get all assignments for playlist
        Returns: {"devices": [...], "tags": [...]}
        """
        pass

    @abstractmethod
    def assign_to_devices(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Bulk assign playlist to devices
        Returns: {assigned: int, skipped_missing: [], skipped_duplicate: []}
        """
        pass

    @abstractmethod
    def assign_to_tags(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Bulk assign playlist to tags
        Returns: {assigned: int, skipped_missing: [], skipped_duplicate: []}
        """
        pass

    @abstractmethod
    def unassign_from_devices(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int
    ) -> int:
        """Bulk unassign from devices. Returns: removed count"""
        pass

    @abstractmethod
    def unassign_from_tags(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int
    ) -> int:
        """Bulk unassign from tags. Returns: removed count"""
        pass

    # ========== Utility Methods ==========

    @abstractmethod
    def calculate_playlist_stats(
        self,
        playlist_id: int,
        organization_id: int
    ) -> Dict[str, int]:
        """
        Calculate playlist statistics
        Returns: {"content_count": int, "total_duration": int}
        """
        pass

    @abstractmethod
    def duplicate(
        self,
        playlist_id: int,
        organization_id: int,
        new_name: str,
        created_by_id: Optional[int] = None,
    ) -> Optional['Playlist']:
        """
        Duplicate a playlist with all its contents
        Returns the new duplicated playlist or None if source not found
        """
        pass
