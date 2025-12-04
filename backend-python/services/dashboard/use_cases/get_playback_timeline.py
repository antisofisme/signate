"""
Get Playback Timeline Use Case

Business logic for retrieving playback timeline data.
"""

from typing import List

from ..domain.dashboard_stats import PlaybackTimeline
from ..repositories.dashboard_repo import DashboardRepository


class GetPlaybackTimelineUseCase:
    """Use case for getting playback timeline"""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int, days: int = 7) -> List[PlaybackTimeline]:
        """
        Get playback timeline for the last N days

        Args:
            organization_id: Organization ID to filter playback data
            days: Number of days to get timeline for (1-30)

        Returns:
            List of PlaybackTimeline entities
        """
        # Validate days range
        if days < 1:
            days = 1
        elif days > 30:
            days = 30

        return self.dashboard_repo.get_playback_timeline(organization_id, days)
