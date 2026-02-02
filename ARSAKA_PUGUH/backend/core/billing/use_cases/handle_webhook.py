"""
Handle Webhook Use Case

Processes payment webhooks from Midtrans (or other providers).
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
import logging
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import (
    IPaymentGateway,
    ISubscriptionRepository,
    IInvoiceRepository,
    IPlanRepository,
)
from ..domain import InvoiceStatus, SubscriptionStatus
from ..exceptions import WebhookVerificationError, InvoiceNotFoundError

logger = logging.getLogger(__name__)


class HandleWebhookUseCase:
    """Process payment webhooks"""

    def __init__(
        self,
        payment_gateway: IPaymentGateway,
        subscription_repo: ISubscriptionRepository,
        invoice_repo: IInvoiceRepository,
        plan_repo: IPlanRepository,
        session_factory=None,  # For webhook logging
    ):
        self._gateway = payment_gateway
        self._subscription_repo = subscription_repo
        self._invoice_repo = invoice_repo
        self._plan_repo = plan_repo
        self._session_factory = session_factory

    async def execute(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> bool:
        """
        Process webhook from payment provider.

        Args:
            payload: Webhook payload
            signature: Signature from headers (if applicable)
            raw_body: Raw request body for verification

        Returns:
            True if processed successfully

        Raises:
            WebhookVerificationError: If signature verification fails
        """
        # Log the webhook
        log_id = await self._log_webhook(payload)

        try:
            # Verify signature
            is_valid = await self._gateway.verify_webhook(payload, signature, raw_body)
            if not is_valid:
                await self._update_webhook_log(
                    log_id,
                    signature_valid=False,
                    verification_error="Invalid signature",
                )
                raise WebhookVerificationError()

            await self._update_webhook_log(log_id, signature_valid=True)

            # Parse webhook
            webhook_data = self._gateway.parse_webhook(payload)

            # Get invoice by order_id (invoice_number)
            invoice = await self._invoice_repo.get_by_number(webhook_data.order_id)
            if not invoice:
                logger.warning(f"Invoice not found for order: {webhook_data.order_id}")
                await self._update_webhook_log(
                    log_id,
                    processed=True,
                    process_error=f"Invoice not found: {webhook_data.order_id}",
                )
                return False

            # Check for idempotency - don't reprocess same status
            current_status = invoice.status.value
            new_status = self._gateway.map_status_to_invoice_status(webhook_data.status)

            if current_status == new_status:
                logger.info(f"Webhook already processed for {webhook_data.order_id}")
                await self._update_webhook_log(log_id, processed=True)
                return True

            # Don't regress from final states
            if invoice.status.is_final:
                logger.info(
                    f"Ignoring webhook for final status invoice {webhook_data.order_id}"
                )
                await self._update_webhook_log(log_id, processed=True)
                return True

            # Process based on status
            if new_status == "paid":
                await self._handle_payment_success(
                    invoice,
                    webhook_data.transaction_id,
                )
            elif new_status == "failed":
                await self._handle_payment_failed(invoice)
            elif new_status == "cancelled":
                invoice.cancel()
                await self._invoice_repo.update(invoice)
            elif new_status == "refunded":
                await self._handle_refund(invoice)

            await self._update_webhook_log(log_id, processed=True)
            return True

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            await self._update_webhook_log(
                log_id,
                processed=False,
                process_error=str(e),
            )
            raise

    async def _handle_payment_success(
        self,
        invoice,
        transaction_id: str,
    ) -> None:
        """Handle successful payment"""
        # Mark invoice as paid
        invoice.mark_paid(payment_id=transaction_id)
        await self._invoice_repo.update(invoice)

        # Get subscription
        subscription = await self._subscription_repo.get_by_id(
            invoice.subscription_id
        )
        if not subscription:
            logger.warning(f"Subscription not found for invoice {invoice.invoice_id}")
            return

        # Determine new plan from invoice metadata
        # In a real implementation, store plan_id in invoice or extract from line items
        # For now, we'll get it from the subscription's scheduled change or keep current

        # Extend subscription period
        subscription.extend_period(days=30)  # Monthly billing

        # If there was a scheduled upgrade, apply it
        if subscription.scheduled_plan_id:
            subscription.upgrade_to(subscription.scheduled_plan_id)

        await self._subscription_repo.update(subscription)
        logger.info(
            f"Payment successful for subscription {subscription.subscription_id}"
        )

    async def _handle_payment_failed(self, invoice) -> None:
        """Handle failed payment"""
        invoice.mark_failed()
        await self._invoice_repo.update(invoice)

        # Mark subscription as past due
        subscription = await self._subscription_repo.get_by_id(
            invoice.subscription_id
        )
        if subscription:
            subscription.mark_past_due()
            await self._subscription_repo.update(subscription)
            logger.warning(
                f"Payment failed for subscription {subscription.subscription_id}"
            )

    async def _handle_refund(self, invoice) -> None:
        """Handle refund"""
        invoice.refund()
        await self._invoice_repo.update(invoice)

        # Downgrade subscription to free
        subscription = await self._subscription_repo.get_by_id(
            invoice.subscription_id
        )
        if subscription:
            subscription.plan_id = "free"
            subscription.status = SubscriptionStatus.ACTIVE
            await self._subscription_repo.update(subscription)
            logger.info(
                f"Refund processed for subscription {subscription.subscription_id}"
            )

    async def _log_webhook(self, payload: Dict[str, Any]) -> Optional[str]:
        """Log webhook to database"""
        if not self._session_factory:
            return None

        try:
            session = self._session_factory()
            try:
                result = await session.execute(
                    text("""
                        INSERT INTO webhook_logs (
                            provider, endpoint, method, payload,
                            order_id, transaction_status, transaction_id
                        ) VALUES (
                            :provider, :endpoint, :method, :payload::jsonb,
                            :order_id, :transaction_status, :transaction_id
                        )
                        RETURNING log_id
                    """),
                    {
                        "provider": self._gateway.provider_name,
                        "endpoint": "/webhooks/midtrans",
                        "method": "POST",
                        "payload": json.dumps(payload),
                        "order_id": payload.get("order_id"),
                        "transaction_status": payload.get("transaction_status"),
                        "transaction_id": payload.get("transaction_id"),
                    },
                )
                await session.commit()
                row = result.first()
                return str(row.log_id) if row else None
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Failed to log webhook: {e}")
            return None

    async def _update_webhook_log(
        self,
        log_id: Optional[str],
        signature_valid: bool = None,
        verification_error: str = None,
        processed: bool = None,
        process_error: str = None,
    ) -> None:
        """Update webhook log"""
        if not log_id or not self._session_factory:
            return

        try:
            session = self._session_factory()
            try:
                updates = []
                params = {"log_id": log_id}

                if signature_valid is not None:
                    updates.append("signature_valid = :signature_valid")
                    params["signature_valid"] = signature_valid

                if verification_error is not None:
                    updates.append("verification_error = :verification_error")
                    params["verification_error"] = verification_error

                if processed is not None:
                    updates.append("processed = :processed")
                    updates.append("processed_at = NOW()")
                    params["processed"] = processed

                if process_error is not None:
                    updates.append("process_error = :process_error")
                    params["process_error"] = process_error

                if updates:
                    await session.execute(
                        text(f"""
                            UPDATE webhook_logs SET {', '.join(updates)}
                            WHERE log_id = :log_id
                        """),
                        params,
                    )
                    await session.commit()
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Failed to update webhook log: {e}")
