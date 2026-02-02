"""
Document entities for RAG and search.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class Document:
    """
    Document entity for knowledge base.
    """
    id: str = ""
    tenant_id: str = ""

    # Content
    content: str = ""
    title: Optional[str] = None

    # Metadata
    source: str = ""  # e.g., "decisions", "documentation"
    source_id: Optional[str] = None  # Original ID in source system
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Chunk:
    """
    Document chunk for embedding.
    """
    id: str = ""
    document_id: str = ""
    tenant_id: str = ""

    # Content
    content: str = ""
    chunk_index: int = 0

    # Embedding
    embedding: Optional[List[float]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Token count
    token_count: int = 0


@dataclass
class SearchResult:
    """
    Search result from vector store.
    """
    id: str
    score: float
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_id: Optional[str] = None

    def to_context_string(self) -> str:
        """Format as context string for LLM."""
        title = self.metadata.get("title", "")
        source = self.metadata.get("source", "")

        prefix = ""
        if title:
            prefix = f"[{title}]"
        elif source:
            prefix = f"[{source}]"

        if prefix:
            return f"{prefix}\n{self.content}"
        return self.content


@dataclass
class RankedDocument:
    """
    Document after reranking.
    """
    id: str
    content: str
    relevance_score: float
    original_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalContext:
    """
    Context for RAG retrieval.
    """
    tenant_id: str
    user_id: str
    top_k: int = 5
    filters: Dict[str, Any] = field(default_factory=dict)
    score_threshold: float = 0.0
    rerank: bool = False
    rerank_top_k: int = 3


@dataclass
class RetrievalResult:
    """
    Result from RAG retrieval.
    """
    results: List[SearchResult] = field(default_factory=list)
    query_embedding: Optional[List[float]] = None
    retrieval_time_ms: float = 0.0
    strategy_used: str = ""
    was_reranked: bool = False

    @property
    def has_results(self) -> bool:
        return len(self.results) > 0

    def get_context_string(self, max_results: int = 5) -> str:
        """Get formatted context string for LLM."""
        if not self.results:
            return ""

        context_parts = []
        for i, result in enumerate(self.results[:max_results], 1):
            context_parts.append(f"[Source {i}]\n{result.to_context_string()}")

        return "\n\n".join(context_parts)


@dataclass
class ProcessedQuery:
    """
    Processed query after preprocessing/rewriting.
    """
    original_query: str
    processed_query: str
    expanded_terms: List[str] = field(default_factory=list)
    detected_intent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def was_modified(self) -> bool:
        return self.original_query != self.processed_query
