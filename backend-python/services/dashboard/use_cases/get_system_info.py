"""
Get System Info Use Case

Business logic for retrieving system information.
"""

import os
import time

from ..domain.dashboard_stats import SystemInfo
from ..repositories.dashboard_repo import DashboardRepository


# Server start time for uptime calculation
SERVER_START_TIME = time.time()


class GetSystemInfoUseCase:
    """Use case for getting system information"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> SystemInfo:
        """
        Get system information for an organization

        Args:
            organization_id: Organization ID to get system info for

        Returns:
            SystemInfo entity with system details
        """
        # Get storage path from environment
        storage_path = os.environ.get('CONTENT_STORAGE_PATH', '/data/signage/content')

        # Get system info from repository
        system_info = self.dashboard_repo.get_system_info(organization_id, storage_path)

        # Calculate uptime
        uptime_seconds = int(time.time() - SERVER_START_TIME)
        system_info.uptime_seconds = uptime_seconds

        return system_info
