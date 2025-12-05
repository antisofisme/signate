"""
Device DTOs (Data Transfer Objects)
Request/Response models for Device API layer
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class RequestActivationCodeRequest(BaseModel):
    """Request activation code - called by player"""
    # 🔒 SECURITY: organization_id removed - should come from device_token JWT or be assigned during activation
    # 🚫 DO NOT allow player to send organization_id - prevents org hijacking attack
    # ✨ ARCHITECTURAL FIX: code is now optional - backend generates code if not provided
    # This ensures backend is the single source of truth for activation codes
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit activation code (optional - backend generates if not provided)")
    device_type: str = Field(default='monitor', pattern='^(tv|monitor)$')
    device_name: str = Field(default='New Device', max_length=200)
    device_uuid: Optional[str] = Field(None, max_length=100)
    platform: str = Field(default='browser', max_length=50)
    device_token: Optional[str] = Field(None, max_length=500)  # JWT token for re-registration


class ActivateDeviceRequest(BaseModel):
    """Activate device - called by CMS admin"""
    unique_code: str = Field(..., min_length=6, max_length=6)
    device_name: Optional[str] = Field(None, max_length=200)
    room_number: Optional[str] = Field(None, max_length=50)
    location_type: Optional[str] = Field(None, pattern='^(guest_room|lobby|conference_room|restaurant|other)$')


class HeartbeatRequest(BaseModel):
    """
    Heartbeat from player - sent every 30 seconds

    OPTIMIZED (Phase 2):
    - Static fields (screen_width, screen_height, device_pixel_ratio, user_agent)
      are now sent ONCE via /capabilities endpoint on startup
    - Viewport only included when changed
    - Added connection_drops_count for reliability tracking
    """
    unique_code: str = Field(..., min_length=6, max_length=6)
    device_uuid: Optional[str] = None

    # Static fields - DEPRECATED, now sent via /capabilities
    # Kept for backward compatibility with older players
    screen_width: Optional[int] = Field(None, gt=0)
    screen_height: Optional[int] = Field(None, gt=0)
    device_pixel_ratio: Optional[float] = Field(None, gt=0)
    user_agent: Optional[str] = Field(None, max_length=500)

    # Semi-static fields - only sent when changed
    viewport_width: Optional[int] = Field(None, gt=0)
    viewport_height: Optional[int] = Field(None, gt=0)

    # Dynamic fields - always sent
    connection_type: Optional[str] = Field(None, max_length=50)
    connection_speed: Optional[float] = Field(None, ge=0)

    # Connection reliability tracking (NEW)
    connection_drops_count: Optional[int] = Field(None, ge=0, description="Number of network disconnections since startup")


class UpdateDeviceRequest(BaseModel):
    """Update device settings - called by CMS admin"""
    device_name: Optional[str] = Field(None, max_length=200)
    room_number: Optional[str] = Field(None, max_length=50)
    location_type: Optional[str] = Field(None, pattern='^(guest_room|lobby|conference_room|restaurant|other)$')
    rotation: Optional[int] = Field(None, ge=0, le=360)  # Rotation in degrees (0, 90, 180, 270)
    is_volume_enabled: Optional[bool] = None
    is_personalization_supported: Optional[bool] = None
    privacy_mode: Optional[str] = Field(None, pattern='^(none|limited|full)$')


class DeviceLogEntry(BaseModel):
    """Single console log entry from player browser"""
    level: Literal['log', 'info', 'warn', 'error', 'debug'] = Field(..., description="Console log level")
    message: str = Field(..., max_length=5000, description="Log message content")
    timestamp: str = Field(..., description="ISO format timestamp from player")

    # Optional context fields
    source: Optional[str] = Field(None, max_length=500, description="File:line where log originated (e.g., 'app.js:42')")
    stack_trace: Optional[str] = Field(None, max_length=10000, description="Error stack trace if available")
    user_agent: Optional[str] = Field(None, max_length=500, description="Browser user agent string")
    url: Optional[str] = Field(None, max_length=1000, description="Page URL when log was created")


class BatchDeviceLogsRequest(BaseModel):
    """Batch of console logs from player - sent periodically"""
    logs: List[DeviceLogEntry] = Field(..., min_items=1, max_items=100, description="Console log entries")


class ValidateResetPasswordRequest(BaseModel):
    """Validate reset password - called by player before hard reset"""
    password: str = Field(..., min_length=1, max_length=100)


class ConnectionLogEntryDTO(BaseModel):
    """Single connection log entry from player"""
    logged_at: datetime = Field(..., description="Timestamp when event occurred on player device")
    event_type: Literal['network', 'server', 'speed_test'] = Field(..., description="Type of event")
    status: str = Field(..., max_length=20, description="Event status")
    latency_ms: Optional[int] = Field(None, ge=0, description="Network latency in milliseconds")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error details if failed")
    download_speed_mbps: Optional[float] = Field(None, ge=0, description="Download speed in Mbps")
    upload_speed_mbps: Optional[float] = Field(None, ge=0, description="Upload speed in Mbps")

    # Dedicated fields for better query performance (added in migration 046)
    connection_type: Optional[str] = Field(None, max_length=20, description="Network type: wifi, ethernet, cellular, etc")
    effective_type: Optional[str] = Field(None, max_length=10, description="Effective network type: 4g, 3g, 2g, etc")
    rtt_ms: Optional[int] = Field(None, ge=0, description="Round-trip time in milliseconds")
    endpoint: Optional[str] = Field(None, max_length=200, description="API endpoint accessed")
    http_status: Optional[int] = Field(None, description="HTTP status code")
    test_trigger: Optional[str] = Field(None, max_length=10, description="Speed test trigger: auto or manual")
    test_duration_ms: Optional[int] = Field(None, ge=0, description="Speed test duration in milliseconds")

    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")


class SaveConnectionLogsDTO(BaseModel):
    """Batch connection logs from player - sent every 5 minutes"""
    logs: List[ConnectionLogEntryDTO] = Field(..., min_items=1, max_items=100, description="Connection log entries")


class DeviceLogResponse(BaseModel):
    """Single device log response - for CMS"""
    id: int
    device_id: int
    organization_id: int
    log_level: str
    message: str
    source: Optional[str]
    stack_trace: Optional[str]
    user_agent: Optional[str]
    url: Optional[str]
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceLogsListResponse(BaseModel):
    """List of device logs with pagination"""
    items: List[DeviceLogResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class SaveDeviceLogsResponse(BaseModel):
    """Response after saving batch of logs"""
    success: bool = True
    logs_saved: int
    message: str = "Logs saved successfully"

    class Config:
        from_attributes = True


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class ActivationCodeResponse(BaseModel):
    """Activation code response - for player"""
    unique_code: str
    device_id: int
    device_token: Optional[str] = None  # 🔑 JWT token for re-registration (only if org assigned)

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Device response - for CMS"""
    id: int
    device_type: str
    device_name: str
    organization_id: Optional[int]  # None for unassigned devices

    # Activation info
    unique_code: Optional[str]
    code_expires_at: Optional[datetime]
    device_uuid: Optional[str]

    # Network info
    ip_address: Optional[str]
    platform: Optional[str]

    # GeoIP data (Phase 6)
    geo_city: Optional[str] = None
    geo_country: Optional[str] = None
    geo_country_code: Optional[str] = None
    geo_region: Optional[str] = None
    geo_isp: Optional[str] = None
    geo_timezone: Optional[str] = None
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None

    # Device metadata
    screen_width: Optional[int]
    screen_height: Optional[int]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]
    connection_type: Optional[str]
    connection_speed: Optional[float]
    connection_drops_count: Optional[int]  # Network disconnections since startup

    # WebOS specific
    model_name: Optional[str]
    firmware_version: Optional[str]

    # Status
    status: str
    last_seen_at: Optional[datetime]
    is_online: bool  # Computed field

    # Display settings
    rotation: int
    is_volume_enabled: bool

    # Hotel-specific
    room_number: Optional[str]
    location_type: str
    is_personalization_supported: bool
    privacy_mode: str

    # Assigned playlist info
    playlist_name: Optional[str] = None  # Name of assigned playlist (from JOIN)

    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    released_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceActivationResponse(BaseModel):
    """Response when device is activated - includes JWT token"""
    device: DeviceResponse
    token: str = Field(..., description="JWT token for device authentication")
    message: Optional[str] = None


