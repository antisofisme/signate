"""
Billing Feature Enforcement Service

SECURITY: Enforces subscription plan limits and features at runtime.
Prevents users from accessing features not included in their plan.

Usage:
    enforcement = FeatureEnforcementService(subscription_repo)
    await enforcement.require_feature(tenant_id, "api_access")
    await enforcement.check_usage_limit(tenant_id, "max_decisions_per_month", 100)
"""

from typing import Optional
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..domain.plan import SubscriptionPlan, PlanFeatures, PlanLimits
from ..domain.subscription import Subscription, SubscriptionStatus
from ..interfaces.subscription_repository import ISubscriptionRepository


class FeatureEnforcementError(Exception):
    """Base exception for feature enforcement errors."""

    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class FeatureNotAvailableError(FeatureEnforcementError):
    """Raised when a feature is not available in the current plan."""

    def __init__(self, feature: str, current_plan: str, required_plan: str):
        super().__init__(
            message=f"Feature '{feature}' is not available in your current plan",
            code="FEATURE_NOT_AVAILABLE",
            details={
                "feature": feature,
                "current_plan": current_plan,
                "upgrade_to": required_plan,
                "action": "upgrade",
            }
        )


class UsageLimitExceededError(FeatureEnforcementError):
    """Raised when usage limit is exceeded."""

    def __init__(self, resource: str, current: int, limit: int, plan: str):
        super().__init__(
            message=f"You have reached your {resource} limit",
            code="USAGE_LIMIT_EXCEEDED",
            details={
                "resource": resource,
                "current_usage": current,
                "limit": limit,
                "current_plan": plan,
                "action": "upgrade",
            }
        )


class SubscriptionRequiredError(FeatureEnforcementError):
    """Raised when no active subscription exists."""

    def __init__(self, tenant_id: str):
        super().__init__(
            message="An active subscription is required to access this feature",
            code="SUBSCRIPTION_REQUIRED",
            details={
                "tenant_id": tenant_id,
                "action": "subscribe",
            }
        )


class SubscriptionExpiredError(FeatureEnforcementError):
    """Raised when subscription has expired."""

    def __init__(self, plan: str, expired_at: str):
        super().__init__(
            message="Your subscription has expired",
            code="SUBSCRIPTION_EXPIRED",
            details={
                "plan": plan,
                "expired_at": expired_at,
                "action": "renew",
            }
        )


@dataclass
class FeatureCheckResult:
    """Result of a feature check."""

    allowed: bool
    feature: str
    current_plan: Optional[str] = None
    required_plan: Optional[str] = None
    message: Optional[str] = None


@dataclass
class UsageCheckResult:
    """Result of a usage limit check."""

    allowed: bool
    resource: str
    current_usage: int
    limit: Optional[int]
    remaining: Optional[int]
    percentage: float
    is_unlimited: bool
    message: Optional[str] = None


