"""
Subscription Plan Domain Entity
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class PlanFeatures:
    """Feature flags for a plan"""

    api_access: bool = False
    sso: bool = False
    priority_support: bool = False
    dedicated_support: bool = False
    sla_guarantee: bool = False
    custom_branding: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "PlanFeatures":
        return cls(
            api_access=data.get("api_access", False),
            sso=data.get("sso", False),
            priority_support=data.get("priority_support", False),
            dedicated_support=data.get("dedicated_support", False),
            sla_guarantee=data.get("sla_guarantee", False),
            custom_branding=data.get("custom_branding", False),
        )

    def to_dict(self) -> dict:
        return {
            "api_access": self.api_access,
            "sso": self.sso,
            "priority_support": self.priority_support,
            "dedicated_support": self.dedicated_support,
            "sla_guarantee": self.sla_guarantee,
            "custom_branding": self.custom_branding,
        }


@dataclass(frozen=True)
class PlanLimits:
    """Resource limits for a plan (None = unlimited)"""

    max_projects: Optional[int] = None
    max_decisions_per_month: Optional[int] = None
    max_team_members: Optional[int] = None
    max_rules: Optional[int] = None
    audit_retention_days: int = 30

    def is_unlimited(self, resource: str) -> bool:
        """Check if a resource is unlimited"""
        value = getattr(self, resource, None)
        return value is None


@dataclass
class SubscriptionPlan:
    """
    Subscription Plan Entity

    Immutable definition of pricing and limits.
    """

    plan_id: str  # "free", "starter", "pro", "enterprise"
    name: str

    # Pricing
    price_cents: int
    currency: str = "IDR"
    billing_interval: str = "month"  # "month" or "year"

    # Limits
    limits: PlanLimits = field(default_factory=PlanLimits)

    # Features
    features: PlanFeatures = field(default_factory=PlanFeatures)

    # Trial
    trial_days: int = 0

    # Status
    is_active: bool = True
    display_order: int = 0

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_free(self) -> bool:
        return self.price_cents == 0

    @property
    def is_paid(self) -> bool:
        return self.price_cents > 0

    @property
    def has_trial(self) -> bool:
        return self.trial_days > 0

    @property
    def price_display(self) -> str:
        """Human-readable price"""
        if self.is_free:
            return "Free"
        # IDR uses no decimal places
        amount = self.price_cents // 100
        return f"Rp {amount:,}/{self.billing_interval}"

    def is_upgrade_from(self, other: "SubscriptionPlan") -> bool:
        """Check if this plan is an upgrade from another"""
        return self.price_cents > other.price_cents

    def is_downgrade_from(self, other: "SubscriptionPlan") -> bool:
        """Check if this plan is a downgrade from another"""
        return self.price_cents < other.price_cents

    def check_limit(self, resource: str, current_usage: int) -> bool:
        """Check if usage is within limit"""
        limit = getattr(self.limits, resource, None)
        if limit is None:
            return True  # Unlimited
        return current_usage < limit

    def get_limit(self, resource: str) -> Optional[int]:
        """Get the limit for a resource"""
        return getattr(self.limits, resource, None)

    # Plan hierarchy for comparison
    PLAN_TIERS = {
        "free": 0,
        "starter": 1,
        "pro": 2,
        "enterprise": 3,
    }

    @property
    def tier(self) -> int:
        return self.PLAN_TIERS.get(self.plan_id, 0)
