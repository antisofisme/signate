"""
Embedding Domain Entity - Represents a decision's vector embedding.

This entity stores the embedding vector for a decision, enabling
semantic search capabilities. Embeddings are immutable once created.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class EmbeddingStatus(str, Enum):
    """Status of an embedding."""
    PENDING = "PENDING"       # Queued for generation
    PROCESSING = "PROCESSING" # Currently being generated
    READY = "READY"           # Successfully generated
    FAILED = "FAILED"         # Generation failed
    STALE = "STALE"          # Decision was updated, needs re-embedding


@dataclass(frozen=True)
class Embedding:
    """
    Immutable embedding entity for a decision.

    The embedding captures the semantic meaning of a decision's
    statement and rationale, enabling similarity search.

    Attributes:
        decision_id: The decision this embedding belongs to
        vector: The embedding vector (e.g., 1536 dimensions for OpenAI)
        model: The embedding model used (e.g., 'text-embedding-3-small')
        text_hash: SHA-256 hash of the embedded text for staleness detection
        created_at: When the embedding was generated
        dimensions: Vector dimension count
        status: Current embedding status
    """
    decision_id: str
    vector: List[float]
    model: str
    text_hash: str
    created_at: datetime
    dimensions: int = field(default=1536)
    status: EmbeddingStatus = field(default=EmbeddingStatus.READY)

    def is_stale(self, current_text_hash: str) -> bool:
        """Check if embedding is stale compared to current text."""
        return self.text_hash != current_text_hash

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "decision_id": self.decision_id,
            "vector": self.vector,
            "model": self.model,
            "text_hash": self.text_hash,
            "created_at": self.created_at.isoformat(),
            "dimensions": self.dimensions,
            "status": self.status.value,
        }


@dataclass
class EmbeddingRequest:
    """
    Request to generate an embedding.

    This is used to queue embedding generation for a decision.
    """
    decision_id: str
    text: str
    priority: int = 0  # Higher = more urgent
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmbeddingStats:
    """Statistics about the embedding collection."""
    total_embeddings: int
    ready_count: int
    pending_count: int
    failed_count: int
    stale_count: int
    avg_dimensions: float
    models_used: List[str]
    last_updated: Optional[datetime]


def create_embedding_text(statement: str, rationale: str, tags: List[str] = None) -> str:
    """
    Create the text to embed for a decision.

    Combines statement and rationale with formatting that works
    well for semantic search.

    Args:
        statement: Decision statement
        rationale: Decision rationale
        tags: Optional tags for context

    Returns:
        Formatted text for embedding
    """
    parts = [
        f"Decision: {statement}",
        f"Rationale: {rationale}",
    ]
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")

    return "\n".join(parts)


def compute_text_hash(text: str) -> str:
    """
    Compute SHA-256 hash of text for staleness detection.

    Args:
        text: Text to hash

    Returns:
        Hex-encoded SHA-256 hash
    """
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
