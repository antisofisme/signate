# CHAT-L1-ARCH-006: Project Structure

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-001, CHAT-LAW-002

---

## Context

Definisi struktur direktori yang mendukung modular architecture dan clean separation of concerns.

---

## Decision

### Directory Structure

```
ATLAS_CHAT_AI/
│
├── docs/                           # Documentation (this folder)
│   ├── layer-0/                   # Constitutional Laws
│   ├── layer-1/                   # Architecture Decisions
│   ├── layer-2/                   # Implementation Specs
│   └── layer-3/                   # Operational Guidelines
│
├── backend/                        # Python FastAPI Backend
│   │
│   ├── core/                      # Domain layer (no external deps)
│   │   ├── interfaces/            # Abstract interfaces (CHAT-LAW-002)
│   │   │   ├── __init__.py
│   │   │   ├── storage.py         # VectorStore, MemoryStore
│   │   │   ├── ai_providers.py    # LLMProvider, EmbeddingProvider, Reranker
│   │   │   ├── rag.py             # RAGStrategy, DocumentChunker
│   │   │   ├── memory.py          # WorkingMemory, EpisodicMemory, etc.
│   │   │   ├── extraction.py      # FactExtractor, Summarizer
│   │   │   ├── tenant.py          # TenantRegistry, KnowledgeSource
│   │   │   └── context.py         # ContextAssembler
│   │   │
│   │   ├── entities/              # Domain entities
│   │   │   ├── __init__.py
│   │   │   ├── message.py         # ChatMessage, Message
│   │   │   ├── session.py         # ChatSession, SessionSummary
│   │   │   ├── memory.py          # UserFact, TimeSummary, MemoryContext
│   │   │   ├── document.py        # Document, Chunk, SearchResult
│   │   │   ├── tenant.py          # TenantConfig, KnowledgeSourceConfig
│   │   │   └── context.py         # AssembledContext, ProcessedQuery
│   │   │
│   │   └── services/              # Domain services (orchestration)
│   │       ├── __init__.py
│   │       ├── chat_orchestrator.py
│   │       ├── rag_orchestrator.py
│   │       ├── memory_manager.py
│   │       └── context_assembler.py
│   │
│   ├── infrastructure/            # External dependencies layer
│   │   ├── adapters/              # Interface implementations
│   │   │   ├── storage/
│   │   │   │   ├── qdrant_adapter.py
│   │   │   │   ├── pinecone_adapter.py
│   │   │   │   └── postgres_memory_store.py
│   │   │   │
│   │   │   ├── ai/
│   │   │   │   ├── openai_adapter.py
│   │   │   │   ├── deepseek_adapter.py
│   │   │   │   ├── claude_adapter.py
│   │   │   │   ├── cohere_reranker.py
│   │   │   │   └── local_embedder.py
│   │   │   │
│   │   │   ├── rag/
│   │   │   │   ├── vanilla_strategy.py
│   │   │   │   ├── hybrid_strategy.py
│   │   │   │   └── corrective_strategy.py
│   │   │   │
│   │   │   └── knowledge/
│   │   │       ├── database_source.py
│   │   │       ├── api_source.py
│   │   │       └── file_source.py
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── repositories/
│   │   │   │   ├── session_repository.py
│   │   │   │   ├── message_repository.py
│   │   │   │   ├── fact_repository.py
│   │   │   │   └── tenant_repository.py
│   │   │   └── migrations/
│   │   │       ├── 001_initial_schema.sql
│   │   │       ├── 002_memory_tables.sql
│   │   │       └── 003_tenant_tables.sql
│   │   │
│   │   └── cache/
│   │       ├── redis_cache.py
│   │       └── memory_cache.py
│   │
│   ├── api/                       # HTTP layer
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app
│   │   ├── routes/
│   │   │   ├── chat.py            # /api/v1/chat
│   │   │   ├── sessions.py        # /api/v1/sessions
│   │   │   ├── search.py          # /api/v1/search
│   │   │   ├── admin.py           # /api/v1/admin
│   │   │   └── health.py          # /health
│   │   ├── middleware/
│   │   │   ├── tenant.py          # Tenant extraction
│   │   │   ├── auth.py            # Authentication
│   │   │   └── logging.py         # Request logging
│   │   └── schemas/
│   │       ├── requests.py
│   │       └── responses.py
│   │
│   ├── workers/                   # Background jobs
│   │   ├── fact_extractor.py      # Extract facts from conversations
│   │   ├── summarizer.py          # Create session summaries
│   │   ├── temporal_aggregator.py # Daily/weekly/monthly summaries
│   │   ├── knowledge_syncer.py    # Sync knowledge sources
│   │   └── embedding_worker.py    # Batch embedding jobs
│   │
│   ├── container.py               # Dependency Injection container
│   ├── config.py                  # Configuration loading
│   ├── requirements.txt
│   └── Dockerfile
│
├── cms/                            # Admin CMS (optional)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── tenants/           # Tenant management
│   │   │   ├── knowledge/         # Knowledge source config
│   │   │   ├── prompts/           # System prompt editor
│   │   │   └── monitoring/        # Usage dashboard
│   │   └── ...
│   └── package.json
│
├── sdk/                            # Client SDK (optional)
│   ├── python/
│   │   ├── atlas_chat/
│   │   │   ├── client.py
│   │   │   └── models.py
│   │   └── setup.py
│   └── typescript/
│       ├── src/
│       │   ├── client.ts
│       │   └── types.ts
│       └── package.json
│
├── docker/
│   ├── docker-compose.yml         # Local development
│   ├── docker-compose.prod.yml    # Production
│   └── qdrant/
│       └── config.yaml
│
├── nomad/                          # Nomad job files
│   ├── chat-api.nomad
│   ├── chat-worker.nomad
│   └── chat-qdrant.nomad
│
├── scripts/
│   ├── init_db.py                 # Initialize database
│   ├── seed_tenant.py             # Seed tenant configs
│   ├── migrate.py                 # Run migrations
│   └── embed_knowledge.py         # Initial embedding
│
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   └── infrastructure/
│   ├── integration/
│   └── e2e/
│
├── .env.example
├── README.md
└── pyproject.toml
```

