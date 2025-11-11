"""
PMS Integration Models
SQLAlchemy models for Firebird PMS integration
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint, Numeric, Text
from sqlalchemy.sql import func
from shared.database import Base


class PMSGuest(Base):
    """Guest data synced from PMS"""

    __tablename__ = "pms_guests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Guest Information
    guest_name = Column(String(255), nullable=False)
    title = Column(String(50))  # Mr., Mrs., Ms., Dr., etc.
    room_number = Column(String(50), nullable=False)
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    country = Column(String(100))
    reservation_no = Column(String(100))
    
    # Additional fields for template processing
    balance = Column(Numeric(10, 2), default=0)
    loyalty_level = Column(String(50))  # Gold, Silver, Bronze, etc.
    language = Column(String(10))  # en, id, zh, etc.
    special_requests = Column(Text)

    # Sync Metadata
    synced_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.guest_name,  # For consistency with API
            "guest_name": self.guest_name,
            "title": self.title,
            "room_number": self.room_number,
            "check_in_date": self.checkin_date.isoformat() if self.checkin_date else None,
            "check_out_date": self.checkout_date.isoformat() if self.checkout_date else None,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "reservation_no": self.reservation_no,
            "balance": float(self.balance) if self.balance else 0,
            "loyalty_level": self.loyalty_level,
            "language": self.language,
            "special_requests": self.special_requests,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class PMSRoom(Base):
    """Room status synced from PMS"""

    __tablename__ = "pms_rooms"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Room Information
    room_number = Column(String(50), nullable=False)
    room_type = Column(String(100))
    status = Column(String(50), nullable=False)  # available, occupied, cleaning, maintenance
    floor = Column(String(20))
    bed_type = Column(String(50))
    max_occupancy = Column(Integer)

    # Sync Metadata
    synced_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'room_number', name='uq_pms_rooms_org_room'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "room_number": self.room_number,
            "room_type": self.room_type,
            "status": self.status,
            "floor": self.floor,
            "bed_type": self.bed_type,
            "max_occupancy": self.max_occupancy,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class PMSConfiguration(Base):
    """PMS integration configuration per organization"""

    __tablename__ = "pms_configurations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)

    # API Key for Bridge Agent authentication
    api_key = Column(String(255), unique=True, nullable=False)

    # Configuration
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_interval_minutes = Column(Integer, default=5)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "api_key": self.api_key,
            "is_active": self.is_active,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_interval_minutes": self.sync_interval_minutes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
