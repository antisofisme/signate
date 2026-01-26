"""
Invoice Domain Entity
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date, timedelta
from uuid import UUID
from enum import Enum
from decimal import Decimal


class InvoiceStatus(str, Enum):
    """Invoice payment status"""

    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

    @property
    def is_final(self) -> bool:
        """Is this a terminal state?"""
        return self in (
            InvoiceStatus.PAID,
            InvoiceStatus.CANCELLED,
            InvoiceStatus.REFUNDED,
        )


@dataclass
class LineItem:
    """Invoice line item"""

    description: str
    quantity: int
    unit_price_cents: int
    amount_cents: int

    @classmethod
    def create(cls, description: str, quantity: int, unit_price_cents: int) -> "LineItem":
        return cls(
            description=description,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
            amount_cents=quantity * unit_price_cents,
        )

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price_cents": self.unit_price_cents,
            "amount_cents": self.amount_cents,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LineItem":
        return cls(
            description=data["description"],
            quantity=data["quantity"],
            unit_price_cents=data["unit_price_cents"],
            amount_cents=data["amount_cents"],
        )


@dataclass
class Invoice:
    """
    Invoice Entity

    Payment record with line items and status tracking.
    """

    invoice_id: UUID
    tenant_id: UUID
    subscription_id: UUID

    # Invoice details
    invoice_number: str
    amount_cents: int
    currency: str = "IDR"

    # Line items
    line_items: List[LineItem] = field(default_factory=list)

    # Tax
    tax_rate: Decimal = Decimal("0")
    tax_amount_cents: int = 0
    total_cents: int = 0

    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT

    # Payment provider
    payment_provider: str = "midtrans"
    provider_invoice_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    snap_token: Optional[str] = None
    snap_redirect_url: Optional[str] = None

    # Dates
    invoice_date: date = field(default_factory=date.today)
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Set default due date (7 days from invoice date)
        if self.due_date is None:
            self.due_date = self.invoice_date + timedelta(days=7)
        # Calculate total if not set
        if self.total_cents == 0:
            self.calculate_total()

    def add_line_item(self, item: LineItem) -> None:
        """Add a line item and recalculate total"""
        self.line_items.append(item)
        self.calculate_total()

    def calculate_total(self) -> None:
        """Calculate totals from line items"""
        self.amount_cents = sum(item.amount_cents for item in self.line_items)
        self.tax_amount_cents = int(self.amount_cents * self.tax_rate)
        self.total_cents = self.amount_cents + self.tax_amount_cents

    @property
    def is_paid(self) -> bool:
        return self.status == InvoiceStatus.PAID

    @property
    def is_pending(self) -> bool:
        return self.status == InvoiceStatus.PENDING

    @property
    def is_overdue(self) -> bool:
        if self.status != InvoiceStatus.PENDING:
            return False
        return date.today() > self.due_date

    @property
    def amount_display(self) -> str:
        """Human-readable amount"""
        amount = self.total_cents // 100
        return f"Rp {amount:,}"

    def mark_pending(self) -> None:
        """Mark as pending payment"""
        self.status = InvoiceStatus.PENDING
        self.updated_at = datetime.utcnow()

    def mark_paid(self, payment_id: Optional[str] = None) -> None:
        """Mark as paid"""
        self.status = InvoiceStatus.PAID
        self.paid_at = datetime.utcnow()
        if payment_id:
            self.provider_payment_id = payment_id
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark as failed"""
        self.status = InvoiceStatus.FAILED
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the invoice"""
        self.status = InvoiceStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def refund(self) -> None:
        """Mark as refunded"""
        self.status = InvoiceStatus.REFUNDED
        self.updated_at = datetime.utcnow()

    def set_snap_details(self, token: str, redirect_url: str) -> None:
        """Set Midtrans Snap details"""
        self.snap_token = token
        self.snap_redirect_url = redirect_url
        self.updated_at = datetime.utcnow()
