-- Migration: 030_schema_v3_fields.sql
-- Description: Add schema v3 fields to decisions table
-- Author: Claude Code
-- Date: 2024-01-29
--
-- This migration adds new v3 columns to support:
-- - Knowledge Consumption (target_roles, audience_level, reading_time)
-- - Applicability Context (applies_when, auto_detect)
-- - Code Artifacts (linked PRs, commits, issues)
-- - Enhanced Search (semantic expansion, intent questions)
-- - Enhanced LLM (RAG optimization, embedding versioning)
-- - Causality (trigger_event)
-- - Implementation Status (progress tracking)
-- - Stability (maturity scoring)
-- - Impact Analysis (cached results)
-- - Usage Analytics (retrieval tracking)
--
-- All new columns are NULLABLE for backward compatibility.

-- ============================================================================
-- Phase 1: Knowledge Consumption & Context
-- ============================================================================

-- Knowledge consumption metadata
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS knowledge_consumption JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.knowledge_consumption IS
    'v3: Who should read and how to consume. Contains target_roles, audience_level, learning_objectives, prerequisites, reading_time_minutes';

-- Applicability context
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS applicability JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.applicability IS
    'v3: When this decision applies. Contains applies_when (context triggers), does_not_apply_when, auto_detect';

-- Code artifacts (traceability)
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS code_artifacts JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.code_artifacts IS
    'v3: Links to implementation artifacts (PRs, commits, issues). Array of {artifact_type, repository, reference, url, status, linked_at, linked_by}';

-- ============================================================================
-- Phase 2: Causality & Implementation Tracking
-- ============================================================================

-- Trigger event (causality context)
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS trigger_event JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.trigger_event IS
    'v3: Event that triggered this decision. Contains event_type, event_id, event_date, description, severity, event_url, related_decisions';

-- Implementation status
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS implementation_status JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.implementation_status IS
    'v3: Implementation progress tracking. Contains status, progress_percentage, started_at, completed_at, verified_at, blockers';

-- Stability metadata
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS stability JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.stability IS
    'v3: Stability and maturity indicator. Contains stability_status, maturity_score, deprecation_date, successor_id, adoption_count, feedback_score';

-- ============================================================================
-- Phase 3: Impact Analysis & Usage Analytics
-- ============================================================================

-- Persisted impact analysis
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS impact_analysis JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.impact_analysis IS
    'v3: Cached impact analysis results. Contains risk_score, risk_level, affected_decision_ids, dependency_depth, recommendations';

-- Usage analytics
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS usage_analytics JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.usage_analytics IS
    'v3: Usage tracking for optimization. Contains retrieval_count, successful_retrievals, common_queries, failed_queries, last_accessed_at';

-- ============================================================================
-- Indexes: Phase 1
-- ============================================================================

-- Index for knowledge consumption queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_target_roles
    ON decisions USING gin((knowledge_consumption->'target_roles') jsonb_path_ops)
    WHERE knowledge_consumption IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_audience_level
    ON decisions((knowledge_consumption->>'audience_level'))
    WHERE knowledge_consumption IS NOT NULL;

-- Index for applicability queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_auto_detect
    ON decisions((applicability->>'auto_detect')::boolean)
    WHERE applicability IS NOT NULL AND (applicability->>'auto_detect')::boolean = true;

-- Index for code artifact lookup
CREATE INDEX IF NOT EXISTS idx_decisions_v3_code_artifacts
    ON decisions USING gin(code_artifacts jsonb_path_ops)
    WHERE code_artifacts IS NOT NULL AND jsonb_array_length(code_artifacts) > 0;

-- ============================================================================
-- Indexes: Phase 2
-- ============================================================================

-- Index for trigger event queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_trigger_type
    ON decisions((trigger_event->>'event_type'))
    WHERE trigger_event IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_trigger_id
    ON decisions((trigger_event->>'event_id'))
    WHERE trigger_event IS NOT NULL AND trigger_event->>'event_id' IS NOT NULL;

-- Index for implementation status queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_impl_status
    ON decisions((implementation_status->>'status'))
    WHERE implementation_status IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_impl_progress
    ON decisions((implementation_status->>'progress_percentage')::int)
    WHERE implementation_status IS NOT NULL;

-- Index for stability queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_stability_status
    ON decisions((stability->>'stability_status'))
    WHERE stability IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_maturity_score
    ON decisions((stability->>'maturity_score')::int)
    WHERE stability IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_deprecated
    ON decisions(decision_id)
    WHERE stability IS NOT NULL AND (stability->>'stability_status') IN ('deprecated', 'archived');

