"""
Repositories Package - Centralized Database Access
==================================================

EXPORTS semua repositories untuk easy import

Usage:
    from app.repositories import DeviceRepository, ContentRepository

    device_repo = DeviceRepository(db)
    devices = device_repo.get_all()
"""

from app.repositories.base import BaseRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.command_repository import CommandRepository

__all__ = [
    "BaseRepository",
    "DeviceRepository",
    "ContentRepository",
    "OrganizationRepository",
    "PlaylistRepository",
    "UserRepository",
    "ActivityRepository",
    "TagRepository",
    "CommandRepository",
]
