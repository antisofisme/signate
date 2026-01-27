"""
MANTRA Ports (Interfaces) - Clean Architecture

This module defines abstract interfaces (ports) for external dependencies.
Following the Dependency Inversion Principle, the domain layer depends on
these abstractions, not concrete implementations.

Available Ports:
- VectorStoreProtocol: Interface for vector database operations
- CacheProtocol: Interface for caching operations
- EmbeddingProtocol: Interface for embedding generation
"""

from .vector_store import VectorStoreProtocol
from .cache import CacheProtocol
from .embedding_service import EmbeddingProtocol

__all__ = [
    "VectorStoreProtocol",
    "CacheProtocol",
    "EmbeddingProtocol",
]
