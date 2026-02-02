"""
Product Subscription Repository Interface

Abstract contract for product subscription data access.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.product_subscription import ProductSubscription


class IProductSubscriptionRepository(ABC):
    """Interface for product subscription data access."""

    @abstractmethod
    async def get_by_id(self, subscription_id: UUID) -> Optional[ProductSubscription]:
        """Get subscription by ID."""
        pass

    @abstractmethod
    async def get_by_tenant_and_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
    ) -> Optional[ProductSubscription]:
        """Get subscription by tenant and product."""
        pass

    @abstractmethod
    async def get_by_tenant_and_code(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> Optional[ProductSubscription]:
        """Get subscription by tenant and product code."""
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_cancelled: bool = False,
    ) -> List[ProductSubscription]:
        """List all subscriptions for a tenant."""
        pass

    @abstractmethod
    async def list_active_by_tenant(
        self,
        tenant_id: UUID,
    ) -> List[ProductSubscription]:
        """List active subscriptions for a tenant."""
        pass

    @abstractmethod
    async def create(self, subscription: ProductSubscription) -> ProductSubscription:
        """Create a new subscription."""
        pass

    @abstractmethod
    async def update(self, subscription: ProductSubscription) -> ProductSubscription:
        """Update subscription."""
        pass

    @abstractmethod
    async def increment_usage(
        self,
        subscription_id: UUID,
        amount: int = 1,
    ) -> None:
        """Increment usage counter."""
        pass

    @abstractmethod
    async def reset_usage(self, subscription_id: UUID) -> None:
        """Reset usage counter (for new billing period)."""
        pass

    @abstractmethod
    async def has_active_subscription(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> bool:
        """Check if tenant has active subscription to a product."""
        pass
