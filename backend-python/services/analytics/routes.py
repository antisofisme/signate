"""
Analytics API Routes
HTTP endpoints for analytics and playback tracking
Phase 2 Day 2 - Analytics Service

Updated: Added Menu Analytics and Device Health trends endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import Optional
from datetime import datetime, timezone, timedelta

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser, get_current_device, CurrentDevice
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
    TimelineDataPoint,
    # New Menu Analytics DTOs
    MenuViewTrendPoint,
    TopMenuResponse,
    PopularHourResponse,
    MenuAnalyticsTrendResponse,
    # New Device Health DTOs
    DeviceHealthTrendPoint,
    DeviceHealthSummary,
    DeviceHealthTrendResponse,
)

# Import models for direct queries
from services.menu.repositories.models import MenuViewModel, MenuModel
from services.device.repositories.models import DeviceHealthMetricModel, DeviceModel

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
    current_device: CurrentDevice = Depends(get_current_device),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Log playback start

    Creates a new playback log entry
    Used by player devices to track content playback
    Requires device authentication (device JWT token)
    """
    start_time = time.time()

    # Create playback log
    playback_data = request_body.dict()
    playback_data["started_at"] = datetime.now(timezone.utc)
    playback_data["organization_id"] = current_device.organization_id

    # Convert playlist_id: 0 to None (player sends 0 when no playlist)
    if playback_data.get("playlist_id") == 0:
        playback_data["playlist_id"] = None

    log = analytics_repo.log_playback(playback_data)

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="POST",
        path="/api/v1/analytics/playback/start",
        status_code=200,
        duration_ms=duration_ms,
        user_id=None  # Device request, no user_id
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
    current_device: CurrentDevice = Depends(get_current_device),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Log playback end

    Updates playback log with end time and completion status
    Used by player devices to complete playback tracking
    Requires device authentication (device JWT token)
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
        user_id=None  # Device request, no user_id
    )

    return success_response(
        data=log.to_dict(),
        message="Playback ended and logged successfully"
    )


# ============================================================================
# MENU ANALYTICS ENDPOINTS (REAL DATA from menu_views table)
# ============================================================================

