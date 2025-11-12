"""
SQLAlchemy Models
Database representation for Device
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    platform = Column(String(50), nullable=True)  # 'webOS', 'browser', etc.

    # Device metadata
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    device_pixel_ratio = Column(Float, nullable=True)
    user_agent = Column(String(500), nullable=True)
    connection_type = Column(String(50), nullable=True)
    connection_speed = Column(Float, nullable=True)

    # WebOS specific
    model_name = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='pending', index=True)  # 'pending', 'active', 'inactive'
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Display settings
    rotation = Column(Integer, default=0, nullable=False)  # 0, 90, 180, 270
    volume_enabled = Column(Boolean, default=True, nullable=False)
    
    # Content assignment
    assigned_playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True)

    # Hotel-specific
    room_number = Column(String(50), nullable=True, index=True)
    location_type = Column(String(50), default='guest_room', nullable=False)
    supports_personalization = Column(Boolean, default=True, nullable=False)
    privacy_mode = Column(String(20), default='limited', nullable=False)  # 'none', 'limited', 'full'

    # Audit tracking
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)  # When device was released/deactivated

    # Relationships
    # organization = relationship("OrganizationModel", back_populates="devices")
    creator = relationship("UserModel", foreign_keys=[created_by])
    updater = relationship("UserModel", foreign_keys=[updated_by])


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
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


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
    connection_quality = Column(String(20), nullable=True)

    # Display metrics
    display_resolution = Column(String(20), nullable=True)
    display_refresh_rate = Column(Integer, nullable=True)
    gpu_usage = Column(__import__('sqlalchemy').Numeric(5, 2), nullable=True)

    # Player metrics
    player_version = Column(String(50), nullable=True)
    player_uptime_hours = Column(Integer, nullable=True)
    content_errors_count = Column(Integer, default=0, nullable=False)
    last_error_message = Column(String, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)

    # Health status
    overall_status = Column(String(20), default='healthy', nullable=False, index=True)
    alert_triggered = Column(Boolean, default=False, nullable=False, index=True)
    alert_message = Column(String, nullable=True)

    # Additional data (use extra_data to avoid SQLAlchemy reserved name)
    extra_data = Column("metadata", type_=__import__('sqlalchemy').dialects.postgresql.JSONB, default={})

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DeviceGroupModel(Base):
    """Device Group database model"""
    __tablename__ = "device_groups"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Group info
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

    # Hierarchy
    parent_group_id = Column(Integer, ForeignKey("device_groups.id"), nullable=True, index=True)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Metadata
    group_type = Column(String(50), nullable=True)  # 'chain', 'hotel', 'floor', 'location', 'custom'
    sort_order = Column(Integer, default=0, nullable=False)

    # Settings
    default_playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=True)

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Audit
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class DeviceGroupMemberModel(Base):
    """Device Group Member database model (Many-to-Many)"""
    __tablename__ = "device_group_members"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Relations
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("device_groups.id"), nullable=False, index=True)

    # Membership metadata
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
