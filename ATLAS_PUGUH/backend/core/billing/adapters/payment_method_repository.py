"""
Payment Method Repository PostgreSQL Implementation
"""

from typing import Optional, List, Callable
from contextlib import asynccontextmanager
from uuid import UUID
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import IPaymentMethodRepository
from ..domain import PaymentMethod, PaymentType


class PostgresPaymentMethodRepository(IPaymentMethodRepository):
    """PostgreSQL implementation of payment method repository"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    @asynccontextmanager
    async def _session(self):
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def _row_to_payment_method(self, row) -> PaymentMethod:
        """Convert database row to domain entity"""
        details = row.details if isinstance(row.details, dict) else {}

        return PaymentMethod(
            payment_method_id=row.payment_method_id,
            tenant_id=row.tenant_id,
            payment_provider=row.payment_provider,
            provider_method_id=row.provider_method_id,
            type=PaymentType(row.type),
            details=details,
            is_default=row.is_default,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, payment_method_id: UUID) -> Optional[PaymentMethod]:
        """Get payment method by ID"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM payment_methods WHERE payment_method_id = :id"),
                {"id": str(payment_method_id)},
            )
            row = result.first()
            if row:
                return self._row_to_payment_method(row)
            return None

    async def list_by_tenant(self, tenant_id: UUID) -> List[PaymentMethod]:
        """List all payment methods for a tenant"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM payment_methods
                    WHERE tenant_id = :tenant_id
                    ORDER BY is_default DESC, created_at DESC
                """),
                {"tenant_id": str(tenant_id)},
            )
            return [self._row_to_payment_method(row) for row in result.fetchall()]

    async def get_default(self, tenant_id: UUID) -> Optional[PaymentMethod]:
        """Get default payment method for a tenant"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM payment_methods
                    WHERE tenant_id = :tenant_id AND is_default = TRUE
                """),
                {"tenant_id": str(tenant_id)},
            )
            row = result.first()
            if row:
                return self._row_to_payment_method(row)
            return None

    async def create(self, payment_method: PaymentMethod) -> PaymentMethod:
        """Create a new payment method"""
        details_json = json.dumps(payment_method.details)

        async with self._session() as session:
            # If this is the first payment method, make it default
            existing = await session.execute(
                text("""
                    SELECT COUNT(*) as count FROM payment_methods
                    WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": str(payment_method.tenant_id)},
            )
            count_row = existing.first()
            is_first = count_row.count == 0 if count_row else True

            is_default = payment_method.is_default or is_first

            await session.execute(
                text("""
                    INSERT INTO payment_methods (
                        payment_method_id, tenant_id,
                        payment_provider, provider_method_id,
                        type, details, is_default
                    ) VALUES (
                        :payment_method_id, :tenant_id,
                        :payment_provider, :provider_method_id,
                        :type, :details::jsonb, :is_default
                    )
                """),
                {
                    "payment_method_id": str(payment_method.payment_method_id),
                    "tenant_id": str(payment_method.tenant_id),
                    "payment_provider": payment_method.payment_provider,
                    "provider_method_id": payment_method.provider_method_id,
                    "type": payment_method.type.value,
                    "details": details_json,
                    "is_default": is_default,
                },
            )

            payment_method.is_default = is_default
            return payment_method

    async def update(self, payment_method: PaymentMethod) -> PaymentMethod:
        """Update a payment method"""
        details_json = json.dumps(payment_method.details)

        async with self._session() as session:
            await session.execute(
                text("""
                    UPDATE payment_methods SET
                        provider_method_id = :provider_method_id,
                        type = :type,
                        details = :details::jsonb,
                        is_default = :is_default,
                        updated_at = NOW()
                    WHERE payment_method_id = :payment_method_id
                """),
                {
                    "payment_method_id": str(payment_method.payment_method_id),
                    "provider_method_id": payment_method.provider_method_id,
                    "type": payment_method.type.value,
                    "details": details_json,
                    "is_default": payment_method.is_default,
                },
            )
            return payment_method

    async def delete(self, payment_method_id: UUID) -> bool:
        """Delete a payment method"""
        async with self._session() as session:
            result = await session.execute(
                text("DELETE FROM payment_methods WHERE payment_method_id = :id"),
                {"id": str(payment_method_id)},
            )
            return result.rowcount > 0

    async def set_default(self, tenant_id: UUID, payment_method_id: UUID) -> bool:
        """Set a payment method as default (unsets others)"""
        async with self._session() as session:
            # First, unset all defaults for this tenant
            await session.execute(
                text("""
                    UPDATE payment_methods
                    SET is_default = FALSE, updated_at = NOW()
                    WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": str(tenant_id)},
            )

            # Then set the new default
            result = await session.execute(
                text("""
                    UPDATE payment_methods
                    SET is_default = TRUE, updated_at = NOW()
                    WHERE payment_method_id = :payment_method_id
                    AND tenant_id = :tenant_id
                """),
                {
                    "payment_method_id": str(payment_method_id),
                    "tenant_id": str(tenant_id),
                },
            )
            return result.rowcount > 0
