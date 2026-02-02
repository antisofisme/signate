"""
MANTRA SDK Exceptions
"""


class MantraError(Exception):
    """Base exception for MANTRA SDK errors."""

    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(MantraError):
    """Raised when decision validation fails."""

    def __init__(self, message: str, violations: list | None = None):
        super().__init__(message, code="VALIDATION_FAILED")
        self.violations = violations or []


class AuthorizationError(MantraError):
    """Raised when operation requires human authorization."""

    def __init__(self, message: str = "This operation requires human authorization"):
        super().__init__(message, code="AUTHORIZATION_REQUIRED")


class NotFoundError(MantraError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, code="NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ConnectionError(MantraError):
    """Raised when connection to MANTRA backend fails."""

    def __init__(self, message: str = "Failed to connect to MANTRA backend"):
        super().__init__(message, code="CONNECTION_ERROR")


class RateLimitError(MantraError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after
