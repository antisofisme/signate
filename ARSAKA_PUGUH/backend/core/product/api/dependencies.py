"""
Product API Dependencies

Dependency injection for FastAPI product routers.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.product_repository import IProductRepository
from ..interfaces.product_subscription_repository import IProductSubscriptionRepository
from ..adapters.product_repository import PostgresProductRepository
from ..adapters.product_subscription_repository import PostgresProductSubscriptionRepository
from ..use_cases import (
    ListProductsUseCase,
    GetProductUseCase,
    CheckProductAccessUseCase,
)

# Import auth dependencies
from ...auth.api.dependencies import (
    get_session,
    get_current_user as auth_get_current_user,
    get_current_user_optional as auth_get_current_user_optional,
)
from ...auth.interfaces.token_service import TokenPayload


# ============================================================================
# Re-export auth dependencies
# ============================================================================

async def get_current_user(
    user: TokenPayload = Depends(auth_get_current_user),
) -> TokenPayload:
    """Get current user (required)."""
    return user


async def get_current_user_optional(
    user: Optional[TokenPayload] = Depends(auth_get_current_user_optional),
) -> Optional[TokenPayload]:
    """Get current user (optional)."""
    return user


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_product_repository(
    session: AsyncSession = Depends(get_session)
) -> IProductRepository:
    """Get product repository."""
    return PostgresProductRepository(session)


async def get_product_subscription_repository(
    session: AsyncSession = Depends(get_session)
) -> IProductSubscriptionRepository:
    """Get product subscription repository."""
    return PostgresProductSubscriptionRepository(session)


# ============================================================================
# Use Case Dependencies
# ============================================================================

async def get_list_products_use_case(
    product_repo: IProductRepository = Depends(get_product_repository),
    subscription_repo: IProductSubscriptionRepository = Depends(get_product_subscription_repository),
) -> ListProductsUseCase:
    """Get ListProductsUseCase with injected dependencies."""
    return ListProductsUseCase(
        product_repo=product_repo,
        subscription_repo=subscription_repo,
    )


async def get_product_use_case(
    product_repo: IProductRepository = Depends(get_product_repository),
    subscription_repo: IProductSubscriptionRepository = Depends(get_product_subscription_repository),
) -> GetProductUseCase:
    """Get GetProductUseCase with injected dependencies."""
    return GetProductUseCase(
        product_repo=product_repo,
        subscription_repo=subscription_repo,
    )


async def get_check_access_use_case(
    subscription_repo: IProductSubscriptionRepository = Depends(get_product_subscription_repository),
) -> CheckProductAccessUseCase:
    """Get CheckProductAccessUseCase with injected dependencies."""
    return CheckProductAccessUseCase(
        subscription_repo=subscription_repo,
    )
