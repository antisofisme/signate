"""
Invitation Domain Entity

Represents an invitation to join a tenant.
Framework-agnostic, pure Python.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum
import secrets

from .membership import MemberRole


class InvitationStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Default invitation expiry (7 days)
DEFAULT_INVITATION_EXPIRY_DAYS = 7


def generate_invitation_token() -> str:
    """Generate secure invitation token."""
    return secrets.token_urlsafe(32)


@dataclass
class Invitation:
    """
    Invitation domain entity.

    Email-based invitation to join a tenant.
    Can be sent to existing users or new users.
    """
    # Identity
    invitation_id: UUID
    token: str  # Secure token for accepting invitation

    # Target
    email: str  # Email to invite
    tenant_id: UUID

    # Assignment
    role: MemberRole  # Role to assign on acceptance

    # Inviter
    invited_by_user_id: UUID

    # Status
    status: InvitationStatus = InvitationStatus.PENDING

    # Target user (filled when user exists or registers)
    target_user_id: Optional[UUID] = None

    # Expiry
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=DEFAULT_INVITATION_EXPIRY_DAYS))

    # Status timestamps
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    # Message from inviter
    message: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate invitation entity."""
        # Email must be lowercase
        self.email = self.email.lower().strip()

    @classmethod
    def create(
        cls,
        email: str,
        tenant_id: UUID,
        role: MemberRole,
        invited_by: UUID,
        message: Optional[str] = None,
        expiry_days: int = DEFAULT_INVITATION_EXPIRY_DAYS,
        target_user_id: Optional[UUID] = None,
    ) -> "Invitation":
        """Create a new invitation.

        Args:
            email: Email address to invite
            tenant_id: Tenant to invite to
            role: Role to assign
            invited_by: User sending the invitation
            message: Optional message to include
            expiry_days: Days until expiry
            target_user_id: User ID if email already registered

        Returns:
            New Invitation entity
        """
        return cls(
            invitation_id=uuid4(),
            token=generate_invitation_token(),
            email=email.lower().strip(),
            tenant_id=tenant_id,
            role=role,
            invited_by_user_id=invited_by,
            target_user_id=target_user_id,
            message=message,
            expires_at=datetime.utcnow() + timedelta(days=expiry_days),
        )

    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == InvitationStatus.PENDING

    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        if self.status == InvitationStatus.EXPIRED:
            return True
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if invitation can be accepted.

        Must be pending and not expired.
        """
        return self.is_pending() and not self.is_expired()

    def accept(self, user_id: UUID) -> None:
        """Accept the invitation.

        Args:
            user_id: User who is accepting
        """
        if not self.is_valid():
            raise ValueError("Cannot accept: invitation is not valid")

        self.status = InvitationStatus.ACCEPTED
        self.target_user_id = user_id
        self.accepted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self) -> None:
        """Reject the invitation."""
        if not self.is_pending():
            raise ValueError("Cannot reject: invitation is not pending")

        self.status = InvitationStatus.REJECTED
        self.rejected_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the invitation (by admin/owner)."""
        if not self.is_pending():
            raise ValueError("Cannot cancel: invitation is not pending")

        self.status = InvitationStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def mark_expired(self) -> None:
        """Mark invitation as expired."""
        self.status = InvitationStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def link_user(self, user_id: UUID) -> None:
        """Link invitation to a user (when user registers).

        Args:
            user_id: Registered user's ID
        """
        self.target_user_id = user_id
        self.updated_at = datetime.utcnow()

    def extend(self, days: int = DEFAULT_INVITATION_EXPIRY_DAYS) -> None:
        """Extend invitation expiry.

        Args:
            days: Additional days to add
        """
        if not self.is_pending():
            raise ValueError("Cannot extend: invitation is not pending")

        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()

    def to_dict(self, include_token: bool = False) -> dict:
        """Convert to dictionary (for API responses).

        Args:
            include_token: Include the token (only for email recipient)
        """
        data = {
            "invitation_id": str(self.invitation_id),
            "email": self.email,
            "tenant_id": str(self.tenant_id),
            "role": self.role.value,
            "status": self.status.value,
            "invited_by_user_id": str(self.invited_by_user_id),
            "message": self.message,
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "created_at": self.created_at.isoformat(),
        }

        if include_token:
            data["token"] = self.token

        if self.target_user_id:
            data["target_user_id"] = str(self.target_user_id)

        return data
