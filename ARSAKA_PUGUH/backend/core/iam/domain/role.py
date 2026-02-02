"""
Role Domain Entity

Represents a role in the IAM system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


@dataclass
class Role:
    """Role domain entity."""

    id: UUID
    tenant_id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool = False
    permissions: List["Permission"] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def can_delete(self) -> bool:
        """Check if this role can be deleted."""
        return not self.is_system

    def can_update(self) -> bool:
        """Check if this role can be updated."""
        return not self.is_system


# Forward reference for type hints
from .permission import Permission  # noqa: E402, F401
