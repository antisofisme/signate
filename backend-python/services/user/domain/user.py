"""
User Domain Entity
Business logic for users
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
    organization_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    VALID_ROLES = ['super_admin', 'admin', 'manager', 'viewer']

    def __post_init__(self):
        """Validate user data"""
        if not self.username or len(self.username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")

        if not self.full_name or len(self.full_name.strip()) < 3:
            raise ValueError("Full name must be at least 3 characters")

        if self.role not in self.VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(self.VALID_ROLES)}")

    def activate(self):
        """Activate user"""
        self.is_active = True

    def deactivate(self):
        """Deactivate user"""
        self.is_active = False

    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role in ['super_admin', 'admin']

    def is_manager(self) -> bool:
        """Check if user is a manager"""
        return self.role == 'manager'

    def can_manage_organization(self) -> bool:
        """Check if user can manage organization"""
        return self.role in ['super_admin', 'admin', 'manager']
