"""
PostgreSQL Product Repository

Implementation of IProductRepository for PostgreSQL database.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.product_repository import IProductRepository
from ..domain.product import Product, ProductStatus, ProductFeatures


class PostgresProductRepository(IProductRepository):
    """PostgreSQL implementation of product repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        result = await self._session.execute(
            text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                WHERE product_id = :product_id
            """),
            {"product_id": str(product_id)}
        )
        row = result.fetchone()
        return self._row_to_product(row) if row else None

    async def get_by_code(self, code: str) -> Optional[Product]:
        """Get product by code."""
        result = await self._session.execute(
            text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                WHERE code = :code
            """),
            {"code": code.lower()}
        )
        row = result.fetchone()
        return self._row_to_product(row) if row else None

    async def list_all(
        self,
        include_disabled: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        """List all products."""
        if include_disabled:
            query = text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                ORDER BY display_order, name
                LIMIT :limit OFFSET :offset
            """)
        else:
            query = text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                WHERE status != 'disabled'
                ORDER BY display_order, name
                LIMIT :limit OFFSET :offset
            """)

        result = await self._session.execute(
            query,
            {"limit": limit, "offset": offset}
        )
        return [self._row_to_product(row) for row in result.fetchall()]

    async def list_active(self) -> List[Product]:
        """List active products available for subscription."""
        result = await self._session.execute(
            text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                WHERE status IN ('active', 'beta')
                ORDER BY display_order, name
            """)
        )
        return [self._row_to_product(row) for row in result.fetchall()]

    async def list_featured(self) -> List[Product]:
        """List featured products."""
        result = await self._session.execute(
            text("""
                SELECT product_id, code, name, description, tagline,
                       icon_url, logo_url, color_primary, color_secondary,
                       app_url, docs_url, support_url,
                       status, is_featured, features, display_order,
                       created_at, updated_at
                FROM products
                WHERE is_featured = true
                  AND status IN ('active', 'beta')
                ORDER BY display_order, name
            """)
        )
        return [self._row_to_product(row) for row in result.fetchall()]

    async def create(self, product: Product) -> Product:
        """Create a new product."""
        await self._session.execute(
            text("""
                INSERT INTO products (
                    product_id, code, name, description, tagline,
                    icon_url, logo_url, color_primary, color_secondary,
                    app_url, docs_url, support_url,
                    status, is_featured, features, display_order,
                    created_at, updated_at
                ) VALUES (
                    :product_id, :code, :name, :description, :tagline,
                    :icon_url, :logo_url, :color_primary, :color_secondary,
                    :app_url, :docs_url, :support_url,
                    :status, :is_featured, :features, :display_order,
                    :created_at, :updated_at
                )
            """),
            {
                "product_id": str(product.product_id),
                "code": product.code,
                "name": product.name,
                "description": product.description,
                "tagline": product.tagline,
                "icon_url": product.icon_url,
                "logo_url": product.logo_url,
                "color_primary": product.color_primary,
                "color_secondary": product.color_secondary,
                "app_url": product.app_url,
                "docs_url": product.docs_url,
                "support_url": product.support_url,
                "status": product.status.value,
                "is_featured": product.is_featured,
                "features": product.features.to_dict(),
                "display_order": product.display_order,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            }
        )
        await self._session.commit()
        return product

    async def update(self, product: Product) -> Product:
        """Update product."""
        await self._session.execute(
            text("""
                UPDATE products SET
                    name = :name,
                    description = :description,
                    tagline = :tagline,
                    icon_url = :icon_url,
                    logo_url = :logo_url,
                    color_primary = :color_primary,
                    color_secondary = :color_secondary,
                    app_url = :app_url,
                    docs_url = :docs_url,
                    support_url = :support_url,
                    status = :status,
                    is_featured = :is_featured,
                    features = :features,
                    display_order = :display_order,
                    updated_at = NOW()
                WHERE product_id = :product_id
            """),
            {
                "product_id": str(product.product_id),
                "name": product.name,
                "description": product.description,
                "tagline": product.tagline,
                "icon_url": product.icon_url,
                "logo_url": product.logo_url,
                "color_primary": product.color_primary,
                "color_secondary": product.color_secondary,
                "app_url": product.app_url,
                "docs_url": product.docs_url,
                "support_url": product.support_url,
                "status": product.status.value,
                "is_featured": product.is_featured,
                "features": product.features.to_dict(),
                "display_order": product.display_order,
            }
        )
        await self._session.commit()
        return product

    def _row_to_product(self, row) -> Product:
        """Convert database row to Product entity."""
        features_data = row.features if isinstance(row.features, dict) else {}

        return Product(
            product_id=UUID(str(row.product_id)),
            code=row.code,
            name=row.name,
            description=row.description,
            tagline=row.tagline,
            icon_url=row.icon_url,
            logo_url=row.logo_url,
            color_primary=row.color_primary,
            color_secondary=row.color_secondary,
            app_url=row.app_url,
            docs_url=row.docs_url,
            support_url=row.support_url,
            status=ProductStatus(row.status),
            is_featured=row.is_featured,
            features=ProductFeatures.from_dict(features_data),
            display_order=row.display_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
