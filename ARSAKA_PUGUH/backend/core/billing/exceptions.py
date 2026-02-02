"""
Billing Module Exceptions
"""

from typing import Optional


class BillingError(Exception):
    """Base exception for billing module"""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or "BILLING_ERROR"
        super().__init__(self.message)


class PlanNotFoundError(BillingError):
    """Plan does not exist"""

    def __init__(self, plan_id: str):
        super().__init__(f"Plan '{plan_id}' not found", "PLAN_NOT_FOUND")
        self.plan_id = plan_id


class SubscriptionNotFoundError(BillingError):
    """Subscription does not exist"""

    def __init__(self, tenant_id: str):
        super().__init__(
            f"No subscription found for tenant '{tenant_id}'",
            "SUBSCRIPTION_NOT_FOUND",
        )
        self.tenant_id = tenant_id


class InvoiceNotFoundError(BillingError):
    """Invoice does not exist"""

    def __init__(self, invoice_id: str):
        super().__init__(f"Invoice '{invoice_id}' not found", "INVOICE_NOT_FOUND")
        self.invoice_id = invoice_id


class PlanLimitError(BillingError):
    """Plan limit exceeded"""

    def __init__(self, limit_type: str, message: str):
        super().__init__(message, f"{limit_type}_LIMIT_EXCEEDED")
        self.limit_type = limit_type


class InvalidPlanTransitionError(BillingError):
    """Invalid plan upgrade/downgrade"""

    def __init__(self, from_plan: str, to_plan: str, reason: str):
        super().__init__(
            f"Cannot change from '{from_plan}' to '{to_plan}': {reason}",
            "INVALID_PLAN_TRANSITION",
        )
        self.from_plan = from_plan
        self.to_plan = to_plan


class PaymentError(BillingError):
    """Payment processing error"""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, "PAYMENT_ERROR")
        self.provider = provider


class WebhookVerificationError(BillingError):
    """Webhook signature verification failed"""

    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message, "WEBHOOK_VERIFICATION_FAILED")


class SubscriptionAlreadyExistsError(BillingError):
    """Tenant already has a subscription"""

    def __init__(self, tenant_id: str):
        super().__init__(
            f"Tenant '{tenant_id}' already has an active subscription",
            "SUBSCRIPTION_EXISTS",
        )
        self.tenant_id = tenant_id


class SubscriptionAlreadyCancelledError(BillingError):
    """Subscription is already cancelled"""

    def __init__(self):
        super().__init__(
            "Subscription is already cancelled",
            "SUBSCRIPTION_ALREADY_CANCELLED",
        )


class CannotDowngradeError(BillingError):
    """Cannot downgrade due to usage exceeding new plan limits"""

    def __init__(self, reason: str):
        super().__init__(
            f"Cannot downgrade: {reason}",
            "CANNOT_DOWNGRADE",
        )
