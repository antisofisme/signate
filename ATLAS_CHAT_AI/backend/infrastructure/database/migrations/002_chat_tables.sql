-- Migration: 002_chat_tables
-- Description: Create chat sessions and messages tables
-- Created: 2026-01-25
-- Complies: CHAT-LAW-004 (Multi-tenant), CHAT-LAW-006 (Append-only)

-- =============================================================================
-- CHAT SESSIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(200) NOT NULL,

    -- Session metadata
    title VARCHAR(500),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,

    -- Summary for long sessions (for retrieval)
    summary TEXT,
    summary_embedding BYTEA,  -- Serialized vector
    summary_updated_at TIMESTAMPTZ,

    -- Topics extracted from conversation
    topics JSONB DEFAULT '[]',

    -- Soft delete (CHAT-LAW-006 compliant - no hard delete)
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
CREATE INDEX idx_sessions_active ON chat_sessions(tenant_id, user_id, is_active, is_deleted)
    WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE chat_sessions IS 'Chat sessions - episodic memory container';
COMMENT ON COLUMN chat_sessions.summary_embedding IS 'Serialized embedding vector for session similarity search';

-- =============================================================================
-- CHAT MESSAGES (APPEND-ONLY per CHAT-LAW-006)
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
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

    -- Redaction only (CHAT-LAW-006 - no delete, only redact)
    is_redacted BOOLEAN DEFAULT FALSE,
    redacted_at TIMESTAMPTZ,
    redacted_by VARCHAR(200),
    redaction_reason VARCHAR(500),

    -- Timestamp (NO updated_at - messages are immutable!)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_messages_tenant_user ON chat_messages(tenant_id, user_id, created_at);

COMMENT ON TABLE chat_messages IS 'Chat messages - APPEND ONLY per CHAT-LAW-006';

-- =============================================================================
-- IMMUTABILITY TRIGGERS (CHAT-LAW-006)
-- =============================================================================

-- Prevent UPDATE on message content/role
CREATE OR REPLACE FUNCTION prevent_message_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow only redaction updates
    IF OLD.content IS DISTINCT FROM NEW.content AND NEW.is_redacted = FALSE THEN
        RAISE EXCEPTION 'Cannot update message content. Messages are immutable per CHAT-LAW-006.';
    END IF;
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        RAISE EXCEPTION 'Cannot update message role. Messages are immutable per CHAT-LAW-006.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_message_immutability
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_update();

-- Prevent DELETE on messages
CREATE OR REPLACE FUNCTION prevent_message_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot delete messages. Use redaction for compliance per CHAT-LAW-006.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_no_delete
    BEFORE DELETE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_delete();

-- =============================================================================
-- SESSION STATS UPDATE TRIGGER
-- =============================================================================

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

-- =============================================================================
-- SESSION UPDATE TRIGGER
-- =============================================================================

CREATE TRIGGER sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
