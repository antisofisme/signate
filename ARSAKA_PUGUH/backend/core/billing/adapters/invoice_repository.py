"""
Invoice Repository PostgreSQL Implementation
"""

from typing import Optional, List, Callable
from contextlib import asynccontextmanager
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import IInvoiceRepository
from ..domain import Invoice, InvoiceStatus, LineItem


class PostgresInvoiceRepository(IInvoiceRepository):
    """PostgreSQL implementation of invoice repository"""

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

    def _row_to_invoice(self, row) -> Invoice:
        """Convert database row to domain entity"""
        # Parse line items from JSON
        line_items_data = row.line_items if isinstance(row.line_items, list) else []
        line_items = [LineItem.from_dict(item) for item in line_items_data]

        return Invoice(
            invoice_id=row.invoice_id,
            tenant_id=row.tenant_id,
            subscription_id=row.subscription_id,
            invoice_number=row.invoice_number,
            amount_cents=row.amount_cents,
            currency=row.currency,
            line_items=line_items,
            tax_rate=Decimal(str(row.tax_rate)) if row.tax_rate else Decimal("0"),
            tax_amount_cents=row.tax_amount_cents,
            total_cents=row.total_cents,
            status=InvoiceStatus(row.status),
            payment_provider=row.payment_provider,
            provider_invoice_id=row.provider_invoice_id,
            provider_payment_id=row.provider_payment_id,
            snap_token=row.snap_token,
            snap_redirect_url=row.snap_redirect_url,
            invoice_date=row.invoice_date,
            due_date=row.due_date,
            paid_at=row.paid_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM invoices WHERE invoice_id = :id"),
                {"id": str(invoice_id)},
            )
            row = result.first()
            if row:
                return self._row_to_invoice(row)
            return None

    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM invoices WHERE invoice_number = :number"),
                {"number": invoice_number},
            )
            row = result.first()
            if row:
                return self._row_to_invoice(row)
            return None

    async def create(self, invoice: Invoice) -> Invoice:
        """Create a new invoice"""
        line_items_json = json.dumps([item.to_dict() for item in invoice.line_items])

        async with self._session() as session:
            await session.execute(
                text("""
                    INSERT INTO invoices (
                        invoice_id, tenant_id, subscription_id,
                        invoice_number, amount_cents, currency,
                        line_items, tax_rate, tax_amount_cents, total_cents,
                        status, payment_provider, provider_invoice_id,
                        snap_token, snap_redirect_url,
                        invoice_date, due_date
                    ) VALUES (
                        :invoice_id, :tenant_id, :subscription_id,
                        :invoice_number, :amount_cents, :currency,
                        :line_items::jsonb, :tax_rate, :tax_amount_cents, :total_cents,
                        :status, :payment_provider, :provider_invoice_id,
                        :snap_token, :snap_redirect_url,
                        :invoice_date, :due_date
                    )
                """),
                {
                    "invoice_id": str(invoice.invoice_id),
                    "tenant_id": str(invoice.tenant_id),
                    "subscription_id": str(invoice.subscription_id),
                    "invoice_number": invoice.invoice_number,
                    "amount_cents": invoice.amount_cents,
                    "currency": invoice.currency,
                    "line_items": line_items_json,
                    "tax_rate": float(invoice.tax_rate),
                    "tax_amount_cents": invoice.tax_amount_cents,
                    "total_cents": invoice.total_cents,
                    "status": invoice.status.value,
                    "payment_provider": invoice.payment_provider,
                    "provider_invoice_id": invoice.provider_invoice_id,
                    "snap_token": invoice.snap_token,
                    "snap_redirect_url": invoice.snap_redirect_url,
                    "invoice_date": invoice.invoice_date,
                    "due_date": invoice.due_date,
                },
            )
            return invoice

    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice"""
        line_items_json = json.dumps([item.to_dict() for item in invoice.line_items])

        async with self._session() as session:
            await session.execute(
                text("""
                    UPDATE invoices SET
                        amount_cents = :amount_cents,
                        line_items = :line_items::jsonb,
                        tax_rate = :tax_rate,
                        tax_amount_cents = :tax_amount_cents,
                        total_cents = :total_cents,
                        status = :status,
                        provider_invoice_id = :provider_invoice_id,
                        provider_payment_id = :provider_payment_id,
                        snap_token = :snap_token,
                        snap_redirect_url = :snap_redirect_url,
                        paid_at = :paid_at,
                        updated_at = NOW()
                    WHERE invoice_id = :invoice_id
                """),
                {
                    "invoice_id": str(invoice.invoice_id),
                    "amount_cents": invoice.amount_cents,
                    "line_items": line_items_json,
                    "tax_rate": float(invoice.tax_rate),
                    "tax_amount_cents": invoice.tax_amount_cents,
                    "total_cents": invoice.total_cents,
                    "status": invoice.status.value,
                    "provider_invoice_id": invoice.provider_invoice_id,
                    "provider_payment_id": invoice.provider_payment_id,
                    "snap_token": invoice.snap_token,
                    "snap_redirect_url": invoice.snap_redirect_url,
                    "paid_at": invoice.paid_at,
                },
            )
            return invoice

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices for a tenant"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM invoices
                    WHERE tenant_id = :tenant_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {
                    "tenant_id": str(tenant_id),
                    "limit": limit,
                    "offset": offset,
                },
            )
            return [self._row_to_invoice(row) for row in result.fetchall()]

    async def list_by_subscription(
        self,
        subscription_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices for a subscription"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM invoices
                    WHERE subscription_id = :subscription_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {
                    "subscription_id": str(subscription_id),
                    "limit": limit,
                    "offset": offset,
                },
            )
            return [self._row_to_invoice(row) for row in result.fetchall()]

    async def list_pending(self) -> List[Invoice]:
        """List all pending invoices"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT * FROM invoices WHERE status = 'pending' ORDER BY due_date"),
            )
            return [self._row_to_invoice(row) for row in result.fetchall()]

    async def list_overdue(self) -> List[Invoice]:
        """List all overdue invoices"""
        async with self._session() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM invoices
                    WHERE status = 'pending' AND due_date < CURRENT_DATE
                    ORDER BY due_date
                """),
            )
            return [self._row_to_invoice(row) for row in result.fetchall()]

    async def generate_invoice_number(self) -> str:
        """Generate unique invoice number using database sequence"""
        async with self._session() as session:
            result = await session.execute(
                text("SELECT generate_invoice_number()"),
            )
            row = result.first()
            return row[0] if row else f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
