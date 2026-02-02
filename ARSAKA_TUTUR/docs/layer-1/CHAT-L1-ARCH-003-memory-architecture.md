# CHAT-L1-ARCH-003: Memory System Architecture

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-003, CHAT-LAW-006

---

## Context

Implementasi 4-layer memory system sesuai CHAT-LAW-003, dengan append-only constraint dari CHAT-LAW-006.

---

## Decision

### Memory Layer Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryManager                             │
│  - Coordinates all memory layers                            │
│  - Builds context for LLM                                   │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Working  │ │ Episodic │ │ Semantic │ │ Temporal │
│ Memory   │ │ Memory   │ │ Memory   │ │ Memory   │
│ (RAM)    │ │ (PG+Vec) │ │ (PG+Vec) │ │ (PG)     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## Layer 1: Working Memory

### Storage
- In-memory (Python list or Redis for distributed)
- Per-session, cleared on session end

### Schema

```python
@dataclass
class WorkingMemoryState:
    session_id: str
    messages: List[ChatMessage]  # Ordered by timestamp
    token_count: int
    max_tokens: int = 4000

    def add(self, message: ChatMessage):
        self.messages.append(message)
        self.token_count += estimate_tokens(message.content)
        self._trim_if_needed()

    def _trim_if_needed(self):
        """Remove oldest messages if over token limit"""
        while self.token_count > self.max_tokens and len(self.messages) > 2:
            removed = self.messages.pop(0)
            self.token_count -= estimate_tokens(removed.content)
```

### Implementation

```python
class InMemoryWorkingMemory(WorkingMemory):
    def __init__(self):
        self._sessions: Dict[str, WorkingMemoryState] = {}

    def add(self, session_id: str, message: ChatMessage) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = WorkingMemoryState(session_id=session_id, messages=[])
        self._sessions[session_id].add(message)

    def get_recent(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        if session_id not in self._sessions:
            return []
        return self._sessions[session_id].messages[-limit:]

    def get_token_count(self, session_id: str) -> int:
        if session_id not in self._sessions:
            return 0
        return self._sessions[session_id].token_count

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
```

---

## Layer 2: Episodic Memory

### Storage
- PostgreSQL for messages and sessions
- Qdrant for session embeddings (searchable)

### Database Schema

```sql
-- Sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,

    -- Metadata
    title VARCHAR(500),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,

    -- Summary for long sessions
    summary TEXT,
    summary_updated_at TIMESTAMPTZ,

    -- Soft delete
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_sessions_tenant_user ON chat_sessions(tenant_id, user_id);
CREATE INDEX idx_sessions_last_message ON chat_sessions(last_message_at DESC);

-- Messages table (APPEND-ONLY per CHAT-LAW-006)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,

    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,

    -- Context
    page_context VARCHAR(500),
    retrieved_doc_ids JSONB,  -- IDs of documents used for this response
    token_count INTEGER,

    -- AI metadata
    provider VARCHAR(50),
    model VARCHAR(100),

    -- Redaction (for compliance only)
    is_redacted BOOLEAN DEFAULT FALSE,
    redacted_at TIMESTAMPTZ,
    redacted_by VARCHAR(200),
    redaction_reason VARCHAR(500),

    -- Timestamp (no updated_at - immutable!)
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE INDEX idx_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_messages_tenant_user ON chat_messages(tenant_id, user_id);

-- Triggers for immutability (CHAT-LAW-006)
-- See CHAT-LAW-006 for trigger definitions
```

### Qdrant Collection for Session Search

```python
# Collection: {tenant_id}_sessions
session_vector_schema = {
    "vectors": {
        "summary": {
            "size": 1536,
            "distance": "Cosine"
        }
    },
    "payload_schema": {
        "session_id": "keyword",
        "user_id": "keyword",
        "started_at": "datetime",
        "topic_keywords": "keyword[]",
        "message_count": "integer"
    }
}
```

### Implementation

```python
class PostgresEpisodicMemory(EpisodicMemory):
    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store

    async def save_session(self, session: ChatSession) -> str:
        # Insert to PostgreSQL
        session_id = await self.db.execute(
            """
            INSERT INTO chat_sessions (tenant_id, user_id, title)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            session.tenant_id, session.user_id, session.title
        )
        return session_id

    async def search_sessions(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SessionSummary]:
        # Search in Qdrant
        results = await self.vector_store.search(
            collection=f"{tenant_id}_sessions",
            query_vector=query_embedding,
            top_k=top_k,
            filters={"user_id": user_id}
        )
        return [SessionSummary(**r.payload) for r in results]
```

---

## Layer 3: Semantic Memory

### Storage
- PostgreSQL for facts
- Qdrant for fact embeddings

### Database Schema

```sql
CREATE TABLE user_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,

    -- Fact content
    fact_type VARCHAR(50) NOT NULL,  -- preference, knowledge, relationship, context
    content TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),

    -- Source tracking
    source_session_id UUID REFERENCES chat_sessions(id),
    source_message_id UUID REFERENCES chat_messages(id),

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES user_facts(id),
    last_confirmed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_facts_tenant_user ON user_facts(tenant_id, user_id);
CREATE INDEX idx_facts_type ON user_facts(fact_type);
CREATE INDEX idx_facts_active ON user_facts(is_active) WHERE is_active = TRUE;
```

### Fact Types

```python
class FactType(Enum):
    PREFERENCE = "preference"      # User likes/dislikes
    KNOWLEDGE = "knowledge"        # What user knows
    RELATIONSHIP = "relationship"  # People/things user mentioned
    CONTEXT = "context"           # User's situation/work
    GOAL = "goal"                 # What user is trying to achieve
```

### Fact Extraction

