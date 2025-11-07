"""
Update Playlist Use Case
"""

from typing import Optional, Dict, Any
from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository


class UpdatePlaylistUseCase:
    """Update playlist details"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        organization_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> Playlist:
        """
        Update playlist

        Raises:
            ValueError: If playlist not found or validation fails
        """
        # Get existing playlist
        playlist = self.playlist_repo.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Update with validation
        playlist.update_details(
            name=name,
            description=description,
            is_active=is_active,
            priority=priority,
            schedule=schedule,
        )

        # Persist changes
        return self.playlist_repo.update(playlist)
