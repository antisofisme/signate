"""
Generic Cache Decorator

Provides generic caching decorator for any function/method.
Uses cache-aside pattern with Redis.

Source: Phase 2 Design & Execution Plan - Section 4.1
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional

from infrastructure.logging import get_logger
from .redis_client import RedisClient


logger = get_logger(__name__)


class CacheDecorator:
    """
    Generic cache decorator using Redis

    Example:
        redis = get_redis_client()
        await redis.connect()

        cache = CacheDecorator(redis, ttl=300)

        @cache.cached(key_prefix="expensive_operation")
        async def expensive_operation(arg1, arg2):
            # ... expensive computation
            return result

        # First call: cache miss, executes function
        result = await expensive_operation("foo", "bar")

        # Second call: cache hit, returns cached value
        result = await expensive_operation("foo", "bar")
    """

    def __init__(self, redis_client: RedisClient, ttl: int = 300):
        """
        Initialize cache decorator

        Args:
            redis_client: Redis client instance
            ttl: Default TTL in seconds (default: 300 = 5 minutes)
        """
        self._redis = redis_client
        self._ttl = ttl

    def cached(
        self,
        key_prefix: str,
        ttl: Optional[int] = None,
        key_builder: Optional[Callable] = None
    ):
        """
        Decorator to cache function results

        Args:
            key_prefix: Cache key prefix (e.g., "expensive_operation")
            ttl: TTL in seconds (optional, defaults to instance TTL)
            key_builder: Custom key builder function (optional)

        Returns:
            Decorator function

        Example:
            @cache.cached(key_prefix="user_profile", ttl=600)
            async def get_user_profile(user_id: UUID):
                # ... fetch from database
                return profile
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._build_default_key(key_prefix, args, kwargs)

                # Try cache first
                cached_value = await self._redis.get(cache_key)

                if cached_value is not None:
                    logger.debug(
                        f"Cache HIT: {key_prefix}",
                        extra={"cache_key": cache_key}
                    )
                    return cached_value

                # Cache miss - execute function
                logger.debug(
                    f"Cache MISS: {key_prefix}",
                    extra={"cache_key": cache_key}
                )

                result = await func(*args, **kwargs)

                # Store in cache
                cache_ttl = ttl if ttl is not None else self._ttl
                await self._redis.set(cache_key, result, ttl=cache_ttl)

                return result

            return wrapper
        return decorator

    def _build_default_key(
        self,
        prefix: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """
        Build cache key from function arguments

        Strategy: Hash arguments to create unique key

        Args:
            prefix: Cache key prefix
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Serialize arguments
        args_str = json.dumps(
            {"args": [str(arg) for arg in args], "kwargs": kwargs},
            sort_keys=True,
            default=str
        )

        # Hash to avoid key length issues
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]

        return f"{prefix}:{args_hash}"
