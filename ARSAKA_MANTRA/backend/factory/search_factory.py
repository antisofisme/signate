"""
Search Factory - Creates search-related adapter instances.

Handles:
- Vector Store (Qdrant, Memory)
- Embedding Service (OpenAI, Local, Ollama, NoOp)
- Text Search (Meilisearch, Memory)

Usage:
    from factory.search_factory import SearchFactory

    vector_store = SearchFactory.get_vector_store()
    embedding = SearchFactory.get_embedding()
    text_search = SearchFactory.get_text_search()
"""

import logging
from typing import Optional

from core.runtime.config import get_config
from core.ports.vector_store import VectorStoreProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.ports.text_search import TextSearchProtocol
from factory.base import FactoryMixin

logger = logging.getLogger(__name__)


class SearchFactory(FactoryMixin):
    """Factory for creating search-related instances."""

    _vector_store: Optional[VectorStoreProtocol] = None
    _embedding: Optional[EmbeddingProtocol] = None
    _text_search: Optional[TextSearchProtocol] = None

    # =========================================================================
    # Vector Store
    # =========================================================================

    @classmethod
    def get_vector_store(cls) -> VectorStoreProtocol:
        """
        Get vector store instance based on configuration.

        Supports:
        - qdrant: Qdrant vector database
        - memory: In-memory store for testing

        Returns:
            VectorStoreProtocol implementation
        """
        if cls._vector_store is None:
            config = get_config()
            store_type = config.vector_store.lower()

            if store_type == "qdrant":
                cls._vector_store = cls._create_qdrant_store(config)
            elif store_type == "memory":
                cls._vector_store = cls._create_memory_vector_store(config)
            else:
                cls.log_fallback("VectorStore", f"Unknown type: {store_type}", "memory")
                cls._vector_store = cls._create_memory_vector_store(config)

        return cls._vector_store

    @classmethod
    def _create_qdrant_store(cls, config) -> VectorStoreProtocol:
        """Create Qdrant vector store instance."""
        from adapters.vector_stores.qdrant_adapter import QdrantVectorStore

        store = QdrantVectorStore(
            url=config.qdrant_url,
            collection_name=config.qdrant_collection,
            api_key=config.qdrant_api_key or None,
        )
        cls.log_using("VectorStore", "Qdrant", config.qdrant_url)
        return store

    @classmethod
    def _create_memory_vector_store(cls, config) -> VectorStoreProtocol:
        """Create in-memory vector store instance."""
        from adapters.vector_stores.memory_adapter import MemoryVectorStore

        store = MemoryVectorStore(collection_name=config.qdrant_collection)
        cls.log_using("VectorStore", "InMemory")
        return store

    # =========================================================================
    # Embedding Service
    # =========================================================================

    @classmethod
    def get_embedding(cls) -> EmbeddingProtocol:
        """
        Get embedding service instance based on configuration.

        Supports:
        - openai: OpenAI embeddings API (cloud, requires API key)
        - local: sentence-transformers (runs offline, no API needed)
        - ollama: Ollama local server (self-hosted LLM)
        - noop: No-op embedding for testing

        Returns:
            EmbeddingProtocol implementation
        """
        if cls._embedding is None:
            config = get_config()
            service_type = config.embedding_service.lower()

            if service_type == "openai":
                cls._embedding = cls._create_openai_embedding(config)
            elif service_type == "local":
                cls._embedding = cls._create_local_embedding(config)
            elif service_type == "ollama":
                cls._embedding = cls._create_ollama_embedding(config)
            elif service_type == "noop":
                cls._embedding = cls._create_noop_embedding(config)
            else:
                cls.log_fallback("Embedding", f"Unknown type: {service_type}", "noop")
                cls._embedding = cls._create_noop_embedding(config)

        return cls._embedding

    @classmethod
    def _create_openai_embedding(cls, config) -> EmbeddingProtocol:
        """Create OpenAI embedding instance."""
        api_key = config.openai_api_key

        if not api_key:
            cls.log_fallback("Embedding", "OpenAI API key not configured", "noop")
            return cls._create_noop_embedding(config)

        from adapters.embeddings.openai_adapter import OpenAIEmbedding

        embedding = OpenAIEmbedding(
            api_key=api_key,
            model=config.embedding_model,
            dimensions=config.embedding_dimensions,
        )
        cls.log_using("Embedding", "OpenAI", config.embedding_model)
        return embedding

    @classmethod
    def _create_local_embedding(cls, config) -> EmbeddingProtocol:
        """Create local sentence-transformers embedding instance."""
        try:
            from adapters.embeddings.local_adapter import LocalEmbedding

            embedding = LocalEmbedding(model_name=config.local_embedding_model)
            cls.log_using("Embedding", "Local", config.local_embedding_model)
            return embedding
        except ImportError as e:
            cls.log_fallback("Embedding", f"Local unavailable ({e})", "noop")
            return cls._create_noop_embedding(config)

    @classmethod
    def _create_ollama_embedding(cls, config) -> EmbeddingProtocol:
        """Create Ollama embedding instance."""
        from adapters.embeddings.ollama_adapter import OllamaEmbedding

        embedding = OllamaEmbedding(
            base_url=config.ollama_url,
            model=config.ollama_embedding_model,
        )
        cls.log_using("Embedding", "Ollama", f"{config.ollama_embedding_model} at {config.ollama_url}")
        return embedding

    @classmethod
    def _create_noop_embedding(cls, config) -> EmbeddingProtocol:
        """Create no-op embedding instance for testing."""
        from adapters.embeddings.noop_adapter import NoOpEmbedding

        embedding = NoOpEmbedding(dimensions=config.embedding_dimensions)
        cls.log_using("Embedding", "NoOp", "(testing mode)")
        return embedding

    # =========================================================================
    # Text Search (Meilisearch)
    # =========================================================================

    @classmethod
    def get_text_search(cls) -> Optional[TextSearchProtocol]:
        """
        Get text search instance based on configuration.

        Returns None if Meilisearch feature is disabled.

        Supports:
        - meilisearch: Meilisearch search engine (primary)
        - memory: In-memory search for testing

        Returns:
            TextSearchProtocol implementation or None
        """
        config = get_config()

        # Feature flag check
        if not config.feature_meilisearch_enabled:
            cls.log_disabled("Meilisearch")
            return None

        if cls._text_search is None:
            if config.meilisearch_url:
                cls._text_search = cls._create_meilisearch(config)
            else:
                cls._text_search = cls._create_memory_text_search()

        return cls._text_search

    @classmethod
    def _create_meilisearch(cls, config) -> TextSearchProtocol:
        """Create Meilisearch adapter instance."""
        try:
            from adapters.text_search.meilisearch_adapter import MeilisearchAdapter

            adapter = MeilisearchAdapter(
                url=config.meilisearch_url,
                api_key=config.meilisearch_api_key or None,
                index_name=config.meilisearch_index_decisions,
            )
            cls.log_using("TextSearch", "Meilisearch", config.meilisearch_url)
            return adapter
        except ImportError:
            cls.log_fallback("TextSearch", "meilisearch-python-sdk not installed", "memory")
            return cls._create_memory_text_search()

    @classmethod
    def _create_memory_text_search(cls) -> TextSearchProtocol:
        """Create in-memory text search instance."""
        from adapters.text_search.memory_adapter import MemoryTextSearchAdapter

        adapter = MemoryTextSearchAdapter()
        cls.log_using("TextSearch", "InMemory")
        return adapter

    # =========================================================================
    # Feature Flags
    # =========================================================================

    @classmethod
    def is_semantic_search_enabled(cls) -> bool:
        """Check if semantic search is enabled."""
        return get_config().enable_semantic_search

    @classmethod
    def is_meilisearch_enabled(cls) -> bool:
        """Check if Meilisearch feature is enabled."""
        return get_config().feature_meilisearch_enabled

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @classmethod
    def reset(cls) -> None:
        """Reset all cached instances."""
        cls._vector_store = None
        cls._embedding = None
        cls._text_search = None

    @classmethod
    async def close_all(cls) -> None:
        """Close all connections."""
        if cls._vector_store:
            await cls._vector_store.close()
        if cls._embedding:
            await cls._embedding.close()
        if cls._text_search:
            await cls._text_search.close()
        cls.reset()

    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize search services.

        Creates vector collection if needed.
        """
        if not cls.is_semantic_search_enabled():
            return

        vector_store = cls.get_vector_store()
        embedding = cls.get_embedding()

        if not await vector_store.collection_exists():
            await vector_store.create_collection(vector_size=embedding.dimensions)
            logger.info(f"Created vector collection with {embedding.dimensions} dimensions")

        # Health check for text search
        if cls.is_meilisearch_enabled():
            text_search = cls.get_text_search()
            if text_search:
                try:
                    if await text_search.health_check():
                        logger.info("Text search service healthy")
                    else:
                        logger.warning("Text search service not available")
                except Exception as e:
                    logger.warning(f"Text search health check failed: {e}")
