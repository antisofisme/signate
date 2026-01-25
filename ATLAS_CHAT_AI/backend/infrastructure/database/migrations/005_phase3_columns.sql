-- Migration: 005_phase3_columns
-- Description: Add columns needed for Phase 3 Memory System and Phase 4 Admin
-- Created: 2026-01-25

-- =============================================================================
-- CHAT_SESSIONS - Add memory processing columns
-- =============================================================================

-- Column to track when facts were extracted from session
ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS facts_extracted_at TIMESTAMPTZ;

-- Column to track when session was summarized
ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS summarized_at TIMESTAMPTZ;

-- Index for finding sessions that need processing
CREATE INDEX IF NOT EXISTS idx_sessions_facts_pending
ON chat_sessions(updated_at DESC)
WHERE facts_extracted_at IS NULL AND is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_sessions_summary_pending
ON chat_sessions(updated_at DESC)
WHERE summary IS NULL AND is_deleted = FALSE;

-- =============================================================================
-- API_KEYS - Add updated_at column
-- =============================================================================

ALTER TABLE api_keys
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- =============================================================================
-- TENANTS - Add missing columns if not present
-- =============================================================================

-- Make sure tenants has the required columns
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Update trigger for tenants
DROP TRIGGER IF EXISTS tenants_updated_at ON tenants;

CREATE TRIGGER tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- USER_FACTS - Add source tracking columns if not present
-- =============================================================================

ALTER TABLE user_facts
ADD COLUMN IF NOT EXISTS source_session_id UUID REFERENCES chat_sessions(id);

ALTER TABLE user_facts
ADD COLUMN IF NOT EXISTS source_message_id UUID REFERENCES chat_messages(id);

-- =============================================================================
-- AUDIT LOGS - Add anonymous actor type
-- =============================================================================

-- Update check constraint to include 'anonymous' actor type
ALTER TABLE audit_logs
DROP CONSTRAINT IF EXISTS audit_logs_actor_type_check;

ALTER TABLE audit_logs
ADD CONSTRAINT audit_logs_actor_type_check
CHECK (actor_type IN ('user', 'api_key', 'system', 'anonymous', 'jwt'));

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON COLUMN chat_sessions.facts_extracted_at IS 'When facts were extracted by background worker';
COMMENT ON COLUMN chat_sessions.summarized_at IS 'When session was summarized by background worker';
COMMENT ON COLUMN user_facts.source_session_id IS 'Session from which this fact was extracted';
COMMENT ON COLUMN user_facts.source_message_id IS 'Message from which this fact was extracted';
