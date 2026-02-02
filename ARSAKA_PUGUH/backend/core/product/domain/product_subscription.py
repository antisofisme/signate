"""
Product Subscription Domain Entity

Links a tenant to a product subscription.
Tracks which products a tenant has access to.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ProductSubscriptionStatus(str, Enum):
    """Product subscription status."""
    ACTIVE = "active"           # Currently subscribed
    TRIALING = "trialing"       # In trial period
    CANCELLED = "cancelled"     # Subscription cancelled
    EXPIRED = "expired"         # Subscription expired
    SUSPENDED = "suspended"     # Suspended (payment issue)


@dataclass
class ProductSubscription:
    """
    Product Subscription Entity

    Represents a tenant's subscription to a specific product.
    """

    # Identity
    subscription_id: UUID
    tenant_id: UUID
    product_id: UUID
    product_code: str           # Denormalized for quick lookup

    # Plan
    plan_id: str                # "free", "starter", "pro", "enterprise"

    # Status
    status: ProductSubscriptionStatus = ProductSubscriptionStatus.ACTIVE

    # Trial
    trial_ends_at: Optional[datetime] = None
    is_trial: bool = False

    # Billing period
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

    # Usage tracking
    usage_this_period: int = 0
    usage_limit: Optional[int] = None  # None = unlimited

    # Cancellation
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        product_id: UUID,
        product_code: str,
        plan_id: str = "free",
        trial_days: int = 0,
    ) -> "ProductSubscription":
        """Create a new product subscription."""
        now = datetime.utcnow()
        trial_ends_at = None
        is_trial = False

        if trial_days > 0:
            from datetime import timedelta
            trial_ends_at = now + timedelta(days=trial_days)
            is_trial = True

        return cls(
            subscription_id=uuid4(),
            tenant_id=tenant_id,
            product_id=product_id,
            product_code=product_code,
            plan_id=plan_id,
            status=ProductSubscriptionStatus.TRIALING if is_trial else ProductSubscriptionStatus.ACTIVE,
            trial_ends_at=trial_ends_at,
            is_trial=is_trial,
            current_period_start=now,
        )

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (
            ProductSubscriptionStatus.ACTIVE,
            ProductSubscriptionStatus.TRIALING,
        )

    @property
    def is_in_trial(self) -> bool:
        """Check if currently in trial."""
        if not self.is_trial or not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at

    @property
    def trial_days_remaining(self) -> int:
        """Get remaining trial days."""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        remaining = self.trial_ends_at - datetime.utcnow()
        return max(0, remaining.days)

    def can_access(self) -> bool:
        """Check if tenant can access the product."""
        if not self.is_active:
            return False
        if self.is_trial and self.trial_ends_at:
            return datetime.utcnow() < self.trial_ends_at
        return True

    def check_usage_limit(self, additional: int = 1) -> bool:
        """Check if usage is within limit."""
        if self.usage_limit is None:
            return True  # Unlimited
        return (self.usage_this_period + additional) <= self.usage_limit

    def increment_usage(self, amount: int = 1) -> None:
        """Increment usage counter."""
        self.usage_this_period += amount
        self.updated_at = datetime.utcnow()

    def cancel(self, at_period_end: bool = True) -> None:
        """Cancel subscription."""
        self.cancelled_at = datetime.utcnow()
        self.cancel_at_period_end = at_period_end
        if not at_period_end:
            self.status = ProductSubscriptionStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "subscription_id": str(self.subscription_id),
            "tenant_id": str(self.tenant_id),
            "product_id": str(self.product_id),
            "product_code": self.product_code,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "is_trial": self.is_trial,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "trial_days_remaining": self.trial_days_remaining,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "usage_this_period": self.usage_this_period,
            "usage_limit": self.usage_limit,
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at.isoformat(),
        }
