"""
Webhook Signature Verifier

Verifies webhook signatures from payment providers.
"""

import hmac
import hashlib
import base64
from typing import Optional
from datetime import datetime, timedelta


class WebhookVerifier:
    """
    Verifies webhook signatures from various providers.

    Supports:
    - Midtrans (SHA512 signature)
    - Stripe (HMAC-SHA256 with timestamp)
    - Generic HMAC verification
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def verify_midtrans(
        self,
        order_id: str,
        status_code: str,
        gross_amount: str,
        signature_key: str,
    ) -> bool:
        """
        Verify Midtrans webhook signature.

        Midtrans signature = SHA512(order_id + status_code + gross_amount + server_key)

        Args:
            order_id: Transaction order ID
            status_code: Transaction status code
            gross_amount: Transaction amount (as string)
            signature_key: Signature from webhook payload

        Returns:
            True if signature is valid
        """
        # Build signature string
        signature_string = f"{order_id}{status_code}{gross_amount}{self.secret_key}"

        # Calculate expected signature
        expected_signature = hashlib.sha512(
            signature_string.encode()
        ).hexdigest()

        # Compare (timing-safe)
        return hmac.compare_digest(expected_signature, signature_key)

    def verify_stripe(
        self,
        payload: bytes,
        signature_header: str,
        tolerance_seconds: int = 300,
    ) -> bool:
        """
        Verify Stripe webhook signature.

        Stripe uses HMAC-SHA256 with timestamp for replay protection.
        Header format: t=timestamp,v1=signature

        Args:
            payload: Raw request body
            signature_header: Stripe-Signature header value
            tolerance_seconds: Max age of webhook (default 5 minutes)

        Returns:
            True if signature is valid and not expired
        """
        try:
            # Parse header
            elements = dict(
                item.split("=", 1) for item in signature_header.split(",")
            )

            timestamp = int(elements.get("t", "0"))
            signature = elements.get("v1", "")

            # Check timestamp (replay protection)
            webhook_time = datetime.fromtimestamp(timestamp)
            if datetime.utcnow() - webhook_time > timedelta(seconds=tolerance_seconds):
                return False

            # Build signed payload
            signed_payload = f"{timestamp}.{payload.decode()}"

            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                signed_payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            # Compare (timing-safe)
            return hmac.compare_digest(expected_signature, signature)

        except (ValueError, KeyError):
            return False

    def verify_hmac_sha256(
        self,
        payload: bytes,
        signature: str,
        encoding: str = "hex",
    ) -> bool:
        """
        Generic HMAC-SHA256 verification.

        Args:
            payload: Raw request body
            signature: Expected signature
            encoding: Signature encoding ('hex' or 'base64')

        Returns:
            True if signature is valid
        """
        expected = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256,
        )

        if encoding == "base64":
            expected_signature = base64.b64encode(expected.digest()).decode()
        else:
            expected_signature = expected.hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def verify_hmac_sha512(
        self,
        payload: bytes,
        signature: str,
        encoding: str = "hex",
    ) -> bool:
        """
        Generic HMAC-SHA512 verification.

        Args:
            payload: Raw request body
            signature: Expected signature
            encoding: Signature encoding ('hex' or 'base64')

        Returns:
            True if signature is valid
        """
        expected = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha512,
        )

        if encoding == "base64":
            expected_signature = base64.b64encode(expected.digest()).decode()
        else:
            expected_signature = expected.hexdigest()

        return hmac.compare_digest(expected_signature, signature)


def create_test_signature(
    secret_key: str,
    order_id: str,
    status_code: str,
    gross_amount: str,
) -> str:
    """
    Create a test Midtrans signature for development/testing.

    Args:
        secret_key: Midtrans server key
        order_id: Test order ID
        status_code: Test status code
        gross_amount: Test amount

    Returns:
        Valid signature for testing
    """
    signature_string = f"{order_id}{status_code}{gross_amount}{secret_key}"
    return hashlib.sha512(signature_string.encode()).hexdigest()
