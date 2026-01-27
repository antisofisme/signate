"""
Embedding Service Port - Abstract interface for embedding generation.

This port defines the contract for text embedding generation used in
semantic search. Implementations can use OpenAI, DeepSeek, Cohere,
or local models.

Usage:
    class OpenAIEmbedding(EmbeddingProtocol):
        async def embed(self, text):
            # OpenAI-specific implementation
            ...
"""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    vector: List[float]
    model: str
    tokens_used: int


class EmbeddingProtocol(ABC):
    """
    Abstract protocol for embedding generation.

    This interface allows swapping embedding providers
    without changing business logic. Supports:
    - OpenAI (primary)
    - DeepSeek
    - Cohere
    - Local models (e.g., sentence-transformers)
    - No-op (testing)
    """

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector (list of floats)
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times
        due to batching.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """
        Generate embedding with additional metadata.

        Args:
            text: Input text to embed

        Returns:
            EmbeddingResult with vector, model name, and token count
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """
        Get the embedding vector dimensions.

        Returns:
            Number of dimensions (e.g., 1536 for OpenAI text-embedding-3-small)
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the embedding model name.

        Returns:
            Model identifier string
        """
        pass

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """
        Get the maximum input tokens supported.

        Returns:
            Maximum token count (e.g., 8191 for OpenAI)
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
