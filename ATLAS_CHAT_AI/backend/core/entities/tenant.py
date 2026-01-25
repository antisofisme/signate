"""
Tenant entities for multi-tenant configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class EmbeddingConfig:
    """Embedding provider configuration."""
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimensions: int = 1536


@dataclass
class RAGConfig:
    """RAG pipeline configuration."""
    enabled: bool = True  # Enable/disable RAG for this tenant
    strategy: str = "hybrid"  # "vanilla", "hybrid"
    reranker_enabled: bool = False
    reranker_provider: Optional[str] = None
    top_k: int = 5
    score_threshold: float = 0.3


@dataclass
class TenantFeatures:
    """Feature flags for tenant."""
    memory_extraction: bool = True
    temporal_memory: bool = True
    streaming: bool = True
    session_summarization: bool = True


@dataclass
class TenantConfig:
    """
    Tenant configuration entity.

    Contains all settings for a tenant including AI providers,
    limits, and feature flags.
    """
    id: str = ""
    name: str = ""
    description: Optional[str] = None

    # AI Configuration
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    embedding_config: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    rag_config: RAGConfig = field(default_factory=RAGConfig)

    # System Prompt
    system_prompt: str = "You are a helpful AI assistant."
    persona_name: str = "Assistant"

    # Limits
    max_context_tokens: int = 8000
    max_response_tokens: int = 1000
    max_messages_per_session: int = 100
    max_sessions_per_user: int = 50

    # Feature Flags
    features: TenantFeatures = field(default_factory=TenantFeatures)

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_llm_provider(self) -> str:
        """Get LLM provider name."""
        return self.llm_config.provider

    def get_embedding_provider(self) -> str:
        """Get embedding provider name."""
        return self.embedding_config.provider

    def is_streaming_enabled(self) -> bool:
        """Check if streaming is enabled for this tenant."""
        return self.features.streaming

    def is_memory_extraction_enabled(self) -> bool:
        """Check if memory extraction is enabled."""
        return self.features.memory_extraction


@dataclass
class KnowledgeSourceConfig:
    """
    Knowledge source configuration for a tenant.
    """
    id: str = ""
    tenant_id: str = ""

    # Source identification
    source_type: str = "database"  # "database", "api", "file"
    source_name: str = ""

    # Connection configuration
    connection_config: Dict[str, Any] = field(default_factory=dict)

    # Chunking configuration
    chunking_strategy: str = "fixed"  # "fixed", "semantic", "recursive"
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Sync configuration
    sync_interval: int = 60  # minutes, 0 = manual only
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    document_count: int = 0
    vector_count: int = 0

    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def needs_sync(self) -> bool:
        """Check if source needs synchronization."""
        if self.sync_interval == 0:
            return False  # Manual only
        if self.last_sync_at is None:
            return True

        minutes_since_sync = (datetime.utcnow() - self.last_sync_at).total_seconds() / 60
        return minutes_since_sync >= self.sync_interval
