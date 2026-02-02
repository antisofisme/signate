-- Migration: 031_schema_v3_enhanced.sql
-- Description: Add cross-agent enhanced fields to decisions table
-- Author: Claude Code
-- Date: 2024-01-29
--
-- This migration adds all fields identified from cross-agent analysis:
-- Phase A: Amendment tracking, Constraint relations, Stale reference detection
-- Phase B: Structured blockers, Embedding lifecycle, Team adoption, Notifications
-- Phase C: Disambiguation, Query hints, Enhanced implementation, Rollback history
--
-- All new columns are NULLABLE for backward compatibility.

-- ============================================================================
-- Phase A: Amendment & Conflict Tracking
-- ============================================================================

-- Amendments (respects immutability principle)
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS amendments JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.amendments IS
    'Cross-agent: Amendments to decision that respect immutability. Array of {amendment_id, decision_id, amendment_type, field_path, previous_value, new_value, reason, amended_by, amended_at, requires_approval, approved_by, approved_at, is_active}';

-- Stale reference warnings
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS stale_reference_warnings JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.stale_reference_warnings IS
    'Cross-agent: Warnings about references to deprecated decisions. Array of {warning_id, referenced_decision_id, reference_type, successor_id, detected_at, acknowledged, resolution_action}';

-- ============================================================================
-- Phase B: Structured Blockers
-- ============================================================================

-- Structured blockers with category and severity
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS structured_blockers JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.structured_blockers IS
    'Cross-agent: Structured blockers. Array of {blocker_id, category, severity, description, root_cause, affected_teams, depends_on_decision_id, expected_resolution_date, resolved_at, resolution}';

-- ============================================================================
-- Phase B: Embedding Lifecycle Management
-- ============================================================================

-- Complete embedding metadata
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS embedding_metadata JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.embedding_metadata IS
    'Cross-agent: Embedding lifecycle metadata. Contains {model, model_version, dimensions, generated_at, content_hash, source_fields, status, stale_reason, reembedding_priority}';

-- ============================================================================
-- Phase B: Team Adoption Tracking
-- ============================================================================

-- Per-team adoption entries
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS team_adoptions JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.team_adoptions IS
    'Cross-agent: Per-team adoption tracking. Array of {team_id, team_name, status, progress_percentage, started_at, completed_at, target_date, contact_person, blocker_ids, opted_out_reason}';

-- Adoption targets
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS adoption_target JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.adoption_target IS
    'Cross-agent: Adoption goals. Contains {target_date, target_percentage, target_team_count, target_teams}';

-- Adoption timeline (historical snapshots)
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS adoption_timeline JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.adoption_timeline IS
    'Cross-agent: Historical adoption snapshots for trend analysis. Array of {snapshot_date, total_teams, adopted_teams, adoption_percentage, active_blockers}';

-- ============================================================================
-- Phase B: Notification Infrastructure
-- ============================================================================

-- Notification subscriptions
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS notification_subscriptions JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.notification_subscriptions IS
    'Cross-agent: Notification subscriptions. Array of {subscription_id, subscriber_type, subscriber_id, triggers, channels, filters, is_active}';

-- ============================================================================
-- Phase C: Disambiguation Support
-- ============================================================================

-- Disambiguation metadata
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS disambiguation JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.disambiguation IS
    'Cross-agent: Query disambiguation support. Contains {disambiguation_group, distinguishing_keywords, distinguishing_summary, clarifying_questions, popularity_rank, default_in_group}';

-- Query processing hints
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS query_hints JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.query_hints IS
    'Cross-agent: Query-side processing hints. Contains {intent_signals, query_expansions, trigger_phrases, required_context, exclude_context}';

-- ============================================================================
-- Phase C: Enhanced Implementation Guidance
-- ============================================================================

-- Enhanced implementation with structured steps
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS enhanced_implementation JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.enhanced_implementation IS
    'Cross-agent: Enhanced implementation guidance. Contains {estimated_effort, estimated_hours, prerequisites, prerequisite_decisions, prerequisite_tools, structured_steps, common_pitfalls, success_criteria, verification_commands, structured_rollback}';

