"""
Get System Alerts Use Case

Business logic for retrieving system alerts.
"""

from typing import List

from ..domain.dashboard_stats import SystemAlert
from ..repositories.dashboard_repo import DashboardRepository


class GetSystemAlertsUseCase:
    """Use case for getting system alerts"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> List[SystemAlert]:
        """
        Get system alerts for an organization

        Args:
            organization_id: Organization ID to get alerts for

        Returns:
            List of SystemAlert entities (max 50)
        """
        return self.dashboard_repo.get_system_alerts(organization_id, max_alerts=50)
