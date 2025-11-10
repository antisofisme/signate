"""
Analytics Repository Interfaces
Defines contracts for data access layer
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from .playback_log import PlaybackLog, ContentPerformance, DeviceEngagement


class IAnalyticsRepository(ABC):
    """Interface for analytics repository"""

    @abstractmethod
    def get_content_performance(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get content performance analytics

        Args:
            organization_id: Organization ID to filter
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of results

        Returns:
            List of content performance dictionaries
        """
        pass

    @abstractmethod
    def get_device_engagement(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get device engagement analytics

        Args:
            organization_id: Organization ID to filter
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of results

        Returns:
            List of device engagement dictionaries
        """
        pass

    @abstractmethod
    def get_playback_stats(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get overall playback statistics

        Args:
            organization_id: Organization ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)

        Returns:
            Dictionary with playback statistics
        """
        pass

    @abstractmethod
    def get_playback_timeline(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get playback timeline grouped by interval

        Args:
            organization_id: Organization ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
            interval: Grouping interval (day, week, month)

        Returns:
            List of timeline data points
        """
        pass

    @abstractmethod
    def log_playback(self, playback_data: Dict[str, Any]) -> PlaybackLog:
        """
        Create a new playback log entry

        Args:
            playback_data: Dictionary with playback information

        Returns:
            Created PlaybackLog domain entity
        """
        pass

    @abstractmethod
    def update_playback_end(
        self,
        log_id: int,
        ended_at: datetime,
        duration_seconds: int,
        completed: bool = False
    ) -> Optional[PlaybackLog]:
        """
        Update playback log with end time and completion status

        Args:
            log_id: Playback log ID
            ended_at: End timestamp
            duration_seconds: Actual playback duration
            completed: Whether playback completed

        Returns:
            Updated PlaybackLog domain entity or None
        """
        pass

    @abstractmethod
    def get_playback_by_id(self, log_id: int) -> Optional[PlaybackLog]:
        """
        Get playback log by ID

        Args:
            log_id: Playback log ID

        Returns:
            PlaybackLog domain entity or None
        """
        pass


class IAnalyticsAggregator(ABC):
    """Interface for analytics aggregation service"""

    @abstractmethod
    def aggregate_daily_stats(
        self,
        organization_id: int,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate daily statistics for an organization

        Args:
            organization_id: Organization ID
            date: Date to aggregate

        Returns:
            Dictionary with daily statistics
        """
        pass

    @abstractmethod
    def calculate_trends(
        self,
        organization_id: int,
        metric: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate trends for a specific metric

        Args:
            organization_id: Organization ID
            metric: Metric to analyze (plays, watch_time, etc.)
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        pass
