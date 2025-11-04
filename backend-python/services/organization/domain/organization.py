"""
Organization Domain Entity
Business logic for organizations/tenants
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Organization:
    """Organization domain entity"""

    id: Optional[int]
    name: str
    organization_pin: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate organization data"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Organization name is required")

        if not self.organization_pin or len(self.organization_pin) < 4:
            raise ValueError("Organization PIN must be at least 4 characters")

        if len(self.organization_pin) > 6:
            raise ValueError("Organization PIN must be maximum 6 characters")

    def activate(self):
        """Activate organization"""
        self.is_active = True

    def deactivate(self):
        """Deactivate organization"""
        self.is_active = False
