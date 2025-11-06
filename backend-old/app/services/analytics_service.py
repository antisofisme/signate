"""
Analytics Service - Scalable Event Collection and Aggregation

Handles high-volume event ingestion (60,000+ events/hour) with:
- Event buffering and batch processing
- Real-time metrics in Redis
- Pre-aggregated data in PostgreSQL
- Time-series analysis and trend detection

Performance Targets:
- Dashboard load: < 500ms
- Real-time metrics: < 100ms
- Event ingestion: 1000 events/batch
- Data freshness: < 1 minute
"""

import asyncio
import logging
from app.core.logging import StructuredLogger
from datetime import datetime, date, time, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import json

from sqlalchemy import (
    select, insert, update, delete, func, and_, or_, desc,
    cast, Integer, Float, extract, distinct
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from redis.asyncio import Redis

from app.models.device import Device
from app.models.content import Content


logger = StructuredLogger(__name__)


class AnalyticsService:
    """
    Scalable analytics service with event buffering and real-time aggregation.

    Architecture:
    - Event Buffer: In-memory queue (1000 events)
    - Flush Strategy: Every 30s OR when buffer full
    - Real-time: Redis counters and sorted sets
    - Batch: PostgreSQL partitioned tables
    - Aggregation: Materialized views (refreshed every 5 min)
    """

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 1000
        self.last_flush = datetime.now(timezone.utc)
        self.flush_lock = asyncio.Lock()

        # Event types for tracking
        self.EVENT_TYPES = {
            'content_play', 'content_pause', 'content_complete', 'content_error',
            'heartbeat', 'device_boot', 'device_shutdown', 'device_error',
            'playlist_start', 'playlist_complete', 'playlist_skip',
            'api_call', 'system_error'
        }

    async def track_event(
        self,
        event_type: str,
        device_id: Optional[int] = None,
        content_id: Optional[int] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track analytics event with buffering.

        Events are buffered in memory and flushed when:
        - Buffer reaches 1000 events
        - 30 seconds elapsed since last flush

        Real-time metrics are updated immediately in Redis.

        Args:
            event_type: Type of event (content_play, heartbeat, etc.)
            device_id: Device ID (optional)
            content_id: Content ID (optional)
            user_id: User ID (optional)
            session_id: Session ID for tracking user sessions
            metrics: Numeric metrics (duration, cpu, memory, etc.)
            metadata: Additional context data

        Returns:
            True if event accepted, False otherwise
        """
        if event_type not in self.EVENT_TYPES:
            logger.warning(f"[Analytics] Unknown event type: {event_type}")
            return False

        now = datetime.now(timezone.utc)

        event = {
            'event_time': now,
            'event_type': event_type,
            'device_id': device_id,
            'content_id': content_id,
            'user_id': user_id,
            'session_id': session_id,
            'metrics': metrics or {},
            'metadata': metadata or {}
        }

        # Add to buffer
        self.event_buffer.append(event)

        # Update real-time counters (non-blocking)
        asyncio.create_task(self._update_realtime(event))

        # Check if flush needed
        should_flush = (
            len(self.event_buffer) >= self.buffer_size or
            (now - self.last_flush).total_seconds() >= 30
        )

        if should_flush:
            asyncio.create_task(self.flush_buffer())

        return True

    async def flush_buffer(self) -> int:
        """
        Flush event buffer to database.

        Uses batch insert for optimal performance.
        Returns number of events flushed.
        """
        async with self.flush_lock:
            if not self.event_buffer:
                return 0

            # Copy and clear buffer
            events_to_flush = self.event_buffer.copy()
            self.event_buffer.clear()
            self.last_flush = datetime.now(timezone.utc)

            try:
                # Prepare bulk insert
                from sqlalchemy import text

                values = []
                for event in events_to_flush:
                    values.append({
                        'event_time': event['event_time'],
                        'event_type': event['event_type'],
                        'device_id': event['device_id'],
                        'content_id': event['content_id'],
                        'user_id': event['user_id'],
                        'session_id': event['session_id'],
                        'metrics': json.dumps(event['metrics']),
                        'metadata': json.dumps(event['metadata'])
                    })

                # Bulk insert (optimized)
                query = text("""
                    INSERT INTO analytics_events
                    (event_time, event_type, device_id, content_id, user_id,
                     session_id, metrics, metadata)
                    VALUES
                    (:event_time, :event_type, :device_id, :content_id, :user_id,
                     :session_id, :metrics::jsonb, :metadata::jsonb)
                """)

                await self.db.execute(query, values)
                await self.db.commit()

                count = len(events_to_flush)
                logger.info(f"[Analytics] Flushed {count} events to database")

                return count

            except Exception as e:
                logger.error(f"[Analytics] Flush failed: {e}")
                # Re-add events to buffer
                self.event_buffer.extend(events_to_flush)
                return 0

    async def _update_realtime(self, event: Dict[str, Any]) -> None:
        """
        Update real-time metrics in Redis.

        Maintains fast-access counters for dashboard:
        - Active devices (5 min TTL)
        - Hourly/daily counters
        - Trending content (sorted set)
        """
        try:
            event_type = event['event_type']
            now = datetime.now(timezone.utc)
            today = now.strftime('%Y-%m-%d')
            hour = now.strftime('%Y-%m-%d-%H')

            # Increment counters
            await self.redis.incr(f"analytics:today:{event_type}")
            await self.redis.incr(f"analytics:hour:{hour}:{event_type}")

            # Set expiry for hourly counters (25 hours)
            await self.redis.expire(f"analytics:hour:{hour}:{event_type}", 90000)

            # Track active devices (5 min TTL)
            if event['device_id']:
                await self.redis.setex(
                    f"analytics:device_active:{event['device_id']}",
                    300,  # 5 minutes
                    '1'
                )

            # Track content views and trends
            if event['content_id'] and event_type == 'content_play':
                # Increment today's view count
                await self.redis.zincrby(
                    f"analytics:trending_content:{today}",
                    1,
                    str(event['content_id'])
                )

                # Global trending (24 hour window)
                await self.redis.zincrby(
                    'analytics:trending_content',
                    1,
                    str(event['content_id'])
                )
                await self.redis.expire('analytics:trending_content', 86400)

            # Track session metrics
            if event['session_id']:
                await self.redis.sadd(
                    f"analytics:sessions:{today}",
                    event['session_id']
                )
                await self.redis.expire(f"analytics:sessions:{today}", 172800)  # 2 days

            # Track system metrics (CPU, Memory)
            if event_type == 'heartbeat' and event.get('metrics'):
                metrics = event['metrics']
                if 'cpu' in metrics:
                    await self.redis.lpush(
                        f"analytics:cpu:{hour}",
                        str(metrics['cpu'])
                    )
                    await self.redis.ltrim(f"analytics:cpu:{hour}", 0, 999)
                    await self.redis.expire(f"analytics:cpu:{hour}", 7200)

                if 'memory' in metrics:
                    await self.redis.lpush(
                        f"analytics:memory:{hour}",
                        str(metrics['memory'])
                    )
                    await self.redis.ltrim(f"analytics:memory:{hour}", 0, 999)
                    await self.redis.expire(f"analytics:memory:{hour}", 7200)

        except Exception as e:
            logger.error(f"[Analytics] Real-time update failed: {e}")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get real-time dashboard metrics.

        Combines:
        - Materialized view (refreshed every 5 min)
        - Redis real-time counters
        - Device status from database

        Target: < 500ms response time
        """
        try:
            from sqlalchemy import text

            # Get materialized view data (cached in DB)
            mv_query = text("SELECT * FROM dashboard_stats LIMIT 1")
            mv_result = await self.db.execute(mv_query)
            mv_data = mv_result.mappings().first()

            # Get real-time data from Redis
            trending = await self.redis.zrevrange(
                'analytics:trending_content',
                0, 9,  # Top 10
                withscores=True
            )

            # Get active device count from Redis
            active_device_keys = await self.redis.keys('analytics:device_active:*')
            online_devices = len(active_device_keys)

            # Get today's event counts
            today_plays = await self.redis.get('analytics:today:content_play') or 0
            today_errors = await self.redis.get('analytics:today:device_error') or 0

            # Get unique sessions today
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            unique_sessions = await self.redis.scard(f'analytics:sessions:{today}')

            # Format response
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'devices': {
                    'total': mv_data['active_devices'] if mv_data else 0,
                    'online': online_devices,
                    'offline': (mv_data['active_devices'] if mv_data else 0) - online_devices
                },
                'content': {
                    'total_plays_today': int(today_plays),
                    'total_watch_time_seconds': mv_data['total_watch_time_today'] if mv_data else 0,
                    'trending': [
                        {
                            'content_id': int(content_id),
                            'views': int(score)
                        }
                        for content_id, score in trending
                    ]
                },
                'system': {
                    'avg_cpu_percent': float(mv_data['avg_cpu']) if mv_data and mv_data['avg_cpu'] else 0,
                    'avg_memory_percent': float(mv_data['avg_memory']) if mv_data and mv_data['avg_memory'] else 0,
                    'unique_sessions': unique_sessions,
                    'error_count': int(today_errors)
                }
            }

        except Exception as e:
            logger.error(f"[Analytics] Dashboard data retrieval failed: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'devices': {'total': 0, 'online': 0, 'offline': 0},
                'content': {'total_plays_today': 0, 'total_watch_time_seconds': 0, 'trending': []},
                'system': {'avg_cpu_percent': 0, 'avg_memory_percent': 0, 'unique_sessions': 0, 'error_count': 0}
            }

    async def get_content_stats(
        self,
        content_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get content performance statistics.

        Queries pre-aggregated daily data for fast results.

        Args:
            content_id: Content ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            Content statistics with time-series data
        """
        start = start_date or (date.today() - timedelta(days=30))
        end = end_date or date.today()

        try:
            from sqlalchemy import text

            # Query daily aggregations
            query = text("""
                SELECT
                    SUM(views) as total_views,
                    SUM(unique_viewers) as unique_viewers,
                    SUM(total_watch_time) as total_watch_time,
                    AVG(avg_watch_time) as avg_watch_time,
                    AVG(completion_rate) as completion_rate,
                    SUM(error_count) as error_count,
                    json_agg(
                        json_build_object(
                            'date', date,
                            'views', views,
                            'unique_viewers', unique_viewers,
                            'watch_time', total_watch_time,
                            'completion_rate', completion_rate
                        ) ORDER BY date
                    ) as time_series
                FROM analytics_daily
                WHERE content_id = :content_id
                  AND date >= :start_date
                  AND date <= :end_date
            """)

            result = await self.db.execute(
                query,
                {
                    'content_id': content_id,
                    'start_date': start,
                    'end_date': end
                }
            )
            row = result.mappings().first()

            if not row or row['total_views'] is None:
                return {
                    'content_id': content_id,
                    'period': {'start': start.isoformat(), 'end': end.isoformat()},
                    'total_views': 0,
                    'unique_viewers': 0,
                    'total_watch_time_seconds': 0,
                    'avg_watch_time_seconds': 0,
                    'completion_rate': 0,
                    'error_count': 0,
                    'time_series': []
                }

            return {
                'content_id': content_id,
                'period': {'start': start.isoformat(), 'end': end.isoformat()},
                'total_views': int(row['total_views'] or 0),
                'unique_viewers': int(row['unique_viewers'] or 0),
                'total_watch_time_seconds': int(row['total_watch_time'] or 0),
                'avg_watch_time_seconds': float(row['avg_watch_time'] or 0),
                'completion_rate': float(row['completion_rate'] or 0),
                'error_count': int(row['error_count'] or 0),
                'time_series': row['time_series'] if row['time_series'] else []
            }

        except Exception as e:
            logger.error(f"[Analytics] Content stats retrieval failed: {e}")
            return {
                'content_id': content_id,
                'period': {'start': start.isoformat(), 'end': end.isoformat()},
                'total_views': 0,
                'unique_viewers': 0,
                'total_watch_time_seconds': 0,
                'avg_watch_time_seconds': 0,
                'completion_rate': 0,
                'error_count': 0,
                'time_series': []
            }

    async def get_device_stats(
        self,
        device_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get device performance statistics.

        Returns uptime, content played, errors, and performance metrics.

        Args:
            device_id: Device ID
            start_date: Start date (default: 7 days ago)
            end_date: End date (default: today)

        Returns:
            Device statistics with time-series data
        """
        start = start_date or (date.today() - timedelta(days=7))
        end = end_date or date.today()

        try:
            from sqlalchemy import text

            # Query device daily aggregations
            query = text("""
                SELECT
                    SUM(uptime_seconds) as total_uptime_seconds,
                    AVG(avg_cpu_usage) as avg_cpu,
                    AVG(avg_memory_usage) as avg_memory,
                    SUM(content_played) as total_content_played,
                    SUM(error_count) as total_errors,
                    SUM(total_bandwidth_mb) as total_bandwidth_mb,
                    json_agg(
                        json_build_object(
                            'date', date,
                            'uptime_seconds', uptime_seconds,
                            'cpu_usage', avg_cpu_usage,
                            'memory_usage', avg_memory_usage,
                            'content_played', content_played,
                            'errors', error_count
                        ) ORDER BY date
                    ) as time_series
                FROM analytics_daily_devices
                WHERE device_id = :device_id
                  AND date >= :start_date
                  AND date <= :end_date
            """)

            result = await self.db.execute(
                query,
                {
                    'device_id': device_id,
                    'start_date': start,
                    'end_date': end
                }
            )
            row = result.mappings().first()

            # Calculate uptime percentage
            total_seconds_in_period = (end - start).days * 86400
            uptime_pct = 0
            if row and row['total_uptime_seconds']:
                uptime_pct = (row['total_uptime_seconds'] / total_seconds_in_period) * 100
                uptime_pct = min(100.0, uptime_pct)  # Cap at 100%

            return {
                'device_id': device_id,
                'period': {'start': start.isoformat(), 'end': end.isoformat()},
                'uptime_percentage': round(uptime_pct, 2),
                'total_content_played': int(row['total_content_played'] or 0) if row else 0,
                'avg_cpu_usage': float(row['avg_cpu'] or 0) if row else 0,
                'avg_memory_usage': float(row['avg_memory'] or 0) if row else 0,
                'total_errors': int(row['total_errors'] or 0) if row else 0,
                'total_bandwidth_mb': float(row['total_bandwidth_mb'] or 0) if row else 0,
                'time_series': row['time_series'] if row and row['time_series'] else []
            }

        except Exception as e:
            logger.error(f"[Analytics] Device stats retrieval failed: {e}")
            return {
                'device_id': device_id,
                'period': {'start': start.isoformat(), 'end': end.isoformat()},
                'uptime_percentage': 0,
                'total_content_played': 0,
                'avg_cpu_usage': 0,
                'avg_memory_usage': 0,
                'total_errors': 0,
                'total_bandwidth_mb': 0,
                'time_series': []
            }

    async def get_trending_content(self, limit: int = 10, period: str = '24h') -> List[Dict[str, Any]]:
        """
        Get trending content based on recent views.

        Args:
            limit: Number of results (default: 10)
            period: Time period ('24h', '7d', '30d')

        Returns:
            List of trending content with view counts
        """
        try:
            # Get from Redis sorted set
            trending = await self.redis.zrevrange(
                'analytics:trending_content',
                0, limit - 1,
                withscores=True
            )

            if not trending:
                return []

            # Get content details
            content_ids = [int(cid) for cid, _ in trending]

            query = select(Content).where(Content.id.in_(content_ids))
            result = await self.db.execute(query)
            contents = {c.id: c for c in result.scalars().all()}

            # Combine data
            results = []
            for content_id, views in trending:
                content_id = int(content_id)
                if content_id in contents:
                    content = contents[content_id]
                    results.append({
                        'content_id': content_id,
                        'name': content.name,
                        'content_type': content.content_type,
                        'views': int(views),
                        'thumbnail_url': content.thumbnail_url
                    })

            return results

        except Exception as e:
            logger.error(f"[Analytics] Trending content retrieval failed: {e}")
            return []

    async def aggregate_hourly_data(self, hour: datetime) -> bool:
        """
        Aggregate hourly data from events table.

        Called by scheduled task every hour.

        Args:
            hour: Hour to aggregate (truncated to hour)

        Returns:
            True if successful
        """
        try:
            from sqlalchemy import text

            query = text("""
                INSERT INTO analytics_hourly (
                    hour_time, device_id, content_id, event_type,
                    event_count, avg_duration, sum_duration, unique_sessions
                )
                SELECT
                    DATE_TRUNC('hour', event_time) as hour_time,
                    device_id,
                    content_id,
                    event_type,
                    COUNT(*) as event_count,
                    AVG(CAST(metrics->>'duration' AS NUMERIC)) as avg_duration,
                    SUM(CAST(metrics->>'duration' AS BIGINT)) as sum_duration,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM analytics_events
                WHERE DATE_TRUNC('hour', event_time) = :hour
                  AND event_type IN ('content_play', 'content_complete')
                GROUP BY hour_time, device_id, content_id, event_type
                ON CONFLICT (hour_time, device_id, content_id, event_type)
                DO UPDATE SET
                    event_count = EXCLUDED.event_count,
                    avg_duration = EXCLUDED.avg_duration,
                    sum_duration = EXCLUDED.sum_duration,
                    unique_sessions = EXCLUDED.unique_sessions
            """)

            await self.db.execute(query, {'hour': hour})
            await self.db.commit()

            logger.info(f"[Analytics] Aggregated hourly data for {hour}")
            return True

        except Exception as e:
            logger.error(f"[Analytics] Hourly aggregation failed: {e}")
            await self.db.rollback()
            return False

    async def aggregate_daily_data(self, target_date: date) -> bool:
        """
        Aggregate daily data from hourly aggregations.

        Called by scheduled task at end of day.

        Args:
            target_date: Date to aggregate

        Returns:
            True if successful
        """
        try:
            from sqlalchemy import text

            # Aggregate content stats
            content_query = text("""
                INSERT INTO analytics_daily (
                    date, device_id, content_id, views, unique_viewers,
                    total_watch_time, avg_watch_time, completion_rate, error_count
                )
                SELECT
                    DATE(:target_date) as date,
                    device_id,
                    content_id,
                    SUM(event_count) FILTER (WHERE event_type = 'content_play') as views,
                    COUNT(DISTINCT device_id) as unique_viewers,
                    SUM(sum_duration) as total_watch_time,
                    AVG(avg_duration) as avg_watch_time,
                    AVG(CASE
                        WHEN event_type = 'content_complete'
                        THEN 1.0
                        ELSE 0.0
                    END) as completion_rate,
                    SUM(event_count) FILTER (WHERE event_type = 'content_error') as error_count
                FROM analytics_hourly
                WHERE DATE(hour_time) = :target_date
                GROUP BY device_id, content_id
                ON CONFLICT (date, device_id, content_id)
                DO UPDATE SET
                    views = EXCLUDED.views,
                    unique_viewers = EXCLUDED.unique_viewers,
                    total_watch_time = EXCLUDED.total_watch_time,
                    avg_watch_time = EXCLUDED.avg_watch_time,
                    completion_rate = EXCLUDED.completion_rate,
                    error_count = EXCLUDED.error_count
            """)

            await self.db.execute(content_query, {'target_date': target_date})

            # Aggregate device stats
            device_query = text("""
                INSERT INTO analytics_daily_devices (
                    date, device_id, uptime_seconds, online_count, offline_count,
                    error_count, avg_cpu_usage, avg_memory_usage, total_bandwidth_mb, content_played
                )
                SELECT
                    DATE(:target_date) as date,
                    device_id,
                    COUNT(*) * 30 as uptime_seconds,
                    COUNT(*) FILTER (WHERE event_type = 'heartbeat') as online_count,
                    COUNT(*) FILTER (WHERE event_type = 'device_shutdown') as offline_count,
                    COUNT(*) FILTER (WHERE event_type = 'device_error') as error_count,
                    AVG(CAST(metrics->>'cpu' AS NUMERIC)) as avg_cpu_usage,
                    AVG(CAST(metrics->>'memory' AS NUMERIC)) as avg_memory_usage,
                    SUM(CAST(metrics->>'bandwidth_kb' AS INTEGER)) / 1024 as total_bandwidth_mb,
                    COUNT(DISTINCT content_id) as content_played
                FROM analytics_events
                WHERE DATE(event_time) = :target_date
                  AND device_id IS NOT NULL
                GROUP BY device_id
                ON CONFLICT (date, device_id)
                DO UPDATE SET
                    uptime_seconds = EXCLUDED.uptime_seconds,
                    online_count = EXCLUDED.online_count,
                    offline_count = EXCLUDED.offline_count,
                    error_count = EXCLUDED.error_count,
                    avg_cpu_usage = EXCLUDED.avg_cpu_usage,
                    avg_memory_usage = EXCLUDED.avg_memory_usage,
                    total_bandwidth_mb = EXCLUDED.total_bandwidth_mb,
                    content_played = EXCLUDED.content_played
            """)

            await self.db.execute(device_query, {'target_date': target_date})
            await self.db.commit()

            logger.info(f"[Analytics] Aggregated daily data for {target_date}")
            return True

        except Exception as e:
            logger.error(f"[Analytics] Daily aggregation failed: {e}")
            await self.db.rollback()
            return False

    async def refresh_materialized_views(self) -> bool:
        """
        Refresh materialized views for dashboard.

        Should be called every 5 minutes via scheduled task.

        Returns:
            True if successful
        """
        try:
            from sqlalchemy import text

            query = text("REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_stats")
            await self.db.execute(query)
            await self.db.commit()

            logger.info("[Analytics] Refreshed materialized views")
            return True

        except Exception as e:
            logger.error(f"[Analytics] Materialized view refresh failed: {e}")
            await self.db.rollback()
            return False
