"""
MANTRA Adapters - Clean Architecture Implementations

This module contains concrete implementations of the port interfaces.
Adapters connect the domain layer to external infrastructure:
- Vector stores (Qdrant, Memory)
- Caches (Redis, Memory)
- Embedding services (OpenAI, NoOp)

Following the Adapter pattern, these implementations can be swapped
without changing business logic.
"""

from .vector_stores import QdrantVectorStore, MemoryVectorStore
from .caches import RedisCache, MemoryCache
from .embeddings import OpenAIEmbedding, NoOpEmbedding

__all__ = [
    # Vector Stores
    "QdrantVectorStore",
    "MemoryVectorStore",
    # Caches
    "RedisCache",
    "MemoryCache",
    # Embeddings
    "OpenAIEmbedding",
    "NoOpEmbedding",
]
