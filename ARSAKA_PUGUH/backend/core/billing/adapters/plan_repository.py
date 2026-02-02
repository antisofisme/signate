"""
Plan Repository PostgreSQL Implementation
"""

from typing import List, Optional, Callable
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import IPlanRepository
from ..domain import SubscriptionPlan, PlanFeatures, PlanLimits


class PostgresPlanRepository(IPlanRepository):
    """PostgreSQL implementation of plan repository"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    @asynccontextmanager
    async def _session(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    def _row_to_plan(self, row) -> SubscriptionPlan:
        """Convert database row to domain entity"""
        features_dict = row.features if isinstance(row.features, dict) else {}

        return SubscriptionPlan(
            plan_id=row.plan_id,
            name=row.name,
            price_cents=row.price_cents,
            currency=row.currency,
            billing_interval=row.billing_interval,
            limits=PlanLimits(
                max_projects=row.max_projects,
                max_decisions_per_month=row.max_decisions_per_month,
                max_team_members=row.max_team_members,
                max_rules=row.max_rules,
                audit_retention_days=row.audit_retention_days,
            ),
            features=PlanFeatures.from_dict(features_dict),
            trial_days=row.trial_days,
            is_active=row.is_active,
            display_order=row.display_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get plan by ID"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscription_plans WHERE plan_id = :plan_id"),
                {"plan_id": plan_id},
            )
            row = result.first()
            if row:
                return self._row_to_plan(row)
            return None

    async def list_active(self) -> List[SubscriptionPlan]:
        """List all active plans (for pricing page)"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscription_plans WHERE is_active = TRUE ORDER BY display_order"),
            )
            return [self._row_to_plan(row) for row in result.fetchall()]

    async def list_all(self) -> List[SubscriptionPlan]:
        """List all plans including inactive"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM subscription_plans ORDER BY display_order"),
            )
            return [self._row_to_plan(row) for row in result.fetchall()]


class InMemoryPlanRepository(IPlanRepository):
    """
    In-memory plan repository for testing and development.

    Plans are hardcoded since they rarely change.
    """

    def __init__(self):
        self._plans = {
            "free": SubscriptionPlan(
                plan_id="free",
                name="Free",
                price_cents=0,
                limits=PlanLimits(
                    max_projects=1,
                    max_decisions_per_month=1000,
                    max_team_members=3,
                    max_rules=10,
                    audit_retention_days=30,
                ),
                features=PlanFeatures(api_access=False, sso=False),
                trial_days=0,
                display_order=1,
            ),
            "starter": SubscriptionPlan(
                plan_id="starter",
                name="Starter",
                price_cents=29000000,  # Rp 290,000 in cents
                limits=PlanLimits(
                    max_projects=5,
                    max_decisions_per_month=10000,
                    max_team_members=10,
                    max_rules=50,
                    audit_retention_days=90,
                ),
                features=PlanFeatures(api_access=True, sso=False),
                trial_days=14,
                display_order=2,
            ),
            "pro": SubscriptionPlan(
                plan_id="pro",
                name="Pro",
                price_cents=99000000,  # Rp 990,000 in cents
                limits=PlanLimits(
                    max_projects=None,  # Unlimited
                    max_decisions_per_month=100000,
                    max_team_members=50,
                    max_rules=None,  # Unlimited
                    audit_retention_days=365,
                ),
                features=PlanFeatures(
                    api_access=True,
                    sso=False,
                    priority_support=True,
                    sla_guarantee=True,
                ),
                trial_days=14,
                display_order=3,
            ),
            "enterprise": SubscriptionPlan(
                plan_id="enterprise",
                name="Enterprise",
                price_cents=0,  # Custom pricing
                limits=PlanLimits(
                    max_projects=None,
                    max_decisions_per_month=None,
                    max_rules=None,
                    max_team_members=None,
                    audit_retention_days=730,
                ),
                features=PlanFeatures(
                    api_access=True,
                    sso=True,
                    priority_support=True,
                    dedicated_support=True,
                    sla_guarantee=True,
                    custom_branding=True,
                ),
                trial_days=0,
                display_order=4,
            ),
        }

    async def get_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        return self._plans.get(plan_id)

    async def list_active(self) -> List[SubscriptionPlan]:
        return sorted(
            [p for p in self._plans.values() if p.is_active],
            key=lambda p: p.display_order,
        )

    async def list_all(self) -> List[SubscriptionPlan]:
        return sorted(self._plans.values(), key=lambda p: p.display_order)
