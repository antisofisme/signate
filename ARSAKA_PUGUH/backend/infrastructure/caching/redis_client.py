"""
Redis Client Wrapper

Provides Redis client with graceful fallback and connection management.

CRITICAL: All Redis failures must gracefully fallback to PostgreSQL.
Redis is OPTIONAL - system must work without it.

Source: Phase 2 Design & Execution Plan - Section 4.1
"""

import os
import json
from typing import Optional, Any
from redis import asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from infrastructure.logging import get_logger


logger = get_logger(__name__)

# Global Redis client (singleton)
_redis_client: Optional['RedisClient'] = None


class RedisClient:
    """
    Async Redis client wrapper with graceful fallback

    Features:
    - Automatic connection management
    - Graceful error handling (logs and returns None)
    - JSON serialization/deserialization
    - TTL support
    - Connection pool

    Usage:
        redis = RedisClient(url="redis://localhost:6379")
        await redis.connect()

        # Set value with TTL
        await redis.set("key", {"data": "value"}, ttl=300)

        # Get value (returns None if not found or Redis unavailable)
        value = await redis.get("key")

        await redis.close()
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        enabled: bool = True,
    ):
        """
        Initialize Redis client

        Args:
            url: Redis connection URL
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
            enabled: Enable Redis (can be disabled for testing)
        """
        self._url = url
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._enabled = enabled
        self._client: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self):
        """
        Connect to Redis

        Gracefully handles connection failures - logs error and continues.
        System remains operational without Redis.
        """
        if not self._enabled:
            logger.info("Redis caching disabled by configuration")
            return

        try:
            self._client = await aioredis.from_url(
                self._url,
                max_connections=self._max_connections,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._socket_connect_timeout,
                decode_responses=True,  # Auto-decode bytes to strings
            )

            # Test connection
            await self._client.ping()
            self._connected = True

            logger.info(
                "Redis client connected successfully",
                extra={"url": self._url, "max_connections": self._max_connections}
            )

        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(
                "Redis connection failed - continuing without cache",
                extra={"error": str(e), "url": self._url}
            )
            self._connected = False
            self._client = None

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis client closed")

    def is_connected(self) -> bool:
        """Check if Redis is connected and available"""
        return self._connected and self._client is not None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found/error

        Note: Returns None on ANY error (graceful degradation)
        """
        if not self.is_connected():
            return None

        try:
            value = await self._client.get(key)

            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(
                "Redis GET failed - falling back to source",
                extra={"key": key, "error": str(e)}
            )
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise

        Note: Fails silently (logs error, returns False)
        """
        if not self.is_connected():
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)

            return True

        except (RedisError, TypeError, json.JSONEncodeError) as e:
            logger.warning(
                "Redis SET failed - value not cached",
                extra={"key": key, "error": str(e)}
            )
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            await self._client.delete(key)
            return True

        except RedisError as e:
            logger.warning(
                "Redis DELETE failed",
                extra={"key": key, "error": str(e)}
            )
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            return await self._client.exists(key) > 0

        except RedisError as e:
            logger.warning(
                "Redis EXISTS failed",
                extra={"key": key, "error": str(e)}
            )
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from Redis

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key -> value (only found keys)
        """
        if not self.is_connected() or not keys:
            return {}

        try:
            values = await self._client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass

            return result

        except RedisError as e:
            logger.warning(
                "Redis MGET failed",
                extra={"keys_count": len(keys), "error": str(e)}
            )
            return {}

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            New value or None if error
        """
        if not self.is_connected():
            return None

        try:
            return await self._client.incrby(key, amount)

        except RedisError as e:
            logger.warning(
                "Redis INCRBY failed",
                extra={"key": key, "error": str(e)}
            )
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set TTL on existing key

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            return await self._client.expire(key, ttl)

        except RedisError as e:
            logger.warning(
                "Redis EXPIRE failed",
                extra={"key": key, "error": str(e)}
            )
            return False


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance (singleton)

    Returns:
        RedisClient instance

    Note: Must call await redis.connect() before use
    """
    global _redis_client

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"

        _redis_client = RedisClient(
            url=redis_url,
            enabled=redis_enabled
        )

    return _redis_client
