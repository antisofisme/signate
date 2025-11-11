"""
Hotel Integration Models
Models for hotel-specific features including PMS integration, guest mapping, and security
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ExternalDataSource(Base):
    """
    External API integrations (PMS, POS, CRM systems)

    Attributes:
        id: Primary key
        name: Name of the external system
        type: Type of integration (pms, pos, crm, other)
        api_endpoint: Base URL for API calls
        api_key_encrypted: Encrypted API key
        auth_type: Authentication method (oauth2, api_key, basic, custom)
        is_active: Whether integration is active
        sync_interval: Sync interval in seconds
        last_sync_at: Last successful sync timestamp
        config: JSON configuration including field mappings
        created_at: Timestamp when integration was created
        updated_at: Timestamp when integration was last updated
    """

    __tablename__ = "external_data_sources"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Integration Info
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # pms, pos, crm, other
    api_endpoint = Column(String(500), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    auth_type = Column(String(50), nullable=True)  # oauth2, api_key, basic, custom

    # Status & Sync
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    sync_interval = Column(Integer, default=30, nullable=True)  # seconds
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)  # Field mappings, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ExternalDataSource(id={self.id}, name='{self.name}', type='{self.type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "api_endpoint": self.api_endpoint,
            "auth_type": self.auth_type,
            "is_active": self.is_active,
            "sync_interval": self.sync_interval,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DeviceGuestMapping(Base):
    """
    Maps devices to current guests for personalization

    Attributes:
        id: Primary key
        device_id: Foreign key to devices table
        guest_id: Guest ID from PMS
        guest_name: Guest name (plain text, may be redacted)
        guest_name_encrypted: Encrypted guest name for GDPR compliance
        guest_nationality: Guest nationality code
        guest_language: Guest language preference
        loyalty_tier: Loyalty program tier
        room_number: Room number
        check_in_date: Check-in date
        check_out_date: Check-out date
        preferences: JSON: dietary, temperature, pillow type, etc.
        special_requests: Special requests text
        is_active: Whether mapping is currently active
        synced_from: Source system name
        last_synced_at: Last sync timestamp
        encryption_key_id: ID of encryption key used
        created_at: Timestamp when mapping was created
        updated_at: Timestamp when mapping was last updated
        deleted_at: Soft delete timestamp for retention policy
    """

    __tablename__ = "device_guest_mappings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Guest Info (from PMS)
    guest_id = Column(String(100), nullable=True, index=True)
    guest_name = Column(String(200), nullable=True)
    guest_name_encrypted = Column(LargeBinary, nullable=True)  # Encrypted for GDPR
    guest_nationality = Column(String(10), nullable=True)
    guest_language = Column(String(10), nullable=True)
    loyalty_tier = Column(String(50), nullable=True)

    # Reservation Info
    room_number = Column(String(20), nullable=True, index=True)
    check_in_date = Column(DateTime(timezone=True), nullable=True)
    check_out_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Preferences (JSONB for flexibility)
    preferences = Column(JSON, nullable=True)
    special_requests = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Audit & Sync
    synced_from = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    encryption_key_id = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    device = relationship("Device")

    def __repr__(self):
        return f"<DeviceGuestMapping(id={self.id}, device_id={self.device_id}, guest_name='{self.guest_name}', room='{self.room_number}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "guest_id": self.guest_id,
            "guest_name": self.guest_name,
            "guest_nationality": self.guest_nationality,
            "guest_language": self.guest_language,
            "loyalty_tier": self.loyalty_tier,
            "room_number": self.room_number,
            "check_in_date": self.check_in_date.isoformat() if self.check_in_date else None,
            "check_out_date": self.check_out_date.isoformat() if self.check_out_date else None,
            "preferences": self.preferences,
            "special_requests": self.special_requests,
            "is_active": self.is_active,
            "synced_from": self.synced_from,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class RoomConfiguration(Base):
    """
    Room-specific settings and device mappings

    Attributes:
        id: Primary key
        room_number: Unique room number
        device_id: Foreign key to devices table (nullable)
        room_type: Type of room (standard, deluxe, suite, etc.)
        floor: Floor number
        building: Building name/number
        default_playlist_id: Default playlist for this room
        default_language: Default language for content
        has_minibar: Whether room has minibar
        has_balcony: Whether room has balcony
        max_occupancy: Maximum occupancy
        created_at: Timestamp when configuration was created
        updated_at: Timestamp when configuration was last updated
    """

    __tablename__ = "room_configurations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Room Info
    room_number = Column(String(20), unique=True, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)

    # Room Details
    room_type = Column(String(50), nullable=True, index=True)
    floor = Column(Integer, nullable=True)
    building = Column(String(50), nullable=True)

    # Content Defaults
    default_playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True)
    default_language = Column(String(10), default='en', nullable=True)

    # Features
    has_minibar = Column(Boolean, default=False, nullable=True)
    has_balcony = Column(Boolean, default=False, nullable=True)
    max_occupancy = Column(Integer, default=2, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    device = relationship("Device")
    default_playlist = relationship("Playlist")

    def __repr__(self):
        return f"<RoomConfiguration(id={self.id}, room_number='{self.room_number}', room_type='{self.room_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "room_number": self.room_number,
            "device_id": self.device_id,
            "room_type": self.room_type,
            "floor": self.floor,
            "building": self.building,
            "default_playlist_id": self.default_playlist_id,
            "default_language": self.default_language,
            "has_minibar": self.has_minibar,
            "has_balcony": self.has_balcony,
            "max_occupancy": self.max_occupancy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Widget(Base):
    """
    Widget definitions for overlays and dynamic content

    Attributes:
        id: Primary key
        widget_type: Type of widget
        widget_name: Display name
        data_source_type: internal, external, or mixed
        data_source_id: Foreign key to external_data_sources (if external)
        template: HTML/template for rendering
        styles: JSON styles configuration
        position: Position on screen (top-left, top-right, etc.)
        is_overlay: TRUE: overlay on content, FALSE: in sequence
        refresh_interval: Refresh interval in seconds
        is_active: Whether widget is active
        created_at: Timestamp when widget was created
        updated_at: Timestamp when widget was last updated
    """

    __tablename__ = "widgets"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Widget Info
    widget_type = Column(String(50), nullable=False, index=True)
    widget_name = Column(String(100), nullable=False)

    # Data Source
    data_source_type = Column(String(50), default='internal', nullable=True)  # internal, external, mixed
    data_source_id = Column(Integer, ForeignKey("external_data_sources.id", ondelete="SET NULL"), nullable=True)

    # Rendering
    template = Column(Text, nullable=True)
    styles = Column(JSON, nullable=True)
    position = Column(String(50), default='top-left', nullable=True)

    # Behavior
    is_overlay = Column(Boolean, default=True, nullable=True)  # TRUE: overlay, FALSE: in sequence
    refresh_interval = Column(Integer, default=300, nullable=True)  # seconds

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    data_source = relationship("ExternalDataSource")

    def __repr__(self):
        return f"<Widget(id={self.id}, name='{self.widget_name}', type='{self.widget_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "widget_type": self.widget_type,
            "widget_name": self.widget_name,
            "data_source_type": self.data_source_type,
            "data_source_id": self.data_source_id,
            "template": self.template,
            "styles": self.styles,
            "position": self.position,
            "is_overlay": self.is_overlay,
            "refresh_interval": self.refresh_interval,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DataAccessPolicy(Base):
    """
    RBAC policies for guest data access

    Attributes:
        id: Primary key
        role: Role name (admin, manager, staff, etc.)
        resource_type: Resource type (device_guest_mapping, etc.)
        allowed_fields: JSON array of allowed fields
        denied_fields: JSON array of denied fields
        conditions: JSON conditions for access
        can_read: Whether role can read
        can_write: Whether role can write
        created_at: Timestamp when policy was created
    """

    __tablename__ = "data_access_policies"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Policy Info
    role = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)

    # Access Control
    allowed_fields = Column(JSON, nullable=True)  # JSON array of field names
    denied_fields = Column(JSON, nullable=True)  # JSON array of field names
    conditions = Column(JSON, nullable=True)  # JSON conditions
    can_read = Column(Boolean, default=False, nullable=False)
    can_write = Column(Boolean, default=False, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DataAccessPolicy(id={self.id}, role='{self.role}', resource='{self.resource_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "role": self.role,
            "resource_type": self.resource_type,
            "allowed_fields": self.allowed_fields,
            "denied_fields": self.denied_fields,
            "conditions": self.conditions,
            "can_read": self.can_read,
            "can_write": self.can_write,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DataAccessLog(Base):
    """
    Audit log for PII access (GDPR compliance)

    Attributes:
        id: Primary key
        user_id: User ID who accessed data
        action: Action performed (read, write, delete, etc.)
        resource_type: Resource type accessed
        resource_id: Resource ID accessed
        guest_id: Guest ID (if applicable)
        ip_address: IP address of accessor
        timestamp: Timestamp of access
        retention_days: Auto-delete after this many days
    """

    __tablename__ = "data_access_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Access Info
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True)
    guest_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)

    # Timestamp & Retention
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    retention_days = Column(Integer, default=90, nullable=True)  # Auto-delete after this many days

    def __repr__(self):
        return f"<DataAccessLog(id={self.id}, action='{self.action}', resource='{self.resource_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "guest_id": self.guest_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "retention_days": self.retention_days,
        }
