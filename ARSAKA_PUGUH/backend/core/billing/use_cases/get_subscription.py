"""
Get Subscription Use Case

Retrieves subscription details with plan info and usage.
"""

from typing import Optional
from uuid import UUID
from dataclasses import dataclass

from ..interfaces import ISubscriptionRepository, IPlanRepository
from ..domain import Subscription, SubscriptionPlan
from ..exceptions import SubscriptionNotFoundError


@dataclass
class SubscriptionDetails:
    """Subscription with plan details and usage info"""

    subscription: Subscription
    plan: SubscriptionPlan
    usage_percentage: float
    is_near_limit: bool
    is_over_limit: bool


class GetSubscriptionUseCase:
    """Get subscription details for tenant"""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
    ):
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo

    async def execute(self, tenant_id: UUID) -> SubscriptionDetails:
        """
        Get subscription with details.

        Args:
            tenant_id: Tenant UUID

        Returns:
            SubscriptionDetails with plan and usage info

        Raises:
            SubscriptionNotFoundError: If no subscription found
        """
        # Get subscription
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            raise SubscriptionNotFoundError(str(tenant_id))

        # Get plan
        plan = await self._plan_repo.get_by_id(subscription.plan_id)
        if not plan:
            # Fallback to free plan if plan not found
            plan = await self._plan_repo.get_by_id("free")

        # Calculate usage percentage
        usage_percentage = 0.0
        is_near_limit = False
        is_over_limit = False

        if plan.limits.max_decisions_per_month:
            usage_percentage = (
                subscription.decisions_this_month
                / plan.limits.max_decisions_per_month
                * 100
            )
            is_near_limit = usage_percentage >= 80
            is_over_limit = usage_percentage >= 100

        return SubscriptionDetails(
            subscription=subscription,
            plan=plan,
            usage_percentage=round(usage_percentage, 1),
            is_near_limit=is_near_limit,
            is_over_limit=is_over_limit,
        )

    async def get_or_none(self, tenant_id: UUID) -> Optional[SubscriptionDetails]:
        """Get subscription or return None if not found"""
        try:
            return await self.execute(tenant_id)
        except SubscriptionNotFoundError:
            return None
