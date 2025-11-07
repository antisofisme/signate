"""
Playlist Content Management Use Cases
Bundled: add, get, remove, reorder content
"""

from typing import List, Dict, Any
from ..domain.playlist import PlaylistContent
from ..domain.interfaces import IPlaylistRepository


class AddContentToPlaylistUseCase:
    """Add content items to playlist (bulk)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        content_ids: List[int],
        organization_id: int,
    ) -> Dict[str, Any]:
        """
        Bulk add content to playlist

        Returns:
            {"added": int, "skipped_missing": [], "skipped_duplicate": []}
        """
        if not content_ids:
            raise ValueError("content_ids cannot be empty")

        return self.playlist_repo.add_contents_to_playlist(
            playlist_id=playlist_id,
            content_ids=content_ids,
            organization_id=organization_id,
        )


class GetPlaylistContentUseCase:
    """Get all content items in playlist"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        organization_id: int,
    ) -> List[PlaylistContent]:
        """Get playlist content items (ordered)"""
        return self.playlist_repo.get_playlist_contents(
            playlist_id=playlist_id,
            organization_id=organization_id,
        )


class RemoveContentFromPlaylistUseCase:
    """Remove content item from playlist"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_content_id: int,
        playlist_id: int,
        organization_id: int,
    ) -> bool:
        """
        Remove content from playlist

        Returns:
            True if removed, False if not found
        """
        return self.playlist_repo.remove_content_from_playlist(
            playlist_content_id=playlist_content_id,
            playlist_id=playlist_id,
            organization_id=organization_id,
        )


class ReorderPlaylistContentUseCase:
    """Reorder and update duration of playlist content"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        content_items: List[Dict[str, Any]],
        organization_id: int,
    ) -> int:
        """
        Bulk reorder content items

        content_items: [{"id": 1, "order_index": 0, "duration": 30}, ...]

        Returns:
            Number of updated items
        """
        if not content_items:
            raise ValueError("content_items cannot be empty")

        return self.playlist_repo.reorder_playlist_contents(
            playlist_id=playlist_id,
            content_items=content_items,
            organization_id=organization_id,
        )
