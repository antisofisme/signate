"""
SQLAlchemy Database Models
All database models for Smart TV Digital Signage
"""

from app.models.user import User
from app.models.organization import Organization
from app.models.role import Role
from app.models.user_organization import UserOrganization
from app.models.device import Device
from app.models.content import Content
from app.models.tag import Tag, DeviceTag
from app.models.assignment import ContentAssignment
from app.models.schedule import Schedule
from app.models.firebird import FirebirdConfig
from app.models.device_log import DeviceLog
from app.models.device_command import DeviceCommand
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
from app.models.activity_log import ActivityLog, ActivityAction, EntityType
from app.models.speed_test import DeviceSpeedTest, SpeedTestQuality
from app.models.hotel import (
    ExternalDataSource,
    DeviceGuestMapping,
    RoomConfiguration,
    Widget,
    DataAccessPolicy,
    DataAccessLog,
)

__all__ = [
    "User",
    "Organization",
    "Role",
    "UserOrganization",
    "Device",
    "Content",
    "Tag",
    "DeviceTag",
    "ContentAssignment",
    "Schedule",
    "FirebirdConfig",
    "DeviceLog",
    "DeviceCommand",
    "Playlist",
    "PlaylistContent",
    "PlaylistAssignment",
    # Activity Logs
    "ActivityLog",
    "ActivityAction",
    "EntityType",
    # Speed Tests
    "DeviceSpeedTest",
    "SpeedTestQuality",
    # Hotel Integration Models
    "ExternalDataSource",
    "DeviceGuestMapping",
    "RoomConfiguration",
    "Widget",
    "DataAccessPolicy",
    "DataAccessLog",
]
