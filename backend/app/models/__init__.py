"""
SQLAlchemy Database Models
All database models for Smart TV Digital Signage
"""

from app.models.user import User
from app.models.device import Device
from app.models.content import Content
from app.models.tag import Tag, DeviceTag
from app.models.assignment import ContentAssignment
from app.models.schedule import Schedule
from app.models.firebird import FirebirdConfig
from app.models.device_log import DeviceLog
from app.models.device_command import DeviceCommand
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
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
    # Hotel Integration Models
    "ExternalDataSource",
    "DeviceGuestMapping",
    "RoomConfiguration",
    "Widget",
    "DataAccessPolicy",
    "DataAccessLog",
]
