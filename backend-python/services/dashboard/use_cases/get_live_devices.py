"""
Get Live Devices Use Case

Business logic for retrieving live device status list.
"""

from typing import List

from ..domain.dashboard_stats import LiveDevice
from ..repositories.dashboard_repo import DashboardRepository


class GetLiveDevicesUseCase:
    """Use case for getting live device status"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> List[LiveDevice]:
        """
        Get live device status list for an organization

        Args:
            organization_id: Organization ID to get devices for

        Returns:
            List of LiveDevice entities
        """
        return self.dashboard_repo.get_live_devices(organization_id)
