"""
SQLAlchemy Models
Database representation for Device
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from shared.database import Base


class DeviceModel(Base):
    """Device database model"""
    __tablename__ = "devices"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    device_type = Column(String(20), nullable=False)  # 'tv' or 'monitor'
    device_name = Column(String(200), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Activation
    unique_code = Column(String(6), unique=True, nullable=True, index=True)  # 6-digit code
    code_expires_at = Column(DateTime(timezone=True), nullable=True)
    device_uuid = Column(String(100), unique=True, nullable=True, index=True)  # For WebOS

    # Network info
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    local_ip = Column(String(45), nullable=True)  # Local network IP from WebRTC (e.g., 192.168.1.100)
    platform = Column(String(50), nullable=True)  # 'webOS', 'browser', etc.

    # GeoIP data (Phase 6: Server-Side Features)
    geo_city = Column(String(100), nullable=True)
    geo_country = Column(String(100), nullable=True)
    geo_country_code = Column(String(10), nullable=True)
    geo_region = Column(String(100), nullable=True)
    geo_isp = Column(String(200), nullable=True)
    geo_timezone = Column(String(50), nullable=True)
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    geo_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Device metadata
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    device_pixel_ratio = Column(Float, nullable=True)
    user_agent = Column(Text, nullable=True)  # Modern user agents can exceed 500 chars
    connection_type = Column(String(50), nullable=True)
    connection_speed = Column(Float, nullable=True)
    connection_drops_count = Column(Integer, default=0, nullable=True)  # Number of network disconnections since startup

    # WebOS specific
    model_name = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='pending', index=True)  # 'pending', 'active', 'inactive'
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Display settings
    rotation = Column(Integer, default=0, nullable=False)  # 0, 90, 180, 270
    is_volume_enabled = Column(Boolean, default=True, nullable=False)
    volume_level = Column(Integer, default=75, nullable=False)  # 0-100 volume level

    # Content assignment
    assigned_playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True)
    background_audio_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)  # Background audio to loop

    # Hotel-specific
    room_number = Column(String(50), nullable=True, index=True)
    location_type = Column(String(50), default='guest_room', nullable=False)
    is_personalization_supported = Column(Boolean, default=True, nullable=False)
    privacy_mode = Column(String(20), default='limited', nullable=False)  # 'none', 'limited', 'full'

    # Audit tracking
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)  # When device was released/deactivated
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Relationships (using string references to avoid circular imports)
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    assigned_playlist = relationship("PlaylistModel", foreign_keys=[assigned_playlist_id])
    background_audio = relationship("ContentModel", foreign_keys=[background_audio_id])
    creator = relationship("UserModel", foreign_keys=[created_by_id])
    updater = relationship("UserModel", foreign_keys=[updated_by_id])
    deleter = relationship("UserModel", foreign_keys=[deleted_by_id])

    # Many-to-many relationships
    tags = relationship("TagModel", secondary="device_tags", back_populates="devices")
    commands = relationship("DeviceCommandModel", back_populates="device", cascade="all, delete-orphan")
    health_metrics = relationship("DeviceHealthMetricModel", back_populates="device", cascade="all, delete-orphan")


class DeviceTagModel(Base):
    """Device Tag Association database model (Many-to-Many)"""
    __tablename__ = "device_tags"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    # Association metadata
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('device_id', 'tag_id', name='uix_device_tag'),
        Index('ix_device_tags_device_id', 'device_id'),
        Index('ix_device_tags_tag_id', 'tag_id'),
    )

    # Relationships
    device = relationship("DeviceModel")
    tag = relationship("TagModel")
    assigned_by_user = relationship("UserModel", foreign_keys=[assigned_by_id])


class DeviceCommandModel(Base):
    """Device Command database model"""
    __tablename__ = "device_commands"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Command details
    command_type = Column(String(50), nullable=False)
    command_data = Column("command_data", type_=__import__('sqlalchemy').dialects.postgresql.JSONB, default={})

    # Status tracking
    status = Column(String(20), nullable=False, default='pending', index=True)
    priority = Column(Integer, nullable=False, default=5)

    # Execution tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column("result", type_=__import__('sqlalchemy').dialects.postgresql.JSONB, nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Audit tracking
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    device = relationship("DeviceModel", back_populates="commands")
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    created_by_user = relationship("UserModel", foreign_keys=[created_by_id])


class DeviceHealthMetricModel(Base):
    """Device Health Metric database model"""
    __tablename__ = "device_health_metrics"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # System metrics
    cpu_usage = Column(__import__('sqlalchemy').Numeric(5, 2), nullable=True)
    memory_usage = Column(__import__('sqlalchemy').Numeric(5, 2), nullable=True)
    memory_total_mb = Column(Integer, nullable=True)
    memory_used_mb = Column(Integer, nullable=True)
    disk_usage = Column(__import__('sqlalchemy').Numeric(5, 2), nullable=True)
    disk_total_gb = Column(Integer, nullable=True)
    disk_used_gb = Column(Integer, nullable=True)

    # Network metrics
    network_latency_ms = Column(Integer, nullable=True)
    network_download_mbps = Column(__import__('sqlalchemy').Numeric(10, 2), nullable=True)
    network_upload_mbps = Column(__import__('sqlalchemy').Numeric(10, 2), nullable=True)
    dns_resolution_ms = Column(Integer, nullable=True)  # Phase 5: DNS lookup time
    connection_quality = Column(String(20), nullable=True)

    # Display metrics
    display_resolution = Column(String(20), nullable=True)
    display_refresh_rate = Column(Integer, nullable=True)

    # Player metrics
    player_version = Column(String(50), nullable=True)
    player_uptime_hours = Column(Integer, nullable=True)
    content_errors_count = Column(Integer, default=0, nullable=False)
    last_error_message = Column(String, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)

    # Behavioral metrics (Phase 3)
    playback_stalls_count = Column(Integer, default=0, nullable=True)  # Video stall events
    buffer_underruns_count = Column(Integer, default=0, nullable=True)  # Buffer underrun events
    time_to_first_playback_ms = Column(Integer, nullable=True)  # Time from load to first frame
    content_play_count = Column(Integer, default=0, nullable=True)  # Total content plays this session
    quality_switches_count = Column(Integer, default=0, nullable=True)  # HLS quality switches
    content_load_failures_count = Column(Integer, default=0, nullable=True)  # Content load failures
    error_rate_percent = Column(__import__('sqlalchemy').Numeric(5, 2), nullable=True)  # Error rate percentage

    # Performance metrics (Phase 4)
    fps_current = Column(Integer, nullable=True)  # Current frames per second
    long_tasks_count = Column(Integer, default=0, nullable=True)  # Long tasks (>50ms) since startup
    cpu_pressure = Column(String(20), nullable=True)  # CPU pressure state: nominal/fair/serious/critical
    ttfb_ms = Column(Integer, nullable=True)  # Time to First Byte (ms)
    page_load_time_ms = Column(Integer, nullable=True)  # Total page load time (ms)

    # Health status
    overall_status = Column(String(20), default='healthy', nullable=False, index=True)
    is_alert_triggered = Column(Boolean, default=False, nullable=False, index=True)
    alert_message = Column(String, nullable=True)

    # Additional data (use extra_data to avoid SQLAlchemy reserved name)
    extra_data = Column("metadata", type_=__import__('sqlalchemy').dialects.postgresql.JSONB, default={})

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    device = relationship("DeviceModel", back_populates="health_metrics")
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])




class DeviceConnectionLogModel(Base):
    """Device Connection Log database model"""
    __tablename__ = "device_connection_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Log data
    logged_at = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'network', 'server', 'speed_test'
    status = Column(String(20), nullable=False)  # 'online', 'offline', 'connected', 'disconnected', 'tested'

    # Optional metrics
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    download_speed_mbps = Column(__import__('sqlalchemy').Numeric(10, 2), nullable=True)
    upload_speed_mbps = Column(__import__('sqlalchemy').Numeric(10, 2), nullable=True)

    # Dedicated columns for frequently queried fields (added in migration 046)
    connection_type = Column(String(20), nullable=True)  # Network connection type
    effective_type = Column(String(10), nullable=True)  # Effective network type
    rtt_ms = Column(Integer, nullable=True)  # Round-trip time
    endpoint = Column(String(200), nullable=True)  # API endpoint accessed
    http_status = Column(Integer, nullable=True)  # HTTP status code
    test_trigger = Column(String(10), nullable=True)  # Speed test trigger (auto/manual)
    test_duration_ms = Column(Integer, nullable=True)  # Speed test duration

    extra_metadata = Column("metadata", type_=JSONB, nullable=True)  # Use 'metadata' as column name in DB, 'extra_metadata' in Python

    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    device = relationship("DeviceModel", foreign_keys=[device_id])


class DeviceLogModel(Base):
    """Device Log database model for browser console logs"""
    __tablename__ = "device_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Log details
    log_level = Column(String(20), nullable=False, index=True)  # 'log', 'info', 'warn', 'error', 'debug'
    message = Column(Text, nullable=False)

    # Optional context
    source = Column(String(500), nullable=True)  # File:line where log originated
    stack_trace = Column(Text, nullable=True)  # Error stack trace
    user_agent = Column(Text, nullable=True)  # Modern user agents can exceed 500 chars  # Browser user agent
    url = Column(String(1000), nullable=True)  # Page URL when logged

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)  # When log was created

    # Composite index for common queries
    __table_args__ = (
        Index('ix_device_logs_device_level_timestamp', 'device_id', 'log_level', 'recorded_at'),
        Index('ix_device_logs_organization', 'organization_id'),
    )

    # Relationships
    device = relationship("DeviceModel", foreign_keys=[device_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])


class DeviceCapabilitiesModel(Base):
    """Device Capabilities database model - stores static device info sent once on startup"""
    __tablename__ = "device_capabilities"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Screen & Display
    screen_width = Column(Integer, nullable=False)
    screen_height = Column(Integer, nullable=False)
    device_pixel_ratio = Column(Float, nullable=False)
    display_refresh_rate = Column(Integer, nullable=False)

    # Hardware
    hardware_concurrency = Column(Integer, nullable=False)  # CPU cores
    device_memory_gb = Column(Float, nullable=True)  # Device RAM in GB (Chrome/Edge only)

    # Video Codec Support
    codec_h264 = Column(Boolean, default=False, nullable=False)
    codec_h265 = Column(Boolean, default=False, nullable=False)
    codec_vp9 = Column(Boolean, default=False, nullable=False)
    codec_av1 = Column(Boolean, default=False, nullable=False)

    # Audio Codec Support
    codec_aac = Column(Boolean, default=False, nullable=False)
    codec_opus = Column(Boolean, default=False, nullable=False)

    # Graphics
    webgl_version = Column(String(10), nullable=False)  # "none", "1.0", "2.0"
    webgl_renderer = Column(String(200), nullable=True)
    webgl_vendor = Column(String(200), nullable=True)

    # Software
    user_agent = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False)
    player_version = Column(String(50), nullable=False)

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("DeviceModel", foreign_keys=[device_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