-- ============================================================================
-- Indexes: Phase 3
-- ============================================================================

-- Index for impact analysis queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_risk_level
    ON decisions((impact_analysis->>'risk_level'))
    WHERE impact_analysis IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_risk_score
    ON decisions((impact_analysis->>'risk_score')::int)
    WHERE impact_analysis IS NOT NULL;

-- Index for usage analytics queries
CREATE INDEX IF NOT EXISTS idx_decisions_v3_retrieval_count
    ON decisions((usage_analytics->>'retrieval_count')::int DESC)
    WHERE usage_analytics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_v3_last_accessed
    ON decisions((usage_analytics->>'last_accessed_at')::timestamp)
    WHERE usage_analytics IS NOT NULL;

-- ============================================================================
-- Composite Indexes: Common Query Patterns
-- ============================================================================

-- Stable decisions by domain (common query)
CREATE INDEX IF NOT EXISTS idx_decisions_v3_stable_by_domain
    ON decisions(domain_id, created_at DESC)
    WHERE stability IS NULL
       OR (stability->>'stability_status') = 'stable';

-- Implemented decisions
CREATE INDEX IF NOT EXISTS idx_decisions_v3_implemented
    ON decisions(domain_id, aspect_id)
    WHERE implementation_status IS NOT NULL
      AND (implementation_status->>'status') IN ('completed', 'verified');

-- Decisions needing attention (deprecated or blocked)
CREATE INDEX IF NOT EXISTS idx_decisions_v3_needs_attention
    ON decisions(created_at DESC)
    WHERE (stability IS NOT NULL AND (stability->>'stability_status') = 'deprecated')
       OR (implementation_status IS NOT NULL AND jsonb_array_length(implementation_status->'blockers') > 0);

-- Popular decisions (high retrieval count)
CREATE INDEX IF NOT EXISTS idx_decisions_v3_popular
    ON decisions((usage_analytics->>'retrieval_count')::int DESC)
    WHERE usage_analytics IS NOT NULL
      AND (usage_analytics->>'retrieval_count')::int > 10;

-- ============================================================================
-- Update existing search_metadata to enhanced format (optional migration)
-- ============================================================================

-- This CTE migrates question_variants to the new questions structure
-- Run only if you have existing v2 data to migrate
/*
WITH migrated AS (
    SELECT
        decision_id,
        jsonb_build_object(
            'aliases', COALESCE(search_metadata->'aliases', '[]'::jsonb),
            'search_keywords', COALESCE(search_metadata->'search_keywords', '[]'::jsonb),
            'questions', jsonb_build_object(
                'how_questions', '[]'::jsonb,
                'why_questions', '[]'::jsonb,
                'what_questions', '[]'::jsonb,
                'when_questions', '[]'::jsonb,
                'negative_questions', '[]'::jsonb
            ),
            'semantic_expansion', NULL,
            'negative_keywords', '[]'::jsonb,
            'retrieval_boost', 1.0,
            'question_variants', COALESCE(search_metadata->'question_variants', '[]'::jsonb)
        ) as new_search_metadata
    FROM decisions
    WHERE search_metadata IS NOT NULL
      AND search_metadata->'questions' IS NULL
)
UPDATE decisions d
SET search_metadata = m.new_search_metadata
FROM migrated m
WHERE d.decision_id = m.decision_id;
*/

