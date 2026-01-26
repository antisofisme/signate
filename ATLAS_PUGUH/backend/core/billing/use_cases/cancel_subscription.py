"""
Cancel Subscription Use Case

Cancels subscription at period end or immediately.
"""

from uuid import UUID

from ..interfaces import ISubscriptionRepository
from ..exceptions import SubscriptionNotFoundError, SubscriptionAlreadyCancelledError


class CancelSubscriptionUseCase:
    """Cancel subscription"""

    def __init__(self, subscription_repo: ISubscriptionRepository):
        self._subscription_repo = subscription_repo

    async def execute(
        self,
        tenant_id: UUID,
        reason: str = None,
        immediate: bool = False,
    ) -> None:
        """
        Cancel subscription.

        By default, cancels at end of current billing period.
        Use immediate=True to cancel right away (no refund).

        Args:
            tenant_id: Tenant UUID
            reason: Optional cancellation reason
            immediate: If True, cancel immediately

        Raises:
            SubscriptionNotFoundError: If no subscription found
            SubscriptionAlreadyCancelledError: If already cancelled
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            raise SubscriptionNotFoundError(str(tenant_id))

        if subscription.is_cancelled:
            raise SubscriptionAlreadyCancelledError()

        if subscription.cancel_at_period_end and not immediate:
            # Already scheduled to cancel
            raise SubscriptionAlreadyCancelledError()

        subscription.cancel(reason=reason, immediate=immediate)
        await self._subscription_repo.update(subscription)
