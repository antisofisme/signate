"""
Analytics API Schemas
Standardized request/response models for analytics endpoints
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


# ============================================================================
# REQUEST MODELS
# ============================================================================

class DateRangeParams(BaseModel):
    """Common date range parameters for analytics queries"""
    start_date: Optional[date] = Field(None, description="Start date (inclusive)")
    end_date: Optional[date] = Field(None, description="End date (inclusive)")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("end_date must be after start_date")
        return v


class AnalyticsEvent(BaseModel):
    """Single analytics event for ingestion"""
    event_type: str = Field(..., description="Event type (content_play, heartbeat, etc.)")
    device_id: Optional[int] = Field(None, description="Device ID")
    content_id: Optional[int] = Field(None, description="Content ID")
    user_id: Optional[int] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Numeric metrics")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

    @validator('event_type')
    def validate_event_type(cls, v):
        allowed = {
            'content_play', 'content_pause', 'content_complete', 'content_error',
            'heartbeat', 'device_boot', 'device_shutdown', 'device_error',
            'playlist_start', 'playlist_complete', 'playlist_skip',
            'api_call', 'system_error'
        }
        if v not in allowed:
            raise ValueError(f"Invalid event_type. Must be one of: {allowed}")
        return v


class BulkEventsRequest(BaseModel):
    """Bulk event submission (up to 1000 events)"""
    events: List[AnalyticsEvent] = Field(..., description="List of events to ingest")

    @validator('events')
    def validate_events_count(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum 1000 events per request")
        if len(v) == 0:
            raise ValueError("Must provide at least 1 event")
        return v


class AggregationTargetRequest(BaseModel):
    """Target period for manual aggregation"""
    target_hour: Optional[datetime] = Field(None, description="Hour to aggregate")
    target_date: Optional[date] = Field(None, description="Date to aggregate")


# ============================================================================
# RESPONSE MODELS - Content Analytics
# ============================================================================

class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    timestamp: datetime = Field(description="Data point timestamp")
    value: float = Field(description="Metric value")
    label: Optional[str] = Field(None, description="Optional label for the data point")


class ContentStatsResponse(BaseModel):
    """Content performance statistics"""
    content_id: int
    period: Dict[str, str] = Field(description="Analysis period (start_date, end_date)")
    total_views: int = Field(description="Total number of views")
    unique_viewers: int = Field(description="Number of unique devices that viewed content")
    total_watch_time_seconds: int = Field(description="Total watch time in seconds")
    avg_watch_time_seconds: float = Field(description="Average watch time per view")
    completion_rate: float = Field(description="Percentage of views that completed (0-100)")
    error_count: int = Field(description="Number of playback errors")
    time_series: List[Dict[str, Any]] = Field(description="Time series data for charting")


class ContentTrendingRank(BaseModel):
    """Trending rank information for content"""
    content_id: int
    rank: Optional[int] = Field(None, description="Current trending rank (1-based, None if not trending)")
    views_24h: int = Field(description="Views in last 24 hours")
    is_trending: bool = Field(description="Whether content is in trending list")
    rank_change: Optional[int] = Field(None, description="Change in rank from previous period")


class TrendingContentItem(BaseModel):
    """Single item in trending content list"""
    content_id: int
    name: str
    content_type: str
    views: int
    thumbnail_url: Optional[str] = None


# ============================================================================
# RESPONSE MODELS - Device Analytics
# ============================================================================

class DeviceStatsResponse(BaseModel):
    """Device health and performance statistics"""
    device_id: int
    period: Dict[str, str] = Field(description="Analysis period (start_date, end_date)")
    uptime_percentage: float = Field(description="Device uptime percentage (0-100)")
    total_content_played: int = Field(description="Total number of content items played")
    unique_content_played: int = Field(default=0, description="Number of unique content items played")
    avg_cpu_usage: float = Field(description="Average CPU usage percentage")
    avg_memory_usage: float = Field(description="Average memory usage percentage")
    total_errors: int = Field(description="Total error count")
    total_bandwidth_mb: float = Field(description="Total bandwidth consumed in MB")
    time_series: List[Dict[str, Any]] = Field(description="Time series data for charting")


class DeviceRealtimeStatus(BaseModel):
    """Real-time device status from Redis"""
    device_id: int
    is_online: bool = Field(description="Whether device is currently online")
    last_heartbeat: Optional[str] = Field(None, description="Last heartbeat timestamp")
    current_content_id: Optional[int] = Field(None, description="ID of currently playing content")
    uptime_seconds: Optional[int] = Field(None, description="Current session uptime in seconds")


# ============================================================================
# RESPONSE MODELS - Dashboard & Overview
# ============================================================================

class DeviceCountStats(BaseModel):
    """Device count statistics"""
    total: int = Field(description="Total devices")
    online: int = Field(description="Currently online devices")
    offline: int = Field(description="Currently offline devices")
    active_24h: int = Field(default=0, description="Devices active in last 24h")


class ContentMetrics(BaseModel):
    """Content performance metrics"""
    total_plays: int = Field(description="Total content plays")
    total_watch_time_seconds: int = Field(description="Total watch time across all content")
    unique_content_played: int = Field(description="Number of unique content items played")
    avg_completion_rate: float = Field(description="Average completion rate (0-100)")
    trending_count: int = Field(default=0, description="Number of trending content items")


class SystemHealthMetrics(BaseModel):
    """System health metrics"""
    avg_cpu_usage: float = Field(description="Average CPU usage across devices")
    avg_memory_usage: float = Field(description="Average memory usage across devices")
    total_errors_24h: int = Field(description="Total errors in last 24 hours")
    active_sessions: int = Field(description="Number of active playback sessions")
    total_bandwidth_gb_24h: float = Field(default=0.0, description="Total bandwidth in last 24h (GB)")


class DashboardResponse(BaseModel):
    """Real-time dashboard overview data"""
    timestamp: str = Field(description="Response timestamp")
    devices: DeviceCountStats = Field(description="Device statistics")
    content: ContentMetrics = Field(description="Content performance metrics")
    system: SystemHealthMetrics = Field(description="System health metrics")


# ============================================================================
# RESPONSE MODELS - Maintenance & Admin
# ============================================================================

class BufferFlushResult(BaseModel):
    """Result of buffer flush operation"""
    status: str = Field(description="Operation status")
    events_flushed: int = Field(description="Number of events flushed to database")
    message: str = Field(description="Human-readable result message")


class ViewRefreshResult(BaseModel):
    """Result of materialized view refresh"""
    status: str = Field(description="Operation status")
    views_refreshed: List[str] = Field(default_factory=list, description="List of refreshed views")
    message: str = Field(description="Human-readable result message")


class AggregationResult(BaseModel):
    """Result of data aggregation operation"""
    status: str = Field(description="Operation status")
    period: str = Field(description="Aggregated period (hour or date)")
    records_processed: int = Field(default=0, description="Number of records processed")
    message: str = Field(description="Human-readable result message")


class EventIngestionResult(BaseModel):
    """Result of event ingestion"""
    status: str = Field(description="Ingestion status (accepted, queued, etc.)")
    events_received: int = Field(description="Number of events received")
    message: str = Field(description="Human-readable status message")


# ============================================================================
# ANALYTICS QUERY PARAMETERS
# ============================================================================

class TrendingPeriod(str):
    """Valid trending period values"""
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"


class ExportFormat(str):
    """Valid export format values"""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
