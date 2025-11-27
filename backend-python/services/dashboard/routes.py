"""
Dashboard Routes

API endpoints for dashboard statistics and metrics.
Thin HTTP layer that delegates to use cases.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from shared.database import get_db
from shared.auth import get_current_user
from services.auth.repositories.models import UserModel

from .dtos import (
    DashboardStatsResponse,
    DeviceHealthSummaryResponse,
    LiveDeviceResponse,
    ContentPerformanceResponse,
    ActivePlaylistAssignmentResponse,
    PlaybackTimelineResponse,
    RecentActivityResponse,
    SystemAlertResponse,
    SystemInfoResponse,
    ContentByType,
)

from .repositories.dashboard_repo import DashboardRepository
from .use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from .use_cases.get_device_health import GetDeviceHealthUseCase
from .use_cases.get_live_devices import GetLiveDevicesUseCase
from .use_cases.get_content_performance import GetContentPerformanceUseCase
from .use_cases.get_active_playlists import GetActivePlaylistsUseCase
from .use_cases.get_playback_timeline import GetPlaybackTimelineUseCase
from .use_cases.get_recent_activity import GetRecentActivityUseCase
from .use_cases.get_system_alerts import GetSystemAlertsUseCase
from .use_cases.get_system_info import GetSystemInfoUseCase


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


# ============================================================================
# Dependency: Dashboard Repository
# ============================================================================

def get_dashboard_repo(db: Session = Depends(get_db)) -> DashboardRepository:
    """Get dashboard repository instance"""
    return DashboardRepository(db)


# ============================================================================
# GET /dashboard/stats - Overall statistics
# ============================================================================

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get overall dashboard statistics"""
    use_case = GetDashboardStatsUseCase(dashboard_repo)
    stats = use_case.execute(current_user.organization_id)

    return DashboardStatsResponse(
        total_devices=stats.total_devices,
        online_devices=stats.online_devices,
        offline_devices=stats.offline_devices,
        warning_devices=stats.warning_devices,
        error_devices=stats.error_devices,
        total_contents=stats.total_contents,
        total_storage_bytes=stats.total_storage_bytes,
        active_playlists=stats.active_playlists,
        total_watch_time_seconds=stats.total_watch_time_seconds,
        avg_completion_rate=stats.avg_completion_rate,
        total_playback_events=stats.total_playback_events
    )


# ============================================================================
# GET /dashboard/device-health - Device health summary
# ============================================================================

