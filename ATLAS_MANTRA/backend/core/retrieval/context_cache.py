"""
MANTRA Context Cache

Pre-computed and cached context windows for fast retrieval.

CACHE TYPES:
1. SCOPE_CONTEXT - Pre-built context for each scope path
2. BUNDLE_CONTEXT - Pre-built context for each bundle
3. HOT_DECISIONS - Frequently accessed decisions
4. QUERY_CACHE - Recent query results

INVALIDATION:
- Decision update → Invalidate related caches
- TTL-based expiry for query cache
- Manual invalidation via API

WARMING:
- Warm cache on startup for common scopes
- Background refresh for hot decisions
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import Lock
import hashlib


# ============================================================================
# ENUMS
# ============================================================================

class CacheType(str, Enum):
    """Type of cached content."""
    SCOPE_CONTEXT = "SCOPE_CONTEXT"     # Pre-built scope context
    BUNDLE_CONTEXT = "BUNDLE_CONTEXT"   # Pre-built bundle context
    QUERY_RESULT = "QUERY_RESULT"       # Cached search results
    DECISION_TEXT = "DECISION_TEXT"     # Cached decision text
    HOT_SET = "HOT_SET"                 # Hot decision IDs


class CacheStatus(str, Enum):
    """Cache entry status."""
    FRESH = "FRESH"       # Recently computed, valid
    STALE = "STALE"       # Past TTL, needs refresh
    INVALID = "INVALID"   # Explicitly invalidated


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    cache_type: CacheType
    value: Any

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    last_hit: Optional[datetime] = None

    # Invalidation tracking
    decision_ids: Set[str] = field(default_factory=set)  # Decisions this depends on
    status: CacheStatus = CacheStatus.FRESH

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.status == CacheStatus.FRESH and not self.is_expired

    def record_hit(self) -> None:
        self.hit_count += 1
        self.last_hit = datetime.now(timezone.utc)


@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_size_bytes: int = 0

    # By type
    entries_by_type: Dict[CacheType, int] = field(default_factory=dict)
    hits_by_type: Dict[CacheType, int] = field(default_factory=dict)

    @property
    def hit_ratio(self) -> float:
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0


@dataclass
class ContextWindow:
    """A pre-computed context window."""
    context_text: str
    decision_ids: List[str]
    decision_codes: List[str]
    token_estimate: int

    # Metadata
    scope_path: Optional[str] = None
    bundle_code: Optional[str] = None
    tags: List[str] = field(default_factory=list)


# ============================================================================
# CONTEXT CACHE
# ============================================================================

class ContextCache:
    """
    Main cache for pre-computed contexts.

    Thread-safe implementation with TTL support.
    """

    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    MAX_ENTRIES = 10000

    def __init__(
        self,
        default_ttl: int = DEFAULT_TTL_SECONDS,
        max_entries: int = MAX_ENTRIES
    ):
        self.default_ttl = default_ttl
        self.max_entries = max_entries

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = CacheStats()

        # Indexes for fast invalidation
        self._by_decision: Dict[str, Set[str]] = {}  # decision_id → cache_keys
        self._by_type: Dict[CacheType, Set[str]] = {}  # type → cache_keys

    # =========================================================================
    # Core Operations
    # =========================================================================

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Returns None if not found or expired.
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.total_misses += 1
                return None

            if not entry.is_valid:
                self._stats.total_misses += 1
                return None

            # Record hit
            entry.record_hit()
            self._stats.total_hits += 1
            self._stats.hits_by_type[entry.cache_type] = (
                self._stats.hits_by_type.get(entry.cache_type, 0) + 1
            )

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        cache_type: CacheType,
        ttl: Optional[int] = None,
        decision_ids: Optional[Set[str]] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cached content
            ttl: Time-to-live in seconds (None = use default)
            decision_ids: Decision IDs this entry depends on (for invalidation)
        """
        if ttl is None:
            ttl = self.default_ttl

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        entry = CacheEntry(
            key=key,
            cache_type=cache_type,
            value=value,
            expires_at=expires_at,
            decision_ids=decision_ids or set()
        )

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_entries:
                self._evict_lru()

            self._cache[key] = entry

            # Update indexes
            for did in entry.decision_ids:
                if did not in self._by_decision:
                    self._by_decision[did] = set()
                self._by_decision[did].add(key)

            if cache_type not in self._by_type:
                self._by_type[cache_type] = set()
            self._by_type[cache_type].add(key)

            # Update stats
            self._stats.total_entries = len(self._cache)
            self._stats.entries_by_type[cache_type] = (
                self._stats.entries_by_type.get(cache_type, 0) + 1
            )

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache.pop(key)

            # Clean up indexes
            for did in entry.decision_ids:
                if did in self._by_decision:
                    self._by_decision[did].discard(key)

            if entry.cache_type in self._by_type:
                self._by_type[entry.cache_type].discard(key)

            self._stats.total_entries = len(self._cache)
            return True

    def invalidate_by_decision(self, decision_id: str) -> int:
        """
        Invalidate all cache entries that depend on a decision.

        Returns number of entries invalidated.
        """
        with self._lock:
            keys = self._by_decision.get(decision_id, set()).copy()
            count = 0

            for key in keys:
                if key in self._cache:
                    self._cache[key].status = CacheStatus.INVALID
                    count += 1

            return count

    def invalidate_by_type(self, cache_type: CacheType) -> int:
        """Invalidate all entries of a given type."""
        with self._lock:
            keys = self._by_type.get(cache_type, set()).copy()
            count = 0

            for key in keys:
                if key in self._cache:
                    self._cache[key].status = CacheStatus.INVALID
                    count += 1

            return count

    def clear(self) -> int:
        """Clear entire cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._by_decision.clear()
            self._by_type.clear()
            self._stats = CacheStats()
            return count

    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        # Find entries to evict (oldest 10%)
        evict_count = max(1, len(self._cache) // 10)

        entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_hit or x[1].created_at
        )

        for key, _ in entries[:evict_count]:
            self.delete(key)

    # =========================================================================
    # High-Level Operations
    # =========================================================================

    def get_scope_context(self, scope_path: str) -> Optional[ContextWindow]:
        """Get cached context for a scope path."""
        key = f"scope:{scope_path}"
        return self.get(key)

    def set_scope_context(
        self,
        scope_path: str,
        context: ContextWindow,
        ttl: Optional[int] = None
    ) -> None:
        """Cache context for a scope path."""
        key = f"scope:{scope_path}"
        decision_ids = set(context.decision_ids)
        self.set(key, context, CacheType.SCOPE_CONTEXT, ttl, decision_ids)

    def get_bundle_context(self, bundle_code: str) -> Optional[ContextWindow]:
        """Get cached context for a bundle."""
        key = f"bundle:{bundle_code}"
        return self.get(key)

    def set_bundle_context(
        self,
        bundle_code: str,
        context: ContextWindow,
        ttl: Optional[int] = None
    ) -> None:
        """Cache context for a bundle."""
        key = f"bundle:{bundle_code}"
        decision_ids = set(context.decision_ids)
        self.set(key, context, CacheType.BUNDLE_CONTEXT, ttl, decision_ids)

    def get_query_result(self, query: str, **filters) -> Optional[List[str]]:
        """Get cached query result."""
        key = self._query_key(query, filters)
        return self.get(key)

    def set_query_result(
        self,
        query: str,
        result: List[str],
        ttl: int = 300,  # 5 minutes for queries
        **filters
    ) -> None:
        """Cache query result."""
        key = self._query_key(query, filters)
        decision_ids = set(result)
        self.set(key, result, CacheType.QUERY_RESULT, ttl, decision_ids)

    def _query_key(self, query: str, filters: Dict[str, Any]) -> str:
        """Generate cache key for a query."""
        # Hash query + filters
        content = f"{query}|{sorted(filters.items())}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"query:{hash_val}"

    # =========================================================================
    # Cache Warming
    # =========================================================================

    def warm_scope_contexts(
        self,
        scope_paths: List[str],
        builder: Callable[[str], ContextWindow]
    ) -> int:
        """
        Warm cache for given scope paths.

        Args:
            scope_paths: Scopes to warm
            builder: Function to build context for a scope

        Returns:
            Number of contexts warmed
        """
        count = 0
        for scope_path in scope_paths:
            try:
                context = builder(scope_path)
                self.set_scope_context(scope_path, context)
                count += 1
            except Exception:
                pass  # Skip on error
        return count

    def warm_bundle_contexts(
        self,
        bundle_codes: List[str],
        builder: Callable[[str], ContextWindow]
    ) -> int:
        """Warm cache for given bundles."""
        count = 0
        for bundle_code in bundle_codes:
            try:
                context = builder(bundle_code)
                self.set_bundle_context(bundle_code, context)
                count += 1
            except Exception:
                pass
        return count

    # =========================================================================
    # Stats & Maintenance
    # =========================================================================

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                total_entries=len(self._cache),
                total_hits=self._stats.total_hits,
                total_misses=self._stats.total_misses,
                entries_by_type=dict(self._stats.entries_by_type),
                hits_by_type=dict(self._stats.hits_by_type)
            )

    def cleanup_expired(self) -> int:
        """Remove expired entries. Call periodically."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired or entry.status == CacheStatus.INVALID
            ]

        # Delete outside lock
        count = 0
        for key in expired_keys:
            if self.delete(key):
                count += 1

        return count

    def get_hot_keys(self, limit: int = 20) -> List[str]:
        """Get most frequently accessed keys."""
        with self._lock:
            entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].hit_count,
                reverse=True
            )
            return [key for key, _ in entries[:limit]]


