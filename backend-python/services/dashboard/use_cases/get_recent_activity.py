"""
Get Recent Activity Use Case

Business logic for retrieving recent activity feed.
"""

from typing import List

from ..domain.dashboard_stats import RecentActivity
from ..repositories.dashboard_repo import DashboardRepository


class GetRecentActivityUseCase:
    """Use case for getting recent activity"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int, limit: int = 20) -> List[RecentActivity]:
        """
        Get recent activity from audit logs

        Args:
            organization_id: Organization ID to get activity for
            limit: Maximum number of activity items to return

        Returns:
            List of RecentActivity entities
        """
        # Validate limit range
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        return self.dashboard_repo.get_recent_activity(organization_id, limit)