@router.get("/menu-trends")
@handle_errors
def get_menu_analytics_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get menu analytics trends with REAL data

    Returns:
    - Daily view trends
    - Views by device type
    - Top performing menus
    - Popular viewing hours

    Data source: menu_views table (real tracking data)
    """
    start_time = time.time()
    org_id = current_user.organization_id

    # Default date range: last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Base query filter
    base_filter = and_(
        MenuViewModel.organization_id == org_id,
        MenuViewModel.viewed_at >= start_date,
        MenuViewModel.viewed_at <= end_date
    )

    # 1. Total views and contact clicks
    totals = db.query(
        func.count(MenuViewModel.id).label('total_views'),
        func.sum(case((MenuViewModel.contact_clicked == True, 1), else_=0)).label('total_contact_clicks')
    ).filter(base_filter).first()

    total_views = totals.total_views or 0
    total_contact_clicks = totals.total_contact_clicks or 0

    # 2. Views by device type
    device_breakdown = db.query(
        MenuViewModel.device_type,
        func.count(MenuViewModel.id).label('count')
    ).filter(base_filter).group_by(
        MenuViewModel.device_type
    ).all()

    views_by_device = {
        'mobile': 0,
        'tablet': 0,
        'desktop': 0,
        'unknown': 0
    }
    for device_type, count in device_breakdown:
        if device_type in views_by_device:
            views_by_device[device_type] = count
        else:
            views_by_device['unknown'] += count

    # 3. Daily trend
    daily_trend_raw = db.query(
        func.date(MenuViewModel.viewed_at).label('date'),
        func.count(MenuViewModel.id).label('views'),
        func.sum(case((MenuViewModel.contact_clicked == True, 1), else_=0)).label('contact_clicks'),
        func.sum(case((MenuViewModel.device_type == 'mobile', 1), else_=0)).label('mobile'),
        func.sum(case((MenuViewModel.device_type == 'tablet', 1), else_=0)).label('tablet'),
        func.sum(case((MenuViewModel.device_type == 'desktop', 1), else_=0)).label('desktop'),
    ).filter(base_filter).group_by(
        func.date(MenuViewModel.viewed_at)
    ).order_by(
        func.date(MenuViewModel.viewed_at).asc()
    ).all()

    daily_trend = [
        MenuViewTrendPoint(
            date=str(row.date),
            views=row.views or 0,
            contact_clicks=row.contact_clicks or 0,
            mobile=row.mobile or 0,
            tablet=row.tablet or 0,
            desktop=row.desktop or 0,
            unknown=(row.views or 0) - (row.mobile or 0) - (row.tablet or 0) - (row.desktop or 0)
        )
        for row in daily_trend_raw
    ]

    # 4. Top menus
    top_menus_raw = db.query(
        MenuViewModel.menu_id,
        MenuModel.name.label('menu_name'),
        MenuModel.menu_type,
        func.count(MenuViewModel.id).label('total_views'),
        func.sum(case((MenuViewModel.contact_clicked == True, 1), else_=0)).label('contact_clicks'),
        func.sum(case((MenuViewModel.device_type == 'mobile', 1), else_=0)).label('mobile_views'),
        func.sum(case((MenuViewModel.device_type == 'tablet', 1), else_=0)).label('tablet_views'),
        func.sum(case((MenuViewModel.device_type == 'desktop', 1), else_=0)).label('desktop_views'),
    ).join(
        MenuModel, MenuViewModel.menu_id == MenuModel.id
    ).filter(base_filter).group_by(
        MenuViewModel.menu_id,
        MenuModel.name,
        MenuModel.menu_type
    ).order_by(
        func.count(MenuViewModel.id).desc()
    ).limit(10).all()

    top_menus = [
        TopMenuResponse(
            menu_id=row.menu_id,
            menu_name=row.menu_name,
            menu_type=row.menu_type,
            total_views=row.total_views or 0,
            contact_clicks=row.contact_clicks or 0,
            mobile_views=row.mobile_views or 0,
            tablet_views=row.tablet_views or 0,
            desktop_views=row.desktop_views or 0
        )
        for row in top_menus_raw
    ]

    # 5. Popular hours
    popular_hours_raw = db.query(
        func.extract('hour', MenuViewModel.viewed_at).label('hour'),
        func.count(MenuViewModel.id).label('views')
    ).filter(base_filter).group_by(
        func.extract('hour', MenuViewModel.viewed_at)
    ).order_by(
        func.extract('hour', MenuViewModel.viewed_at).asc()
    ).all()

    popular_hours = [
        PopularHourResponse(
            hour=int(row.hour),
            views=row.views or 0,
            percentage=round((row.views / total_views * 100), 1) if total_views > 0 else 0
        )
        for row in popular_hours_raw
    ]

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/menu-trends",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=MenuAnalyticsTrendResponse(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_views=total_views,
            total_contact_clicks=total_contact_clicks,
            views_by_device=views_by_device,
            daily_trend=daily_trend,
            top_menus=top_menus,
            popular_hours=popular_hours
        ).model_dump(),
        message="Menu analytics trends retrieved successfully"
    )


# ============================================================================
# DEVICE HEALTH ANALYTICS ENDPOINTS (REAL DATA from device_health_metrics table)
# ============================================================================

@router.get("/device-health-trends")
@handle_errors
def get_device_health_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get device health analytics trends with REAL data

    Returns:
    - Daily health trends (CPU, memory, disk usage)
    - Fleet health score
    - Device health summaries

    Data source: device_health_metrics table (real device metrics)
    """
    start_time = time.time()
    org_id = current_user.organization_id

    # Default date range: last 7 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=7)

    # Base query filter
    base_filter = and_(
        DeviceHealthMetricModel.organization_id == org_id,
        DeviceHealthMetricModel.recorded_at >= start_date,
        DeviceHealthMetricModel.recorded_at <= end_date
    )

    # 1. Daily trend
    daily_trend_raw = db.query(
        func.date(DeviceHealthMetricModel.recorded_at).label('date'),
        func.avg(DeviceHealthMetricModel.cpu_usage).label('avg_cpu'),
        func.avg(DeviceHealthMetricModel.memory_usage).label('avg_memory'),
        func.avg(DeviceHealthMetricModel.disk_usage).label('avg_disk'),
        func.avg(DeviceHealthMetricModel.network_latency_ms).label('avg_latency'),
        func.count(func.distinct(DeviceHealthMetricModel.device_id)).label('devices_reporting')
    ).filter(base_filter).group_by(
        func.date(DeviceHealthMetricModel.recorded_at)
    ).order_by(
        func.date(DeviceHealthMetricModel.recorded_at).asc()
    ).all()

    daily_trend = [
        DeviceHealthTrendPoint(
            date=str(row.date),
            avg_cpu_usage=round(float(row.avg_cpu or 0), 1),
            avg_memory_usage=round(float(row.avg_memory or 0), 1),
            avg_disk_usage=round(float(row.avg_disk or 0), 1),
            avg_network_latency_ms=round(float(row.avg_latency), 1) if row.avg_latency else None,
            devices_reporting=row.devices_reporting or 0
        )
        for row in daily_trend_raw
    ]

    # 2. Overall averages
    overall_avg = db.query(
        func.avg(DeviceHealthMetricModel.cpu_usage).label('avg_cpu'),
        func.avg(DeviceHealthMetricModel.memory_usage).label('avg_memory'),
        func.avg(DeviceHealthMetricModel.disk_usage).label('avg_disk')
    ).filter(base_filter).first()

    avg_cpu = round(float(overall_avg.avg_cpu or 0), 1)
    avg_memory = round(float(overall_avg.avg_memory or 0), 1)
    avg_disk = round(float(overall_avg.avg_disk or 0), 1)

    # 3. Device summaries (latest metrics per device)
    # Subquery to get latest metric per device
    latest_subq = db.query(
        DeviceHealthMetricModel.device_id,
        func.max(DeviceHealthMetricModel.recorded_at).label('latest_at')
    ).filter(
        DeviceHealthMetricModel.organization_id == org_id
    ).group_by(
        DeviceHealthMetricModel.device_id
    ).subquery()

    device_summaries_raw = db.query(
        DeviceHealthMetricModel.device_id,
        DeviceModel.device_name.label('device_name'),
        DeviceHealthMetricModel.cpu_usage,
        DeviceHealthMetricModel.memory_usage,
        DeviceHealthMetricModel.disk_usage,
        DeviceHealthMetricModel.recorded_at
    ).join(
        latest_subq,
        and_(
            DeviceHealthMetricModel.device_id == latest_subq.c.device_id,
            DeviceHealthMetricModel.recorded_at == latest_subq.c.latest_at
        )
    ).join(
        DeviceModel, DeviceHealthMetricModel.device_id == DeviceModel.id
    ).filter(
        DeviceHealthMetricModel.organization_id == org_id
    ).all()

    # Calculate health scores
    device_summaries = []
    devices_healthy = 0
    devices_warning = 0
    devices_critical = 0

    for row in device_summaries_raw:
        cpu = float(row.cpu_usage or 0)
        memory = float(row.memory_usage or 0)
        disk = float(row.disk_usage or 0)

        # Calculate health score (inverse of max usage)
        max_usage = max(cpu, memory, disk)
        health_score = max(0, int(100 - max_usage))

        # Determine status
        if max_usage >= 90:
            status = 'critical'
            devices_critical += 1
        elif max_usage >= 70:
            status = 'warning'
            devices_warning += 1
        else:
            status = 'healthy'
            devices_healthy += 1

        device_summaries.append(DeviceHealthSummary(
            device_id=row.device_id,
            device_name=row.device_name,
            latest_cpu_usage=round(cpu, 1),
            latest_memory_usage=round(memory, 1),
            latest_disk_usage=round(disk, 1),
            health_score=health_score,
            status=status,
            last_reported_at=row.recorded_at
        ))

    # Calculate fleet health score
    total_devices = len(device_summaries)
    if total_devices > 0:
        fleet_health_score = int(
            (devices_healthy * 100 + devices_warning * 50 + devices_critical * 0) / total_devices
        )
    else:
        fleet_health_score = 100  # No devices = no issues

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_request(
        method="GET",
        path="/api/v1/analytics/device-health-trends",
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    return success_response(
        data=DeviceHealthTrendResponse(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            fleet_health_score=fleet_health_score,
            devices_healthy=devices_healthy,
            devices_warning=devices_warning,
            devices_critical=devices_critical,
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            avg_disk_usage=avg_disk,
            daily_trend=daily_trend,
            device_summaries=device_summaries
        ).model_dump(),
        message="Device health trends retrieved successfully"
    )
