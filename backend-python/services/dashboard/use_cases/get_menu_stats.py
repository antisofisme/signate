"""
Get Menu Stats Use Case

Business logic for retrieving menu statistics for dashboard.
"""

from ..domain.dashboard_stats import MenuStats
from ..repositories.dashboard_repo import DashboardRepository


class GetMenuStatsUseCase:
    """Use case for getting menu statistics"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> MenuStats:
        """
        Get menu statistics for an organization

        Args:
            organization_id: Organization ID to get stats for

        Returns:
            MenuStats entity with menu statistics
        """
        return self.dashboard_repo.get_menu_stats(organization_id)
