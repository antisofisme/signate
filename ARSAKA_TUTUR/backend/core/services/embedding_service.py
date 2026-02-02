"""
Embedding Service

Cached embedding generation with deduplication.
"""

import hashlib
from typing import Optional, List

from ..interfaces import EmbeddingProvider, ICache
from ...shared.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Embedding service with caching.

    Features:
    - Content hashing for deduplication
    - Redis cache for embeddings
    - Batch processing
    - Multiple provider support
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        cache: Optional[ICache] = None,
        cache_ttl: int = 86400 * 7,  # 7 days
    ):
        self.provider = embedding_provider
        self.cache = cache
        self.cache_ttl = cache_ttl

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    @property
    def dimensions(self) -> int:
        return self.provider.dimensions

    def _content_hash(self, content: str) -> str:
        """Generate SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _cache_key(self, tenant_id: str, content_hash: str) -> str:
        """Generate cache key."""
        return f"embed:{tenant_id}:{self.model_name}:{content_hash}"

    async def embed(
        self,
        content: str,
        tenant_id: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        Embed content with caching.

        Args:
            content: Text to embed
            tenant_id: Tenant ID for cache isolation
            use_cache: Whether to use cache

        Returns:
            Embedding vector
        """
        content_hash = self._content_hash(content)

        # Check cache
        if use_cache and self.cache:
            cache_key = self._cache_key(tenant_id, content_hash)
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Embedding cache hit for {content_hash[:8]}...")
                return cached

        # Generate embedding
        embedding = await self.provider.embed(content)

        # Store in cache
        if use_cache and self.cache:
            cache_key = self._cache_key(tenant_id, content_hash)
            await self.cache.set(cache_key, embedding, self.cache_ttl)
            logger.debug(f"Cached embedding for {content_hash[:8]}...")

        return embedding

    async def embed_batch(
        self,
        contents: List[str],
        tenant_id: str,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Embed multiple contents with caching.

        Args:
            contents: List of texts
            tenant_id: Tenant ID
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        if not contents:
            return []

        # Generate hashes
        hashes = [self._content_hash(c) for c in contents]

        # Check cache for all
        cached_embeddings: dict = {}
        uncached_indices: List[int] = []

        if use_cache and self.cache:
            cache_keys = [self._cache_key(tenant_id, h) for h in hashes]
            cached = await self.cache.get_many(cache_keys)

            for i, (key, hash) in enumerate(zip(cache_keys, hashes)):
                if key in cached:
                    cached_embeddings[i] = cached[key]
                else:
                    uncached_indices.append(i)
        else:
            uncached_indices = list(range(len(contents)))

        # Generate missing embeddings
        if uncached_indices:
            uncached_contents = [contents[i] for i in uncached_indices]
            new_embeddings = await self.provider.embed_batch(uncached_contents)

            # Store in cache and collect
            cache_items = {}
            for idx, embedding in zip(uncached_indices, new_embeddings):
                cached_embeddings[idx] = embedding
                if use_cache and self.cache:
                    cache_key = self._cache_key(tenant_id, hashes[idx])
                    cache_items[cache_key] = embedding

            if cache_items:
                await self.cache.set_many(cache_items, self.cache_ttl)

            logger.debug(
                f"Batch embed: {len(new_embeddings)} new, "
                f"{len(contents) - len(new_embeddings)} cached"
            )

        # Return in order
        return [cached_embeddings[i] for i in range(len(contents))]

    async def embed_query(
        self,
        query: str,
        tenant_id: str
    ) -> List[float]:
        """
        Embed a search query.

        Queries are cached with shorter TTL since they're often unique.
        """
        return await self.embed(
            content=query,
            tenant_id=tenant_id,
            use_cache=True,  # Cache queries too
        )

    async def embed_document(
        self,
        content: str,
        tenant_id: str
    ) -> List[float]:
        """
        Embed a document chunk.

        Documents are cached with longer TTL.
        """
        return await self.embed(
            content=content,
            tenant_id=tenant_id,
            use_cache=True,
        )
