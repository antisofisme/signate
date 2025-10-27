"""
Quick Wins Demo Endpoints
Demonstrates the 4 Quick Wins in action
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
import logging

from app.schemas.common import (
    APIResponse,
    PaginatedAPIResponse,
    success_response,
    paginated_response
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BadRequestException
)
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger

router = APIRouter()
logger = StructuredLogger(__name__)


@router.get("/demo/success")
async def demo_success_response(request: Request):
    """
    Demo: Success response with standardized APIResponse format

    Shows:
    - Standardized response wrapper
    - Request ID in metadata
    - Timestamp automatically added
    """
    request_id = get_request_id(request)

    # Log with structured data
    logger.info(
        "Success response demo called",
        request_id=request_id,
        endpoint="/demo/success"
    )

    # Return standardized response
    return success_response(
        data={
            "message": "This is a standardized success response",
            "features": [
                "Consistent response format",
                "Request ID tracking",
                "Automatic timestamps",
                "JSON structured logging"
            ]
        },
        request_id=request_id
    )


@router.get("/demo/paginated")
async def demo_paginated_response(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Demo: Paginated response with standardized format

    Shows:
    - Paginated response wrapper
    - Pagination metadata (total, page, page_size, total_pages)
    - Request ID tracking
    """
    request_id = get_request_id(request)

    # Simulate data
    total_items = 47
    items = [
        {"id": i, "name": f"Item {i}"}
        for i in range((page - 1) * page_size + 1, min(page * page_size + 1, total_items + 1))
    ]

    logger.info(
        "Paginated response demo called",
        request_id=request_id,
        page=page,
        page_size=page_size,
        total_items=total_items
    )

    return paginated_response(
        data=items,
        total=total_items,
        page=page,
        page_size=page_size,
        request_id=request_id
    )


@router.get("/demo/error-not-found")
async def demo_not_found_error(request: Request):
    """
    Demo: Not Found error with standardized format

    Shows:
    - Custom exception with consistent error format
    - Error code and message
    - Request ID in error response
    - Automatic logging
    """
    request_id = get_request_id(request)

    logger.warning(
        "Not found error demo - throwing NotFoundException",
        request_id=request_id
    )

    raise NotFoundException(
        message="Device with ID 999 not found",
        resource_type="Device",
        resource_id=999
    )


@router.get("/demo/error-validation")
async def demo_validation_error(request: Request, email: Optional[str] = None):
    """
    Demo: Validation error with standardized format

    Shows:
    - Validation exception with field info
    - Error details
    - Request ID tracking
    """
    request_id = get_request_id(request)

    if not email:
        raise ValidationException(
            message="Email is required",
            field="email",
            details={"required": True}
        )

    if "@" not in email:
        raise ValidationException(
            message="Invalid email format",
            field="email",
            details={"pattern": "must contain @"}
        )

    return success_response(
        data={"email": email, "valid": True},
        request_id=request_id
    )


@router.get("/demo/error-generic")
async def demo_generic_error(request: Request):
    """
    Demo: Generic unhandled exception

    Shows:
    - Generic exception handler catches all errors
    - Logs full traceback
    - Returns safe error message to client
    - Request ID for tracing
    """
    request_id = get_request_id(request)

    logger.warning(
        "Generic error demo - throwing unhandled exception",
        request_id=request_id
    )

    # This will be caught by generic exception handler
    raise ValueError("This is an unhandled exception for demo purposes")


@router.get("/demo/logging")
async def demo_structured_logging(request: Request):
    """
    Demo: Structured logging at different levels

    Shows:
    - JSON structured logging
    - Different log levels
    - Request ID in all logs
    - Custom fields
    """
    request_id = get_request_id(request)

    # Debug log
    logger.debug(
        "Debug level log",
        request_id=request_id,
        user_action="view_demo"
    )

    # Info log
    logger.info(
        "Info level log with structured data",
        request_id=request_id,
        endpoint="/demo/logging",
        user_id=123,
        action="test_logging"
    )

    # Warning log
    logger.warning(
        "Warning level log",
        request_id=request_id,
        threshold_exceeded=True,
        current_value=85,
        threshold=80
    )

    # Error log (without exception)
    logger.error(
        "Error level log",
        request_id=request_id,
        error_code="DEMO_ERROR",
        details="This is just a demo, not a real error"
    )

    return success_response(
        data={
            "message": "Check your logs to see structured logging in action",
            "request_id": request_id,
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
            "log_format": "JSON" if logger.logger.handlers else "default"
        },
        request_id=request_id
    )


@router.get("/demo/request-id")
async def demo_request_id(request: Request):
    """
    Demo: Request ID tracking

    Shows:
    - Request ID generated by middleware
    - Available in request.state
    - Included in response headers (X-Request-ID)
    - Used for distributed tracing
    """
    request_id = get_request_id(request)

    logger.info(
        "Request ID demo called",
        request_id=request_id,
        note="Check response headers for X-Request-ID"
    )

    return success_response(
        data={
            "request_id": request_id,
            "message": "Check the response headers for X-Request-ID",
            "usage": "Use this ID for distributed tracing and debugging",
            "benefits": [
                "Track requests across services",
                "Debug issues in production",
                "Correlate logs",
                "Monitor request flow"
            ]
        },
        request_id=request_id
    )


@router.get("/demo/all-features")
async def demo_all_features(request: Request):
    """
    Demo: All Quick Wins together

    Shows all 4 Quick Wins in action:
    1. Response Format Wrapper
    2. Request ID Tracking
    3. Standardized Error Handling (see error endpoints)
    4. Structured Logging
    """
    request_id = get_request_id(request)

    logger.info(
        "All features demo called",
        request_id=request_id,
        features_demonstrated=4,
        quick_wins=[
            "Response Format Wrapper",
            "Request ID Tracking",
            "Standardized Error Handling",
            "Structured Logging"
        ]
    )

    return success_response(
        data={
            "quick_wins_implemented": [
                {
                    "name": "Response Format Wrapper",
                    "description": "Consistent APIResponse format with data, meta, success fields",
                    "file": "backend/app/schemas/common.py",
                    "demo_endpoint": "/demo/success"
                },
                {
                    "name": "Request ID Tracking",
                    "description": "UUID tracking for every request with middleware",
                    "file": "backend/app/middleware/request_id.py",
                    "demo_endpoint": "/demo/request-id"
                },
                {
                    "name": "Standardized Error Handling",
                    "description": "Consistent error responses with codes and messages",
                    "file": "backend/app/core/exceptions.py",
                    "demo_endpoints": ["/demo/error-not-found", "/demo/error-validation"]
                },
                {
                    "name": "Structured Logging",
                    "description": "JSON logging with request_id and custom fields",
                    "file": "backend/app/core/logging.py",
                    "demo_endpoint": "/demo/logging"
                }
            ],
            "request_id": request_id,
            "timestamp": "See meta.timestamp below",
            "next_steps": [
                "Gradually migrate existing endpoints to use new response format",
                "Add more custom exception types as needed",
                "Configure log aggregation (ELK, Datadog, etc.)",
                "Add metrics and monitoring"
            ]
        },
        request_id=request_id
    )
