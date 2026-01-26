"""
Tenant Domain Entity

Core business entity representing an organization/workspace.
Framework-agnostic, pure Python.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum
import re


class TenantStatus(str, Enum):
    """Tenant account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class TenantPlan(str, Enum):
    """Subscription plan."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Plan limits
PLAN_LIMITS = {
    TenantPlan.FREE: {
        "max_projects": 1,
        "max_members": 3,
        "max_decisions_per_month": 1000,
    },
    TenantPlan.STARTER: {
        "max_projects": 5,
        "max_members": 10,
        "max_decisions_per_month": 10000,
    },
    TenantPlan.PRO: {
        "max_projects": -1,  # Unlimited
        "max_members": 50,
        "max_decisions_per_month": 100000,
    },
    TenantPlan.ENTERPRISE: {
        "max_projects": -1,  # Unlimited
        "max_members": -1,  # Unlimited
        "max_decisions_per_month": -1,  # Unlimited
    },
}


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name.

    Args:
        name: Tenant name

    Returns:
        Lowercase, hyphenated slug
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove any non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


@dataclass
class Tenant:
    """
    Tenant domain entity.

    Represents an organization/workspace in the SaaS platform.
    Users belong to tenants via memberships.
    """
    # Identity
    tenant_id: UUID
    name: str
    slug: str

    # Owner (user who created this tenant)
    owner_user_id: UUID

    # Plan & Status
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE

    # Settings (JSON)
    settings: dict = field(default_factory=dict)

    # Billing info
    billing_email: Optional[str] = None

    # Soft delete
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate tenant entity."""
        # Name must be at least 2 characters
        if len(self.name.strip()) < 2:
            raise ValueError("Tenant name must be at least 2 characters")

        # Generate slug if not provided
        if not self.slug:
            self.slug = generate_slug(self.name)

        # Slug must be at least 2 characters
        if len(self.slug) < 2:
            raise ValueError("Tenant slug must be at least 2 characters")

    @classmethod
    def create(
        cls,
        name: str,
        owner_user_id: UUID,
        slug: Optional[str] = None,
        plan: TenantPlan = TenantPlan.FREE,
        billing_email: Optional[str] = None,
    ) -> "Tenant":
        """Create a new tenant.

        Args:
            name: Tenant display name
            owner_user_id: User ID of the owner
            slug: URL-friendly identifier (auto-generated if not provided)
            plan: Subscription plan
            billing_email: Email for billing notifications

        Returns:
            New Tenant entity
        """
        return cls(
            tenant_id=uuid4(),
            name=name.strip(),
            slug=slug or generate_slug(name),
            owner_user_id=owner_user_id,
            plan=plan,
            billing_email=billing_email,
        )

    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL) and not self.is_deleted

    def get_limit(self, limit_key: str) -> int:
        """Get plan limit value.

        Args:
            limit_key: One of max_projects, max_members, max_decisions_per_month

        Returns:
            Limit value (-1 for unlimited)
        """
        return PLAN_LIMITS[self.plan].get(limit_key, 0)

    def can_add_member(self, current_count: int) -> bool:
        """Check if can add more members.

        Args:
            current_count: Current member count

        Returns:
            True if under limit
        """
        max_members = self.get_limit("max_members")
        return max_members == -1 or current_count < max_members

    def can_add_project(self, current_count: int) -> bool:
        """Check if can add more projects.

        Args:
            current_count: Current project count

        Returns:
            True if under limit
        """
        max_projects = self.get_limit("max_projects")
        return max_projects == -1 or current_count < max_projects

    def update(
        self,
        name: Optional[str] = None,
        billing_email: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> None:
        """Update tenant properties.

        Args:
            name: New name (slug will be regenerated)
            billing_email: New billing email
            settings: Settings to merge
        """
        if name is not None:
            self.name = name.strip()
            # Optionally regenerate slug (controlled separately)
        if billing_email is not None:
            self.billing_email = billing_email
        if settings is not None:
            self.settings.update(settings)
        self.updated_at = datetime.utcnow()

    def upgrade_plan(self, new_plan: TenantPlan) -> None:
        """Upgrade/change subscription plan."""
        self.plan = new_plan
        self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend tenant."""
        self.status = TenantStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate tenant."""
        self.status = TenantStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete tenant."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "slug": self.slug,
            "owner_user_id": str(self.owner_user_id),
            "plan": self.plan.value,
            "status": self.status.value,
            "settings": self.settings,
            "billing_email": self.billing_email,
            "limits": {
                "max_projects": self.get_limit("max_projects"),
                "max_members": self.get_limit("max_members"),
                "max_decisions_per_month": self.get_limit("max_decisions_per_month"),
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
