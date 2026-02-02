"""
Subscription Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain import Subscription


class ISubscriptionRepository(ABC):
    """Interface for subscription data access"""

    @abstractmethod
    async def get_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> Optional[Subscription]:
        """Get subscription for a tenant (one subscription per tenant)"""
        pass

    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription:
        """Create a new subscription"""
        pass

    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription:
        """Update an existing subscription"""
        pass

    @abstractmethod
    async def delete(self, subscription_id: UUID) -> bool:
        """Delete a subscription"""
        pass

    @abstractmethod
    async def list_expiring_soon(self, days: int = 7) -> List[Subscription]:
        """List subscriptions expiring within N days"""
        pass

    @abstractmethod
    async def list_past_due(self) -> List[Subscription]:
        """List all past due subscriptions"""
        pass

    @abstractmethod
    async def list_needing_usage_reset(self) -> List[Subscription]:
        """List subscriptions needing monthly usage reset"""
        pass

    @abstractmethod
    async def increment_usage(self, tenant_id: UUID) -> int:
        """Increment decision count, return new value"""
        pass
