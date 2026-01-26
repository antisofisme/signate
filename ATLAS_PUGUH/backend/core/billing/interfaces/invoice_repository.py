"""
Invoice Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain import Invoice


class IInvoiceRepository(ABC):
    """Interface for invoice data access"""

    @abstractmethod
    async def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID"""
        pass

    @abstractmethod
    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        pass

    @abstractmethod
    async def create(self, invoice: Invoice) -> Invoice:
        """Create a new invoice"""
        pass

    @abstractmethod
    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice"""
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices for a tenant"""
        pass

    @abstractmethod
    async def list_by_subscription(
        self,
        subscription_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices for a subscription"""
        pass

    @abstractmethod
    async def list_pending(self) -> List[Invoice]:
        """List all pending invoices"""
        pass

    @abstractmethod
    async def list_overdue(self) -> List[Invoice]:
        """List all overdue invoices"""
        pass

    @abstractmethod
    async def generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        pass
