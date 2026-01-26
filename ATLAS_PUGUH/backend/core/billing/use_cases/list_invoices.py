"""
List Invoices Use Case

Retrieves invoice history for a tenant.
"""

from typing import List, Optional
from uuid import UUID

from ..interfaces import IInvoiceRepository
from ..domain import Invoice


class ListInvoicesUseCase:
    """List invoices for tenant"""

    def __init__(self, invoice_repo: IInvoiceRepository):
        self._invoice_repo = invoice_repo

    async def execute(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Invoice]:
        """
        List invoices for tenant.

        Args:
            tenant_id: Tenant UUID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of invoices
        """
        return await self._invoice_repo.list_by_tenant(
            tenant_id,
            limit=limit,
            offset=offset,
        )

    async def get_by_id(
        self,
        invoice_id: UUID,
        tenant_id: UUID,
    ) -> Optional[Invoice]:
        """
        Get specific invoice.

        Args:
            invoice_id: Invoice UUID
            tenant_id: Tenant UUID (for access control)

        Returns:
            Invoice if found and belongs to tenant
        """
        invoice = await self._invoice_repo.get_by_id(invoice_id)
        if invoice and invoice.tenant_id == tenant_id:
            return invoice
        return None
