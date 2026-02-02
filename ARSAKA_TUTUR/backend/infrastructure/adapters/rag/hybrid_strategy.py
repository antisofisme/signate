"""
Hybrid RAG Strategy

Combines dense vector search with BM25 keyword matching.
"""

import time
from typing import Optional, List, Dict, Any
import re
from collections import Counter
import math

from ....core.interfaces import RAGStrategy, VectorStore, EmbeddingProvider
from ....core.entities import RetrievalContext, RetrievalResult, SearchResult
from ....shared.logging import get_logger

logger = get_logger(__name__)


class HybridRAGStrategy(RAGStrategy):
    """
    Hybrid RAG - combines dense vectors with sparse BM25.

    Pipeline:
    1. Dense search (semantic similarity)
    2. BM25 search (keyword matching) - using PostgreSQL FTS
    3. Reciprocal Rank Fusion (RRF) to combine results
    4. Optional reranking

    Good for:
    - Larger knowledge bases
    - Technical content with specific terms
    - When keyword matches matter
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        db_pool=None,  # For BM25 via PostgreSQL FTS
        collection_prefix: str = "knowledge",
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.db_pool = db_pool
        self.collection_prefix = collection_prefix
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k  # RRF constant

    @property
    def strategy_name(self) -> str:
        return "hybrid"

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get collection name for tenant."""
        return f"{self.collection_prefix}_{tenant_id}"

    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> RetrievalResult:
        """
        Retrieve using hybrid dense + sparse search.

        Args:
            query: User query
            context: RetrievalContext

        Returns:
            RetrievalResult with fused results
        """
        start_time = time.time()

        # 1. Dense search
        query_embedding = await self.embedding_provider.embed(query)

        filters = {"tenant_id": context.tenant_id}
        if context.filters:
            filters.update(context.filters)

        collection = self._get_collection_name(context.tenant_id)

        dense_results = await self.vector_store.search(
            collection=collection,
            query_vector=query_embedding,
            top_k=context.top_k * 2,  # Get more for fusion
            filters=filters,
            score_threshold=0.0,  # Don't filter yet
        )

        # 2. Sparse search (BM25 via PostgreSQL FTS if available)
        sparse_results = []
        if self.db_pool:
            sparse_results = await self._bm25_search(
                query=query,
                tenant_id=context.tenant_id,
                top_k=context.top_k * 2,
                filters=context.filters,
            )

        # 3. Fuse results using RRF
        if sparse_results:
            fused_results = self._reciprocal_rank_fusion(
                dense_results,
                sparse_results,
                top_k=context.top_k,
            )
        else:
            # Fallback to dense only
            fused_results = dense_results[:context.top_k]

        # 4. Apply score threshold
        fused_results = [
            r for r in fused_results
            if r.score >= context.score_threshold
        ]

        retrieval_time = (time.time() - start_time) * 1000

        logger.debug(
            f"Hybrid RAG: {len(fused_results)} results in {retrieval_time:.1f}ms "
            f"(dense={len(dense_results)}, sparse={len(sparse_results)})"
        )

        return RetrievalResult(
            results=fused_results,
            query_embedding=query_embedding,
            retrieval_time_ms=retrieval_time,
            strategy_used=self.strategy_name,
            was_reranked=False,
        )

    async def _bm25_search(
        self,
        query: str,
        tenant_id: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        BM25 search using PostgreSQL full-text search.

        Requires a documents table with ts_vector column.
        """
        if not self.db_pool:
            return []

        try:
            # Build query - convert to tsquery format
            query_terms = self._tokenize_query(query)
            if not query_terms:
                return []

            ts_query = " | ".join(query_terms)  # OR between terms

            # Search using PostgreSQL FTS
            sql = """
                SELECT
                    id,
                    content,
                    metadata,
                    ts_rank_cd(search_vector, plainto_tsquery('english', $1)) as score
                FROM documents
                WHERE tenant_id = $2
                  AND search_vector @@ plainto_tsquery('english', $1)
                ORDER BY score DESC
                LIMIT $3
            """

            rows = await self.db_pool.fetch(sql, query, tenant_id, top_k)

            return [
                SearchResult(
                    id=str(row["id"]),
                    score=float(row["score"]),
                    content=row["content"],
                    metadata=row["metadata"] or {},
                )
                for row in rows
            ]

        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return []

    def _tokenize_query(self, query: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Remove special characters, lowercase
        text = re.sub(r'[^\w\s]', ' ', query.lower())
        # Split and filter
        tokens = [t for t in text.split() if len(t) > 2]
        return tokens

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).

        RRF score = sum(1 / (k + rank_i)) for each result list
        """
        # Build id -> result mapping
        all_results: Dict[str, SearchResult] = {}
        for r in dense_results + sparse_results:
            if r.id not in all_results:
                all_results[r.id] = r

        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}

        # Dense contribution
        for rank, result in enumerate(dense_results, 1):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0)
            rrf_scores[result.id] += self.dense_weight / (self.rrf_k + rank)

        # Sparse contribution
        for rank, result in enumerate(sparse_results, 1):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0)
            rrf_scores[result.id] += self.sparse_weight / (self.rrf_k + rank)

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build final results with RRF score
        fused = []
        for id in sorted_ids[:top_k]:
            result = all_results[id]
            # Update score with RRF score (normalized to 0-1)
            fused.append(SearchResult(
                id=result.id,
                score=rrf_scores[id],
                content=result.content,
                metadata=result.metadata,
                document_id=result.document_id,
            ))

        return fused

    async def ensure_collection(self, tenant_id: str) -> bool:
        """Ensure collection exists for tenant."""
        collection = self._get_collection_name(tenant_id)
        return await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.embedding_provider.dimensions,
        )
