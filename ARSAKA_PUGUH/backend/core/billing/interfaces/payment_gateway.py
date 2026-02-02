"""
Payment Gateway Interface

Abstract interface for payment providers (Midtrans, Stripe, etc.)
Implementations are in adapters/ directory.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class CheckoutResult:
    """Result of creating a checkout session"""

    # Provider-specific identifiers
    order_id: str
    provider_checkout_id: Optional[str] = None

    # For redirect/popup based flows (Midtrans Snap)
    token: Optional[str] = None
    redirect_url: Optional[str] = None

    # For hosted checkout (Stripe)
    checkout_url: Optional[str] = None

    # Raw provider response
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class WebhookPayload:
    """Parsed webhook payload from payment provider"""

    # Common fields across providers
    order_id: str
    transaction_id: str
    status: str  # Provider's status (will be mapped to our InvoiceStatus)
    amount_cents: int
    currency: str
    payment_type: str

    # Signature for verification
    signature: Optional[str] = None

    # Raw payload
    raw_payload: Dict[str, Any] = None


class IPaymentGateway(ABC):
    """
    Abstract Payment Gateway Interface

    Implement this interface to add new payment providers.
    The business logic (use cases) depends only on this interface,
    making it easy to swap providers.

    Current implementations:
    - MidtransGateway (adapters/midtrans.py)

    Future implementations:
    - StripeGateway
    - XenditGateway
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'midtrans', 'stripe')"""
        pass

    @abstractmethod
    async def create_checkout(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        customer_email: str,
        customer_name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutResult:
        """
        Create a checkout session for payment.

        For Midtrans: Creates a Snap token
        For Stripe: Creates a Checkout Session

        Args:
            order_id: Unique order ID (invoice number)
            amount_cents: Amount in smallest currency unit
            currency: Currency code (IDR, USD)
            customer_email: Customer email
            customer_name: Customer name
            description: Item description
            metadata: Additional metadata

        Returns:
            CheckoutResult with token/URL for payment flow
        """
        pass

    @abstractmethod
    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Parsed webhook payload
            signature: Signature from headers (provider-specific)
            raw_body: Raw request body for signature verification

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookPayload:
        """
        Parse webhook payload into common format.

        Args:
            payload: Raw webhook payload

        Returns:
            WebhookPayload with normalized fields
        """
        pass

    @abstractmethod
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from provider.

        Args:
            transaction_id: Provider's transaction ID

        Returns:
            Transaction details or None if not found
        """
        pass

    @abstractmethod
    async def cancel_transaction(self, transaction_id: str) -> bool:
        """
        Cancel/void a pending transaction.

        Args:
            transaction_id: Provider's transaction ID

        Returns:
            True if cancelled successfully
        """
        pass

    @abstractmethod
    async def refund_transaction(
        self,
        transaction_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Refund a completed transaction.

        Args:
            transaction_id: Provider's transaction ID
            amount_cents: Partial refund amount (None = full refund)
            reason: Refund reason

        Returns:
            True if refund initiated successfully
        """
        pass

    def map_status_to_invoice_status(self, provider_status: str) -> str:
        """
        Map provider's status to our InvoiceStatus.

        Override in implementations if needed.
        Default mapping assumes common statuses.
        """
        status_map = {
            # Success states
            "capture": "pending",  # Card authorized, waiting settlement
            "settlement": "paid",
            "success": "paid",
            "paid": "paid",
            # Pending states
            "pending": "pending",
            "authorize": "pending",
            # Failure states
            "deny": "failed",
            "cancel": "cancelled",
            "expire": "failed",
            "failure": "failed",
            # Refund
            "refund": "refunded",
            "partial_refund": "refunded",
        }
        return status_map.get(provider_status.lower(), "pending")
