-- Migration: 003_memory_tables
-- Description: Create memory system tables (semantic, temporal, cache)
-- Created: 2026-01-25
-- Complies: CHAT-LAW-003 (Memory Hierarchy), CHAT-LAW-004 (Multi-tenant)

-- =============================================================================
-- USER FACTS (SEMANTIC MEMORY)
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_facts (
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
CREATE INDEX idx_facts_type ON user_facts(tenant_id, user_id, fact_type);
CREATE INDEX idx_facts_active ON user_facts(tenant_id, user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_facts_confidence ON user_facts(confidence DESC) WHERE is_active = TRUE;

COMMENT ON TABLE user_facts IS 'Semantic memory - user facts extracted from conversations';
COMMENT ON COLUMN user_facts.confidence IS 'Confidence score 0.0-1.0, decreases if contradicted';
COMMENT ON COLUMN user_facts.superseded_by IS 'If fact was replaced by a newer fact, reference to replacement';

-- =============================================================================
-- MEMORY TIMELINE (TEMPORAL MEMORY)
-- =============================================================================

CREATE TABLE IF NOT EXISTS memory_timeline (
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

COMMENT ON TABLE memory_timeline IS 'Temporal memory - periodic summaries of user activity';

-- =============================================================================
-- EMBEDDING CACHE
-- =============================================================================

CREATE TABLE IF NOT EXISTS embedding_cache (
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

-- =============================================================================
-- SYNC JOBS
-- =============================================================================

CREATE TABLE IF NOT EXISTS sync_jobs (
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

-- =============================================================================
-- UPDATE TRIGGERS
-- =============================================================================

CREATE TRIGGER facts_updated_at
    BEFORE UPDATE ON user_facts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
