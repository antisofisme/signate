"""
Analytics API Routes
HTTP endpoints for analytics and playback tracking
Phase 2 Day 2 - Analytics Service
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger
from shared.pagination import PaginationParams
import time

from .repositories.analytics_repo import AnalyticsRepository
from .dtos import (
    AnalyticsQueryRequest,
    TimelineQueryRequest,
    PlaybackLogRequest,
    PlaybackEndRequest,
    ContentPerformanceResponse,
    DeviceEngagementResponse,
    PlaybackStatsResponse,
    PlaybackTimelineResponse,
    PlaybackLogResponse,
    AnalyticsDashboardResponse,
    TimelineDataPoint
)

router = APIRouter()
request_logger = RequestLogger()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_analytics_repository(db: Session = Depends(get_db)) -> AnalyticsRepository:
    """Get analytics repository instance"""
    return AnalyticsRepository(db)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard")
@handle_errors
def get_analytics_dashboard(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get complete analytics dashboard

    Returns overall stats, top content, and top devices
    Requires authentication
    """
    start_time = time.time()

    # Get overall stats
    stats = analytics_repo.get_playback_stats(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )

    # Get top content
    top_content = analytics_repo.get_content_performance(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit
    )

    # Get top devices
    top_devices = analytics_repo.get_device_engagement(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit
    )

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/dashboard",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data={
            "stats": stats,
            "top_content": top_content,
            "top_devices": top_devices
        },
        message="Analytics dashboard retrieved successfully"
    )


@router.get("/content-performance")
@handle_errors
def get_content_performance(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get content performance analytics

    Returns list of content with playback statistics
    Requires authentication
    """
    start_time = time.time()

    content_performance = analytics_repo.get_content_performance(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit
    )

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/content-performance",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=content_performance,
        message=f"Retrieved {len(content_performance)} content performance records"
    )


@router.get("/device-engagement")
@handle_errors
def get_device_engagement(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get device engagement analytics

    Returns list of devices with engagement statistics
    Requires authentication
    """
    start_time = time.time()

    device_engagement = analytics_repo.get_device_engagement(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit
    )

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/device-engagement",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=device_engagement,
        message=f"Retrieved {len(device_engagement)} device engagement records"
    )


@router.get("/stats")
@handle_errors
def get_playback_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get overall playback statistics

    Returns aggregate statistics for the organization
    Requires authentication
    """
    start_time = time.time()

    stats = analytics_repo.get_playback_stats(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/stats",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=stats,
        message="Playback statistics retrieved successfully"
    )


@router.get("/timeline")
@handle_errors
def get_playback_timeline(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interval: str = Query("day", regex="^(day|week|month)$"),
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get playback timeline

    Returns time-series data of playback activity
    Requires authentication
    """
    start_time = time.time()

    timeline_data = analytics_repo.get_playback_timeline(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/timeline",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data={
            "data": timeline_data,
            "interval": interval,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        message=f"Retrieved {len(timeline_data)} timeline data points"
    )


@router.post("/playback/start")
@handle_errors
def start_playback_log(
    request_body: PlaybackLogRequest,
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Log playback start

    Creates a new playback log entry
    Used by player devices to track content playback
    """
    start_time = time.time()

    # Create playback log
    playback_data = request_body.dict()
    playback_data["started_at"] = datetime.now(timezone.utc)
    playback_data["organization_id"] = current_user.organization_id

    log = analytics_repo.log_playback(playback_data)

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="POST",
        path="/api/v1/analytics/playback/start",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=log.to_dict(),
        message="Playback started and logged successfully"
    )


@router.put("/playback/{log_id}/end")
@handle_errors
def end_playback_log(
    log_id: int,
    request_body: PlaybackEndRequest,
    current_user: CurrentUser = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Log playback end

    Updates playback log with end time and completion status
    Used by player devices to complete playback tracking
    """
    start_time = time.time()

    # Update playback log
    log = analytics_repo.update_playback_end(
        log_id=log_id,
        ended_at=datetime.now(timezone.utc),
        duration_seconds=request_body.duration_seconds,
        completed=request_body.completed
    )

    if not log:
        from shared.errors import NotFoundError
        raise NotFoundError(message=f"Playback log with ID {log_id} not found")

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="PUT",
        path=f"/api/v1/analytics/playback/{log_id}/end",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=log.to_dict(),
        message="Playback ended and logged successfully"
    )
