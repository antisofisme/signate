"""
RAG Orchestrator

Coordinates the RAG pipeline for document retrieval.
"""

from typing import Optional, List, Dict, Any

from ..interfaces import RAGStrategy, VectorStore
from ..entities import (
    RequestContext,
    RetrievalContext,
    RetrievalResult,
    SearchResult,
    Document,
    Chunk,
)
from .embedding_service import EmbeddingService
from ...shared.logging import get_logger

logger = get_logger(__name__)


class RAGOrchestrator:
    """
    Orchestrates the RAG retrieval pipeline.

    Responsibilities:
    - Strategy selection based on tenant config
    - Context building for retrieval
    - Document indexing
    - Search coordination
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        default_strategy: Optional[RAGStrategy] = None,
        strategies: Optional[Dict[str, RAGStrategy]] = None,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.default_strategy = default_strategy
        self.strategies = strategies or {}

    def _get_strategy(self, strategy_name: str) -> RAGStrategy:
        """Get strategy by name."""
        if strategy_name in self.strategies:
            return self.strategies[strategy_name]
        if self.default_strategy:
            return self.default_strategy
        raise ValueError(f"No RAG strategy found for: {strategy_name}")

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get collection name for tenant."""
        return f"knowledge_{tenant_id}"

    async def search(
        self,
        ctx: RequestContext,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.3,
    ) -> RetrievalResult:
        """
        Search for relevant documents.

        Args:
            ctx: Request context
            query: Search query
            top_k: Number of results
            filters: Optional metadata filters
            score_threshold: Minimum similarity score

        Returns:
            RetrievalResult with documents
        """
        # Get strategy from tenant config
        strategy_name = "vanilla"
        if ctx.tenant_config:
            strategy_name = ctx.tenant_config.rag_config.strategy

        strategy = self._get_strategy(strategy_name)

        # Build retrieval context
        retrieval_ctx = RetrievalContext(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            top_k=top_k,
            filters=filters or {},
            score_threshold=score_threshold,
            rerank=ctx.tenant_config.rag_config.reranker_enabled if ctx.tenant_config else False,
        )

        # Execute retrieval
        result = await strategy.retrieve(query, retrieval_ctx)

        logger.info(
            f"RAG search: {len(result.results)} results in {result.retrieval_time_ms:.1f}ms "
            f"(strategy={strategy_name}, tenant={ctx.tenant_id})"
        )

        return result

    async def index_document(
        self,
        tenant_id: str,
        document: Document,
        chunks: List[Chunk],
    ) -> int:
        """
        Index a document with its chunks.

        Args:
            tenant_id: Tenant ID
            document: Document metadata
            chunks: List of chunks with content

        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0

        collection = self._get_collection_name(tenant_id)

        # Ensure collection exists
        await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.embedding_service.dimensions,
        )

        # Embed all chunks
        contents = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(contents, tenant_id)

        # Prepare points for upsert
        items = []
        for chunk, embedding in zip(chunks, embeddings):
            payload = {
                "tenant_id": tenant_id,
                "document_id": document.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "source": document.source,
                **document.metadata,
                **chunk.metadata,
            }

            items.append({
                "id": chunk.id or f"{document.id}_{chunk.chunk_index}",
                "vector": embedding,
                "payload": payload,
            })

        # Batch upsert
        count = await self.vector_store.upsert_batch(collection, items)

        logger.info(f"Indexed {count} chunks for document {document.id}")
        return count

    async def delete_document(
        self,
        tenant_id: str,
        document_id: str,
    ) -> int:
        """
        Delete a document and all its chunks.

        Args:
            tenant_id: Tenant ID
            document_id: Document ID

        Returns:
            Number of chunks deleted
        """
        collection = self._get_collection_name(tenant_id)

        count = await self.vector_store.delete_by_filter(
            collection=collection,
            filters={
                "tenant_id": tenant_id,
                "document_id": document_id,
            },
        )

        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count

    async def ensure_tenant_collection(self, tenant_id: str) -> bool:
        """Ensure collection exists for tenant."""
        collection = self._get_collection_name(tenant_id)
        return await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.embedding_service.dimensions,
        )

    async def get_collection_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get collection statistics for tenant."""
        collection = self._get_collection_name(tenant_id)

        try:
            # Check if collection exists
            from ..interfaces.storage import VectorStore

            if hasattr(self.vector_store, 'get_collection_info'):
                return await self.vector_store.get_collection_info(collection)
            return {"name": collection, "status": "unknown"}

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"name": collection, "error": str(e)}
