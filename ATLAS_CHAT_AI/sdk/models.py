"""
SDK Data Models

Pydantic models for SDK responses.
"""

from typing import Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TokenUsage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ChatResponse:
    """Response from chat endpoint."""
    session_id: str
    message_id: str
    content: str
    retrieved_docs: List[str] = field(default_factory=list)
    token_usage: Optional[TokenUsage] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ChatResponse":
        """Create from API response dict."""
        token_data = data.get("token_usage", {})
        return cls(
            session_id=data.get("session_id", ""),
            message_id=data.get("message_id", ""),
            content=data.get("content", ""),
            retrieved_docs=data.get("retrieved_docs", []),
            token_usage=TokenUsage(
                prompt_tokens=token_data.get("prompt_tokens", 0),
                completion_tokens=token_data.get("completion_tokens", 0),
            ) if token_data else None,
        )


@dataclass
class SearchResult:
    """A single search result."""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SearchResult":
        """Create from API response dict."""
        return cls(
            document_id=data.get("document_id", ""),
            chunk_id=data.get("chunk_id", ""),
            content=data.get("content", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchResponse:
    """Response from search endpoint."""
    results: List[SearchResult]
    total: int
    query: str

    @classmethod
    def from_dict(cls, data: dict) -> "SearchResponse":
        """Create from API response dict."""
        return cls(
            results=[SearchResult.from_dict(r) for r in data.get("results", [])],
            total=data.get("total", 0),
            query=data.get("query", ""),
        )


@dataclass
class Message:
    """A chat message."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from API response dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            role=data.get("role", ""),
            content=data.get("content", ""),
            created_at=created_at,
        )


@dataclass
class Session:
    """A chat session."""
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    message_count: int = 0
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from API response dict."""
        started_at = data.get("started_at")
        updated_at = data.get("updated_at")

        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            title=data.get("title"),
            summary=data.get("summary"),
            message_count=data.get("message_count", 0),
            started_at=started_at,
            updated_at=updated_at,
        )


@dataclass
class UserFact:
    """A user fact from memory."""
    id: str
    fact_type: str
    content: str
    confidence: float
    is_active: bool = True
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UserFact":
        """Create from API response dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            fact_type=data.get("fact_type", ""),
            content=data.get("content", ""),
            confidence=data.get("confidence", 0.0),
            is_active=data.get("is_active", True),
            created_at=created_at,
        )


class APIError(Exception):
    """API error exception."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(f"{code}: {message}")

    @classmethod
    def from_response(cls, response_data: dict, status_code: int) -> "APIError":
        """Create from API error response."""
        error = response_data.get("error", {})
        return cls(
            code=error.get("code", "UNKNOWN_ERROR"),
            message=error.get("message", "Unknown error occurred"),
            status_code=status_code,
            details=error.get("details", {}),
        )
