"""
Invitation Repository Interface

Abstract contract for invitation data access.

Source: INFRA-DEC-011-modular-architecture.md
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.invitation import Invitation


class IInvitationRepository(ABC):
    """Interface for invitation data access."""

    @abstractmethod
    async def create(self, invitation: Invitation) -> Invitation:
        """Create a new invitation.

        Args:
            invitation: Invitation entity to create

        Returns:
            Created invitation

        Raises:
            InvitationAlreadyPendingError: If pending invitation already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get invitation by ID.

        Args:
            invitation_id: Invitation's UUID

        Returns:
            Invitation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token.

        Used when accepting invitation via link.

        Args:
            token: Secure invitation token

        Returns:
            Invitation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_pending_by_email_and_tenant(
        self,
        email: str,
        tenant_id: UUID
    ) -> Optional[Invitation]:
        """Get pending invitation for email in tenant.

        Args:
            email: Email address
            tenant_id: Tenant's UUID

        Returns:
            Pending invitation if exists, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Invitation]:
        """List invitations for a tenant.

        Args:
            tenant_id: Tenant's UUID
            status: Filter by status (pending, accepted, etc.)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of invitations
        """
        pass

    @abstractmethod
    async def list_by_email(
        self,
        email: str,
        status: Optional[str] = None
    ) -> List[Invitation]:
        """List invitations for an email address.

        Args:
            email: Email address
            status: Filter by status

        Returns:
            List of invitations
        """
        pass

    @abstractmethod
    async def list_pending_for_user(self, user_id: UUID) -> List[Invitation]:
        """List pending invitations for a user (by their email).

        Args:
            user_id: User's UUID (will lookup email)

        Returns:
            List of pending invitations
        """
        pass

    @abstractmethod
    async def count_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None
    ) -> int:
        """Count invitations for a tenant.

        Args:
            tenant_id: Tenant's UUID
            status: Filter by status

        Returns:
            Invitation count
        """
        pass

    @abstractmethod
    async def update(self, invitation: Invitation) -> Invitation:
        """Update invitation.

        Args:
            invitation: Invitation entity with updated fields

        Returns:
            Updated invitation
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        invitation_id: UUID,
        status: str
    ) -> None:
        """Update invitation status.

        Args:
            invitation_id: Invitation's UUID
            status: New status
        """
        pass

    @abstractmethod
    async def link_to_user(
        self,
        invitation_id: UUID,
        user_id: UUID
    ) -> None:
        """Link invitation to a registered user.

        Called when invited user registers.

        Args:
            invitation_id: Invitation's UUID
            user_id: User's UUID
        """
        pass

    @abstractmethod
    async def delete(self, invitation_id: UUID) -> None:
        """Delete invitation (hard delete).

        Args:
            invitation_id: Invitation's UUID
        """
        pass

    @abstractmethod
    async def expire_old_invitations(self) -> int:
        """Expire all old pending invitations.

        Called periodically by scheduler.

        Returns:
            Number of invitations expired
        """
        pass

    @abstractmethod
    async def has_pending_invitation(
        self,
        email: str,
        tenant_id: UUID
    ) -> bool:
        """Check if pending invitation exists.

        Args:
            email: Email address
            tenant_id: Tenant's UUID

        Returns:
            True if pending invitation exists
        """
        pass
