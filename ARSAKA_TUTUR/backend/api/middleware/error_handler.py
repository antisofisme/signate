"""
Error handler middleware - catches exceptions and returns standard error responses.
"""

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...shared.logging import get_logger
from ...shared.exceptions import ChatAIError
from .rate_limit import RateLimitExceeded

logger = get_logger(__name__)


async def error_handler_middleware(request: Request, call_next: Callable):
    """
    Middleware to handle exceptions and return standard error responses.
    """
    try:
        return await call_next(request)

    except RateLimitExceeded as e:
        # Rate limit errors
        logger.warning(
            f"Rate limit exceeded for {request.url.path}",
            extra={
                "limit": e.limit,
                "window": e.window,
                "reset_at": e.reset_at,
            }
        )

        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {e.limit} requests per {e.window} seconds.",
                    "details": {
                        "limit": e.limit,
                        "window_seconds": e.window,
                        "reset_at": e.reset_at,
                    },
                },
            },
            headers={
                "Retry-After": str(e.reset_at - int(__import__("time").time())),
            },
        )

    except ChatAIError as e:
        # Known application errors
        logger.warning(
            f"Application error: {e.code} - {e.message}",
            extra={
                "error_code": e.code,
                "status_code": e.status_code,
                "details": e.details,
            }
        )

        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.to_dict(),
            }
        )

    except Exception as e:
        # Unexpected errors
        logger.exception(f"Unexpected error: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            }
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Error handler as middleware class.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        return await error_handler_middleware(request, call_next)
