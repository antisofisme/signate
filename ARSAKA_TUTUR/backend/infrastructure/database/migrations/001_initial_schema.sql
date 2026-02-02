-- Migration: 001_initial_schema
-- Description: Create tenants and knowledge sources tables
-- Created: 2026-01-25
-- Complies: CHAT-LAW-004 (Multi-tenant), CHAT-LAW-006 (Append-only)

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- =============================================================================
-- TENANTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,

    -- AI Configuration (JSONB for flexibility)
    llm_config JSONB NOT NULL DEFAULT '{
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    }',
    embedding_config JSONB NOT NULL DEFAULT '{
        "provider": "openai",
        "model": "text-embedding-3-small",
        "dimensions": 1536
    }',
    rag_config JSONB NOT NULL DEFAULT '{
        "strategy": "hybrid",
        "reranker_enabled": false,
        "top_k": 5,
        "score_threshold": 0.3
    }',

    -- System Prompt
    system_prompt TEXT NOT NULL DEFAULT 'You are a helpful AI assistant.',
    persona_name VARCHAR(100) NOT NULL DEFAULT 'Assistant',

    -- Limits
    max_context_tokens INTEGER DEFAULT 8000,
    max_response_tokens INTEGER DEFAULT 1000,
    max_messages_per_session INTEGER DEFAULT 100,
    max_sessions_per_user INTEGER DEFAULT 50,

    -- Feature Flags
    features JSONB NOT NULL DEFAULT '{
        "memory_extraction": true,
        "temporal_memory": true,
        "streaming": true,
        "session_summarization": true
    }',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tenants IS 'Tenant registration and configuration';
COMMENT ON COLUMN tenants.llm_config IS 'LLM provider settings: {provider, model, temperature, max_tokens}';
COMMENT ON COLUMN tenants.embedding_config IS 'Embedding settings: {provider, model, dimensions}';
COMMENT ON COLUMN tenants.rag_config IS 'RAG pipeline settings: {strategy, reranker_enabled, top_k, score_threshold}';
COMMENT ON COLUMN tenants.features IS 'Feature flags: {memory_extraction, temporal_memory, streaming}';

-- =============================================================================
-- KNOWLEDGE SOURCES
-- =============================================================================

CREATE TABLE IF NOT EXISTS tenant_knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Source identification
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('database', 'api', 'file')),
    source_name VARCHAR(200) NOT NULL,

    -- Connection configuration
    -- For database: {table, fields[], filter, connection_string}
    -- For api: {url, headers, method, body_template}
    -- For file: {path, format, watch_changes}
    connection_config JSONB NOT NULL,

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

-- =============================================================================
-- UPDATE TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER knowledge_sources_updated_at
    BEFORE UPDATE ON tenant_knowledge_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
