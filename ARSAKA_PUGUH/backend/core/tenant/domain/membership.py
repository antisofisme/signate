"""
Tenant Membership Domain Entity

Represents a user's membership in a tenant with a specific role.
Framework-agnostic, pure Python.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class MemberRole(str, Enum):
    """Member role in tenant."""
    OWNER = "owner"      # Full control, can delete tenant
    ADMIN = "admin"      # Can manage members and settings
    MEMBER = "member"    # Can use all features
    VIEWER = "viewer"    # Read-only access


class MembershipStatus(str, Enum):
    """Membership status."""
    ACTIVE = "active"
    INVITED = "invited"  # Pending acceptance
    SUSPENDED = "suspended"


# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    MemberRole.OWNER: 4,
    MemberRole.ADMIN: 3,
    MemberRole.MEMBER: 2,
    MemberRole.VIEWER: 1,
}


@dataclass
class TenantMembership:
    """
    Tenant membership domain entity.

    Links a user to a tenant with a specific role.
    One user can have memberships in multiple tenants.
    """
    # Identity
    membership_id: UUID
    user_id: UUID
    tenant_id: UUID

    # Role & Status
    role: MemberRole
    status: MembershipStatus = MembershipStatus.ACTIVE

    # Invitation tracking
    invited_by_user_id: Optional[UUID] = None
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create_owner(
        cls,
        user_id: UUID,
        tenant_id: UUID,
    ) -> "TenantMembership":
        """Create owner membership (used when creating tenant).

        Args:
            user_id: Owner's user ID
            tenant_id: Tenant ID

        Returns:
            New owner membership
        """
        now = datetime.utcnow()
        return cls(
            membership_id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            role=MemberRole.OWNER,
            status=MembershipStatus.ACTIVE,
            joined_at=now,
            created_at=now,
        )

    @classmethod
    def create_invited(
        cls,
        user_id: UUID,
        tenant_id: UUID,
        role: MemberRole,
        invited_by: UUID,
    ) -> "TenantMembership":
        """Create invited membership (pending acceptance).

        Args:
            user_id: Invited user's ID
            tenant_id: Tenant ID
            role: Assigned role
            invited_by: User who sent the invitation

        Returns:
            New invited membership
        """
        now = datetime.utcnow()
        return cls(
            membership_id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            status=MembershipStatus.INVITED,
            invited_by_user_id=invited_by,
            invited_at=now,
            created_at=now,
        )

    @classmethod
    def create_direct(
        cls,
        user_id: UUID,
        tenant_id: UUID,
        role: MemberRole,
        added_by: UUID,
    ) -> "TenantMembership":
        """Create direct membership (no invitation needed).

        Used when admin adds an existing user directly.

        Args:
            user_id: User's ID
            tenant_id: Tenant ID
            role: Assigned role
            added_by: User who added this member

        Returns:
            New active membership
        """
        now = datetime.utcnow()
        return cls(
            membership_id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            status=MembershipStatus.ACTIVE,
            invited_by_user_id=added_by,
            invited_at=now,
            joined_at=now,
            created_at=now,
        )

    def is_active(self) -> bool:
        """Check if membership is active."""
        return self.status == MembershipStatus.ACTIVE

    def is_owner(self) -> bool:
        """Check if this is an owner membership."""
        return self.role == MemberRole.OWNER

    def is_admin_or_higher(self) -> bool:
        """Check if admin or owner."""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN)

    def has_permission(self, required_role: MemberRole) -> bool:
        """Check if has required role or higher.

        Args:
            required_role: Minimum required role

        Returns:
            True if has sufficient permissions
        """
        return ROLE_HIERARCHY[self.role] >= ROLE_HIERARCHY[required_role]

    def can_manage_role(self, target_role: MemberRole) -> bool:
        """Check if can manage (add/change/remove) a member with target role.

        Rules:
        - Owner can manage anyone
        - Admin can manage members and viewers
        - Members and viewers cannot manage anyone

        Args:
            target_role: Role to be managed

        Returns:
            True if can manage
        """
        if self.role == MemberRole.OWNER:
            return True
        if self.role == MemberRole.ADMIN:
            return target_role in (MemberRole.MEMBER, MemberRole.VIEWER)
        return False

    def accept_invitation(self) -> None:
        """Accept invitation and activate membership."""
        if self.status != MembershipStatus.INVITED:
            raise ValueError("Can only accept invited memberships")
        self.status = MembershipStatus.ACTIVE
        self.joined_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def change_role(self, new_role: MemberRole) -> None:
        """Change member's role.

        Args:
            new_role: New role to assign
        """
        self.role = new_role
        self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend membership."""
        self.status = MembershipStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def reactivate(self) -> None:
        """Reactivate suspended membership."""
        if self.status != MembershipStatus.SUSPENDED:
            raise ValueError("Can only reactivate suspended memberships")
        self.status = MembershipStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "membership_id": str(self.membership_id),
            "user_id": str(self.user_id),
            "tenant_id": str(self.tenant_id),
            "role": self.role.value,
            "status": self.status.value,
            "invited_by_user_id": str(self.invited_by_user_id) if self.invited_by_user_id else None,
            "invited_at": self.invited_at.isoformat() if self.invited_at else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
