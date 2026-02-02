"""
Runtime Configuration

Environment-based configuration for ARSAKA_MANTRA backend.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Database (REQUIRED - no default credentials)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://mantra@localhost:5432/arsaka_mantra"  # No password in default
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

    # Service Feature Flags - ENABLED BY DEFAULT for production-ready stack
    feature_meilisearch_enabled: bool = os.getenv("FEATURE_MEILISEARCH_ENABLED", "true").lower() == "true"
    feature_rabbitmq_enabled: bool = os.getenv("FEATURE_RABBITMQ_ENABLED", "false").lower() == "true"
    feature_redis_enhanced_cache: bool = os.getenv("FEATURE_REDIS_ENHANCED_CACHE", "true").lower() == "true"

    # Retrieval Optimization (Multi-Agent Tuned - Jan 2025)
    retrieval_profile: str = os.getenv("RETRIEVAL_PROFILE", "max_accuracy")
    fusion_method: str = os.getenv("FUSION_METHOD", "combsum_normalized")
    retrieval_vector_weight: float = float(os.getenv("RETRIEVAL_VECTOR_WEIGHT", "0.03"))
    retrieval_keyword_weight: float = float(os.getenv("RETRIEVAL_KEYWORD_WEIGHT", "0.97"))
    retrieval_min_score: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.37"))
    retrieval_max_results: int = int(os.getenv("RETRIEVAL_MAX_RESULTS", "10"))

    # Query Embedding Cache
    query_embedding_cache_enabled: bool = os.getenv("QUERY_EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
    query_embedding_cache_size: int = int(os.getenv("QUERY_EMBEDDING_CACHE_SIZE", "1000"))
    query_embedding_cache_ttl: int = int(os.getenv("QUERY_EMBEDDING_CACHE_TTL", "3600"))

    # Cache Warming
    cache_warming_enabled: bool = os.getenv("CACHE_WARMING_ENABLED", "true").lower() == "true"
    cache_warming_hot_decisions: int = int(os.getenv("CACHE_WARMING_HOT_DECISIONS", "100"))

    # ARSAKA_TUTUR Integration
    # MANTRA delegates all AI functionality to ARSAKA_TUTUR service
    arsaka_tutur_url: str = os.getenv("ARSAKA_TUTUR_URL", "http://localhost:8010")
    arsaka_tutur_api_key: str = os.getenv("ARSAKA_TUTUR_API_KEY", "")
    arsaka_tutur_timeout: float = float(os.getenv("ARSAKA_TUTUR_TIMEOUT", "30"))

    # Vector Store Configuration - Default to qdrant for production
    vector_store: str = os.getenv("VECTOR_STORE", "qdrant")  # qdrant, memory
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "mantra_decisions")

    # Cache Configuration - Default to redis for production
    cache: str = os.getenv("CACHE", "redis")  # redis, memory
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

    # Embedding Configuration - Default to local for CPU-based embeddings
    # Supported: openai, local, ollama, noop
    # Use "local" for development (free, fast, works offline)
    # Use "openai" for production (better quality, requires API key)
    embedding_service: str = os.getenv("EMBEDDING_SERVICE", "local")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # OpenAI API Key (used for embedding if embedding_service=openai)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

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

    # RabbitMQ Configuration (no default credentials)
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://localhost:5672/")
    rabbitmq_exchange: str = os.getenv("RABBITMQ_EXCHANGE", "mantra_events")
    rabbitmq_queue_validation: str = os.getenv("RABBITMQ_QUEUE_VALIDATION", "mantra_validation")
    rabbitmq_queue_sync: str = os.getenv("RABBITMQ_QUEUE_SYNC", "mantra_sync")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration instance (singleton)."""
    global _config
    if _config is None:
        _config = Config()
    return _config
