# CHAT-L2-SPEC-004: Configuration

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-004, CHAT-LAW-005

---

## Overview

Environment variables and configuration specification for ARSAKA_TUTUR.

---

## Environment Variables

### Core Settings

```bash
# Application
APP_NAME=atlas-chat-ai
APP_ENV=development                    # development | staging | production
APP_DEBUG=true                         # Enable debug mode
APP_LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR
APP_HOST=0.0.0.0
APP_PORT=8003

# API
API_PREFIX=/api/v1
API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS=60             # Requests per minute
```

### Database

```bash
# PostgreSQL
DATABASE_URL=postgresql://chat_user:password@localhost:5432/atlas_chat
DATABASE_POOL_SIZE=20
DATABASE_POOL_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false                    # Log SQL queries
```

### Vector Store

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=                        # Optional for auth
QDRANT_GRPC_PORT=6334                  # For gRPC (optional)
QDRANT_TIMEOUT=30                      # Request timeout in seconds
```

### Cache

```bash
# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_PREFIX=chat:
REDIS_TTL_DEFAULT=3600                 # 1 hour default TTL
```

### AI Providers

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=                         # Optional

# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-...

# Groq
GROQ_API_KEY=gsk_...

# Cohere (for reranking)
COHERE_API_KEY=...
```

### Default AI Settings

```bash
# Default providers (can be overridden per tenant)
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o-mini
DEFAULT_EMBEDDING_PROVIDER=openai
DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
DEFAULT_RERANKER_PROVIDER=cohere
DEFAULT_RERANKER_MODEL=rerank-english-v3.0
```

### RAG Settings

```bash
# RAG Configuration
RAG_STRATEGY=hybrid                    # vanilla | hybrid | corrective
RAG_TOP_K=10                          # Documents to retrieve
RAG_SCORE_THRESHOLD=0.5               # Minimum similarity score
RAG_RERANK_ENABLED=true
RAG_RERANK_TOP_K=5                    # Documents after reranking
```

### Memory Settings

```bash
# Working Memory
MEMORY_WORKING_MAX_MESSAGES=20
MEMORY_WORKING_MAX_TOKENS=4000

# Episodic Memory
MEMORY_EPISODIC_SUMMARY_THRESHOLD=30  # Messages before summarizing
MEMORY_EPISODIC_SEARCH_TOP_K=3

# Semantic Memory
MEMORY_SEMANTIC_MAX_FACTS=100         # Max facts per user
MEMORY_SEMANTIC_MIN_CONFIDENCE=0.7
MEMORY_SEMANTIC_EXTRACTION_ENABLED=true

# Temporal Memory
MEMORY_TEMPORAL_DAILY_ENABLED=true
MEMORY_TEMPORAL_WEEKLY_ENABLED=true
MEMORY_TEMPORAL_MONTHLY_ENABLED=true
```

### Context Assembly

```bash
# Token Budgets
CONTEXT_MAX_TOKENS=8000
CONTEXT_SYSTEM_PROMPT_TOKENS=1000
CONTEXT_RETRIEVED_DOCS_TOKENS=2500
CONTEXT_USER_FACTS_TOKENS=500
CONTEXT_CONVERSATION_TOKENS=3000
CONTEXT_CURRENT_QUERY_TOKENS=1000
```

### Background Jobs

```bash
# Celery / Redis Streams
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Job Settings
JOB_FACT_EXTRACTION_BATCH_SIZE=10
JOB_SUMMARY_INTERVAL_MINUTES=30
JOB_KNOWLEDGE_SYNC_ENABLED=true
```

### Security

```bash
# JWT
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Keys (for service-to-service)
ADMIN_API_KEY=admin-secret-key
SERVICE_API_KEY=service-secret-key
```

---

## Configuration File

### config.py