-- Rollback history
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS rollback_history JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.rollback_history IS
    'Cross-agent: Past rollback events. Array of {rollback_id, trigger_event_id, reason, initiated_by, steps, verification_status, lessons_learned, prevention_measures, postmortem_url}';

-- ============================================================================
-- Phase C: Enhanced Stability Metadata
-- ============================================================================

-- Enhanced stability with per-team tracking
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS enhanced_stability JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.enhanced_stability IS
    'Cross-agent: Enhanced stability with team adoptions. Contains {stability_status, maturity_score, team_adoptions, adoption_target, adoption_timeline, blockers, aggregate_metrics}';

-- ============================================================================
-- Indexes: Phase A
-- ============================================================================

-- Index for active amendments
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_amendments_active
    ON decisions USING gin(amendments jsonb_path_ops)
    WHERE amendments IS NOT NULL AND jsonb_array_length(amendments) > 0;

-- Index for amendments requiring approval
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_amendments_pending
    ON decisions(decision_id)
    WHERE amendments IS NOT NULL
      AND jsonb_array_length(amendments) > 0;

-- Index for unacknowledged stale references
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_stale_refs
    ON decisions USING gin(stale_reference_warnings jsonb_path_ops)
    WHERE stale_reference_warnings IS NOT NULL
      AND jsonb_array_length(stale_reference_warnings) > 0;

-- ============================================================================
-- Indexes: Phase B
-- ============================================================================

-- Index for structured blockers
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_blockers
    ON decisions USING gin(structured_blockers jsonb_path_ops)
    WHERE structured_blockers IS NOT NULL
      AND jsonb_array_length(structured_blockers) > 0;

-- Index for blocker severity
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_critical_blockers
    ON decisions(decision_id)
    WHERE structured_blockers @> '[{"severity": "critical"}]'::jsonb;

-- Index for embedding status
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_embedding_status
    ON decisions((embedding_metadata->>'status'))
    WHERE embedding_metadata IS NOT NULL;

-- Index for stale embeddings
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_embedding_stale
    ON decisions(decision_id)
    WHERE embedding_metadata IS NOT NULL
      AND (embedding_metadata->>'status') IN ('stale', 'pending');

-- Index for team adoptions
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_team_adoptions
    ON decisions USING gin(team_adoptions jsonb_path_ops)
    WHERE team_adoptions IS NOT NULL
      AND jsonb_array_length(team_adoptions) > 0;

-- Index for adoption by status
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_adoption_incomplete
    ON decisions(decision_id)
    WHERE team_adoptions IS NOT NULL
      AND jsonb_array_length(team_adoptions) > 0;

-- Index for notification subscriptions
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_notifications
    ON decisions USING gin(notification_subscriptions jsonb_path_ops)
    WHERE notification_subscriptions IS NOT NULL
      AND jsonb_array_length(notification_subscriptions) > 0;

-- ============================================================================
-- Indexes: Phase C
-- ============================================================================

-- Index for disambiguation groups
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_disambiguation_group
    ON decisions((disambiguation->>'disambiguation_group'))
    WHERE disambiguation IS NOT NULL
      AND (disambiguation->>'disambiguation_group') IS NOT NULL;

-- Index for default in disambiguation group
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_disambiguation_default
    ON decisions(decision_id)
    WHERE disambiguation IS NOT NULL
      AND (disambiguation->>'default_in_group')::boolean = true;

-- Index for query trigger phrases
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_query_triggers
    ON decisions USING gin((query_hints->'trigger_phrases') jsonb_path_ops)
    WHERE query_hints IS NOT NULL
      AND (query_hints->'trigger_phrases') IS NOT NULL;

-- Index for enhanced implementation
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_enhanced_impl
    ON decisions((enhanced_implementation->>'estimated_effort'))
    WHERE enhanced_implementation IS NOT NULL;

-- Index for rollback history
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_rollback_history
    ON decisions USING gin(rollback_history jsonb_path_ops)
    WHERE rollback_history IS NOT NULL
      AND jsonb_array_length(rollback_history) > 0;

-- Index for enhanced stability
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_enhanced_stability
    ON decisions((enhanced_stability->>'stability_status'))
    WHERE enhanced_stability IS NOT NULL;

