"""
Decision Cache - Fast Access Layer

Provides caching for:
1. Hot decisions (frequently accessed)
2. Pre-computed context bundles (file pattern → decisions)
3. Session-specific results (avoid re-computation)

CACHE TIERS:
- L1: In-memory (fastest, limited size)
- L2: Redis (fast, larger capacity)
- L3: Database (slow, unlimited)

INVALIDATION:
- TTL-based (configurable per cache type)
- Event-based (on decision update/create)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json


@dataclass
class CacheConfig:
    """Cache configuration."""
    # L1 (memory) settings
    l1_max_items: int = 100
    l1_ttl_seconds: int = 300  # 5 minutes

    # L2 (Redis) settings
    l2_ttl_seconds: int = 3600  # 1 hour

    # Bundle settings
    bundle_ttl_seconds: int = 1800  # 30 minutes
    max_bundles: int = 50

    # Session cache settings
    session_ttl_seconds: int = 600  # 10 minutes


@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


@dataclass
class ContextBundle:
    """Pre-computed decision bundle for a context pattern."""
    pattern: str              # e.g., "*.tsx", "src/features/*"
    decision_ids: List[str]
    decision_codes: List[str]
    context_text: str         # Pre-rendered context
    token_count: int
    created_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class DecisionCache:
    """
    Multi-tier caching system for decisions.

    Provides fast access to frequently used decisions
    and pre-computed context bundles.
    """

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        redis_client: Optional[Any] = None,
    ):
        """
        Initialize cache.

        Args:
            config: Cache configuration
            redis_client: Optional Redis client for L2 cache
        """
        self.config = config or CacheConfig()
        self.redis = redis_client

        # L1 cache (LRU)
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Bundle cache
        self._bundles: Dict[str, ContextBundle] = {}

        # Session cache
        self._sessions: Dict[str, Dict[str, Any]] = {}

        # Stats
        self._stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "bundle_hits": 0,
            "bundle_misses": 0,
        }

    # =========================================================================
    # L1 Cache (Memory)
    # =========================================================================

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 → L2)."""
        # Try L1
        entry = self._l1_cache.get(key)
        if entry and not entry.is_expired:
            self._stats["l1_hits"] += 1
            entry.hit_count += 1
            # Move to end (LRU)
            self._l1_cache.move_to_end(key)
            return entry.value

        self._stats["l1_misses"] += 1

        # Try L2 (Redis)
        if self.redis:
            value = self._get_l2(key)
            if value is not None:
                self._stats["l2_hits"] += 1
                # Promote to L1
                self._set_l1(key, value)
                return value
            self._stats["l2_misses"] += 1

        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ):
        """Set value in cache (L1 + L2)."""
        ttl = ttl_seconds or self.config.l1_ttl_seconds
        self._set_l1(key, value, ttl)

        if self.redis:
            self._set_l2(key, value, ttl_seconds or self.config.l2_ttl_seconds)

    def delete(self, key: str):
        """Delete from all cache tiers."""
        if key in self._l1_cache:
            del self._l1_cache[key]

        if self.redis:
            self.redis.delete(f"mantra:cache:{key}")

    def _set_l1(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set in L1 cache."""
        ttl = ttl_seconds or self.config.l1_ttl_seconds
        now = datetime.utcnow()

        # Remove oldest if at capacity
        while len(self._l1_cache) >= self.config.l1_max_items:
            self._l1_cache.popitem(last=False)

        self._l1_cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )

    def _get_l2(self, key: str) -> Optional[Any]:
        """Get from L2 (Redis)."""
        if not self.redis:
            return None

        try:
            data = self.redis.get(f"mantra:cache:{key}")
            if data:
                return json.loads(data)
        except Exception:
            pass

        return None

    def _set_l2(self, key: str, value: Any, ttl_seconds: int):
        """Set in L2 (Redis)."""
        if not self.redis:
            return

        try:
            self.redis.setex(
                f"mantra:cache:{key}",
                ttl_seconds,
                json.dumps(value, default=str),
            )
        except Exception:
            pass

    # =========================================================================
    # Context Bundles
    # =========================================================================

    def get_bundle(self, pattern: str) -> Optional[ContextBundle]:
        """Get pre-computed bundle for pattern."""
        bundle = self._bundles.get(pattern)
        if bundle and not bundle.is_expired:
            self._stats["bundle_hits"] += 1
            return bundle

        self._stats["bundle_misses"] += 1
        return None

    def set_bundle(
        self,
        pattern: str,
        decision_ids: List[str],
        decision_codes: List[str],
        context_text: str,
        token_count: int,
    ):
        """Store pre-computed bundle."""
        # Remove oldest if at capacity
        while len(self._bundles) >= self.config.max_bundles:
            oldest = min(self._bundles.items(), key=lambda x: x[1].created_at)
            del self._bundles[oldest[0]]

        now = datetime.utcnow()
        self._bundles[pattern] = ContextBundle(
            pattern=pattern,
            decision_ids=decision_ids,
            decision_codes=decision_codes,
            context_text=context_text,
            token_count=token_count,
            created_at=now,
            expires_at=now + timedelta(seconds=self.config.bundle_ttl_seconds),
        )

    def get_or_compute_bundle(
        self,
        pattern: str,
        compute_fn,
    ) -> ContextBundle:
        """Get bundle or compute if missing."""
        bundle = self.get_bundle(pattern)
        if bundle:
            return bundle

        # Compute
        result = compute_fn(pattern)

        # Cache
        self.set_bundle(
            pattern=pattern,
            decision_ids=result["decision_ids"],
            decision_codes=result["decision_codes"],
            context_text=result["context_text"],
            token_count=result["token_count"],
        )

        return self.get_bundle(pattern)

    # =========================================================================
    # Session Cache
    # =========================================================================

    def get_session(self, session_id: str, key: str) -> Optional[Any]:
        """Get value from session cache."""
        session = self._sessions.get(session_id, {})
        entry = session.get(key)

        if entry and entry.get("expires_at", datetime.min) > datetime.utcnow():
            return entry.get("value")

        return None

    def set_session(self, session_id: str, key: str, value: Any):
        """Set value in session cache."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {}

        now = datetime.utcnow()
        self._sessions[session_id][key] = {
            "value": value,
            "created_at": now,
            "expires_at": now + timedelta(seconds=self.config.session_ttl_seconds),
        }

    def clear_session(self, session_id: str):
        """Clear session cache."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    # =========================================================================
    # Hot Decisions
    # =========================================================================

    def cache_hot_decisions(self, decisions: List[Dict[str, Any]]):
        """Pre-cache frequently used decisions."""
        for decision in decisions:
            decision_id = decision.get("decision_id")
            if decision_id:
                self.set(f"decision:{decision_id}", decision)

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get cached decision."""
        return self.get(f"decision:{decision_id}")

    # =========================================================================
    # Cache Management
    # =========================================================================

    def invalidate_decision(self, decision_id: str):
        """Invalidate all caches related to a decision."""
        # Remove from L1/L2
        self.delete(f"decision:{decision_id}")

        # Invalidate bundles containing this decision
        to_remove = []
        for pattern, bundle in self._bundles.items():
            if decision_id in bundle.decision_ids:
                to_remove.append(pattern)

        for pattern in to_remove:
            del self._bundles[pattern]

    def clear_all(self):
        """Clear all caches."""
        self._l1_cache.clear()
        self._bundles.clear()
        self._sessions.clear()

        if self.redis:
            # Clear Redis keys with pattern
            keys = self.redis.keys("mantra:cache:*")
            if keys:
                self.redis.delete(*keys)

    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()

        # L1
        expired_l1 = [k for k, v in self._l1_cache.items() if v.is_expired]
        for k in expired_l1:
            del self._l1_cache[k]

        # Bundles
        expired_bundles = [k for k, v in self._bundles.items() if v.is_expired]
        for k in expired_bundles:
            del self._bundles[k]

        # Sessions
        expired_sessions = []
        for sid, session in self._sessions.items():
            expired_keys = [
                k for k, v in session.items()
                if v.get("expires_at", datetime.min) < now
            ]
            for k in expired_keys:
                del session[k]
            if not session:
                expired_sessions.append(sid)

        for sid in expired_sessions:
            del self._sessions[sid]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            **self._stats,
            "l1_size": len(self._l1_cache),
            "l1_max": self.config.l1_max_items,
            "bundles_count": len(self._bundles),
            "bundles_max": self.config.max_bundles,
            "sessions_count": len(self._sessions),
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "CacheConfig",
    "CacheEntry",
    "ContextBundle",
    "DecisionCache",
]
