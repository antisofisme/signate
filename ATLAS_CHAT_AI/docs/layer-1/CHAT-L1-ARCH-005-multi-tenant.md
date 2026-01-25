# CHAT-L1-ARCH-005: Multi-Tenant Configuration

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-004

---

## Context

ATLAS_CHAT_AI akan digunakan oleh multiple projects (tenants): MANTRA, PUGUH, PANDAWA, dll. Setiap tenant memiliki:
- Knowledge base berbeda
- System prompt berbeda
- Konfigurasi AI berbeda

---

## Decision

### Tenant Configuration Model

```python
@dataclass
class TenantConfig:
    # Identity
    tenant_id: str                    # e.g., "mantra", "pandawa"
    name: str                         # e.g., "ATLAS_MANTRA"
    description: str

    # AI Configuration
    llm_provider: str                 # openai | deepseek | claude | groq
    llm_model: str                    # gpt-4o-mini | deepseek-chat | etc.
    embedding_provider: str           # openai | cohere | local
    embedding_model: str              # text-embedding-3-small | etc.

    # RAG Configuration
    rag_strategy: str                 # vanilla | hybrid | corrective
    reranker_enabled: bool
    reranker_provider: Optional[str]  # cohere | cross-encoder | none

    # System Prompt
    system_prompt: str                # Full system prompt for this tenant
    persona_name: str                 # e.g., "MANTRA", "Hospitality Assistant"

    # Knowledge Sources
    knowledge_sources: List[KnowledgeSourceConfig]

    # Limits
    max_context_tokens: int = 8000
    max_response_tokens: int = 1000
    max_messages_per_session: int = 100
    max_sessions_per_user: int = 50

    # Feature Flags
    enable_memory_extraction: bool = True
    enable_temporal_memory: bool = True
    enable_streaming: bool = True

    # Metadata
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


@dataclass
class KnowledgeSourceConfig:
    source_type: str        # database | api | file
    source_name: str        # e.g., "decisions", "reservations"
    connection_config: dict # Connection details
    sync_interval: int      # Minutes between syncs (0 = manual only)
    chunking_strategy: str  # fixed | semantic | recursive
    chunk_size: int = 500
    chunk_overlap: int = 50
```

---

## Database Schema

```sql
-- Tenants table
CREATE TABLE tenants (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,

    -- AI Config (stored as JSONB for flexibility)
    llm_config JSONB NOT NULL DEFAULT '{
        "provider": "openai",
        "model": "gpt-4o-mini"
    }',
    embedding_config JSONB NOT NULL DEFAULT '{
        "provider": "openai",
        "model": "text-embedding-3-small"
    }',
    rag_config JSONB NOT NULL DEFAULT '{
        "strategy": "hybrid",
        "reranker_enabled": true,
        "reranker_provider": "cohere"
    }',

    -- System Prompt
    system_prompt TEXT NOT NULL,
    persona_name VARCHAR(100) NOT NULL,

    -- Limits
    max_context_tokens INTEGER DEFAULT 8000,
    max_response_tokens INTEGER DEFAULT 1000,
    max_messages_per_session INTEGER DEFAULT 100,
    max_sessions_per_user INTEGER DEFAULT 50,

    -- Feature Flags
    features JSONB NOT NULL DEFAULT '{
        "memory_extraction": true,
        "temporal_memory": true,
        "streaming": true
    }',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge sources for each tenant
CREATE TABLE tenant_knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id),

    source_type VARCHAR(50) NOT NULL,  -- database | api | file
    source_name VARCHAR(200) NOT NULL,
    connection_config JSONB NOT NULL,

    -- Chunking config
    chunking_strategy VARCHAR(50) DEFAULT 'fixed',
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,

    -- Sync config
    sync_interval INTEGER DEFAULT 60,  -- minutes
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(50),
    document_count INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (tenant_id, source_name)
);

CREATE INDEX idx_knowledge_sources_tenant ON tenant_knowledge_sources(tenant_id);
```

---

## Tenant Registration Examples

### MANTRA Tenant

