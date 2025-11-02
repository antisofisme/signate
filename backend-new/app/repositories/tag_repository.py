"""
Tag Repository - Database Access untuk Tag Entity
==================================================

CENTRALIZED QUERIES untuk tags and device_tags tables
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.tag import Tag, DeviceTag
from app.models.device import Device


class TagRepository(BaseRepository):
    """Tag Repository dengan tag-specific queries"""

    def __init__(self, db: Session):
        super().__init__(Tag, db)
        self.db = db

    # =========================================================================
    # TAG CRUD OPERATIONS
    # =========================================================================

    def create_tag(
        self,
        tag_name: str,
        organization_id: int,
        description: Optional[str] = None,
        color: str = "#3B82F6",
        tag_priority: int = 0,
        created_by: Optional[int] = None
    ) -> Tag:
        """
        Create new tag

        Args:
            tag_name: Tag name (will be lowercased)
            organization_id: Organization ID
            description: Optional description
            color: Hex color code
            tag_priority: Priority (0-100)
            created_by: User ID who created

        Returns:
            Created Tag object
        """
        tag = Tag(
            tag_name=tag_name.lower().strip(),
            description=description,
            color=color,
            tag_priority=tag_priority,
            organization_id=organization_id,
            created_by=created_by
        )
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def get_by_organization(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tag]:
        """Get all tags for an organization"""
        return self.db.query(Tag).filter(
            Tag.organization_id == organization_id
        ).order_by(Tag.tag_priority.desc(), Tag.tag_name).offset(skip).limit(limit).all()

    def get_by_name(
        self,
        tag_name: str,
        organization_id: int
    ) -> Optional[Tag]:
        """Get tag by name (case-insensitive)"""
        return self.db.query(Tag).filter(
            and_(
                Tag.tag_name == tag_name.lower().strip(),
                Tag.organization_id == organization_id
            )
        ).first()

    def search_tags(
        self,
        organization_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Tag]:
        """Search tags by name or description"""
        return self.db.query(Tag).filter(
            and_(
                Tag.organization_id == organization_id,
                or_(
                    Tag.tag_name.ilike(f"%{search_term}%"),
                    Tag.description.ilike(f"%{search_term}%")
                )
            )
        ).offset(skip).limit(limit).all()

    # =========================================================================
    # DEVICE-TAG ASSIGNMENT OPERATIONS
    # =========================================================================

    def assign_tag_to_device(
        self,
        tag_id: int,
        device_id: int
    ) -> DeviceTag:
        """
        Assign tag to device

        Returns:
            DeviceTag object (or existing if already assigned)
        """
        # Check if already assigned
        existing = self.db.query(DeviceTag).filter(
            and_(
                DeviceTag.tag_id == tag_id,
                DeviceTag.device_id == device_id
            )
        ).first()

        if existing:
            return existing

        # Create new assignment
        device_tag = DeviceTag(
            tag_id=tag_id,
            device_id=device_id
        )
        self.db.add(device_tag)
        self.db.commit()
        self.db.refresh(device_tag)
        return device_tag

    def remove_tag_from_device(
        self,
        tag_id: int,
        device_id: int
    ) -> bool:
        """
        Remove tag from device

        Returns:
            True if removed, False if not found
        """
        result = self.db.query(DeviceTag).filter(
            and_(
                DeviceTag.tag_id == tag_id,
                DeviceTag.device_id == device_id
            )
        ).delete()

        self.db.commit()
        return result > 0

    def bulk_assign_tag(
        self,
        tag_id: int,
        device_ids: List[int]
    ) -> int:
        """
        Assign tag to multiple devices

        Returns:
            Number of new assignments created
        """
        count = 0
        for device_id in device_ids:
            # Check if already assigned
            existing = self.db.query(DeviceTag).filter(
                and_(
                    DeviceTag.tag_id == tag_id,
                    DeviceTag.device_id == device_id
                )
            ).first()

            if not existing:
                device_tag = DeviceTag(
                    tag_id=tag_id,
                    device_id=device_id
                )
                self.db.add(device_tag)
                count += 1

        self.db.commit()
        return count

    def get_device_tags(self, device_id: int) -> List[Tag]:
        """Get all tags assigned to a device"""
        return self.db.query(Tag).join(DeviceTag).filter(
            DeviceTag.device_id == device_id
        ).order_by(Tag.tag_priority.desc()).all()

    def get_tag_devices(self, tag_id: int) -> List[Device]:
        """Get all devices with a specific tag"""
        return self.db.query(Device).join(DeviceTag).filter(
            DeviceTag.tag_id == tag_id
        ).all()

    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================

    def get_tag_with_device_count(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """Get tag with device count"""
        tag = self.get(tag_id)
        if not tag:
            return None

        device_count = self.db.query(func.count(DeviceTag.device_id)).filter(
            DeviceTag.tag_id == tag_id
        ).scalar() or 0

        tag_dict = tag.to_dict()
        tag_dict["device_count"] = device_count
        return tag_dict

    def get_organization_tags_with_counts(
        self,
        organization_id: int
    ) -> List[Dict[str, Any]]:
        """Get all tags with device counts for an organization"""
        # Query tags with device count
        query = self.db.query(
            Tag,
            func.count(DeviceTag.device_id).label("device_count")
        ).outerjoin(
            DeviceTag, Tag.id == DeviceTag.tag_id
        ).filter(
            Tag.organization_id == organization_id
        ).group_by(Tag.id).order_by(
            Tag.tag_priority.desc(),
            Tag.tag_name
        )

        results = []
        for tag, device_count in query.all():
            tag_dict = tag.to_dict()
            tag_dict["device_count"] = device_count or 0
            results.append(tag_dict)

        return results

    def get_tag_statistics(self, organization_id: int) -> Dict[str, Any]:
        """Get tag statistics for organization"""
        # Total tags
        total_tags = self.db.query(func.count(Tag.id)).filter(
            Tag.organization_id == organization_id
        ).scalar() or 0

        # Total assignments
        total_assignments = self.db.query(func.count(DeviceTag.device_id)).join(
            Tag, Tag.id == DeviceTag.tag_id
        ).filter(
            Tag.organization_id == organization_id
        ).scalar() or 0

        # Most used tags (top 5)
        most_used = self.db.query(
            Tag.tag_name,
            func.count(DeviceTag.device_id).label("device_count")
        ).join(
            DeviceTag, Tag.id == DeviceTag.tag_id
        ).filter(
            Tag.organization_id == organization_id
        ).group_by(Tag.id).order_by(
            func.count(DeviceTag.device_id).desc()
        ).limit(5).all()

        most_used_tags = [
            {"tag_name": tag_name, "device_count": count}
            for tag_name, count in most_used
        ]

        # Devices without tags
        total_devices = self.db.query(func.count(Device.id)).filter(
            Device.organization_id == organization_id,
            Device.is_active == True
        ).scalar() or 0

        devices_with_tags = self.db.query(
            func.count(func.distinct(DeviceTag.device_id))
        ).join(
            Device, Device.id == DeviceTag.device_id
        ).filter(
            Device.organization_id == organization_id,
            Device.is_active == True
        ).scalar() or 0

        unassigned_devices = total_devices - devices_with_tags

        return {
            "total_tags": total_tags,
            "total_assignments": total_assignments,
            "most_used_tags": most_used_tags,
            "unassigned_devices": max(0, unassigned_devices)
        }

    def count_by_organization(self, organization_id: int) -> int:
        """Count tags in organization"""
        return self.db.query(func.count(Tag.id)).filter(
            Tag.organization_id == organization_id
        ).scalar() or 0
