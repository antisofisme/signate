"""
Shared Response Formatters
Standardized response format for all API endpoints
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    data: Any
    message: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: Dict[str, Any]
    timestamp: str = datetime.utcnow().isoformat()


class PaginatedResponse(BaseModel):
    """Paginated response"""
    success: bool = True
    data: List[Any]
    pagination: Dict[str, int]
    timestamp: str = datetime.utcnow().isoformat()


# =============================================================================
# RESPONSE HELPERS
# =============================================================================

def success_response(
    data: Any,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response

    Args:
        data: The response data
        message: Optional success message

    Returns:
        Dict with standardized success response format

    Example:
        >>> success_response({"id": 1, "name": "Device 1"}, "Device created successfully")
        {
            "success": True,
            "data": {"id": 1, "name": "Device 1"},
            "message": "Device created successfully",
            "timestamp": "2025-01-04T12:00:00.000000"
        }
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


def error_response(
    message: str,
    code: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """
    Create a standardized error response

    Args:
        message: Error message
        code: Error code
        details: Optional error details
        status_code: HTTP status code

    Returns:
        Dict with standardized error response format

    Example:
        >>> error_response("User not found", "NOT_FOUND", status_code=404)
        {
            "success": False,
            "error": {
                "message": "User not found",
                "code": "NOT_FOUND",
                "details": {}
            },
            "timestamp": "2025-01-04T12:00:00.000000"
        }
    """
    return {
        "success": False,
        "error": {
            "message": message,
            "code": code,
            "details": details or {},
            "status_code": status_code
        },
        "timestamp": datetime.utcnow().isoformat()
    }


def paginated_response(
    data: List[Any],
    page: int = 1,
    page_size: int = 10,
    total: int = 0
) -> Dict[str, Any]:
    """
    Create a paginated response

    Args:
        data: List of items
        page: Current page number
        page_size: Items per page
        total: Total number of items

    Returns:
        Dict with paginated response format

    Example:
        >>> paginated_response([{...}, {...}], page=1, page_size=10, total=25)
        {
            "success": True,
            "data": [{...}, {...}],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 25,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False
            },
            "timestamp": "2025-01-04T12:00:00.000000"
        }
    """
    import math

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": datetime.utcnow().isoformat()
    }


def created_response(
    data: Any,
    message: str = "Resource created successfully"
) -> Dict[str, Any]:
    """
    Create a 201 Created response

    Args:
        data: The created resource
        message: Success message

    Returns:
        Dict with standardized created response
    """
    return success_response(data, message)


def updated_response(
    data: Any,
    message: str = "Resource updated successfully"
) -> Dict[str, Any]:
    """
    Create a 200 Updated response

    Args:
        data: The updated resource
        message: Success message

    Returns:
        Dict with standardized updated response
    """
    return success_response(data, message)


def deleted_response(
    message: str = "Resource deleted successfully"
) -> Dict[str, Any]:
    """
    Create a 200 Deleted response

    Args:
        message: Success message

    Returns:
        Dict with standardized deleted response
    """
    return success_response(None, message)


# =============================================================================
# VALIDATION ERROR RESPONSE
# =============================================================================

def validation_error_response(
    errors: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a validation error response

    Args:
        errors: List of validation errors from Pydantic

    Returns:
        Dict with standardized validation error response

    Example:
        >>> validation_error_response([
        ...     {"field": "email", "message": "Invalid email format"}
        ... ])
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": {
                    "errors": [{"field": "email", "message": "Invalid email format"}]
                }
            },
            "timestamp": "2025-01-04T12:00:00.000000"
        }
    """
    return error_response(
        message="Validation failed",
        code="VALIDATION_ERROR",
        details={"errors": errors},
        status_code=400
    )
