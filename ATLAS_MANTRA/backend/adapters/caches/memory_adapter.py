"""
Memory Cache Adapter - In-memory implementation for testing.

This adapter stores cached values in memory with TTL support.
Useful for testing and development without external dependencies.

Usage:
    cache = MemoryCache()
    await cache.set("key", {"data": "value"}, ttl=300)
    value = await cache.get("key")
"""

import logging
import time
import fnmatch
from typing import Optional, Any, List
from dataclasses import dataclass

from core.ports.cache import CacheProtocol

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Internal representation of a cached value."""
    value: Any
    expires_at: float


class MemoryCache(CacheProtocol):
    """
    In-memory implementation of CacheProtocol.

    Stores values in a dictionary with expiration support.
    Suitable for:
    - Unit testing
    - Local development
    - Single-instance applications
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize in-memory cache.

        Args:
            default_ttl: Default TTL in seconds
        """
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        logger.info("Memory cache initialized")

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired."""
        return time.time() > entry.expires_at

    def _cleanup_expired(self) -> None:
        """Remove expired entries (lazy cleanup)."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key]

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._cache[key]
            return None
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> None:
        """Store a value in cache."""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl,
        )
        logger.debug(f"Cache set: {key}, ttl={ttl}s")

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        entry = self._cache.get(key)
        if entry is None:
            return False
        if self._is_expired(entry):
            del self._cache[key]
            return False
        return True

    async def get_many(self, keys: List[str]) -> dict[str, Any]:
        """Retrieve multiple values from cache."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int = None
    ) -> None:
        """Store multiple values in cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        # Convert glob pattern to match keys
        matching_keys = [
            key for key in self._cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        for key in matching_keys:
            del self._cache[key]
        logger.debug(f"Deleted {len(matching_keys)} keys matching {pattern}")
        return len(matching_keys)

    async def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Memory cache cleared")

    async def close(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Memory cache closed")
