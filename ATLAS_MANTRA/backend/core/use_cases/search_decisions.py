"""
Search Decisions Use Case - Semantic search for MANTRA decisions.

This use case implements high-performance semantic search using:
- Vector embeddings for semantic similarity
- Caching for fast repeated queries
- Filtering by domain, aspect, tags

Usage:
    use_case = SearchDecisionsUseCase(vector_store, cache, embedding, repository)
    result = await use_case.execute(query="database technology", limit=10)
"""

import time
import hashlib
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from core.ports.vector_store import VectorStoreProtocol
from core.ports.cache import CacheProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.repositories.decision_repository import DecisionRepository
from core.domain.search_result import (
    SemanticSearchResult,
    SearchHit,
    SearchStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchDecisionsInput:
    """Input for semantic search."""
    query: str
    limit: int = 10
    min_score: float = 0.5
    domain_id: Optional[str] = None
    aspect_id: Optional[str] = None
    tags: Optional[List[str]] = None
    use_cache: bool = True


class SearchDecisionsUseCase:
    """
    Semantic search for MANTRA decisions.

    Workflow:
    1. Check cache for existing results
    2. Generate query embedding
    3. Search vector store
    4. Enrich results with full decision data
    5. Cache results for future queries
    """

    CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        vector_store: VectorStoreProtocol,
        cache: CacheProtocol,
        embedding_service: EmbeddingProtocol,
        repository: DecisionRepository,
    ):
        self.vector_store = vector_store
        self.cache = cache
        self.embedding = embedding_service
        self.repository = repository

    def _cache_key(self, input: SearchDecisionsInput) -> str:
        """Generate cache key from search input."""
        key_data = f"{input.query}:{input.limit}:{input.min_score}:{input.domain_id}:{input.aspect_id}:{input.tags}"
        hash_value = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"search:{hash_value}"

    async def execute(self, input: SearchDecisionsInput) -> SemanticSearchResult:
        """
        Execute semantic search.

        Args:
            input: Search parameters

        Returns:
            SemanticSearchResult with matched decisions
        """
        start_time = time.time()

        try:
            # 1. Check cache
            if input.use_cache:
                cache_key = self._cache_key(input)
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for query: {input.query[:50]}")
                    return SemanticSearchResult(
                        status=SearchStatus(cached["status"]),
                        hits=[SearchHit(**h) for h in cached["hits"]],
                        total_count=cached["total_count"],
                        query=input.query,
                        filters_applied=cached.get("filters_applied", {}),
                        execution_time_ms=(time.time() - start_time) * 1000,
                        cached=True,
                    )

            # 2. Generate query embedding
            query_vector = await self.embedding.embed(input.query)

            # 3. Build filters
            filters = {}
            if input.domain_id:
                filters["domain_id"] = input.domain_id
            if input.aspect_id:
                filters["aspect_id"] = input.aspect_id
            if input.tags:
                filters["tags"] = input.tags

            # 4. Search vector store
            vector_results = await self.vector_store.search(
                query_vector=query_vector,
                limit=input.limit,
                min_score=input.min_score,
                filters=filters if filters else None,
            )

            # 5. Build search hits
            hits = []
            for vr in vector_results:
                # Get full decision from repository if available
                decision = self.repository.find_by_id(vr.id)
                if decision:
                    hits.append(SearchHit(
                        decision_id=vr.id,
                        decision_code=decision.decision_code,
                        statement=decision.statement,
                        rationale=decision.rationale,
                        score=vr.score,
                        domain_id=decision.domain_id.value if hasattr(decision.domain_id, 'value') else str(decision.domain_id),
                        aspect_id=decision.aspect_id.value if hasattr(decision.aspect_id, 'value') else str(decision.aspect_id),
                        version=decision.version,
                        tags=[t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
                    ))
                else:
                    # Fallback to payload data
                    payload = vr.payload
                    hits.append(SearchHit(
                        decision_id=vr.id,
                        decision_code=payload.get("decision_code", vr.id),
                        statement=payload.get("statement", ""),
                        rationale=payload.get("rationale", ""),
                        score=vr.score,
                        domain_id=payload.get("domain_id", ""),
                        aspect_id=payload.get("aspect_id", ""),
                        version=payload.get("version", "1.0.0"),
                        tags=payload.get("tags", []),
                    ))

            # Determine status
            status = SearchStatus.FOUND if hits else SearchStatus.NOT_FOUND

            result = SemanticSearchResult(
                status=status,
                hits=hits,
                total_count=len(hits),
                query=input.query,
                filters_applied=filters,
                execution_time_ms=(time.time() - start_time) * 1000,
                cached=False,
            )

            # 6. Cache results
            if input.use_cache and hits:
                cache_data = {
                    "status": result.status.value,
                    "hits": [h.to_dict() for h in result.hits],
                    "total_count": result.total_count,
                    "filters_applied": result.filters_applied,
                }
                await self.cache.set(cache_key, cache_data, ttl=self.CACHE_TTL)

            logger.info(f"Search completed: query='{input.query[:50]}', hits={len(hits)}, time={result.execution_time_ms:.1f}ms")
            return result

        except Exception as e:
            logger.error(f"Search error: {e}")
            return SemanticSearchResult(
                status=SearchStatus.ERROR,
                hits=[],
                total_count=0,
                query=input.query,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )


async def search_decisions(
    query: str,
    vector_store: VectorStoreProtocol,
    cache: CacheProtocol,
    embedding_service: EmbeddingProtocol,
    repository: DecisionRepository,
    limit: int = 10,
    min_score: float = 0.5,
    domain_id: Optional[str] = None,
    aspect_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    use_cache: bool = True,
) -> SemanticSearchResult:
    """
    Convenience function for semantic search.

    Args:
        query: Search query text
        vector_store: Vector store implementation
        cache: Cache implementation
        embedding_service: Embedding service implementation
        repository: Decision repository
        limit: Maximum results
        min_score: Minimum similarity score
        domain_id: Filter by domain
        aspect_id: Filter by aspect
        tags: Filter by tags
        use_cache: Whether to use caching

    Returns:
        SemanticSearchResult
    """
    use_case = SearchDecisionsUseCase(
        vector_store=vector_store,
        cache=cache,
        embedding_service=embedding_service,
        repository=repository,
    )
    return await use_case.execute(SearchDecisionsInput(
        query=query,
        limit=limit,
        min_score=min_score,
        domain_id=domain_id,
        aspect_id=aspect_id,
        tags=tags,
        use_cache=use_cache,
    ))
