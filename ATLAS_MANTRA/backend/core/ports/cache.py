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


# =============================================================================
# Cache Key Patterns
# =============================================================================

class CacheKeys:
    """
    Standardized cache key patterns for MANTRA.

    All keys follow the pattern: mantra:{domain}:{resource}:{identifier}

    Examples:
        CacheKeys.decision("abc-123")          -> "mantra:decision:abc-123"
        CacheKeys.decision_version("abc", 2)   -> "mantra:decision:abc:v2"
        CacheKeys.search_hash("xyz")           -> "mantra:search:xyz"
    """

    # Base prefix
    PREFIX = "mantra"

    # Decision cache
    @staticmethod
    def decision(decision_id: str) -> str:
        """Cache key for a single decision."""
        return f"{CacheKeys.PREFIX}:decision:{decision_id}"

    @staticmethod
    def decision_version(decision_id: str, version: int) -> str:
        """Cache key for a specific decision version."""
        return f"{CacheKeys.PREFIX}:decision:{decision_id}:v{version}"

    @staticmethod
    def decision_list(page: int = 1, page_size: int = 20) -> str:
        """Cache key for paginated decision list."""
        return f"{CacheKeys.PREFIX}:decisions:page:{page}:size:{page_size}"

    @staticmethod
    def decisions_by_domain(domain_id: str) -> str:
        """Cache key for decisions filtered by domain."""
        return f"{CacheKeys.PREFIX}:decisions:domain:{domain_id}"

    # Search cache
    @staticmethod
    def search_results(query_hash: str) -> str:
        """Cache key for text search results."""
        return f"{CacheKeys.PREFIX}:search:{query_hash}"

    @staticmethod
    def search_semantic(query_hash: str) -> str:
        """Cache key for semantic search results."""
        return f"{CacheKeys.PREFIX}:semantic:{query_hash}"

    @staticmethod
    def search_hybrid(query_hash: str) -> str:
        """Cache key for hybrid search results."""
        return f"{CacheKeys.PREFIX}:hybrid:{query_hash}"

    # Validation cache
    @staticmethod
    def validation_result(decision_id: str) -> str:
        """Cache key for validation result."""
        return f"{CacheKeys.PREFIX}:validation:{decision_id}"

    @staticmethod
    def alignment_check(content_hash: str) -> str:
        """Cache key for alignment check result."""
        return f"{CacheKeys.PREFIX}:alignment:{content_hash}"

    # Statistics cache
    @staticmethod
    def stats_domains() -> str:
        """Cache key for domain statistics."""
        return f"{CacheKeys.PREFIX}:stats:domains"

    @staticmethod
    def stats_features() -> str:
        """Cache key for feature statistics."""
        return f"{CacheKeys.PREFIX}:stats:features"

    @staticmethod
    def stats_overview() -> str:
        """Cache key for overview statistics."""
        return f"{CacheKeys.PREFIX}:stats:overview"

    # Patterns for bulk operations
    @staticmethod
    def pattern_decisions() -> str:
        """Pattern for all decision cache keys."""
        return f"{CacheKeys.PREFIX}:decision:*"

    @staticmethod
    def pattern_search() -> str:
        """Pattern for all search cache keys."""
        return f"{CacheKeys.PREFIX}:search:*"

    @staticmethod
    def pattern_stats() -> str:
        """Pattern for all stats cache keys."""
        return f"{CacheKeys.PREFIX}:stats:*"


# =============================================================================
# Cache TTL Configuration
# =============================================================================

class CacheTTL:
    """
    TTL (Time-to-Live) configuration for different cache types.

    Values are in seconds. Adjust based on:
    - How frequently data changes
    - How expensive the operation is to recompute
    - Memory constraints
    """

    # Decision data - changes infrequently
    DECISION = 3600              # 1 hour
    DECISION_VERSION = 86400     # 24 hours (immutable once created)
    DECISION_LIST = 300          # 5 minutes

    # Search results - moderate TTL for freshness
    SEARCH_RESULTS = 300         # 5 minutes
    SEARCH_SEMANTIC = 300        # 5 minutes
    SEARCH_HYBRID = 300          # 5 minutes

    # Validation - expensive operation
    VALIDATION = 1800            # 30 minutes
    ALIGNMENT = 1800             # 30 minutes

    # Statistics - aggregated data
    STATS = 600                  # 10 minutes
    STATS_DETAILED = 300         # 5 minutes

    # Session/temp data
    TEMP = 60                    # 1 minute
    SESSION = 3600               # 1 hour


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
