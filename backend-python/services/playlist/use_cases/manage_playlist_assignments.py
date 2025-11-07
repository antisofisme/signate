"""
Playlist Assignment Use Cases
Bundled: assign/unassign devices and tags
"""

from typing import List, Dict, Any
from ..domain.interfaces import IPlaylistRepository


class GetPlaylistAssignmentsUseCase:
    """Get all device and tag assignments"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        organization_id: int,
    ) -> Dict[str, Any]:
        """
        Get playlist assignments

        Returns:
            {"devices": [...], "tags": [...]}
        """
        return self.playlist_repo.get_playlist_assignments(
            playlist_id=playlist_id,
            organization_id=organization_id,
        )


class AssignPlaylistToDevicesUseCase:
    """Assign playlist to devices (bulk)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int,
    ) -> Dict[str, Any]:
        """
        Bulk assign to devices

        Returns:
            {"assigned": int, "skipped_missing": [], "skipped_duplicate": []}
        """
        if not device_ids:
            raise ValueError("device_ids cannot be empty")

        return self.playlist_repo.assign_to_devices(
            playlist_id=playlist_id,
            device_ids=device_ids,
            organization_id=organization_id,
        )


class AssignPlaylistToTagsUseCase:
    """Assign playlist to tags (bulk)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int,
    ) -> Dict[str, Any]:
        """
        Bulk assign to tags

        Returns:
            {"assigned": int, "skipped_missing": [], "skipped_duplicate": []}
        """
        if not tag_ids:
            raise ValueError("tag_ids cannot be empty")

        return self.playlist_repo.assign_to_tags(
            playlist_id=playlist_id,
            tag_ids=tag_ids,
            organization_id=organization_id,
        )


class UnassignPlaylistFromDevicesUseCase:
    """Unassign playlist from devices (bulk)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int,
    ) -> int:
        """
        Bulk unassign from devices

        Returns:
            Number of removed assignments
        """
        if not device_ids:
            raise ValueError("device_ids cannot be empty")

        return self.playlist_repo.unassign_from_devices(
            playlist_id=playlist_id,
            device_ids=device_ids,
            organization_id=organization_id,
        )


class UnassignPlaylistFromTagsUseCase:
    """Unassign playlist from tags (bulk)"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int,
    ) -> int:
        """
        Bulk unassign from tags

        Returns:
            Number of removed assignments
        """
        if not tag_ids:
            raise ValueError("tag_ids cannot be empty")

        return self.playlist_repo.unassign_from_tags(
            playlist_id=playlist_id,
            tag_ids=tag_ids,
            organization_id=organization_id,
        )
