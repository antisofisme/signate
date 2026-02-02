"""
Vanilla RAG Strategy

Simple dense vector search only.
"""

import time
from typing import Optional, List

from ....core.interfaces import RAGStrategy, VectorStore, EmbeddingProvider
from ....core.entities import RetrievalContext, RetrievalResult, SearchResult
from ....shared.logging import get_logger

logger = get_logger(__name__)


class VanillaRAGStrategy(RAGStrategy):
    """
    Vanilla RAG - dense vector search only.

    Simple and effective for most use cases:
    1. Embed query
    2. Search vector store
    3. Return top-k results

    Good for:
    - Small to medium knowledge bases
    - Simple semantic search
    - Low latency requirements
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        collection_prefix: str = "knowledge"
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.collection_prefix = collection_prefix

    @property
    def strategy_name(self) -> str:
        return "vanilla"

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get collection name for tenant."""
        return f"{self.collection_prefix}_{tenant_id}"

    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> RetrievalResult:
        """
        Retrieve relevant documents using dense vector search.

        Args:
            query: User query
            context: RetrievalContext with tenant, filters, etc.

        Returns:
            RetrievalResult with documents and metadata
        """
        start_time = time.time()

        # 1. Embed query
        query_embedding = await self.embedding_provider.embed(query)

        # 2. Build filters
        filters = {"tenant_id": context.tenant_id}
        if context.filters:
            filters.update(context.filters)

        # 3. Search vector store
        collection = self._get_collection_name(context.tenant_id)

        results = await self.vector_store.search(
            collection=collection,
            query_vector=query_embedding,
            top_k=context.top_k,
            filters=filters,
            score_threshold=context.score_threshold,
        )

        # 4. Build result
        retrieval_time = (time.time() - start_time) * 1000

        logger.debug(
            f"Vanilla RAG: {len(results)} results in {retrieval_time:.1f}ms "
            f"for tenant {context.tenant_id}"
        )

        return RetrievalResult(
            results=results,
            query_embedding=query_embedding,
            retrieval_time_ms=retrieval_time,
            strategy_used=self.strategy_name,
            was_reranked=False,
        )

    async def ensure_collection(self, tenant_id: str) -> bool:
        """Ensure collection exists for tenant."""
        collection = self._get_collection_name(tenant_id)
        return await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.embedding_provider.dimensions,
        )
