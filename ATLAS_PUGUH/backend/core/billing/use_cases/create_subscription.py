"""
Create Subscription Use Case

Creates initial subscription for a new tenant (usually free plan).
"""

from uuid import UUID, uuid4
from datetime import datetime, timedelta

from ..interfaces import ISubscriptionRepository, IPlanRepository
from ..domain import Subscription, SubscriptionStatus
from ..exceptions import (
    PlanNotFoundError,
    SubscriptionAlreadyExistsError,
)


class CreateSubscriptionUseCase:
    """Create subscription for new tenant"""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
    ):
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo

    async def execute(
        self,
        tenant_id: UUID,
        plan_id: str = "free",
        with_trial: bool = False,
    ) -> Subscription:
        """
        Create subscription for tenant.

        Args:
            tenant_id: Tenant UUID
            plan_id: Plan to subscribe to (default: free)
            with_trial: Start with trial period if plan supports it

        Returns:
            Created subscription

        Raises:
            PlanNotFoundError: If plan doesn't exist
            SubscriptionAlreadyExistsError: If tenant already has subscription
        """
        # Check if tenant already has subscription
        existing = await self._subscription_repo.get_by_tenant(tenant_id)
        if existing:
            raise SubscriptionAlreadyExistsError(str(tenant_id))

        # Get plan
        plan = await self._plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(plan_id)

        # Calculate dates
        now = datetime.utcnow()
        period_days = 30 if plan.billing_interval == "month" else 365

        # Determine status and trial
        trial_end_at = None
        if with_trial and plan.has_trial:
            status = SubscriptionStatus.TRIALING
            trial_end_at = now + timedelta(days=plan.trial_days)
            # Trial period determines end date
            current_period_end = trial_end_at
        else:
            status = SubscriptionStatus.ACTIVE
            current_period_end = now + timedelta(days=period_days)

        # Create subscription
        subscription = Subscription(
            subscription_id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=status,
            payment_provider="manual" if plan.is_free else "midtrans",
            current_period_start=now,
            current_period_end=current_period_end,
            trial_end_at=trial_end_at,
            usage_reset_at=now,
        )

        return await self._subscription_repo.create(subscription)
