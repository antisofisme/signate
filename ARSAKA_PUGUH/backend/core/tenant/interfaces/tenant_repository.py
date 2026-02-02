"""
Tenant Repository Interface

Abstract contract for tenant data access.
Implementations handle actual database operations.

Source: INFRA-DEC-011-modular-architecture.md
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.tenant import Tenant


class ITenantRepository(ABC):
    """Interface for tenant data access."""

    @abstractmethod
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant.

        Args:
            tenant: Tenant entity to create

        Returns:
            Created tenant with generated ID

        Raises:
            TenantSlugExistsError: If slug already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant's UUID

        Returns:
            Tenant if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug.

        Args:
            slug: URL-friendly identifier

        Returns:
            Tenant if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[Tenant]:
        """List tenants that user is a member of.

        Args:
            user_id: User's UUID
            include_inactive: Include suspended/deleted tenants

        Returns:
            List of tenants
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        include_inactive: bool = False
    ) -> List[Tenant]:
        """List all tenants (admin only).

        Args:
            limit: Max results
            offset: Pagination offset
            include_inactive: Include suspended/deleted tenants

        Returns:
            List of tenants
        """
        pass

    @abstractmethod
    async def count_all(self, include_inactive: bool = False) -> int:
        """Count all tenants.

        Args:
            include_inactive: Include suspended/deleted tenants

        Returns:
            Total count
        """
        pass

    @abstractmethod
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant.

        Args:
            tenant: Tenant entity with updated fields

        Returns:
            Updated tenant
        """
        pass

    @abstractmethod
    async def update_status(self, tenant_id: UUID, status: str) -> None:
        """Update tenant status.

        Args:
            tenant_id: Tenant's UUID
            status: New status (active, suspended, trial)
        """
        pass

    @abstractmethod
    async def update_plan(self, tenant_id: UUID, plan: str) -> None:
        """Update tenant subscription plan.

        Args:
            tenant_id: Tenant's UUID
            plan: New plan (free, starter, pro, enterprise)
        """
        pass

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID) -> None:
        """Soft delete tenant.

        Args:
            tenant_id: Tenant's UUID
        """
        pass

    @abstractmethod
    async def slug_exists(self, slug: str, exclude_tenant_id: Optional[UUID] = None) -> bool:
        """Check if slug exists.

        Args:
            slug: Slug to check
            exclude_tenant_id: Exclude this tenant from check (for updates)

        Returns:
            True if slug exists
        """
        pass
