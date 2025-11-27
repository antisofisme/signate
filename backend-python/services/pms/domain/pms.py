"""
PMS Domain Entities
Pure business logic for Property Management System integration
"""

from typing import Optional
from datetime import datetime, date, timezone


class PMSConfig:
    """PMS Configuration entity - pure Python domain object"""

    def __init__(
        self,
        organization_id: int,
        api_key: str,
        id: Optional[int] = None,
        is_active: bool = True,
        sync_interval_minutes: int = 5,
        last_synced_at: Optional[datetime] = None,
        created_by_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.organization_id = organization_id
        self.api_key = api_key
        self.is_active = is_active
        self.sync_interval_minutes = sync_interval_minutes
        self.last_synced_at = last_synced_at
        self.created_by_id = created_by_id
        self.created_at = created_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.organization_id:
            raise ValueError("Organization ID is required")

        if not self.api_key or len(self.api_key.strip()) == 0:
            raise ValueError("API key is required")

        if self.sync_interval_minutes < 1 or self.sync_interval_minutes > 60:
            raise ValueError("Sync interval must be between 1 and 60 minutes")

    def activate(self):
        """Activate PMS integration"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate PMS integration"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_sync_interval(self, minutes: int):
        """Update sync interval with validation"""
        if minutes < 1 or minutes > 60:
            raise ValueError("Sync interval must be between 1 and 60 minutes")
        self.sync_interval_minutes = minutes
        self.updated_at = datetime.now(timezone.utc)

    def mark_synced(self):
        """Mark as synced with current timestamp"""
        self.last_synced_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def needs_sync(self) -> bool:
        """Check if sync is needed based on interval"""
        if not self.is_active:
            return False

        if not self.last_synced_at:
            return True

        now = datetime.now(timezone.utc)
        elapsed_minutes = (now - self.last_synced_at).total_seconds() / 60
        return elapsed_minutes >= self.sync_interval_minutes

    def __repr__(self):
        return f"<PMSConfig(id={self.id}, org={self.organization_id}, active={self.is_active})>"


class Guest:
    """Guest entity - pure Python domain object"""

    def __init__(
        self,
        organization_id: int,
        guest_name: str,
        room_number: str,
        checkin_date: date,
        checkout_date: date,
        id: Optional[int] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        country: Optional[str] = None,
        reservation_no: Optional[str] = None,
        synced_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.organization_id = organization_id
        self.guest_name = guest_name
        self.room_number = room_number
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
        self.email = email
        self.phone = phone
        self.country = country
        self.reservation_no = reservation_no
        self.synced_at = synced_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.organization_id:
            raise ValueError("Organization ID is required")

        if not self.guest_name or len(self.guest_name.strip()) == 0:
            raise ValueError("Guest name is required")

        if not self.room_number or len(self.room_number.strip()) == 0:
            raise ValueError("Room number is required")

        if not self.checkin_date or not self.checkout_date:
            raise ValueError("Check-in and check-out dates are required")

        if self.checkout_date < self.checkin_date:
            raise ValueError("Check-out date cannot be before check-in date")

    def is_checked_in(self) -> bool:
        """Check if guest is currently checked in"""
        today = date.today()
        return self.checkin_date <= today <= self.checkout_date

    def is_checking_out_today(self) -> bool:
        """Check if guest is checking out today"""
        return self.checkout_date == date.today()

    def is_checking_in_today(self) -> bool:
        """Check if guest is checking in today"""
        return self.checkin_date == date.today()

    def days_remaining(self) -> int:
        """Get number of days remaining in stay"""
        today = date.today()
        if today > self.checkout_date:
            return 0
        return (self.checkout_date - today).days

    def mark_synced(self):
        """Mark as synced with current timestamp"""
        self.synced_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Guest(id={self.id}, name='{self.guest_name}', room={self.room_number})>"


class Room:
    """Room entity - pure Python domain object"""

    VALID_STATUSES = ["available", "occupied", "cleaning", "maintenance"]

    def __init__(
        self,
        organization_id: int,
        room_number: str,
        status: str,
        id: Optional[int] = None,
        room_type: Optional[str] = None,
        floor: Optional[str] = None,
        bed_type: Optional[str] = None,
        max_occupancy: Optional[int] = None,
        synced_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.organization_id = organization_id
        self.room_number = room_number
        self.status = status
        self.room_type = room_type
        self.floor = floor
        self.bed_type = bed_type
        self.max_occupancy = max_occupancy
        self.synced_at = synced_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.organization_id:
            raise ValueError("Organization ID is required")

        if not self.room_number or len(self.room_number.strip()) == 0:
            raise ValueError("Room number is required")

        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")

        if self.max_occupancy is not None and self.max_occupancy < 1:
            raise ValueError("Max occupancy must be at least 1")

    def is_available(self) -> bool:
        """Check if room is available"""
        return self.status == "available"

    def is_occupied(self) -> bool:
        """Check if room is occupied"""
        return self.status == "occupied"

    def needs_cleaning(self) -> bool:
        """Check if room needs cleaning"""
        return self.status == "cleaning"

    def under_maintenance(self) -> bool:
        """Check if room is under maintenance"""
        return self.status == "maintenance"

    def update_status(self, new_status: str):
        """Update room status with validation"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def mark_synced(self):
        """Mark as synced with current timestamp"""
        self.synced_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Room(id={self.id}, number={self.room_number}, status={self.status})>"
