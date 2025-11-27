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
        updated_by_id: Optional[int] = None,
    ) -> Playlist:
        """
        Update playlist

        Args:
            playlist_id: Playlist ID to update
            organization_id: Organization ID for ownership check
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)
            priority: New priority (optional)
            schedule: New schedule (optional)
            updated_by_id: User ID who updated the playlist (audit trail)

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

        # Persist changes with audit tracking
        return self.playlist_repo.update(playlist, updated_by_id=updated_by_id)
