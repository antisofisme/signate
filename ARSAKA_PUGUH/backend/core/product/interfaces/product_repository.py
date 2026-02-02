"""
Product Repository Interface

Abstract contract for product data access.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.product import Product


class IProductRepository(ABC):
    """Interface for product data access."""

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]:
        """Get product by code."""
        pass

    @abstractmethod
    async def list_all(
        self,
        include_disabled: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        """List all products."""
        pass

    @abstractmethod
    async def list_active(self) -> List[Product]:
        """List active products available for subscription."""
        pass

    @abstractmethod
    async def list_featured(self) -> List[Product]:
        """List featured products."""
        pass

    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Create a new product."""
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Update product."""
        pass
