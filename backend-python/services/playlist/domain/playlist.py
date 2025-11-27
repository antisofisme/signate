"""
Playlist Domain Entity
Pure business logic for playlist management
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone


class Playlist:
    """Playlist entity - pure Python domain object"""

    def __init__(
        self,
        name: str,
        organization_id: int,
        id: Optional[int] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        priority: int = 0,
        schedule: Optional[Dict[str, Any]] = None,
        is_default: bool = False,
        is_pms_template: bool = False,
        created_by_id: Optional[int] = None,
        updated_by_id: Optional[int] = None,
        deleted_by_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
        # Computed fields
        content_count: int = 0,
        total_duration: int = 0,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.is_active = is_active
        self.priority = priority
        self.schedule = schedule or {}
        self.is_default = is_default
        self.is_pms_template = is_pms_template
        self.organization_id = organization_id
        # Audit trail fields
        self.created_by_id = created_by_id
        self.updated_by_id = updated_by_id
        self.deleted_by_id = deleted_by_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at

        # Computed fields (not stored in DB)
        self.content_count = content_count
        self.total_duration = total_duration

        # Validate on creation
        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Playlist name cannot be empty")

        if len(self.name) > 255:
            raise ValueError("Playlist name too long (max 255 characters)")

        if self.priority < 0:
            raise ValueError("Priority cannot be negative")

        if not self.organization_id:
            raise ValueError("Organization ID is required")

    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None,
        schedule: Optional[Dict[str, Any]] = None,
    ):
        """Update playlist details with validation"""
        if name is not None:
            if not name or len(name.strip()) == 0:
                raise ValueError("Playlist name cannot be empty")
            self.name = name

        if description is not None:
            self.description = description

        if is_active is not None:
            self.is_active = is_active

        if priority is not None:
            if priority < 0:
                raise ValueError("Priority cannot be negative")
            self.priority = priority

        if schedule is not None:
            self.schedule = schedule

        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        """Activate playlist"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate playlist"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def soft_delete(self):
        """Soft delete playlist"""
        self.deleted_at = datetime.now(timezone.utc)

    def is_deleted(self) -> bool:
        """Check if playlist is soft deleted"""
        return self.deleted_at is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "priority": self.priority,
            "schedule": self.schedule,
            "organization_id": self.organization_id,
            "created_by": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "content_count": self.content_count,
            "total_duration": self.total_duration,
        }

    def __repr__(self):
        return f"<Playlist(id={self.id}, name='{self.name}', org={self.organization_id}, active={self.is_active})>"


class PlaylistContent:
    """Playlist content item entity"""

    def __init__(
        self,
        playlist_id: int,
        content_id: int,
        order_index: int,
        id: Optional[int] = None,
        duration: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.playlist_id = playlist_id
        self.content_id = content_id
        self.order_index = order_index
        self.duration = duration
        self.created_at = created_at

        self._validate()

    def _validate(self):
        """Validate playlist content item"""
        if self.order_index < 0:
            raise ValueError("Order index cannot be negative")

        if self.duration is not None and self.duration <= 0:
            raise ValueError("Duration must be positive")

    def update_order(self, new_order: int):
        """Update order index"""
        if new_order < 0:
            raise ValueError("Order index cannot be negative")
        self.order_index = new_order

    def update_duration(self, new_duration: Optional[int]):
        """Update duration override"""
        if new_duration is not None and new_duration <= 0:
            raise ValueError("Duration must be positive")
        self.duration = new_duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "content_id": self.content_id,
            "order_index": self.order_index,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<PlaylistContent(id={self.id}, playlist={self.playlist_id}, content={self.content_id}, order={self.order_index})>"


class PlaylistAssignment:
    """Playlist assignment entity (to device or tag)"""

    def __init__(
        self,
        playlist_id: int,
        id: Optional[int] = None,
        device_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.playlist_id = playlist_id
        self.device_id = device_id
        self.tag_id = tag_id
        self.created_at = created_at

        self._validate()

    def _validate(self):
        """Validate assignment (must be device OR tag, not both)"""
        if self.device_id is None and self.tag_id is None:
            raise ValueError("Assignment must have either device_id or tag_id")

        if self.device_id is not None and self.tag_id is not None:
            raise ValueError("Assignment cannot have both device_id and tag_id")

    def is_device_assignment(self) -> bool:
        """Check if this is a device assignment"""
        return self.device_id is not None

    def is_tag_assignment(self) -> bool:
        """Check if this is a tag assignment"""
        return self.tag_id is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "device_id": self.device_id,
            "tag_id": self.tag_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        target = f"device={self.device_id}" if self.device_id else f"tag={self.tag_id}"
        return f"<PlaylistAssignment(id={self.id}, playlist={self.playlist_id}, {target})>"
