"""
Query Embedding Cache - Reduces Redundant Embedding API Calls

Problem: Same queries get embedded multiple times, wasting:
- API costs (OpenAI: $0.02/1M tokens)
- Latency (200-500ms per embedding call)

Solution: Cache query embeddings with semantic similarity matching.

Features:
1. Exact match cache (fast lookup)
2. Semantic similarity cache (find similar cached queries)
3. TTL-based expiration
4. LRU eviction for memory management

Usage:
    cache = QueryEmbeddingCache(embedding_provider)

    # First call: generates embedding
    embedding = cache.get_or_embed("database design")  # 200ms

    # Second call: returns cached
    embedding = cache.get_or_embed("database design")  # 1ms

    # Similar query: reuses if similarity > 0.95
    embedding = cache.get_or_embed("database designs")  # may reuse
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict
import threading
import math


@dataclass
class CachedEmbedding:
    """Cached query embedding."""
    query: str
    embedding: List[float]
    created_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class QueryEmbeddingCache:
    """
    Cache for query embeddings to reduce API calls and latency.

    Features:
    - Exact match lookup (O(1) via hash)
    - Semantic similarity lookup (O(n) but typically small cache)
    - TTL expiration
    - LRU eviction
    - Thread-safe operations
    """

    def __init__(
        self,
        embedding_provider: Any = None,
        max_size: int = 1000,
        ttl_seconds: int = 3600,  # 1 hour default
        similarity_threshold: float = 0.95,
        enable_semantic_lookup: bool = True,
    ):
        """
        Initialize query embedding cache.

        Args:
            embedding_provider: Provider with embed(text) method
            max_size: Maximum cached embeddings
            ttl_seconds: Time-to-live for entries
            similarity_threshold: Threshold for semantic match
            enable_semantic_lookup: Enable similarity-based lookup
        """
        self._provider = embedding_provider
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._similarity_threshold = similarity_threshold
        self._enable_semantic = enable_semantic_lookup

        # Exact match cache (query_hash -> CachedEmbedding)
        self._exact_cache: OrderedDict[str, CachedEmbedding] = OrderedDict()

        # Lock for thread safety
        self._lock = threading.RLock()

        # Stats
        self._hits = 0
        self._misses = 0
        self._semantic_hits = 0

    def _hash_query(self, query: str) -> str:
        """Create hash key for query."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _is_expired(self, entry: CachedEmbedding) -> bool:
        """Check if entry has expired."""
        return time.time() - entry.created_at > self._ttl

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        while len(self._exact_cache) >= self._max_size:
            # Remove oldest (first) item
            self._exact_cache.popitem(last=False)

    def _cleanup_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._exact_cache.items()
            if current_time - entry.created_at > self._ttl
        ]
        for key in expired_keys:
            del self._exact_cache[key]

    def get(self, query: str) -> Optional[List[float]]:
        """
        Get cached embedding for query (exact match only).

        Returns:
            Cached embedding or None if not found
        """
        with self._lock:
            key = self._hash_query(query)

            if key in self._exact_cache:
                entry = self._exact_cache[key]

                # Check expiration
                if self._is_expired(entry):
                    del self._exact_cache[key]
                    return None

                # Update access stats
                entry.access_count += 1
                entry.last_accessed = time.time()

                # Move to end (most recently used)
                self._exact_cache.move_to_end(key)

                self._hits += 1
                return entry.embedding

            return None

    def get_similar(self, query: str, query_embedding: List[float]) -> Optional[Tuple[str, List[float]]]:
        """
        Find similar cached query via semantic similarity.

        Args:
            query: Original query
            query_embedding: Embedding of the query

        Returns:
            Tuple of (similar_query, embedding) or None
        """
        if not self._enable_semantic:
            return None

        with self._lock:
            best_match = None
            best_similarity = 0.0

            for key, entry in self._exact_cache.items():
                if self._is_expired(entry):
                    continue

                similarity = self._cosine_similarity(query_embedding, entry.embedding)

                if similarity >= self._similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry

            if best_match:
                self._semantic_hits += 1
                return (best_match.query, best_match.embedding)

            return None

    def set(self, query: str, embedding: List[float]):
        """
        Cache an embedding for a query.

        Args:
            query: Original query
            embedding: Computed embedding
        """
        with self._lock:
            # Cleanup expired entries periodically
            if len(self._exact_cache) % 100 == 0:
                self._cleanup_expired()

            # Evict if needed
            self._evict_if_needed()

            key = self._hash_query(query)
            self._exact_cache[key] = CachedEmbedding(
                query=query,
                embedding=embedding,
                created_at=time.time(),
            )

    def get_or_embed(self, query: str) -> List[float]:
        """
        Get cached embedding or generate new one.

        This is the main entry point for the cache.

        Args:
            query: Query to embed

        Returns:
            Embedding vector
        """
        # Try exact match first
        cached = self.get(query)
        if cached:
            return cached

        self._misses += 1

        # Generate new embedding
        if self._provider is None:
            raise ValueError("No embedding provider configured")

        embedding = self._provider.embed(query)

        # Try semantic lookup before caching
        if self._enable_semantic and len(self._exact_cache) > 0:
            similar = self.get_similar(query, embedding)
            if similar:
                # Reuse similar embedding (saves storage)
                return similar[1]

        # Cache the new embedding
        self.set(query, embedding)

        return embedding

    def invalidate(self, query: str):
        """Invalidate cache entry for a query."""
        with self._lock:
            key = self._hash_query(query)
            if key in self._exact_cache:
                del self._exact_cache[key]

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._exact_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._exact_cache),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "semantic_hits": self._semantic_hits,
                "hit_rate": round(hit_rate, 4),
                "total_requests": total_requests,
                "memory_estimate_kb": len(self._exact_cache) * 8,  # ~8KB per 1536-dim embedding
            }


# =============================================================================
# ASYNC VERSION
# =============================================================================

class AsyncQueryEmbeddingCache:
    """
    Async version of QueryEmbeddingCache for use with async embedding providers.
    """

    def __init__(
        self,
        embedding_provider: Any = None,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        similarity_threshold: float = 0.95,
    ):
        self._sync_cache = QueryEmbeddingCache(
            embedding_provider=None,  # We handle async provider separately
            max_size=max_size,
            ttl_seconds=ttl_seconds,
            similarity_threshold=similarity_threshold,
            enable_semantic_lookup=True,
        )
        self._provider = embedding_provider

    async def get_or_embed(self, query: str) -> List[float]:
        """Async version of get_or_embed."""
        # Try cache first
        cached = self._sync_cache.get(query)
        if cached:
            return cached

        # Generate new embedding async
        if self._provider is None:
            raise ValueError("No embedding provider configured")

        embedding = await self._provider.embed_async(query)

        # Cache it
        self._sync_cache.set(query, embedding)

        return embedding

    def get_stats(self) -> Dict[str, Any]:
        return self._sync_cache.get_stats()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CachedEmbedding",
    "QueryEmbeddingCache",
    "AsyncQueryEmbeddingCache",
]
