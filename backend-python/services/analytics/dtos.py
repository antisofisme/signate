"""
Analytics DTOs (Data Transfer Objects)
Request and Response models for Analytics API
Phase 2 Day 2 - Analytics Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST DTOs
# ============================================================================

class AnalyticsQueryRequest(BaseModel):
    """Request model for analytics queries"""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")


class TimelineQueryRequest(BaseModel):
    """Request model for timeline analytics"""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    interval: Optional[str] = Field("day", description="Grouping interval (day, week, month)")


class PlaybackLogRequest(BaseModel):
    """Request model for logging playback"""
    content_id: int = Field(..., description="Content ID being played")
    device_id: int = Field(..., description="Device ID playing content")
    playlist_id: Optional[int] = Field(None, description="Playlist ID (if part of playlist)")
    organization_id: Optional[int] = Field(None, description="Organization ID (optional - taken from device JWT if not provided)")
    expected_duration: Optional[int] = Field(None, description="Expected duration in seconds")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")
    playback_quality: Optional[str] = Field(None, description="Playback quality (SD, HD, FHD)")

    model_config = {"extra": "ignore"}  # Ignore any extra fields from player


class PlaybackEndRequest(BaseModel):
    """Request model for ending playback"""
    duration_seconds: int = Field(..., ge=0, description="Actual playback duration in seconds")
    completed: bool = Field(False, description="Whether playback completed successfully")
    error_count: Optional[int] = Field(0, description="Number of errors during playback")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")

    model_config = {"extra": "ignore"}  # Ignore any extra fields from player


# ============================================================================
# RESPONSE DTOs
# ============================================================================

class ContentPerformanceResponse(BaseModel):
    """Response model for content performance"""
    content_id: int
    title: str
    content_type: str
    total_plays: int
    completed_plays: int
    avg_duration_seconds: Optional[float]
    last_played_at: Optional[datetime]
    unique_devices: int
    completion_rate: Optional[float]


class DeviceEngagementResponse(BaseModel):
    """Response model for device engagement"""
    device_id: int
    device_name: str
    total_plays: int
    unique_content: int
    last_playback_at: Optional[datetime]
    total_watch_time_seconds: int
    total_watch_time_hours: float


class PlaybackStatsResponse(BaseModel):
    """Response model for overall playback statistics"""
    total_plays: int
    completed_plays: int
    unique_content: int
    unique_devices: int
    total_watch_time_seconds: int
    total_watch_time_hours: float
    completion_rate: float
    period_start: str
    period_end: str


class TimelineDataPoint(BaseModel):
    """Single data point in timeline"""
    period: datetime
    total_plays: int
    completed_plays: int
    unique_content: int
    unique_devices: int
    total_watch_time_seconds: int


class PlaybackTimelineResponse(BaseModel):
    """Response model for playback timeline"""
    data: List[TimelineDataPoint]
    interval: str
    start_date: str
    end_date: str


class PlaybackLogResponse(BaseModel):
    """Response model for playback log"""
    id: int
    content_id: int
    device_id: int
    playlist_id: Optional[int]
    organization_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    expected_duration: Optional[int]
    completed: bool
    playback_quality: Optional[str]
    error_count: int
    created_at: datetime


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics dashboard response"""
    stats: PlaybackStatsResponse
    top_content: List[ContentPerformanceResponse]
    top_devices: List[DeviceEngagementResponse]


# ============================================================================
# MENU ANALYTICS DTOs (REAL DATA from menu_views table)
# ============================================================================

class MenuViewTrendPoint(BaseModel):
    """Single data point for menu view trends"""
    date: str
    views: int
    contact_clicks: int
    mobile: int = 0
    tablet: int = 0
    desktop: int = 0
    unknown: int = 0


class TopMenuResponse(BaseModel):
    """Top performing menu response"""
    menu_id: int
    menu_name: str
    menu_type: str
    total_views: int
    contact_clicks: int
    mobile_views: int
    tablet_views: int
    desktop_views: int


class PopularHourResponse(BaseModel):
    """Popular viewing hours response"""
    hour: int  # 0-23
    views: int
    percentage: float


class MenuAnalyticsTrendResponse(BaseModel):
    """Complete menu analytics trend response"""
    period_start: str
    period_end: str
    total_views: int
    total_contact_clicks: int
    views_by_device: Dict[str, int]
    daily_trend: List[MenuViewTrendPoint]
    top_menus: List[TopMenuResponse]
    popular_hours: List[PopularHourResponse]


# ============================================================================
# DEVICE HEALTH ANALYTICS DTOs (REAL DATA from device_health_metrics table)
# ============================================================================

class DeviceHealthTrendPoint(BaseModel):
    """Single data point for device health trends"""
    date: str
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_disk_usage: float
    avg_network_latency_ms: Optional[float] = None
    devices_reporting: int


class DeviceHealthSummary(BaseModel):
    """Health summary for a single device"""
    device_id: int
    device_name: str
    latest_cpu_usage: Optional[float] = None
    latest_memory_usage: Optional[float] = None
    latest_disk_usage: Optional[float] = None
    health_score: int  # 0-100
    status: str  # 'healthy', 'warning', 'critical'
    last_reported_at: Optional[datetime] = None


class DeviceHealthTrendResponse(BaseModel):
    """Complete device health trend response"""
    period_start: str
    period_end: str
    fleet_health_score: int  # 0-100
    devices_healthy: int
    devices_warning: int
    devices_critical: int
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_disk_usage: float
    daily_trend: List[DeviceHealthTrendPoint]
    device_summaries: List[DeviceHealthSummary]
