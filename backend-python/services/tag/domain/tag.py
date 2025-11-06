"""
Tag Domain Entity - CORE BUSINESS LOGIC
Pure Python class, no framework dependencies
"""

from datetime import datetime
from typing import Optional


class Tag:
    """
    Tag Entity - Domain Model

    Business rules:
    - tag_name must be unique
    - tag_name cannot be empty
    - color must be valid hex format
    """

    def __init__(
        self,
        id: Optional[int],
        tag_name: str,
        description: Optional[str],
        color: str,
        organization_id: int,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.tag_name = tag_name
        self.description = description
        self.color = color
        self.organization_id = organization_id
        self.created_at = created_at or datetime.utcnow()

        # Business validation
        self._validate()

    def _validate(self):
        """Validate business rules"""
        if not self.tag_name or not self.tag_name.strip():
            raise ValueError("Tag name cannot be empty")

        if not self.color or not self.color.startswith('#'):
            raise ValueError("Color must be a valid hex format (e.g., #3B82F6)")

        if len(self.color) not in [4, 7]:  # #RGB or #RRGGBB
            raise ValueError("Color must be #RGB or #RRGGBB format")

    def update(
        self,
        tag_name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ):
        """Update tag properties with validation"""
        if tag_name is not None:
            self.tag_name = tag_name
        if description is not None:
            self.description = description
        if color is not None:
            self.color = color

        self._validate()

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "tag_name": self.tag_name,
            "description": self.description,
            "color": self.color,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.tag_name}', color='{self.color}')>"
