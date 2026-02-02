# CHAT-LAW-004: Multi-Tenant Isolation

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Security

---

## Statement

> Data antar tenant HARUS terisolasi secara absolut.
> Tenant A TIDAK BOLEH bisa mengakses, melihat, atau menyimpulkan data Tenant B.

---

## Rationale

ARSAKA_TUTUR adalah sistem reusable yang akan di-attach ke berbagai project:
- ARSAKA_MANTRA (decisions)
- ARSAKA_PUGUH (enforcement)
- ARSAKA_PANDAWA (hospitality)
- Future projects

Setiap project adalah tenant berbeda dengan data berbeda.

---

## Isolation Levels

### Level 1: Data Isolation

```sql
-- SETIAP table HARUS punya tenant_id
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL,  -- WAJIB
    user_id VARCHAR(200) NOT NULL,
    ...
);

-- SETIAP query HARUS filter by tenant_id
SELECT * FROM chat_sessions
WHERE tenant_id = $1 AND user_id = $2;  -- WAJIB
```

### Level 2: Vector Isolation

```python
# Qdrant: Use separate collections per tenant
collection_name = f"tenant_{tenant_id}_documents"

# OR use payload filtering
results = qdrant.search(
    collection="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
        ]
    )
)
```

### Level 3: Knowledge Isolation

```
Tenant MANTRA:
  - Knowledge base: Decisions, Groups, Features
  - System prompt: MANTRA persona

Tenant PANDAWA:
  - Knowledge base: Reservations, Guests, Rooms
  - System prompt: Hospitality assistant
```

### Level 4: Configuration Isolation

```python
# Per-tenant configuration
class TenantConfig:
    tenant_id: str
    llm_provider: str       # Different per tenant
    embedding_model: str    # Different per tenant
    system_prompt: str      # Different per tenant
    rag_strategy: str       # Different per tenant
    max_context_tokens: int
```

---

## Constraints

### REQUIREMENT
- SEMUA tables HARUS memiliki kolom `tenant_id`
- SEMUA queries HARUS include `WHERE tenant_id = ?`
- SEMUA vector searches HARUS filter by `tenant_id`
- Tenant config HARUS loaded di awal request

### PROHIBITION
- DILARANG query tanpa tenant_id filter (bahkan untuk admin)
- DILARANG share vector collections antar tenant
- DILARANG cache data lintas tenant
- DILARANG log user messages dengan tenant lain visible

### LIMITATION
- Cross-tenant analytics HANYA boleh aggregated (no individual data)
- Admin access HARUS per-tenant (no super-admin across all)

---

## Implementation Pattern

### Request Flow

```python
async def chat_endpoint(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_from_token),  # Extract from JWT
    user_id: str = Depends(get_user_from_token),
):
    # Tenant context set at entry point
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        config=await get_tenant_config(tenant_id),
    )

    # All downstream operations use this context
    response = await orchestrator.chat(request.message, context)
    return response
```

### Repository Pattern

```python
class ChatRepository:
    async def get_sessions(
        self,
        tenant_id: str,  # WAJIB parameter
        user_id: str
    ) -> List[ChatSession]:
        return await self.db.fetch_all(
            """
            SELECT * FROM chat_sessions
            WHERE tenant_id = $1 AND user_id = $2
            ORDER BY created_at DESC
            """,
            tenant_id, user_id
        )

    # WRONG - no tenant_id
    # async def get_all_sessions(self):  # DILARANG!
    #     return await self.db.fetch_all("SELECT * FROM chat_sessions")
```

---

## Tenant Registration

```python
# When attaching ARSAKA_TUTUR to a project
await chat_ai.register_tenant(
    tenant_id="mantra",
    config=TenantConfig(
        name="ARSAKA_MANTRA",
        llm_provider="openai",
        system_prompt=MANTRA_SYSTEM_PROMPT,
        knowledge_sources=["decisions"],
        embedding_model="text-embedding-3-small",
    )
)

await chat_ai.register_tenant(
    tenant_id="pandawa",
    config=TenantConfig(
        name="ARSAKA_PANDAWA",
        llm_provider="deepseek",
        system_prompt=HOSPITALITY_SYSTEM_PROMPT,
        knowledge_sources=["reservations", "guests"],
        embedding_model="text-embedding-3-small",
    )
)
```

---

## Invariants

1. Tidak ada query yang berjalan tanpa tenant_id
2. Tidak ada response yang berisi data tenant lain
3. Tidak ada log yang menggabungkan data multi-tenant
4. Tenant deletion = semua data tenant terhapus
