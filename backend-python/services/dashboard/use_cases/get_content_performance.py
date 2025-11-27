"""
Get Content Performance Use Case

Business logic for retrieving content performance metrics.
"""

from typing import List

from ..domain.dashboard_stats import ContentPerformance
from ..repositories.dashboard_repo import DashboardRepository


class GetContentPerformanceUseCase:
    """Use case for getting content performance metrics"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int, limit: int = 10) -> List[ContentPerformance]:
        """
        Get content performance metrics for an organization

        Args:
            organization_id: Organization ID to get metrics for
            limit: Maximum number of content items to return

        Returns:
            List of ContentPerformance entities
        """
        return self.dashboard_repo.get_content_performance(organization_id, limit)