class FeatureEnforcementService:
    """
    Service for enforcing billing features and limits.

    SECURITY: This service is critical for preventing unauthorized feature access.
    It should be called before any feature-gated operation.
    """

    # Feature to minimum plan mapping
    FEATURE_PLANS = {
        "api_access": "starter",
        "sso": "pro",
        "priority_support": "pro",
        "dedicated_support": "enterprise",
        "sla_guarantee": "enterprise",
        "custom_branding": "enterprise",
    }

    def __init__(self, subscription_repo: ISubscriptionRepository):
        self._subscription_repo = subscription_repo

    async def get_subscription_with_plan(
        self, tenant_id: UUID
    ) -> tuple[Subscription, SubscriptionPlan]:
        """Get subscription and plan for tenant.

        Raises SubscriptionRequiredError if no subscription exists.
        """
        result = await self._subscription_repo.get_with_plan(tenant_id)
        if not result:
            raise SubscriptionRequiredError(str(tenant_id))

        subscription, plan = result
        return subscription, plan

    async def check_subscription_active(self, tenant_id: UUID) -> None:
        """Check if subscription is active.

        Raises appropriate error if subscription is expired or cancelled.
        """
        subscription, plan = await self.get_subscription_with_plan(tenant_id)

        # Check if subscription period has ended (expired)
        if (
            subscription.current_period_end is not None
            and subscription.current_period_end < datetime.utcnow()
            and subscription.status not in (
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.ACTIVE,
            )
        ):
            raise SubscriptionExpiredError(
                plan=plan.plan_id,
                expired_at=str(subscription.current_period_end),
            )

        if subscription.status == SubscriptionStatus.CANCELLED:
            raise SubscriptionRequiredError(str(tenant_id))

        # Allow trialing, active, and past_due (grace period)
        if not subscription.status.is_usable:
            raise SubscriptionRequiredError(str(tenant_id))

    async def check_feature(
        self, tenant_id: UUID, feature: str
    ) -> FeatureCheckResult:
        """Check if a feature is available for the tenant.

        Returns FeatureCheckResult indicating if feature is allowed.
        Does NOT raise exception - use require_feature for that.
        """
        try:
            subscription, plan = await self.get_subscription_with_plan(tenant_id)
        except SubscriptionRequiredError:
            return FeatureCheckResult(
                allowed=False,
                feature=feature,
                message="No subscription found",
            )

        # Check if feature exists in plan features
        feature_value = getattr(plan.features, feature, None)
        if feature_value is None:
            return FeatureCheckResult(
                allowed=False,
                feature=feature,
                current_plan=plan.plan_id,
                message=f"Unknown feature: {feature}",
            )

        if feature_value:
            return FeatureCheckResult(
                allowed=True,
                feature=feature,
                current_plan=plan.plan_id,
            )
        else:
            return FeatureCheckResult(
                allowed=False,
                feature=feature,
                current_plan=plan.plan_id,
                required_plan=self.FEATURE_PLANS.get(feature, "pro"),
                message=f"Feature '{feature}' requires upgrade",
            )

    async def require_feature(self, tenant_id: UUID, feature: str) -> None:
        """Require that a feature is available.

        Raises FeatureNotAvailableError if feature is not in plan.

        Usage:
            @router.post("/api-keys")
            async def create_api_key(...):
                await enforcement.require_feature(tenant_id, "api_access")
                # ... proceed with creating API key
        """
        result = await self.check_feature(tenant_id, feature)
        if not result.allowed:
            raise FeatureNotAvailableError(
                feature=feature,
                current_plan=result.current_plan or "none",
                required_plan=result.required_plan or "pro",
            )

    async def check_usage(
        self, tenant_id: UUID, resource: str, current_usage: int
    ) -> UsageCheckResult:
        """Check if current usage is within limits.

        Returns UsageCheckResult indicating if more usage is allowed.
        """
        try:
            subscription, plan = await self.get_subscription_with_plan(tenant_id)
        except SubscriptionRequiredError:
            return UsageCheckResult(
                allowed=False,
                resource=resource,
                current_usage=current_usage,
                limit=0,
                remaining=0,
                percentage=100.0,
                is_unlimited=False,
                message="No subscription found",
            )

        limit = plan.get_limit(resource)

        if limit is None:
            # Unlimited
            return UsageCheckResult(
                allowed=True,
                resource=resource,
                current_usage=current_usage,
                limit=None,
                remaining=None,
                percentage=0.0,
                is_unlimited=True,
            )

        remaining = max(0, limit - current_usage)
        percentage = (current_usage / limit * 100) if limit > 0 else 100.0

        return UsageCheckResult(
            allowed=current_usage < limit,
            resource=resource,
            current_usage=current_usage,
            limit=limit,
            remaining=remaining,
            percentage=percentage,
            is_unlimited=False,
        )

    async def require_usage_limit(
        self, tenant_id: UUID, resource: str, current_usage: int
    ) -> None:
        """Require that usage is within limits.

        Raises UsageLimitExceededError if limit is exceeded.

        Usage:
            @router.post("/decisions")
            async def create_decision(...):
                await enforcement.require_usage_limit(
                    tenant_id, "max_decisions_per_month", decisions_this_month
                )
                # ... proceed with creating decision
        """
        result = await self.check_usage(tenant_id, resource, current_usage)
        if not result.allowed:
            subscription, plan = await self.get_subscription_with_plan(tenant_id)
            raise UsageLimitExceededError(
                resource=resource,
                current=current_usage,
                limit=result.limit or 0,
                plan=plan.plan_id,
            )

    async def get_limits_status(
        self, tenant_id: UUID, usage_counts: dict[str, int]
    ) -> dict[str, UsageCheckResult]:
        """Get status of all limits for a tenant.

        Args:
            tenant_id: The tenant to check
            usage_counts: Dict mapping resource names to current counts

        Returns:
            Dict mapping resource names to UsageCheckResult
        """
        results = {}
        for resource, count in usage_counts.items():
            results[resource] = await self.check_usage(tenant_id, resource, count)
        return results

    async def get_available_features(self, tenant_id: UUID) -> dict[str, bool]:
        """Get all feature flags for a tenant's current plan.

        Returns dict mapping feature names to availability.
        """
        try:
            subscription, plan = await self.get_subscription_with_plan(tenant_id)
            return plan.features.to_dict()
        except SubscriptionRequiredError:
            # No subscription = no features
            return {
                "api_access": False,
                "sso": False,
                "priority_support": False,
                "dedicated_support": False,
                "sla_guarantee": False,
                "custom_branding": False,
            }
