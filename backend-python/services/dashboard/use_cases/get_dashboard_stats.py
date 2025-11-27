"""
Get Dashboard Stats Use Case

Business logic for retrieving overall dashboard statistics.
"""

from ..domain.dashboard_stats import DashboardStats
from ..repositories.dashboard_repo import DashboardRepository


class GetDashboardStatsUseCase:
    """Use case for getting overall dashboard statistics"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> DashboardStats:
        """
        Get overall dashboard statistics for an organization

        Args:
            organization_id: Organization ID to get stats for

        Returns:
            DashboardStats entity with all statistics
        """
        return self.dashboard_repo.get_dashboard_stats(organization_id)
