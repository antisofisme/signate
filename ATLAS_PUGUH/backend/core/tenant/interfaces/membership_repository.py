"""
Membership Repository Interface

Abstract contract for tenant membership data access.

Source: INFRA-DEC-011-modular-architecture.md
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.membership import TenantMembership, MemberRole


class IMembershipRepository(ABC):
    """Interface for membership data access."""

    @abstractmethod
    async def create(self, membership: TenantMembership) -> TenantMembership:
        """Create a new membership.

        Args:
            membership: Membership entity to create

        Returns:
            Created membership

        Raises:
            AlreadyMemberError: If user is already a member
        """
        pass

    @abstractmethod
    async def get_by_id(self, membership_id: UUID) -> Optional[TenantMembership]:
        """Get membership by ID.

        Args:
            membership_id: Membership's UUID

        Returns:
            Membership if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_and_tenant(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> Optional[TenantMembership]:
        """Get user's membership in a specific tenant.

        Args:
            user_id: User's UUID
            tenant_id: Tenant's UUID

        Returns:
            Membership if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_inactive: bool = False
    ) -> List[TenantMembership]:
        """List all memberships for a tenant.

        Args:
            tenant_id: Tenant's UUID
            include_inactive: Include suspended/invited memberships

        Returns:
            List of memberships
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[TenantMembership]:
        """List all memberships for a user.

        Args:
            user_id: User's UUID
            include_inactive: Include suspended/invited memberships

        Returns:
            List of memberships
        """
        pass

    @abstractmethod
    async def count_by_tenant(
        self,
        tenant_id: UUID,
        include_inactive: bool = False
    ) -> int:
        """Count members in a tenant.

        Args:
            tenant_id: Tenant's UUID
            include_inactive: Include suspended/invited memberships

        Returns:
            Member count
        """
        pass

    @abstractmethod
    async def count_owners(self, tenant_id: UUID) -> int:
        """Count owners in a tenant.

        Args:
            tenant_id: Tenant's UUID

        Returns:
            Owner count
        """
        pass

    @abstractmethod
    async def update(self, membership: TenantMembership) -> TenantMembership:
        """Update membership.

        Args:
            membership: Membership entity with updated fields

        Returns:
            Updated membership
        """
        pass

    @abstractmethod
    async def update_role(
        self,
        membership_id: UUID,
        new_role: MemberRole
    ) -> None:
        """Update membership role.

        Args:
            membership_id: Membership's UUID
            new_role: New role to assign
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        membership_id: UUID,
        status: str
    ) -> None:
        """Update membership status.

        Args:
            membership_id: Membership's UUID
            status: New status (active, invited, suspended)
        """
        pass

    @abstractmethod
    async def delete(self, membership_id: UUID) -> None:
        """Delete membership (hard delete).

        Args:
            membership_id: Membership's UUID
        """
        pass

    @abstractmethod
    async def is_member(self, user_id: UUID, tenant_id: UUID) -> bool:
        """Check if user is a member of tenant.

        Args:
            user_id: User's UUID
            tenant_id: Tenant's UUID

        Returns:
            True if active member
        """
        pass

    @abstractmethod
    async def transfer_ownership(
        self,
        tenant_id: UUID,
        from_user_id: UUID,
        to_user_id: UUID
    ) -> None:
        """Transfer tenant ownership to another member.

        Args:
            tenant_id: Tenant's UUID
            from_user_id: Current owner's UUID
            to_user_id: New owner's UUID
        """
        pass
