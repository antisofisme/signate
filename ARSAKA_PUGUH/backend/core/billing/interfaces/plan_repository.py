"""
Plan Repository Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain import SubscriptionPlan


class IPlanRepository(ABC):
    """Interface for subscription plan data access"""

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get plan by ID"""
        pass

    @abstractmethod
    async def list_active(self) -> List[SubscriptionPlan]:
        """List all active plans (for pricing page)"""
        pass

    @abstractmethod
    async def list_all(self) -> List[SubscriptionPlan]:
        """List all plans including inactive"""
        pass
