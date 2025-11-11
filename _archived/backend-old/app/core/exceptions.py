"""
Custom Exception Classes and Handlers
Standardized error handling for consistent API error responses
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

from app.schemas.common import ErrorResponse, ErrorDetail, ResponseMeta
from app.middleware.request_id import get_request_id

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM EXCEPTION CLASSES
# =============================================================================

class APIException(Exception):
    """
    Base API Exception for standardized error handling

    All custom exceptions should inherit from this class to ensure
    consistent error response format across the application.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., "DEVICE_NOT_FOUND")
        status_code: HTTP status code (default: 400)
        field: Optional field name for validation errors
        details: Optional additional context
    """

    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field
        self.details = details or {}
        super().__init__(self.message)

    def to_error_response(self, request_id: Optional[str] = None) -> ErrorResponse:
        """Convert exception to ErrorResponse schema"""
        error_detail = ErrorDetail(
            code=self.code,
            message=self.message,
            field=self.field,
            details=self.details if self.details else None
        )
        meta = ResponseMeta(request_id=request_id)
        return ErrorResponse(error=error_detail, meta=meta)


# =============================================================================
# SPECIFIC EXCEPTION TYPES
# =============================================================================

class ValidationException(APIException):
    """Raised when request validation fails"""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            field=field,
            details=details
        )


class NotFoundException(APIException):
    """Raised when requested resource is not found"""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details if details else None
        )


class UnauthorizedException(APIException):
    """Raised when authentication is required but not provided"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(APIException):
    """Raised when user doesn't have permission for the action"""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictException(APIException):
    """Raised when resource conflict occurs (e.g., duplicate entry)"""

    def __init__(
        self,
        message: str = "Resource conflict",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            field=field,
            details=details
        )


class BadRequestException(APIException):
    """Raised when request is malformed or invalid"""

    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class InternalServerException(APIException):
    """Raised when an internal server error occurs"""

    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="INTERNAL_SERVER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DatabaseException(APIException):
    """Raised when database operation fails"""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceException(APIException):
    """Raised when external service call fails"""

    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if service_name:
            error_details["service"] = service_name

        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details if error_details else None
        )


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handler for custom APIException and its subclasses

    Returns standardized error response with request_id for tracing
    """
    request_id = get_request_id(request)

    # Log the error
    logger.warning(
        f"[{request_id}] {exc.code}: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "status_code": exc.status_code,
            "field": exc.field,
            "details": exc.details
        }
    )

    # Convert to ErrorResponse
    error_response = exc.to_error_response(request_id=request_id)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for FastAPI RequestValidationError (Pydantic validation errors)

    Converts Pydantic validation errors to standardized error format
    """
    request_id = get_request_id(request)

    # Extract validation errors
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    # Format field path
    field_path = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    error_msg = first_error.get("msg", "Validation failed")

    # Build error details
    details = {
        "validation_errors": [
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", "")
            }
            for err in errors
        ]
    }

    # Log validation error
    logger.warning(
        f"[{request_id}] Validation error: {field_path} - {error_msg}",
        extra={
            "request_id": request_id,
            "validation_errors": details["validation_errors"]
        }
    )

    # Create error response
    error_detail = ErrorDetail(
        code="VALIDATION_ERROR",
        message=f"Validation failed: {error_msg}",
        field=field_path if field_path else None,
        details=details
    )
    meta = ResponseMeta(request_id=request_id)
    error_response = ErrorResponse(error=error_detail, meta=meta)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handler for SQLAlchemy IntegrityError (e.g., unique constraint violations)

    Converts database constraint errors to user-friendly messages
    """
    request_id = get_request_id(request)

    # Parse error message
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

    # Detect common constraint violations
    if "unique constraint" in error_msg.lower():
        message = "A record with this value already exists"
        code = "DUPLICATE_ENTRY"
    elif "foreign key constraint" in error_msg.lower():
        message = "Referenced record does not exist"
        code = "FOREIGN_KEY_VIOLATION"
    elif "not null constraint" in error_msg.lower():
        message = "Required field is missing"
        code = "NULL_CONSTRAINT_VIOLATION"
    else:
        message = "Database constraint violation"
        code = "INTEGRITY_ERROR"

    # Log the error
    logger.error(
        f"[{request_id}] Database integrity error: {error_msg}",
        extra={
            "request_id": request_id,
            "error_code": code
        },
        exc_info=True
    )

    # Create error response
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details={"database_error": error_msg[:200]}  # Truncate for security
    )
    meta = ResponseMeta(request_id=request_id)
    error_response = ErrorResponse(error=error_detail, meta=meta)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for general SQLAlchemy errors

    Provides safe error messages without exposing database details
    """
    request_id = get_request_id(request)

    # Log the full error
    logger.error(
        f"[{request_id}] Database error: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )

    # Create generic error response (don't expose DB details)
    error_detail = ErrorDetail(
        code="DATABASE_ERROR",
        message="A database error occurred. Please try again later."
    )
    meta = ResponseMeta(request_id=request_id)
    error_response = ErrorResponse(error=error_detail, meta=meta)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions

    Catches all other exceptions and returns standardized error response
    """
    request_id = get_request_id(request)

    # Log the unexpected error
    logger.error(
        f"[{request_id}] Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )

    # Create generic error response
    error_detail = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later."
    )
    meta = ResponseMeta(request_id=request_id)
    error_response = ErrorResponse(error=error_detail, meta=meta)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app

    Usage in main.py:
        from app.core.exceptions import register_exception_handlers
        register_exception_handlers(app)
    """
    # Custom API exceptions
    app.add_exception_handler(APIException, api_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Database errors
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    # Generic exception (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("✓ Exception handlers registered")
