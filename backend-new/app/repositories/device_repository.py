"""
Device Repository - Database Access untuk Device Entity
========================================================

CENTRALIZED QUERIES untuk devices table
Semua query device WAJIB melalui repository ini
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.device import Device


class DeviceRepository(BaseRepository):
    """
    Device Repository dengan business-specific queries

    Extends BaseRepository untuk CRUD dasar +
    custom queries khusus untuk Device
    """

    def __init__(self, db: Session):
        super().__init__(Device, db)
        self.db = db

    # =========================================================================
    # DEVICE-SPECIFIC QUERIES
    # =========================================================================

    def get_by_device_id(self, device_id: str) -> Optional[Any]:
        """
        Get device by unique device_id (bukan primary key id)

        Example:
            device = device_repo.get_by_device_id("abc123xyz")
        """
        return self.get_by_field("device_id", device_id)

    def get_by_organization(
        self,
        organization_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Get all devices untuk organization tertentu

        Example:
            # All devices
            devices = device_repo.get_by_organization(org_id=1)

            # Only active devices
            active_devices = device_repo.get_by_organization(
                org_id=1,
                status="active"
            )

            # With custom filters
            approved = device_repo.get_by_organization(
                org_id=1,
                filters={"is_approved": True, "device_type": "screen"}
            )
        """
        query_filters = filters or {}
        query_filters["organization_id"] = organization_id

        if status:
            query_filters["status"] = status

        # Build query with filters
        query = self.db.query(self.model)
        for key, value in query_filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        # Order by created_at DESC
        query = query.order_by(self.model.created_at.desc())

        return query.offset(skip).limit(limit).all()

    def get_online_devices(self, organization_id: int) -> List[Any]:
        """
        Get devices yang online (last_seen < 5 menit yang lalu)

        Business rule: Device dianggap online jika heartbeat < 5 menit
        """
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.last_seen >= five_minutes_ago,
                self.model.status == "active"
            )
        )
        return query.all()

    def get_offline_devices(self, organization_id: int) -> List[Any]:
        """Get devices yang offline (last_seen > 5 menit)"""
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                or_(
                    self.model.last_seen < five_minutes_ago,
                    self.model.last_seen.is_(None)
                ),
                self.model.status == "active"
            )
        )
        return query.all()

    def update_heartbeat(self, device_id: str) -> bool:
        """
        Update last_seen timestamp (device heartbeat)

        Called setiap kali device mengirim heartbeat
        """
        device = self.get_by_device_id(device_id)
        if not device:
            return False

        device.last_seen = datetime.utcnow()
        self.db.commit()
        return True

    def get_devices_by_tags(
        self,
        organization_id: int,
        tag_ids: List[int]
    ) -> List[Any]:
        """
        Get devices yang punya tag tertentu

        Example:
            # Get devices dengan tag "lobby" atau "reception"
            devices = device_repo.get_devices_by_tags(
                org_id=1,
                tag_ids=[1, 2]
            )
        """
        from app.models.device_tag import DeviceTag

        query = self.db.query(self.model).join(DeviceTag).filter(
            and_(
                self.model.organization_id == organization_id,
                DeviceTag.tag_id.in_(tag_ids)
            )
        ).distinct()

        return query.all()

    def count_by_organization(
        self,
        organization_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count devices by organization with filters

        Example:
            # Count all devices
            total = device_repo.count_by_organization(org_id=1)

            # Count approved devices
            approved = device_repo.count_by_organization(
                org_id=1,
                filters={"is_approved": True}
            )
        """
        query_filters = filters or {}
        query_filters["organization_id"] = organization_id

        query = self.db.query(func.count(self.model.id))
        for key, value in query_filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.scalar() or 0

    def get_device_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get statistik devices untuk dashboard

        Returns:
            {
                "total": 100,
                "online": 85,
                "offline": 15,
                "active": 90,
                "inactive": 10,
                "approved": 95,
                "pending": 5,
                "by_type": {"screen": 80, "tv": 20}
            }
        """
        total = self.count({"organization_id": organization_id})
        online = len(self.get_online_devices(organization_id))

        active_count = self.count({
            "organization_id": organization_id,
            "is_active": True
        })

        approved_count = self.count({
            "organization_id": organization_id,
            "is_approved": True
        })

        # Count by device type
        type_stats = self.db.query(
            self.model.device_type,
            func.count(self.model.id)
        ).filter(
            self.model.organization_id == organization_id
        ).group_by(self.model.device_type).all()

        by_type = {t: c for t, c in type_stats}

        return {
            "total": total,
            "online": online,
            "offline": total - online,
            "active": active_count,
            "inactive": total - active_count,
            "approved": approved_count,
            "pending": total - approved_count,
            "by_type": by_type
        }

    def search_devices(
        self,
        organization_id: int,
        search_term: str
    ) -> List[Any]:
        """
        Search devices by name, device_id, or location

        Example:
            results = device_repo.search_devices(1, "lobby")
        """
        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                or_(
                    self.model.name.ilike(f"%{search_term}%"),
                    self.model.device_id.ilike(f"%{search_term}%"),
                    self.model.location.ilike(f"%{search_term}%")
                )
            )
        )
        return query.all()

    def activate_device(self, device_id: str, activation_code: str) -> Optional[Any]:
        """
        Aktivasi device dengan activation code

        Business logic untuk device registration
        """
        device = self.get_by_field("activation_code", activation_code)
        if not device:
            return None

        # Update status dan device_id
        device.device_id = device_id
        device.status = "active"
        device.activated_at = datetime.utcnow()
        device.last_seen = datetime.utcnow()

        self.db.commit()
        self.db.refresh(device)
        return device

    def deactivate_device(self, id: int) -> bool:
        """Set device status ke inactive"""
        return self.update(id, {
            "status": "inactive",
            "deactivated_at": datetime.utcnow()
        }) is not None

    def get_devices_needing_update(self, organization_id: int) -> List[Any]:
        """
        Get devices yang perlu update firmware/software

        Business rule: Cek version number vs latest version
        """
        # TODO: Implement version checking logic
        # Query devices where firmware_version < latest_version
        pass
