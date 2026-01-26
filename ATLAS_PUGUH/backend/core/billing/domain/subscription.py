"""
Subscription Domain Entity
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle status"""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"

    @property
    def is_usable(self) -> bool:
        """Can the tenant use paid features?"""
        return self in (
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE,  # Grace period
        )


@dataclass
class Subscription:
    """
    Subscription Entity

    One subscription per tenant. Tracks plan, status, and usage.
    """

    subscription_id: UUID
    tenant_id: UUID

    # Plan
    plan_id: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    # Payment provider
    payment_provider: str = "manual"  # "midtrans", "stripe", "manual"
    provider_subscription_id: Optional[str] = None

    # Billing period
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: Optional[datetime] = None

    # Trial
    trial_end_at: Optional[datetime] = None

    # Cancellation
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Usage metering
    decisions_this_month: int = 0
    usage_reset_at: datetime = field(default_factory=datetime.utcnow)

    # Scheduled plan change (for downgrades)
    scheduled_plan_id: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Set default period end if not provided
        if self.current_period_end is None:
            self.current_period_end = self.current_period_start + timedelta(days=30)

    @property
    def is_trialing(self) -> bool:
        return self.status == SubscriptionStatus.TRIALING

    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def is_cancelled(self) -> bool:
        return self.status == SubscriptionStatus.CANCELLED

    @property
    def is_past_due(self) -> bool:
        return self.status == SubscriptionStatus.PAST_DUE

    @property
    def is_usable(self) -> bool:
        """Can tenant use paid features?"""
        return self.status.is_usable

    @property
    def will_cancel(self) -> bool:
        """Will cancel at period end?"""
        return self.cancel_at_period_end

    @property
    def days_until_renewal(self) -> int:
        """Days until next billing"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_in_trial(self) -> bool:
        """Currently in trial period?"""
        if not self.trial_end_at:
            return False
        return datetime.utcnow() < self.trial_end_at

    def activate(self) -> None:
        """Activate subscription after successful payment"""
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def mark_past_due(self) -> None:
        """Mark as past due (payment failed)"""
        self.status = SubscriptionStatus.PAST_DUE
        self.updated_at = datetime.utcnow()

    def cancel(self, reason: Optional[str] = None, immediate: bool = False) -> None:
        """
        Cancel subscription.

        If immediate=False, cancels at end of current period.
        If immediate=True, cancels immediately.
        """
        if immediate:
            self.status = SubscriptionStatus.CANCELLED
        else:
            self.cancel_at_period_end = True
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.updated_at = datetime.utcnow()

    def reactivate(self) -> None:
        """Reactivate a cancelled subscription"""
        if self.cancel_at_period_end:
            self.cancel_at_period_end = False
            self.cancelled_at = None
            self.cancellation_reason = None
            self.updated_at = datetime.utcnow()

    def extend_period(self, days: int = 30) -> None:
        """Extend billing period after payment"""
        self.current_period_start = datetime.utcnow()
        self.current_period_end = self.current_period_start + timedelta(days=days)
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def increment_usage(self) -> int:
        """Increment decision count, return new value"""
        self.decisions_this_month += 1
        self.updated_at = datetime.utcnow()
        return self.decisions_this_month

    def reset_usage(self) -> None:
        """Reset monthly usage counter"""
        self.decisions_this_month = 0
        self.usage_reset_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def schedule_plan_change(self, new_plan_id: str) -> None:
        """Schedule plan change for next billing cycle"""
        self.scheduled_plan_id = new_plan_id
        self.updated_at = datetime.utcnow()

    def apply_scheduled_change(self) -> Optional[str]:
        """Apply scheduled plan change, return new plan_id if changed"""
        if self.scheduled_plan_id:
            old_plan = self.plan_id
            self.plan_id = self.scheduled_plan_id
            self.scheduled_plan_id = None
            self.updated_at = datetime.utcnow()
            return self.plan_id
        return None

    def upgrade_to(self, new_plan_id: str) -> None:
        """Upgrade plan immediately"""
        self.plan_id = new_plan_id
        self.scheduled_plan_id = None  # Clear any scheduled downgrade
        self.updated_at = datetime.utcnow()
