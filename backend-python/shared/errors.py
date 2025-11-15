"""
Shared Error Classes and Handlers
Centralized error handling for the application
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


# =============================================================================
# BASE EXCEPTION CLASSES
# =============================================================================

class AppException(Exception):
    """Base exception for application errors"""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# SPECIFIC EXCEPTION CLASSES
# =============================================================================

class ValidationError(AppException):
    """Validation error (400)"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(AppException):
    """Authentication error (401)"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(AppException):
    """Authorization error (403)"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundError(AppException):
    """Resource not found error (404)"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictError(AppException):
    """Conflict error (409)"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(AppException):
    """Rate limit exceeded error (429)"""
    def __init__(self, message: str = "Too many requests", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class DatabaseError(AppException):
    """Database error (500)"""
    def __init__(self, message: str = "Database error occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceError(AppException):
    """External service error (502)"""
    def __init__(self, message: str = "External service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


# =============================================================================
# ERROR CODES
# =============================================================================

class ErrorCodes:
    """Centralized error codes"""

    # Authentication & Authorization
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INVALID_TOKEN = "INVALID_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    ACCESS_DENIED = "ACCESS_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    SESSION_REVOKED = "SESSION_REVOKED"  # BUG FIX #3
    SESSION_EXPIRED = "SESSION_EXPIRED"  # Additional error code

    # Validation
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Resources
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"  # BUG FIX #2

    # Business Logic
    ACTIVATION_CODE_EXPIRED = "ACTIVATION_CODE_EXPIRED"
    ACTIVATION_CODE_INVALID = "ACTIVATION_CODE_INVALID"
    DEVICE_ALREADY_ACTIVATED = "DEVICE_ALREADY_ACTIVATED"
    ORGANIZATION_NOT_FOUND = "ORGANIZATION_NOT_FOUND"

    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


# =============================================================================
# ERROR HANDLER DECORATOR
# =============================================================================

def handle_errors(func):
    """
    Decorator to handle errors and convert to HTTPException
    Supports both sync and async functions
    Usage:
        @handle_errors
        def my_endpoint():  # or async def
            ...
    """
    from functools import wraps
    import inspect

    # Check if function is async
    is_async = inspect.iscoroutinefunction(func)

    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AppException as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail={
                        "message": e.message,
                        "code": e.code,
                        "details": e.details
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                # Log unexpected errors
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": "An unexpected error occurred",
                        "code": ErrorCodes.INTERNAL_ERROR,
                        "details": {"error": str(e)}
                    }
                )
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppException as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail={
                        "message": e.message,
                        "code": e.code,
                        "details": e.details
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                # Log unexpected errors
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": "An unexpected error occurred",
                        "code": ErrorCodes.INTERNAL_ERROR,
                        "details": {"error": str(e)}
                    }
                )
        return sync_wrapper
