"""
Embedding Adapters - Implementations for embedding generation.
"""

from .openai_adapter import OpenAIEmbedding
from .noop_adapter import NoOpEmbedding

__all__ = [
    "OpenAIEmbedding",
    "NoOpEmbedding",
]
