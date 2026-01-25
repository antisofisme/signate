"""
AI provider interfaces for LLM and embedding.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, AsyncIterator

from ..entities import Message, GenerationResult, RankedDocument


class EmbeddingProvider(ABC):
    """
    Interface for embedding generation.

    Implementations: OpenAIEmbeddingAdapter
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Embed single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        pass


class LLMProvider(ABC):
    """
    Interface for LLM completion.

    Implementations: OpenAIAdapter, DeepSeekAdapter, GroqAdapter
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name (openai, deepseek, groq)."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stop: Optional[List[str]] = None
    ) -> GenerationResult:
        """
        Generate completion.

        Args:
            messages: List of Message (role, content)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            stop: Stop sequences

        Returns:
            GenerationResult with content and token counts
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """
        Stream completion token by token.

        Args:
            messages: List of Message
            temperature: Sampling temperature
            max_tokens: Max tokens

        Yields:
            Token strings as they're generated
        """
        pass


class Reranker(ABC):
    """
    Interface for reranking search results.

    Implementations: CohereReranker (optional)
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get reranker model name."""
        pass

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[RankedDocument]:
        """
        Rerank documents by relevance to query.

        Args:
            query: Search query
            documents: List of document contents
            top_k: Number of documents to return

        Returns:
            List of RankedDocument ordered by relevance
        """
        pass
