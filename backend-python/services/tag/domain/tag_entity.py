"""
Tag Domain Entity
Business logic for tags
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class Tag:
    """Tag domain entity with business rules"""

    id: Optional[int] = None
    name: str = ""
    color: str = "#3B82F6"
    description: Optional[str] = None
    organization_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate tag after initialization"""
        self.validate()

    def validate(self):
        """Validate tag business rules"""
        # Name validation
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")

        if len(self.name) > 100:
            raise ValueError("Tag name cannot exceed 100 characters")

        # Color validation (hex color format)
        if not self._is_valid_hex_color(self.color):
            raise ValueError(f"Invalid color format: {self.color}. Must be hex color (e.g., #3B82F6)")

        # Organization ID validation
        if not self.organization_id or self.organization_id <= 0:
            raise ValueError("Valid organization_id is required")

        # Description validation
        if self.description and len(self.description) > 500:
            raise ValueError("Tag description cannot exceed 500 characters")

    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """Validate hex color format (#RRGGBB)"""
        if not color:
            return False

        # Regex for hex color validation
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(hex_pattern, color))

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
