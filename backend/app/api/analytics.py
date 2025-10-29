"""
Analytics API Endpoints

Provides comprehensive analytics and metrics:
- Event ingestion (bulk)
- Content performance stats
- Device health metrics
- Dashboard data
- Trend analysis
- Real-time metrics via WebSocket

Performance:
- Bulk event ingestion: 1000 events/batch
- Dashboard data: < 500ms
- Content stats: < 200ms (cached)
- Device stats: < 300ms (cached)

Quick Wins Pattern Compliant:
- StructuredLogger with request_id tracking
- success_response wrapper for all responses
- Custom exceptions (no HTTPException)
- Standardized response schemas
- Comprehensive error handling
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, ValidationException
from app.core.deps import get_current_active_user, require_admin
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.schemas.analytics import (
    # Request models
    AnalyticsEvent,
    BulkEventsRequest,
    AggregationTargetRequest,
    DateRangeParams,
    # Response models
    ContentStatsResponse,
    ContentTrendingRank,
    TrendingContentItem,
    DeviceStatsResponse,
    DeviceRealtimeStatus,
    DashboardResponse,
    BufferFlushResult,
    ViewRefreshResult,
    AggregationResult,
    EventIngestionResult,
    DeviceCountStats,
    ContentMetrics,
    SystemHealthMetrics
)
from app.services.analytics_service import AnalyticsService
from app.models.user import User
from redis.asyncio import Redis


logger = StructuredLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ============================================================================
# EVENT INGESTION ENDPOINTS
# ============================================================================

@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    request: Request,
    event_data: BulkEventsRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ingest analytics events in bulk.

    Accepts up to 1000 events per request. Events are buffered and
    flushed to database in batches for optimal performance.

    **Performance:**
    - Accepts 1000 events/request
    - Non-blocking (returns 202 Accepted)
    - Events buffered for batch insert

    **Event Types:**
    - content_play, content_pause, content_complete, content_error
    - heartbeat, device_boot, device_shutdown, device_error
    - playlist_start, playlist_complete, playlist_skip
    - api_call, system_error

    **Example Request:**
    ```json
    {
        "events": [
            {
                "event_type": "content_play",
                "device_id": 123,
                "content_id": 456,
                "metrics": {
                    "duration": 120,
                    "completed": true
                }
            }
        ]
    }
    ```
    """
    request_id = get_request_id(request)

    logger.info(
        "Ingesting bulk events",
        request_id=request_id,
        event_count=len(event_data.events),
        user_id=current_user.id if current_user else None
    )

    try:
        analytics = AnalyticsService(db, redis)

        # Track all events
        for event in event_data.events:
            await analytics.track_event(
                event_type=event.event_type,
                device_id=event.device_id,
                content_id=event.content_id,
                user_id=event.user_id,
                session_id=event.session_id,
                metrics=event.metrics,
                metadata=event.metadata
            )

        logger.info(
            "Events ingested successfully",
            request_id=request_id,
            events_received=len(event_data.events)
        )

        return success_response(
            data={
                "status": "accepted",
                "events_received": len(event_data.events),
                "message": "Events queued for processing"
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Event ingestion failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to ingest events")


@router.post("/events/single", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_event(
    request: Request,
    event: AnalyticsEvent,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ingest a single analytics event.

    Convenience endpoint for single event submission.
    Use bulk endpoint for better performance with multiple events.
    """
    request_id = get_request_id(request)

    logger.info(
        "Ingesting single event",
        request_id=request_id,
        event_type=event.event_type,
        device_id=event.device_id,
        content_id=event.content_id
    )

    try:
        analytics = AnalyticsService(db, redis)

        await analytics.track_event(
            event_type=event.event_type,
            device_id=event.device_id,
            content_id=event.content_id,
            user_id=event.user_id,
            session_id=event.session_id,
            metrics=event.metrics,
            metadata=event.metadata
        )

        logger.info(
            "Single event ingested successfully",
            request_id=request_id,
            event_type=event.event_type
        )

        return success_response(
            data={
                "status": "accepted",
                "message": "Event queued for processing"
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Single event ingestion failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to ingest event")


# ============================================================================
# CONTENT ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/content/{content_id}")
async def get_content_analytics(
    request: Request,
    content_id: int,
    start_date: Optional[date] = Query(None, description="Start date (default: 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics for specific content.

    Returns comprehensive performance metrics:
    - Total views and unique viewers
    - Watch time (total and average)
    - Completion rate
    - Error count
    - Time-series data for charting

    **Performance:** < 200ms (cached)

    **Default Period:** Last 30 days
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting content analytics",
        request_id=request_id,
        content_id=content_id,
        start_date=str(start_date) if start_date else None,
        end_date=str(end_date) if end_date else None
    )

    try:
        analytics = AnalyticsService(db, redis)

        stats = await analytics.get_content_stats(
            content_id=content_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(
            "Content analytics retrieved successfully",
            request_id=request_id,
            content_id=content_id,
            total_views=stats.get('total_views', 0)
        )

        return success_response(
            data=stats,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Content analytics retrieval failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        raise NotFoundException(detail=f"Failed to retrieve analytics for content {content_id}")


@router.get("/content/{content_id}/trending")
async def get_content_trending_rank(
    request: Request,
    content_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trending rank for specific content.

    Returns:
    - Current rank in trending list (1-based)
    - Total views in last 24h
    - Rank change from previous period
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting content trending rank",
        request_id=request_id,
        content_id=content_id
    )

    try:
        # Get trending data from Redis
        trending = await redis.zrevrank('analytics:trending_content', str(content_id))
        views = await redis.zscore('analytics:trending_content', str(content_id))

        if trending is None:
            result = {
                "content_id": content_id,
                "rank": None,
                "views_24h": 0,
                "is_trending": False
            }
        else:
            result = {
                "content_id": content_id,
                "rank": trending + 1,  # Convert to 1-based
                "views_24h": int(views) if views else 0,
                "is_trending": True
            }

        logger.info(
            "Content trending rank retrieved",
            request_id=request_id,
            content_id=content_id,
            rank=result['rank']
        )

        return success_response(
            data=result,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Trending rank retrieval failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        raise NotFoundException(detail=f"Failed to retrieve trending rank for content {content_id}")


# ============================================================================
# DEVICE ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/devices/{device_id}")
async def get_device_analytics(
    request: Request,
    device_id: int,
    start_date: Optional[date] = Query(None, description="Start date (default: 7 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics for specific device.

    Returns health and performance metrics:
    - Uptime percentage
    - Content played (total and unique)
    - CPU and memory usage
    - Error count
    - Bandwidth consumption
    - Time-series data for charting

    **Performance:** < 300ms (cached)

    **Default Period:** Last 7 days
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting device analytics",
        request_id=request_id,
        device_id=device_id,
        start_date=str(start_date) if start_date else None,
        end_date=str(end_date) if end_date else None
    )

    try:
        analytics = AnalyticsService(db, redis)

        stats = await analytics.get_device_stats(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(
            "Device analytics retrieved successfully",
            request_id=request_id,
            device_id=device_id,
            uptime=stats.get('uptime_percentage', 0)
        )

        return success_response(
            data=stats,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Device analytics retrieval failed",
            request_id=request_id,
            device_id=device_id,
            error=str(e),
            exc_info=True
        )
        raise NotFoundException(detail=f"Failed to retrieve analytics for device {device_id}")


@router.get("/devices/{device_id}/realtime")
async def get_device_realtime(
    request: Request,
    device_id: int,
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get real-time device status.

    Returns immediate device state from Redis:
    - Online/offline status
    - Last heartbeat time
    - Current content playing

    **Performance:** < 50ms (Redis lookup)
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting device real-time status",
        request_id=request_id,
        device_id=device_id
    )

    try:
        # Check if device is active (5 min TTL)
        is_active = await redis.exists(f'analytics:device_active:{device_id}')

        # Get last heartbeat time from cache
        last_heartbeat = await redis.get(f'device:last_heartbeat:{device_id}')

        # Get current content from cache
        current_content = await redis.get(f'device:current_content:{device_id}')

        result = {
            "device_id": device_id,
            "is_online": bool(is_active),
            "last_heartbeat": last_heartbeat.decode() if last_heartbeat else None,
            "current_content_id": int(current_content) if current_content else None
        }

        logger.info(
            "Device real-time status retrieved",
            request_id=request_id,
            device_id=device_id,
            is_online=result['is_online']
        )

        return success_response(
            data=result,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Real-time status retrieval failed",
            request_id=request_id,
            device_id=device_id,
            error=str(e),
            exc_info=True
        )
        raise NotFoundException(detail=f"Failed to retrieve real-time status for device {device_id}")


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard")
async def get_dashboard_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get real-time dashboard metrics.

    Returns aggregated metrics optimized for dashboard display:
    - Device counts (total, online, offline)
    - Content metrics (plays, watch time, trending)
    - System health (CPU, memory, sessions, errors)

    **Performance:** < 500ms (materialized view + Redis)

    **Refresh Rate:** Data refreshed every 5 minutes
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting dashboard data",
        request_id=request_id
    )

    try:
        analytics = AnalyticsService(db, redis)
        data = await analytics.get_dashboard_data()

        logger.info(
            "Dashboard data retrieved successfully",
            request_id=request_id,
            devices_online=data.get('devices', {}).get('online', 0)
        )

        return success_response(
            data=data,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Dashboard data retrieval failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to retrieve dashboard data")


@router.get("/trending")
async def get_trending_content(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of results (1-50)"),
    period: str = Query('24h', regex='^(24h|7d|30d)$', description="Time period"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trending content.

    Returns most-viewed content based on recent activity.

    **Periods:**
    - 24h: Last 24 hours
    - 7d: Last 7 days
    - 30d: Last 30 days

    **Performance:** < 200ms (Redis sorted set)
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting trending content",
        request_id=request_id,
        limit=limit,
        period=period
    )

    try:
        analytics = AnalyticsService(db, redis)
        trending = await analytics.get_trending_content(limit=limit, period=period)

        logger.info(
            "Trending content retrieved successfully",
            request_id=request_id,
            count=len(trending)
        )

        return success_response(
            data=trending,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Trending content retrieval failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to retrieve trending content")


# ============================================================================
# ADMIN/MAINTENANCE ENDPOINTS
# ============================================================================

@router.post("/maintenance/flush-buffer")
async def force_flush_buffer(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Force flush event buffer to database.

    Admin endpoint for manual buffer flush.
    Normally happens automatically every 30s or 1000 events.

    **Requires:** Admin privileges
    """
    request_id = get_request_id(request)

    logger.info(
        "Forcing buffer flush",
        request_id=request_id,
        admin_user_id=current_user.id
    )

    try:
        analytics = AnalyticsService(db, redis)
        count = await analytics.flush_buffer()

        logger.info(
            "Buffer flushed successfully",
            request_id=request_id,
            events_flushed=count
        )

        return success_response(
            data={
                "status": "success",
                "events_flushed": count,
                "message": f"Flushed {count} events to database"
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Buffer flush failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to flush buffer")


@router.post("/maintenance/refresh-views")
async def refresh_materialized_views(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Refresh materialized views.

    Admin endpoint for manual view refresh.
    Normally happens automatically every 5 minutes.

    **Requires:** Admin privileges
    """
    request_id = get_request_id(request)

    logger.info(
        "Refreshing materialized views",
        request_id=request_id,
        admin_user_id=current_user.id
    )

    try:
        analytics = AnalyticsService(db, redis)
        success = await analytics.refresh_materialized_views()

        if success:
            logger.info(
                "Materialized views refreshed successfully",
                request_id=request_id
            )

            return success_response(
                data={
                    "status": "success",
                    "message": "Materialized views refreshed"
                },
                request_id=request_id
            )
        else:
            raise BadRequestException(detail="View refresh failed")

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(
            "View refresh failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to refresh views")


@router.post("/maintenance/aggregate-hourly")
async def run_hourly_aggregation(
    request: Request,
    hour: Optional[datetime] = Query(None, description="Hour to aggregate (default: previous hour)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Run hourly data aggregation.

    Admin endpoint for manual aggregation.
    Normally triggered by scheduled task.

    **Requires:** Admin privileges
    """
    request_id = get_request_id(request)

    target_hour = hour or (datetime.now() - timedelta(hours=1))
    target_hour = target_hour.replace(minute=0, second=0, microsecond=0)

    logger.info(
        "Running hourly aggregation",
        request_id=request_id,
        target_hour=target_hour.isoformat(),
        admin_user_id=current_user.id
    )

    try:
        analytics = AnalyticsService(db, redis)
        success = await analytics.aggregate_hourly_data(target_hour)

        if success:
            logger.info(
                "Hourly aggregation completed successfully",
                request_id=request_id,
                target_hour=target_hour.isoformat()
            )

            return success_response(
                data={
                    "status": "success",
                    "hour": target_hour.isoformat(),
                    "message": f"Aggregated data for {target_hour}"
                },
                request_id=request_id
            )
        else:
            raise BadRequestException(detail="Aggregation failed")

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(
            "Hourly aggregation failed",
            request_id=request_id,
            target_hour=target_hour.isoformat(),
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to aggregate hourly data")


@router.post("/maintenance/aggregate-daily")
async def run_daily_aggregation(
    request: Request,
    target_date: Optional[date] = Query(None, description="Date to aggregate (default: yesterday)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Run daily data aggregation.

    Admin endpoint for manual aggregation.
    Normally triggered by scheduled task at end of day.

    **Requires:** Admin privileges
    """
    request_id = get_request_id(request)

    agg_date = target_date or (date.today() - timedelta(days=1))

    logger.info(
        "Running daily aggregation",
        request_id=request_id,
        target_date=agg_date.isoformat(),
        admin_user_id=current_user.id
    )

    try:
        analytics = AnalyticsService(db, redis)
        success = await analytics.aggregate_daily_data(agg_date)

        if success:
            logger.info(
                "Daily aggregation completed successfully",
                request_id=request_id,
                target_date=agg_date.isoformat()
            )

            return success_response(
                data={
                    "status": "success",
                    "date": agg_date.isoformat(),
                    "message": f"Aggregated data for {agg_date}"
                },
                request_id=request_id
            )
        else:
            raise BadRequestException(detail="Aggregation failed")

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(
            "Daily aggregation failed",
            request_id=request_id,
            target_date=agg_date.isoformat(),
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(detail="Failed to aggregate daily data")


# ============================================================================
# WEBSOCKET ENDPOINT (REAL-TIME METRICS)
# ============================================================================

@router.websocket("/ws/metrics")
async def metrics_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    WebSocket endpoint for real-time metrics streaming.

    Pushes dashboard metrics every 5 seconds.
    Client receives JSON updates for live dashboard.
    """
    await websocket.accept()

    logger.info("WebSocket connection established for metrics streaming")

    try:
        analytics = AnalyticsService(db, redis)

        while True:
            # Get fresh metrics
            metrics = await analytics.get_dashboard_data()

            # Send to client
            await websocket.send_json(metrics)

            # Wait 5 seconds
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for metrics streaming")
    except Exception as e:
        logger.error(
            "WebSocket error for metrics streaming",
            error=str(e),
            exc_info=True
        )
        await websocket.close()
