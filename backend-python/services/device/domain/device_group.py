"""
Device Group Domain Model
Domain entity for hierarchical device grouping
"""

from datetime import datetime
from typing import Optional, List


class DeviceGroup:
    """
    Device Group Domain Entity
    Represents a hierarchical group of devices for bulk management
    """

    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        description: Optional[str] = None,
        parent_group_id: Optional[int] = None,
        organization_id: int = 0,
        group_type: Optional[str] = None,
        sort_order: int = 0,
        default_playlist_id: Optional[int] = None,
        deleted_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
        updated_by_id: Optional[int] = None,
        deleted_by_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        # Computed fields
        device_count: int = 0,
        parent_name: Optional[str] = None,
        full_path: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.parent_group_id = parent_group_id
        self.organization_id = organization_id
        self.group_type = group_type
        self.sort_order = sort_order
        self.default_playlist_id = default_playlist_id
        self.deleted_at = deleted_at
        self.created_by_id = created_by
        self.updated_by_id = updated_by_id
        self.deleted_by_id = deleted_by_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.device_count = device_count
        self.parent_name = parent_name
        self.full_path = full_path

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_group_id": self.parent_group_id,
            "organization_id": self.organization_id,
            "group_type": self.group_type,
            "sort_order": self.sort_order,
            "default_playlist_id": self.default_playlist_id,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_by": self.created_by_id,
            "updated_by": self.updated_by_id,
            "deleted_by": self.deleted_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "device_count": self.device_count,
            "parent_name": self.parent_name,
            "full_path": self.full_path,
        }

    def is_deleted(self) -> bool:
        """Check if group is soft deleted"""
        return self.deleted_at is not None

    def is_root_group(self) -> bool:
        """Check if this is a root group (no parent)"""
        return self.parent_group_id is None

    def __repr__(self):
        return f"<DeviceGroup {self.id}: {self.name} (org={self.organization_id})>"


class DeviceGroupMember:
    """
    Device Group Member Domain Entity
    Represents membership of a device in a group
    """

    def __init__(
        self,
        id: Optional[int] = None,
        device_id: int = 0,
        group_id: int = 0,
        joined_at: Optional[datetime] = None,
        added_by: Optional[int] = None,
        # Computed fields
        device_name: Optional[str] = None,
        group_name: Optional[str] = None,
    ):
        self.id = id
        self.device_id = device_id
        self.group_id = group_id
        self.joined_at = joined_at
        self.added_by_id = added_by
        self.device_name = device_name
        self.group_name = group_name

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "group_id": self.group_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "added_by": self.added_by_id,
            "device_name": self.device_name,
            "group_name": self.group_name,
        }

    def __repr__(self):
        return f"<DeviceGroupMember device={self.device_id} in group={self.group_id}>"
