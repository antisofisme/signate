"""
Redis Client Unit Tests

Tests Redis client fail-open behavior and graceful degradation.

Critical Test Cases:
1. Connection failures (graceful)
2. Operation failures (returns None/False)
3. Disabled Redis configuration
4. Invalid data handling

Source: Phase 2 Week 3 - Testing & Quality Assurance
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import json

from infrastructure.caching.redis_client import RedisClient, get_redis_client


class TestRedisClientConnection:
    """Test Redis connection handling"""

    @pytest.mark.asyncio
    async def test_connection_success(self):
        """Test successful Redis connection"""
        redis = RedisClient(url="redis://localhost:6379")

        with patch('infrastructure.caching.redis_client.aioredis.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_client

            await redis.connect()

            assert redis.is_connected() is True
            assert redis._client is not None
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_failure_graceful(self):
        """Test connection failure is handled gracefully (FAIL-OPEN)"""
        redis = RedisClient(url="redis://localhost:6379")

        with patch('infrastructure.caching.redis_client.aioredis.from_url') as mock_from_url:
            # Simulate connection failure
            mock_from_url.side_effect = ConnectionError("Connection refused")

            # Should NOT raise exception
            await redis.connect()

            # Verify graceful degradation
            assert redis.is_connected() is False
            assert redis._client is None

    @pytest.mark.asyncio
    async def test_connection_timeout_graceful(self):
        """Test connection timeout is handled gracefully"""
        redis = RedisClient(url="redis://localhost:6379")

        with patch('infrastructure.caching.redis_client.aioredis.from_url') as mock_from_url:
            # Simulate timeout
            mock_from_url.side_effect = TimeoutError("Connection timeout")

            await redis.connect()

            assert redis.is_connected() is False
            assert redis._client is None

    @pytest.mark.asyncio
    async def test_connection_disabled_by_config(self):
        """Test Redis can be disabled via configuration"""
        redis = RedisClient(url="redis://localhost:6379", enabled=False)

        await redis.connect()

        # Should NOT attempt connection
        assert redis.is_connected() is False
        assert redis._client is None

    @pytest.mark.asyncio
    async def test_ping_failure_graceful(self):
        """Test ping failure after connection is handled gracefully"""
        redis = RedisClient(url="redis://localhost:6379")

        with patch('infrastructure.caching.redis_client.aioredis.from_url') as mock_from_url:
            mock_client = AsyncMock()
            # Connection succeeds but ping fails
            mock_client.ping = AsyncMock(side_effect=RedisError("Ping failed"))
            mock_from_url.return_value = mock_client

            await redis.connect()

            assert redis.is_connected() is False
            assert redis._client is None


class TestRedisClientOperations:
    """Test Redis operations fail-open behavior"""

    @pytest.mark.asyncio
    async def test_get_when_disconnected(self):
        """Test GET returns None when Redis is disconnected"""
        redis = RedisClient(enabled=False)
        await redis.connect()

        result = await redis.get("test_key")

        assert result is None  # Graceful fallback

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET operation"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Mock successful get
        test_data = {"value": "test"}
        redis._client.get = AsyncMock(return_value=json.dumps(test_data))

        result = await redis.get("test_key")

        assert result == test_data
        redis._client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test GET returns None when key not found"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.get = AsyncMock(return_value=None)

        result = await redis.get("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error_graceful(self):
        """Test GET handles Redis errors gracefully (FAIL-OPEN)"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Simulate Redis error
        redis._client.get = AsyncMock(side_effect=RedisError("Redis error"))

        result = await redis.get("test_key")

        # Should return None, NOT raise exception
        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_decode_error_graceful(self):
        """Test GET handles JSON decode errors gracefully"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Return invalid JSON
        redis._client.get = AsyncMock(return_value="invalid json{")

        result = await redis.get("test_key")

        # Should return None, NOT raise exception
        assert result is None

    @pytest.mark.asyncio
    async def test_set_when_disconnected(self):
        """Test SET returns False when Redis is disconnected"""
        redis = RedisClient(enabled=False)
        await redis.connect()

        result = await redis.set("test_key", {"data": "value"})

        assert result is False  # Graceful fallback

    @pytest.mark.asyncio
    async def test_set_success(self):
        """Test successful SET operation"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.set = AsyncMock(return_value=True)

        result = await redis.set("test_key", {"data": "value"})

        assert result is True
        redis._client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test SET with TTL"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.setex = AsyncMock(return_value=True)

        result = await redis.set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        redis._client.setex.assert_called_once()
        # Verify TTL was passed
        call_args = redis._client.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 300

    @pytest.mark.asyncio
    async def test_set_redis_error_graceful(self):
        """Test SET handles Redis errors gracefully (FAIL-OPEN)"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Simulate Redis error
        redis._client.set = AsyncMock(side_effect=RedisError("Redis error"))

        result = await redis.set("test_key", {"data": "value"})

        # Should return False, NOT raise exception
        assert result is False

    @pytest.mark.asyncio
    async def test_set_json_encode_error_graceful(self):
        """Test SET handles JSON encode errors gracefully"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Create un-serializable object
        class UnserializableObject:
            def __repr__(self):
                raise Exception("Cannot serialize")

        # Should handle gracefully (using default=str fallback)
        result = await redis.set("test_key", {"obj": UnserializableObject()})

        # With default=str, this should succeed
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_when_disconnected(self):
        """Test DELETE returns False when Redis is disconnected"""
        redis = RedisClient(enabled=False)
        await redis.connect()

        result = await redis.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful DELETE operation"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.delete = AsyncMock(return_value=1)

        result = await redis.delete("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_redis_error_graceful(self):
        """Test DELETE handles Redis errors gracefully"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.delete = AsyncMock(side_effect=RedisError("Redis error"))

        result = await redis.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_increment_when_disconnected(self):
        """Test INCREMENT returns None when Redis is disconnected"""
        redis = RedisClient(enabled=False)
        await redis.connect()

        result = await redis.increment("counter_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_increment_success(self):
        """Test successful INCREMENT operation"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.incrby = AsyncMock(return_value=5)

        result = await redis.increment("counter_key", amount=1)

        assert result == 5

    @pytest.mark.asyncio
    async def test_increment_redis_error_graceful(self):
        """Test INCREMENT handles Redis errors gracefully"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.incrby = AsyncMock(side_effect=RedisError("Redis error"))

        result = await redis.increment("counter_key")

        assert result is None


class TestRedisClientSingleton:
    """Test Redis client singleton pattern"""

    def test_get_redis_client_singleton(self):
        """Test get_redis_client returns same instance"""
        # Reset singleton
        import infrastructure.caching.redis_client as redis_module
        redis_module._redis_client = None

        client1 = get_redis_client()
        client2 = get_redis_client()

        assert client1 is client2

    def test_get_redis_client_respects_env_vars(self):
        """Test get_redis_client respects REDIS_ENABLED env var"""
        import infrastructure.caching.redis_client as redis_module
        redis_module._redis_client = None

        with patch.dict('os.environ', {'REDIS_ENABLED': 'false'}):
            client = get_redis_client()

            assert client._enabled is False

    def test_get_redis_client_default_url(self):
        """Test get_redis_client uses default URL"""
        import infrastructure.caching.redis_client as redis_module
        redis_module._redis_client = None

        with patch.dict('os.environ', {}, clear=True):
            client = get_redis_client()

            assert client._url == "redis://localhost:6379"


class TestRedisClientEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self):
        """Test close() when not connected does not raise error"""
        redis = RedisClient(enabled=False)

        # Should not raise exception
        await redis.close()

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test successful close"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()
        redis._client.close = AsyncMock()

        await redis.close()

        assert redis._connected is False
        redis._client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_when_disconnected(self):
        """Test EXISTS returns False when disconnected"""
        redis = RedisClient(enabled=False)
        await redis.connect()

        result = await redis.exists("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_success(self):
        """Test successful EXISTS check"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.exists = AsyncMock(return_value=1)

        result = await redis.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_not_found(self):
        """Test EXISTS returns False for non-existent key"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.exists = AsyncMock(return_value=0)

        result = await redis.exists("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_complex_data_serialization(self):
        """Test serialization of complex data structures"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        redis._client.set = AsyncMock(return_value=True)

        # Complex nested data
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "null": None,
            "bool": True
        }

        result = await redis.set("test_key", complex_data)

        assert result is True

        # Verify JSON serialization was called
        call_args = redis._client.set.call_args
        serialized = call_args[0][1]

        # Should be valid JSON
        deserialized = json.loads(serialized)
        assert deserialized == complex_data


