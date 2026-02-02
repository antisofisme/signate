"""
Rate Limiting Infrastructure

Provides Redis-based rate limiting with token bucket algorithm.
Uses middleware pattern to wrap Phase 1 WITHOUT modifying it.

Source: Phase 2 Design & Execution Plan - Section 4.3
"""

import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from typing import Callable

from infrastructure.logging import get_logger
from infrastructure.caching import RedisClient


logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter using Redis

    Algorithm: Token Bucket
    - Each tenant/endpoint has a bucket with N tokens
    - Tokens refill at rate R per window
    - Each request consumes 1 token
    - If no tokens available → 429 Too Many Requests

    Example:
        redis = get_redis_client()
        await redis.connect()

        limiter = RateLimiter(redis)

        # Check if request allowed
        allowed = await limiter.check_rate_limit(
            key="tenant:550e8400-...:decisions",
            limit=100,
            window=60
        )

        if not allowed:
            # Rate limit exceeded
            raise HTTPException(status_code=429)
    """

    def __init__(self, redis_client: RedisClient):
        """
        Initialize rate limiter

        Args:
            redis_client: Redis client for storing counters
        """
        self._redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit

        Args:
            key: Rate limit key (e.g., "tenant:xxx:endpoint:yyy")
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict)
            - allowed: True if request allowed, False if rate limited
            - info: Dict with rate limit info (remaining, reset_time)

        Algorithm: Sliding Window Counter
        1. Get current count from Redis
        2. If count < limit: increment and allow
        3. If count >= limit: deny with 429
        4. Set TTL to window duration
        """
        if not self._redis.is_connected():
            # Redis unavailable - allow request (fail open)
            logger.warning(
                "Rate limiting disabled (Redis unavailable)",
                extra={"key": key}
            )
            return True, {"remaining": limit, "reset": time.time() + window}

        try:
            # Get current count
            current_count = await self._redis.get(key)

            if current_count is None:
                # First request in window
                await self._redis.set(key, 1, ttl=window)

                return True, {
                    "limit": limit,
                    "remaining": limit - 1,
                    "reset": time.time() + window
                }

            # Existing count
            count = int(current_count)

            if count >= limit:
                # Rate limit exceeded
                ttl = await self._get_ttl(key)
                reset_time = time.time() + (ttl if ttl > 0 else window)

                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "key": key,
                        "limit": limit,
                        "count": count,
                        "window": window
                    }
                )

                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "retry_after": ttl if ttl > 0 else window
                }

            # Increment count
            new_count = await self._redis.increment(key)

            if new_count is None:
                # Increment failed - allow request (fail open)
                return True, {"remaining": limit, "reset": time.time() + window}

            ttl = await self._get_ttl(key)
            reset_time = time.time() + (ttl if ttl > 0 else window)

            return True, {
                "limit": limit,
                "remaining": limit - new_count,
                "reset": reset_time
            }

        except Exception as e:
            # Error in rate limiting - allow request (fail open)
            logger.error(
                "Rate limiting error - allowing request",
                extra={"key": key, "error": str(e)}
            )
            return True, {"remaining": limit, "reset": time.time() + window}

    async def _get_ttl(self, key: str) -> int:
        """
        Get TTL for key

        Args:
            key: Redis key

        Returns:
            TTL in seconds (0 if not found)
        """
        try:
            # Redis TTL command returns seconds
            if self._redis._client:
                ttl = await self._redis._client.ttl(key)
                return max(0, ttl)
        except Exception:
            pass

        return 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Applies rate limits per-tenant and per-endpoint.

    Configuration:
    - Global limit: 1000 req/min for all endpoints
    - Per-tenant limit: 100 req/min for decisions, 50 req/min for workflows

    Example:
        redis = get_redis_client()
        await redis.connect()

        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, redis_client=redis)
    """

    def __init__(
        self,
        app,
        redis_client: RedisClient,
        global_limit: int = 1000,
        global_window: int = 60,
        tenant_limits: Optional[dict] = None
    ):
        """
        Initialize rate limit middleware

        Args:
            app: FastAPI application
            redis_client: Redis client for rate limiting
            global_limit: Global requests per window (default: 1000/min)
            global_window: Global window in seconds (default: 60)
            tenant_limits: Per-tenant limits dict (optional)

        tenant_limits format:
        {
            "decisions": {"limit": 100, "window": 60},
            "workflows": {"limit": 50, "window": 60}
        }
        """
        super().__init__(app)
        self._limiter = RateLimiter(redis_client)
        self._global_limit = global_limit
        self._global_window = global_window
        self._tenant_limits = tenant_limits or {
            "decisions": {"limit": 100, "window": 60},
            "workflows": {"limit": 50, "window": 60}
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limits before processing request

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response (or 429 if rate limited)
        """
        # Extract tenant_id from request (if available)
        tenant_id = await self._extract_tenant_id(request)

        # Extract endpoint category
        endpoint_category = self._categorize_endpoint(request.url.path)

        # Check global rate limit
        global_key = "rate_limit:global"
        global_allowed, global_info = await self._limiter.check_rate_limit(
            global_key,
            self._global_limit,
            self._global_window
        )

        if not global_allowed:
            return self._rate_limit_response(global_info)

        # Check per-tenant rate limit (if tenant identified)
        if tenant_id and endpoint_category:
            tenant_config = self._tenant_limits.get(endpoint_category, {})

            if tenant_config:
                tenant_key = f"rate_limit:tenant:{tenant_id}:{endpoint_category}"
                tenant_allowed, tenant_info = await self._limiter.check_rate_limit(
                    tenant_key,
                    tenant_config["limit"],
                    tenant_config["window"]
                )

                if not tenant_allowed:
                    return self._rate_limit_response(tenant_info)

        # Rate limits passed - process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self._global_limit)
        response.headers["X-RateLimit-Remaining"] = str(global_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(int(global_info.get("reset", 0)))

        return response

    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant_id from request

        Checks:
        1. Request body (POST requests)
        2. Query parameters
        3. Headers (future: JWT token)

        Args:
            request: HTTP request

        Returns:
            Tenant ID string or None
        """
        try:
            # Check request body (for POST requests)
            if request.method == "POST":
                body = await request.body()

                # Re-attach body for next middleware (important!)
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive

                # Parse JSON body
                import json
                try:
                    data = json.loads(body)
                    if "tenant_id" in data:
                        return str(data["tenant_id"])
                except json.JSONDecodeError:
                    pass

            # Check query parameters
            tenant_id = request.query_params.get("tenant_id")
            if tenant_id:
                return str(tenant_id)

            # Check headers (future: JWT token)
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                return str(tenant_id)

        except Exception as e:
            logger.warning(
                "Failed to extract tenant_id from request",
                extra={"error": str(e)}
            )

        return None

    def _categorize_endpoint(self, path: str) -> Optional[str]:
        """
        Categorize endpoint for per-tenant rate limiting

        Args:
            path: Request path

        Returns:
            Category string ("decisions", "workflows") or None
        """
        if "/decisions" in path:
            return "decisions"
        elif "/workflows" in path:
            return "workflows"

        return None

    def _rate_limit_response(self, info: dict) -> JSONResponse:
        """
        Create 429 rate limit response

        Args:
            info: Rate limit info dict

        Returns:
            JSONResponse with 429 status
        """
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "details": {
                    "limit": info.get("limit"),
                    "remaining": info.get("remaining", 0),
                    "reset": info.get("reset"),
                    "retry_after": info.get("retry_after")
                }
            },
            headers={
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(info.get("reset", 0))),
                "Retry-After": str(int(info.get("retry_after", 60)))
            }
        )
