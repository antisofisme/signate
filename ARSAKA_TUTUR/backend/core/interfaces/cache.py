"""
Cache interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List


class ICache(ABC):
    """
    Interface for caching service.

    Implementations: RedisCache
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> dict:
        """
        Get multiple values.

        Args:
            keys: List of keys

        Returns:
            Dict of key -> value (missing keys not included)
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "tenant:*:cache:*")

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
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
        pass
