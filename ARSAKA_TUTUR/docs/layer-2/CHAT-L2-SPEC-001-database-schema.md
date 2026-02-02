# CHAT-L2-SPEC-001: Database Schema

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-004, CHAT-LAW-006

---

## Overview

Complete PostgreSQL schema for ARSAKA_TUTUR, following CHAT-LAW-004 (multi-tenant) and CHAT-LAW-006 (append-only).

---

## Tables

### 1. Tenants

```sql
-- Tenant registration and configuration
CREATE TABLE tenants (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,

    -- AI Configuration
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

COMMENT ON TABLE tenants IS 'Tenant registration and configuration';
COMMENT ON COLUMN tenants.llm_config IS 'JSON: {provider, model, temperature, max_tokens}';
COMMENT ON COLUMN tenants.features IS 'JSON: {memory_extraction, temporal_memory, streaming}';
```

### 2. Knowledge Sources

```sql
-- Knowledge sources per tenant
CREATE TABLE tenant_knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Source identification
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('database', 'api', 'file')),
    source_name VARCHAR(200) NOT NULL,

    -- Connection configuration
    connection_config JSONB NOT NULL,
    -- For database: {table, fields[], filter, connection_string}
    -- For api: {url, headers, method, body_template}
    -- For file: {path, format, watch_changes}

    -- Chunking configuration
    chunking_strategy VARCHAR(50) DEFAULT 'fixed' CHECK (chunking_strategy IN ('fixed', 'semantic', 'recursive')),
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,

    -- Sync configuration
    sync_interval INTEGER DEFAULT 60,  -- minutes, 0 = manual only
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,
    document_count INTEGER DEFAULT 0,
    vector_count INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (tenant_id, source_name)
);

CREATE INDEX idx_knowledge_sources_tenant ON tenant_knowledge_sources(tenant_id);
CREATE INDEX idx_knowledge_sources_sync ON tenant_knowledge_sources(last_sync_at) WHERE is_active = TRUE;

COMMENT ON TABLE tenant_knowledge_sources IS 'Knowledge sources configuration per tenant';
```

### 3. Chat Sessions

```sql
-- Chat sessions (episodic memory container)
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(200) NOT NULL,

    -- Session metadata
    title VARCHAR(500),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,

    -- Summary for long sessions
    summary TEXT,
    summary_embedding BYTEA,  -- Serialized vector for similarity search
    summary_updated_at TIMESTAMPTZ,

    -- Topics extracted from conversation
    topics JSONB DEFAULT '[]',

    -- Soft delete (CHAT-LAW-006 compliant)
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(200),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_tenant_user ON chat_sessions(tenant_id, user_id);
CREATE INDEX idx_sessions_last_message ON chat_sessions(last_message_at DESC);
CREATE INDEX idx_sessions_active ON chat_sessions(is_active, is_deleted) WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE chat_sessions IS 'Chat sessions - episodic memory container';
COMMENT ON COLUMN chat_sessions.summary_embedding IS 'Serialized embedding vector for session similarity search';
```

### 4. Chat Messages (APPEND-ONLY)

```sql
-- Chat messages (APPEND-ONLY per CHAT-LAW-006)
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

    -- Token tracking
    token_count INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,

    -- AI metadata
    provider VARCHAR(50),
    model VARCHAR(100),
    temperature FLOAT,

    -- Redaction only (CHAT-LAW-006)
    is_redacted BOOLEAN DEFAULT FALSE,
    redacted_at TIMESTAMPTZ,
    redacted_by VARCHAR(200),
    redaction_reason VARCHAR(500),

    -- Timestamp (NO updated_at - immutable!)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_messages_tenant_user ON chat_messages(tenant_id, user_id, created_at);

-- Trigger to prevent UPDATE on content (CHAT-LAW-006)
CREATE OR REPLACE FUNCTION prevent_message_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.content IS DISTINCT FROM NEW.content THEN
        RAISE EXCEPTION 'Cannot update message content. Messages are immutable.';
    END IF;
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        RAISE EXCEPTION 'Cannot update message role. Messages are immutable.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_message_immutability
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_update();

-- Trigger to prevent DELETE (CHAT-LAW-006)
CREATE OR REPLACE FUNCTION prevent_message_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot delete messages. Use redaction for compliance.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_no_delete
    BEFORE DELETE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_delete();

-- Trigger to update session stats
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions
    SET
        message_count = message_count + 1,
        last_message_at = NEW.created_at,
        updated_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_on_message
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_stats();

COMMENT ON TABLE chat_messages IS 'Chat messages - APPEND ONLY per CHAT-LAW-006';
```

