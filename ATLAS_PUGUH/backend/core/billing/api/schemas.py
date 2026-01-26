"""
Billing API Schemas

Pydantic models for request/response validation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# Plan Schemas
# =============================================================================


class PlanFeaturesResponse(BaseModel):
    """Plan features"""

    api_access: bool = False
    sso: bool = False
    priority_support: bool = False
    dedicated_support: bool = False
    sla_guarantee: bool = False
    custom_branding: bool = False


class PlanLimitsResponse(BaseModel):
    """Plan limits (null = unlimited)"""

    max_projects: Optional[int] = None
    max_decisions_per_month: Optional[int] = None
    max_team_members: Optional[int] = None
    max_rules: Optional[int] = None
    audit_retention_days: int = 30


class PlanResponse(BaseModel):
    """Subscription plan response"""

    plan_id: str
    name: str
    price_cents: int
    currency: str = "IDR"
    billing_interval: str = "month"
    limits: PlanLimitsResponse
    features: PlanFeaturesResponse
    trial_days: int = 0
    is_active: bool = True
    display_order: int = 0
    price_display: str = ""

    class Config:
        from_attributes = True


class PlansListResponse(BaseModel):
    """List of plans response"""

    success: bool = True
    data: List[PlanResponse]


# =============================================================================
# Subscription Schemas
# =============================================================================


class SubscriptionResponse(BaseModel):
    """Subscription details response"""

    subscription_id: UUID
    tenant_id: UUID
    plan_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end_at: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    decisions_this_month: int = 0
    days_until_renewal: int = 0

    class Config:
        from_attributes = True


class SubscriptionDetailsResponse(BaseModel):
    """Full subscription with plan and usage"""

    success: bool = True
    data: SubscriptionResponse
    plan: PlanResponse
    usage: "UsageResponse"


class UsageResponse(BaseModel):
    """Current usage info"""

    decisions_used: int
    decisions_limit: Optional[int]
    usage_percentage: float
    is_near_limit: bool = False
    is_over_limit: bool = False


# =============================================================================
# Checkout Schemas
# =============================================================================


class CreateCheckoutRequest(BaseModel):
    """Request to create checkout"""

    plan_id: str = Field(..., description="Target plan ID")


class CheckoutResponse(BaseModel):
    """Checkout session response"""

    success: bool = True
    data: "CheckoutData"


class CheckoutData(BaseModel):
    """Checkout data with Snap token"""

    invoice_id: UUID
    invoice_number: str
    amount_cents: int
    currency: str
    snap_token: str
    redirect_url: str


# =============================================================================
# Invoice Schemas
# =============================================================================


class LineItemResponse(BaseModel):
    """Invoice line item"""

    description: str
    quantity: int
    unit_price_cents: int
    amount_cents: int


class InvoiceResponse(BaseModel):
    """Invoice response"""

    invoice_id: UUID
    tenant_id: UUID
    invoice_number: str
    amount_cents: int
    currency: str
    line_items: List[LineItemResponse]
    tax_rate: float
    tax_amount_cents: int
    total_cents: int
    status: str
    invoice_date: date
    due_date: date
    paid_at: Optional[datetime] = None
    created_at: datetime
    amount_display: str = ""

    class Config:
        from_attributes = True


class InvoicesListResponse(BaseModel):
    """List of invoices response"""

    success: bool = True
    data: List[InvoiceResponse]


class InvoiceDetailResponse(BaseModel):
    """Single invoice response"""

    success: bool = True
    data: InvoiceResponse


# =============================================================================
# Cancel/Reactivate Schemas
# =============================================================================


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""

    reason: Optional[str] = Field(None, max_length=500)
    immediate: bool = False


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = True
    message: str = "Operation completed successfully"


# =============================================================================
# Webhook Schemas
# =============================================================================


class WebhookResponse(BaseModel):
    """Webhook acknowledgment"""

    success: bool = True


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorDetail(BaseModel):
    """Error detail"""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response"""

    success: bool = False
    error: ErrorDetail


# Update forward references
SubscriptionDetailsResponse.model_rebuild()
CheckoutResponse.model_rebuild()
