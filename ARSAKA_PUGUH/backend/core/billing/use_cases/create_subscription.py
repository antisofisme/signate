"""
Create Subscription Use Case

Creates initial subscription for a new tenant (usually free plan).

SECURITY: Includes trial abuse prevention to detect and block:
- Disposable email addresses
- Multiple trials from same organization
- IP-based abuse patterns
"""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from ..interfaces import ISubscriptionRepository, IPlanRepository
from ..domain import Subscription, SubscriptionStatus
from ..exceptions import (
    PlanNotFoundError,
    SubscriptionAlreadyExistsError,
    BillingError,
)
from ..services.trial_abuse_prevention import (
    TrialAbusePreventionService,
    TrialAbuseError,
    DisposableEmailError,
    TrialAlreadyUsedError,
    TooManyTrialsError,
)


class TrialAbuseDetectedError(BillingError):
    """Raised when trial abuse is detected."""

    def __init__(self, original_error: TrialAbuseError):
        super().__init__(
            message=original_error.message,
            code=original_error.code,
        )
        self.details = original_error.details


class CreateSubscriptionUseCase:
    """Create subscription for new tenant.

    SECURITY: Includes trial abuse prevention when with_trial=True.
    """

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
        trial_prevention: Optional[TrialAbusePreventionService] = None,
    ):
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo
        self._trial_prevention = trial_prevention

    async def execute(
        self,
        tenant_id: UUID,
        plan_id: str = "free",
        with_trial: bool = False,
        # Trial abuse prevention context
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Subscription:
        """
        Create subscription for tenant.

        Args:
            tenant_id: Tenant UUID
            plan_id: Plan to subscribe to (default: free)
            with_trial: Start with trial period if plan supports it
            user_email: Email for trial abuse detection (required if with_trial=True)
            ip_address: IP for rate limiting
            user_agent: User agent for fingerprinting

        Returns:
            Created subscription

        Raises:
            PlanNotFoundError: If plan doesn't exist
            SubscriptionAlreadyExistsError: If tenant already has subscription
            TrialAbuseDetectedError: If trial abuse is detected

        SECURITY: Trial abuse prevention is enforced when with_trial=True.
        """
        # Check if tenant already has subscription
        existing = await self._subscription_repo.get_by_tenant(tenant_id)
        if existing:
            raise SubscriptionAlreadyExistsError(str(tenant_id))

        # Get plan
        plan = await self._plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(plan_id)

        # SECURITY: Check for trial abuse before allowing trial
        if with_trial and plan.has_trial:
            if self._trial_prevention and user_email:
                try:
                    await self._trial_prevention.check_can_start_trial(
                        email=user_email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                except TrialAbuseError as e:
                    raise TrialAbuseDetectedError(e)

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

        created = await self._subscription_repo.create(subscription)

        # SECURITY: Record trial for future abuse detection
        if with_trial and plan.has_trial and self._trial_prevention and user_email:
            await self._trial_prevention.record_trial_start(
                email=user_email,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                trial_days=plan.trial_days,
            )

        return created