### 5. User Facts (Semantic Memory)

```sql
-- User facts extracted from conversations
CREATE TABLE user_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,

    -- Fact content
    fact_type VARCHAR(50) NOT NULL CHECK (fact_type IN ('preference', 'knowledge', 'relationship', 'context', 'goal')),
    content TEXT NOT NULL,
    content_embedding BYTEA,  -- Serialized vector
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),

    -- Source tracking
    source_session_id UUID REFERENCES chat_sessions(id),
    source_message_id UUID REFERENCES chat_messages(id),
    extracted_at TIMESTAMPTZ DEFAULT NOW(),

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES user_facts(id),
    last_confirmed_at TIMESTAMPTZ,
    confirmation_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_facts_tenant_user ON user_facts(tenant_id, user_id);
CREATE INDEX idx_facts_type ON user_facts(fact_type);
CREATE INDEX idx_facts_active ON user_facts(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_facts_confidence ON user_facts(confidence DESC) WHERE is_active = TRUE;

COMMENT ON TABLE user_facts IS 'Semantic memory - user facts extracted from conversations';
COMMENT ON COLUMN user_facts.confidence IS 'Confidence score 0.0-1.0, decreases if contradicted';
```

### 6. Memory Timeline (Temporal Memory)

```sql
-- Time-based memory summaries
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
    summary_embedding BYTEA,
    topics JSONB,  -- [{"topic": "...", "count": N}, ...]
    session_count INTEGER,
    message_count INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (tenant_id, user_id, period_type, period_start)
);

CREATE INDEX idx_timeline_lookup ON memory_timeline(tenant_id, user_id, period_type, period_start DESC);

COMMENT ON TABLE memory_timeline IS 'Temporal memory - periodic summaries';
```

### 7. Embedding Cache

```sql
-- Embedding cache to avoid re-embedding
CREATE TABLE embedding_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,

    -- Content identification
    content_hash VARCHAR(64) NOT NULL,  -- SHA256 of content
    content_type VARCHAR(50) NOT NULL,  -- 'query', 'document', 'fact', 'session'

    -- Embedding data
    embedding_model VARCHAR(100) NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    embedding BYTEA NOT NULL,  -- Serialized vector

    -- Vector store reference
    qdrant_point_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL = never expires

    UNIQUE (tenant_id, content_hash, embedding_model)
);

CREATE INDEX idx_embedding_cache_lookup ON embedding_cache(tenant_id, content_hash, embedding_model);
CREATE INDEX idx_embedding_cache_expires ON embedding_cache(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE embedding_cache IS 'Cache for embeddings to avoid re-computation';
```

### 8. Sync Jobs

```sql
-- Knowledge sync job tracking
CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL REFERENCES tenant_knowledge_sources(id),

    -- Job status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Progress
    documents_total INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    vectors_created INTEGER DEFAULT 0,
    vectors_updated INTEGER DEFAULT 0,
    vectors_deleted INTEGER DEFAULT 0,

    -- Error tracking
    error_message TEXT,
    error_details JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sync_jobs_tenant ON sync_jobs(tenant_id, created_at DESC);
CREATE INDEX idx_sync_jobs_source ON sync_jobs(source_id, created_at DESC);
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status) WHERE status IN ('pending', 'running');

COMMENT ON TABLE sync_jobs IS 'Knowledge source sync job tracking';
```

---

## Migration Files

### 001_initial_schema.sql
- Creates tenants, tenant_knowledge_sources tables
- Creates basic indexes

### 002_chat_tables.sql
- Creates chat_sessions, chat_messages tables
- Creates immutability triggers
- Creates indexes

### 003_memory_tables.sql
- Creates user_facts, memory_timeline tables
- Creates embedding_cache table
- Creates indexes

### 004_sync_tables.sql
- Creates sync_jobs table
- Creates indexes

---

## Performance Considerations

### Partitioning for Large Tables

```sql
-- Partition chat_messages by month for large tenants
CREATE TABLE chat_messages (
    ...
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE chat_messages_2026_01 PARTITION OF chat_messages
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### Index Strategies

```sql
-- Partial indexes for active records
CREATE INDEX idx_sessions_active ON chat_sessions(tenant_id, user_id)
    WHERE is_active = TRUE AND is_deleted = FALSE;

-- BRIN indexes for time-series data
CREATE INDEX idx_messages_created_brin ON chat_messages USING BRIN (created_at);
```

---

## Backup Strategy

- Full backup: Daily
- WAL archiving: Continuous
- Point-in-time recovery: Enabled
- Retention: 30 days
