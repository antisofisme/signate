"""
Get Playlist Use Case
"""

from typing import Optional
from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository


class GetPlaylistUseCase:
    """Get single playlist by ID with organization validation"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(self, playlist_id: int, organization_id: int) -> Optional[Playlist]:
        """
        Get playlist by ID

        Returns:
            Playlist or None if not found / access denied
        """
        return self.playlist_repo.find_by_id(playlist_id, organization_id)
