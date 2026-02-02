"""
Domain Entities

Pure data classes representing the core business concepts.
"""

from .message import ChatMessage, Role, Message, GenerationResult
from .session import ChatSession, SessionSummary
from .memory import UserFact, FactType, TimeSummary, ExtractedFact
from .document import Document, Chunk, SearchResult, RankedDocument, RetrievalResult, RetrievalContext, ProcessedQuery
from .tenant import TenantConfig, LLMConfig, EmbeddingConfig, RAGConfig, TenantFeatures, KnowledgeSourceConfig
from .user import User, UserProfile, APIKeyPayload
from .context import RequestContext, AssembledContext
from .audit import AuditEntry, AuditLog

__all__ = [
    # Message
    "ChatMessage", "Role", "Message", "GenerationResult",
    # Session
    "ChatSession", "SessionSummary",
    # Memory
    "UserFact", "FactType", "TimeSummary", "ExtractedFact",
    # Document
    "Document", "Chunk", "SearchResult", "RankedDocument",
    "RetrievalResult", "RetrievalContext", "ProcessedQuery",
    # Tenant
    "TenantConfig", "LLMConfig", "EmbeddingConfig", "RAGConfig",
    "TenantFeatures", "KnowledgeSourceConfig",
    # User
    "User", "UserProfile", "APIKeyPayload",
    # Context
    "RequestContext", "AssembledContext",
    # Audit
    "AuditEntry", "AuditLog",
]
