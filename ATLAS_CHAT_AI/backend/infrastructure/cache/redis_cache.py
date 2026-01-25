"""
Redis Cache Adapter

Implements ICache interface for Redis.
"""

from typing import Optional, Any, List
import json

import redis.asyncio as redis

from ...core.interfaces import ICache
from ...config import RedisConfig, get_settings
from ...shared.logging import get_logger

logger = get_logger(__name__)


class RedisCache(ICache):
    """
    Redis implementation of ICache interface.

    Features:
    - JSON serialization
    - TTL support
    - Pattern-based operations
    - Atomic counters
    """

    def __init__(
        self,
        config: Optional[RedisConfig] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
    ):
        if config:
            self.config = config
        else:
            # Allow individual parameters for container injection
            settings = get_settings()
            self.config = RedisConfig(
                host=host or settings.redis.host,
                port=port or settings.redis.port,
                db=db if db is not None else settings.redis.db,
                password=password or settings.redis.password,
            )
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Explicitly connect to Redis."""
        if self._client is None:
            self._client = redis.from_url(
                self.config.url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            await self.connect()
        return self._client

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None
        """
        client = await self._get_client()

        try:
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)

        except json.JSONDecodeError:
            # Return raw value if not JSON
            return value
        except Exception as e:
            logger.error(f"Redis get error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time to live

        Returns:
            True if set
        """
        client = await self._get_client()

        try:
            serialized = json.dumps(value)
            if ttl_seconds:
                await client.setex(key, ttl_seconds, serialized)
            else:
                await client.set(key, serialized)
            return True

        except Exception as e:
            logger.error(f"Redis set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self._get_client()

        try:
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await self._get_client()

        try:
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for {key}: {e}")
            return False

    async def get_many(self, keys: List[str]) -> dict:
        """
        Get multiple values.

        Args:
            keys: List of keys

        Returns:
            Dict of key -> value (missing keys not included)
        """
        if not keys:
            return {}

        client = await self._get_client()

        try:
            values = await client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value

            return result

        except Exception as e:
            logger.error(f"Redis get_many error: {e}")
            return {}

    async def set_many(
        self,
        items: dict,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set multiple values.

        Args:
            items: Dict of key -> value
            ttl_seconds: TTL for all items

        Returns:
            True if all set
        """
        if not items:
            return True

        client = await self._get_client()

        try:
            # Serialize all values
            serialized = {k: json.dumps(v) for k, v in items.items()}

            if ttl_seconds:
                # Use pipeline for TTL
                pipe = client.pipeline()
                for key, value in serialized.items():
                    pipe.setex(key, ttl_seconds, value)
                await pipe.execute()
            else:
                await client.mset(serialized)

            return True

        except Exception as e:
            logger.error(f"Redis set_many error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "tenant:*:cache:*")

        Returns:
            Number of keys deleted
        """
        client = await self._get_client()

        try:
            keys = []
            async for key in client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                return await client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Redis delete_pattern error for {pattern}: {e}")
            return 0

    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        Increment counter.

        Args:
            key: Counter key
            amount: Increment amount
            ttl_seconds: TTL (set on first increment)

        Returns:
            New value
        """
        client = await self._get_client()

        try:
            value = await client.incrby(key, amount)

            # Set TTL if provided and key is new
            if ttl_seconds and value == amount:
                await client.expire(key, ttl_seconds)

            return value

        except Exception as e:
            logger.error(f"Redis increment error for {key}: {e}")
            return 0

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    # =========================================================================
    # Embedding Cache Helpers
    # =========================================================================

    def _embedding_key(self, tenant_id: str, content_hash: str, model: str) -> str:
        """Generate key for embedding cache."""
        return f"embed:{tenant_id}:{model}:{content_hash}"

    async def get_embedding(
        self,
        tenant_id: str,
        content_hash: str,
        model: str
    ) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._embedding_key(tenant_id, content_hash, model)
        return await self.get(key)

    async def set_embedding(
        self,
        tenant_id: str,
        content_hash: str,
        model: str,
        embedding: List[float],
        ttl_seconds: int = 86400 * 7  # 7 days
    ) -> bool:
        """Cache embedding."""
        key = self._embedding_key(tenant_id, content_hash, model)
        return await self.set(key, embedding, ttl_seconds)

    # =========================================================================
    # Rate Limit Helpers
    # =========================================================================

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit.

        Args:
            key: Rate limit key
            limit: Max requests per window
            window_seconds: Window duration

        Returns:
            Tuple of (is_allowed, current_count)
        """
        client = await self._get_client()

        try:
            current = await client.incr(key)

            # Set expiry on first request
            if current == 1:
                await client.expire(key, window_seconds)

            return (current <= limit, current)

        except Exception as e:
            logger.error(f"Redis rate limit error for {key}: {e}")
            return (True, 0)  # Allow on error