class DeviceListResponse(BaseModel):
    """List of devices - for CMS dashboard"""
    items: list[DeviceResponse]  # Changed from 'devices' to 'items' to match frontend
    total: int
    online: int

    class Config:
        from_attributes = True


class HeartbeatResponse(BaseModel):
    """Heartbeat response - minimal response to player"""
    success: bool = True
    message: str = "Heartbeat received"

    class Config:
        from_attributes = True


class ActivationStatusResponse(BaseModel):
    """Check activation status - for player polling"""
    activated: bool  # Player expects 'activated' not 'is_activated'
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    organization_id: Optional[int] = None  # For player to know which org it belongs to
    organization_pin: Optional[str] = None  # 6-digit PIN for hard reset (if org assigned)
    device_token: Optional[str] = None  # JWT token for session restore after cache clear
    unique_code: Optional[str] = None  # 6-digit activation code for heartbeat
    message: str

    class Config:
        from_attributes = True


# =============================================================================
# DEVICE COMMANDS DTOs
# =============================================================================

class DeviceCommandCreate(BaseModel):
    """Create device command - called by CMS"""
    command_type: str = Field(..., pattern='^(reboot|refresh_content|update_settings|clear_cache|screenshot|update_playlist)$')
    command_data: Optional[dict] = Field(default={})
    priority: int = Field(default=5, ge=1, le=10)
    expires_in_minutes: int = Field(default=60, ge=5, le=1440)