```python
class LLMFactExtractor(FactExtractor):
    EXTRACTION_PROMPT = """
    Analyze this conversation and extract factual information about the user.

    Categories:
    - PREFERENCE: Things the user likes/dislikes (e.g., "prefers TypeScript")
    - KNOWLEDGE: What the user knows/doesn't know (e.g., "familiar with FastAPI")
    - RELATIONSHIP: People/projects mentioned (e.g., "works on ATLAS project")
    - CONTEXT: User's situation (e.g., "works at tech company")
    - GOAL: What user is trying to achieve (e.g., "building chat system")

    Rules:
    - Only extract FACTS, not opinions or questions
    - Each fact should be a single, clear statement
    - Include confidence score (0.0-1.0)
    - Skip facts that are already known

    Existing facts about this user:
    {existing_facts}

    Conversation:
    {messages}

    Output as JSON array:
    [{"type": "PREFERENCE", "content": "...", "confidence": 0.9}, ...]
    """

    async def extract(
        self,
        messages: List[ChatMessage],
        existing_facts: List[UserFact]
    ) -> List[ExtractedFact]:
        prompt = self.EXTRACTION_PROMPT.format(
            existing_facts=self._format_facts(existing_facts),
            messages=self._format_messages(messages)
        )
        result = await self.llm.generate([Message(role="user", content=prompt)])
        return self._parse_facts(result)
```

---

## Layer 4: Temporal Memory

### Storage
- PostgreSQL only (aggregated data)

### Database Schema

```sql
CREATE TABLE memory_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,

    -- Time period
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('day', 'week', 'month')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregated content
    summary TEXT NOT NULL,
    topics JSONB,  -- [{"topic": "...", "count": N}, ...]
    session_count INTEGER,
    message_count INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (tenant_id, user_id, period_type, period_start)
);

CREATE INDEX idx_timeline_lookup ON memory_timeline(tenant_id, user_id, period_type, period_start);
```

### Aggregation Job

```python
async def aggregate_daily_summary(date: date):
    """Run daily at midnight to create day summaries"""

    # Get all users with activity on this date
    users = await db.fetch_all(
        """
        SELECT DISTINCT tenant_id, user_id
        FROM chat_messages
        WHERE DATE(created_at) = $1
        """,
        date
    )

    for user in users:
        # Get all messages for this user on this date
        messages = await db.fetch_all(
            """
            SELECT * FROM chat_messages
            WHERE tenant_id = $1 AND user_id = $2
            AND DATE(created_at) = $3
            ORDER BY created_at
            """,
            user.tenant_id, user.user_id, date
        )

        # Generate summary using LLM
        summary = await summarizer.summarize(messages)
        topics = await topic_extractor.extract(messages)

        # Save to timeline
        await db.execute(
            """
            INSERT INTO memory_timeline
            (tenant_id, user_id, period_type, period_start, period_end, summary, topics, message_count)
            VALUES ($1, $2, 'day', $3, $3, $4, $5, $6)
            ON CONFLICT (tenant_id, user_id, period_type, period_start)
            DO UPDATE SET summary = $4, topics = $5, message_count = $6
            """,
            user.tenant_id, user.user_id, date, summary, topics, len(messages)
        )
```

---

## Memory Manager

```python
class MemoryManager:
    def __init__(
        self,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        temporal: TemporalMemory,
        embedder: EmbeddingProvider,
    ):
        self.working = working
        self.episodic = episodic
        self.semantic = semantic
        self.temporal = temporal
        self.embedder = embedder

    async def build_context(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        current_query: str
    ) -> MemoryContext:
        """Build context from all memory layers"""

        query_embedding = await self.embedder.embed(current_query)

        # Parallel fetch from all layers
        working_messages, relevant_sessions, user_facts, temporal_summary = await asyncio.gather(
            self._get_working_context(session_id),
            self._get_episodic_context(tenant_id, user_id, query_embedding),
            self._get_semantic_context(tenant_id, user_id, query_embedding),
            self._get_temporal_context(tenant_id, user_id, current_query),
        )

        return MemoryContext(
            working_messages=working_messages,
            relevant_sessions=relevant_sessions,
            user_facts=user_facts,
            temporal_summary=temporal_summary,
        )

    async def save_interaction(
        self,
        session_id: str,
        user_message: ChatMessage,
        assistant_message: ChatMessage
    ):
        """Save interaction to appropriate layers"""

        # 1. Add to working memory (sync)
        self.working.add(session_id, user_message)
        self.working.add(session_id, assistant_message)

        # 2. Save to episodic (async)
        await self.episodic.save_messages(session_id, [user_message, assistant_message])

        # 3. Queue fact extraction (background)
        await self.queue.enqueue("extract_facts", {
            "session_id": session_id,
            "messages": [user_message.dict(), assistant_message.dict()]
        })
```

---

## Consequences

### Positive
- Complete memory system covering all use cases
- Efficient token usage (only relevant context)
- Scalable (background processing for extraction)
- Compliant with LAW-006 (append-only)

### Negative
- Complexity in managing 4 layers
- Background jobs needed for extraction/aggregation
- Storage costs increase over time

---

## Configuration

```python
MEMORY_CONFIG = {
    "working": {
        "max_messages": 20,
        "max_tokens": 4000,
    },
    "episodic": {
        "summary_threshold": 30,  # Messages before summarization
        "search_top_k": 3,
    },
    "semantic": {
        "max_facts_per_user": 100,
        "min_confidence": 0.7,
        "extraction_batch_size": 10,
    },
    "temporal": {
        "daily_aggregation_time": "00:00",
        "weekly_aggregation_day": "sunday",
        "retention_days": 365,
    },
}
```
