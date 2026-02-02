"""
PostgreSQL Product Subscription Repository

Implementation of IProductSubscriptionRepository for PostgreSQL database.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.product_subscription_repository import IProductSubscriptionRepository
from ..domain.product_subscription import ProductSubscription, ProductSubscriptionStatus


class PostgresProductSubscriptionRepository(IProductSubscriptionRepository):
    """PostgreSQL implementation of product subscription repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, subscription_id: UUID) -> Optional[ProductSubscription]:
        """Get subscription by ID."""
        result = await self._session.execute(
            text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE subscription_id = :subscription_id
            """),
            {"subscription_id": str(subscription_id)}
        )
        row = result.fetchone()
        return self._row_to_subscription(row) if row else None

    async def get_by_tenant_and_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
    ) -> Optional[ProductSubscription]:
        """Get subscription by tenant and product."""
        result = await self._session.execute(
            text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                  AND product_id = :product_id
            """),
            {"tenant_id": str(tenant_id), "product_id": str(product_id)}
        )
        row = result.fetchone()
        return self._row_to_subscription(row) if row else None

    async def get_by_tenant_and_code(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> Optional[ProductSubscription]:
        """Get subscription by tenant and product code."""
        result = await self._session.execute(
            text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                  AND product_code = :product_code
            """),
            {"tenant_id": str(tenant_id), "product_code": product_code}
        )
        row = result.fetchone()
        return self._row_to_subscription(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_cancelled: bool = False,
    ) -> List[ProductSubscription]:
        """List all subscriptions for a tenant."""
        if include_cancelled:
            query = text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                ORDER BY created_at
            """)
        else:
            query = text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                  AND status NOT IN ('cancelled', 'expired')
                ORDER BY created_at
            """)

        result = await self._session.execute(query, {"tenant_id": str(tenant_id)})
        return [self._row_to_subscription(row) for row in result.fetchall()]

    async def list_active_by_tenant(
        self,
        tenant_id: UUID,
    ) -> List[ProductSubscription]:
        """List active subscriptions for a tenant."""
        result = await self._session.execute(
            text("""
                SELECT subscription_id, tenant_id, product_id, product_code,
                       plan_id, status, trial_ends_at, is_trial,
                       current_period_start, current_period_end,
                       usage_this_period, usage_limit,
                       cancel_at_period_end, cancelled_at,
                       created_at, updated_at
                FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                  AND status IN ('active', 'trialing')
                ORDER BY created_at
            """),
            {"tenant_id": str(tenant_id)}
        )
        return [self._row_to_subscription(row) for row in result.fetchall()]

    async def create(self, subscription: ProductSubscription) -> ProductSubscription:
        """Create a new subscription."""
        await self._session.execute(
            text("""
                INSERT INTO product_subscriptions (
                    subscription_id, tenant_id, product_id, product_code,
                    plan_id, status, trial_ends_at, is_trial,
                    current_period_start, current_period_end,
                    usage_this_period, usage_limit,
                    cancel_at_period_end, cancelled_at,
                    created_at, updated_at
                ) VALUES (
                    :subscription_id, :tenant_id, :product_id, :product_code,
                    :plan_id, :status, :trial_ends_at, :is_trial,
                    :current_period_start, :current_period_end,
                    :usage_this_period, :usage_limit,
                    :cancel_at_period_end, :cancelled_at,
                    :created_at, :updated_at
                )
            """),
            {
                "subscription_id": str(subscription.subscription_id),
                "tenant_id": str(subscription.tenant_id),
                "product_id": str(subscription.product_id),
                "product_code": subscription.product_code,
                "plan_id": subscription.plan_id,
                "status": subscription.status.value,
                "trial_ends_at": subscription.trial_ends_at,
                "is_trial": subscription.is_trial,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "usage_this_period": subscription.usage_this_period,
                "usage_limit": subscription.usage_limit,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "cancelled_at": subscription.cancelled_at,
                "created_at": subscription.created_at,
                "updated_at": subscription.updated_at,
            }
        )
        await self._session.commit()
        return subscription

    async def update(self, subscription: ProductSubscription) -> ProductSubscription:
        """Update subscription."""
        await self._session.execute(
            text("""
                UPDATE product_subscriptions SET
                    plan_id = :plan_id,
                    status = :status,
                    trial_ends_at = :trial_ends_at,
                    is_trial = :is_trial,
                    current_period_start = :current_period_start,
                    current_period_end = :current_period_end,
                    usage_this_period = :usage_this_period,
                    usage_limit = :usage_limit,
                    cancel_at_period_end = :cancel_at_period_end,
                    cancelled_at = :cancelled_at,
                    updated_at = NOW()
                WHERE subscription_id = :subscription_id
            """),
            {
                "subscription_id": str(subscription.subscription_id),
                "plan_id": subscription.plan_id,
                "status": subscription.status.value,
                "trial_ends_at": subscription.trial_ends_at,
                "is_trial": subscription.is_trial,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "usage_this_period": subscription.usage_this_period,
                "usage_limit": subscription.usage_limit,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "cancelled_at": subscription.cancelled_at,
            }
        )
        await self._session.commit()
        return subscription

    async def increment_usage(
        self,
        subscription_id: UUID,
        amount: int = 1,
    ) -> None:
        """Increment usage counter."""
        await self._session.execute(
            text("""
                UPDATE product_subscriptions SET
                    usage_this_period = usage_this_period + :amount,
                    updated_at = NOW()
                WHERE subscription_id = :subscription_id
            """),
            {"subscription_id": str(subscription_id), "amount": amount}
        )
        await self._session.commit()

    async def reset_usage(self, subscription_id: UUID) -> None:
        """Reset usage counter (for new billing period)."""
        await self._session.execute(
            text("""
                UPDATE product_subscriptions SET
                    usage_this_period = 0,
                    updated_at = NOW()
                WHERE subscription_id = :subscription_id
            """),
            {"subscription_id": str(subscription_id)}
        )
        await self._session.commit()

    async def has_active_subscription(
        self,
        tenant_id: UUID,
        product_code: str,
    ) -> bool:
        """Check if tenant has active subscription to a product."""
        result = await self._session.execute(
            text("""
                SELECT 1 FROM product_subscriptions
                WHERE tenant_id = :tenant_id
                  AND product_code = :product_code
                  AND status IN ('active', 'trialing')
            """),
            {"tenant_id": str(tenant_id), "product_code": product_code}
        )
        return result.scalar() is not None

    def _row_to_subscription(self, row) -> ProductSubscription:
        """Convert database row to ProductSubscription entity."""
        return ProductSubscription(
            subscription_id=UUID(str(row.subscription_id)),
            tenant_id=UUID(str(row.tenant_id)),
            product_id=UUID(str(row.product_id)),
            product_code=row.product_code,
            plan_id=row.plan_id,
            status=ProductSubscriptionStatus(row.status),
            trial_ends_at=row.trial_ends_at,
            is_trial=row.is_trial,
            current_period_start=row.current_period_start,
            current_period_end=row.current_period_end,
            usage_this_period=row.usage_this_period or 0,
            usage_limit=row.usage_limit,
            cancel_at_period_end=row.cancel_at_period_end,
            cancelled_at=row.cancelled_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
