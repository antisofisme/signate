"""
API Schemas - Request and response models.
"""

from .requests import (
    ChatRequest,
    CreateSessionRequest,
    SearchRequest,
)
from .responses import (
    ErrorDetail,
    SuccessResponse,
    ErrorResponse,
    ChatResponseData,
    ChatResponse,
    SessionData,
    SessionResponse,
    SessionListResponse,
    SessionDeleteResponse,
    MessageData,
    MessageListResponse,
    MessageResponse,
    SessionWithMessagesData,
    SessionWithMessagesResponse,
    SearchResultItem,
    SearchResponse,
    HealthChecks,
    HealthResponse,
)
from .common import PaginationMeta, TokenUsage

__all__ = [
    # Requests
    "ChatRequest",
    "CreateSessionRequest",
    "SearchRequest",
    # Responses
    "ErrorDetail",
    "SuccessResponse",
    "ErrorResponse",
    "ChatResponseData",
    "ChatResponse",
    "SessionData",
    "SessionResponse",
    "SessionListResponse",
    "SessionDeleteResponse",
    "MessageData",
    "MessageListResponse",
    "MessageResponse",
    "SessionWithMessagesData",
    "SessionWithMessagesResponse",
    "SearchResultItem",
    "SearchResponse",
    "HealthChecks",
    "HealthResponse",
    # Common
    "PaginationMeta",
    "TokenUsage",
]