class BulkDeviceCommandCreate(BaseModel):
    """Create command for multiple devices"""
    device_ids: list[int] = Field(..., min_items=1, max_items=100)
    command_type: str = Field(..., pattern='^(reboot|refresh_content|update_settings|clear_cache|screenshot|update_playlist)$')
    command_data: Optional[dict] = Field(default={})
    priority: int = Field(default=5, ge=1, le=10)
    expires_in_minutes: int = Field(default=60, ge=5, le=1440)


class DeviceCommandResponse(BaseModel):
    """Device command response"""
    id: int
    device_id: int
    organization_id: int
    command_type: str
    command_data: dict
    status: str
    priority: int
    sent_at: Optional[datetime]
    executed_at: Optional[datetime]
    failed_at: Optional[datetime]
    result: Optional[dict]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class PendingCommandsResponse(BaseModel):
    """Pending commands response - for player"""
    commands: list[DeviceCommandResponse]
    count: int


class CommandExecutionRequest(BaseModel):
    """Mark command as executed - from player"""
    result: Optional[dict] = Field(default={"status": "success"})


class CommandFailureRequest(BaseModel):
    """Mark command as failed - from player"""
    error_message: str = Field(..., max_length=500)


# =============================================================================
# DEVICE HEALTH METRICS DTOs
# =============================================================================