@router.get("/device-health", response_model=DeviceHealthSummaryResponse)
def get_device_health(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get device health summary"""
    use_case = GetDeviceHealthUseCase(dashboard_repo)
    health = use_case.execute(current_user.organization_id)

    return DeviceHealthSummaryResponse(
        healthy=health.healthy,
        warning=health.warning,
        error=health.error,
        offline=health.offline,
        issues=health.issues
    )


# ============================================================================
# GET /dashboard/live-devices - Live device status
# ============================================================================

@router.get("/live-devices", response_model=List[LiveDeviceResponse])
def get_live_devices(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get live device status list"""
    use_case = GetLiveDevicesUseCase(dashboard_repo)
    devices = use_case.execute(current_user.organization_id)

    return [
        LiveDeviceResponse(
            id=device.id,
            name=device.name,
            status=device.status,
            location=device.location,
            current_content=device.current_content,
            last_seen_at=device.last_seen_at,
            cpu_usage=device.cpu_usage,
            memory_usage=device.memory_usage,
            storage_usage=device.storage_usage
        )
        for device in devices
    ]


# ============================================================================
# GET /dashboard/content-performance - Content performance metrics
# ============================================================================

@router.get("/content-performance", response_model=List[ContentPerformanceResponse])
def get_content_performance(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get content performance metrics"""
    use_case = GetContentPerformanceUseCase(dashboard_repo)
    performances = use_case.execute(current_user.organization_id, limit)

    return [
        ContentPerformanceResponse(
            content_id=perf.content_id,
            content_name=perf.content_name,
            content_type=perf.content_type,
            total_plays=perf.total_plays,
            unique_devices=perf.unique_devices,
            total_duration_seconds=perf.total_duration_seconds,
            avg_completion_rate=perf.avg_completion_rate,
            last_played=perf.last_played
        )
        for perf in performances
    ]


# ============================================================================
# GET /dashboard/active-playlists - Active playlist assignments
# ============================================================================

@router.get("/active-playlists", response_model=List[ActivePlaylistAssignmentResponse])
def get_active_playlists(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get active playlist assignments"""
    use_case = GetActivePlaylistsUseCase(dashboard_repo)
    playlists = use_case.execute(current_user.organization_id)

    return [
        ActivePlaylistAssignmentResponse(
            playlist_id=playlist.playlist_id,
            playlist_name=playlist.playlist_name,
            device_count=playlist.device_count,
            content_count=playlist.content_count,
            total_duration_seconds=playlist.total_duration_seconds,
            last_updated=playlist.last_updated,
            devices=playlist.devices
        )
        for playlist in playlists
    ]


# ============================================================================
# GET /dashboard/playback-timeline - Playback timeline data
# ============================================================================

@router.get("/playback-timeline", response_model=List[PlaybackTimelineResponse])
def get_playback_timeline(
    days: int = Query(default=7, ge=1, le=30),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get playback timeline for the last N days"""
    use_case = GetPlaybackTimelineUseCase(dashboard_repo)
    timeline = use_case.execute(days)

    return [
        PlaybackTimelineResponse(
            date=point.date,
            playback_count=point.playback_count,
            unique_devices=point.unique_devices,
            total_duration_seconds=point.total_duration_seconds
        )
        for point in timeline
    ]


# ============================================================================
# GET /dashboard/recent-activity - Recent activity feed
# ============================================================================

@router.get("/recent-activity", response_model=List[RecentActivityResponse])
def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get recent activity from audit logs"""
    use_case = GetRecentActivityUseCase(dashboard_repo)
    activities = use_case.execute(current_user.organization_id, limit)

    return [
        RecentActivityResponse(
            id=activity.id,
            timestamp=activity.timestamp,
            action=activity.action,
            user=activity.user,
            resource_type=activity.resource_type,
            resource_name=activity.resource_name,
            details=activity.details
        )
        for activity in activities
    ]


# ============================================================================
# GET /dashboard/alerts - System alerts
# ============================================================================

@router.get("/alerts", response_model=List[SystemAlertResponse])
def get_system_alerts(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get system alerts"""
    use_case = GetSystemAlertsUseCase(dashboard_repo)
    alerts = use_case.execute(current_user.organization_id)

    return [
        SystemAlertResponse(
            id=alert.id,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            timestamp=alert.timestamp,
            acknowledged=alert.acknowledged,
            device_id=alert.device_id,
            device_name=alert.device_name
        )
        for alert in alerts
    ]


# ============================================================================
# POST /dashboard/alerts/{alert_id}/acknowledge - Acknowledge alert
# ============================================================================

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    current_user: UserModel = Depends(get_current_user)
):
    """Acknowledge a system alert"""
    # TODO: Implement alert acknowledgement persistence if needed
    return {"status": "acknowledged", "alert_id": alert_id}


# ============================================================================
# GET /dashboard/system-info - System information
# ============================================================================

@router.get("/system-info", response_model=SystemInfoResponse)
def get_system_info(
    current_user: UserModel = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """Get system information"""
    use_case = GetSystemInfoUseCase(dashboard_repo)
    info = use_case.execute(current_user.organization_id)

    # Convert domain ContentByType to DTO ContentByType
    content_by_type_dto = [
        ContentByType(type=c.type, count=c.count, size_bytes=c.size_bytes)
        for c in info.content_by_type
    ]

    return SystemInfoResponse(
        storage_total_bytes=info.storage_total_bytes,
        storage_used_bytes=info.storage_used_bytes,
        storage_free_bytes=info.storage_free_bytes,
        content_by_type=content_by_type_dto,
        database_size_bytes=info.database_size_bytes,
        uptime_seconds=info.uptime_seconds
    )
