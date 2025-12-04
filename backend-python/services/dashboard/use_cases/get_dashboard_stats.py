"""
Get Dashboard Stats Use Case

Business logic for retrieving overall dashboard statistics.

PERFORMANCE: Added caching with 60-second TTL to reduce database load.
Dashboard stats don't need real-time accuracy.
"""

from ..domain.dashboard_stats import DashboardStats
from ..repositories.dashboard_repo import DashboardRepository
from shared.cache import cache
import logging

logger = logging.getLogger(__name__)


class GetDashboardStatsUseCase:
    """Use case for getting overall dashboard statistics"""

    # Cache TTL in seconds (1 minute - stats don't need real-time accuracy)
    CACHE_TTL = 60

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    def execute(self, organization_id: int) -> DashboardStats:
        """
        Get overall dashboard statistics for an organization.

        PERFORMANCE FIX: Uses 60-second cache to reduce DB queries.
        Dashboard stats are not critical for real-time accuracy.

        Args:
            organization_id: Organization ID to get stats for

        Returns:
            DashboardStats entity with all statistics
        """
        cache_key = f"dashboard_stats:{organization_id}"

        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Dashboard stats cache HIT for org {organization_id}")
            # Reconstruct DashboardStats from cached dict
            return DashboardStats(**cached_data)

        logger.debug(f"Dashboard stats cache MISS for org {organization_id}")

        # Get from database
        stats = self.dashboard_repo.get_dashboard_stats(organization_id)

        # Cache the result (convert to dict for serialization)
        cache.set(cache_key, stats.__dict__, ttl=self.CACHE_TTL)

        return stats

    def invalidate_cache(self, organization_id: int) -> None:
        """Invalidate dashboard stats cache for an organization"""
        cache_key = f"dashboard_stats:{organization_id}"
        cache.delete(cache_key)
        logger.debug(f"Dashboard stats cache invalidated for org {organization_id}")
