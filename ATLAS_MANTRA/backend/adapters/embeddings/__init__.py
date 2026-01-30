"""
Embedding Adapters - Implementations for embedding generation.

Supported providers:
- OpenAI: Cloud-based, high quality (requires API key)
- Local: sentence-transformers, runs offline
- Ollama: Local LLM server, self-hosted
- NoOp: Testing only, returns zero vectors
"""

from .openai_adapter import OpenAIEmbedding
from .noop_adapter import NoOpEmbedding
from .local_adapter import LocalEmbedding
from .ollama_adapter import OllamaEmbedding

__all__ = [
    "OpenAIEmbedding",
    "NoOpEmbedding",
    "LocalEmbedding",
    "OllamaEmbedding",
]