class DeviceHealthMetricsCreate(BaseModel):
    """
    Record health metrics - called by player every 5 minutes

    OPTIMIZED (Phase 2):
    - player_version kept for backward compatibility (now also in /capabilities)

    ENHANCED (Phase 3):
    - Added behavioral metrics (stalls, buffers, quality switches, etc.)
    """
    # System metrics
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_total_mb: Optional[float] = Field(None, ge=0)  # Allow float from player
    memory_used_mb: Optional[float] = Field(None, ge=0)   # Allow float from player
    disk_usage: Optional[float] = Field(None, ge=0, le=100)
    disk_total_gb: Optional[float] = Field(None, ge=0)    # Allow float from player
    disk_used_gb: Optional[float] = Field(None, ge=0)     # Allow float from player

    # Network metrics
    network_latency_ms: Optional[int] = Field(None, ge=0)
    network_download_mbps: Optional[float] = Field(None, ge=0)
    network_upload_mbps: Optional[float] = Field(None, ge=0)
    dns_resolution_ms: Optional[int] = Field(None, ge=0, description="DNS lookup time in milliseconds")  # Phase 5
    connection_quality: Optional[str] = Field(None, max_length=20)  # From player

    # Display metrics
    display_resolution: Optional[str] = Field(None, max_length=20)
    display_refresh_rate: Optional[int] = Field(None, gt=0)

    # Player metrics
    player_version: Optional[str] = Field(None, max_length=50)
    player_uptime_hours: Optional[int] = Field(None, ge=0)
    content_errors_count: int = Field(default=0, ge=0)
    last_error_message: Optional[str] = Field(None, max_length=500)
    last_error_at: Optional[str] = Field(None, max_length=50)  # ISO timestamp from player

    # Behavioral metrics (Phase 3)
    playback_stalls_count: Optional[int] = Field(None, ge=0, description="Video stall events since startup")
    buffer_underruns_count: Optional[int] = Field(None, ge=0, description="Buffer underrun events since startup")
    time_to_first_playback_ms: Optional[int] = Field(None, ge=0, description="Time from load to first frame (ms)")
    content_play_count: Optional[int] = Field(None, ge=0, description="Total content plays this session")
    quality_switches_count: Optional[int] = Field(None, ge=0, description="HLS quality switches this session")
    content_load_failures_count: Optional[int] = Field(None, ge=0, description="Content load failures this session")
    error_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Error rate percentage")

    # Performance metrics (Phase 4)
    fps_current: Optional[int] = Field(None, ge=0, description="Current frames per second")
    long_tasks_count: Optional[int] = Field(None, ge=0, description="Long tasks (>50ms) since startup")
    cpu_pressure: Optional[str] = Field(None, max_length=20, description="CPU pressure state: nominal/fair/serious/critical")
    ttfb_ms: Optional[int] = Field(None, ge=0, description="Time to First Byte (ms)")
    page_load_time_ms: Optional[int] = Field(None, ge=0, description="Total page load time (ms)")

    # Additional metadata
    metadata: Optional[dict] = Field(default={})

    model_config = {"extra": "ignore"}  # Ignore any extra fields player might send


class DeviceHealthResponse(BaseModel):
    """Device health response with behavioral and performance metrics (Phase 3 & 4)"""
    id: int
    device_id: int
    organization_id: int

    # System metrics
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    memory_total_mb: Optional[int]
    memory_used_mb: Optional[int]
    disk_usage: Optional[float]
    disk_total_gb: Optional[int]
    disk_used_gb: Optional[int]

    # Network metrics
    network_latency_ms: Optional[int]
    network_download_mbps: Optional[float]
    network_upload_mbps: Optional[float]
    dns_resolution_ms: Optional[int]  # Phase 5
    connection_quality: Optional[str]

    # Display metrics
    display_resolution: Optional[str]
    display_refresh_rate: Optional[int]

    # Player metrics
    player_version: Optional[str]
    player_uptime_hours: Optional[int]
    content_errors_count: int
    last_error_message: Optional[str]
    last_error_at: Optional[datetime]

    # Behavioral metrics (Phase 3)
    playback_stalls_count: Optional[int] = None
    buffer_underruns_count: Optional[int] = None
    time_to_first_playback_ms: Optional[int] = None
    content_play_count: Optional[int] = None
    quality_switches_count: Optional[int] = None
    content_load_failures_count: Optional[int] = None
    error_rate_percent: Optional[float] = None

    # Performance metrics (Phase 4)
    fps_current: Optional[int] = None
    long_tasks_count: Optional[int] = None
    cpu_pressure: Optional[str] = None
    ttfb_ms: Optional[int] = None
    page_load_time_ms: Optional[int] = None

    # Health status
    overall_status: str
    is_alert_triggered: bool
    alert_message: Optional[str]

    # Metadata
    metadata: dict
    recorded_at: datetime

    class Config:
        from_attributes = True


