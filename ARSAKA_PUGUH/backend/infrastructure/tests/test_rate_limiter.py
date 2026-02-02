"""
Rate Limiter Unit Tests

Tests rate limiter token bucket algorithm and fail-open behavior.

Critical Test Cases:
1. Token bucket algorithm correctness
2. Fail-open when Redis unavailable
3. Per-tenant and global limits
4. Rate limit headers

Source: Phase 2 Week 3 - Testing & Quality Assurance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import time

from starlette.requests import Request
from starlette.responses import Response

from infrastructure.caching.redis_client import RedisClient
from infrastructure.security.rate_limiter import RateLimiter, RateLimitMiddleware


class TestRateLimiterAlgorithm:
    """Test token bucket algorithm"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)
        redis.get = AsyncMock()
        redis.set = AsyncMock()
        redis.increment = AsyncMock()
        redis._client = MagicMock()
        redis._client.ttl = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_first_request_in_window_allowed(self, mock_redis):
        """Test first request in window is allowed"""
        # Setup
        mock_redis.get.return_value = None  # No existing count (first request)
        mock_redis.set.return_value = True

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify
        assert allowed is True
        assert info["limit"] == 100
        assert info["remaining"] == 99  # 100 - 1
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_within_limit_allowed(self, mock_redis):
        """Test request within limit is allowed"""
        # Setup - 50 requests already made, limit is 100
        mock_redis.get.return_value = 50
        mock_redis.increment.return_value = 51
        mock_redis._client.ttl.return_value = 30

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify
        assert allowed is True
        assert info["remaining"] == 49  # 100 - 51
        mock_redis.increment.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_at_limit_rejected(self, mock_redis):
        """Test request at limit is rejected"""
        # Setup - already at limit
        mock_redis.get.return_value = 100  # At limit
        mock_redis._client.ttl.return_value = 30

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify
        assert allowed is False
        assert info["remaining"] == 0
        assert "retry_after" in info
        mock_redis.increment.assert_not_called()  # Should not increment

    @pytest.mark.asyncio
    async def test_request_above_limit_rejected(self, mock_redis):
        """Test request above limit is rejected"""
        # Setup - exceeded limit
        mock_redis.get.return_value = 150  # Above limit
        mock_redis._client.ttl.return_value = 30

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify
        assert allowed is False
        assert info["remaining"] == 0

    @pytest.mark.asyncio
    async def test_rate_limit_reset_time_calculated(self, mock_redis):
        """Test reset time is correctly calculated"""
        # Setup
        mock_redis.get.return_value = 100  # At limit
        mock_redis._client.ttl.return_value = 45  # 45 seconds remaining

        limiter = RateLimiter(mock_redis)

        # Execute
        before_time = time.time()
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)
        after_time = time.time()

        # Verify
        assert "reset" in info
        # Reset time should be approximately now + 45 seconds
        assert before_time + 45 <= info["reset"] <= after_time + 45 + 1

    @pytest.mark.asyncio
    async def test_ttl_with_window_default(self, mock_redis):
        """Test TTL is set to window duration on first request"""
        # Setup
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        limiter = RateLimiter(mock_redis)
        window = 60

        # Execute
        await limiter.check_rate_limit("test_key", limit=100, window=window)

        # Verify TTL passed to set
        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs["ttl"] == window