-- ============================================================================
-- Validation Function: Check v3 schema compliance
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_decision_v3(decision_data JSONB)
RETURNS TABLE(
    is_valid BOOLEAN,
    validation_errors TEXT[]
) AS $$
DECLARE
    errors TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check stability_status enum
    IF decision_data->'stability' IS NOT NULL
       AND decision_data->'stability'->>'stability_status' IS NOT NULL THEN
        IF decision_data->'stability'->>'stability_status' NOT IN
           ('experimental', 'alpha', 'beta', 'stable', 'deprecated', 'archived') THEN
            errors := array_append(errors, 'Invalid stability_status value');
        END IF;
    END IF;

    -- Check implementation status enum
    IF decision_data->'implementation_status' IS NOT NULL
       AND decision_data->'implementation_status'->>'status' IS NOT NULL THEN
        IF decision_data->'implementation_status'->>'status' NOT IN
           ('not_started', 'in_progress', 'partial', 'completed', 'verified', 'reverted') THEN
            errors := array_append(errors, 'Invalid implementation_status value');
        END IF;
    END IF;

    -- Check audience_level enum
    IF decision_data->'knowledge_consumption' IS NOT NULL
       AND decision_data->'knowledge_consumption'->>'audience_level' IS NOT NULL THEN
        IF decision_data->'knowledge_consumption'->>'audience_level' NOT IN
           ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT') THEN
            errors := array_append(errors, 'Invalid audience_level value');
        END IF;
    END IF;

    -- Check maturity_score range
    IF decision_data->'stability' IS NOT NULL
       AND decision_data->'stability'->>'maturity_score' IS NOT NULL THEN
        IF (decision_data->'stability'->>'maturity_score')::int NOT BETWEEN 0 AND 100 THEN
            errors := array_append(errors, 'maturity_score must be between 0 and 100');
        END IF;
    END IF;

    -- Check progress_percentage range
    IF decision_data->'implementation_status' IS NOT NULL
       AND decision_data->'implementation_status'->>'progress_percentage' IS NOT NULL THEN
        IF (decision_data->'implementation_status'->>'progress_percentage')::int NOT BETWEEN 0 AND 100 THEN
            errors := array_append(errors, 'progress_percentage must be between 0 and 100');
        END IF;
    END IF;

    RETURN QUERY SELECT
        array_length(errors, 1) IS NULL OR array_length(errors, 1) = 0,
        errors;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION validate_decision_v3(JSONB) IS
    'Validates v3-specific fields in a decision JSONB object';

-- ============================================================================
-- Helper Function: Auto-populate v3 defaults
-- ============================================================================

CREATE OR REPLACE FUNCTION populate_v3_defaults()
RETURNS TRIGGER AS $$
BEGIN
    -- Set default implementation_status if not provided
    IF NEW.implementation_status IS NULL THEN
        NEW.implementation_status := jsonb_build_object(
            'status', 'not_started',
            'progress_percentage', 0,
            'updated_at', NOW()
        );
    END IF;

    -- Set default stability if not provided
    IF NEW.stability IS NULL THEN
        NEW.stability := jsonb_build_object(
            'stability_status', 'stable',
            'maturity_score', 50,
            'adoption_count', 0
        );
    END IF;

    -- Set default usage_analytics if not provided
    IF NEW.usage_analytics IS NULL THEN
        NEW.usage_analytics := jsonb_build_object(
            'retrieval_count', 0,
            'successful_retrievals', 0,
            'common_queries', '[]'::jsonb,
            'failed_queries', '[]'::jsonb
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-populating defaults (optional - enable if desired)
-- DROP TRIGGER IF EXISTS trigger_populate_v3_defaults ON decisions;
-- CREATE TRIGGER trigger_populate_v3_defaults
--     BEFORE INSERT ON decisions
--     FOR EACH ROW
--     EXECUTE FUNCTION populate_v3_defaults();

-- ============================================================================
-- View: v3 Decision Summary
-- ============================================================================

CREATE OR REPLACE VIEW decisions_v3_summary AS
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

    -- Knowledge consumption
    d.knowledge_consumption->>'audience_level' as audience_level,
    d.knowledge_consumption->'target_roles' as target_roles,
    (d.knowledge_consumption->>'reading_time_minutes')::int as reading_time_minutes,

    -- Stability
    d.stability->>'stability_status' as stability_status,
    (d.stability->>'maturity_score')::int as maturity_score,

    -- Implementation
    d.implementation_status->>'status' as impl_status,
    (d.implementation_status->>'progress_percentage')::int as impl_progress,

    -- Impact
    d.impact_analysis->>'risk_level' as risk_level,
    (d.impact_analysis->>'affected_count')::int as affected_count,

    -- Usage
    (d.usage_analytics->>'retrieval_count')::int as retrieval_count,
    (d.usage_analytics->>'last_accessed_at')::timestamp as last_accessed_at,

    -- Code artifacts count
    COALESCE(jsonb_array_length(d.code_artifacts), 0) as code_artifact_count,

    -- Has trigger event
    d.trigger_event IS NOT NULL as has_trigger_event

FROM decisions d
ORDER BY d.created_at DESC;

COMMENT ON VIEW decisions_v3_summary IS
    'Summary view of decisions with v3 fields for quick dashboard queries';

-- ============================================================================
-- Grant permissions (adjust as needed for your setup)
-- ============================================================================

-- GRANT SELECT ON decisions_v3_summary TO readonly_user;
-- GRANT EXECUTE ON FUNCTION validate_decision_v3(JSONB) TO app_user;
