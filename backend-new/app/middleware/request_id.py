"""
Request ID Middleware
Generates and tracks unique request IDs for distributed tracing and debugging
"""

import uuid
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track unique request IDs

    Features:
    - Generates UUID v4 for each incoming request
    - Stores request_id in request.state for access in endpoints
    - Adds X-Request-ID header to all responses
    - Accepts existing X-Request-ID from client (for distributed tracing)
    - Logs request/response with request_id for debugging
    - Tracks request duration

    Usage in endpoints:
        @app.get("/example")
        async def example(request: Request):
            request_id = request.state.request_id
            return {"request_id": request_id}
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generate_if_missing: bool = True,
        log_requests: bool = True
    ):
        """
        Initialize RequestIDMiddleware

        Args:
            app: FastAPI application instance
            header_name: HTTP header name for request ID (default: X-Request-ID)
            generate_if_missing: Generate new ID if not provided by client (default: True)
            log_requests: Log incoming requests with request_id (default: True)
        """
        super().__init__(app)
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing
        self.log_requests = log_requests

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and add request ID tracking

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with X-Request-ID header added
        """
        # Start timing
        start_time = time.time()

        # Get or generate request ID
        request_id = request.headers.get(self.header_name)

        if not request_id and self.generate_if_missing:
            request_id = str(uuid.uuid4())
        elif not request_id:
            request_id = "no-request-id"

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Log incoming request
        if self.log_requests:
            logger.info(
                f"[{request_id}] {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_host": request.client.host if request.client else None
                }
            )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Add request ID to response headers
            response.headers[self.header_name] = request_id

            # Log response
            if self.log_requests:
                logger.info(
                    f"[{request_id}] {response.status_code} - {duration:.3f}s",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "duration_seconds": round(duration, 3)
                    }
                )

            return response

        except Exception as exc:
            # Log exception with request ID
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Request failed - {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(exc),
                    "duration_seconds": round(duration, 3)
                },
                exc_info=True
            )
            raise


def get_request_id(request: Request) -> str:
    """
    Helper function to get request ID from request state

    Args:
        request: FastAPI Request object

    Returns:
        Request ID string, or "unknown" if not found

    Usage:
        from app.middleware.request_id import get_request_id

        @app.get("/example")
        async def example(request: Request):
            request_id = get_request_id(request)
            return {"request_id": request_id}
    """
    return getattr(request.state, "request_id", "unknown")