-- ============================================================================
-- Composite Indexes: Common Query Patterns
-- ============================================================================

-- Decisions needing attention (multiple criteria)
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_needs_attention
    ON decisions(created_at DESC)
    WHERE (embedding_metadata IS NOT NULL AND (embedding_metadata->>'status') IN ('stale', 'pending'))
       OR (structured_blockers IS NOT NULL AND jsonb_array_length(structured_blockers) > 0)
       OR (stale_reference_warnings IS NOT NULL AND jsonb_array_length(stale_reference_warnings) > 0);

-- Decisions with active adoptions in progress
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_adoption_active
    ON decisions(domain_id, created_at DESC)
    WHERE team_adoptions IS NOT NULL
      AND jsonb_array_length(team_adoptions) > 0;

-- Decisions with rollback potential (has rollback steps)
CREATE INDEX IF NOT EXISTS idx_decisions_v3e_has_rollback
    ON decisions(decision_id)
    WHERE enhanced_implementation IS NOT NULL
      AND (enhanced_implementation->'structured_rollback') IS NOT NULL
      AND jsonb_array_length(enhanced_implementation->'structured_rollback') > 0;

-- ============================================================================
-- Separate Tables for Cross-Decision Data
-- ============================================================================

-- Learning Paths (curriculum aggregation)
CREATE TABLE IF NOT EXISTS learning_paths (
    path_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_role VARCHAR(100) NOT NULL,
    target_level VARCHAR(50) DEFAULT 'INTERMEDIATE',
    ordered_decision_ids UUID[] NOT NULL,
    optional_decision_ids UUID[] DEFAULT ARRAY[]::UUID[],
    checkpoints JSONB DEFAULT '[]'::jsonb,
    estimated_total_hours FLOAT,
    recommended_pace VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE learning_paths IS
    'Cross-agent: Curated learning paths for onboarding and skill development';

CREATE INDEX IF NOT EXISTS idx_learning_paths_role
    ON learning_paths(target_role)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_learning_paths_decisions
    ON learning_paths USING gin(ordered_decision_ids);

-- Learner Progress (individual progress tracking)
CREATE TABLE IF NOT EXISTS learner_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learner_id VARCHAR(255) NOT NULL,
    path_id UUID NOT NULL REFERENCES learning_paths(path_id) ON DELETE CASCADE,
    completed_decision_ids UUID[] DEFAULT ARRAY[]::UUID[],
    current_decision_id UUID,
    progress_percentage INT DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    completed_checkpoints VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_minutes INT DEFAULT 0,
    UNIQUE(learner_id, path_id)
);

COMMENT ON TABLE learner_progress IS
    'Cross-agent: Individual learner progress through learning paths';

CREATE INDEX IF NOT EXISTS idx_learner_progress_learner
    ON learner_progress(learner_id);

CREATE INDEX IF NOT EXISTS idx_learner_progress_incomplete
    ON learner_progress(learner_id)
    WHERE completed_at IS NULL;

-- Expected Coverage Registry (gap analysis)
CREATE TABLE IF NOT EXISTS expected_coverage (
    coverage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id VARCHAR(10) NOT NULL,
    aspect_id VARCHAR(10) NOT NULL,
    expected_count INT DEFAULT 1 CHECK (expected_count >= 1),
    importance VARCHAR(20) DEFAULT 'important',
    topic_description TEXT NOT NULL,
    example_decisions TEXT[],
    responsible_team VARCHAR(255),
    responsible_person VARCHAR(255),
    target_date DATE,
    current_count INT DEFAULT 0,
    is_satisfied BOOLEAN DEFAULT false,
    matching_decision_ids UUID[] DEFAULT ARRAY[]::UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    notes TEXT
);

COMMENT ON TABLE expected_coverage IS
    'Cross-agent: Expected decision coverage for gap analysis';

CREATE INDEX IF NOT EXISTS idx_expected_coverage_domain_aspect
    ON expected_coverage(domain_id, aspect_id);

CREATE INDEX IF NOT EXISTS idx_expected_coverage_unsatisfied
    ON expected_coverage(domain_id, aspect_id)
    WHERE is_satisfied = false;