```python
mantra_config = TenantConfig(
    tenant_id="mantra",
    name="ATLAS_MANTRA",
    description="Constitutional Law System for Decisions",

    llm_provider="openai",
    llm_model="gpt-4o-mini",
    embedding_provider="openai",
    embedding_model="text-embedding-3-small",

    rag_strategy="hybrid",
    reranker_enabled=True,
    reranker_provider="cohere",

    system_prompt="""You are MANTRA - an intellectual sparring partner...
    [Full MANTRA system prompt]
    """,
    persona_name="MANTRA",

    knowledge_sources=[
        KnowledgeSourceConfig(
            source_type="database",
            source_name="decisions",
            connection_config={
                "table": "decisions",
                "fields": ["decision_code", "statement", "rationale", "constraints"],
                "filter": "is_active = TRUE"
            },
            sync_interval=5,  # Every 5 minutes
            chunking_strategy="semantic",
        )
    ],

    max_context_tokens=8000,
    enable_memory_extraction=True,
)
```

### PANDAWA Tenant

```python
pandawa_config = TenantConfig(
    tenant_id="pandawa",
    name="ATLAS_PANDAWA",
    description="Enterprise Hospitality Platform",

    llm_provider="deepseek",
    llm_model="deepseek-chat",
    embedding_provider="openai",
    embedding_model="text-embedding-3-small",

    rag_strategy="vanilla",  # Simpler for now
    reranker_enabled=False,

    system_prompt="""You are a Hospitality Assistant for ATLAS_PANDAWA.
    You help hotel staff with:
    - Reservation management
    - Guest inquiries
    - Room assignments
    - Check-in/check-out procedures

    Be helpful, professional, and concise.
    """,
    persona_name="Hospitality Assistant",

    knowledge_sources=[
        KnowledgeSourceConfig(
            source_type="database",
            source_name="reservations",
            connection_config={
                "table": "reservations",
                "fields": ["reservation_number", "guest_name", "room_type", "dates"],
            },
            sync_interval=1,  # Real-time for reservations
        ),
        KnowledgeSourceConfig(
            source_type="database",
            source_name="room_types",
            connection_config={
                "table": "room_types",
                "fields": ["name", "description", "amenities", "capacity"],
            },
            sync_interval=60,  # Hourly
        ),
    ],

    max_context_tokens=6000,  # Smaller for faster responses
    enable_memory_extraction=False,  # Not needed for transactional queries
)
```

---

## Tenant Registry Service

```python
class TenantRegistry:
    def __init__(self, db: Database, cache: Cache):
        self.db = db
        self.cache = cache
        self._local_cache: Dict[str, TenantConfig] = {}

    async def get_config(self, tenant_id: str) -> Optional[TenantConfig]:
        # 1. Check local cache
        if tenant_id in self._local_cache:
            return self._local_cache[tenant_id]

        # 2. Check Redis cache
        cache_key = f"tenant:{tenant_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            config = TenantConfig(**json.loads(cached))
            self._local_cache[tenant_id] = config
            return config

        # 3. Load from database
        row = await self.db.fetch_one(
            "SELECT * FROM tenants WHERE id = $1 AND is_active = TRUE",
            tenant_id
        )
        if not row:
            return None

        config = self._row_to_config(row)

        # 4. Cache and return
        await self.cache.set(cache_key, config.json(), ttl=300)
        self._local_cache[tenant_id] = config
        return config

    async def register(self, config: TenantConfig) -> str:
        await self.db.execute(
            """
            INSERT INTO tenants (id, name, description, llm_config, embedding_config,
                                 rag_config, system_prompt, persona_name, features)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            config.tenant_id, config.name, config.description,
            json.dumps({"provider": config.llm_provider, "model": config.llm_model}),
            json.dumps({"provider": config.embedding_provider, "model": config.embedding_model}),
            json.dumps({"strategy": config.rag_strategy, "reranker_enabled": config.reranker_enabled}),
            config.system_prompt, config.persona_name,
            json.dumps({"memory_extraction": config.enable_memory_extraction}),
        )

        # Invalidate cache
        await self.cache.delete(f"tenant:{config.tenant_id}")
        self._local_cache.pop(config.tenant_id, None)

        return config.tenant_id

    def invalidate_cache(self, tenant_id: str):
        """Call this when tenant config is updated"""
        self._local_cache.pop(tenant_id, None)
        asyncio.create_task(self.cache.delete(f"tenant:{tenant_id}"))
```

