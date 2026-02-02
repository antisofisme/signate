"""
OpenAI Embedding Adapter - Implementation using OpenAI's embedding API.

OpenAI provides state-of-the-art text embeddings with models like:
- text-embedding-3-small (1536 dimensions, cost-effective)
- text-embedding-3-large (3072 dimensions, highest quality)
- text-embedding-ada-002 (1536 dimensions, legacy)

Requirements:
    pip install openai

Usage:
    embedding = OpenAIEmbedding(api_key="sk-...")
    vector = await embedding.embed("decision statement")
"""

import logging
from typing import List

from openai import AsyncOpenAI

from core.ports.embedding_service import EmbeddingProtocol, EmbeddingResult

logger = logging.getLogger(__name__)


class OpenAIEmbedding(EmbeddingProtocol):
    """
    OpenAI implementation of EmbeddingProtocol.

    Provides high-quality text embeddings using OpenAI's API.
    Supports batching for efficiency.
    """

    # Model configurations
    MODEL_CONFIGS = {
        "text-embedding-3-small": {
            "dimensions": 1536,
            "max_tokens": 8191,
        },
        "text-embedding-3-large": {
            "dimensions": 3072,
            "max_tokens": 8191,
        },
        "text-embedding-ada-002": {
            "dimensions": 1536,
            "max_tokens": 8191,
        },
    }

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = None,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Embedding model name
            dimensions: Override dimensions (for variable-dimension models)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._config = self.MODEL_CONFIGS.get(model, self.MODEL_CONFIGS["text-embedding-3-small"])
        self._dimensions = dimensions or self._config["dimensions"]
        logger.info(f"OpenAI embedding initialized: model={model}, dim={self._dimensions}")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = await self.client.embeddings.create(
                model=self._model,
                input=text,
                dimensions=self._dimensions if self._model.startswith("text-embedding-3") else None,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        try:
            # OpenAI supports batch embedding
            response = await self.client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions if self._model.startswith("text-embedding-3") else None,
            )

            # Sort by index to ensure order matches input
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise

    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with additional metadata."""
        try:
            response = await self.client.embeddings.create(
                model=self._model,
                input=text,
                dimensions=self._dimensions if self._model.startswith("text-embedding-3") else None,
            )
            return EmbeddingResult(
                vector=response.data[0].embedding,
                model=self._model,
                tokens_used=response.usage.total_tokens,
            )
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model

    @property
    def max_tokens(self) -> int:
        """Get maximum input tokens."""
        return self._config["max_tokens"]

    async def close(self) -> None:
        """Close the client (OpenAI client doesn't require explicit cleanup)."""
        await self.client.close()
        logger.info("OpenAI embedding client closed")
