-- Migration: 033_lifecycle_events.sql
-- Purpose: Create lifecycle_events table for tracking decision status changes
-- Per MANTRA-LAW-001 §2.3: Decisions are append-only, status tracked separately

-- ============================================================================
-- LIFECYCLE EVENTS TABLE
-- ============================================================================
-- This table stores immutable events that track lifecycle state changes.
-- The current status of a decision is COMPUTED from the latest event.
-- This preserves decision immutability while allowing status tracking.

CREATE TABLE IF NOT EXISTS lifecycle_events (
    -- Primary key
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Decision reference
    decision_id UUID NOT NULL,

    -- Status transition
    status VARCHAR(20) NOT NULL CHECK (status IN ('DRAFT', 'REVIEW', 'APPROVED', 'DEPRECATED')),
    previous_status VARCHAR(20) CHECK (previous_status IN ('DRAFT', 'REVIEW', 'APPROVED', 'DEPRECATED', NULL)),

    -- Who made the change (REQUIRED per LAW §6 - human authority)
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Reason for transition
    reason VARCHAR(50) NOT NULL DEFAULT 'OTHER',
    reason_detail TEXT,

    -- Gate validation reference (if transition from gate approval)
    gate_result_id UUID,

    -- Audit metadata
    client_ip INET,
    user_agent TEXT,

    -- Ensure decision exists (soft reference - decision might be in different table)
    -- CONSTRAINT fk_decision FOREIGN KEY (decision_id) REFERENCES decisions(decision_id)

    -- Note: We don't enforce FK here because decisions table structure varies
    -- Validation should be done at application level

    CONSTRAINT valid_reason CHECK (reason IN (
        'READY_FOR_REVIEW',
        'REVIEW_PASSED',
        'GATE_VALIDATION_PASSED',
        'REVIEW_REJECTED',
        'NEEDS_REVISION',
        'SUPERSEDED',
        'OBSOLETE',
        'SECURITY_ISSUE',
        'MANUAL_OVERRIDE',
        'OTHER'
    ))
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by decision
CREATE INDEX IF NOT EXISTS idx_lifecycle_decision_id
    ON lifecycle_events(decision_id);

-- Fast lookup by status (for "get all REVIEW decisions")
CREATE INDEX IF NOT EXISTS idx_lifecycle_status
    ON lifecycle_events(status);

-- Fast lookup by change time (for recent activity)
CREATE INDEX IF NOT EXISTS idx_lifecycle_changed_at
    ON lifecycle_events(changed_at DESC);

-- Composite for getting latest event per decision
CREATE INDEX IF NOT EXISTS idx_lifecycle_decision_time
    ON lifecycle_events(decision_id, changed_at DESC);

-- ============================================================================
-- VIEW: Current status per decision
-- ============================================================================

CREATE OR REPLACE VIEW decision_current_status AS
WITH latest_events AS (
    SELECT
        decision_id,
        status,
        changed_by,
        changed_at,
        reason,
        ROW_NUMBER() OVER (PARTITION BY decision_id ORDER BY changed_at DESC) as rn
    FROM lifecycle_events
)
SELECT
    decision_id,
    status as current_status,
    changed_by as last_changed_by,
    changed_at as last_changed_at,
    reason as last_reason,
    -- Computed flags
    (status = 'DRAFT') as is_editable,
    (status = 'APPROVED') as is_enforceable,
    (status = 'DEPRECATED') as is_deprecated
FROM latest_events
WHERE rn = 1;

-- ============================================================================
-- FUNCTION: Get valid transitions for a status
-- ============================================================================

CREATE OR REPLACE FUNCTION get_valid_transitions(current_status VARCHAR(20))
RETURNS VARCHAR(20)[] AS $$
BEGIN
    RETURN CASE current_status
        WHEN 'DRAFT' THEN ARRAY['REVIEW']
        WHEN 'REVIEW' THEN ARRAY['APPROVED', 'DRAFT']
        WHEN 'APPROVED' THEN ARRAY['DEPRECATED']
        WHEN 'DEPRECATED' THEN ARRAY[]::VARCHAR(20)[]
        ELSE ARRAY[]::VARCHAR(20)[]
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: Validate transition
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_lifecycle_transition()
RETURNS TRIGGER AS $$
DECLARE
    current_status VARCHAR(20);
    valid_targets VARCHAR(20)[];
BEGIN
    -- Get current status for this decision
    SELECT status INTO current_status
    FROM lifecycle_events
    WHERE decision_id = NEW.decision_id
    ORDER BY changed_at DESC
    LIMIT 1;

    -- If no existing events, only DRAFT is valid
    IF current_status IS NULL THEN
        IF NEW.status != 'DRAFT' THEN
            RAISE EXCEPTION 'First lifecycle event must be DRAFT, got %', NEW.status;
        END IF;
        RETURN NEW;
    END IF;

    -- Set previous_status
    NEW.previous_status := current_status;

    -- Validate transition
    valid_targets := get_valid_transitions(current_status);

    IF NOT (NEW.status = ANY(valid_targets)) THEN
        RAISE EXCEPTION 'Invalid transition: % -> %. Valid targets: %',
            current_status, NEW.status, valid_targets;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Validate transitions on insert
-- ============================================================================

DROP TRIGGER IF EXISTS trg_validate_lifecycle ON lifecycle_events;

CREATE TRIGGER trg_validate_lifecycle
    BEFORE INSERT ON lifecycle_events
    FOR EACH ROW
    EXECUTE FUNCTION validate_lifecycle_transition();

-- ============================================================================
-- HELPER: Initialize lifecycle for a decision
-- ============================================================================

CREATE OR REPLACE FUNCTION initialize_decision_lifecycle(
    p_decision_id UUID,
    p_created_by TEXT
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    -- Check if already initialized
    IF EXISTS (SELECT 1 FROM lifecycle_events WHERE decision_id = p_decision_id) THEN
        RAISE EXCEPTION 'Decision % already has lifecycle events', p_decision_id;
    END IF;

    -- Insert initial DRAFT event
    INSERT INTO lifecycle_events (decision_id, status, changed_by, reason, reason_detail)
    VALUES (p_decision_id, 'DRAFT', p_created_by, 'OTHER', 'Initial creation')
    RETURNING event_id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- HELPER: Transition a decision
-- ============================================================================

CREATE OR REPLACE FUNCTION transition_decision_lifecycle(
    p_decision_id UUID,
    p_target_status VARCHAR(20),
    p_changed_by TEXT,
    p_reason VARCHAR(50) DEFAULT 'OTHER',
    p_reason_detail TEXT DEFAULT NULL,
    p_gate_result_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO lifecycle_events (
        decision_id,
        status,
        changed_by,
        reason,
        reason_detail,
        gate_result_id
    )
    VALUES (
        p_decision_id,
        p_target_status,
        p_changed_by,
        p_reason,
        p_reason_detail,
        p_gate_result_id
    )
    RETURNING event_id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE lifecycle_events IS
    'Append-only audit trail of decision lifecycle state changes. '
    'Current status is computed from latest event per decision.';

COMMENT ON VIEW decision_current_status IS
    'Computed current lifecycle status for each decision. '
    'Use this view to query current status efficiently.';

COMMENT ON FUNCTION initialize_decision_lifecycle IS
    'Initialize lifecycle for a new decision (creates DRAFT event).';

COMMENT ON FUNCTION transition_decision_lifecycle IS
    'Transition a decision to a new lifecycle status. '
    'Validates transition is allowed, creates audit event.';
