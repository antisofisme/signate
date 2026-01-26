"""
Billing API Dependencies

FastAPI dependency injection setup.
"""

import os
from typing import Optional

from ..interfaces import (
    IPaymentGateway,
    ISubscriptionRepository,
    IInvoiceRepository,
    IPlanRepository,
)
from ..adapters import (
    MidtransGateway,
    PostgresSubscriptionRepository,
    PostgresInvoiceRepository,
    InMemoryPlanRepository,  # Use in-memory for plans (static data)
)
from ..use_cases import (
    GetPlansUseCase,
    CreateCheckoutUseCase,
    HandleWebhookUseCase,
    GetSubscriptionUseCase,
    CancelSubscriptionUseCase,
    ReactivateSubscriptionUseCase,
    ListInvoicesUseCase,
    CheckUsageLimitUseCase,
    CreateSubscriptionUseCase,
)

# Global instances (initialized at startup)
_payment_gateway: Optional[IPaymentGateway] = None
_subscription_repo: Optional[ISubscriptionRepository] = None
_invoice_repo: Optional[IInvoiceRepository] = None
_plan_repo: Optional[IPlanRepository] = None
_session_factory = None


def init_billing_dependencies(session_factory=None) -> None:
    """
    Initialize billing module dependencies.

    Call this at application startup.
    """
    global _payment_gateway, _subscription_repo, _invoice_repo, _plan_repo, _session_factory

    _session_factory = session_factory

    # Initialize payment gateway (Midtrans)
    _payment_gateway = MidtransGateway(
        server_key=os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-xxx"),
        client_key=os.getenv("MIDTRANS_CLIENT_KEY", "SB-Mid-client-xxx"),
        merchant_id=os.getenv("MIDTRANS_MERCHANT_ID", "G123456789"),
        is_production=os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true",
    )

    # Initialize repositories
    if session_factory:
        _subscription_repo = PostgresSubscriptionRepository(session_factory)
        _invoice_repo = PostgresInvoiceRepository(session_factory)

    # Plans are static - use in-memory
    _plan_repo = InMemoryPlanRepository()


# =============================================================================
# Dependency Getters
# =============================================================================


def get_payment_gateway() -> IPaymentGateway:
    """Get payment gateway instance"""
    if _payment_gateway is None:
        raise RuntimeError("Billing dependencies not initialized")
    return _payment_gateway


def get_subscription_repo() -> ISubscriptionRepository:
    """Get subscription repository"""
    if _subscription_repo is None:
        raise RuntimeError("Billing dependencies not initialized")
    return _subscription_repo


def get_invoice_repo() -> IInvoiceRepository:
    """Get invoice repository"""
    if _invoice_repo is None:
        raise RuntimeError("Billing dependencies not initialized")
    return _invoice_repo


def get_plan_repo() -> IPlanRepository:
    """Get plan repository"""
    if _plan_repo is None:
        raise RuntimeError("Billing dependencies not initialized")
    return _plan_repo


# =============================================================================
# Use Case Dependencies
# =============================================================================


def get_plans_use_case() -> GetPlansUseCase:
    """Get plans use case"""
    return GetPlansUseCase(plan_repo=get_plan_repo())


def get_subscription_use_case() -> GetSubscriptionUseCase:
    """Get subscription use case"""
    return GetSubscriptionUseCase(
        subscription_repo=get_subscription_repo(),
        plan_repo=get_plan_repo(),
    )


def create_subscription_use_case() -> CreateSubscriptionUseCase:
    """Create subscription use case"""
    return CreateSubscriptionUseCase(
        subscription_repo=get_subscription_repo(),
        plan_repo=get_plan_repo(),
    )


def create_checkout_use_case() -> CreateCheckoutUseCase:
    """Create checkout use case"""
    return CreateCheckoutUseCase(
        payment_gateway=get_payment_gateway(),
        subscription_repo=get_subscription_repo(),
        invoice_repo=get_invoice_repo(),
        plan_repo=get_plan_repo(),
    )


def handle_webhook_use_case() -> HandleWebhookUseCase:
    """Handle webhook use case"""
    return HandleWebhookUseCase(
        payment_gateway=get_payment_gateway(),
        subscription_repo=get_subscription_repo(),
        invoice_repo=get_invoice_repo(),
        plan_repo=get_plan_repo(),
        session_factory=_session_factory,
    )


def cancel_subscription_use_case() -> CancelSubscriptionUseCase:
    """Cancel subscription use case"""
    return CancelSubscriptionUseCase(
        subscription_repo=get_subscription_repo(),
    )


def reactivate_subscription_use_case() -> ReactivateSubscriptionUseCase:
    """Reactivate subscription use case"""
    return ReactivateSubscriptionUseCase(
        subscription_repo=get_subscription_repo(),
    )


def list_invoices_use_case() -> ListInvoicesUseCase:
    """List invoices use case"""
    return ListInvoicesUseCase(
        invoice_repo=get_invoice_repo(),
    )


def check_usage_limit_use_case() -> CheckUsageLimitUseCase:
    """Check usage limit use case"""
    return CheckUsageLimitUseCase(
        subscription_repo=get_subscription_repo(),
        plan_repo=get_plan_repo(),
    )
