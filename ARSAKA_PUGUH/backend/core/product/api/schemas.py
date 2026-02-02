"""
Product API Schemas

Pydantic models for Product HTTP transport.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Product Info
# ============================================================================

class ProductFeatures(BaseModel):
    """Product features."""
    mcp_integration: bool = False
    api_access: bool = False
    sso_support: bool = False
    webhooks: bool = False
    custom_branding: bool = False


class ProductInfo(BaseModel):
    """Product information."""
    product_id: str
    code: str
    name: str
    description: Optional[str] = None
    tagline: Optional[str] = None
    icon_url: Optional[str] = None
    logo_url: Optional[str] = None
    color_primary: Optional[str] = None
    app_url: Optional[str] = None
    docs_url: Optional[str] = None
    status: str
    is_featured: bool
    features: ProductFeatures
    display_order: int


class ProductWithSubscription(BaseModel):
    """Product with subscription status."""
    product: ProductInfo
    is_subscribed: bool
    subscription_status: Optional[str] = None
    plan_id: Optional[str] = None
    trial_days_remaining: int = 0


# ============================================================================
# List Products
# ============================================================================

class ListProductsData(BaseModel):
    """List products response data."""
    products: List[ProductWithSubscription]
    subscribed_count: int
    total_count: int


class ListProductsResponse(BaseModel):
    """GET /products response."""
    success: bool = True
    data: ListProductsData


# ============================================================================
# Get Product
# ============================================================================

class GetProductResponse(BaseModel):
    """GET /products/{code} response."""
    success: bool = True
    data: ProductWithSubscription


# ============================================================================
# Check Product Access
# ============================================================================

class ProductAccessData(BaseModel):
    """Product access check result."""
    has_access: bool
    product_code: str
    plan_id: Optional[str] = None
    status: Optional[str] = None
    is_trial: bool
    trial_days_remaining: int
    usage_this_period: int
    usage_limit: Optional[int] = None
    reason: Optional[str] = None


class ProductAccessResponse(BaseModel):
    """GET /products/{code}/access response."""
    success: bool = True
    data: ProductAccessData


# ============================================================================
# Tenant's Product Subscriptions
# ============================================================================

class SubscriptionInfo(BaseModel):
    """Product subscription info."""
    subscription_id: str
    product_id: str
    product_code: str
    plan_id: str
    status: str
    is_trial: bool
    trial_days_remaining: int
    usage_this_period: int
    usage_limit: Optional[int] = None
    created_at: str


class ListSubscriptionsData(BaseModel):
    """List subscriptions response data."""
    subscriptions: List[SubscriptionInfo]
    total: int


class ListSubscriptionsResponse(BaseModel):
    """GET /products/subscriptions response."""
    success: bool = True
    data: ListSubscriptionsData


# ============================================================================
# Error Response
# ============================================================================

class ProductErrorDetail(BaseModel):
    """Error detail for product operations."""
    code: str
    message: str


class ProductErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: ProductErrorDetail
