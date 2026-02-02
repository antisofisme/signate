"""
Check Product Access Use Case

Verifies if a tenant has access to a specific product.
Used by product apps to validate subscription.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..interfaces.product_subscription_repository import IProductSubscriptionRepository


@dataclass
class ProductAccessResult:
    """Product access check result."""
    has_access: bool
    product_code: str
    plan_id: Optional[str]
    status: Optional[str]
    is_trial: bool
    trial_days_remaining: int
    usage_this_period: int
    usage_limit: Optional[int]
    reason: Optional[str]  # Why access denied


class CheckProductAccessUseCase:
    """Check if tenant has access to a product."""

    def __init__(
        self,
        subscription_repo: IProductSubscriptionRepository,
    ):
        self._subscriptions = subscription_repo

    async def execute(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> ProductAccessResult:
        """Check product access.

        Args:
            tenant_id: Tenant UUID
            product_code: Product code to check

        Returns:
            ProductAccessResult with access status
        """
        # 1. Get subscription
        sub = await self._subscriptions.get_by_tenant_and_code(
            tenant_id,
            product_code,
        )

        # 2. No subscription
        if not sub:
            return ProductAccessResult(
                has_access=False,
                product_code=product_code,
                plan_id=None,
                status=None,
                is_trial=False,
                trial_days_remaining=0,
                usage_this_period=0,
                usage_limit=None,
                reason="No subscription found. Please subscribe to access this product.",
            )

        # 3. Check access
        if not sub.can_access():
            reason = "Subscription not active."
            if sub.status.value == "cancelled":
                reason = "Subscription has been cancelled."
            elif sub.status.value == "expired":
                reason = "Subscription has expired."
            elif sub.status.value == "suspended":
                reason = "Subscription suspended due to payment issue."
            elif sub.is_trial and sub.trial_days_remaining == 0:
                reason = "Trial period has ended. Please upgrade to continue."

            return ProductAccessResult(
                has_access=False,
                product_code=product_code,
                plan_id=sub.plan_id,
                status=sub.status.value,
                is_trial=sub.is_trial,
                trial_days_remaining=sub.trial_days_remaining,
                usage_this_period=sub.usage_this_period,
                usage_limit=sub.usage_limit,
                reason=reason,
            )

        # 4. Has access
        return ProductAccessResult(
            has_access=True,
            product_code=product_code,
            plan_id=sub.plan_id,
            status=sub.status.value,
            is_trial=sub.is_trial,
            trial_days_remaining=sub.trial_days_remaining,
            usage_this_period=sub.usage_this_period,
            usage_limit=sub.usage_limit,
            reason=None,
        )

    async def execute_strict(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> ProductAccessResult:
        """Check product access and raise exception if denied.

        Args:
            tenant_id: Tenant UUID
            product_code: Product code to check

        Returns:
            ProductAccessResult if access granted

        Raises:
            ProductAccessDeniedError if access denied
        """
        from ..exceptions import ProductAccessDeniedError

        result = await self.execute(tenant_id, product_code)
        if not result.has_access:
            raise ProductAccessDeniedError(product_code, result.reason)

        return result
