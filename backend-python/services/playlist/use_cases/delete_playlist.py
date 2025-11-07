"""
Delete Playlist Use Case
"""

from ..domain.interfaces import IPlaylistRepository


class DeletePlaylistUseCase:
    """Delete playlist (hard delete with cascade)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(self, playlist_id: int, organization_id: int) -> bool:
        """
        Delete playlist permanently
        Cascades to playlist_contents and playlist_assignments

        Returns:
            True if deleted, False if not found
        """
        return self.playlist_repo.delete(
            playlist_id=playlist_id,
            organization_id=organization_id,
            soft=False  # Hard delete
        )
