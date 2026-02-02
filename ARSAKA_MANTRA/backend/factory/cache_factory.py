"""
Cache Factory - Creates cache adapter instances.

Supports:
- redis: Redis cache (production)
- memory: In-memory cache (testing/development)

Usage:
    from factory.cache_factory import CacheFactory

    cache = CacheFactory.get_cache()
"""

import logging
from typing import Optional

from core.runtime.config import get_config
from core.ports.cache import CacheProtocol
from factory.base import FactoryMixin

logger = logging.getLogger(__name__)


class CacheFactory(FactoryMixin):
    """Factory for creating cache instances."""

    _instance: Optional[CacheProtocol] = None

    @classmethod
    def get_cache(cls) -> CacheProtocol:
        """
        Get cache instance based on configuration.

        Supports:
        - redis: Redis cache
        - memory: In-memory cache for testing

        Returns:
            CacheProtocol implementation
        """
        if cls._instance is None:
            config = get_config()
            cache_type = config.cache.lower()

            if cache_type == "redis":
                cls._instance = cls._create_redis_cache(config)
            elif cache_type == "memory":
                cls._instance = cls._create_memory_cache(config)
            else:
                cls.log_fallback("Cache", f"Unknown type: {cache_type}", "memory")
                cls._instance = cls._create_memory_cache(config)

        return cls._instance

    @classmethod
    def _create_redis_cache(cls, config) -> CacheProtocol:
        """Create Redis cache instance."""
        from adapters.caches.redis_adapter import RedisCache

        cache = RedisCache(
            url=config.redis_url,
            default_ttl=config.cache_ttl,
        )
        cls.log_using("Cache", "Redis", config.redis_url)
        return cache

    @classmethod
    def _create_memory_cache(cls, config) -> CacheProtocol:
        """Create in-memory cache instance."""
        from adapters.caches.memory_adapter import MemoryCache

        cache = MemoryCache(default_ttl=config.cache_ttl)
        cls.log_using("Cache", "InMemory")
        return cache

    @classmethod
    def reset(cls) -> None:
        """Reset cached instance."""
        cls._instance = None

    @classmethod
    async def close(cls) -> None:
        """Close cache connection."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
