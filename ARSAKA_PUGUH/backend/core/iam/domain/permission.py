"""
Permission Domain Entity

Represents a permission in the IAM system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Permission:
    """Permission domain entity."""

    id: UUID
    resource: str  # e.g., "rules", "workflows", "users"
    action: str    # e.g., "read", "create", "update", "delete", "approve"
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @property
    def key(self) -> str:
        """Get permission key in format 'resource.action'."""
        return f"{self.resource}.{self.action}"

    def __str__(self) -> str:
        return self.key
