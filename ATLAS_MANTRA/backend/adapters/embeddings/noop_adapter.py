"""
NoOp Embedding Adapter - Mock implementation for testing.

This adapter generates deterministic pseudo-random embeddings
based on text hash. Useful for testing without API calls.

Usage:
    embedding = NoOpEmbedding()
    vector = await embedding.embed("decision statement")
"""

import hashlib
import logging
from typing import List

from core.ports.embedding_service import EmbeddingProtocol, EmbeddingResult

logger = logging.getLogger(__name__)


class NoOpEmbedding(EmbeddingProtocol):
    """
    No-op implementation of EmbeddingProtocol.

    Generates deterministic pseudo-random embeddings based on text hash.
    Same text always produces same embedding, enabling predictable tests.
    """

    def __init__(self, dimensions: int = 1536):
        """
        Initialize no-op embedding.

        Args:
            dimensions: Number of dimensions to generate
        """
        self._dimensions = dimensions
        self._model = "noop-embedding"
        logger.info(f"NoOp embedding initialized: dim={dimensions}")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic embedding from text hash.

        Uses SHA-256 hash expanded to fill dimensions.
        """
        # Create hash of text
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Expand hash to fill dimensions
        embedding = []
        idx = 0
        while len(embedding) < self._dimensions:
            # Use rolling hash to generate more values
            if idx >= len(hash_bytes):
                # Generate new hash based on previous
                hash_bytes = hashlib.sha256(hash_bytes).digest()
                idx = 0
            # Convert byte to normalized float [-1, 1]
            value = (hash_bytes[idx] / 255.0) * 2 - 1
            embedding.append(value)
            idx += 1

        return embedding

    async def embed(self, text: str) -> List[float]:
        """Generate deterministic embedding for a single text."""
        return self._generate_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for multiple texts."""
        return [self._generate_embedding(text) for text in texts]

    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with metadata."""
        return EmbeddingResult(
            vector=self._generate_embedding(text),
            model=self._model,
            tokens_used=len(text.split()),  # Approximate token count
        )

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
        """Get maximum input tokens (no real limit for noop)."""
        return 100000

    async def close(self) -> None:
        """No cleanup needed."""
        logger.info("NoOp embedding closed")
