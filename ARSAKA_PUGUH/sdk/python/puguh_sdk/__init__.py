"""
PUGUH SDK - Python client for PUGUH Platform.

PUGUH provides infrastructure for SaaS applications:
- Authentication & user management
- Multi-tenant organization management
- Project isolation
- Billing & subscriptions

Quick Start:
    ```python
    from puguh_sdk import PuguhClient

    # Initialize client
    client = PuguhClient(
        base_url="https://api.puguh.io",
        access_token="your_jwt_token"
    )

    # Use services
    async with client:
        # List organizations
        tenants = await client.tenants.list()

        # Create project
        project = await client.projects.create(
            tenant_id=tenants[0].tenant_id,
            name="My Project"
        )

        # Get billing plans
        plans = await client.billing.get_plans()
    ```

For service-to-service communication:
    ```python
    from puguh_sdk import PuguhClient

    client = PuguhClient(
        base_url="https://api.puguh.io",
        api_key="pk_live_xxxxxxxxxxxx"
    )

    # Set tenant context for operations
    client.set_tenant_context(tenant_id="tenant_uuid")
    ```
"""

__version__ = "1.0.0"

# Main client
from .client import PuguhClient, create_client

# Sub-clients (for type hints)
from .auth import (
    AuthClient,
    AuthProvider,
    TokenPair,
    UserContext,
    User,
)
from .tenant import (
    TenantClient,
    Tenant,
    TenantPlan,
    TenantStatus,
    Member,
    MemberRole,
    Invitation,
    InvitationStatus,
)
from .project import (
    ProjectClient,
    Project,
    ProjectVisibility,
    ProjectMember,
    ProjectMemberRole,
)
from .billing import (
    BillingClient,
    Plan,
    Subscription,
    SubscriptionStatus,
    Invoice,
    PaymentStatus,
    BillingInterval,
    UsageMetrics,
)

# Exceptions
from .exceptions import (
    # Base
    PuguhError,
    # Auth
    AuthError,
    TokenExpiredError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    # Tenant
    TenantError,
    TenantNotFoundError,
    TenantAccessDeniedError,
    TenantLimitExceededError,
    TenantIsolationViolationError,
    # Project
    ProjectError,
    ProjectNotFoundError,
    # Billing
    BillingError,
    SubscriptionRequiredError,
    SubscriptionExpiredError,
    PaymentFailedError,
    # Validation
    ValidationError,
    # Network
    NetworkError,
    TimeoutError,
    RateLimitError,
    # Core service (backward compatibility)
    CoreServiceError,
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "PuguhClient",
    "create_client",
    # Auth
    "AuthClient",
    "AuthProvider",
    "TokenPair",
    "UserContext",
    "User",
    # Tenant
    "TenantClient",
    "Tenant",
    "TenantPlan",
    "TenantStatus",
    "Member",
    "MemberRole",
    "Invitation",
    "InvitationStatus",
    # Project
    "ProjectClient",
    "Project",
    "ProjectVisibility",
    "ProjectMember",
    "ProjectMemberRole",
    # Billing
    "BillingClient",
    "Plan",
    "Subscription",
    "SubscriptionStatus",
    "Invoice",
    "PaymentStatus",
    "BillingInterval",
    "UsageMetrics",
    # Exceptions
    "PuguhError",
    "AuthError",
    "TokenExpiredError",
    "InvalidCredentialsError",
    "EmailNotVerifiedError",
    "TenantError",
    "TenantNotFoundError",
    "TenantAccessDeniedError",
    "TenantLimitExceededError",
    "TenantIsolationViolationError",
    "ProjectError",
    "ProjectNotFoundError",
    "BillingError",
    "SubscriptionRequiredError",
    "SubscriptionExpiredError",
    "PaymentFailedError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "CoreServiceError",
    "IdempotencyConflictError",
    "WorkflowNotFoundError",
    "ApproverRoleMismatchError",
    "InvalidWorkflowTransitionError",
]
