"""
Cache Port - Abstract interface for caching operations.

This port defines the contract for caching operations used to
speed up repeated queries. Implementations can use Redis,
Memcached, or in-memory caching.

Usage:
    class RedisCache(CacheProtocol):
        async def get(self, key):
            # Redis-specific implementation
            ...
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List


class CacheProtocol(ABC):
    """
    Abstract protocol for cache operations.

    This interface allows swapping cache implementations
    without changing business logic. Supports:
    - Redis (primary)
    - In-memory (testing/development)
    - No-op (disabled caching)
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> None:
        """
        Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dict of key -> value for found keys
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int = 300
    ) -> None:
        """
        Store multiple values in cache.

        Args:
            items: Dict of key -> value
            ttl: Time-to-live in seconds
        """
        pass

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Glob-style pattern (e.g., "search:*")

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached data (use with caution)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
