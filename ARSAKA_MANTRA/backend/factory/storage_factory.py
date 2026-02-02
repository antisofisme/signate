"""
Storage Factory - Creates storage and messaging adapter instances.

Handles:
- Decision Repository (PostgreSQL, Memory)
- Message Queue (RabbitMQ, Redis Streams, Memory)

Usage:
    from factory.storage_factory import StorageFactory

    repository = StorageFactory.get_decision_repository()
    message_queue = StorageFactory.get_message_queue()
"""

import logging
from typing import Optional

from core.runtime.config import get_config
from core.repositories.decision_repository import DecisionRepository
from core.ports.message_queue import MessageQueueProtocol
from factory.base import FactoryMixin

logger = logging.getLogger(__name__)


class StorageFactory(FactoryMixin):
    """Factory for creating storage and messaging instances."""

    _decision_repository: Optional[DecisionRepository] = None
    _message_queue: Optional[MessageQueueProtocol] = None
    _repository_initialized: bool = False

    # =========================================================================
    # Decision Repository
    # =========================================================================

    @classmethod
    def get_decision_repository(cls) -> DecisionRepository:
        """
        Get decision repository instance based on configuration.

        Supports:
        - postgresql: PostgreSQL database (production)
        - memory: In-memory store for testing

        Note: For PostgreSQL, call initialize_repository() first.

        Returns:
            DecisionRepository implementation
        """
        if cls._decision_repository is None:
            config = get_config()

            if config.database_url:
                # PostgreSQL - will be initialized in initialize_repository()
                # Return a temporary in-memory until initialized
                from core.repositories.decision_repository import InMemoryDecisionRepository
                cls._decision_repository = InMemoryDecisionRepository()
                cls.log_using("Repository", "InMemory", "(pending PostgreSQL initialization)")
            else:
                # No database configured - use in-memory
                from core.repositories.decision_repository import InMemoryDecisionRepository
                cls._decision_repository = InMemoryDecisionRepository()
                cls._repository_initialized = True
                cls.log_using("Repository", "InMemory")

        return cls._decision_repository

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
                cls.log_using("Repository", "PostgreSQL")
            except Exception as e:
                logger.error(f"PostgreSQL init failed ({e}), using InMemory")
                from core.repositories.decision_repository import InMemoryDecisionRepository
                cls._decision_repository = InMemoryDecisionRepository()
                cls._repository_initialized = True
        else:
            cls.log_using("Repository", "InMemory", "(no DATABASE_URL)")
            cls._repository_initialized = True

    @classmethod
    def is_repository_initialized(cls) -> bool:
        """Check if repository is initialized."""
        return cls._repository_initialized

    # =========================================================================
    # Message Queue
    # =========================================================================

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
            cls.log_disabled("RabbitMQ")
            return None

        if cls._message_queue is None:
            if config.rabbitmq_url and config.rabbitmq_url.startswith("amqp"):
                cls._message_queue = cls._create_rabbitmq(config)
            elif config.redis_url:
                cls._message_queue = cls._create_redis_streams(config)
            else:
                cls._message_queue = cls._create_memory_queue()

        return cls._message_queue

    @classmethod
    def _create_rabbitmq(cls, config) -> MessageQueueProtocol:
        """Create RabbitMQ adapter instance."""
        try:
            from adapters.message_queues.rabbitmq_adapter import RabbitMQAdapter

            adapter = RabbitMQAdapter(
                url=config.rabbitmq_url,
                exchange_name=config.rabbitmq_exchange,
            )
            cls.log_using("MessageQueue", "RabbitMQ")
            return adapter
        except ImportError:
            cls.log_fallback("MessageQueue", "aio-pika not installed", "memory")
            return cls._create_memory_queue()

    @classmethod
    def _create_redis_streams(cls, config) -> MessageQueueProtocol:
        """Create Redis Streams adapter instance."""
        try:
            from adapters.message_queues.redis_streams_adapter import RedisStreamsAdapter

            adapter = RedisStreamsAdapter(url=config.redis_url)
            cls.log_using("MessageQueue", "RedisStreams", "(fallback)")
            return adapter
        except ImportError:
            cls.log_fallback("MessageQueue", "redis not installed", "memory")
            return cls._create_memory_queue()

    @classmethod
    def _create_memory_queue(cls) -> MessageQueueProtocol:
        """Create in-memory queue instance."""
        from adapters.message_queues.memory_adapter import MemoryQueueAdapter

        adapter = MemoryQueueAdapter()
        cls.log_using("MessageQueue", "InMemory")
        return adapter

    @classmethod
    def is_rabbitmq_enabled(cls) -> bool:
        """Check if RabbitMQ feature is enabled."""
        return get_config().feature_rabbitmq_enabled

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @classmethod
    def reset(cls) -> None:
        """Reset all cached instances."""
        cls._decision_repository = None
        cls._message_queue = None
        cls._repository_initialized = False

    @classmethod
    async def close_all(cls) -> None:
        """Close all connections."""
        if cls._decision_repository and hasattr(cls._decision_repository, 'close'):
            await cls._decision_repository.close()
        if cls._message_queue:
            await cls._message_queue.close()
        cls.reset()

    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize storage services.

        - Initializes decision repository
        - Connects to message queue if enabled
        """
        # Initialize repository
        await cls.initialize_repository()

        # Connect message queue if enabled
        if cls.is_rabbitmq_enabled():
            message_queue = cls.get_message_queue()
            if message_queue:
                try:
                    await message_queue.connect()
                    logger.info("Message queue connected")
                except Exception as e:
                    logger.warning(f"Message queue connection failed: {e}")
