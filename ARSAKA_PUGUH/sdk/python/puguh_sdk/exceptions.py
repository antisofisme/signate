"""
PUGUH SDK - Exceptions

Custom exception hierarchy for PUGUH Platform SDK.
All exceptions inherit from PuguhError base class.
"""

from typing import Optional, Dict, Any


class PuguhError(Exception):
    """
    Base exception for all PUGUH SDK errors.

    Attributes:
        message: Human-readable error message
        code: Error code from API
        details: Additional error details
        status_code: HTTP status code (if applicable)
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def __str__(self):
        return f"[{self.code}] {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# =============================================================================
# Authentication Errors
# =============================================================================

class AuthError(PuguhError):
    """
    Authentication error.

    Raised when:
    - Invalid credentials
    - Invalid/expired token
    - Unauthorized access
    """

    def __init__(
        self,
        message: str,
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=401)


class TokenExpiredError(AuthError):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="TOKEN_EXPIRED")


class InvalidCredentialsError(AuthError):
    """Invalid email or password."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, code="INVALID_CREDENTIALS")


class EmailNotVerifiedError(AuthError):
    """Email not yet verified."""

    def __init__(self, message: str = "Email not verified"):
        super().__init__(message, code="EMAIL_NOT_VERIFIED")


# =============================================================================
# Tenant Errors
# =============================================================================

class TenantError(PuguhError):
    """
    Tenant (organization) error.

    Raised when:
    - Tenant not found
    - Access denied to tenant
    - Tenant limit exceeded
    """

    def __init__(
        self,
        message: str,
        code: str = "TENANT_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=403)


class TenantNotFoundError(TenantError):
    """Tenant not found."""

    def __init__(self, tenant_id: str, message: str = "Tenant not found"):
        super().__init__(message, code="TENANT_NOT_FOUND", details={"tenant_id": tenant_id})
        self.tenant_id = tenant_id


class TenantAccessDeniedError(TenantError):
    """Access to tenant denied."""

    def __init__(self, tenant_id: str, message: str = "Access denied to tenant"):
        super().__init__(message, code="TENANT_ACCESS_DENIED", details={"tenant_id": tenant_id})
        self.tenant_id = tenant_id


class TenantLimitExceededError(TenantError):
    """Tenant limit exceeded (members, projects, etc)."""

    def __init__(self, limit_type: str, current: int, maximum: int):
        message = f"{limit_type} limit exceeded: {current}/{maximum}"
        super().__init__(
            message,
            code="TENANT_LIMIT_EXCEEDED",
            details={
                "limit_type": limit_type,
                "current": current,
                "maximum": maximum,
            }
        )
        self.limit_type = limit_type
        self.current = current
        self.maximum = maximum


class TenantIsolationViolationError(TenantError):
    """
    Cross-tenant access violation.

    Raised when attempting to access resources from another tenant.
    """

    def __init__(self, message: str = "Tenant isolation violation"):
        super().__init__(message, code="TENANT_ISOLATION_VIOLATION")


# =============================================================================
# Project Errors
# =============================================================================

class ProjectError(PuguhError):
    """Project-related error."""

    def __init__(
        self,
        message: str,
        code: str = "PROJECT_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=403)


class ProjectNotFoundError(ProjectError):
    """Project not found."""

    def __init__(self, project_id: str, message: str = "Project not found"):
        super().__init__(message, code="PROJECT_NOT_FOUND", details={"project_id": project_id})
        self.project_id = project_id


# =============================================================================
# Billing Errors
# =============================================================================

class BillingError(PuguhError):
    """Billing-related error."""

    def __init__(
        self,
        message: str,
        code: str = "BILLING_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=402)


class SubscriptionRequiredError(BillingError):
    """Active subscription required."""

    def __init__(self, product: str, message: str = "Subscription required"):
        super().__init__(
            message,
            code="SUBSCRIPTION_REQUIRED",
            details={"product": product}
        )
        self.product = product


class SubscriptionExpiredError(BillingError):
    """Subscription has expired."""

    def __init__(self, product: str, message: str = "Subscription expired"):
        super().__init__(
            message,
            code="SUBSCRIPTION_EXPIRED",
            details={"product": product}
        )
        self.product = product


class PaymentFailedError(BillingError):
    """Payment processing failed."""

    def __init__(self, message: str = "Payment failed"):
        super().__init__(message, code="PAYMENT_FAILED")


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(PuguhError):
    """
    Input validation error.

    Raised when request data fails validation.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details, status_code=422)


# =============================================================================
# Network Errors
# =============================================================================

class NetworkError(PuguhError):
    """
    Network communication error.

    Raised when HTTP request fails due to network issues.
    """

    def __init__(self, message: str):
        super().__init__(message, "NETWORK_ERROR")


class TimeoutError(NetworkError):
    """Request timed out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)
        self.code = "TIMEOUT"


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimitError(PuguhError):
    """
    Rate limit exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message,
            "RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=429
        )
        self.retry_after = retry_after


# =============================================================================
# Core Service Errors (for backward compatibility)
# =============================================================================

class CoreServiceError(PuguhError):
    """Base exception for Core Service API errors."""
    pass


class IdempotencyConflictError(CoreServiceError):
    """
    Idempotency key conflict.

    Raised when the same idempotency key was used for a different request.
    """

    def __init__(
        self,
        message: str,
        existing_decision_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "IDEMPOTENCY_CONFLICT", details, status_code=409)
        self.existing_decision_id = existing_decision_id


class WorkflowNotFoundError(CoreServiceError):
    """Workflow not found."""

    def __init__(
        self,
        message: str,
        workflow_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "WORKFLOW_NOT_FOUND", details, status_code=404)
        self.workflow_id = workflow_id


class ApproverRoleMismatchError(CoreServiceError):
    """Approver role does not match workflow requirements."""

    def __init__(
        self,
        message: str,
        expected: str,
        actual: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "APPROVER_ROLE_MISMATCH", details, status_code=403)
        self.expected = expected
        self.actual = actual


class InvalidWorkflowTransitionError(CoreServiceError):
    """Invalid workflow state transition."""

    def __init__(
        self,
        message: str,
        from_state: str,
        to_state: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "INVALID_WORKFLOW_TRANSITION", details, status_code=400)
        self.from_state = from_state
        self.to_state = to_state
