"""
Rate Limiting Middleware

Implements sliding window rate limiting with Redis backend.
"""

from typing import Optional, Callable, Awaitable
from datetime import datetime
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ...shared.logging import get_logger
from ...infrastructure.cache.redis_cache import RedisCache

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Features:
    - Per-user rate limiting (by user_id or API key)
    - Per-IP fallback for anonymous requests
    - Configurable limits per endpoint pattern
    - Redis-backed for distributed deployments
    - Lazy Redis initialization from container
    """

    def __init__(
        self,
        app,
        redis_cache: Optional[RedisCache] = None,
        default_limit: int = 100,
        default_window: int = 60,  # seconds
        bypass_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self._redis = redis_cache
        self._redis_initialized = redis_cache is not None
        self.default_limit = default_limit
        self.default_window = default_window
        self.bypass_paths = bypass_paths or ["/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]

        # Endpoint-specific limits (path pattern -> (limit, window))
        self.endpoint_limits: dict = {
            "/api/v1/chat": (30, 60),  # 30 requests/minute for chat
            "/api/v1/search": (60, 60),  # 60 requests/minute for search
            "/api/v1/knowledge": (20, 60),  # 20 requests/minute for indexing
        }

    @property
    def redis(self) -> Optional[RedisCache]:
        """Get Redis client, lazily initializing from container if needed."""
        if not self._redis_initialized:
            try:
                from ...container import _container
                if _container and _container._initialized:
                    self._redis = _container._redis_cache
                    self._redis_initialized = True
            except Exception:
                pass
        return self._redis

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with rate limiting."""
        # Skip for bypass paths
        if self._should_bypass(request.url.path):
            return await call_next(request)

        # Get rate limit key
        key = self._get_rate_limit_key(request)

        # Get limit for this endpoint
        limit, window = self._get_endpoint_limit(request.url.path)

        # Check rate limit
        allowed, remaining, reset_at = await self._check_rate_limit(key, limit, window)

        if not allowed:
            return self._rate_limit_response(limit, window, reset_at)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

        return response

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass rate limiting."""
        for bypass_path in self.bypass_paths:
            if path.startswith(bypass_path):
                return True
        return False

    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Get rate limit key for this request.

        Priority:
        1. User ID (from context/state)
        2. API Key hash
        3. Client IP
        """
        # Try to get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            tenant_id = getattr(request.state, "tenant_id", "default")
            return f"ratelimit:{tenant_id}:user:{user_id}"

        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Use first 8 chars as identifier
            key_prefix = api_key[:8] if len(api_key) >= 8 else api_key
            return f"ratelimit:apikey:{key_prefix}"

        # Fallback to IP
        client_ip = self._get_client_ip(request)
        return f"ratelimit:ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        # Check X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in the list is the client
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _get_endpoint_limit(self, path: str) -> tuple:
        """Get rate limit for endpoint."""
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        return (self.default_limit, self.default_window)

    async def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple:
        """
        Check rate limit using sliding window.

        Returns:
            (allowed, remaining, reset_timestamp)
        """
        if not self.redis:
            # No Redis - allow all (local fallback)
            return (True, limit, int(time.time()) + window)

        now = time.time()
        window_start = now - window

        try:
            # Use Redis sorted set for sliding window
            redis_key = f"{key}:{window}"

            # Remove old entries
            await self.redis._client.zremrangebyscore(redis_key, "-inf", window_start)

            # Count current requests
            current_count = await self.redis._client.zcard(redis_key)

            if current_count >= limit:
                # Rate limited
                # Get oldest entry to determine reset time
                oldest = await self.redis._client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    reset_at = int(oldest[0][1] + window)
                else:
                    reset_at = int(now + window)

                return (False, 0, reset_at)

            # Add current request
            await self.redis._client.zadd(redis_key, {str(now): now})

            # Set expiry on the key
            await self.redis._client.expire(redis_key, window * 2)

            remaining = limit - current_count - 1
            reset_at = int(now + window)

            return (True, remaining, reset_at)

        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}, allowing request")
            return (True, limit, int(time.time()) + window)

    def _rate_limit_response(
        self,
        limit: int,
        window: int,
        reset_at: int,
    ) -> JSONResponse:
        """Return rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                    "details": {
                        "limit": limit,
                        "window_seconds": window,
                        "reset_at": reset_at,
                    },
                },
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_at),
                "Retry-After": str(reset_at - int(time.time())),
            },
        )


class RateLimiter:
    """
    Standalone rate limiter for use in dependencies.

    Example usage:
        rate_limiter = RateLimiter(redis, limit=10, window=60)

        @app.get("/endpoint")
        async def endpoint(request: Request):
            await rate_limiter.check(request)
            ...
    """

    def __init__(
        self,
        redis: Optional[RedisCache] = None,
        limit: int = 100,
        window: int = 60,
    ):
        self.redis = redis
        self.limit = limit
        self.window = window

    async def check(
        self,
        identifier: str,
        cost: int = 1,
    ) -> tuple:
        """
        Check rate limit for identifier.

        Args:
            identifier: Unique identifier (user_id, ip, etc.)
            cost: Request cost (for weighted limits)

        Returns:
            (allowed, remaining, reset_at)

        Raises:
            RateLimitExceeded if limit is exceeded
        """
        if not self.redis:
            return (True, self.limit, int(time.time()) + self.window)

        now = time.time()
        key = f"ratelimit:{identifier}:{self.window}"

        try:
            # Sliding window counter
            await self.redis._client.zremrangebyscore(key, "-inf", now - self.window)

            current = await self.redis._client.zcard(key)

            if current + cost > self.limit:
                oldest = await self.redis._client.zrange(key, 0, 0, withscores=True)
                reset_at = int(oldest[0][1] + self.window) if oldest else int(now + self.window)
                raise RateLimitExceeded(self.limit, self.window, reset_at)

            # Add entries for cost
            for i in range(cost):
                await self.redis._client.zadd(key, {f"{now}:{i}": now})

            await self.redis._client.expire(key, self.window * 2)

            return (True, self.limit - current - cost, int(now + self.window))

        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.warning(f"Rate limiter error: {e}")
            return (True, self.limit, int(time.time()) + self.window)


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""

    def __init__(self, limit: int, window: int, reset_at: int):
        self.limit = limit
        self.window = window
        self.reset_at = reset_at
        super().__init__(f"Rate limit exceeded: {limit} per {window}s")