---

## Layer Separation

### Core Layer (`core/`)
- **NO external dependencies** (no SDK imports)
- Pure Python with standard library only
- Contains: interfaces, entities, domain services
- Can be tested without mocking external services

### Infrastructure Layer (`infrastructure/`)
- **ALL external dependencies here**
- Implements interfaces from core
- Contains: adapters, repositories, external clients
- Each adapter is replaceable

### API Layer (`api/`)
- HTTP-specific code only
- FastAPI routes, middleware, schemas
- Thin layer - delegates to core services

### Workers Layer (`workers/`)
- Background job definitions
- Uses core services for logic
- Handles scheduling and retry

---

## Import Rules

```python
# CORRECT - core imports only from core
# core/services/chat_orchestrator.py
from core.interfaces.storage import VectorStore
from core.interfaces.ai_providers import LLMProvider
from core.entities.message import ChatMessage

# CORRECT - infrastructure imports from core
# infrastructure/adapters/storage/qdrant_adapter.py
from core.interfaces.storage import VectorStore, SearchResult
from qdrant_client import QdrantClient  # External import OK here

# CORRECT - api imports from core and infrastructure
# api/routes/chat.py
from core.services.chat_orchestrator import ChatOrchestrator
from infrastructure.container import get_orchestrator

# WRONG - core importing from infrastructure
# core/services/chat_orchestrator.py
from infrastructure.adapters.storage.qdrant_adapter import QdrantAdapter  # NO!
```

---

## Dependency Injection

```python
# container.py - Composition Root

from core.interfaces.storage import VectorStore
from core.interfaces.ai_providers import LLMProvider, EmbeddingProvider
from core.services.chat_orchestrator import ChatOrchestrator
from infrastructure.adapters.storage.qdrant_adapter import QdrantAdapter
from infrastructure.adapters.ai.openai_adapter import OpenAIAdapter

class Container:
    def __init__(self, config: Config):
        self.config = config
        self._instances = {}

    def get_vector_store(self) -> VectorStore:
        if "vector_store" not in self._instances:
            match self.config.vector_store:
                case "qdrant":
                    from infrastructure.adapters.storage.qdrant_adapter import QdrantAdapter
                    self._instances["vector_store"] = QdrantAdapter(self.config.qdrant_url)
                case "pinecone":
                    from infrastructure.adapters.storage.pinecone_adapter import PineconeAdapter
                    self._instances["vector_store"] = PineconeAdapter(self.config.pinecone_api_key)
        return self._instances["vector_store"]

    def get_llm(self, tenant_config: TenantConfig) -> LLMProvider:
        # Create per-tenant, not cached
        match tenant_config.llm_provider:
            case "openai":
                from infrastructure.adapters.ai.openai_adapter import OpenAIAdapter
                return OpenAIAdapter(self.config.openai_api_key, tenant_config.llm_model)
            case "deepseek":
                from infrastructure.adapters.ai.deepseek_adapter import DeepSeekAdapter
                return DeepSeekAdapter(self.config.deepseek_api_key, tenant_config.llm_model)

    def get_orchestrator(self, tenant_config: TenantConfig) -> ChatOrchestrator:
        return ChatOrchestrator(
            vector_store=self.get_vector_store(),
            llm=self.get_llm(tenant_config),
            embedder=self.get_embedder(tenant_config),
            memory_manager=self.get_memory_manager(),
        )


# Global container instance
_container: Optional[Container] = None

def init_container(config: Config):
    global _container
    _container = Container(config)

def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container
```

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Interface | `{name}.py` | `storage.py`, `ai_providers.py` |
| Adapter | `{vendor}_adapter.py` | `qdrant_adapter.py` |
| Entity | `{name}.py` | `message.py`, `session.py` |
| Service | `{name}_service.py` or `{name}_orchestrator.py` | `chat_orchestrator.py` |
| Repository | `{entity}_repository.py` | `session_repository.py` |
| Route | `{resource}.py` | `chat.py`, `sessions.py` |
| Worker | `{job_name}.py` or `{job_name}_worker.py` | `fact_extractor.py` |
| Migration | `{number}_{description}.sql` | `001_initial_schema.sql` |

---

## Consequences

### Positive
- Clear separation of concerns
- Easy to test core without mocks
- Easy to add new adapters
- Standard Python package structure

### Negative
- More files/directories
- Import paths can be long
- Need to understand layers

---

## Quick Reference

```
Where to put new code:

New interface?           → core/interfaces/
New domain entity?       → core/entities/
New business logic?      → core/services/
New external adapter?    → infrastructure/adapters/{category}/
New database table?      → infrastructure/database/migrations/
New API endpoint?        → api/routes/
New background job?      → workers/
New test?                → tests/{unit|integration|e2e}/
```