# Integration-style test (still unit test scope)
class TestRedisClientFailOpenScenarios:
    """Test complete fail-open scenarios"""

    @pytest.mark.asyncio
    async def test_complete_failure_scenario(self):
        """Test complete Redis failure does not break application"""
        # Scenario: Redis down, all operations should fail gracefully
        redis = RedisClient()

        # Simulate connection failure
        with patch('infrastructure.caching.redis_client.aioredis.from_url') as mock_from_url:
            mock_from_url.side_effect = ConnectionError("Redis down")
            await redis.connect()

        # All operations should return None/False, not raise exceptions
        assert await redis.get("key") is None
        assert await redis.set("key", "value") is False
        assert await redis.delete("key") is False
        assert await redis.exists("key") is False
        assert await redis.increment("key") is None

        # Application continues to work (fail-open verified)

    @pytest.mark.asyncio
    async def test_partial_failure_scenario(self):
        """Test Redis connection succeeds but operations fail"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # All operations fail with Redis errors
        redis._client.get = AsyncMock(side_effect=RedisError("Operation failed"))
        redis._client.set = AsyncMock(side_effect=RedisError("Operation failed"))
        redis._client.delete = AsyncMock(side_effect=RedisError("Operation failed"))

        # Should handle gracefully
        assert await redis.get("key") is None
        assert await redis.set("key", "value") is False
        assert await redis.delete("key") is False

        # Application continues (fail-open verified)

    @pytest.mark.asyncio
    async def test_network_timeout_scenario(self):
        """Test network timeout is handled gracefully"""
        redis = RedisClient()
        redis._connected = True
        redis._client = AsyncMock()

        # Simulate network timeout on operations
        redis._client.get = AsyncMock(side_effect=TimeoutError("Network timeout"))
        redis._client.set = AsyncMock(side_effect=TimeoutError("Network timeout"))

        # Should handle gracefully (TimeoutError is a RedisError subclass)
        # Note: Our code catches RedisError which should cover TimeoutError
        # Let's verify this works as expected
        result_get = await redis.get("key")
        result_set = await redis.set("key", "value")

        # Both should return None/False, not raise exception
        assert result_get is None
        assert result_set is False
