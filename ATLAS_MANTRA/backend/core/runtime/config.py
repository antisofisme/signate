"""
Runtime Configuration

Environment-based configuration for ATLAS_MANTRA backend.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://mantra:mantra@localhost:5432/atlas_mantra"
    )

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))

    # API
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    )

    # Feature flags
    enable_docs: bool = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"
    enable_semantic_search: bool = os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() == "true"

    # New Service Feature Flags (disabled by default for gradual rollout)
    feature_meilisearch_enabled: bool = os.getenv("FEATURE_MEILISEARCH_ENABLED", "false").lower() == "true"
    feature_rabbitmq_enabled: bool = os.getenv("FEATURE_RABBITMQ_ENABLED", "false").lower() == "true"
    feature_redis_enhanced_cache: bool = os.getenv("FEATURE_REDIS_ENHANCED_CACHE", "true").lower() == "true"

    # AI Configuration
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    zai_api_key: str = os.getenv("ZAI_API_KEY", "")

    # AI Model settings
    ai_model: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    ai_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2000"))
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))

    # Vector Store Configuration
    vector_store: str = os.getenv("VECTOR_STORE", "memory")  # qdrant, memory
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "mantra_decisions")

    # Cache Configuration
    cache: str = os.getenv("CACHE", "memory")  # redis, memory
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

    # Embedding Configuration
    # Supported: openai, local, ollama, noop
    embedding_service: str = os.getenv("EMBEDDING_SERVICE", "noop")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # Local embedding (sentence-transformers)
    # Models: all-MiniLM-L6-v2 (384), all-mpnet-base-v2 (768)
    local_embedding_model: str = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Ollama embedding
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    # Meilisearch Configuration
    meilisearch_url: str = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
    meilisearch_api_key: str = os.getenv("MEILISEARCH_API_KEY", "")
    meilisearch_index_decisions: str = os.getenv("MEILISEARCH_INDEX_DECISIONS", "mantra_decisions")

    # RabbitMQ Configuration
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    rabbitmq_exchange: str = os.getenv("RABBITMQ_EXCHANGE", "mantra_events")
    rabbitmq_queue_validation: str = os.getenv("RABBITMQ_QUEUE_VALIDATION", "mantra_validation")
    rabbitmq_queue_sync: str = os.getenv("RABBITMQ_QUEUE_SYNC", "mantra_sync")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def get_ai_api_key(self, provider: Optional[str] = None) -> str:
        """Get API key for the specified or default provider."""
        p = provider or self.ai_provider
        keys = {
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
            "groq": self.groq_api_key,
            "openrouter": self.openrouter_api_key,
            "zai": self.zai_api_key,
        }
        return keys.get(p, "")


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration instance (singleton)."""
    global _config
    if _config is None:
        _config = Config()
    return _config
