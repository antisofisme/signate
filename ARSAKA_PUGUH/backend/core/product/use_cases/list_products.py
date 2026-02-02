"""
List Products Use Case

Lists available products with subscription status for a tenant.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from ..interfaces.product_repository import IProductRepository
from ..interfaces.product_subscription_repository import IProductSubscriptionRepository
from ..domain.product import Product


@dataclass
class ProductWithSubscription:
    """Product with subscription status."""
    product: Product
    is_subscribed: bool
    subscription_status: Optional[str]  # 'active', 'trialing', etc.
    plan_id: Optional[str]
    trial_days_remaining: int


@dataclass
class ListProductsResult:
    """List products result."""
    products: List[ProductWithSubscription]
    subscribed_count: int
    total_count: int


class ListProductsUseCase:
    """List available products with subscription status."""

    def __init__(
        self,
        product_repo: IProductRepository,
        subscription_repo: IProductSubscriptionRepository,
    ):
        self._products = product_repo
        self._subscriptions = subscription_repo

    async def execute(
        self,
        tenant_id: Optional[UUID] = None,
        include_coming_soon: bool = True,
    ) -> ListProductsResult:
        """List products with subscription status.

        Args:
            tenant_id: Tenant to check subscription status (optional)
            include_coming_soon: Include coming soon products

        Returns:
            ListProductsResult with products and subscription info
        """
        # 1. Get all visible products
        products = await self._products.list_active()

        # 2. If no tenant, return products without subscription status
        if not tenant_id:
            return ListProductsResult(
                products=[
                    ProductWithSubscription(
                        product=p,
                        is_subscribed=False,
                        subscription_status=None,
                        plan_id=None,
                        trial_days_remaining=0,
                    )
                    for p in products
                ],
                subscribed_count=0,
                total_count=len(products),
            )

        # 3. Get tenant's subscriptions
        subscriptions = await self._subscriptions.list_by_tenant(tenant_id)
        sub_by_product = {sub.product_id: sub for sub in subscriptions}

        # 4. Combine products with subscription status
        result_products = []
        subscribed_count = 0

        for product in products:
            sub = sub_by_product.get(product.product_id)
            is_subscribed = sub is not None and sub.is_active

            if is_subscribed:
                subscribed_count += 1

            result_products.append(ProductWithSubscription(
                product=product,
                is_subscribed=is_subscribed,
                subscription_status=sub.status.value if sub else None,
                plan_id=sub.plan_id if sub else None,
                trial_days_remaining=sub.trial_days_remaining if sub else 0,
            ))

        return ListProductsResult(
            products=result_products,
            subscribed_count=subscribed_count,
            total_count=len(products),
        )


class GetProductUseCase:
    """Get a single product with subscription status."""

    def __init__(
        self,
        product_repo: IProductRepository,
        subscription_repo: IProductSubscriptionRepository,
    ):
        self._products = product_repo
        self._subscriptions = subscription_repo

    async def execute(
        self,
        product_code: str,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[ProductWithSubscription]:
        """Get product by code with subscription status.

        Args:
            product_code: Product code
            tenant_id: Tenant to check subscription status (optional)

        Returns:
            ProductWithSubscription if found, None otherwise
        """
        # 1. Get product
        product = await self._products.get_by_code(product_code)
        if not product:
            return None

        # 2. If no tenant, return product without subscription status
        if not tenant_id:
            return ProductWithSubscription(
                product=product,
                is_subscribed=False,
                subscription_status=None,
                plan_id=None,
                trial_days_remaining=0,
            )

        # 3. Get subscription
        sub = await self._subscriptions.get_by_tenant_and_code(tenant_id, product_code)

        return ProductWithSubscription(
            product=product,
            is_subscribed=sub is not None and sub.is_active,
            subscription_status=sub.status.value if sub else None,
            plan_id=sub.plan_id if sub else None,
            trial_days_remaining=sub.trial_days_remaining if sub else 0,
        )
