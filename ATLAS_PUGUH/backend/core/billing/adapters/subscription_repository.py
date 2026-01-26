"""
Subscription Repository PostgreSQL Implementation
"""

from typing import Optional, List, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import ISubscriptionRepository
from ..domain import Subscription, SubscriptionStatus


class PostgresSubscriptionRepository(ISubscriptionRepository):
    """PostgreSQL implementation of subscription repository"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    @asynccontextmanager
    async def _session(self):
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def _row_to_subscription(self, row) -> Subscription:
        """Convert database row to domain entity"""
        return Subscription(
            subscription_id=row.subscription_id,
            tenant_id=row.tenant_id,
            plan_id=row.plan_id,
            status=SubscriptionStatus(row.status),
            payment_provider=row.payment_provider,
            provider_subscription_id=row.provider_subscription_id,
            current_period_start=row.current_period_start,
            current_period_end=row.current_period_end,
            trial_end_at=row.trial_end_at,
            cancel_at_period_end=row.cancel_at_period_end,
            cancelled_at=row.cancelled_at,
            cancellation_reason=row.cancellation_reason,
            decisions_this_month=row.decisions_this_month,
            usage_reset_at=row.usage_reset_at,
            scheduled_plan_id=row.scheduled_plan_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscriptions WHERE subscription_id = :id"),
                {"id": str(subscription_id)},
            )
            row = result.first()
            if row:
                return self._row_to_subscription(row)
            return None

    async def get_by_tenant(self, tenant_id: UUID) -> Optional[Subscription]:
        """Get subscription for a tenant"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscriptions WHERE tenant_id = :tenant_id"),
                {"tenant_id": str(tenant_id)},
            )
            row = result.first()
            if row:
                return self._row_to_subscription(row)
            return None

    async def create(self, subscription: Subscription) -> Subscription:
        """Create a new subscription"""
        async with self._session() as session:
            await session.execute(
                text("""
                    INSERT INTO subscriptions (
                        subscription_id, tenant_id, plan_id, status,
                        payment_provider, provider_subscription_id,
                        current_period_start, current_period_end,
                        trial_end_at, cancel_at_period_end,
                        decisions_this_month, usage_reset_at,
                        scheduled_plan_id
                    ) VALUES (
                        :subscription_id, :tenant_id, :plan_id, :status,
                        :payment_provider, :provider_subscription_id,
                        :current_period_start, :current_period_end,
                        :trial_end_at, :cancel_at_period_end,
                        :decisions_this_month, :usage_reset_at,
                        :scheduled_plan_id
                    )
                """),
                {
                    "subscription_id": str(subscription.subscription_id),
                    "tenant_id": str(subscription.tenant_id),
                    "plan_id": subscription.plan_id,
                    "status": subscription.status.value,
                    "payment_provider": subscription.payment_provider,
                    "provider_subscription_id": subscription.provider_subscription_id,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "trial_end_at": subscription.trial_end_at,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "decisions_this_month": subscription.decisions_this_month,
                    "usage_reset_at": subscription.usage_reset_at,
                    "scheduled_plan_id": subscription.scheduled_plan_id,
                },
            )
            return subscription

    async def update(self, subscription: Subscription) -> Subscription:
        """Update an existing subscription"""
        async with self._session() as session:
            await session.execute(
                text("""
                    UPDATE subscriptions SET
                        plan_id = :plan_id,
                        status = :status,
                        payment_provider = :payment_provider,
                        provider_subscription_id = :provider_subscription_id,
                        current_period_start = :current_period_start,
                        current_period_end = :current_period_end,
                        trial_end_at = :trial_end_at,
                        cancel_at_period_end = :cancel_at_period_end,
                        cancelled_at = :cancelled_at,
                        cancellation_reason = :cancellation_reason,
                        decisions_this_month = :decisions_this_month,
                        usage_reset_at = :usage_reset_at,
                        scheduled_plan_id = :scheduled_plan_id,
                        updated_at = NOW()
                    WHERE subscription_id = :subscription_id
                """),
                {
                    "subscription_id": str(subscription.subscription_id),
                    "plan_id": subscription.plan_id,
                    "status": subscription.status.value,
                    "payment_provider": subscription.payment_provider,
                    "provider_subscription_id": subscription.provider_subscription_id,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "trial_end_at": subscription.trial_end_at,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "cancelled_at": subscription.cancelled_at,
                    "cancellation_reason": subscription.cancellation_reason,
                    "decisions_this_month": subscription.decisions_this_month,
                    "usage_reset_at": subscription.usage_reset_at,
                    "scheduled_plan_id": subscription.scheduled_plan_id,
                },
            )
            return subscription

    async def delete(self, subscription_id: UUID) -> bool:
        """Delete a subscription"""
        async with self._session() as session:
            result = await session.execute(
                text("DELETE FROM subscriptions WHERE subscription_id = :id"),
                {"id": str(subscription_id)},
            )
            return result.rowcount > 0

    async def list_expiring_soon(self, days: int = 7) -> List[Subscription]:
        """List subscriptions expiring within N days"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM subscriptions
                    WHERE status = 'active'
                    AND current_period_end BETWEEN NOW() AND NOW() + INTERVAL ':days days'
                    ORDER BY current_period_end
                """),
                {"days": days},
            )
            return [self._row_to_subscription(row) for row in result.fetchall()]

    async def list_past_due(self) -> List[Subscription]:
        """List all past due subscriptions"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscriptions WHERE status = 'past_due'"),
            )
            return [self._row_to_subscription(row) for row in result.fetchall()]

    async def list_needing_usage_reset(self) -> List[Subscription]:
        """List subscriptions needing monthly usage reset"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM subscriptions
                    WHERE usage_reset_at < NOW() - INTERVAL '1 month'
                """),
            )
            return [self._row_to_subscription(row) for row in result.fetchall()]

    async def increment_usage(self, tenant_id: UUID) -> int:
        """Increment decision count, return new value"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    UPDATE subscriptions
                    SET decisions_this_month = decisions_this_month + 1,
                        updated_at = NOW()
                    WHERE tenant_id = :tenant_id
                    RETURNING decisions_this_month
                """),
                {"tenant_id": str(tenant_id)},
            )
            row = result.first()
            return row.decisions_this_month if row else 0
