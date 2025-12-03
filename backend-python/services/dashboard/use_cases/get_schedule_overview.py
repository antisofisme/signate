"""
Get Schedule Overview Use Case

Business logic for retrieving schedule overview for dashboard.
"""

from ..domain.dashboard_stats import ScheduleOverview
from ..repositories.dashboard_repo import DashboardRepository


class GetScheduleOverviewUseCase:
    """Use case for getting schedule overview"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> ScheduleOverview:
        """
        Get schedule overview for an organization

        Args:
            organization_id: Organization ID to get overview for

        Returns:
            ScheduleOverview entity with schedule statistics
        """
        return self.dashboard_repo.get_schedule_overview(organization_id)
