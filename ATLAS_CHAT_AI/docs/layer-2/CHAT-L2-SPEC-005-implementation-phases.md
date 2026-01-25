# CHAT-L2-SPEC-005: Implementation Phases

**Status**: Active
**Created**: 2026-01-25
**Complies With**: All Layer 0 Laws

---

## Overview

Development roadmap for ATLAS_CHAT_AI, organized in phases with clear deliverables.

---

## Phase Summary

| Phase | Focus | Effort | Dependencies |
|-------|-------|--------|--------------|
| 1 | Foundation (Persistence) | 3-4 days | None |
| 2 | Vector Store (RAG) | 4-5 days | Phase 1 |
| 3 | Memory System | 3-4 days | Phase 2 |
| 4 | Streaming & Polish | 2-3 days | Phase 3 |
| 5 | Multi-Tenant CMS | 3-4 days | Phase 4 |

**Total**: ~16-20 days

---

## Phase 1: Foundation (Persistence)

### Goal
Replace in-memory storage with PostgreSQL. Chat history persists across restarts.

### Deliverables
- [ ] Database schema (CHAT-L2-SPEC-001)
- [ ] Session repository
- [ ] Message repository (append-only)
- [ ] Basic API endpoints
- [ ] Migration scripts

### Files to Create

```
backend/
├── infrastructure/
│   └── database/
│       ├── connection.py
│       ├── repositories/
│       │   ├── session_repository.py
│       │   └── message_repository.py
│       └── migrations/
│           ├── 001_initial_schema.sql
│           └── 002_chat_tables.sql
├── core/
│   ├── entities/
│   │   ├── message.py
│   │   └── session.py
│   └── interfaces/
│       └── storage.py (MemoryStore interface)
└── api/
    └── routes/
        ├── chat.py
        └── sessions.py
```

### Verification

```bash
# 1. Start services
docker-compose up -d postgres

# 2. Run migrations
python scripts/migrate.py

# 3. Test persistence
curl -X POST http://localhost:8003/api/v1/chat \
  -H "X-Tenant-ID: test" \
  -d '{"message": "Hello"}'

# 4. Restart and verify
docker-compose restart chat-api
curl http://localhost:8003/api/v1/sessions
# Expected: Previous session still exists
```

### Acceptance Criteria
- [x] Chat messages persist in PostgreSQL
- [x] Sessions can be listed and retrieved
- [x] Message immutability enforced by trigger
- [x] No breaking changes to existing API

---

## Phase 2: Vector Store (RAG)

### Goal
Implement Qdrant-based retrieval. AI can find relevant documents.

### Deliverables
- [ ] Qdrant collections (SPEC-003)
- [ ] Embedding service
- [ ] RAG strategies (vanilla, hybrid)
- [ ] Document sync worker
- [ ] Search API

### Files to Create

```
backend/
├── infrastructure/
│   ├── adapters/
│   │   ├── storage/
│   │   │   └── qdrant_adapter.py
│   │   └── ai/
│   │       └── openai_adapter.py (embeddings)
│   └── cache/
│       └── embedding_cache.py
├── core/
│   ├── interfaces/
│   │   ├── storage.py (VectorStore interface)
│   │   └── ai_providers.py (EmbeddingProvider)
│   └── services/
│       └── embedding_service.py
├── workers/
│   └── knowledge_syncer.py
└── api/
    └── routes/
        └── search.py
```

### Verification

```bash
# 1. Start Qdrant
docker-compose up -d qdrant

# 2. Sync knowledge
python scripts/embed_knowledge.py --tenant=mantra --source=decisions

# 3. Test search
curl -X POST http://localhost:8003/api/v1/search \
  -H "X-Tenant-ID: mantra" \
  -d '{"query": "API authentication"}'
# Expected: Relevant decisions with similarity scores

# 4. Test RAG in chat
curl -X POST http://localhost:8003/api/v1/chat \
  -H "X-Tenant-ID: mantra" \
  -d '{"message": "What decisions exist about security?"}'
# Expected: Response references actual decisions
```

### Acceptance Criteria
- [x] Documents embedded in Qdrant
- [x] Semantic search returns relevant results
- [x] Chat responses include retrieved context
- [x] Embedding cache working

---

## Phase 3: Memory System

### Goal
Implement 4-layer memory (CHAT-LAW-003). AI remembers user facts and past conversations.

### Deliverables
- [ ] Working memory (in-process)
- [ ] Episodic memory (session embeddings)
- [ ] Semantic memory (user facts)
- [ ] Temporal memory (summaries)
- [ ] Memory manager
- [ ] Fact extraction worker
- [ ] Summarization worker

### Files to Create

```
backend/
├── core/
│   ├── interfaces/
│   │   ├── memory.py
│   │   └── extraction.py
│   └── services/
│       ├── memory_manager.py
│       └── context_assembler.py
├── infrastructure/
│   ├── adapters/
│   │   └── memory/
│   │       ├── working_memory.py
│   │       ├── episodic_memory.py
│   │       ├── semantic_memory.py
│   │       └── temporal_memory.py
│   └── database/
│       └── repositories/
│           ├── fact_repository.py
│           └── timeline_repository.py
├── workers/
│   ├── fact_extractor.py
│   ├── summarizer.py
│   └── temporal_aggregator.py
└── api/
    └── routes/
        └── memory.py
```