class TestRateLimiterFailOpen:
    """Test fail-open behavior when Redis unavailable"""

    @pytest.fixture
    def mock_redis_disconnected(self):
        """Mock disconnected Redis client"""
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=False)
        return redis

    @pytest.mark.asyncio
    async def test_redis_disconnected_allows_request(self, mock_redis_disconnected):
        """Test requests allowed when Redis is disconnected (FAIL-OPEN)"""
        limiter = RateLimiter(mock_redis_disconnected)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - fail-open behavior
        assert allowed is True
        assert info["remaining"] == 100  # Full limit available

    @pytest.mark.asyncio
    async def test_redis_get_error_allows_request(self):
        """Test request allowed when Redis GET fails"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - fail-open behavior
        assert allowed is True

    @pytest.mark.asyncio
    async def test_redis_set_error_allows_request(self):
        """Test request allowed when Redis SET fails"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - fail-open behavior
        assert allowed is True

    @pytest.mark.asyncio
    async def test_redis_increment_error_allows_request(self):
        """Test request allowed when Redis INCREMENT fails"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=50)
        mock_redis.increment = AsyncMock(return_value=None)  # Increment failed

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - fail-open behavior
        assert allowed is True


class TestRateLimitMiddleware:
    """Test rate limit middleware integration"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)
        redis.get = AsyncMock()
        redis.set = AsyncMock()
        redis.increment = AsyncMock()
        redis._client = MagicMock()
        redis._client.ttl = AsyncMock()
        return redis

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        app = MagicMock()
        return app

    @pytest.fixture
    async def mock_request(self):
        """Mock HTTP request"""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/v1/decisions"
        request.query_params = {}
        request.headers = {}

        # Mock body
        body_data = b'{"tenant_id":"550e8400-e29b-41d4-a716-446655440000"}'
        request.body = AsyncMock(return_value=body_data)

        return request

    @pytest.mark.asyncio
    async def test_middleware_checks_global_limit(self, mock_redis, mock_app, mock_request):
        """Test middleware checks global rate limit"""
        # Setup
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        middleware = RateLimitMiddleware(
            mock_app,
            mock_redis,
            global_limit=1000,
            global_window=60
        )

        async def call_next(request):
            response = Response(status_code=200)
            return response

        # Execute
        response = await middleware.dispatch(mock_request, call_next)

        # Verify global limit was checked
        assert response.status_code == 200
        mock_redis.get.assert_called()  # Global rate limit checked

    @pytest.mark.asyncio
    async def test_middleware_extracts_tenant_id_from_body(self, mock_redis, mock_app):
        """Test middleware extracts tenant_id from request body"""
        # Setup
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/v1/decisions"
        request.query_params = {}
        request.headers = {}

        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        body_data = f'{{"tenant_id":"{tenant_id}"}}'.encode()
        request.body = AsyncMock(return_value=body_data)

        middleware = RateLimitMiddleware(mock_app, mock_redis)

        # Execute
        extracted_tenant = await middleware._extract_tenant_id(request)

        # Verify
        assert extracted_tenant == tenant_id

    @pytest.mark.asyncio
    async def test_middleware_extracts_tenant_id_from_query(self, mock_redis, mock_app):
        """Test middleware extracts tenant_id from query params"""
        # Setup
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/v1/decisions"
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        request.query_params = {"tenant_id": tenant_id}
        request.headers = {}

        middleware = RateLimitMiddleware(mock_app, mock_redis)

        # Execute
        extracted_tenant = await middleware._extract_tenant_id(request)

        # Verify
        assert extracted_tenant == tenant_id

    @pytest.mark.asyncio
    async def test_middleware_categorizes_decisions_endpoint(self, mock_redis, mock_app):
        """Test middleware categorizes /decisions endpoint"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/v1/decisions"

        middleware = RateLimitMiddleware(mock_app, mock_redis)

        # Execute
        category = middleware._categorize_endpoint(request.url.path)

        # Verify
        assert category == "decisions"

    @pytest.mark.asyncio
    async def test_middleware_categorizes_workflows_endpoint(self, mock_redis, mock_app):
        """Test middleware categorizes /workflows endpoint"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/v1/workflows"

        middleware = RateLimitMiddleware(mock_app, mock_redis)

        # Execute
        category = middleware._categorize_endpoint(request.url.path)

        # Verify
        assert category == "workflows"

    @pytest.mark.asyncio
    async def test_middleware_returns_429_when_rate_limited(self, mock_redis, mock_app, mock_request):
        """Test middleware returns 429 when rate limit exceeded"""
        # Setup - global limit exceeded
        mock_redis.get.return_value = 1000  # At limit
        mock_redis._client.ttl.return_value = 30

        middleware = RateLimitMiddleware(
            mock_app,
            mock_redis,
            global_limit=1000,
            global_window=60
        )

        async def call_next(request):
            return Response(status_code=200)

        # Execute
        response = await middleware.dispatch(mock_request, call_next)

        # Verify
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_adds_rate_limit_headers(self, mock_redis, mock_app, mock_request):
        """Test middleware adds rate limit headers to response"""
        # Setup
        mock_redis.get.return_value = 50  # Under limit
        mock_redis.increment.return_value = 51
        mock_redis._client.ttl.return_value = 30

        middleware = RateLimitMiddleware(
            mock_app,
            mock_redis,
            global_limit=1000,
            global_window=60
        )

        async def call_next(request):
            return Response(status_code=200)

        # Execute
        response = await middleware.dispatch(mock_request, call_next)

        # Verify headers
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_per_tenant_limit_checked(self, mock_redis, mock_app):
        """Test middleware checks per-tenant limit"""
        # Setup
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/v1/decisions"
        request.query_params = {}
        request.headers = {}

        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        body_data = f'{{"tenant_id":"{tenant_id}"}}'.encode()
        request.body = AsyncMock(return_value=body_data)

        # Global limit OK, tenant limit exceeded
        call_count = [0]
        async def mock_get_side_effect(key):
            call_count[0] += 1
            if "global" in key:
                return 50  # Under global limit
            else:
                return 100  # At tenant limit

        mock_redis.get.side_effect = mock_get_side_effect
        mock_redis._client.ttl.return_value = 30

        middleware = RateLimitMiddleware(
            mock_app,
            mock_redis,
            global_limit=1000,
            tenant_limits={"decisions": {"limit": 100, "window": 60}}
        )

        async def call_next(request):
            return Response(status_code=200)

        # Execute
        response = await middleware.dispatch(request, call_next)

        # Verify - tenant limit triggered 429
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_middleware_fail_open_when_redis_down(self, mock_app, mock_request):
        """Test middleware allows requests when Redis is down (FAIL-OPEN)"""
        # Setup - disconnected Redis
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=False)

        middleware = RateLimitMiddleware(mock_app, mock_redis)

        async def call_next(request):
            return Response(status_code=200)

        # Execute
        response = await middleware.dispatch(mock_request, call_next)

        # Verify - request allowed despite Redis being down
        assert response.status_code == 200


class TestRateLimiterEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_zero_limit_always_rejects(self):
        """Test zero limit always rejects requests"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)

        limiter = RateLimiter(mock_redis)

        # Execute with limit=0
        allowed, info = await limiter.check_rate_limit("test_key", limit=0, window=60)

        # Verify - should be rejected (though this is an edge case config)
        # With limit=0, count>=limit is always true
        assert allowed is False

    @pytest.mark.asyncio
    async def test_negative_count_handled(self):
        """Test negative count is handled (shouldn't happen but defensive)"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=-1)  # Invalid state
        mock_redis.increment = AsyncMock(return_value=0)
        mock_redis._client.ttl = AsyncMock(return_value=30)

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - should allow (count < limit)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_key_format_per_tenant(self):
        """Test rate limit key format for per-tenant limits"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)

        limiter = RateLimiter(mock_redis)
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        endpoint_category = "decisions"

        expected_key = f"rate_limit:tenant:{tenant_id}:{endpoint_category}"

        # Execute
        await limiter.check_rate_limit(expected_key, limit=100, window=60)

        # Verify key format
        call_args = mock_redis.get.call_args
        assert call_args[0][0] == expected_key

    @pytest.mark.asyncio
    async def test_ttl_zero_handled(self):
        """Test TTL=0 is handled (key exists but no TTL info)"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.is_connected = MagicMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=100)
        mock_redis._client.ttl = AsyncMock(return_value=0)  # No TTL or expired

        limiter = RateLimiter(mock_redis)

        # Execute
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # Verify - should still work, using window as fallback
        assert "reset" in info
