"""
Ollama Embedding Adapter - Implementation using local Ollama server.

Ollama provides easy-to-run local LLMs with embedding support.
Great for:
- Self-hosted deployments
- Privacy requirements
- Cost-free embeddings
- Models like nomic-embed-text, mxbai-embed-large

Requirements:
    - Ollama installed and running (https://ollama.ai)
    - An embedding model pulled: ollama pull nomic-embed-text

Usage:
    embedding = OllamaEmbedding(base_url="http://localhost:11434")
    vector = await embedding.embed("decision statement")
"""

import logging
import httpx
from typing import List, Optional

from core.ports.embedding_service import EmbeddingProtocol, EmbeddingResult

logger = logging.getLogger(__name__)


class OllamaEmbedding(EmbeddingProtocol):
    """
    Ollama embedding using local Ollama server.

    Supports various embedding models:
    - nomic-embed-text: 768 dims, good quality, fast
    - mxbai-embed-large: 1024 dims, high quality
    - all-minilm: 384 dims, fast (if available)
    """

    # Model configurations
    MODEL_CONFIGS = {
        "nomic-embed-text": {
            "dimensions": 768,
            "max_tokens": 8192,
            "description": "Fast, good quality embedding",
        },
        "mxbai-embed-large": {
            "dimensions": 1024,
            "max_tokens": 512,
            "description": "High quality, larger model",
        },
        "all-minilm": {
            "dimensions": 384,
            "max_tokens": 256,
            "description": "Small and fast",
        },
        "snowflake-arctic-embed": {
            "dimensions": 1024,
            "max_tokens": 512,
            "description": "Snowflake Arctic embedding",
        },
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 30.0,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            model: Embedding model name
            timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._config = self.MODEL_CONFIGS.get(
            model,
            {"dimensions": 768, "max_tokens": 512}
        )
        self._client = httpx.AsyncClient(timeout=timeout)
        self._verified_dimensions: Optional[int] = None
        logger.info(f"Ollama embedding initialized: model={model}, url={base_url}")

    async def _call_embed(self, text: str) -> List[float]:
        """Call Ollama embed API."""
        url = f"{self._base_url}/api/embeddings"
        payload = {
            "model": self._model,
            "prompt": text,
        }

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])

            # Update verified dimensions on first successful call
            if self._verified_dimensions is None and embedding:
                self._verified_dimensions = len(embedding)
                logger.info(f"Ollama model {self._model} has {self._verified_dimensions} dimensions")

            return embedding
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return await self._call_embed(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Ollama API doesn't support native batching,
        so we make sequential requests.
        """
        if not texts:
            return []

        results = []
        for text in texts:
            embedding = await self._call_embed(text)
            results.append(embedding)
        return results

    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with additional metadata."""
        vector = await self.embed(text)
        # Estimate tokens (rough approximation)
        tokens_used = len(text.split()) + len(text) // 4
        return EmbeddingResult(
            vector=vector,
            model=self._model,
            tokens_used=min(tokens_used, self._config["max_tokens"]),
        )

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        if self._verified_dimensions is not None:
            return self._verified_dimensions
        return self._config["dimensions"]

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self._model

    @property
    def max_tokens(self) -> int:
        """Get maximum input tokens."""
        return self._config["max_tokens"]

    async def health_check(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("Ollama embedding client closed")


__all__ = ["OllamaEmbedding"]
