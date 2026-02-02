"""
Product API Routes

FastAPI router for product catalog endpoints.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from ..use_cases import (
    ListProductsUseCase,
    GetProductUseCase,
    CheckProductAccessUseCase,
)
from ..exceptions import ProductNotFoundError, ProductAccessDeniedError
from .schemas import (
    ListProductsResponse,
    ListProductsData,
    GetProductResponse,
    ProductAccessResponse,
    ProductAccessData,
    ListSubscriptionsResponse,
    ListSubscriptionsData,
    ProductWithSubscription,
    ProductInfo,
    ProductFeatures,
    SubscriptionInfo,
    ProductErrorResponse,
)
from .dependencies import (
    get_list_products_use_case,
    get_product_use_case,
    get_check_access_use_case,
    get_current_user_optional,
    get_current_user,
)
from ...auth.interfaces.token_service import TokenPayload


router = APIRouter(prefix="/products", tags=["products"])


# ============================================================================
# List Products
# ============================================================================

@router.get(
    "",
    response_model=ListProductsResponse,
    summary="List Products",
    description="List all available products with subscription status for the current tenant.",
)
async def list_products(
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
    use_case: ListProductsUseCase = Depends(get_list_products_use_case),
):
    """List all products."""
    tenant_id = None
    if current_user and current_user.active_tenant_id:
        tenant_id = UUID(current_user.active_tenant_id)

    result = await use_case.execute(tenant_id=tenant_id)

    products = [
        ProductWithSubscription(
            product=ProductInfo(
                product_id=str(p.product.product_id),
                code=p.product.code,
                name=p.product.name,
                description=p.product.description,
                tagline=p.product.tagline,
                icon_url=p.product.icon_url,
                logo_url=p.product.logo_url,
                color_primary=p.product.color_primary,
                app_url=p.product.app_url,
                docs_url=p.product.docs_url,
                status=p.product.status.value,
                is_featured=p.product.is_featured,
                features=ProductFeatures(**p.product.features.to_dict()),
                display_order=p.product.display_order,
            ),
            is_subscribed=p.is_subscribed,
            subscription_status=p.subscription_status,
            plan_id=p.plan_id,
            trial_days_remaining=p.trial_days_remaining,
        )
        for p in result.products
    ]

    return ListProductsResponse(
        data=ListProductsData(
            products=products,
            subscribed_count=result.subscribed_count,
            total_count=result.total_count,
        )
    )


# ============================================================================
# Get Product
# ============================================================================

@router.get(
    "/{product_code}",
    response_model=GetProductResponse,
    responses={
        404: {"model": ProductErrorResponse, "description": "Product not found"},
    },
    summary="Get Product",
    description="Get a specific product by code with subscription status.",
)
async def get_product(
    product_code: str,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
    use_case: GetProductUseCase = Depends(get_product_use_case),
):
    """Get product by code."""
    tenant_id = None
    if current_user and current_user.active_tenant_id:
        tenant_id = UUID(current_user.active_tenant_id)

    result = await use_case.execute(
        product_code=product_code.lower(),
        tenant_id=tenant_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PRODUCT_NOT_FOUND",
                "message": f"Product '{product_code}' not found",
            }
        )

    return GetProductResponse(
        data=ProductWithSubscription(
            product=ProductInfo(
                product_id=str(result.product.product_id),
                code=result.product.code,
                name=result.product.name,
                description=result.product.description,
                tagline=result.product.tagline,
                icon_url=result.product.icon_url,
                logo_url=result.product.logo_url,
                color_primary=result.product.color_primary,
                app_url=result.product.app_url,
                docs_url=result.product.docs_url,
                status=result.product.status.value,
                is_featured=result.product.is_featured,
                features=ProductFeatures(**result.product.features.to_dict()),
                display_order=result.product.display_order,
            ),
            is_subscribed=result.is_subscribed,
            subscription_status=result.subscription_status,
            plan_id=result.plan_id,
            trial_days_remaining=result.trial_days_remaining,
        )
    )


# ============================================================================
# Check Product Access
# ============================================================================

@router.get(
    "/{product_code}/access",
    response_model=ProductAccessResponse,
    responses={
        401: {"model": ProductErrorResponse, "description": "Authentication required"},
    },
    summary="Check Product Access",
    description="Check if the current tenant has access to a product.",
)
async def check_product_access(
    product_code: str,
    current_user: TokenPayload = Depends(get_current_user),
    use_case: CheckProductAccessUseCase = Depends(get_check_access_use_case),
):
    """Check if tenant has access to product."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    result = await use_case.execute(
        tenant_id=UUID(current_user.active_tenant_id),
        product_code=product_code.lower(),
    )

    return ProductAccessResponse(
        data=ProductAccessData(
            has_access=result.has_access,
            product_code=result.product_code,
            plan_id=result.plan_id,
            status=result.status,
            is_trial=result.is_trial,
            trial_days_remaining=result.trial_days_remaining,
            usage_this_period=result.usage_this_period,
            usage_limit=result.usage_limit,
            reason=result.reason,
        )
    )


# ============================================================================
# Tenant's Subscriptions
# ============================================================================

@router.get(
    "/subscriptions/my",
    response_model=ListSubscriptionsResponse,
    responses={
        401: {"model": ProductErrorResponse, "description": "Authentication required"},
    },
    summary="List My Subscriptions",
    description="List all product subscriptions for the current tenant.",
)
async def list_my_subscriptions(
    current_user: TokenPayload = Depends(get_current_user),
    use_case: ListProductsUseCase = Depends(get_list_products_use_case),
):
    """List tenant's subscriptions."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    result = await use_case.execute(
        tenant_id=UUID(current_user.active_tenant_id),
    )

    # Filter to only subscribed products
    subscriptions = [
        SubscriptionInfo(
            subscription_id="",  # Would need to add to ProductWithSubscription
            product_id=str(p.product.product_id),
            product_code=p.product.code,
            plan_id=p.plan_id or "free",
            status=p.subscription_status or "active",
            is_trial=p.trial_days_remaining > 0,
            trial_days_remaining=p.trial_days_remaining,
            usage_this_period=0,  # Would need to add to ProductWithSubscription
            usage_limit=None,
            created_at="",  # Would need to add to ProductWithSubscription
        )
        for p in result.products
        if p.is_subscribed
    ]

    return ListSubscriptionsResponse(
        data=ListSubscriptionsData(
            subscriptions=subscriptions,
            total=len(subscriptions),
        )
    )
