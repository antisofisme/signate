"""
Billing API Routes

FastAPI router with billing endpoints.
"""

from typing import Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .schemas import (
    PlansListResponse,
    PlanResponse,
    PlanLimitsResponse,
    PlanFeaturesResponse,
    SubscriptionDetailsResponse,
    SubscriptionResponse,
    UsageResponse,
    CreateCheckoutRequest,
    CheckoutResponse,
    CheckoutData,
    InvoicesListResponse,
    InvoiceDetailResponse,
    InvoiceResponse,
    LineItemResponse,
    CancelSubscriptionRequest,
    SuccessResponse,
    WebhookResponse,
)
from .dependencies import (
    get_plans_use_case,
    get_subscription_use_case,
    create_checkout_use_case,
    handle_webhook_use_case,
    cancel_subscription_use_case,
    reactivate_subscription_use_case,
    list_invoices_use_case,
)
from ..use_cases import (
    GetPlansUseCase,
    GetSubscriptionUseCase,
    CreateCheckoutUseCase,
    HandleWebhookUseCase,
    CancelSubscriptionUseCase,
    ReactivateSubscriptionUseCase,
    ListInvoicesUseCase,
)
from ..exceptions import (
    BillingError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    WebhookVerificationError,
)

# Auth dependency - import from auth module
from ...auth.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


# =============================================================================
# Plans Endpoints
# =============================================================================


@router.get("/plans", response_model=PlansListResponse)
async def list_plans(
    use_case: GetPlansUseCase = Depends(get_plans_use_case),
):
    """
    List available subscription plans.

    Returns all active plans for the pricing page.
    This endpoint is public (no auth required).
    """
    plans = await use_case.get_all()

    return PlansListResponse(
        data=[
            PlanResponse(
                plan_id=p.plan_id,
                name=p.name,
                price_cents=p.price_cents,
                currency=p.currency,
                billing_interval=p.billing_interval,
                limits=PlanLimitsResponse(
                    max_projects=p.limits.max_projects,
                    max_decisions_per_month=p.limits.max_decisions_per_month,
                    max_team_members=p.limits.max_team_members,
                    max_rules=p.limits.max_rules,
                    audit_retention_days=p.limits.audit_retention_days,
                ),
                features=PlanFeaturesResponse(
                    api_access=p.features.api_access,
                    sso=p.features.sso,
                    priority_support=p.features.priority_support,
                    dedicated_support=p.features.dedicated_support,
                    sla_guarantee=p.features.sla_guarantee,
                    custom_branding=p.features.custom_branding,
                ),
                trial_days=p.trial_days,
                is_active=p.is_active,
                display_order=p.display_order,
                price_display=p.price_display,
            )
            for p in plans
        ]
    )


# =============================================================================
# Subscription Endpoints
# =============================================================================


@router.get("/subscription", response_model=SubscriptionDetailsResponse)
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    use_case: GetSubscriptionUseCase = Depends(get_subscription_use_case),
):
    """
    Get current subscription details.

    Returns subscription, plan info, and usage statistics.
    """
    # Get tenant_id from user context
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    try:
        details = await use_case.execute(UUID(tenant_id))

        return SubscriptionDetailsResponse(
            data=SubscriptionResponse(
                subscription_id=details.subscription.subscription_id,
                tenant_id=details.subscription.tenant_id,
                plan_id=details.subscription.plan_id,
                status=details.subscription.status.value,
                current_period_start=details.subscription.current_period_start,
                current_period_end=details.subscription.current_period_end,
                trial_end_at=details.subscription.trial_end_at,
                cancel_at_period_end=details.subscription.cancel_at_period_end,
                cancelled_at=details.subscription.cancelled_at,
                decisions_this_month=details.subscription.decisions_this_month,
                days_until_renewal=details.subscription.days_until_renewal,
            ),
            plan=PlanResponse(
                plan_id=details.plan.plan_id,
                name=details.plan.name,
                price_cents=details.plan.price_cents,
                currency=details.plan.currency,
                billing_interval=details.plan.billing_interval,
                limits=PlanLimitsResponse(
                    max_projects=details.plan.limits.max_projects,
                    max_decisions_per_month=details.plan.limits.max_decisions_per_month,
                    max_team_members=details.plan.limits.max_team_members,
                    max_rules=details.plan.limits.max_rules,
                    audit_retention_days=details.plan.limits.audit_retention_days,
                ),
                features=PlanFeaturesResponse(
                    api_access=details.plan.features.api_access,
                    sso=details.plan.features.sso,
                    priority_support=details.plan.features.priority_support,
                    dedicated_support=details.plan.features.dedicated_support,
                    sla_guarantee=details.plan.features.sla_guarantee,
                    custom_branding=details.plan.features.custom_branding,
                ),
                trial_days=details.plan.trial_days,
                is_active=details.plan.is_active,
                display_order=details.plan.display_order,
                price_display=details.plan.price_display,
            ),
            usage=UsageResponse(
                decisions_used=details.subscription.decisions_this_month,
                decisions_limit=details.plan.limits.max_decisions_per_month,
                usage_percentage=details.usage_percentage,
                is_near_limit=details.is_near_limit,
                is_over_limit=details.is_over_limit,
            ),
        )

    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for this tenant",
        )


