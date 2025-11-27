"""
Get Active Playlists Use Case

Business logic for retrieving active playlist assignments.
"""

from typing import List

from ..domain.dashboard_stats import ActivePlaylistAssignment
from ..repositories.dashboard_repo import DashboardRepository


class GetActivePlaylistsUseCase:
    """Use case for getting active playlist assignments"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> List[ActivePlaylistAssignment]:
        """
        Get active playlist assignments for an organization

        Args:
            organization_id: Organization ID to get playlists for

        Returns:
            List of ActivePlaylistAssignment entities
        """
        return self.dashboard_repo.get_active_playlists(organization_id)