CREATE INDEX IF NOT EXISTS idx_expected_coverage_critical
    ON expected_coverage(domain_id)
    WHERE importance = 'critical' AND is_satisfied = false;

-- Coverage Gaps (identified gaps)
CREATE TABLE IF NOT EXISTS coverage_gaps (
    gap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expected_coverage_id UUID NOT NULL REFERENCES expected_coverage(coverage_id) ON DELETE CASCADE,
    domain_id VARCHAR(10) NOT NULL,
    aspect_id VARCHAR(10) NOT NULL,
    gap_description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL,
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by_decision_id UUID
);

COMMENT ON TABLE coverage_gaps IS
    'Cross-agent: Identified coverage gaps';

CREATE INDEX IF NOT EXISTS idx_coverage_gaps_unresolved
    ON coverage_gaps(domain_id, aspect_id)
    WHERE resolved_at IS NULL;

-- Notification Records (sent notifications)
CREATE TABLE IF NOT EXISTS notification_records (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL,
    trigger VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered BOOLEAN DEFAULT false,
    delivery_error TEXT,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    escalation_level INT DEFAULT 1,
    escalated_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE notification_records IS
    'Cross-agent: Record of sent notifications';

CREATE INDEX IF NOT EXISTS idx_notification_records_decision
    ON notification_records(decision_id, sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_notification_records_unacked
    ON notification_records(recipient)
    WHERE acknowledged = false AND delivered = true;

-- Escalation Paths (notification escalation)
CREATE TABLE IF NOT EXISTS escalation_paths (
    path_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    applicable_triggers VARCHAR[] NOT NULL,
    levels JSONB NOT NULL,
    auto_resolve_after_hours INT,
    require_acknowledgment BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE escalation_paths IS
    'Cross-agent: Escalation paths for critical notifications';

-- ============================================================================
-- Validation Function: Check enhanced schema compliance
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_decision_v3_enhanced(decision_data JSONB)
RETURNS TABLE(
    is_valid BOOLEAN,
    validation_errors TEXT[]
) AS $$
DECLARE
    errors TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check blocker severity enum
    IF decision_data->'structured_blockers' IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM jsonb_array_elements(decision_data->'structured_blockers') elem
            WHERE elem->>'severity' NOT IN ('low', 'medium', 'high', 'critical')
        ) THEN
            errors := array_append(errors, 'Invalid blocker severity value');
        END IF;
    END IF;

    -- Check blocker category enum
    IF decision_data->'structured_blockers' IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM jsonb_array_elements(decision_data->'structured_blockers') elem
            WHERE elem->>'category' NOT IN ('technical', 'resource', 'dependency', 'process', 'knowledge', 'priority', 'other')
        ) THEN
            errors := array_append(errors, 'Invalid blocker category value');
        END IF;
    END IF;

    -- Check embedding status enum
    IF decision_data->'embedding_metadata' IS NOT NULL
       AND decision_data->'embedding_metadata'->>'status' IS NOT NULL THEN
        IF decision_data->'embedding_metadata'->>'status' NOT IN
           ('pending', 'generating', 'current', 'stale', 'failed') THEN
            errors := array_append(errors, 'Invalid embedding status value');
        END IF;
    END IF;

    -- Check adoption status enum
    IF decision_data->'team_adoptions' IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM jsonb_array_elements(decision_data->'team_adoptions') elem
            WHERE elem->>'status' NOT IN ('not_started', 'evaluating', 'in_progress', 'partial', 'completed', 'opted_out')
        ) THEN
            errors := array_append(errors, 'Invalid adoption status value');
        END IF;
    END IF;

    -- Check amendment type enum
    IF decision_data->'amendments' IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM jsonb_array_elements(decision_data->'amendments') elem
            WHERE elem->>'amendment_type' NOT IN ('correction', 'enrichment', 'clarification', 'retraction')
        ) THEN
            errors := array_append(errors, 'Invalid amendment type value');
        END IF;
    END IF;

    RETURN QUERY SELECT
        array_length(errors, 1) IS NULL OR array_length(errors, 1) = 0,
        errors;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION validate_decision_v3_enhanced(JSONB) IS
    'Validates cross-agent enhanced fields in a decision JSONB object';

