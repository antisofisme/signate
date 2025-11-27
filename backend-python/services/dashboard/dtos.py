"""
Dashboard DTOs

Response models for dashboard endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Dashboard Stats
# ============================================================================

class DashboardStatsResponse(BaseModel):
    """Overall dashboard statistics"""
    total_devices: int
    online_devices: int
    offline_devices: int
    warning_devices: int
    error_devices: int
    total_contents: int
    total_storage_bytes: int
    active_playlists: int
    total_watch_time_seconds: int
    avg_completion_rate: float
    total_playback_events: int


# ============================================================================
# Device Health
# ============================================================================

class DeviceIssue(BaseModel):
    """Device issue details"""
    type: str
    count: int
    devices: List[str]


class DeviceHealthSummaryResponse(BaseModel):
    """Device health summary"""
    healthy: int
    warning: int
    error: int
    offline: int
    issues: List[DeviceIssue]


# ============================================================================
# Live Devices
# ============================================================================

class LiveDeviceResponse(BaseModel):
    """Live device status"""
    id: int
    name: str
    status: str  # 'online' | 'offline' | 'warning' | 'error'
    location: Optional[str]
    current_content: Optional[str]
    last_seen_at: Optional[datetime]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    storage_usage: Optional[float]


# ============================================================================
# Content Performance
# ============================================================================

class ContentPerformanceResponse(BaseModel):
    """Content performance metrics"""
    content_id: int
    content_name: str
    content_type: str
    total_plays: int
    unique_devices: int
    total_duration_seconds: int
    avg_completion_rate: float
    last_played: Optional[datetime]


# ============================================================================
# Active Playlists
# ============================================================================

class ActivePlaylistAssignmentResponse(BaseModel):
    """Active playlist assignment details"""
    playlist_id: int
    playlist_name: str
    device_count: int
    content_count: int
    total_duration_seconds: int
    last_updated: Optional[datetime]
    devices: List[str]


# ============================================================================
# Playback Timeline
# ============================================================================

class PlaybackTimelineResponse(BaseModel):
    """Playback timeline data point"""
    date: str
    playback_count: int
    unique_devices: int
    total_duration_seconds: int


# ============================================================================
# Recent Activity
# ============================================================================

class RecentActivityResponse(BaseModel):
    """Recent activity item"""
    id: int
    timestamp: datetime
    action: str
    user: str
    resource_type: str
    resource_name: str
    details: Optional[str]


# ============================================================================
# System Alerts
# ============================================================================

class SystemAlertResponse(BaseModel):
    """System alert"""
    id: int
    severity: str  # 'info' | 'warning' | 'error' | 'critical'
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool
    device_id: Optional[int]
    device_name: Optional[str]


# ============================================================================
# System Info
# ============================================================================

class ContentByType(BaseModel):
    """Content count by type"""
    type: str
    count: int
    size_bytes: int


class SystemInfoResponse(BaseModel):
    """System information"""
    storage_total_bytes: int
    storage_used_bytes: int
    storage_free_bytes: int
    content_by_type: List[ContentByType]
    database_size_bytes: int
    uptime_seconds: int