class HealthAlertResponse(BaseModel):
    """Health alert response"""
    alert_type: str
    alert_level: str
    alert_message: str
    metric_value: float
    threshold_value: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class DeviceHealthWithAlertsResponse(BaseModel):
    """Device health with alerts"""
    health: Optional[DeviceHealthResponse]
    alerts: list[HealthAlertResponse]


class HealthHistoryResponse(BaseModel):
    """Health history response"""
    history: list[DeviceHealthResponse]
    count: int


class OrganizationHealthSummaryResponse(BaseModel):
    """Organization health summary"""
    total_devices: int
    healthy_devices: int
    warning_devices: int
    critical_devices: int
    offline_devices: int
    avg_cpu_usage: Optional[float]
    avg_memory_usage: Optional[float]
    avg_disk_usage: Optional[float]
    devices_with_errors: int

    class Config:
        from_attributes = True


# =============================================================================
# DEVICE CAPABILITIES DTOs
# =============================================================================

class DeviceCapabilitiesCreate(BaseModel):
    """
    Device capabilities - sent ONCE on startup
    Static device info that rarely changes (screen, hardware, codecs)
    """
    # Screen & Display
    screen_width: int = Field(..., gt=0)
    screen_height: int = Field(..., gt=0)
    device_pixel_ratio: float = Field(..., gt=0)
    display_refresh_rate: int = Field(..., gt=0)

    # Hardware
    hardware_concurrency: int = Field(..., ge=1)  # CPU cores
    device_memory_gb: Optional[float] = Field(None, ge=0)  # Device RAM in GB (Chrome/Edge only)

    # Video Codec Support
    codec_h264: bool = Field(...)  # H.264/AVC
    codec_h265: bool = Field(...)  # H.265/HEVC
    codec_vp9: bool = Field(...)   # VP9
    codec_av1: bool = Field(...)   # AV1

    # Audio Codec Support
    codec_aac: bool = Field(...)   # AAC
    codec_opus: bool = Field(...)  # Opus

    # Graphics
    webgl_version: str = Field(..., max_length=10)  # "none", "1.0", "2.0"
    webgl_renderer: Optional[str] = Field(None, max_length=200)
    webgl_vendor: Optional[str] = Field(None, max_length=200)

    # Software
    user_agent: str = Field(..., max_length=500)
    platform: str = Field(..., max_length=50)
    player_version: str = Field(..., max_length=50)

    model_config = {"extra": "ignore"}


class DeviceCapabilitiesResponse(BaseModel):
    """Device capabilities response"""
    id: int
    device_id: int
    organization_id: int

    # Screen & Display
    screen_width: int
    screen_height: int
    device_pixel_ratio: float
    display_refresh_rate: int

    # Hardware
    hardware_concurrency: int
    device_memory_gb: Optional[float]

    # Video Codec Support
    codec_h264: bool
    codec_h265: bool
    codec_vp9: bool
    codec_av1: bool

    # Audio Codec Support
    codec_aac: bool
    codec_opus: bool

    # Graphics
    webgl_version: str
    webgl_renderer: Optional[str]
    webgl_vendor: Optional[str]

    # Software
    user_agent: str
    platform: str
    player_version: str

    # Timestamps
    recorded_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


