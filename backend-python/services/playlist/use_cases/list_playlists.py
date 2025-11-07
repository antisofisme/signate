"""
List Playlists Use Case
"""

from typing import List, Tuple, Optional
from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository


class ListPlaylistsUseCase:
    """List playlists with organization filter and pagination"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Playlist], int]:
        """
        Get all playlists for organization

        Returns:
            Tuple of (playlists, total_count)
        """
        return self.playlist_repo.find_all(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            is_active=is_active,
            include_deleted=include_deleted,
        )
