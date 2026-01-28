"""
Redis Cache Adapter - Implementation using Redis for caching.

Redis provides high-performance caching with support for:
- Key expiration (TTL)
- Pattern-based operations
- Atomic operations

Requirements:
    pip install redis

Usage:
    cache = RedisCache(url="redis://localhost:6379/0")
    await cache.set("key", {"data": "value"}, ttl=300)
    value = await cache.get("key")
"""

import json
import logging
from typing import Optional, Any, List

import redis.asyncio as redis

from core.ports.cache import CacheProtocol

logger = logging.getLogger(__name__)


class RedisCache(CacheProtocol):
    """
    Redis implementation of CacheProtocol.

    Provides high-performance caching with:
    - Automatic JSON serialization
    - TTL support
    - Pattern-based deletion
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "mantra:",
        default_ttl: int = 300,
    ):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL
            prefix: Key prefix for namespacing
            default_ttl: Default TTL in seconds
        """
        self.url = url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.client = redis.from_url(url, decode_responses=True)
        logger.info(f"Redis cache initialized: {url}, prefix={prefix}")

    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        try:
            value = await self.client.get(self._key(key))
            if value is not None:
                return json.loads(value)
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> None:
        """Store a value in cache."""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            await self.client.setex(self._key(key), ttl, serialized)
            logger.debug(f"Cache set: {key}, ttl={ttl}s")
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            result = await self.client.delete(self._key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return await self.client.exists(self._key(key)) > 0
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False

    async def get_many(self, keys: List[str]) -> dict[str, Any]:
        """Retrieve multiple values from cache."""
        if not keys:
            return {}

        try:
            prefixed_keys = [self._key(k) for k in keys]
            values = await self.client.mget(prefixed_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int = None
    ) -> None:
        """Store multiple values in cache."""
        if not items:
            return

        try:
            ttl = ttl or self.default_ttl
            pipe = self.client.pipeline()
            for key, value in items.items():
                serialized = json.dumps(value, default=str)
                pipe.setex(self._key(key), ttl, serialized)
            await pipe.execute()
            logger.debug(f"Cache set_many: {len(items)} items")
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            raise

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            full_pattern = self._key(pattern)
            keys = []
            async for key in self.client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                count = await self.client.delete(*keys)
                logger.debug(f"Deleted {count} keys matching {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for {pattern}: {e}")
            return 0

    async def clear(self) -> None:
        """Clear all cached data with our prefix."""
        try:
            await self.delete_pattern("*")
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            raise

    async def close(self) -> None:
        """Close the Redis connection."""
        try:
            await self.client.close()
            logger.info("Redis cache closed")
        except Exception as e:
            logger.error(f"Cache close error: {e}")

    # =============================================================================
    # Enhanced Cache Methods
    # =============================================================================

    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: int = None
    ) -> Any:
        """
        Get from cache or compute and store.

        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            ttl: Time-to-live in seconds

        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value

        # Compute new value
        value = await factory()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        try:
            return await self.client.incrby(self._key(key), amount)
        except Exception as e:
            logger.error(f"Cache increment error for {key}: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement a counter in cache.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value after decrement
        """
        try:
            return await self.client.decrby(self._key(key), amount)
        except Exception as e:
            logger.error(f"Cache decrement error for {key}: {e}")
            return 0

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        try:
            return await self.client.ttl(self._key(key))
        except Exception as e:
            logger.error(f"Cache get_ttl error for {key}: {e}")
            return -2

    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """
        Extend TTL for an existing key.

        Args:
            key: Cache key
            ttl: New TTL in seconds

        Returns:
            True if successful
        """
        try:
            return await self.client.expire(self._key(key), ttl)
        except Exception as e:
            logger.error(f"Cache extend_ttl error for {key}: {e}")
            return False

    async def add_to_set(self, key: str, *values: str) -> int:
        """
        Add values to a Redis set.

        Args:
            key: Set key
            values: Values to add

        Returns:
            Number of new members added
        """
        try:
            return await self.client.sadd(self._key(key), *values)
        except Exception as e:
            logger.error(f"Cache add_to_set error for {key}: {e}")
            return 0

    async def get_set_members(self, key: str) -> set:
        """
        Get all members of a Redis set.

        Args:
            key: Set key

        Returns:
            Set of members
        """
        try:
            return await self.client.smembers(self._key(key))
        except Exception as e:
            logger.error(f"Cache get_set_members error for {key}: {e}")
            return set()

    async def is_member(self, key: str, value: str) -> bool:
        """
        Check if value is member of a set.

        Args:
            key: Set key
            value: Value to check

        Returns:
            True if member
        """
        try:
            return await self.client.sismember(self._key(key), value)
        except Exception as e:
            logger.error(f"Cache is_member error for {key}: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Check if Redis is healthy.

        Returns:
            True if Redis is responding
        """
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (key count, memory, etc.)
        """
        try:
            info = await self.client.info("memory")
            keys = await self.client.dbsize()

            return {
                "connected": True,
                "key_count": keys,
                "used_memory": info.get("used_memory_human", "unknown"),
                "used_memory_peak": info.get("used_memory_peak_human", "unknown"),
                "prefix": self.prefix,
                "default_ttl": self.default_ttl,
            }
        except Exception as e:
            logger.error(f"Cache get_stats error: {e}")
            return {
                "connected": False,
                "error": str(e),
            }
