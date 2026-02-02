"""
Request schemas.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator


class ContextDocument(BaseModel):
    """Context document provided by caller (for mode=with_context)."""
    content: str = Field(..., description="Document content")
    type: Optional[str] = Field(None, description="Document type (e.g., 'decision', 'policy')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatRequest(BaseModel):
    """
    Chat message request.

    Supports two modes:
    - with_retrieval: TUTUR does RAG retrieval (default)
    - with_context: Caller provides context, TUTUR only handles AI + memory
    """
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: Optional[str] = Field(None, description="Existing session ID")

    # Mode selection
    mode: Literal["with_retrieval", "with_context"] = Field(
        "with_retrieval",
        description="Chat mode: 'with_retrieval' (TUTUR does RAG) or 'with_context' (caller provides context)"
    )

    # For mode=with_context: caller-provided context documents
    context_documents: Optional[List[ContextDocument]] = Field(
        None,
        description="Context documents (only used when mode=with_context)"
    )

    # Legacy context field (for page_context, etc.)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not just whitespace."""
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

    @property
    def page_context(self) -> Optional[str]:
        """Get page from context."""
        if self.context:
            return self.context.get("page")
        return None


class CreateSessionRequest(BaseModel):
    """Create session request."""
    title: Optional[str] = Field(None, max_length=500, description="Session title")


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    score_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity score")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()


class SearchSessionsRequest(BaseModel):
    """Search past sessions request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)


class FactDeleteRequest(BaseModel):
    """Fact deletion request."""
    reason: Optional[str] = Field(None, max_length=500)


class RedactMessageRequest(BaseModel):
    """Message redaction request."""
    reason: str = Field(..., min_length=1, max_length=500)
