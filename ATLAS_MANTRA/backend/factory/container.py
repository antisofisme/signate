"""
Dependency Injection Container - Factory for creating service instances.

This container manages the lifecycle of adapters and provides them
to use cases. It follows the Factory pattern and ensures singleton
instances for shared resources.

Configuration is read from environment variables through the Config class.

Usage:
    from factory.container import Container

    # Get instances
    vector_store = Container.get_vector_store()
    cache = Container.get_cache()
    embedding = Container.get_embedding()
    repository = Container.get_decision_repository()

    # Reset for testing
    Container.reset()
"""

import logging
from typing import Optional

from core.runtime.config import get_config
from core.ports.vector_store import VectorStoreProtocol
from core.ports.cache import CacheProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.ports.message_queue import MessageQueueProtocol
from core.ports.text_search import TextSearchProtocol
from core.repositories.decision_repository import DecisionRepository

logger = logging.getLogger(__name__)


class Container:
    """
    Dependency injection container for MANTRA services.

    Provides factory methods that create appropriate adapter
    implementations based on configuration. Instances are cached
    for reuse (singleton pattern).
    """

    _vector_store: Optional[VectorStoreProtocol] = None
    _cache: Optional[CacheProtocol] = None
    _embedding: Optional[EmbeddingProtocol] = None
    _decision_repository: Optional[DecisionRepository] = None
    _message_queue: Optional[MessageQueueProtocol] = None
    _text_search: Optional[TextSearchProtocol] = None
    _repository_initialized: bool = False
    _initialized: bool = False

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
                from adapters.vector_stores.qdrant_adapter import QdrantVectorStore
                cls._vector_store = QdrantVectorStore(
                    url=config.qdrant_url,
                    collection_name=config.qdrant_collection,
                    api_key=config.qdrant_api_key or None,
                )
                logger.info(f"Using Qdrant vector store: {config.qdrant_url}")

            elif store_type == "memory":
                from adapters.vector_stores.memory_adapter import MemoryVectorStore
                cls._vector_store = MemoryVectorStore(
                    collection_name=config.qdrant_collection,
                )
                logger.info("Using in-memory vector store")

            else:
                # Default to memory
                logger.warning(f"Unknown vector store type: {store_type}, using memory")
                from adapters.vector_stores.memory_adapter import MemoryVectorStore
                cls._vector_store = MemoryVectorStore()

        return cls._vector_store

    @classmethod
    def get_cache(cls) -> CacheProtocol:
        """
        Get cache instance based on configuration.

        Supports:
        - redis: Redis cache
        - memory: In-memory cache for testing

        Returns:
            CacheProtocol implementation
        """
        if cls._cache is None:
            config = get_config()
            cache_type = config.cache.lower()

            if cache_type == "redis":
                from adapters.caches.redis_adapter import RedisCache
                cls._cache = RedisCache(
                    url=config.redis_url,
                    default_ttl=config.cache_ttl,
                )
                logger.info(f"Using Redis cache: {config.redis_url}")

            elif cache_type == "memory":
                from adapters.caches.memory_adapter import MemoryCache
                cls._cache = MemoryCache(
                    default_ttl=config.cache_ttl,
                )
                logger.info("Using in-memory cache")

            else:
                # Default to memory
                logger.warning(f"Unknown cache type: {cache_type}, using memory")
                from adapters.caches.memory_adapter import MemoryCache
                cls._cache = MemoryCache()

        return cls._cache

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
                api_key = config.openai_api_key
                if not api_key:
                    logger.warning("OpenAI API key not configured, falling back to noop")
                    from adapters.embeddings.noop_adapter import NoOpEmbedding
                    cls._embedding = NoOpEmbedding(
                        dimensions=config.embedding_dimensions,
                    )
                else:
                    from adapters.embeddings.openai_adapter import OpenAIEmbedding
                    cls._embedding = OpenAIEmbedding(
                        api_key=api_key,
                        model=config.embedding_model,
                        dimensions=config.embedding_dimensions,
                    )
                    logger.info(f"Using OpenAI embedding: {config.embedding_model}")

            elif service_type == "local":
                try:
                    from adapters.embeddings.local_adapter import LocalEmbedding
                    cls._embedding = LocalEmbedding(
                        model_name=config.local_embedding_model,
                    )
                    logger.info(f"Using local embedding: {config.local_embedding_model}")
                except ImportError as e:
                    logger.warning(f"Local embedding unavailable ({e}), falling back to noop")
                    from adapters.embeddings.noop_adapter import NoOpEmbedding
                    cls._embedding = NoOpEmbedding(
                        dimensions=config.embedding_dimensions,
                    )

            elif service_type == "ollama":
                from adapters.embeddings.ollama_adapter import OllamaEmbedding
                cls._embedding = OllamaEmbedding(
                    base_url=config.ollama_url,
                    model=config.ollama_embedding_model,
                )
                logger.info(f"Using Ollama embedding: {config.ollama_embedding_model} at {config.ollama_url}")

            elif service_type == "noop":
                from adapters.embeddings.noop_adapter import NoOpEmbedding
                cls._embedding = NoOpEmbedding(
                    dimensions=config.embedding_dimensions,
                )
                logger.info("Using NoOp embedding (testing mode)")

            else:
                # Default to noop
                logger.warning(f"Unknown embedding service: {service_type}, using noop")
                from adapters.embeddings.noop_adapter import NoOpEmbedding
                cls._embedding = NoOpEmbedding()

        return cls._embedding

    @classmethod
    def get_decision_repository(cls) -> DecisionRepository:
        """
        Get decision repository instance based on configuration.

        Supports:
        - postgresql: PostgreSQL database (production)
        - memory: In-memory store for testing

        Note: For PostgreSQL, call initialize() first to establish connection.

        Returns:
            DecisionRepository implementation
        """
        if cls._decision_repository is None:
            config = get_config()

            if config.database_url:
                # PostgreSQL - will be initialized in initialize()
                # Return a lazy proxy that requires initialization
                from core.repositories.decision_repository import InMemoryDecisionRepository
                # Temporarily use in-memory until initialize() is called
                cls._decision_repository = InMemoryDecisionRepository()
                logger.info("Decision repository: InMemory (pending initialization)")
            else:
                # No database configured - use in-memory
                from core.repositories.decision_repository import InMemoryDecisionRepository
                cls._decision_repository = InMemoryDecisionRepository()
                cls._repository_initialized = True
                logger.info("Using in-memory decision repository")

        return cls._decision_repository

    @classmethod
    def get_message_queue(cls) -> Optional[MessageQueueProtocol]:
        """
        Get message queue instance based on configuration.

        Returns None if RabbitMQ feature is disabled.

        Supports:
        - rabbitmq: RabbitMQ message broker (primary)
        - redis_streams: Redis Streams (fallback)
        - memory: In-memory queue for testing

        Returns:
            MessageQueueProtocol implementation or None
        """
        config = get_config()

        # Feature flag check
        if not config.feature_rabbitmq_enabled:
            logger.debug("RabbitMQ feature is disabled")
            return None

        if cls._message_queue is None:
            # Determine adapter based on config
            if config.rabbitmq_url and config.rabbitmq_url.startswith("amqp"):
                try:
                    from adapters.message_queues.rabbitmq_adapter import RabbitMQAdapter
                    cls._message_queue = RabbitMQAdapter(
                        url=config.rabbitmq_url,
                        exchange_name=config.rabbitmq_exchange,
                    )
                    logger.info(f"Using RabbitMQ message queue")
                except ImportError:
                    logger.warning("aio-pika not installed, using memory queue")
                    from adapters.message_queues.memory_adapter import MemoryQueueAdapter
                    cls._message_queue = MemoryQueueAdapter()

            elif config.redis_url:
                # Fallback to Redis Streams
                try:
                    from adapters.message_queues.redis_streams_adapter import RedisStreamsAdapter
                    cls._message_queue = RedisStreamsAdapter(
                        url=config.redis_url,
                    )
                    logger.info("Using Redis Streams message queue (fallback)")
                except ImportError:
                    from adapters.message_queues.memory_adapter import MemoryQueueAdapter
                    cls._message_queue = MemoryQueueAdapter()

            else:
                # In-memory for development/testing
                from adapters.message_queues.memory_adapter import MemoryQueueAdapter
                cls._message_queue = MemoryQueueAdapter()
                logger.info("Using in-memory message queue")

        return cls._message_queue

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
            logger.debug("Meilisearch feature is disabled")
            return None

        if cls._text_search is None:
            if config.meilisearch_url:
                try:
                    from adapters.text_search.meilisearch_adapter import MeilisearchAdapter
                    cls._text_search = MeilisearchAdapter(
                        url=config.meilisearch_url,
                        api_key=config.meilisearch_api_key or None,
                        index_name=config.meilisearch_index_decisions,
                    )
                    logger.info(f"Using Meilisearch text search: {config.meilisearch_url}")
                except ImportError:
                    logger.warning("meilisearch-python-sdk not installed, using memory search")
                    from adapters.text_search.memory_adapter import MemoryTextSearchAdapter
                    cls._text_search = MemoryTextSearchAdapter()

            else:
                # In-memory for development/testing
                from adapters.text_search.memory_adapter import MemoryTextSearchAdapter
                cls._text_search = MemoryTextSearchAdapter()
                logger.info("Using in-memory text search")

        return cls._text_search

    @classmethod
    def is_meilisearch_enabled(cls) -> bool:
        """Check if Meilisearch feature is enabled."""
        config = get_config()
        return config.feature_meilisearch_enabled

    @classmethod
    def is_rabbitmq_enabled(cls) -> bool:
        """Check if RabbitMQ feature is enabled."""
        config = get_config()
        return config.feature_rabbitmq_enabled

    @classmethod
    async def initialize_repository(cls) -> None:
        """
        Initialize the decision repository.

        If database_url is configured, creates PostgreSQL repository.
        Otherwise, keeps in-memory repository.
        """
        if cls._repository_initialized:
            return

        config = get_config()

        if config.database_url:
            try:
                from adapters.repositories.postgres_decision_repository import PostgresDecisionRepository
                repo = PostgresDecisionRepository(config.database_url)
                await repo.initialize()
                cls._decision_repository = repo
                cls._repository_initialized = True
                logger.info(f"Decision repository: PostgreSQL")
            except Exception as e:
                logger.error(f"PostgreSQL init failed ({e}), using InMemory")
                from core.repositories.decision_repository import InMemoryDecisionRepository
                cls._decision_repository = InMemoryDecisionRepository()
                cls._repository_initialized = True
        else:
            logger.info("Decision repository: InMemory (no DATABASE_URL)")
            cls._repository_initialized = True

    @classmethod
    def reset(cls) -> None:
        """
        Reset all cached instances.

        Useful for testing or when configuration changes.
        """
        cls._vector_store = None
        cls._cache = None
        cls._embedding = None
        cls._decision_repository = None
        cls._message_queue = None
        cls._text_search = None
        cls._validation_pipeline = None
        cls._approval_manager = None
        cls._repository_initialized = False
        cls._initialized = False
        logger.info("Container reset")

    @classmethod
    async def close_all(cls) -> None:
        """
        Close all connections and cleanup resources.

        Should be called during application shutdown.
        """
        if cls._vector_store:
            await cls._vector_store.close()
        if cls._cache:
            await cls._cache.close()
        if cls._embedding:
            await cls._embedding.close()
        if cls._decision_repository and hasattr(cls._decision_repository, 'close'):
            await cls._decision_repository.close()
        if cls._message_queue:
            await cls._message_queue.close()
        if cls._text_search:
            await cls._text_search.close()
        cls.reset()
        logger.info("Container closed all connections")

    @classmethod
    def is_semantic_search_enabled(cls) -> bool:
        """Check if semantic search is enabled."""
        config = get_config()
        return config.enable_semantic_search

    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize all services.

        Creates collections, establishes connections, etc.
        Should be called during application startup.
        """
        if cls._initialized:
            return

        logger.info("Initializing container services...")

        # Initialize decision repository first (core service)
        await cls.initialize_repository()

        # Initialize vector store collection
        if cls.is_semantic_search_enabled():
            vector_store = cls.get_vector_store()
            embedding = cls.get_embedding()

            if not await vector_store.collection_exists():
                await vector_store.create_collection(
                    vector_size=embedding.dimensions
                )
                logger.info(f"Created vector collection with {embedding.dimensions} dimensions")

        # Initialize message queue if enabled
        if cls.is_rabbitmq_enabled():
            message_queue = cls.get_message_queue()
            if message_queue:
                try:
                    await message_queue.connect()
                    logger.info("Message queue connected")
                except Exception as e:
                    logger.warning(f"Message queue connection failed: {e}")

        # Initialize text search if enabled (no connection needed, lazy)
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

        cls._initialized = True
        logger.info("Container initialization complete")

    # =========================================================================
    # Validation Pipeline & Approval Manager
    # =========================================================================

    _validation_pipeline = None
    _approval_manager = None

    @classmethod
    def get_validation_pipeline(cls):
        """
        Get validation pipeline instance (singleton).

        The pipeline orchestrates the 3-gate validation process:
        - Gate 1: Deterministic validation
        - Gate 2: AI heuristic validation
        - Gate 3: Human approval workflow

        Returns:
            ValidationPipeline instance
        """
        if cls._validation_pipeline is None:
            from core.validation import create_pipeline
            cls._validation_pipeline = create_pipeline()
            logger.info("Validation pipeline created")
        return cls._validation_pipeline

    @classmethod
    def get_approval_manager(cls):
        """
        Get human approval manager instance (singleton).

        Manages the Gate 3 approval workflow:
        - Pending approvals tracking
        - Approval/rejection actions
        - Review comments

        Per MANTRA LAW §6: AI has ZERO authority for approval.

        Returns:
            HumanApprovalManager instance
        """
        if cls._approval_manager is None:
            from core.validation import create_approval_manager
            cls._approval_manager = create_approval_manager()
            logger.info("Approval manager created")
        return cls._approval_manager
