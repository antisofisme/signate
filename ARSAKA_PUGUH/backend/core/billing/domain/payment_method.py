"""
Payment Method Domain Entity
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class PaymentType(str, Enum):
    """Payment method types"""

    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    GOPAY = "gopay"
    OVO = "ovo"
    DANA = "dana"
    SHOPEEPAY = "shopeepay"

    @property
    def display_name(self) -> str:
        """Human-readable name"""
        names = {
            PaymentType.CARD: "Credit/Debit Card",
            PaymentType.BANK_TRANSFER: "Bank Transfer",
            PaymentType.GOPAY: "GoPay",
            PaymentType.OVO: "OVO",
            PaymentType.DANA: "DANA",
            PaymentType.SHOPEEPAY: "ShopeePay",
        }
        return names.get(self, self.value)


@dataclass
class PaymentMethod:
    """
    Payment Method Entity

    Stored payment method for recurring billing.
    """

    payment_method_id: UUID
    tenant_id: UUID

    # Provider
    payment_provider: str = "midtrans"
    provider_method_id: Optional[str] = None

    # Type
    type: PaymentType = PaymentType.CARD

    # Details (masked/safe to store)
    details: Dict[str, Any] = field(default_factory=dict)

    # Default
    is_default: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        """Human-readable display name"""
        if self.type == PaymentType.CARD:
            brand = self.details.get("brand", "Card").title()
            last_four = self.details.get("last_four", "****")
            return f"{brand} ending in {last_four}"
        elif self.type == PaymentType.BANK_TRANSFER:
            bank = self.details.get("bank", "Bank").upper()
            return f"{bank} Transfer"
        else:
            return self.type.display_name

    @property
    def is_card(self) -> bool:
        return self.type == PaymentType.CARD

    @property
    def is_ewallet(self) -> bool:
        return self.type in (
            PaymentType.GOPAY,
            PaymentType.OVO,
            PaymentType.DANA,
            PaymentType.SHOPEEPAY,
        )

    def set_as_default(self) -> None:
        """Mark as default payment method"""
        self.is_default = True
        self.updated_at = datetime.utcnow()

    def unset_default(self) -> None:
        """Unmark as default"""
        self.is_default = False
        self.updated_at = datetime.utcnow()

    @classmethod
    def from_card(
        cls,
        payment_method_id: UUID,
        tenant_id: UUID,
        brand: str,
        last_four: str,
        exp_month: int,
        exp_year: int,
        provider_method_id: Optional[str] = None,
    ) -> "PaymentMethod":
        """Create card payment method"""
        return cls(
            payment_method_id=payment_method_id,
            tenant_id=tenant_id,
            type=PaymentType.CARD,
            provider_method_id=provider_method_id,
            details={
                "brand": brand.lower(),
                "last_four": last_four,
                "exp_month": exp_month,
                "exp_year": exp_year,
            },
        )

    @classmethod
    def from_ewallet(
        cls,
        payment_method_id: UUID,
        tenant_id: UUID,
        wallet_type: PaymentType,
        phone_masked: Optional[str] = None,
        provider_method_id: Optional[str] = None,
    ) -> "PaymentMethod":
        """Create e-wallet payment method"""
        details = {}
        if phone_masked:
            details["phone_masked"] = phone_masked
        return cls(
            payment_method_id=payment_method_id,
            tenant_id=tenant_id,
            type=wallet_type,
            provider_method_id=provider_method_id,
            details=details,
        )