# ============================================================================
# HOT DECISIONS CACHE
# ============================================================================

class HotDecisionsCache:
    """
    Specialized cache for frequently accessed decisions.

    Keeps full decision data in memory for instant access.
    """

    DEFAULT_SIZE = 100

    def __init__(self, max_size: int = DEFAULT_SIZE):
        self.max_size = max_size
        self._decisions: Dict[str, Dict[str, Any]] = {}
        self._access_count: Dict[str, int] = {}
        self._lock = Lock()

    def get(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get decision from hot cache."""
        with self._lock:
            if decision_id in self._decisions:
                self._access_count[decision_id] = (
                    self._access_count.get(decision_id, 0) + 1
                )
                return self._decisions[decision_id]
        return None

    def put(self, decision: Dict[str, Any]) -> None:
        """Add decision to hot cache."""
        decision_id = decision.get("decision_id", "")
        if not decision_id:
            return

        with self._lock:
            # Evict if at capacity
            if len(self._decisions) >= self.max_size and decision_id not in self._decisions:
                self._evict_least_accessed()

            self._decisions[decision_id] = decision
            self._access_count[decision_id] = self._access_count.get(decision_id, 0)

    def remove(self, decision_id: str) -> bool:
        """Remove decision from hot cache."""
        with self._lock:
            if decision_id in self._decisions:
                del self._decisions[decision_id]
                self._access_count.pop(decision_id, None)
                return True
        return False

    def _evict_least_accessed(self) -> None:
        """Evict least accessed decision."""
        if not self._access_count:
            return

        min_key = min(self._access_count.keys(), key=lambda k: self._access_count[k])
        self._decisions.pop(min_key, None)
        self._access_count.pop(min_key, None)

    def refresh_from_usage(
        self,
        decision_ids: List[str],
        loader: Callable[[str], Optional[Dict[str, Any]]]
    ) -> int:
        """
        Refresh hot cache based on usage data.

        Args:
            decision_ids: Hot decision IDs from analytics
            loader: Function to load decision by ID

        Returns:
            Number of decisions loaded
        """
        count = 0
        for did in decision_ids[:self.max_size]:
            if did not in self._decisions:
                decision = loader(did)
                if decision:
                    self.put(decision)
                    count += 1
        return count

    def get_all_ids(self) -> List[str]:
        """Get all cached decision IDs."""
        with self._lock:
            return list(self._decisions.keys())


# ============================================================================
# GLOBAL CACHE INSTANCE
# ============================================================================

_context_cache: Optional[ContextCache] = None
_hot_cache: Optional[HotDecisionsCache] = None


def get_context_cache() -> ContextCache:
    """Get global context cache instance."""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache


def get_hot_cache() -> HotDecisionsCache:
    """Get global hot decisions cache instance."""
    global _hot_cache
    if _hot_cache is None:
        _hot_cache = HotDecisionsCache()
    return _hot_cache


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "CacheType",
    "CacheStatus",
    # Data structures
    "CacheEntry",
    "CacheStats",
    "ContextWindow",
    # Caches
    "ContextCache",
    "HotDecisionsCache",
    # Global access
    "get_context_cache",
    "get_hot_cache",
]
