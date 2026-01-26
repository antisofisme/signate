"""
Midtrans Payment Gateway Adapter

Implements IPaymentGateway for Midtrans Snap integration.
"""

import hashlib
import httpx
import base64
import logging
from typing import Optional, Dict, Any

from ..interfaces import IPaymentGateway, CheckoutResult, WebhookPayload
from ..exceptions import PaymentError, WebhookVerificationError

logger = logging.getLogger(__name__)


class MidtransGateway(IPaymentGateway):
    """
    Midtrans Payment Gateway Implementation

    Uses Midtrans Snap API for payment popup.
    Supports: Credit Card, GoPay, OVO, Bank Transfer, etc.
    """

    def __init__(
        self,
        server_key: str,
        client_key: str,
        merchant_id: str,
        is_production: bool = False,
    ):
        self.server_key = server_key
        self.client_key = client_key
        self.merchant_id = merchant_id
        self.is_production = is_production

        # Set API URLs based on environment
        if is_production:
            self.snap_url = "https://app.midtrans.com/snap/v1/transactions"
            self.core_url = "https://api.midtrans.com/v2"
        else:
            self.snap_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
            self.core_url = "https://api.sandbox.midtrans.com/v2"

        # Auth header
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "midtrans"

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
        Create Midtrans Snap transaction.

        Note: Midtrans uses whole numbers for IDR (no cents).
        amount_cents should be passed as the actual amount in IDR cents,
        then divided by 100 for Midtrans (which expects whole IDR).
        """
        # Midtrans expects whole IDR, not cents
        # For consistency with other providers, we accept cents and convert
        gross_amount = amount_cents // 100  # Convert cents to IDR

        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": gross_amount,
            },
            "customer_details": {
                "email": customer_email,
                "first_name": customer_name.split()[0] if customer_name else "Customer",
                "last_name": " ".join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else "",
            },
            "item_details": [
                {
                    "id": order_id,
                    "price": gross_amount,
                    "quantity": 1,
                    "name": description[:50],  # Midtrans has 50 char limit
                }
            ],
        }

        # Add metadata if provided
        if metadata:
            payload["custom_field1"] = str(metadata.get("tenant_id", ""))
            payload["custom_field2"] = str(metadata.get("plan_id", ""))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.snap_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )

                if response.status_code != 201:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error_messages", [str(response.status_code)])
                    logger.error(f"Midtrans create_checkout failed: {error_msg}")
                    raise PaymentError(
                        f"Failed to create checkout: {', '.join(error_msg)}",
                        provider="midtrans",
                    )

                data = response.json()
                return CheckoutResult(
                    order_id=order_id,
                    provider_checkout_id=order_id,  # Midtrans uses order_id
                    token=data.get("token"),
                    redirect_url=data.get("redirect_url"),
                    raw_response=data,
                )

        except httpx.TimeoutException:
            raise PaymentError("Midtrans request timed out", provider="midtrans")
        except httpx.RequestError as e:
            raise PaymentError(f"Midtrans request failed: {str(e)}", provider="midtrans")

    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> bool:
        """
        Verify Midtrans webhook signature.

        Midtrans signature = SHA512(order_id + status_code + gross_amount + server_key)
        """
        try:
            order_id = payload.get("order_id", "")
            status_code = payload.get("status_code", "")
            gross_amount = payload.get("gross_amount", "")
            received_signature = payload.get("signature_key", "")

            # Build signature string
            signature_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
            expected_signature = hashlib.sha512(signature_string.encode()).hexdigest()

            is_valid = received_signature == expected_signature

            if not is_valid:
                logger.warning(
                    f"Midtrans webhook signature mismatch for order {order_id}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Midtrans webhook verification error: {e}")
            return False

    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookPayload:
        """Parse Midtrans webhook payload into common format"""
        # Extract amount (Midtrans sends as string with decimals)
        gross_amount_str = payload.get("gross_amount", "0")
        try:
            # Remove decimals and convert to cents
            amount_cents = int(float(gross_amount_str) * 100)
        except (ValueError, TypeError):
            amount_cents = 0

        return WebhookPayload(
            order_id=payload.get("order_id", ""),
            transaction_id=payload.get("transaction_id", ""),
            status=payload.get("transaction_status", ""),
            amount_cents=amount_cents,
            currency=payload.get("currency", "IDR"),
            payment_type=payload.get("payment_type", ""),
            signature=payload.get("signature_key"),
            raw_payload=payload,
        )

    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction status from Midtrans"""
        url = f"{self.core_url}/{transaction_id}/status"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0,
                )

                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    logger.error(f"Midtrans get_transaction failed: {response.status_code}")
                    return None

                return response.json()

        except Exception as e:
            logger.error(f"Midtrans get_transaction error: {e}")
            return None

    async def cancel_transaction(self, transaction_id: str) -> bool:
        """Cancel a pending Midtrans transaction"""
        url = f"{self.core_url}/{transaction_id}/cancel"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    timeout=30.0,
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Midtrans cancel_transaction error: {e}")
            return False

    async def refund_transaction(
        self,
        transaction_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Refund a Midtrans transaction"""
        url = f"{self.core_url}/{transaction_id}/refund"

        payload = {}
        if amount_cents:
            payload["refund_amount"] = amount_cents // 100  # Convert to IDR
        if reason:
            payload["reason"] = reason

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Midtrans refund_transaction error: {e}")
            return False

    def map_status_to_invoice_status(self, provider_status: str) -> str:
        """
        Map Midtrans transaction status to our InvoiceStatus.

        Midtrans statuses:
        - capture: Card payment captured (awaiting settlement)
        - settlement: Payment settled (success)
        - pending: Waiting for payment
        - deny: Payment denied
        - cancel: Transaction cancelled
        - expire: Transaction expired
        - refund: Transaction refunded
        """
        status_map = {
            "capture": "pending",  # For cards, capture means auth success
            "settlement": "paid",
            "pending": "pending",
            "deny": "failed",
            "cancel": "cancelled",
            "expire": "failed",
            "refund": "refunded",
            "partial_refund": "refunded",
        }
        return status_map.get(provider_status.lower(), "pending")
