"""
Custom exceptions for ATLAS_CHAT_AI.
"""

from typing import Optional, Dict, Any


class ChatAIError(Exception):
    """
    Base exception for ATLAS_CHAT_AI.

    All custom exceptions should inherit from this.
    """
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to error response dict."""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class NotFoundError(ChatAIError):
    """Resource not found."""
    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message is None:
            if resource_id:
                message = f"{resource} with ID '{resource_id}' not found"
            else:
                message = f"{resource} not found"

        super().__init__(
            message=message,
            code=f"{resource.upper()}_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class ValidationError(ChatAIError):
    """Validation failed."""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=error_details
        )


class AuthenticationError(ChatAIError):
    """Authentication failed."""
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details
        )


class AuthorizationError(ChatAIError):
    """Authorization failed (insufficient permissions)."""
    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission

        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=error_details
        )


class RateLimitError(ChatAIError):
    """Rate limit exceeded."""
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after

        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429,
            details=error_details
        )


class ExternalServiceError(ChatAIError):
    """External service error (LLM, Qdrant, etc.)."""
    def __init__(
        self,
        service: str,
        message: Optional[str] = None,
        original_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["service"] = service
        if original_error:
            error_details["original_error"] = original_error

        super().__init__(
            message=message or f"Error communicating with {service}",
            code=f"{service.upper()}_ERROR",
            status_code=502,
            details=error_details
        )


class ContextTooLongError(ChatAIError):
    """Context exceeds token limit."""
    def __init__(
        self,
        current_tokens: int,
        max_tokens: int,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["current_tokens"] = current_tokens
        error_details["max_tokens"] = max_tokens

        super().__init__(
            message=f"Context too long: {current_tokens} tokens exceeds limit of {max_tokens}",
            code="CONTEXT_TOO_LONG",
            status_code=400,
            details=error_details
        )


class TenantNotFoundError(NotFoundError):
    """Tenant not found or inactive."""
    def __init__(self, tenant_id: str):
        super().__init__(
            resource="tenant",
            resource_id=tenant_id,
            message=f"Tenant '{tenant_id}' not found or inactive"
        )


class SessionNotFoundError(NotFoundError):
    """Session not found."""
    def __init__(self, session_id: str):
        super().__init__(
            resource="session",
            resource_id=session_id
        )


class SessionLimitExceededError(ChatAIError):
    """User has reached session limit."""
    def __init__(
        self,
        current_count: int,
        max_count: int
    ):
        super().__init__(
            message=f"Session limit exceeded: {current_count}/{max_count}",
            code="SESSION_LIMIT_EXCEEDED",
            status_code=400,
            details={
                "current_count": current_count,
                "max_count": max_count
            }
        )