---

## Component Factory

```python
class TenantComponentFactory:
    """Creates properly configured components for a tenant"""

    def __init__(self, global_config: GlobalConfig):
        self.global_config = global_config

    def create_llm(self, tenant_config: TenantConfig) -> LLMProvider:
        match tenant_config.llm_provider:
            case "openai":
                return OpenAIProvider(
                    api_key=self.global_config.openai_api_key,
                    model=tenant_config.llm_model
                )
            case "deepseek":
                return DeepSeekProvider(
                    api_key=self.global_config.deepseek_api_key,
                    model=tenant_config.llm_model
                )
            case "claude":
                return ClaudeProvider(
                    api_key=self.global_config.anthropic_api_key,
                    model=tenant_config.llm_model
                )
            case _:
                raise ValueError(f"Unknown LLM provider: {tenant_config.llm_provider}")

    def create_embedder(self, tenant_config: TenantConfig) -> EmbeddingProvider:
        match tenant_config.embedding_provider:
            case "openai":
                return OpenAIEmbedder(
                    api_key=self.global_config.openai_api_key,
                    model=tenant_config.embedding_model
                )
            case "cohere":
                return CohereEmbedder(
                    api_key=self.global_config.cohere_api_key,
                    model=tenant_config.embedding_model
                )
            case "local":
                return LocalEmbedder(
                    model_path=self.global_config.local_embedding_model
                )

    def create_rag_strategy(self, tenant_config: TenantConfig) -> RAGStrategy:
        match tenant_config.rag_strategy:
            case "vanilla":
                return VanillaRAGStrategy(self.create_vector_store(tenant_config))
            case "hybrid":
                return HybridRAGStrategy(
                    self.create_vector_store(tenant_config),
                    self.create_bm25_index(tenant_config)
                )
            case "corrective":
                return CorrectiveRAGStrategy(
                    HybridRAGStrategy(...),
                    self.create_llm(tenant_config)
                )

    def create_orchestrator(self, tenant_config: TenantConfig) -> RAGOrchestrator:
        return RAGOrchestrator(
            query_processor=QueryProcessor(self.create_llm(tenant_config)),
            embedding_service=EmbeddingService(self.create_embedder(tenant_config)),
            rag_strategy=self.create_rag_strategy(tenant_config),
            reranker=self.create_reranker(tenant_config),
            context_assembler=ContextAssembler(tenant_config.max_context_tokens),
            generator=ResponseGenerator(self.create_llm(tenant_config)),
        )
```

---

## Request Flow with Tenant Context

```python
@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user_id: str = Depends(get_current_user),
):
    # 1. Get tenant config
    tenant_config = await tenant_registry.get_config(tenant_id)
    if not tenant_config:
        raise HTTPException(404, "Tenant not found")

    # 2. Create tenant-specific orchestrator
    orchestrator = component_factory.create_orchestrator(tenant_config)

    # 3. Get memory context
    memory_context = await memory_manager.build_context(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=request.session_id,
        current_query=request.message,
    )

    # 4. Process with RAG
    async def generate():
        async for chunk in orchestrator.process(
            query=request.message,
            tenant_config=tenant_config,
            memory_context=memory_context,
        ):
            yield {"event": "message", "data": json.dumps({"content": chunk})}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())
```

---

## Consequences

### Positive
- Each tenant fully customizable
- Easy to onboard new projects
- Component reuse across tenants
- Clear separation of concerns

### Negative
- Configuration complexity
- Need CMS for management
- Cache invalidation important

---

## CMS Requirements

For managing tenants, a CMS should provide:
1. Tenant CRUD (create, read, update, delete)
2. Knowledge source configuration
3. System prompt editor
4. Feature flag toggles
5. Usage monitoring per tenant
6. Sync status dashboard
