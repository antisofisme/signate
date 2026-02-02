"""
Create Checkout Use Case

Creates a checkout session for plan upgrade/renewal.
"""

from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from ..interfaces import (
    IPaymentGateway,
    ISubscriptionRepository,
    IInvoiceRepository,
    IPlanRepository,
)
from ..domain import Invoice, InvoiceStatus, LineItem
from ..exceptions import (
    PlanNotFoundError,
    SubscriptionNotFoundError,
    InvalidPlanTransitionError,
)


@dataclass
class CheckoutResult:
    """Result of checkout creation"""

    invoice_id: UUID
    invoice_number: str
    amount_cents: int
    currency: str
    snap_token: str
    redirect_url: str


class CreateCheckoutUseCase:
    """Create checkout for plan upgrade"""

    def __init__(
        self,
        payment_gateway: IPaymentGateway,
        subscription_repo: ISubscriptionRepository,
        invoice_repo: IInvoiceRepository,
        plan_repo: IPlanRepository,
    ):
        self._gateway = payment_gateway
        self._subscription_repo = subscription_repo
        self._invoice_repo = invoice_repo
        self._plan_repo = plan_repo

    async def execute(
        self,
        tenant_id: UUID,
        plan_id: str,
        customer_email: str,
        customer_name: str,
    ) -> CheckoutResult:
        """
        Create checkout session for plan upgrade.

        Args:
            tenant_id: Tenant UUID
            plan_id: Target plan ID
            customer_email: Customer email for receipt
            customer_name: Customer name

        Returns:
            CheckoutResult with Snap token and redirect URL

        Raises:
            PlanNotFoundError: If plan doesn't exist
            SubscriptionNotFoundError: If no subscription found
            InvalidPlanTransitionError: If transition is invalid
        """
        # Get current subscription
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if not subscription:
            raise SubscriptionNotFoundError(str(tenant_id))

        # Get target plan
        target_plan = await self._plan_repo.get_by_id(plan_id)
        if not target_plan:
            raise PlanNotFoundError(plan_id)

        # Get current plan
        current_plan = await self._plan_repo.get_by_id(subscription.plan_id)

        # Validate transition
        if target_plan.is_free:
            raise InvalidPlanTransitionError(
                subscription.plan_id,
                plan_id,
                "Cannot checkout for free plan. Use downgrade endpoint instead.",
            )

        if current_plan and target_plan.plan_id == current_plan.plan_id:
            raise InvalidPlanTransitionError(
                subscription.plan_id,
                plan_id,
                "Already on this plan. Use renewal endpoint instead.",
            )

        # Enterprise requires manual handling
        if plan_id == "enterprise":
            raise InvalidPlanTransitionError(
                subscription.plan_id,
                plan_id,
                "Enterprise plan requires contacting sales.",
            )

        # Generate invoice number
        invoice_number = await self._invoice_repo.generate_invoice_number()

        # Create line item
        description = f"{target_plan.name} Plan - Monthly"
        line_item = LineItem.create(
            description=description,
            quantity=1,
            unit_price_cents=target_plan.price_cents,
        )

        # Create invoice
        invoice = Invoice(
            invoice_id=uuid4(),
            tenant_id=tenant_id,
            subscription_id=subscription.subscription_id,
            invoice_number=invoice_number,
            amount_cents=target_plan.price_cents,
            currency="IDR",
            line_items=[line_item],
            status=InvoiceStatus.PENDING,
            payment_provider=self._gateway.provider_name,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=7),
        )
        invoice.calculate_total()

        # Create Midtrans checkout
        checkout = await self._gateway.create_checkout(
            order_id=invoice_number,
            amount_cents=invoice.total_cents,
            currency=invoice.currency,
            customer_email=customer_email,
            customer_name=customer_name,
            description=description,
            metadata={
                "tenant_id": str(tenant_id),
                "plan_id": plan_id,
                "invoice_id": str(invoice.invoice_id),
            },
        )

        # Store Snap details on invoice
        invoice.set_snap_details(
            token=checkout.token,
            redirect_url=checkout.redirect_url,
        )

        # Save invoice
        await self._invoice_repo.create(invoice)

        return CheckoutResult(
            invoice_id=invoice.invoice_id,
            invoice_number=invoice_number,
            amount_cents=invoice.total_cents,
            currency=invoice.currency,
            snap_token=checkout.token,
            redirect_url=checkout.redirect_url,
        )
