"""
Duplicate Playlist Use Case
"""

from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository
from services.organization.domain.quota_service import OrganizationQuotaService


class DuplicatePlaylistUseCase:
    """Duplicate an existing playlist with all its contents"""

    def __init__(self, playlist_repo: IPlaylistRepository):
        self.playlist_repo = playlist_repo

    def execute(
        self,
        playlist_id: int,
        organization_id: int,
        new_name: str | None = None,
        created_by: int | None = None,
    ) -> Playlist:
        """
        Duplicate playlist with all contents

        Args:
            playlist_id: ID of playlist to duplicate
            organization_id: Organization ID (for access check)
            new_name: Optional custom name for new playlist (defaults to "Copy of <original>")
            created_by: User ID creating the duplicate

        Returns:
            The newly created duplicate playlist

        Raises:
            ValueError: If source playlist not found, duplicate name exists, or quota exceeded
        """
        # Get source playlist to validate and get name
        source = self.playlist_repo.find_by_id(playlist_id, organization_id)
        if not source:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Generate name if not provided
        if not new_name:
            new_name = f"Copy of {source.name}"

        # Check if name already exists
        existing = self.playlist_repo.find_by_name(new_name, organization_id)
        if existing:
            # Auto-generate unique name with suffix
            counter = 1
            base_name = new_name
            while existing:
                counter += 1
                new_name = f"{base_name} ({counter})"
                existing = self.playlist_repo.find_by_name(new_name, organization_id)

        # Check organization playlist quota
        db_session = self.playlist_repo.db
        quota_service = OrganizationQuotaService(db_session)

        try:
            quota_service.enforce_playlist_quota_atomic(organization_id)
        except ValueError as e:
            raise ValueError(f"Cannot duplicate: {str(e)}")

        # Perform duplication
        duplicated = self.playlist_repo.duplicate(
            playlist_id=playlist_id,
            organization_id=organization_id,
            new_name=new_name,
            created_by_id=created_by,
        )

        if not duplicated:
            raise ValueError(f"Failed to duplicate playlist {playlist_id}")

        return duplicated
