"""
Reactivate Subscription Use Case

Reactivates a cancelled subscription (if still within billing period).
"""

from uuid import UUID

from ..interfaces import ISubscriptionRepository
from ..exceptions import SubscriptionNotFoundError, BillingError


class ReactivateSubscriptionUseCase:
    """Reactivate cancelled subscription"""

    def __init__(self, subscription_repo: ISubscriptionRepository):
        self._subscription_repo = subscription_repo

    async def execute(self, tenant_id: UUID) -> None:
        """
        Reactivate subscription.

        Only works if subscription is marked to cancel at period end
        but hasn't been fully cancelled yet.

        Args:
            tenant_id: Tenant UUID

        Raises:
            SubscriptionNotFoundError: If no subscription found
            BillingError: If subscription cannot be reactivated
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            raise SubscriptionNotFoundError(str(tenant_id))

        if subscription.is_cancelled:
            raise BillingError(
                "Subscription is fully cancelled. Create a new checkout to resubscribe.",
                "CANNOT_REACTIVATE",
            )

        if not subscription.cancel_at_period_end:
            raise BillingError(
                "Subscription is not scheduled for cancellation.",
                "NOT_CANCELLED",
            )

        subscription.reactivate()
        await self._subscription_repo.update(subscription)