# =============================================================================
# Checkout Endpoints
# =============================================================================


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_user),
    use_case: CreateCheckoutUseCase = Depends(create_checkout_use_case),
):
    """
    Create checkout session for plan upgrade.

    Returns Midtrans Snap token and redirect URL.
    Frontend should open Snap popup with the token.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    try:
        result = await use_case.execute(
            tenant_id=UUID(tenant_id),
            plan_id=request.plan_id,
            customer_email=current_user.get("email", ""),
            customer_name=current_user.get("name", "Customer"),
        )

        return CheckoutResponse(
            data=CheckoutData(
                invoice_id=result.invoice_id,
                invoice_number=result.invoice_number,
                amount_cents=result.amount_cents,
                currency=result.currency,
                snap_token=result.snap_token,
                redirect_url=result.redirect_url,
            )
        )

    except PlanNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {e.plan_id}",
        )
    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# =============================================================================
# Cancel/Reactivate Endpoints
# =============================================================================


@router.post("/cancel", response_model=SuccessResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    use_case: CancelSubscriptionUseCase = Depends(cancel_subscription_use_case),
):
    """
    Cancel subscription.

    By default, cancels at end of current billing period.
    Set immediate=true to cancel immediately (no refund).
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    try:
        await use_case.execute(
            tenant_id=UUID(tenant_id),
            reason=request.reason,
            immediate=request.immediate,
        )

        if request.immediate:
            message = "Subscription cancelled immediately"
        else:
            message = "Subscription will be cancelled at the end of the billing period"

        return SuccessResponse(message=message)

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post("/reactivate", response_model=SuccessResponse)
async def reactivate_subscription(
    current_user: dict = Depends(get_current_user),
    use_case: ReactivateSubscriptionUseCase = Depends(reactivate_subscription_use_case),
):
    """
    Reactivate a cancelled subscription.

    Only works if subscription is scheduled to cancel at period end
    but hasn't been fully cancelled yet.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    try:
        await use_case.execute(tenant_id=UUID(tenant_id))
        return SuccessResponse(message="Subscription reactivated successfully")

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# =============================================================================
# Invoice Endpoints
# =============================================================================


@router.get("/invoices", response_model=InvoicesListResponse)
async def list_invoices(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    use_case: ListInvoicesUseCase = Depends(list_invoices_use_case),
):
    """
    List invoices for current tenant.

    Returns paginated list of invoices.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    invoices = await use_case.execute(
        tenant_id=UUID(tenant_id),
        limit=min(limit, 100),
        offset=offset,
    )

    return InvoicesListResponse(
        data=[
            InvoiceResponse(
                invoice_id=inv.invoice_id,
                tenant_id=inv.tenant_id,
                invoice_number=inv.invoice_number,
                amount_cents=inv.amount_cents,
                currency=inv.currency,
                line_items=[
                    LineItemResponse(
                        description=item.description,
                        quantity=item.quantity,
                        unit_price_cents=item.unit_price_cents,
                        amount_cents=item.amount_cents,
                    )
                    for item in inv.line_items
                ],
                tax_rate=float(inv.tax_rate),
                tax_amount_cents=inv.tax_amount_cents,
                total_cents=inv.total_cents,
                status=inv.status.value,
                invoice_date=inv.invoice_date,
                due_date=inv.due_date,
                paid_at=inv.paid_at,
                created_at=inv.created_at,
                amount_display=inv.amount_display,
            )
            for inv in invoices
        ]
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: UUID,
    current_user: dict = Depends(get_current_user),
    use_case: ListInvoicesUseCase = Depends(list_invoices_use_case),
):
    """
    Get specific invoice by ID.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant selected",
        )

    invoice = await use_case.get_by_id(
        invoice_id=invoice_id,
        tenant_id=UUID(tenant_id),
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return InvoiceDetailResponse(
        data=InvoiceResponse(
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            invoice_number=invoice.invoice_number,
            amount_cents=invoice.amount_cents,
            currency=invoice.currency,
            line_items=[
                LineItemResponse(
                    description=item.description,
                    quantity=item.quantity,
                    unit_price_cents=item.unit_price_cents,
                    amount_cents=item.amount_cents,
                )
                for item in invoice.line_items
            ],
            tax_rate=float(invoice.tax_rate),
            tax_amount_cents=invoice.tax_amount_cents,
            total_cents=invoice.total_cents,
            status=invoice.status.value,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            paid_at=invoice.paid_at,
            created_at=invoice.created_at,
            amount_display=invoice.amount_display,
        )
    )


# =============================================================================
# Webhook Endpoint (Public - No Auth)
# =============================================================================


@router.post("/webhooks/midtrans", response_model=WebhookResponse)
async def handle_midtrans_webhook(
    request: Request,
    use_case: HandleWebhookUseCase = Depends(handle_webhook_use_case),
):
    """
    Handle Midtrans payment webhook.

    This endpoint is called by Midtrans when payment status changes.
    No authentication required (uses signature verification).
    """
    try:
        # Get raw body and JSON payload
        raw_body = await request.body()
        payload = await request.json()

        # Get signature from headers (if any)
        signature = request.headers.get("X-Midtrans-Signature")

        # Process webhook
        success = await use_case.execute(
            payload=payload,
            signature=signature,
            raw_body=raw_body,
        )

        return WebhookResponse(success=success)

    except WebhookVerificationError:
        logger.warning("Webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Return 200 to prevent Midtrans from retrying
        # Log the error for investigation
        return WebhookResponse(success=False)
