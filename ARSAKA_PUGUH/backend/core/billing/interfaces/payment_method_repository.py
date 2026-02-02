"""
Payment Method Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain import PaymentMethod


class IPaymentMethodRepository(ABC):
    """Interface for payment method data access"""

    @abstractmethod
    async def get_by_id(self, payment_method_id: UUID) -> Optional[PaymentMethod]:
        """Get payment method by ID"""
        pass

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> List[PaymentMethod]:
        """List all payment methods for a tenant"""
        pass

    @abstractmethod
    async def get_default(self, tenant_id: UUID) -> Optional[PaymentMethod]:
        """Get default payment method for a tenant"""
        pass

    @abstractmethod
    async def create(self, payment_method: PaymentMethod) -> PaymentMethod:
        """Create a new payment method"""
        pass

    @abstractmethod
    async def update(self, payment_method: PaymentMethod) -> PaymentMethod:
        """Update a payment method"""
        pass

    @abstractmethod
    async def delete(self, payment_method_id: UUID) -> bool:
        """Delete a payment method"""
        pass

    @abstractmethod
    async def set_default(self, tenant_id: UUID, payment_method_id: UUID) -> bool:
        """Set a payment method as default (unsets others)"""
        pass
