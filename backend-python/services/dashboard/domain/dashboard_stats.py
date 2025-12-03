"""
Dashboard Domain Entities

Domain models for dashboard statistics and metrics.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Dashboard Statistics
# ============================================================================

@dataclass
class DashboardStats:
    """Overall dashboard statistics entity"""
    total_devices: int
    online_devices: int
    offline_devices: int
    warning_devices: int
    error_devices: int
    total_contents: int
    total_storage_bytes: int
    active_playlists: int
    total_watch_time_seconds: int = 0
    avg_completion_rate: float = 0.0
    total_playback_events: int = 0


# ============================================================================
# Device Health
# ============================================================================

@dataclass
class DeviceIssue:
    """Device issue details entity"""
    type: str
    count: int
    devices: List[str]


@dataclass
class DeviceHealthSummary:
    """Device health summary entity"""
    healthy: int
    warning: int
    error: int
    offline: int
    issues: List[DeviceIssue]


# ============================================================================
# Live Devices
# ============================================================================

@dataclass
class LiveDevice:
    """Live device status entity"""
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

@dataclass
class ContentPerformance:
    """Content performance metrics entity"""
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

@dataclass
class ActivePlaylistAssignment:
    """Active playlist assignment details entity"""
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

@dataclass
class PlaybackTimeline:
    """Playback timeline data point entity"""
    date: str
    playback_count: int
    unique_devices: int
    total_duration_seconds: int


# ============================================================================
# Recent Activity
# ============================================================================

@dataclass
class RecentActivity:
    """Recent activity item entity"""
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

@dataclass
class SystemAlert:
    """System alert entity"""
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

@dataclass
class ContentByType:
    """Content count by type entity"""
    type: str
    count: int
    size_bytes: int


@dataclass
class SystemInfo:
    """System information entity"""
    storage_total_bytes: int
    storage_used_bytes: int
    storage_free_bytes: int
    content_by_type: List[ContentByType]
    database_size_bytes: int
    uptime_seconds: int


# ============================================================================
# Menu Analytics (NEW)
# ============================================================================

@dataclass
class MenuViewsByDevice:
    """Menu views breakdown by device type"""
    mobile: int = 0
    tablet: int = 0
    desktop: int = 0
    unknown: int = 0


@dataclass
class TopMenu:
    """Top performing menu"""
    menu_id: int
    menu_name: str
    menu_type: str
    views: int
    contact_clicks: int


@dataclass
class MenuStats:
    """Menu statistics for dashboard"""
    total_menus: int
    active_menus: int
    total_items: int
    total_views: int
    total_contact_clicks: int
    views_by_device: MenuViewsByDevice
    top_menus: List[TopMenu]


# ============================================================================
# Schedule Overview (NEW)
# ============================================================================

@dataclass
class ActiveSchedule:
    """Currently active schedule"""
    schedule_id: int
    name: str
    playlist_name: Optional[str]
    priority: int
    start_time: Optional[str]
    end_time: Optional[str]


@dataclass
class ScheduleOverview:
    """Schedule overview for dashboard"""
    total_schedules: int
    active_schedules: int
    running_now: int
    ending_soon: int  # Schedules ending within 7 days
    active_today: List[ActiveSchedule]
