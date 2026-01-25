"""
Response schemas.
"""

from typing import Optional, List, Dict, Any, Generic, TypeVar, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from .common import PaginationMeta, TokenUsage

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response."""
    success: Literal[True] = True
    data: T
    meta: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: Literal[False] = False
    error: ErrorDetail


# =========================================================================
# Chat Responses
# =========================================================================

class ChatResponseData(BaseModel):
    """Chat response data."""
    session_id: str = Field(..., description="Session ID")
    message_id: str = Field(..., description="Generated message ID")
    content: str = Field(..., description="Assistant response")
    retrieved_docs: List[str] = Field(default_factory=list, description="Retrieved document IDs")
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class ChatResponse(BaseModel):
    """Chat API response."""
    success: bool = True
    data: ChatResponseData


# =========================================================================
# Session Responses
# =========================================================================

class SessionData(BaseModel):
    """Session data."""
    id: str
    title: Optional[str] = None
    started_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Single session response."""
    success: bool = True
    data: SessionData


class SessionListResponse(BaseModel):
    """Session list response."""
    success: bool = True
    data: List[SessionData]
    meta: PaginationMeta


class SessionDeleteResponse(BaseModel):
    """Session delete response."""
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=lambda: {"deleted": True})


# =========================================================================
# Message Responses
# =========================================================================

class MessageData(BaseModel):
    """Message data."""
    id: str
    role: str
    content: str
    created_at: datetime
    retrieved_doc_ids: Optional[List[str]] = None
    is_redacted: bool = False

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Message list response."""
    success: bool = True
    data: List[MessageData]


class MessageResponse(BaseModel):
    """Single message response."""
    success: bool = True
    data: MessageData


# =========================================================================
# Session with Messages
# =========================================================================

class SessionWithMessagesData(BaseModel):
    """Session data with messages."""
    id: str
    title: Optional[str] = None
    started_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    messages: List[MessageData] = Field(default_factory=list)


class SessionWithMessagesResponse(BaseModel):
    """Session with messages response."""
    success: bool = True
    data: SessionWithMessagesData


# =========================================================================
# Health Response
# =========================================================================

# =========================================================================
# Search Responses
# =========================================================================

class SearchResultItem(BaseModel):
    """Single search result."""
    id: str = Field(..., description="Result ID")
    content: str = Field(..., description="Matched content")
    score: float = Field(..., description="Similarity score")
    document_id: Optional[str] = Field(None, description="Source document ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SearchResponse(BaseModel):
    """Search API response."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


# =========================================================================
# Health Response
# =========================================================================

class HealthChecks(BaseModel):
    """Health check results."""
    database: str = "unknown"
    qdrant: str = "unknown"
    redis: str = "unknown"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    checks: HealthChecks = Field(default_factory=HealthChecks)