### Verification

```bash
# 1. Test fact extraction
# After multiple chats mentioning "I prefer TypeScript"
curl http://localhost:8003/api/v1/memory/facts
# Expected: {"type": "preference", "content": "Prefers TypeScript"}

# 2. Test session search
curl -X POST http://localhost:8003/api/v1/search/sessions \
  -d '{"query": "authentication discussion"}'
# Expected: Past sessions about authentication

# 3. Test context assembly
# Chat should include user facts and relevant past sessions
```

### Acceptance Criteria
- [x] User facts extracted and stored
- [x] Past sessions searchable by content
- [x] Daily/weekly summaries generated
- [x] Context includes relevant memories

---

## Phase 4: Streaming & Polish

### Goal
Add SSE streaming and improve UX. Production-ready polish.

### Deliverables
- [ ] SSE streaming endpoint
- [ ] Frontend SSE support
- [ ] Error handling improvements
- [ ] Rate limiting
- [ ] Logging & monitoring
- [ ] Performance optimization

### Files to Create/Modify

```
backend/
├── api/
│   ├── routes/
│   │   └── chat.py (add streaming)
│   └── middleware/
│       ├── rate_limit.py
│       └── logging.py
└── core/
    └── services/
        └── response_generator.py (streaming)

frontend/
├── hooks/
│   └── useAIChat.ts (SSE support)
├── components/
│   └── ai/
│       ├── FloatingChat.tsx (update)
│       └── StreamingText.tsx (new)
```

### Verification

```bash
# 1. Test streaming
curl -N -H "Accept: text/event-stream" \
  -X POST http://localhost:8003/api/v1/chat \
  -d '{"message": "Explain RAG architecture"}'
# Expected: Chunks arrive progressively

# 2. Test rate limiting
for i in {1..100}; do
  curl -X POST http://localhost:8003/api/v1/chat -d '{"message": "test"}'
done
# Expected: Rate limit error after threshold

# 3. Frontend test
# Open chat, send message, see typing animation
```

### Acceptance Criteria
- [x] Streaming responses work in browser
- [x] Rate limiting prevents abuse
- [x] Errors handled gracefully
- [x] Performance within targets (< 500ms to first token)

---

## Phase 5: Multi-Tenant CMS

### Goal
Admin interface for managing tenants. Self-service onboarding.

### Deliverables
- [ ] Tenant CRUD API
- [ ] CMS frontend
- [ ] Knowledge source configuration
- [ ] System prompt editor
- [ ] Usage dashboard
- [ ] SDK for integration

### Files to Create

```
backend/
├── api/
│   └── routes/
│       └── admin/
│           ├── tenants.py
│           ├── knowledge.py
│           └── stats.py
└── core/
    └── services/
        └── tenant_service.py

cms/
├── src/
│   ├── pages/
│   │   ├── tenants/
│   │   │   ├── index.tsx
│   │   │   ├── [id].tsx
│   │   │   └── new.tsx
│   │   ├── knowledge/
│   │   │   └── index.tsx
│   │   └── monitoring/
│   │       └── index.tsx
│   └── components/
│       ├── TenantForm.tsx
│       ├── SystemPromptEditor.tsx
│       └── UsageChart.tsx
```

### Verification

```bash
# 1. Create tenant via CMS
# - Navigate to /tenants/new
# - Fill form, submit
# - Tenant appears in list

# 2. Configure knowledge source
# - Select tenant
# - Add PostgreSQL source for "decisions"
# - Trigger sync
# - Check vector count

# 3. Test new tenant chat
curl -X POST http://localhost:8003/api/v1/chat \
  -H "X-Tenant-ID: new-tenant" \
  -d '{"message": "Hello"}'
# Expected: Response using new tenant's prompt
```

### Acceptance Criteria
- [x] Tenants manageable via CMS
- [x] Knowledge sources configurable
- [x] System prompts editable
- [x] Usage stats visible
- [x] New project can integrate via SDK

---

## Integration with MANTRA

After Phase 2+, integrate with existing ATLAS_MANTRA:

### Changes to MANTRA

```python
# MANTRA backend - use ATLAS_CHAT_AI as service
from atlas_chat_sdk import ChatClient

chat_client = ChatClient(
    base_url="http://chat-api:8003",
    tenant_id="mantra",
    api_key=settings.chat_api_key
)

# In AI routes
@router.post("/ai/chat")
async def chat(request: ChatRequest):
    async for chunk in chat_client.chat(
        message=request.message,
        user_id=request.user_id,
        session_id=request.session_id
    ):
        yield chunk
```

### MANTRA Knowledge Source

```python
# Register MANTRA's decisions as knowledge source
await chat_client.register_knowledge_source(
    source_type="database",
    source_name="decisions",
    connection_config={
        "table": "decisions",
        "fields": ["decision_code", "statement", "rationale", "constraints"],
        "filter": "status = 'active'"
    },
    sync_interval=5  # Every 5 minutes
)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Qdrant complexity | Start with single node, scale later |
| Embedding costs | Use caching, batch operations |
| Memory extraction quality | Start simple, iterate |
| Multi-tenant bugs | Extensive testing, isolation checks |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first token | < 500ms |
| Search relevance | > 0.7 precision |
| Memory recall | > 80% for recent facts |
| System uptime | > 99.5% |
| User satisfaction | To be measured |
