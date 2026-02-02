"""
Prometheus Middleware for FastAPI

Collects HTTP request/response metrics.
Middleware runs BEFORE Phase 1 routers (no modification to Phase 1).

Source: Phase 2 Design & Execution Plan - Section 3.2
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

from .prometheus_client import http_requests_total, http_request_duration_seconds


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics

    Metrics collected:
    - http_requests_total: Counter with method, endpoint, status_code labels
    - http_request_duration_seconds: Histogram with method, endpoint labels
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics

        Args:
            request: HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Extract endpoint path (remove query params)
        endpoint = request.url.path
        method = request.method

        # Start timer
        start_time = time.time()

        try:
            # Call next middleware/handler (Phase 1 router)
            response = await call_next(request)

            # Record success metrics
            status_code = response.status_code
            self._record_metrics(method, endpoint, status_code, start_time)

            return response

        except Exception as e:
            # Record error metrics (500 Internal Server Error)
            self._record_metrics(method, endpoint, 500, start_time)

            # Re-raise exception (don't swallow it)
            raise

    def _record_metrics(self, method: str, endpoint: str, status_code: int, start_time: float):
        """
        Record HTTP metrics

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Request path
            status_code: HTTP status code
            start_time: Request start time (Unix timestamp)
        """
        # Calculate duration
        duration = time.time() - start_time

        # Increment request counter
        if http_requests_total:
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()

        # Observe request duration
        if http_request_duration_seconds:
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
