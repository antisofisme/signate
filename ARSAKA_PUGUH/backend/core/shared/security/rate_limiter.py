"""
Rate Limiter

Simple in-memory rate limiting for API endpoints.
For production, use Redis-based rate limiting.
"""

import time
from functools import wraps
from typing import Dict, Tuple, Optional, Callable
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    For production use with multiple workers, replace with Redis-based limiter.
    """

    def __init__(self):
        # {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current window"""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [
            (ts, count) for ts, count in self._requests[key]
            if ts > cutoff
        ]

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Returns:
            (is_allowed, current_count, remaining)
        """
        now = time.time()

        # Cleanup old requests
        self._cleanup_old_requests(key, window_seconds)

        # Count requests in window
        current_count = sum(count for _, count in self._requests[key])

        if current_count >= max_requests:
            return False, current_count, 0

        # Record this request
        self._requests[key].append((now, 1))

        return True, current_count + 1, max_requests - current_count - 1

    def get_key(self, request: Request, key_func: Optional[Callable] = None) -> str:
        """Get rate limit key for request"""
        if key_func:
            return key_func(request)

        # Default: use client IP
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:{client_ip}:{request.url.path}"


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable[[Request], str]] = None,
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Usage:
        @app.get("/api/endpoint")
        @rate_limit(max_requests=10, window_seconds=60)
        async def my_endpoint(request: Request):
            ...

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Optional function to generate rate limit key from request
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            key = _rate_limiter.get_key(request, key_func)
            is_allowed, current, remaining = _rate_limiter.is_allowed(
                key, max_requests, window_seconds
            )

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {window_seconds} seconds.",
                        "limit": max_requests,
                        "window": window_seconds,
                    },
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
                        "Retry-After": str(window_seconds),
                    },
                )

            # Add rate limit headers to response
            # Note: This requires middleware to actually add headers to response
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
            }

            return await func(*args, **kwargs)

        return wrapper
    return decorator


class RateLimitMiddleware:
    """
    Middleware to add rate limit headers to responses.

    Usage:
        app.add_middleware(RateLimitMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Check if rate limit headers are set
                request = scope.get("state", {})
                if hasattr(request, "rate_limit_headers"):
                    headers = list(message.get("headers", []))
                    for key, value in request.rate_limit_headers.items():
                        headers.append((key.encode(), value.encode()))
                    message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
