"""
Message Queue Adapters - Implementations for async message processing.

Available adapters:
- RabbitMQAdapter: RabbitMQ implementation (primary) - requires aio-pika
- RedisStreamsAdapter: Redis Streams implementation (fallback)
- MemoryQueueAdapter: In-memory implementation (testing)

Note: Imports are lazy to avoid requiring all dependencies.
"""


def __getattr__(name):
    """Lazy import adapters to avoid requiring all dependencies."""
    if name == "RabbitMQAdapter":
        from .rabbitmq_adapter import RabbitMQAdapter
        return RabbitMQAdapter
    elif name == "RedisStreamsAdapter":
        from .redis_streams_adapter import RedisStreamsAdapter
        return RedisStreamsAdapter
    elif name == "MemoryQueueAdapter":
        from .memory_adapter import MemoryQueueAdapter
        return MemoryQueueAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "RabbitMQAdapter",
    "RedisStreamsAdapter",
    "MemoryQueueAdapter",
]
