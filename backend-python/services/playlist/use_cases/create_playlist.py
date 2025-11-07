"""
Create Playlist Use Case
"""

from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository


class CreatePlaylistUseCase:
    """Create a new playlist with organization validation"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        name: str,
        organization_id: int,
        description: str | None = None,
        is_active: bool = True,
        priority: int = 0,
        schedule: dict | None = None,
        created_by: int | None = None,
    ) -> Playlist:
        """
        Create new playlist

        Raises:
            ValueError: If validation fails
        """
        # Create domain entity (with validation)
        playlist = Playlist(
            name=name,
            description=description,
            is_active=is_active,
            priority=priority,
            schedule=schedule,
            organization_id=organization_id,
            created_by=created_by,
        )

        # Persist to database
        return self.playlist_repo.create(playlist)
