"""
Embedding Bridge - Connects retrieval system to embedding services.

This module bridges the smart_index EmbeddingProvider interface
to the core.ports.embedding_service.EmbeddingProtocol.

This allows the retrieval system to use any configured embedding provider:
- OpenAI
- Local (sentence-transformers)
- Ollama
- NoOp (testing)

Usage:
    from factory.container import Container
    from core.retrieval.embedding_bridge import create_embedding_provider

    # Get embedding provider that wraps the configured service
    provider = create_embedding_provider()

    # Use in smart index
    index = DecisionIndex(embedding_provider=provider)
"""

import asyncio
from typing import List, Optional

from .smart_index import EmbeddingProvider
from core.ports.embedding_service import EmbeddingProtocol


class EmbeddingServiceBridge(EmbeddingProvider):
    """
    Bridges EmbeddingProtocol (async) to EmbeddingProvider (sync).

    The smart_index uses synchronous EmbeddingProvider interface,
    while our adapters use async EmbeddingProtocol. This bridge
    handles the conversion.
    """

    def __init__(self, embedding_service: EmbeddingProtocol):
        """
        Initialize bridge with an EmbeddingProtocol implementation.

        Args:
            embedding_service: Any EmbeddingProtocol implementation
        """
        self._service = embedding_service
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for sync-to-async calls."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create one
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            return self._loop

    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # Already in async context, need to use run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=30)
        except RuntimeError:
            # No running loop, use asyncio.run
            return asyncio.run(coro)

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text (sync wrapper)."""
        return self._run_async(self._service.embed(text))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (sync wrapper)."""
        return self._run_async(self._service.embed_batch(texts))

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._service.dimensions


class AsyncEmbeddingProvider(EmbeddingProvider):
    """
    Async-native embedding provider for use in async contexts.

    Use this when you need the smart_index in async code and
    want to avoid sync-to-async overhead.
    """

    def __init__(self, embedding_service: EmbeddingProtocol):
        """Initialize with an EmbeddingProtocol implementation."""
        self._service = embedding_service
        self._cached_dimension: Optional[int] = None

    async def embed_async(self, text: str) -> List[float]:
        """Generate embedding asynchronously."""
        return await self._service.embed(text)

    async def embed_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts asynchronously."""
        return await self._service.embed_batch(texts)

    # Sync methods (required by EmbeddingProvider interface)
    def embed(self, text: str) -> List[float]:
        """Sync embed - runs async method."""
        return asyncio.run(self._service.embed(text))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Sync batch embed - runs async method."""
        return asyncio.run(self._service.embed_batch(texts))

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._cached_dimension is None:
            self._cached_dimension = self._service.dimensions
        return self._cached_dimension


def create_embedding_provider() -> EmbeddingProvider:
    """
    Create an EmbeddingProvider using the configured embedding service.

    This function uses the Container to get the configured embedding
    service and wraps it in an EmbeddingProvider interface.

    Returns:
        EmbeddingProvider instance
    """
    from factory.container import Container

    embedding_service = Container.get_embedding()
    return EmbeddingServiceBridge(embedding_service)


def create_async_embedding_provider() -> AsyncEmbeddingProvider:
    """
    Create an async-optimized EmbeddingProvider.

    Use this in async contexts for better performance.

    Returns:
        AsyncEmbeddingProvider instance
    """
    from factory.container import Container

    embedding_service = Container.get_embedding()
    return AsyncEmbeddingProvider(embedding_service)


__all__ = [
    "EmbeddingServiceBridge",
    "AsyncEmbeddingProvider",
    "create_embedding_provider",
    "create_async_embedding_provider",
]
