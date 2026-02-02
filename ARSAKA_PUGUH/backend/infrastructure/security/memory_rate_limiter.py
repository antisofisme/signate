"""
In-Memory Rate Limiter

Provides rate limiting without Redis dependency.
Used as fallback when Redis is unavailable (Phase A).

Features:
- Token bucket algorithm
- Automatic cleanup of expired entries
- Thread-safe with asyncio locks
- Per-IP and per-user rate limiting

Limitations:
- Not distributed (single-instance only)
- Memory usage grows with unique keys
- Resets on application restart

Source: Security Implementation Plan - Phase 1
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry."""
    count: int = 0
    window_start: float = field(default_factory=time.time)
    last_cleanup: float = field(default_factory=time.time)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window.

    Thread-safe implementation for single-instance deployments.
    Automatically cleans up expired entries to prevent memory bloat.
    """

    def __init__(self, cleanup_interval: int = 300):
        """Initialize rate limiter.

        Args:
            cleanup_interval: Seconds between cleanup runs (default: 5 min)
        """
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, dict]:
        """Check if request is within rate limit.

        Args:
            key: Rate limit key (e.g., "ip:192.168.1.1")
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        async with self._lock:
            now = time.time()

            # Periodic cleanup
            if now - self._last_cleanup > self._cleanup_interval:
                await self._cleanup_expired(window)
                self._last_cleanup = now

            entry = self._entries[key]

            # Check if window has expired
            if now - entry.window_start >= window:
                # Reset window
                entry.count = 1
                entry.window_start = now
                return True, {
                    "limit": limit,
                    "remaining": limit - 1,
                    "reset": now + window
                }

            # Check if within limit
            if entry.count >= limit:
                reset_time = entry.window_start + window
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "retry_after": int(reset_time - now)
                }

            # Increment and allow
            entry.count += 1
            return True, {
                "limit": limit,
                "remaining": limit - entry.count,
                "reset": entry.window_start + window
            }

    async def _cleanup_expired(self, max_window: int) -> int:
        """Remove expired entries to prevent memory bloat.

        Args:
            max_window: Maximum window duration to consider

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._entries.items()
            if now - entry.window_start > max_window * 2
        ]

        for key in expired_keys:
            del self._entries[key]

        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "active_keys": len(self._entries),
            "last_cleanup": self._last_cleanup,
        }


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for in-memory rate limiting.

    Used when Redis is unavailable (Phase A).
    Provides per-IP rate limiting with configurable limits.
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/favicon.ico",
    }

    # Stricter limits for sensitive endpoints
    SENSITIVE_ENDPOINTS = {
        "/api/v1/auth/login": {"limit": 10, "window": 60},      # 10/min
        "/api/v1/auth/register": {"limit": 5, "window": 60},    # 5/min
        "/api/v1/auth/forgot-password": {"limit": 3, "window": 60},  # 3/min
        "/api/v1/auth/reset-password": {"limit": 5, "window": 60},   # 5/min
        "/api/v1/auth/refresh": {"limit": 30, "window": 60},    # 30/min
    }

    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        enabled: bool = True,
    ):
        """Initialize middleware.

        Args:
            app: FastAPI application
            default_limit: Default requests per window (100/min)
            default_window: Default window in seconds (60)
            enabled: Enable/disable rate limiting
        """
        super().__init__(app)
        self._limiter = InMemoryRateLimiter()
        self._default_limit = default_limit
        self._default_window = default_window
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limiting to request."""
        # Skip if disabled
        if not self._enabled:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if path in self.EXCLUDED_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)

        # Determine rate limit for this endpoint
        limit_config = self.SENSITIVE_ENDPOINTS.get(path)
        if limit_config:
            limit = limit_config["limit"]
            window = limit_config["window"]
        else:
            limit = self._default_limit
            window = self._default_window

        # Check rate limit
        key = f"ip:{client_ip}:{path}"
        allowed, info = await self._limiter.check_rate_limit(key, limit, window)

        if not allowed:
            return self._rate_limit_response(info, client_ip, path)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(int(info.get("reset", 0)))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address.

        Handles proxied requests via X-Forwarded-For header.
        """
        # Check for forwarded header (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (original client)
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _rate_limit_response(self, info: dict, client_ip: str, path: str) -> JSONResponse:
        """Create 429 rate limit response."""
        import logging
        logging.getLogger(__name__).warning(
            f"Rate limit exceeded: ip={client_ip}, path={path}, "
            f"limit={info.get('limit')}"
        )

        retry_after = info.get("retry_after", 60)

        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {
                        "retry_after": retry_after,
                        "limit": info.get("limit"),
                    }
                }
            },
            headers={
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(info.get("reset", 0))),
                "Retry-After": str(retry_after),
            }
        )
