"""
Create Playlist Use Case
"""

from ..domain.playlist import Playlist
from ..domain.interfaces import IPlaylistRepository
from services.organization.domain.quota_service import OrganizationQuotaService


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
            ValueError: If validation fails (duplicate name, quota exceeded)
        """
        # Check for duplicate name in organization
        existing = self.playlist_repo.find_by_name(name, organization_id)
        if existing:
            raise ValueError(f"Playlist dengan nama '{name}' sudah ada")

        # Check organization playlist quota
        db_session = self.playlist_repo.db
        quota_service = OrganizationQuotaService(db_session)

        # Enforce playlist quota atomically (CRITICAL FIX P0-9)
        try:
            quota_service.enforce_playlist_quota_atomic(organization_id)
        except ValueError as e:
            raise ValueError(f"Quota exceeded: {str(e)}")

        # Create domain entity (with validation)
        playlist = Playlist(
            name=name,
            description=description,
            is_active=is_active,
            priority=priority,
            schedule=schedule,
            organization_id=organization_id,
            created_by_id=created_by,
        )

        # Persist to database
        return self.playlist_repo.create(playlist)
