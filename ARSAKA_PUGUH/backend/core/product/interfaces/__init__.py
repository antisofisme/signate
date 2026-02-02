"""Product Interfaces - Repository contracts."""

from .product_repository import IProductRepository
from .product_subscription_repository import IProductSubscriptionRepository

__all__ = [
    "IProductRepository",
    "IProductSubscriptionRepository",
]
