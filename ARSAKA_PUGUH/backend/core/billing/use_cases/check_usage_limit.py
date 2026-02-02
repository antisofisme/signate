"""
Check Usage Limit Use Case

Checks if tenant has reached plan limits before operations.
"""

from uuid import UUID
from typing import Tuple

from ..interfaces import ISubscriptionRepository, IPlanRepository
from ..domain import SubscriptionPlan
from ..exceptions import PlanLimitError, SubscriptionNotFoundError


class CheckUsageLimitUseCase:
    """Check plan usage limits"""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
    ):
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo

    async def check_decisions(self, tenant_id: UUID) -> Tuple[bool, int, int]:
        """
        Check if tenant can create more decisions.

        Returns:
            Tuple of (can_create, current_usage, limit)
            limit = -1 means unlimited

        Raises:
            SubscriptionNotFoundError: If no subscription
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            raise SubscriptionNotFoundError(str(tenant_id))

        plan = await self._plan_repo.get_by_id(subscription.plan_id)
        if not plan:
            # Default to free plan limits
            return (subscription.decisions_this_month < 1000, subscription.decisions_this_month, 1000)

        limit = plan.limits.max_decisions_per_month
        if limit is None:
            return (True, subscription.decisions_this_month, -1)

        can_create = subscription.decisions_this_month < limit
        return (can_create, subscription.decisions_this_month, limit)

    async def check_projects(
        self,
        tenant_id: UUID,
        current_count: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if tenant can create more projects.

        Args:
            tenant_id: Tenant UUID
            current_count: Current number of projects

        Returns:
            Tuple of (can_create, current_count, limit)
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            # No subscription = free tier
            return (current_count < 1, current_count, 1)

        plan = await self._plan_repo.get_by_id(subscription.plan_id)
        if not plan:
            return (current_count < 1, current_count, 1)

        limit = plan.limits.max_projects
        if limit is None:
            return (True, current_count, -1)

        return (current_count < limit, current_count, limit)

    async def check_team_members(
        self,
        tenant_id: UUID,
        current_count: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if tenant can add more team members.

        Args:
            tenant_id: Tenant UUID
            current_count: Current number of members

        Returns:
            Tuple of (can_add, current_count, limit)
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            return (current_count < 3, current_count, 3)

        plan = await self._plan_repo.get_by_id(subscription.plan_id)
        if not plan:
            return (current_count < 3, current_count, 3)

        limit = plan.limits.max_team_members
        if limit is None:
            return (True, current_count, -1)

        return (current_count < limit, current_count, limit)

    async def increment_decision_usage(self, tenant_id: UUID) -> int:
        """
        Increment decision usage counter.

        Call this after successfully creating a decision.

        Returns:
            New usage count
        """
        return await self._subscription_repo.increment_usage(tenant_id)

    async def enforce_decision_limit(self, tenant_id: UUID) -> None:
        """
        Check and raise if decision limit exceeded.

        Use as a guard before creating decisions.

        Raises:
            PlanLimitError: If limit exceeded
        """
        can_create, current, limit = await self.check_decisions(tenant_id)
        if not can_create:
            raise PlanLimitError(
                "DECISIONS",
                f"You've reached your monthly limit of {limit:,} decisions. "
                f"Upgrade your plan for more capacity.",
            )
