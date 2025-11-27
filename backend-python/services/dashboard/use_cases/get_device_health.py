"""
Get Device Health Use Case

Business logic for retrieving device health summary.
"""

from ..domain.dashboard_stats import DeviceHealthSummary
from ..repositories.dashboard_repo import DashboardRepository


class GetDeviceHealthUseCase:
    """Use case for getting device health summary"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> DeviceHealthSummary:
        """
        Get device health summary for an organization

        Args:
            organization_id: Organization ID to get health summary for

        Returns:
            DeviceHealthSummary entity with health statistics
        """
        return self.dashboard_repo.get_device_health_summary(organization_id)
