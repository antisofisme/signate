"""
Product Module

Product catalog and subscription management for PUGUH platform.
"""

from .domain import (
    Product,
    ProductStatus,
    ProductFeatures,
    ProductSubscription,
    ProductSubscriptionStatus,
    MANTRA_PRODUCT,
)
from .interfaces import (
    IProductRepository,
    IProductSubscriptionRepository,
)
from .adapters import (
    PostgresProductRepository,
    PostgresProductSubscriptionRepository,
)
from .use_cases import (
    ListProductsUseCase,
    ListProductsResult,
    GetProductUseCase,
    ProductWithSubscription,
    CheckProductAccessUseCase,
    ProductAccessResult,
)
from .exceptions import (
    ProductError,
    ProductNotFoundError,
    ProductAccessDeniedError,
    ProductSubscriptionExistsError,
    ProductNotAvailableError,
    UsageLimitExceededError,
)

__all__ = [
    # Domain
    "Product",
    "ProductStatus",
    "ProductFeatures",
    "ProductSubscription",
    "ProductSubscriptionStatus",
    "MANTRA_PRODUCT",
    # Interfaces
    "IProductRepository",
    "IProductSubscriptionRepository",
    # Adapters
    "PostgresProductRepository",
    "PostgresProductSubscriptionRepository",
    # Use Cases
    "ListProductsUseCase",
    "ListProductsResult",
    "GetProductUseCase",
    "ProductWithSubscription",
    "CheckProductAccessUseCase",
    "ProductAccessResult",
    # Exceptions
    "ProductError",
    "ProductNotFoundError",
    "ProductAccessDeniedError",
    "ProductSubscriptionExistsError",
    "ProductNotAvailableError",
    "UsageLimitExceededError",
]
