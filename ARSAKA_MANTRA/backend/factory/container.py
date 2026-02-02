"""
Dependency Injection Container - Facade for all factory modules.

This container provides a unified interface to all factory modules.
Each factory module handles a specific domain:
- CacheFactory: Cache adapters (Redis, Memory)
- SearchFactory: Vector store, embedding, text search
- StorageFactory: Repository, message queue
- ValidationFactory: Validation pipeline, approval manager

Usage:
    from factory.container import Container

    # Get instances (delegates to appropriate factory)
    cache = Container.get_cache()
    vector_store = Container.get_vector_store()
    embedding = Container.get_embedding()
    repository = Container.get_decision_repository()

    # Initialize all services
    await Container.initialize()

    # Cleanup on shutdown
    await Container.close_all()

    # Reset for testing
    Container.reset()
"""

import logging
from typing import Optional

from core.ports.vector_store import VectorStoreProtocol
from core.ports.cache import CacheProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.ports.message_queue import MessageQueueProtocol
from core.ports.text_search import TextSearchProtocol
from core.repositories.decision_repository import DecisionRepository

# Import factory modules
from factory.cache_factory import CacheFactory
from factory.search_factory import SearchFactory
from factory.storage_factory import StorageFactory
from factory.validation_factory import ValidationFactory

logger = logging.getLogger(__name__)


class Container:
    """
    Dependency injection container for MANTRA services.

    This is a facade that delegates to specialized factory modules.
    Each factory handles its own domain of adapters.

    Factory Modules:
    - CacheFactory: Cache adapters
    - SearchFactory: Vector store, embedding, text search
    - StorageFactory: Repository, message queue
    - ValidationFactory: Validation pipeline, approval manager
    """

    _initialized: bool = False

    # =========================================================================
    # Cache (delegates to CacheFactory)
    # =========================================================================

    @classmethod
    def get_cache(cls) -> CacheProtocol:
        """Get cache instance. See CacheFactory.get_cache()."""
        return CacheFactory.get_cache()

    # =========================================================================
    # Search Services (delegates to SearchFactory)
    # =========================================================================

    @classmethod
    def get_vector_store(cls) -> VectorStoreProtocol:
        """Get vector store instance. See SearchFactory.get_vector_store()."""
        return SearchFactory.get_vector_store()

    @classmethod
    def get_embedding(cls) -> EmbeddingProtocol:
        """Get embedding service instance. See SearchFactory.get_embedding()."""
        return SearchFactory.get_embedding()

    @classmethod
    def get_text_search(cls) -> Optional[TextSearchProtocol]:
        """Get text search instance. See SearchFactory.get_text_search()."""
        return SearchFactory.get_text_search()

    @classmethod
    def is_semantic_search_enabled(cls) -> bool:
        """Check if semantic search is enabled."""
        return SearchFactory.is_semantic_search_enabled()

    @classmethod
    def is_meilisearch_enabled(cls) -> bool:
        """Check if Meilisearch feature is enabled."""
        return SearchFactory.is_meilisearch_enabled()

    # =========================================================================
    # Storage Services (delegates to StorageFactory)
    # =========================================================================

    @classmethod
    def get_decision_repository(cls) -> DecisionRepository:
        """Get decision repository instance. See StorageFactory.get_decision_repository()."""
        return StorageFactory.get_decision_repository()

    @classmethod
    def get_message_queue(cls) -> Optional[MessageQueueProtocol]:
        """Get message queue instance. See StorageFactory.get_message_queue()."""
        return StorageFactory.get_message_queue()

    @classmethod
    def is_rabbitmq_enabled(cls) -> bool:
        """Check if RabbitMQ feature is enabled."""
        return StorageFactory.is_rabbitmq_enabled()

    @classmethod
    async def initialize_repository(cls) -> None:
        """Initialize decision repository. See StorageFactory.initialize_repository()."""
        await StorageFactory.initialize_repository()

    # =========================================================================
    # Validation Services (delegates to ValidationFactory)
    # =========================================================================

    @classmethod
    def get_validation_pipeline(cls):
        """Get validation pipeline instance. See ValidationFactory.get_validation_pipeline()."""
        return ValidationFactory.get_validation_pipeline()

    @classmethod
    def get_approval_manager(cls):
        """Get human approval manager instance. See ValidationFactory.get_approval_manager()."""
        return ValidationFactory.get_approval_manager()

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize all services.

        Creates collections, establishes connections, etc.
        Should be called during application startup.

        Initialization order:
        1. Storage (repository, message queue)
        2. Search (vector store, text search)
        """
        if cls._initialized:
            return

        logger.info("Initializing container services...")

        # Initialize storage first (core services)
        await StorageFactory.initialize()

        # Initialize search services
        await SearchFactory.initialize()

        cls._initialized = True
        logger.info("Container initialization complete")

    @classmethod
    async def close_all(cls) -> None:
        """
        Close all connections and cleanup resources.

        Should be called during application shutdown.
        """
        logger.info("Closing all container connections...")

        await CacheFactory.close()
        await SearchFactory.close_all()
        await StorageFactory.close_all()

        cls.reset()
        logger.info("Container closed all connections")

    @classmethod
    def reset(cls) -> None:
        """
        Reset all cached instances.

        Useful for testing or when configuration changes.
        """
        CacheFactory.reset()
        SearchFactory.reset()
        StorageFactory.reset()
        ValidationFactory.reset()
        cls._initialized = False
        logger.info("Container reset")

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if container is initialized."""
        return cls._initialized


# =============================================================================
# Backward Compatibility Exports
# =============================================================================

# These allow existing code to continue working without changes
__all__ = [
    "Container",
    "CacheFactory",
    "SearchFactory",
    "StorageFactory",
    "ValidationFactory",
]