```python
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "atlas-chat-ai"
    app_env: str = "development"
    app_debug: bool = False
    app_log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8003

    # API
    api_prefix: str = "/api/v1"
    api_cors_origins: List[str] = ["http://localhost:3000"]
    api_rate_limit_enabled: bool = True
    api_rate_limit_requests: int = 60

    # Database
    database_url: str
    database_pool_size: int = 20
    database_pool_max_overflow: int = 10
    database_echo: bool = False

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_prefix: str = "chat:"
    redis_ttl_default: int = 3600

    # AI Providers
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Defaults
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4o-mini"
    default_embedding_provider: str = "openai"
    default_embedding_model: str = "text-embedding-3-small"
    default_reranker_provider: str = "cohere"

    # RAG
    rag_strategy: str = "hybrid"
    rag_top_k: int = 10
    rag_score_threshold: float = 0.5
    rag_rerank_enabled: bool = True
    rag_rerank_top_k: int = 5

    # Memory
    memory_working_max_messages: int = 20
    memory_working_max_tokens: int = 4000
    memory_episodic_summary_threshold: int = 30
    memory_semantic_max_facts: int = 100
    memory_semantic_min_confidence: float = 0.7

    # Context
    context_max_tokens: int = 8000

    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## Per-Environment Configs

### Development (.env.development)

```bash
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG
DATABASE_ECHO=true

# Local services
DATABASE_URL=postgresql://chat_user:devpass@localhost:5432/atlas_chat_dev
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0

# Use test API keys
OPENAI_API_KEY=sk-test-...
```

### Staging (.env.staging)

```bash
APP_ENV=staging
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# Staging infrastructure
DATABASE_URL=postgresql://chat_user:stagingpass@db-staging:5432/atlas_chat
QDRANT_URL=http://qdrant-staging:6333
REDIS_URL=redis://redis-staging:6379/0

# Real API keys (limited quota)
OPENAI_API_KEY=sk-staging-...
```

### Production (.env.production)

```bash
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=WARNING

# Production infrastructure
DATABASE_URL=postgresql://chat_user:prodpass@db-prod:5432/atlas_chat
QDRANT_URL=http://qdrant-prod:6333
REDIS_URL=redis://redis-prod:6379/0

# Production API keys
OPENAI_API_KEY=sk-prod-...

# Stricter limits
API_RATE_LIMIT_REQUESTS=30
MEMORY_SEMANTIC_MAX_FACTS=50
```

---

## Docker Compose Config

```yaml
# docker-compose.yml
version: '3.8'

services:
  chat-api:
    build: ./backend
    ports:
      - "8003:8003"
    environment:
      - APP_ENV=${APP_ENV:-development}
      - DATABASE_URL=postgresql://chat_user:password@postgres:5432/atlas_chat
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - postgres
      - qdrant
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: chat_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: atlas_chat
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:v1.12.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

---

## Nomad Job Config

```hcl
# chat-api.nomad
job "chat-api" {
  datacenters = ["dc1"]
  namespace   = "chat"

  group "api" {
    count = 2

    network {
      port "http" {
        static = 8003
        to     = 8003
      }
    }

    task "api" {
      driver = "docker"

      config {
        image = "atlas-chat-api:latest"
        ports = ["http"]
      }

      env {
        APP_ENV = "production"
        APP_PORT = "8003"
      }

      template {
        data = <<EOF
DATABASE_URL={{ key "chat/database_url" }}
QDRANT_URL={{ key "chat/qdrant_url" }}
REDIS_URL={{ key "chat/redis_url" }}
OPENAI_API_KEY={{ key "chat/openai_api_key" }}
JWT_SECRET_KEY={{ key "chat/jwt_secret" }}
EOF
        destination = "secrets/env"
        env = true
      }

      resources {
        cpu    = 500
        memory = 1024
      }
    }
  }
}
```

---

## Validation

The application validates configuration on startup:

```python
def validate_config(settings: Settings):
    errors = []

    # Required API keys based on default provider
    if settings.default_llm_provider == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY required when default_llm_provider=openai")

    if settings.rag_rerank_enabled and not settings.cohere_api_key:
        errors.append("COHERE_API_KEY required when rag_rerank_enabled=true")

    # Database URL format
    if not settings.database_url.startswith("postgresql://"):
        errors.append("DATABASE_URL must be a PostgreSQL connection string")

    if errors:
        raise ConfigurationError("\n".join(errors))
```
