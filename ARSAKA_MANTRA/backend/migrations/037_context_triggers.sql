-- Migration: 037_context_triggers.sql
-- Purpose: Context triggers for automatic decision injection
-- Dynamic rules that inject decisions based on context conditions

-- ============================================================================
-- CONTEXT TRIGGERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_triggers (
    -- Primary key
    trigger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Condition (stored as JSONB)
    condition JSONB NOT NULL,

    -- What to inject
    decision_ids UUID[] DEFAULT '{}',
    bundle_ids UUID[] DEFAULT '{}',

    -- Configuration
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL' CHECK (priority IN (
        'CRITICAL',  -- Always evaluate first
        'HIGH',
        'NORMAL',
        'LOW'
    )),

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Limits
    max_tokens INT,

    -- Stats
    trigger_count INT NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,

    -- Audit
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- ============================================================================
-- TRIGGER TYPES ENUM (for documentation/validation)
-- ============================================================================
-- Stored in condition.trigger_type:
--   FILE_PATTERN   - Glob pattern on file path
--   CONTENT_MATCH  - Regex on file content
--   KEYWORD        - Keywords in query/context
--   SCOPE          - Scope path match
--   TAG            - Tag match
--   COMPOSITE      - AND/OR/NOT combination

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup for enabled triggers
CREATE INDEX IF NOT EXISTS idx_triggers_enabled
    ON context_triggers(enabled) WHERE enabled = TRUE;

-- Priority ordering
CREATE INDEX IF NOT EXISTS idx_triggers_priority
    ON context_triggers(priority);

-- JSONB condition queries
CREATE INDEX IF NOT EXISTS idx_triggers_condition
    ON context_triggers USING GIN(condition);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Trigger statistics
CREATE OR REPLACE VIEW trigger_stats AS
SELECT
    trigger_id,
    name,
    priority,
    enabled,
    trigger_count,
    last_triggered_at,
    array_length(decision_ids, 1) as decision_count,
    array_length(bundle_ids, 1) as bundle_count,
    condition->>'trigger_type' as trigger_type,
    created_at
FROM context_triggers
ORDER BY trigger_count DESC;

-- Active triggers by type
CREATE OR REPLACE VIEW triggers_by_type AS
SELECT
    condition->>'trigger_type' as trigger_type,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE enabled = TRUE) as enabled_count,
    SUM(trigger_count) as total_triggers
FROM context_triggers
GROUP BY condition->>'trigger_type';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Record trigger activation
CREATE OR REPLACE FUNCTION record_trigger_activation(p_trigger_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE context_triggers
    SET
        trigger_count = trigger_count + 1,
        last_triggered_at = NOW()
    WHERE trigger_id = p_trigger_id;
END;
$$ LANGUAGE plpgsql;

-- Get active triggers by priority
CREATE OR REPLACE FUNCTION get_active_triggers()
RETURNS TABLE (
    trigger_id UUID,
    name VARCHAR,
    condition JSONB,
    decision_ids UUID[],
    bundle_ids UUID[],
    priority VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.trigger_id,
        t.name,
        t.condition,
        t.decision_ids,
        t.bundle_ids,
        t.priority
    FROM context_triggers t
    WHERE t.enabled = TRUE
    ORDER BY
        CASE t.priority
            WHEN 'CRITICAL' THEN 0
            WHEN 'HIGH' THEN 1
            WHEN 'NORMAL' THEN 2
            WHEN 'LOW' THEN 3
        END;
END;
$$ LANGUAGE plpgsql;

-- Find triggers by scope (for pre-filtering)
CREATE OR REPLACE FUNCTION find_triggers_for_scope(p_scope_path TEXT)
RETURNS TABLE (
    trigger_id UUID,
    name VARCHAR,
    priority VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.trigger_id, t.name, t.priority
    FROM context_triggers t
    WHERE t.enabled = TRUE
      AND t.condition->>'trigger_type' = 'SCOPE'
      AND (
          t.condition->>'scope_path' = '*'
          OR t.condition->>'scope_path' = p_scope_path
          OR p_scope_path LIKE (t.condition->>'scope_path') || '.%'
      );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Update timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_trigger_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_context_trigger_updated
    BEFORE UPDATE ON context_triggers
    FOR EACH ROW
    EXECUTE FUNCTION update_trigger_timestamp();

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Example: React file trigger
-- INSERT INTO context_triggers (name, description, condition, decision_ids, created_by)
-- VALUES (
--     'React Component Files',
--     'Inject React decisions for .tsx files',
--     '{"trigger_type": "FILE_PATTERN", "pattern": "*.tsx"}'::jsonb,
--     ARRAY[]::uuid[],
--     'system'
-- );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE context_triggers IS
    'Dynamic rules for auto-injecting decisions based on context. '
    'Evaluated against file path, content, scope, keywords, etc.';

COMMENT ON COLUMN context_triggers.condition IS
    'JSONB condition with trigger_type and type-specific fields. '
    'Types: FILE_PATTERN, CONTENT_MATCH, KEYWORD, SCOPE, TAG, COMPOSITE';

COMMENT ON COLUMN context_triggers.priority IS
    'Evaluation priority. CRITICAL triggers are always evaluated first.';
