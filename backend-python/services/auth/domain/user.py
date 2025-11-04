"""
User Entity - Domain Model
Pure business object, no framework dependencies
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain entity"""
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    full_name: str
    role: str
    organization_id: Optional[int]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role in ["ADMIN", "SUPER_ADMIN"]

    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == "SUPER_ADMIN"

    def can_manage_organization(self, org_id: int) -> bool:
        """Check if user can manage specific organization"""
        if self.is_super_admin():
            return True
        return self.organization_id == org_id


@dataclass(frozen=True)
class Credentials:
    """Login credentials value object (immutable)"""
    username: str
    password: str

    def __post_init__(self):
        """Validation"""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not self.password or len(self.password) < 6:
            raise ValueError("Password must be at least 6 characters")
