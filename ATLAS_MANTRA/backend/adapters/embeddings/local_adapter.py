"""
Local Embedding Adapter - Implementation using sentence-transformers.

Provides high-quality embeddings running locally without API calls.
Great for:
- Privacy-sensitive deployments
- Offline usage
- Cost reduction
- Lower latency

Models supported:
- all-MiniLM-L6-v2: 384 dims, fast, good quality
- all-mpnet-base-v2: 768 dims, slower, better quality
- multi-qa-mpnet-base-dot-v1: 768 dims, optimized for QA

Requirements:
    pip install sentence-transformers

Usage:
    embedding = LocalEmbedding(model_name="all-MiniLM-L6-v2")
    vector = await embedding.embed("decision statement")
"""

import logging
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor

from core.ports.embedding_service import EmbeddingProtocol, EmbeddingResult

logger = logging.getLogger(__name__)


class LocalEmbedding(EmbeddingProtocol):
    """
    Local embedding using sentence-transformers.

    Runs entirely on local hardware (CPU or GPU).
    No API calls, no costs, works offline.
    """

    # Model configurations
    MODEL_CONFIGS = {
        "all-MiniLM-L6-v2": {
            "dimensions": 384,
            "max_tokens": 256,
            "description": "Fast, good quality, recommended for most uses",
        },
        "all-mpnet-base-v2": {
            "dimensions": 768,
            "max_tokens": 384,
            "description": "Higher quality, slower",
        },
        "multi-qa-mpnet-base-dot-v1": {
            "dimensions": 768,
            "max_tokens": 512,
            "description": "Optimized for question-answering",
        },
        "paraphrase-MiniLM-L6-v2": {
            "dimensions": 384,
            "max_tokens": 128,
            "description": "Good for paraphrase detection",
        },
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None,
        max_workers: int = 2,
    ):
        """
        Initialize local embedding model.

        Args:
            model_name: Model name from sentence-transformers hub
            device: 'cpu', 'cuda', or None for auto-detect
            max_workers: Thread pool size for async operations
        """
        self._model_name = model_name
        self._device = device
        self._model = None
        self._config = self.MODEL_CONFIGS.get(
            model_name,
            {"dimensions": 384, "max_tokens": 256}
        )
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"Local embedding initialized: model={model_name}")

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self._model_name,
                    device=self._device
                )
                # Verify dimensions
                test_emb = self._model.encode(["test"])
                actual_dim = len(test_emb[0])
                if actual_dim != self._config["dimensions"]:
                    self._config["dimensions"] = actual_dim
                    logger.warning(f"Model dimensions differ from config: {actual_dim}")
                logger.info(f"Loaded model: {self._model_name} ({actual_dim} dims)")
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. Install with: "
                    "pip install sentence-transformers"
                )

    def _embed_sync(self, text: str) -> List[float]:
        """Synchronous embedding (for thread pool)."""
        self._load_model()
        embedding = self._model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()

    def _embed_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous batch embedding (for thread pool)."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._embed_sync, text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._embed_batch_sync, texts)

    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with additional metadata."""
        vector = await self.embed(text)
        # Estimate tokens (rough approximation)
        tokens_used = len(text.split()) + len(text) // 4
        return EmbeddingResult(
            vector=vector,
            model=self._model_name,
            tokens_used=min(tokens_used, self._config["max_tokens"]),
        )

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._config["dimensions"]

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model_name

    @property
    def max_tokens(self) -> int:
        """Get maximum input tokens."""
        return self._config["max_tokens"]

    async def close(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=False)
        self._model = None
        logger.info("Local embedding resources released")


__all__ = ["LocalEmbedding"]
