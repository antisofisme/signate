"""
Streaming Middleware for Smart TV Digital Signage
Handles HTTP Range Requests, bandwidth throttling, and streaming analytics
"""

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import asyncio
import time
import logging
from typing import Optional, Callable
import re

from app.core.logging import StructuredLogger
from app.core.config import settings

logger = StructuredLogger(__name__)

# Default bandwidth limit in bytes per second (10 MB/s)
DEFAULT_BANDWIDTH_LIMIT = 10 * 1024 * 1024  # 10 MB/s

# Regex pattern to match streaming endpoints
STREAMING_PATH_PATTERN = re.compile(r"^/api/content/\d+/stream/")
HLS_DATA_PATTERN = re.compile(r"^/data/hls/")


class StreamingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle streaming-specific features:
    - HTTP Range Request processing
    - Bandwidth throttling
    - Request logging for analytics
    - CORS headers for cross-origin streaming
    """

    def __init__(
        self,
        app: ASGIApp,
        bandwidth_limit: Optional[int] = None,
        enable_analytics: bool = True
    ):
        super().__init__(app)
        self.bandwidth_limit = bandwidth_limit or DEFAULT_BANDWIDTH_LIMIT
        self.enable_analytics = enable_analytics

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process streaming requests with special handling
        """
        # Check if this is a streaming endpoint
        is_streaming_path = (
            STREAMING_PATH_PATTERN.match(request.url.path) or
            HLS_DATA_PATTERN.match(request.url.path)
        )

        if not is_streaming_path:
            # Not a streaming endpoint, pass through
            return await call_next(request)

        # Log streaming request for analytics
        if self.enable_analytics:
            self._log_streaming_request(request)

        # Process the request
        start_time = time.time()
        response = await call_next(request)

        # Add streaming-specific headers
        response = self._add_streaming_headers(request, response)

        # Log response metrics
        if self.enable_analytics:
            duration = time.time() - start_time
            self._log_streaming_response(request, response, duration)

        return response

    def _log_streaming_request(self, request: Request):
        """Log streaming request for analytics"""
        logger.info(
            "Streaming request",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            range_header=request.headers.get("range")
        )

    def _log_streaming_response(self, request: Request, response: Response, duration: float):
        """Log streaming response metrics"""
        logger.info(
            "Streaming response",
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=int(duration * 1000),
            content_length=response.headers.get("content-length"),
            content_type=response.headers.get("content-type")
        )

    def _add_streaming_headers(self, request: Request, response: Response) -> Response:
        """Add streaming-specific headers to response"""
        # Add CORS headers for cross-origin streaming
        origin = request.headers.get("origin")
        if origin and origin in settings.CORS_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Range, Accept-Encoding"
            response.headers["Access-Control-Expose-Headers"] = "Accept-Ranges, Content-Range, Content-Length"

        # Add timing header for performance monitoring
        response.headers["X-Stream-Timing"] = str(time.time())

        return response


class BandwidthThrottler:
    """
    Bandwidth throttling for streaming responses
    Limits the data transfer rate to prevent server overload
    """

    def __init__(self, bandwidth_limit: int = DEFAULT_BANDWIDTH_LIMIT):
        """
        Initialize bandwidth throttler

        Args:
            bandwidth_limit: Maximum bytes per second
        """
        self.bandwidth_limit = bandwidth_limit
        self.chunk_size = 8192  # 8KB chunks
        self.last_send_time = None
        self.bytes_sent = 0

    async def throttle_stream(self, stream_generator):
        """
        Throttle a streaming generator to limit bandwidth

        Args:
            stream_generator: Async generator yielding data chunks

        Yields:
            Throttled data chunks
        """
        start_time = time.time()

        async for chunk in stream_generator:
            chunk_size = len(chunk)

            # Calculate expected time based on bandwidth limit
            self.bytes_sent += chunk_size
            expected_time = self.bytes_sent / self.bandwidth_limit
            elapsed_time = time.time() - start_time

            # Sleep if we're sending too fast
            if expected_time > elapsed_time:
                sleep_time = expected_time - elapsed_time
                await asyncio.sleep(sleep_time)

            yield chunk


class StreamingAnalytics:
    """
    Analytics collector for streaming metrics
    Tracks bandwidth usage, popular content, and viewer patterns
    """

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "total_bytes_served": 0,
            "active_streams": 0,
            "content_views": {},
            "bandwidth_by_hour": {}
        }

    async def record_stream_start(self, content_id: int, client_ip: str):
        """Record the start of a streaming session"""
        self.metrics["total_requests"] += 1
        self.metrics["active_streams"] += 1

        # Track content popularity
        if content_id not in self.metrics["content_views"]:
            self.metrics["content_views"][content_id] = 0
        self.metrics["content_views"][content_id] += 1

        logger.info(
            "Stream started",
            content_id=content_id,
            client_ip=client_ip,
            active_streams=self.metrics["active_streams"]
        )

    async def record_stream_end(self, content_id: int, bytes_served: int):
        """Record the end of a streaming session"""
        self.metrics["active_streams"] -= 1
        self.metrics["total_bytes_served"] += bytes_served

        # Track bandwidth by hour
        hour_key = time.strftime("%Y-%m-%d %H:00")
        if hour_key not in self.metrics["bandwidth_by_hour"]:
            self.metrics["bandwidth_by_hour"][hour_key] = 0
        self.metrics["bandwidth_by_hour"][hour_key] += bytes_served

        logger.info(
            "Stream ended",
            content_id=content_id,
            bytes_served=bytes_served,
            active_streams=self.metrics["active_streams"]
        )

    def get_metrics(self) -> dict:
        """Get current streaming metrics"""
        return self.metrics.copy()


# Global analytics instance
streaming_analytics = StreamingAnalytics()