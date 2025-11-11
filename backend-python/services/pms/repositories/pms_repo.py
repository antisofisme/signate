"""
PMS Repository
Data access layer for PMS integration
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date

from .models import PMSGuest, PMSRoom, PMSConfiguration


class PMSRepository:
    """Repository for PMS data access"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Guest Methods
    # ========================================================================

    def create_guest(self, guest_data: dict) -> PMSGuest:
        """Create guest record"""
        guest = PMSGuest(**guest_data)
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def get_guests_by_organization(
        self, organization_id: int, limit: int = 100, offset: int = 0
    ) -> List[PMSGuest]:
        """Get guests for organization"""
        return (
            self.db.query(PMSGuest)
            .filter(PMSGuest.organization_id == organization_id)
            .order_by(PMSGuest.checkin_date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_current_guests(self, organization_id: int) -> List[PMSGuest]:
        """Get currently checked-in guests"""
        now = datetime.now()
        return (
            self.db.query(PMSGuest)
            .filter(
                and_(
                    PMSGuest.organization_id == organization_id,
                    PMSGuest.checkin_date <= now,
                    PMSGuest.checkout_date >= now,
                )
            )
            .all()
        )

    def get_checkins_today(self, organization_id: int) -> List[PMSGuest]:
        """Get today's check-ins"""
        today = date.today()
        return (
            self.db.query(PMSGuest)
            .filter(
                and_(
                    PMSGuest.organization_id == organization_id,
                    func.date(PMSGuest.checkin_date) == today,
                )
            )
            .all()
        )

    def get_checkouts_today(self, organization_id: int) -> List[PMSGuest]:
        """Get today's check-outs"""
        today = date.today()
        return (
            self.db.query(PMSGuest)
            .filter(
                and_(
                    PMSGuest.organization_id == organization_id,
                    func.date(PMSGuest.checkout_date) == today,
                )
            )
            .all()
        )

    # ========================================================================
    # Room Methods
    # ========================================================================

    def upsert_room(self, room_data: dict) -> PMSRoom:
        """Create or update room record"""
        existing = (
            self.db.query(PMSRoom)
            .filter(
                and_(
                    PMSRoom.organization_id == room_data["organization_id"],
                    PMSRoom.room_number == room_data["room_number"],
                )
            )
            .first()
        )

        if existing:
            # Update existing
            for key, value in room_data.items():
                setattr(existing, key, value)
            existing.synced_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new
            room = PMSRoom(**room_data)
            self.db.add(room)
            self.db.commit()
            self.db.refresh(room)
            return room

    def get_rooms_by_organization(self, organization_id: int) -> List[PMSRoom]:
        """Get all rooms for organization"""
        return (
            self.db.query(PMSRoom)
            .filter(PMSRoom.organization_id == organization_id)
            .order_by(PMSRoom.room_number)
            .all()
        )

    def get_rooms_by_status(self, organization_id: int, status: str) -> List[PMSRoom]:
        """Get rooms by status"""
        return (
            self.db.query(PMSRoom)
            .filter(
                and_(
                    PMSRoom.organization_id == organization_id,
                    PMSRoom.status == status,
                )
            )
            .all()
        )

    def get_room_stats(self, organization_id: int) -> dict:
        """Get room statistics"""
        total = self.db.query(func.count(PMSRoom.id)).filter(
            PMSRoom.organization_id == organization_id
        ).scalar()

        occupied = self.db.query(func.count(PMSRoom.id)).filter(
            and_(
                PMSRoom.organization_id == organization_id,
                PMSRoom.status == "occupied",
            )
        ).scalar()

        available = self.db.query(func.count(PMSRoom.id)).filter(
            and_(
                PMSRoom.organization_id == organization_id,
                PMSRoom.status == "available",
            )
        ).scalar()

        return {
            "total_rooms": total or 0,
            "occupied_rooms": occupied or 0,
            "available_rooms": available or 0,
        }

    # ========================================================================
    # Configuration Methods
    # ========================================================================

    def create_config(self, config_data: dict) -> PMSConfiguration:
        """Create PMS configuration"""
        config = PMSConfiguration(**config_data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_config_by_organization(self, organization_id: int) -> Optional[PMSConfiguration]:
        """Get PMS configuration for organization"""
        return (
            self.db.query(PMSConfiguration)
            .filter(PMSConfiguration.organization_id == organization_id)
            .first()
        )

    def get_config_by_api_key(self, api_key: str) -> Optional[PMSConfiguration]:
        """Get configuration by API key"""
        return (
            self.db.query(PMSConfiguration)
            .filter(PMSConfiguration.api_key == api_key)
            .first()
        )

    def update_config(self, config_id: int, updates: dict) -> PMSConfiguration:
        """Update configuration"""
        config = self.db.query(PMSConfiguration).filter(PMSConfiguration.id == config_id).first()
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        for key, value in updates.items():
            if value is not None:
                setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def update_last_sync(self, organization_id: int) -> None:
        """Update last sync timestamp"""
        config = self.get_config_by_organization(organization_id)
        if config:
            config.last_sync = datetime.now()
            self.db.commit()