-- ============================================================================
-- View: Enhanced Decision Summary with Cross-Agent Fields
-- ============================================================================

CREATE OR REPLACE VIEW decisions_v3_enhanced_summary AS
SELECT
    d.decision_id,
    d.decision_code,
    d.domain_id,
    d.aspect_id,
    LEFT(d.statement, 100) as statement_preview,
    d.scope,
    d.blast_radius,
    d.version,
    d.created_at,

    -- Amendments
    COALESCE(jsonb_array_length(d.amendments), 0) as amendment_count,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.amendments, '[]'::jsonb)) elem
     WHERE (elem->>'is_active')::boolean = true
       AND (elem->>'requires_approval')::boolean = true
       AND (elem->>'approved_at') IS NULL) as pending_amendments,

    -- Stale references
    COALESCE(jsonb_array_length(d.stale_reference_warnings), 0) as stale_reference_count,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.stale_reference_warnings, '[]'::jsonb)) elem
     WHERE (elem->>'acknowledged')::boolean = false) as unacked_stale_refs,

    -- Blockers
    COALESCE(jsonb_array_length(d.structured_blockers), 0) as blocker_count,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.structured_blockers, '[]'::jsonb)) elem
     WHERE (elem->>'resolved_at') IS NULL) as active_blockers,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.structured_blockers, '[]'::jsonb)) elem
     WHERE (elem->>'severity') = 'critical'
       AND (elem->>'resolved_at') IS NULL) as critical_blockers,

    -- Embedding
    d.embedding_metadata->>'status' as embedding_status,
    d.embedding_metadata->>'model' as embedding_model,
    (d.embedding_metadata->>'generated_at')::timestamp as embedding_generated_at,

    -- Team adoption
    COALESCE(jsonb_array_length(d.team_adoptions), 0) as team_count,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.team_adoptions, '[]'::jsonb)) elem
     WHERE elem->>'status' = 'completed') as adopted_teams,
    (SELECT COUNT(*) FROM jsonb_array_elements(COALESCE(d.team_adoptions, '[]'::jsonb)) elem
     WHERE elem->>'status' IN ('in_progress', 'partial')) as in_progress_teams,

    -- Adoption target
    (d.adoption_target->>'target_date')::date as adoption_target_date,
    (d.adoption_target->>'target_percentage')::int as adoption_target_percentage,

    -- Disambiguation
    d.disambiguation->>'disambiguation_group' as disambiguation_group,
    (d.disambiguation->>'default_in_group')::boolean as is_default_in_group,

    -- Enhanced implementation
    d.enhanced_implementation->>'estimated_effort' as estimated_effort,
    (d.enhanced_implementation->>'estimated_hours')::float as estimated_hours,
    COALESCE(jsonb_array_length(d.enhanced_implementation->'structured_steps'), 0) as step_count,
    COALESCE(jsonb_array_length(d.enhanced_implementation->'structured_rollback'), 0) as rollback_step_count,

    -- Rollback history
    COALESCE(jsonb_array_length(d.rollback_history), 0) as rollback_count,

    -- Notifications
    COALESCE(jsonb_array_length(d.notification_subscriptions), 0) as subscriber_count,

    -- Enhanced stability
    d.enhanced_stability->>'stability_status' as enhanced_stability_status,
    (d.enhanced_stability->>'maturity_score')::int as enhanced_maturity_score,
    (d.enhanced_stability->>'adoption_count')::int as enhanced_adoption_count

FROM decisions d
ORDER BY d.created_at DESC;

COMMENT ON VIEW decisions_v3_enhanced_summary IS
    'Summary view of decisions with all cross-agent enhanced fields for dashboard queries';

-- ============================================================================
-- Grant permissions (adjust as needed for your setup)
-- ============================================================================

-- GRANT SELECT ON decisions_v3_enhanced_summary TO readonly_user;
-- GRANT SELECT, INSERT, UPDATE ON learning_paths TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON learner_progress TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON expected_coverage TO app_user;
-- GRANT SELECT, INSERT ON notification_records TO app_user;
-- GRANT EXECUTE ON FUNCTION validate_decision_v3_enhanced(JSONB) TO app_user;
