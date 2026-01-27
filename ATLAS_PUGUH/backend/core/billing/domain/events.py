"""
Billing Domain Events

Events emitted by billing operations for audit and integration.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class BillingEvent:
    """Base class for billing events"""

    event_type: str
    tenant_id: UUID
    timestamp: datetime

    @classmethod
    def create(cls, tenant_id: UUID, **kwargs):
        return cls(
            event_type=cls.__name__,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            **kwargs,
        )


@dataclass(frozen=True)
class SubscriptionCreatedEvent(BillingEvent):
    """Subscription created for tenant"""

    subscription_id: UUID
    plan_id: str
    is_trial: bool


@dataclass(frozen=True)
class SubscriptionUpgradedEvent(BillingEvent):
    """Subscription upgraded to higher plan"""

    subscription_id: UUID
    from_plan_id: str
    to_plan_id: str


@dataclass(frozen=True)
class SubscriptionDowngradedEvent(BillingEvent):
    """Subscription downgraded to lower plan"""

    subscription_id: UUID
    from_plan_id: str
    to_plan_id: str
    effective_at: datetime  # When downgrade takes effect


@dataclass(frozen=True)
class SubscriptionCancelledEvent(BillingEvent):
    """Subscription cancelled"""

    subscription_id: UUID
    plan_id: str
    reason: Optional[str]
    immediate: bool  # True if cancelled immediately, False if at period end


@dataclass(frozen=True)
class SubscriptionReactivatedEvent(BillingEvent):
    """Subscription reactivated after cancellation"""

    subscription_id: UUID
    plan_id: str


@dataclass(frozen=True)
class PaymentReceivedEvent(BillingEvent):
    """Payment successfully processed"""

    invoice_id: UUID
    amount_cents: int
    currency: str
    payment_provider: str
    provider_payment_id: Optional[str]


@dataclass(frozen=True)
class PaymentFailedEvent(BillingEvent):
    """Payment failed"""

    invoice_id: UUID
    amount_cents: int
    currency: str
    payment_provider: str
    error_message: Optional[str]


@dataclass(frozen=True)
class InvoiceCreatedEvent(BillingEvent):
    """Invoice created"""

    invoice_id: UUID
    invoice_number: str
    amount_cents: int
    currency: str


@dataclass(frozen=True)
class UsageLimitApproachedEvent(BillingEvent):
    """Usage approaching plan limit (80% threshold)"""

    resource: str  # "decisions", "projects", "members", etc.
    current_usage: int
    limit: int
    percentage: float


@dataclass(frozen=True)
class UsageLimitExceededEvent(BillingEvent):
    """Usage exceeded plan limit"""

    resource: str
    current_usage: int
    limit: int
