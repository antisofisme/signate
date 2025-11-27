"""
Delete Playlist Use Case
"""

from typing import Optional
from ..domain.interfaces import IPlaylistRepository


class DeletePlaylistUseCase:
    """Delete playlist (soft delete with audit tracking)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        organization_id: int,
        deleted_by_id: Optional[int] = None
    ) -> bool:
        """
        Soft delete playlist with audit tracking

        Args:
            playlist_id: Playlist ID to delete
            organization_id: Organization ID for ownership check
            deleted_by_id: User ID who deleted the playlist (audit trail)

        Returns:
            True if deleted, False if not found
        """
        return self.playlist_repo.delete(
            playlist_id=playlist_id,
            organization_id=organization_id,
            soft=True,  # Soft delete for audit trail
            deleted_by_id=deleted_by_id
        )
