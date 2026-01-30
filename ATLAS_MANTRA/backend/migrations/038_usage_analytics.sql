-- Migration: 038_usage_analytics.sql
-- Purpose: Usage analytics for decision tracking
-- Tracks access patterns, feedback, and decision health

-- ============================================================================
-- USAGE EVENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS usage_events (
    -- Primary key
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event type
    event_type VARCHAR(20) NOT NULL CHECK (event_type IN (
        'VIEW',      -- Decision was viewed/retrieved
        'APPLY',     -- Decision was applied
        'SKIP',      -- Decision was skipped
        'FEEDBACK'   -- Explicit feedback given
    )),

    -- What was accessed
    decision_id UUID NOT NULL,
    decision_code VARCHAR(50),

    -- Context
    scope_path TEXT,
    query TEXT,
    file_path TEXT,

    -- Who & when
    user_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Additional data
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- FEEDBACK EVENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS feedback_events (
    -- Primary key
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was rated
    decision_id UUID NOT NULL,

    -- Feedback type
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN (
        'HELPFUL',       -- Decision was helpful
        'NOT_HELPFUL',   -- Decision was not helpful
        'OUTDATED',      -- Decision seems outdated
        'UNCLEAR',       -- Decision is unclear
        'WRONG_CONTEXT'  -- Wrong decision for context
    )),

    -- Optional details
    comment TEXT,
    context_scope TEXT,

    -- Who & when
    user_id TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- DECISION STATS TABLE (Aggregated)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_stats (
    -- Primary key
    decision_id UUID PRIMARY KEY,
    decision_code VARCHAR(50),

    -- Counts
    view_count INT NOT NULL DEFAULT 0,
    apply_count INT NOT NULL DEFAULT 0,
    skip_count INT NOT NULL DEFAULT 0,

    -- Feedback counts
    helpful_count INT NOT NULL DEFAULT 0,
    not_helpful_count INT NOT NULL DEFAULT 0,
    outdated_count INT NOT NULL DEFAULT 0,
    unclear_count INT NOT NULL DEFAULT 0,

    -- Timing
    first_access TIMESTAMPTZ,
    last_access TIMESTAMPTZ,
    last_feedback TIMESTAMPTZ,

    -- Computed (updated by trigger)
    health_status VARCHAR(20) DEFAULT 'NEW' CHECK (health_status IN (
        'HEALTHY',     -- Good usage, positive feedback
        'STALE',       -- No recent usage
        'UNDERUSED',   -- Lower than expected usage
        'PROBLEMATIC', -- Negative feedback
        'NEW'          -- Too new to evaluate
    )),

    -- Last computation
    stats_updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Usage events indexes
CREATE INDEX IF NOT EXISTS idx_usage_decision ON usage_events(decision_id);
CREATE INDEX IF NOT EXISTS idx_usage_type ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_scope ON usage_events(scope_path) WHERE scope_path IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_events(session_id) WHERE session_id IS NOT NULL;

-- Feedback indexes
CREATE INDEX IF NOT EXISTS idx_feedback_decision ON feedback_events(decision_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback_events(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback_events(timestamp);

-- Stats indexes
CREATE INDEX IF NOT EXISTS idx_stats_health ON decision_stats(health_status);
CREATE INDEX IF NOT EXISTS idx_stats_last_access ON decision_stats(last_access);
CREATE INDEX IF NOT EXISTS idx_stats_view_count ON decision_stats(view_count DESC);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Hot decisions (most viewed)
CREATE OR REPLACE VIEW hot_decisions AS
SELECT
    decision_id,
    decision_code,
    view_count,
    apply_count,
    CASE WHEN view_count > 0
        THEN ROUND(100.0 * apply_count / view_count, 1)
        ELSE 0
    END as apply_rate_pct,
    last_access,
    health_status
FROM decision_stats
WHERE view_count > 0
ORDER BY view_count DESC
LIMIT 100;

-- Stale decisions (no recent access)
CREATE OR REPLACE VIEW stale_decisions AS
SELECT
    decision_id,
    decision_code,
    view_count,
    last_access,
    EXTRACT(DAY FROM NOW() - last_access) as days_since_access,
    health_status
FROM decision_stats
WHERE last_access < NOW() - INTERVAL '90 days'
ORDER BY last_access ASC;

-- Problematic decisions (negative feedback)
CREATE OR REPLACE VIEW problematic_decisions AS
SELECT
    decision_id,
    decision_code,
    helpful_count,
    not_helpful_count,
    outdated_count,
    unclear_count,
    CASE WHEN (helpful_count + not_helpful_count) > 0
        THEN ROUND(100.0 * helpful_count / (helpful_count + not_helpful_count), 1)
        ELSE 50
    END as helpfulness_pct,
    last_feedback,
    health_status
FROM decision_stats
WHERE not_helpful_count + outdated_count + unclear_count > 0
ORDER BY (not_helpful_count + outdated_count + unclear_count) DESC;

-- Usage by scope
CREATE OR REPLACE VIEW usage_by_scope AS
SELECT
    scope_path,
    COUNT(*) as event_count,
    COUNT(DISTINCT decision_id) as unique_decisions,
    COUNT(DISTINCT user_id) as unique_users,
    MAX(timestamp) as last_activity
FROM usage_events
WHERE scope_path IS NOT NULL
GROUP BY scope_path
ORDER BY event_count DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Record a usage event and update stats
CREATE OR REPLACE FUNCTION record_usage_event(
    p_event_type VARCHAR,
    p_decision_id UUID,
    p_decision_code VARCHAR DEFAULT NULL,
    p_scope_path TEXT DEFAULT NULL,
    p_query TEXT DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    -- Insert event
    INSERT INTO usage_events (event_type, decision_id, decision_code, scope_path, query, user_id, session_id)
    VALUES (p_event_type, p_decision_id, p_decision_code, p_scope_path, p_query, p_user_id, p_session_id)
    RETURNING event_id INTO v_event_id;

    -- Update stats
    INSERT INTO decision_stats (decision_id, decision_code, first_access, last_access)
    VALUES (p_decision_id, p_decision_code, NOW(), NOW())
    ON CONFLICT (decision_id) DO UPDATE SET
        decision_code = COALESCE(EXCLUDED.decision_code, decision_stats.decision_code),
        last_access = NOW(),
        view_count = CASE WHEN p_event_type = 'VIEW' THEN decision_stats.view_count + 1 ELSE decision_stats.view_count END,
        apply_count = CASE WHEN p_event_type = 'APPLY' THEN decision_stats.apply_count + 1 ELSE decision_stats.apply_count END,
        skip_count = CASE WHEN p_event_type = 'SKIP' THEN decision_stats.skip_count + 1 ELSE decision_stats.skip_count END,
        stats_updated_at = NOW();

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- Record feedback and update stats
CREATE OR REPLACE FUNCTION record_feedback(
    p_decision_id UUID,
    p_feedback_type VARCHAR,
    p_comment TEXT DEFAULT NULL,
    p_context_scope TEXT DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_feedback_id UUID;
BEGIN
    -- Insert feedback
    INSERT INTO feedback_events (decision_id, feedback_type, comment, context_scope, user_id)
    VALUES (p_decision_id, p_feedback_type, p_comment, p_context_scope, p_user_id)
    RETURNING feedback_id INTO v_feedback_id;

    -- Update stats
    INSERT INTO decision_stats (decision_id, last_feedback)
    VALUES (p_decision_id, NOW())
    ON CONFLICT (decision_id) DO UPDATE SET
        last_feedback = NOW(),
        helpful_count = CASE WHEN p_feedback_type = 'HELPFUL' THEN decision_stats.helpful_count + 1 ELSE decision_stats.helpful_count END,
        not_helpful_count = CASE WHEN p_feedback_type = 'NOT_HELPFUL' THEN decision_stats.not_helpful_count + 1 ELSE decision_stats.not_helpful_count END,
        outdated_count = CASE WHEN p_feedback_type = 'OUTDATED' THEN decision_stats.outdated_count + 1 ELSE decision_stats.outdated_count END,
        unclear_count = CASE WHEN p_feedback_type = 'UNCLEAR' THEN decision_stats.unclear_count + 1 ELSE decision_stats.unclear_count END,
        stats_updated_at = NOW();

    RETURN v_feedback_id;
END;
$$ LANGUAGE plpgsql;

-- Recompute health status for all decisions
CREATE OR REPLACE FUNCTION recompute_health_status(p_stale_days INT DEFAULT 90)
RETURNS INT AS $$
DECLARE
    v_updated INT;
BEGIN
    UPDATE decision_stats
    SET health_status = CASE
        -- Problematic: more negative than positive feedback
        WHEN not_helpful_count + outdated_count > helpful_count THEN 'PROBLEMATIC'
        -- Stale: no recent access
        WHEN last_access < NOW() - (p_stale_days || ' days')::INTERVAL THEN 'STALE'
        -- Underused: low apply ratio with significant views
        WHEN view_count > 10 AND (apply_count::FLOAT / view_count) < 0.1 THEN 'UNDERUSED'
        -- New: recent first access
        WHEN first_access > NOW() - INTERVAL '7 days' THEN 'NEW'
        -- Healthy: default
        ELSE 'HEALTHY'
    END,
    stats_updated_at = NOW();

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated;
END;
$$ LANGUAGE plpgsql;

-- Get relevance boost based on usage
CREATE OR REPLACE FUNCTION get_relevance_boost(p_decision_id UUID)
RETURNS FLOAT AS $$
DECLARE
    v_stats decision_stats%ROWTYPE;
    v_boost FLOAT := 1.0;
    v_days_since_access INT;
    v_helpfulness FLOAT;
BEGIN
    SELECT * INTO v_stats FROM decision_stats WHERE decision_id = p_decision_id;

    IF NOT FOUND THEN
        RETURN 1.0;
    END IF;

    -- Recency factor
    v_days_since_access := EXTRACT(DAY FROM NOW() - COALESCE(v_stats.last_access, NOW() - INTERVAL '999 days'));
    IF v_days_since_access < 7 THEN
        v_boost := v_boost * 1.2;
    ELSIF v_days_since_access < 30 THEN
        v_boost := v_boost * 1.1;
    ELSIF v_days_since_access > 90 THEN
        v_boost := v_boost * 0.8;
    END IF;

    -- Helpfulness factor
    IF (v_stats.helpful_count + v_stats.not_helpful_count) > 5 THEN
        v_helpfulness := v_stats.helpful_count::FLOAT / (v_stats.helpful_count + v_stats.not_helpful_count);
        IF v_helpfulness > 0.8 THEN
            v_boost := v_boost * 1.3;
        ELSIF v_helpfulness > 0.6 THEN
            v_boost := v_boost * 1.1;
        ELSIF v_helpfulness < 0.3 THEN
            v_boost := v_boost * 0.7;
        END IF;
    END IF;

    RETURN v_boost;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULED MAINTENANCE
-- ============================================================================
-- Run periodically: SELECT recompute_health_status();
-- Consider partitioning usage_events by timestamp for large datasets

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE usage_events IS
    'Individual usage events for decision access tracking. '
    'Use for detailed analysis; aggregated stats in decision_stats.';

COMMENT ON TABLE feedback_events IS
    'Explicit user feedback on decisions. '
    'Used to identify problematic/outdated decisions.';

COMMENT ON TABLE decision_stats IS
    'Aggregated statistics per decision. '
    'Updated automatically via record_usage_event and record_feedback functions.';

COMMENT ON FUNCTION get_relevance_boost IS
    'Returns a multiplier (0.5-1.5) for search ranking based on usage patterns.';
