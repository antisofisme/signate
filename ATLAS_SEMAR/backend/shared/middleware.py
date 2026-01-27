"""
ATLAS_SEMAR Backend - Middleware
Follows PANDAWA Clean Architecture standards
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response logging middleware"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"({process_time:.3f}s) "
            f"{request.method} {request.url.path}"
        )

        return response
