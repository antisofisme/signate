"""
Analytics Repository
Handles data access for analytics and playback logs
Phase 2 Day 2 - Analytics Service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
from .models import ContentPlaybackLog


class AnalyticsRepository:
    """Repository for analytics data access"""

    def __init__(self, db: Session):
        self.db = db

    def get_content_performance(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get content performance analytics using the content_performance view

        Args:
            organization_id: Organization ID to filter
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of results

        Returns:
            List of content performance dictionaries
        """
        query = text("""
            SELECT
                cp.content_id,
                cp.title,
                cp.content_type,
                cp.total_plays,
                cp.completed_plays,
                cp.avg_duration_seconds,
                cp.last_played_at,
                cp.unique_devices,
                ROUND((cp.completed_plays::numeric / NULLIF(cp.total_plays, 0) * 100), 2) as completion_rate
            FROM content_performance cp
            WHERE cp.organization_id = :org_id
            ORDER BY cp.total_plays DESC
            LIMIT :limit
        """)

        result = self.db.execute(
            query,
            {"org_id": organization_id, "limit": limit}
        )

        return [dict(row._mapping) for row in result]

    def get_device_engagement(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get device engagement analytics using the device_engagement view

        Args:
            organization_id: Organization ID to filter
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of results

        Returns:
            List of device engagement dictionaries
        """
        query = text("""
            SELECT
                de.device_id,
                de.device_name,
                de.total_plays,
                de.unique_content,
                de.last_playback_at,
                de.total_watch_time_seconds,
                ROUND((de.total_watch_time_seconds / 3600.0)::numeric, 2) as total_watch_time_hours
            FROM device_engagement de
            WHERE de.organization_id = :org_id
            ORDER BY de.total_plays DESC
            LIMIT :limit
        """)

        result = self.db.execute(
            query,
            {"org_id": organization_id, "limit": limit}
        )

        return [dict(row._mapping) for row in result]

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
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Total plays query
        total_plays = self.db.query(func.count(ContentPlaybackLog.id)).filter(
            ContentPlaybackLog.organization_id == organization_id,
            ContentPlaybackLog.started_at >= start_date,
            ContentPlaybackLog.started_at <= end_date
        ).scalar()

        # Completed plays
        completed_plays = self.db.query(func.count(ContentPlaybackLog.id)).filter(
            ContentPlaybackLog.organization_id == organization_id,
            ContentPlaybackLog.completed == True,
            ContentPlaybackLog.started_at >= start_date,
            ContentPlaybackLog.started_at <= end_date
        ).scalar()

        # Unique content count
        unique_content = self.db.query(func.count(func.distinct(ContentPlaybackLog.content_id))).filter(
            ContentPlaybackLog.organization_id == organization_id,
            ContentPlaybackLog.started_at >= start_date,
            ContentPlaybackLog.started_at <= end_date
        ).scalar()

        # Unique devices count
        unique_devices = self.db.query(func.count(func.distinct(ContentPlaybackLog.device_id))).filter(
            ContentPlaybackLog.organization_id == organization_id,
            ContentPlaybackLog.started_at >= start_date,
            ContentPlaybackLog.started_at <= end_date
        ).scalar()

        # Total watch time in seconds
        total_watch_time = self.db.query(func.sum(ContentPlaybackLog.duration_seconds)).filter(
            ContentPlaybackLog.organization_id == organization_id,
            ContentPlaybackLog.started_at >= start_date,
            ContentPlaybackLog.started_at <= end_date
        ).scalar() or 0

        # Average completion rate
        completion_rate = (completed_plays / total_plays * 100) if total_plays > 0 else 0

        return {
            "total_plays": total_plays or 0,
            "completed_plays": completed_plays or 0,
            "unique_content": unique_content or 0,
            "unique_devices": unique_devices or 0,
            "total_watch_time_seconds": total_watch_time,
            "total_watch_time_hours": round(total_watch_time / 3600, 2) if total_watch_time else 0,
            "completion_rate": round(completion_rate, 2),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

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
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Determine date_trunc format based on interval
        trunc_format = {
            "day": "day",
            "week": "week",
            "month": "month"
        }.get(interval, "day")

        query = text(f"""
            SELECT
                DATE_TRUNC('{trunc_format}', started_at) as period,
                COUNT(*) as total_plays,
                COUNT(*) FILTER (WHERE completed = true) as completed_plays,
                COUNT(DISTINCT content_id) as unique_content,
                COUNT(DISTINCT device_id) as unique_devices,
                COALESCE(SUM(duration_seconds), 0) as total_watch_time_seconds
            FROM content_playback_logs
            WHERE organization_id = :org_id
                AND started_at >= :start_date
                AND started_at <= :end_date
            GROUP BY period
            ORDER BY period ASC
        """)

        result = self.db.execute(
            query,
            {
                "org_id": organization_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        return [dict(row._mapping) for row in result]

    def log_playback(self, playback_data: Dict[str, Any]) -> ContentPlaybackLog:
        """
        Create a new playback log entry

        Args:
            playback_data: Dictionary with playback information

        Returns:
            Created ContentPlaybackLog instance
        """
        log = ContentPlaybackLog(**playback_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def update_playback_end(
        self,
        log_id: int,
        ended_at: datetime,
        duration_seconds: int,
        completed: bool = False
    ) -> Optional[ContentPlaybackLog]:
        """
        Update playback log with end time and completion status

        Args:
            log_id: Playback log ID
            ended_at: End timestamp
            duration_seconds: Actual playback duration
            completed: Whether playback completed

        Returns:
            Updated ContentPlaybackLog instance or None
        """
        log = self.db.query(ContentPlaybackLog).filter(
            ContentPlaybackLog.id == log_id
        ).first()

        if log:
            log.ended_at = ended_at
            log.duration_seconds = duration_seconds
            log.completed = completed
            self.db.commit()
            self.db.refresh(log)

        return log
