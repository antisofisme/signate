"""
Data models for transformation between Firebird and Cloud formats
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class GuestData:
    """Guest check-in data model"""
    organization_id: int
    guest_name: str
    room_number: str
    checkin_date: str
    checkout_date: str
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    reservation_no: Optional[str] = None

    @classmethod
    def from_firebird(cls, fb_data: Dict[str, Any], org_id: int):
        """Transform Firebird row to GuestData"""
        return cls(
            organization_id=org_id,
            guest_name=fb_data.get('GUEST_NAME', ''),
            room_number=fb_data.get('ROOM_NO', ''),
            checkin_date=fb_data.get('CHECKIN_DATE').isoformat() if fb_data.get('CHECKIN_DATE') else None,
            checkout_date=fb_data.get('CHECKOUT_DATE').isoformat() if fb_data.get('CHECKOUT_DATE') else None,
            email=fb_data.get('GUEST_EMAIL'),
            phone=fb_data.get('GUEST_PHONE'),
            country=fb_data.get('GUEST_COUNTRY'),
            reservation_no=fb_data.get('RESERVATION_NO')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class RoomStatus:
    """Room status data model"""
    organization_id: int
    room_number: str
    room_type: str
    status: str
    floor: Optional[str] = None
    bed_type: Optional[str] = None
    max_occupancy: Optional[int] = None

    @classmethod
    def from_firebird(cls, fb_data: Dict[str, Any], org_id: int):
        """Transform Firebird row to RoomStatus"""
        return cls(
            organization_id=org_id,
            room_number=fb_data.get('ROOM_NO', ''),
            room_type=fb_data.get('ROOM_TYPE', ''),
            status=fb_data.get('STATUS', ''),
            floor=fb_data.get('FLOOR'),
            bed_type=fb_data.get('BED_TYPE'),
            max_occupancy=fb_data.get('MAX_OCCUPANCY')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
