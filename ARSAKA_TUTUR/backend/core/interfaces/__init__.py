"""
Core Interfaces

Abstract contracts that define the boundaries between layers.
All external dependencies must implement these interfaces.
"""

from .storage import VectorStore, MemoryStore
from .ai_providers import LLMProvider, EmbeddingProvider, Reranker
from .rag import RAGStrategy, DocumentChunker, QueryProcessor
from .memory import WorkingMemory, EpisodicMemory, SemanticMemory, TemporalMemory
from .extraction import FactExtractor, Summarizer
from .tenant import TenantRegistry, KnowledgeSource, SyncResult
from .auth import IAuthService, TokenPayload
from .rbac import IRBACService, Permission
from .audit import IAuditService
from .queue import JobQueue
from .cache import ICache

__all__ = [
    # Storage
    "VectorStore", "MemoryStore",
    # AI Providers
    "LLMProvider", "EmbeddingProvider", "Reranker",
    # RAG
    "RAGStrategy", "DocumentChunker", "QueryProcessor",
    # Memory
    "WorkingMemory", "EpisodicMemory", "SemanticMemory", "TemporalMemory",
    # Extraction
    "FactExtractor", "Summarizer",
    # Tenant
    "TenantRegistry", "KnowledgeSource", "SyncResult",
    # Auth
    "IAuthService", "TokenPayload",
    # RBAC
    "IRBACService", "Permission",
    # Audit
    "IAuditService",
    # Queue
    "JobQueue",
    # Cache
    "ICache",
]
