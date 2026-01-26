"""
Project Membership Domain Entity
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class ProjectRole(str, Enum):
    """Roles within a project"""

    ADMIN = "admin"     # Full project control
    MEMBER = "member"   # Can create/edit resources
    VIEWER = "viewer"   # Read-only access

    @property
    def can_edit(self) -> bool:
        return self in (ProjectRole.ADMIN, ProjectRole.MEMBER)

    @property
    def can_manage(self) -> bool:
        return self == ProjectRole.ADMIN

    @classmethod
    def from_string(cls, value: str) -> "ProjectRole":
        """Parse role from string"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.VIEWER


@dataclass
class ProjectMembership:
    """
    Project Membership Entity

    Optional project-level access control.
    If no memberships exist for a project, all tenant members have access.
    """

    project_id: UUID
    user_id: UUID
    role: ProjectRole = ProjectRole.MEMBER

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def change_role(self, new_role: ProjectRole) -> None:
        """Change member's role"""
        self.role = new_role
        self.updated_at = datetime.utcnow()

    def promote_to_admin(self) -> None:
        """Promote to admin"""
        self.change_role(ProjectRole.ADMIN)

    def demote_to_member(self) -> None:
        """Demote to member"""
        self.change_role(ProjectRole.MEMBER)

    def demote_to_viewer(self) -> None:
        """Demote to viewer"""
        self.change_role(ProjectRole.VIEWER)
