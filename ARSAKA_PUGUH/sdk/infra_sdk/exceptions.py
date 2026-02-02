"""
SDK Exceptions - Explicit Error Types

Every error is explicit. NO silent failures. NO fallbacks.
Default behavior on any error: DENY.

Source: Phase 2 Requirements
"""


class InfraSDKError(Exception):
    """
    Base exception for all SDK errors.

    All SDK errors result in operation failure.
    NO fallback. NO retry. NO default behavior.
    """

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class MissingContextError(InfraSDKError):
    """
    Raised when required context is missing.

    This is a client error - the SDK consumer must provide all context.
    NO implicit defaults.
    """

    def __init__(self, missing_field: str):
        super().__init__(
            message=f"Required context field missing: {missing_field}",
            error_code="SDK_MISSING_CONTEXT"
        )
        self.missing_field = missing_field


class ValidationError(InfraSDKError):
    """
    Raised when request validation fails.

    SDK validates structure only (not business rules).
    """

    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=f"Validation failed: {message}",
            error_code="SDK_VALIDATION_ERROR"
        )
        self.field = field


class IdempotencyRequiredError(InfraSDKError):
    """
    Raised when idempotency key is missing for a mutating operation.

    ALL mutating operations REQUIRE idempotency key.
    NO exceptions. NO fallback.
    """

    def __init__(self, operation: str):
        super().__init__(
            message=f"Idempotency key is REQUIRED for operation: {operation}",
            error_code="SDK_IDEMPOTENCY_REQUIRED"
        )
        self.operation = operation


class CoreAPIError(InfraSDKError):
    """
    Raised when Core API returns an error.

    SDK does NOT interpret Core errors.
    SDK does NOT retry.
    SDK passes the error through.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        core_error_code: str = None,
        core_details: dict = None
    ):
        super().__init__(
            message=f"Core API error: {message}",
            error_code="SDK_CORE_API_ERROR"
        )
        self.status_code = status_code
        self.core_error_code = core_error_code
        self.core_details = core_details or {}


class TenantMismatchError(InfraSDKError):
    """
    Raised when tenant context doesn't match the operation target.

    Cross-tenant operations are FORBIDDEN.
    """

    def __init__(self, context_tenant: str, target_tenant: str):
        super().__init__(
            message=f"Tenant mismatch: context={context_tenant}, target={target_tenant}",
            error_code="SDK_TENANT_MISMATCH"
        )
        self.context_tenant = context_tenant
        self.target_tenant = target_tenant


class ConnectionError(InfraSDKError):
    """
    Raised when connection to Core API fails.

    SDK does NOT retry. SDK does NOT fallback.
    Caller must handle retry logic if desired.
    """

    def __init__(self, message: str):
        super().__init__(
            message=f"Connection failed: {message}",
            error_code="SDK_CONNECTION_ERROR"
        )
