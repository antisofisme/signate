"""
Product Domain Entity

Represents a product in the PUGUH platform catalog.
Products are SaaS applications that tenants can subscribe to.

Examples: MANTRA (Decision Governance), Future products...
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ProductStatus(str, Enum):
    """Product availability status."""
    ACTIVE = "active"           # Available for subscription
    COMING_SOON = "coming_soon" # Announced but not available
    BETA = "beta"               # Available for beta testers
    DEPRECATED = "deprecated"   # No new subscriptions
    DISABLED = "disabled"       # Hidden from catalog


@dataclass
class ProductFeatures:
    """Feature flags for a product."""

    mcp_integration: bool = False   # MCP server support
    api_access: bool = False        # REST API available
    sso_support: bool = False       # SSO integration
    webhooks: bool = False          # Webhook notifications
    custom_branding: bool = False   # White-label support

    @classmethod
    def from_dict(cls, data: dict) -> "ProductFeatures":
        return cls(
            mcp_integration=data.get("mcp_integration", False),
            api_access=data.get("api_access", False),
            sso_support=data.get("sso_support", False),
            webhooks=data.get("webhooks", False),
            custom_branding=data.get("custom_branding", False),
        )

    def to_dict(self) -> dict:
        return {
            "mcp_integration": self.mcp_integration,
            "api_access": self.api_access,
            "sso_support": self.sso_support,
            "webhooks": self.webhooks,
            "custom_branding": self.custom_branding,
        }


@dataclass
class Product:
    """
    Product Entity

    Represents a SaaS product in the PUGUH platform.
    Tenants subscribe to products to access their features.
    """

    # Identity
    product_id: UUID
    code: str           # Unique code: "mantra", "future_product"
    name: str           # Display name: "MANTRA"
    description: Optional[str] = None
    tagline: Optional[str] = None  # Short tagline for cards

    # Visual
    icon_url: Optional[str] = None      # Product icon
    logo_url: Optional[str] = None      # Full logo
    color_primary: Optional[str] = None # Brand color (hex)
    color_secondary: Optional[str] = None

    # URLs
    app_url: Optional[str] = None       # Product app URL
    docs_url: Optional[str] = None      # Documentation URL
    support_url: Optional[str] = None   # Support URL

    # Status
    status: ProductStatus = ProductStatus.ACTIVE
    is_featured: bool = False           # Featured in catalog

    # Features
    features: ProductFeatures = field(default_factory=ProductFeatures)

    # Display
    display_order: int = 0              # Sort order in catalog

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        description: Optional[str] = None,
        tagline: Optional[str] = None,
        app_url: Optional[str] = None,
        status: ProductStatus = ProductStatus.ACTIVE,
    ) -> "Product":
        """Create a new product."""
        return cls(
            product_id=uuid4(),
            code=code.lower(),
            name=name,
            description=description,
            tagline=tagline,
            app_url=app_url,
            status=status,
        )

    @property
    def is_available(self) -> bool:
        """Check if product is available for subscription."""
        return self.status in (ProductStatus.ACTIVE, ProductStatus.BETA)

    @property
    def is_visible(self) -> bool:
        """Check if product should be shown in catalog."""
        return self.status != ProductStatus.DISABLED

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "product_id": str(self.product_id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "tagline": self.tagline,
            "icon_url": self.icon_url,
            "logo_url": self.logo_url,
            "color_primary": self.color_primary,
            "app_url": self.app_url,
            "docs_url": self.docs_url,
            "status": self.status.value,
            "is_featured": self.is_featured,
            "features": self.features.to_dict(),
            "display_order": self.display_order,
        }


# ============================================================================
# Pre-defined Products
# ============================================================================

MANTRA_PRODUCT = Product(
    product_id=UUID("00000000-0000-0000-0000-000000000001"),
    code="mantra",
    name="MANTRA",
    description="Decision Governance Platform - Record, validate, and enforce architectural decisions using constitutional law principles.",
    tagline="Constitutional Law for Software Decisions",
    color_primary="#2563EB",  # Blue
    status=ProductStatus.ACTIVE,
    is_featured=True,
    features=ProductFeatures(
        mcp_integration=True,
        api_access=True,
        webhooks=True,
    ),
    display_order=1,
)
