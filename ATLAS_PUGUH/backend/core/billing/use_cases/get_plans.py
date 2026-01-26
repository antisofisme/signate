"""
Get Plans Use Case

Retrieves available subscription plans for pricing page.
"""

from typing import List, Optional

from ..interfaces import IPlanRepository
from ..domain import SubscriptionPlan


class GetPlansUseCase:
    """Get available subscription plans"""

    def __init__(self, plan_repo: IPlanRepository):
        self._plan_repo = plan_repo

    async def get_all(self) -> List[SubscriptionPlan]:
        """Get all active plans for pricing page"""
        return await self._plan_repo.list_active()

    async def get_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a specific plan by ID"""
        return await self._plan_repo.get_by_id(plan_id)
