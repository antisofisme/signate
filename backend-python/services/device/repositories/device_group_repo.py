"""
Device Group Repository
Data access layer for device groups
"""

from typing import List, Optional
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import Session

from services.device.domain.device_group import DeviceGroup, DeviceGroupMember
from services.device.repositories.models import (
    DeviceGroupModel,
    DeviceGroupMemberModel,
    DeviceModel,
)


class DeviceGroupRepository:
    """Repository for device group operations"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(self, group: DeviceGroup) -> DeviceGroup:
        """Create a new device group"""
        db_group = DeviceGroupModel(
            name=group.name,
            description=group.description,
            parent_group_id=group.parent_group_id,
            organization_id=group.organization_id,
            group_type=group.group_type,
            sort_order=group.sort_order,
            default_playlist_id=group.default_playlist_id,
            created_by_id=group.created_by_id,
        )

        self.db.add(db_group)
        self.db.commit()
        self.db.refresh(db_group)

        return self._to_domain(db_group)

    def add_device_to_group(
        self, device_id: int, group_id: int, added_by_id: Optional[int] = None
    ) -> DeviceGroupMember:
        """Add a device to a group"""
        db_member = DeviceGroupMemberModel(
            device_id=device_id, group_id=group_id, added_by_id=added_by_id
        )

        self.db.add(db_member)
        self.db.commit()
        self.db.refresh(db_member)

        return self._member_to_domain(db_member)

    # ========================================================================
    # READ
    # ========================================================================

    def get_by_id(self, group_id: int) -> Optional[DeviceGroup]:
        """Get group by ID"""
        stmt = (
            select(DeviceGroupModel)
            .where(DeviceGroupModel.id == group_id)
            .where(DeviceGroupModel.deleted_at.is_(None))
        )

        result = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(result) if result else None

    def get_by_organization(
        self, organization_id: int, include_deleted: bool = False
    ) -> List[DeviceGroup]:
        """Get all groups for an organization"""
        stmt = select(DeviceGroupModel).where(
            DeviceGroupModel.organization_id == organization_id
        )

        if not include_deleted:
            stmt = stmt.where(DeviceGroupModel.deleted_at.is_(None))

        stmt = stmt.order_by(DeviceGroupModel.sort_order, DeviceGroupModel.name)

        results = self.db.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def get_children(self, parent_group_id: int) -> List[DeviceGroup]:
        """Get child groups of a parent group"""
        stmt = (
            select(DeviceGroupModel)
            .where(DeviceGroupModel.parent_group_id == parent_group_id)
            .where(DeviceGroupModel.deleted_at.is_(None))
            .order_by(DeviceGroupModel.sort_order, DeviceGroupModel.name)
        )

        results = self.db.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def get_root_groups(self, organization_id: int) -> List[DeviceGroup]:
        """Get root groups (no parent) for an organization"""
        stmt = (
            select(DeviceGroupModel)
            .where(DeviceGroupModel.organization_id == organization_id)
            .where(DeviceGroupModel.parent_group_id.is_(None))
            .where(DeviceGroupModel.deleted_at.is_(None))
            .order_by(DeviceGroupModel.sort_order, DeviceGroupModel.name)
        )

        results = self.db.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def get_devices_in_group(self, group_id: int) -> List[int]:
        """Get device IDs in a group (direct members only)"""
        stmt = select(DeviceGroupMemberModel.device_id).where(
            DeviceGroupMemberModel.group_id == group_id
        )

        results = self.db.execute(stmt).scalars().all()
        return list(results)

    def get_devices_in_group_recursive(self, group_id: int) -> List[int]:
        """Get device IDs in a group and all child groups"""
        # Use SQL function from migration
        stmt = text("SELECT device_id FROM get_devices_in_group(:group_id)")
        results = self.db.execute(stmt, {"group_id": group_id}).scalars().all()
        return list(results)

    def get_group_stats(self, group_id: int) -> dict:
        """Get group statistics (device count, online/offline)"""
        # Count devices
        device_count_stmt = (
            select(func.count(DeviceGroupMemberModel.device_id))
            .where(DeviceGroupMemberModel.group_id == group_id)
        )
        device_count = self.db.execute(device_count_stmt).scalar() or 0

        # Count online devices
        online_count_stmt = (
            select(func.count(DeviceGroupMemberModel.device_id))
            .select_from(DeviceGroupMemberModel)
            .join(DeviceModel, DeviceModel.id == DeviceGroupMemberModel.device_id)
            .where(DeviceGroupMemberModel.group_id == group_id)
            .where(DeviceModel.status == "active")
        )
        online_count = self.db.execute(online_count_stmt).scalar() or 0

        return {
            "total_devices": device_count,
            "online_devices": online_count,
            "offline_devices": device_count - online_count,
        }

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update(self, group: DeviceGroup, updated_by_id: Optional[int] = None) -> DeviceGroup:
        """Update a device group"""
        stmt = (
            select(DeviceGroupModel)
            .where(DeviceGroupModel.id == group.id)
            .where(DeviceGroupModel.deleted_at.is_(None))
        )

        db_group = self.db.execute(stmt).scalar_one_or_none()

        if not db_group:
            raise ValueError(f"Group {group.id} not found")

        # Update fields
        if group.name:
            db_group.name = group.name
        if group.description is not None:
            db_group.description = group.description
        if group.parent_group_id is not None:
            db_group.parent_group_id = group.parent_group_id
        if group.group_type is not None:
            db_group.group_type = group.group_type
        if group.sort_order is not None:
            db_group.sort_order = group.sort_order
        if group.default_playlist_id is not None:
            db_group.default_playlist_id = group.default_playlist_id

        # Track who updated
        if updated_by_id is not None:
            db_group.updated_by_id = updated_by_id

        self.db.commit()
        self.db.refresh(db_group)

        return self._to_domain(db_group)

    # ========================================================================
    # DELETE
    # ========================================================================

    def soft_delete(self, group_id: int, deleted_by_id: Optional[int] = None) -> bool:
        """Soft delete a group"""
        from datetime import datetime, timezone

        stmt = (
            select(DeviceGroupModel)
            .where(DeviceGroupModel.id == group_id)
            .where(DeviceGroupModel.deleted_at.is_(None))
        )

        db_group = self.db.execute(stmt).scalar_one_or_none()

        if not db_group:
            return False

        db_group.deleted_at = datetime.now(timezone.utc)
        if deleted_by_id is not None:
            db_group.deleted_by_id = deleted_by_id
        self.db.commit()

        return True

    def remove_device_from_group(self, device_id: int, group_id: int) -> bool:
        """Remove a device from a group"""
        stmt = select(DeviceGroupMemberModel).where(
            and_(
                DeviceGroupMemberModel.device_id == device_id,
                DeviceGroupMemberModel.group_id == group_id,
            )
        )

        db_member = self.db.execute(stmt).scalar_one_or_none()

        if not db_member:
            return False

        self.db.delete(db_member)
        self.db.commit()

        return True

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _to_domain(self, db_group: DeviceGroupModel) -> DeviceGroup:
        """Convert SQLAlchemy model to domain entity"""
        return DeviceGroup(
            id=db_group.id,
            name=db_group.name,
            description=db_group.description,
            parent_group_id=db_group.parent_group_id,
            organization_id=db_group.organization_id,
            group_type=db_group.group_type,
            sort_order=db_group.sort_order,
            default_playlist_id=db_group.default_playlist_id,
            deleted_at=db_group.deleted_at,
            created_by=db_group.created_by_id,
            updated_by_id=getattr(db_group, 'updated_by_id', None),
            deleted_by_id=getattr(db_group, 'deleted_by_id', None),
            created_at=db_group.created_at,
            updated_at=db_group.updated_at,
        )

    def _member_to_domain(
        self, db_member: DeviceGroupMemberModel
    ) -> DeviceGroupMember:
        """Convert SQLAlchemy model to domain entity"""
        return DeviceGroupMember(
            id=db_member.id,
            device_id=db_member.device_id,
            group_id=db_member.group_id,
            joined_at=db_member.joined_at,
            added_by=db_member.added_by_id,
        )
