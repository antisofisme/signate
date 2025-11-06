"""
Common Response Schemas
Standardized API response formats for consistency across all endpoints
"""

from typing import Any, Optional, Dict, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

# Generic type for data payload
T = TypeVar('T')


class ResponseMeta(BaseModel):
    """
    Metadata for API responses

    Attributes:
        timestamp: ISO format timestamp of response generation
        request_id: Unique identifier for request tracing (populated by middleware)
        version: API version (optional)
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    version: str = "1.0.0"

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-27T10:30:00Z",
                "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "version": "1.0.0"
            }
        }


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response wrapper

    Wraps all successful API responses with consistent structure:
    - success: Boolean flag indicating success
    - data: The actual response payload (generic type)
    - meta: Metadata about the response (timestamp, request_id, etc.)

    Usage:
        return APIResponse(
            success=True,
            data={"user_id": 123, "name": "John"},
            meta=ResponseMeta(request_id=request.state.request_id)
        )
    """
    success: bool = Field(
        default=True,
        description="Indicates if the request was successful"
    )
    data: T = Field(
        description="Response payload - can be any type (object, list, string, etc.)"
    )
    meta: ResponseMeta = Field(
        default_factory=ResponseMeta,
        description="Metadata about the response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "id": 1,
                    "name": "Example Data"
                },
                "meta": {
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "version": "1.0.0"
                }
            }
        }


class PaginationMeta(ResponseMeta):
    """
    Extended metadata for paginated responses

    Includes standard pagination information:
    - total: Total number of items across all pages
    - page: Current page number (1-indexed)
    - page_size: Number of items per page
    - total_pages: Total number of pages
    """
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-27T10:30:00Z",
                "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "version": "1.0.0",
                "total": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }


class PaginatedAPIResponse(BaseModel, Generic[T]):
    """
    Standardized paginated API response

    Used for endpoints that return lists with pagination support

    Usage:
        return PaginatedAPIResponse(
            success=True,
            data=items,
            meta=PaginationMeta(
                request_id=request.state.request_id,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total_count / page_size)
            )
        )
    """
    success: bool = Field(default=True)
    data: list[T] = Field(description="List of items for current page")
    meta: PaginationMeta

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "meta": {
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "version": "1.0.0",
                    "total": 150,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 8
                }
            }
        }


class SuccessResponse(BaseModel):
    """
    Simple success response with message and optional details

    Used for operations that don't return complex data (e.g., delete, validate)

    Attributes:
        message: Success message
        details: Optional additional context
    """
    message: str = Field(description="Success message")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "details": {"organization_name": "Acme Corp"}
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Alias for PaginatedAPIResponse for backward compatibility

    Use PaginatedAPIResponse for new code
    """
    success: bool = Field(default=True)
    data: list[T] = Field(description="List of items for current page")
    meta: PaginationMeta

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "meta": {
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "version": "1.0.0",
                    "total": 150,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 8
                }
            }
        }


class ErrorDetail(BaseModel):
    """
    Error detail structure for API errors

    Attributes:
        code: Machine-readable error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        field: Optional field name for validation errors
        details: Optional additional error context
    """
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name for validation errors")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid email format",
                "field": "email",
                "details": {"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
            }
        }


class ErrorResponse(BaseModel):
    """
    Standardized error response format

    Used by exception handlers to return consistent error structure

    Attributes:
        success: Always False for error responses
        error: Error details (code, message, field, details)
        meta: Response metadata including request_id for tracing
    """
    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(description="Error information")
    meta: ResponseMeta = Field(
        default_factory=ResponseMeta,
        description="Response metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Device not found",
                    "field": None,
                    "details": {"device_id": 123}
                },
                "meta": {
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "version": "1.0.0"
                }
            }
        }


# Helper functions for creating responses
def success_response(data: Any, request_id: Optional[str] = None, **meta_kwargs) -> APIResponse:
    """
    Helper function to create standardized success response

    Args:
        data: Response payload
        request_id: Optional request ID from middleware
        **meta_kwargs: Additional metadata fields

    Returns:
        APIResponse with standardized format
    """
    meta = ResponseMeta(request_id=request_id, **meta_kwargs)
    return APIResponse(success=True, data=data, meta=meta)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> tuple[ErrorResponse, int]:
    """
    Helper function to create standardized error response

    Args:
        code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code (default: 400)
        field: Optional field name for validation errors
        details: Optional additional error context
        request_id: Optional request ID from middleware

    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    error = ErrorDetail(code=code, message=message, field=field, details=details)
    meta = ResponseMeta(request_id=request_id)
    return ErrorResponse(error=error, meta=meta), status_code


def paginated_response(
    data: list,
    total: int,
    page: int,
    page_size: int,
    request_id: Optional[str] = None
) -> PaginatedAPIResponse:
    """
    Helper function to create standardized paginated response

    Args:
        data: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page
        request_id: Optional request ID from middleware

    Returns:
        PaginatedAPIResponse with standardized format
    """
    import math
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    meta = PaginationMeta(
        request_id=request_id,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    return PaginatedAPIResponse(success=True, data=data, meta=meta)
