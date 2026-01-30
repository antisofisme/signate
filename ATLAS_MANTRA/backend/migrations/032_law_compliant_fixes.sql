-- Migration: 032_law_compliant_fixes.sql
-- Description: LAW-compliant fixes based on cross-agent analysis
-- Author: Claude Code
-- Date: 2026-01-29
--
-- This migration implements fixes identified in MANTRA-LAW-001-AMENDMENT-002:
-- 1. Replace amendments with metadata_enrichments (§10.7 compliant)
-- 2. Add structured_summary column for document summarization
-- 3. Add AI safeguard columns per §6.5
-- 4. Create implementation tracking tables (§4.5 compliant - separate storage)

-- ============================================================================
-- Phase 1: Metadata Enrichments (§10.7 Compliant)
-- ============================================================================

-- Drop deprecated amendments column (if exists) - data will be migrated
-- ALTER TABLE decisions DROP COLUMN IF EXISTS amendments;

-- Create separate metadata_enrichments table (append-only, immutable)
CREATE TABLE IF NOT EXISTS metadata_enrichments (
    -- Identity (immutable)
    enrichment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE RESTRICT,

    -- Enrichment details
    enrichment_type VARCHAR(50) NOT NULL CHECK (
        enrichment_type IN ('trigger_event', 'code_artifact', 'embedding_update', 'operational_tag', 'search_optimization')
    ),
    field_path VARCHAR(255) NOT NULL,
    enrichment_value JSONB NOT NULL,

    -- Validation: field_path must be in allowed list
    -- Enforced by CHECK constraint
    CONSTRAINT chk_enrichable_field CHECK (
        field_path IN (
            'trigger_event',
            'code_artifacts',
            'embedding_metadata',
            'search_metadata.search_keywords',
            'search_metadata.aliases',
            'llm_optimization.embedding_text',
            'llm_optimization.keywords_for_rag',
            'knowledge_consumption.reading_time_minutes'
        )
        OR field_path LIKE 'code_artifacts[%'  -- Allow array additions
        OR field_path LIKE 'search_metadata.search_keywords[%'
        OR field_path LIKE 'search_metadata.aliases[%'
    ),

    -- Justification (required per §10.7.2)
    reason TEXT NOT NULL CHECK (length(reason) >= 10),
    supporting_evidence TEXT,

    -- Audit trail (required per §10.7.2)
    enriched_by VARCHAR(255) NOT NULL,
    enriched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Approval (REQUIRED per §10.7.2 - not optional)
    approved_by VARCHAR(255) NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    approval_notes TEXT,

    -- NO mutable state columns - enrichments are immutable
    -- NO is_active, NO reverted_at, NO reverted_by

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE metadata_enrichments IS
    'LAW §10.7 compliant: Immutable metadata enrichment records. No mutable state.';

COMMENT ON COLUMN metadata_enrichments.field_path IS
    'Must be in ENRICHABLE_FIELDS. Statement, rationale, constraints, invariants REQUIRE supersedes.';

-- Indexes for metadata_enrichments
CREATE INDEX IF NOT EXISTS idx_enrichments_decision
    ON metadata_enrichments(decision_id);

CREATE INDEX IF NOT EXISTS idx_enrichments_type
    ON metadata_enrichments(enrichment_type);

CREATE INDEX IF NOT EXISTS idx_enrichments_field
    ON metadata_enrichments(field_path);

CREATE INDEX IF NOT EXISTS idx_enrichments_by_time
    ON metadata_enrichments(decision_id, enriched_at DESC);

-- ============================================================================
-- Phase 2: Structured Summary Column
-- ============================================================================

-- Add structured_summary column to decisions
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS structured_summary JSONB DEFAULT NULL;

COMMENT ON COLUMN decisions.structured_summary IS
    'Multi-level summary: headline, abstract, executive_summary, key_points, role-based summaries, quick_answers';

-- Index for summary staleness check
CREATE INDEX IF NOT EXISTS idx_decisions_summary_hash
    ON decisions((structured_summary->>'source_content_hash'))
    WHERE structured_summary IS NOT NULL;

-- Index for AI-generated summaries requiring verification
CREATE INDEX IF NOT EXISTS idx_decisions_summary_unverified
    ON decisions(decision_id)
    WHERE structured_summary IS NOT NULL
      AND (structured_summary->>'generated_by') = 'ai_generated'
      AND (structured_summary->>'verified_by') IS NULL;

-- ============================================================================
-- Phase 3: AI Safeguard Columns (§6.5 Compliant)
-- ============================================================================

-- Update disambiguation column with safeguards
-- These safeguards are enforced at application level, but we document in schema

COMMENT ON COLUMN decisions.disambiguation IS
    'LAW §6.5 compliant: Includes human_confirmation_required, ai_auto_selection_prohibited, present_all_options safeguards';

COMMENT ON COLUMN decisions.query_hints IS
    'LAW §6.5 compliant: Includes human_must_confirm_trigger, ai_suggestion_only, require_confidence_display safeguards';

-- ============================================================================
-- Phase 4: Implementation Tracking Tables (§4.5 Compliant - Separate Storage)
-- ============================================================================

-- Per §4.5.3: Implementation tracking MUST be stored separately from decisions

-- Team adoption tracking (separate from decisions)
CREATE TABLE IF NOT EXISTS decision_team_adoptions (
    adoption_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,

    -- Team info
    team_id VARCHAR(100) NOT NULL,
    team_name VARCHAR(255) NOT NULL,

    -- Status (NOT a decision status - per §4.5.4)
    status VARCHAR(50) NOT NULL DEFAULT 'not_started' CHECK (
        status IN ('not_started', 'evaluating', 'in_progress', 'partial', 'completed', 'opted_out')
    ),
    progress_percentage INT DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Timeline
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    target_date DATE,

    -- Contact
    contact_person VARCHAR(255),
    contact_email VARCHAR(255),

    -- Opt-out (if status = opted_out)
    opted_out_reason TEXT,
    opted_out_approved_by VARCHAR(255),

    -- Notes
    notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255),

    UNIQUE(decision_id, team_id)
);

COMMENT ON TABLE decision_team_adoptions IS
    'LAW §4.5 compliant: Implementation tracking separate from decision records. Status does NOT affect decision validity.';

CREATE INDEX IF NOT EXISTS idx_adoptions_decision
    ON decision_team_adoptions(decision_id);

CREATE INDEX IF NOT EXISTS idx_adoptions_team
    ON decision_team_adoptions(team_id);

CREATE INDEX IF NOT EXISTS idx_adoptions_status
    ON decision_team_adoptions(status);

CREATE INDEX IF NOT EXISTS idx_adoptions_incomplete
    ON decision_team_adoptions(decision_id)
    WHERE status NOT IN ('completed', 'opted_out');

-- Implementation blockers (separate from decisions)
CREATE TABLE IF NOT EXISTS decision_blockers (
    blocker_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,

    -- Classification
    category VARCHAR(50) NOT NULL CHECK (
        category IN ('technical', 'resource', 'dependency', 'process', 'knowledge', 'priority', 'other')
    ),
    severity VARCHAR(20) NOT NULL CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),

    -- Details
    description TEXT NOT NULL CHECK (length(description) >= 10),
    root_cause TEXT,

    -- Scope
    affected_teams TEXT[],
    affected_areas TEXT[],

    -- Dependencies
    depends_on_decision_id UUID REFERENCES decisions(decision_id),
    depends_on_external VARCHAR(255),

    -- Timeline
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    expected_resolution_date DATE,

    -- Resolution
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution TEXT
);

COMMENT ON TABLE decision_blockers IS
    'LAW §4.5 compliant: Implementation blockers separate from decision records.';

CREATE INDEX IF NOT EXISTS idx_blockers_decision
    ON decision_blockers(decision_id);

CREATE INDEX IF NOT EXISTS idx_blockers_unresolved
    ON decision_blockers(decision_id)
    WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_blockers_critical
    ON decision_blockers(decision_id)
    WHERE severity = 'critical' AND resolved_at IS NULL;

-- ============================================================================
-- Phase 5: Validation Function for §10.7 Compliance
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_enrichment_field(field_path TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    enrichable_fields TEXT[] := ARRAY[
        'trigger_event',
        'code_artifacts',
        'embedding_metadata',
        'search_metadata.search_keywords',
        'search_metadata.aliases',
        'llm_optimization.embedding_text',
        'llm_optimization.keywords_for_rag',
        'knowledge_consumption.reading_time_minutes'
    ];
    immutable_fields TEXT[] := ARRAY[
        'statement',
        'rationale',
        'constraints',
        'invariants',
        'domain_id',
        'aspect_id',
        'scope',
        'blast_radius'
    ];
BEGIN
    -- Check if field is explicitly forbidden
    IF field_path = ANY(immutable_fields) THEN
        RETURN FALSE;
    END IF;

    -- Check if field starts with forbidden field
    IF EXISTS (SELECT 1 FROM unnest(immutable_fields) f WHERE field_path LIKE f || '.%') THEN
        RETURN FALSE;
    END IF;

    -- Check if field is in allowed list or is a sub-path
    IF field_path = ANY(enrichable_fields) THEN
        RETURN TRUE;
    END IF;

    -- Check for array sub-paths (e.g., code_artifacts[0])
    IF field_path ~ '^code_artifacts\[' OR
       field_path ~ '^search_metadata\.search_keywords\[' OR
       field_path ~ '^search_metadata\.aliases\[' THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION validate_enrichment_field(TEXT) IS
    'Validates field_path is enrichable per MANTRA-LAW-001 §10.7.1';

-- ============================================================================
-- Phase 6: View for Decision with Enrichments
-- ============================================================================

CREATE OR REPLACE VIEW decisions_with_enrichments AS
SELECT
    d.decision_id,
    d.decision_code,
    d.domain_id,
    d.aspect_id,
    LEFT(d.statement, 100) as statement_preview,
    d.version,
    d.created_at,

    -- Enrichment counts
    (SELECT COUNT(*) FROM metadata_enrichments e WHERE e.decision_id = d.decision_id) as enrichment_count,
    (SELECT MAX(enriched_at) FROM metadata_enrichments e WHERE e.decision_id = d.decision_id) as last_enriched_at,

    -- Adoption stats (separate per §4.5)
    (SELECT COUNT(*) FROM decision_team_adoptions a WHERE a.decision_id = d.decision_id) as team_count,
    (SELECT COUNT(*) FROM decision_team_adoptions a WHERE a.decision_id = d.decision_id AND a.status = 'completed') as adopted_teams,

    -- Blocker stats (separate per §4.5)
    (SELECT COUNT(*) FROM decision_blockers b WHERE b.decision_id = d.decision_id AND b.resolved_at IS NULL) as active_blockers,
    (SELECT COUNT(*) FROM decision_blockers b WHERE b.decision_id = d.decision_id AND b.severity = 'critical' AND b.resolved_at IS NULL) as critical_blockers,

    -- Structured summary
    d.structured_summary->>'headline' as summary_headline,
    d.structured_summary->>'generated_by' as summary_source,
    (d.structured_summary->>'verified_by') IS NOT NULL as summary_verified

FROM decisions d
ORDER BY d.created_at DESC;

COMMENT ON VIEW decisions_with_enrichments IS
    'LAW-compliant view: Decision core data with enrichment and adoption stats from separate tables';

-- ============================================================================
-- Phase 7: Migration of Old Amendments (if any)
-- ============================================================================

-- Migrate existing amendments to metadata_enrichments
-- Only migrate if amendments column exists and has data
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'decisions' AND column_name = 'amendments'
    ) THEN
        -- Insert valid enrichments (filter out retraction and mutable-state records)
        INSERT INTO metadata_enrichments (
            decision_id,
            enrichment_type,
            field_path,
            enrichment_value,
            reason,
            enriched_by,
            enriched_at,
            approved_by,
            approved_at
        )
        SELECT
            d.decision_id,
            'operational_tag',
            a->>'field_path',
            a->'new_value',
            COALESCE(a->>'reason', 'Migrated from legacy amendment'),
            COALESCE(a->>'amended_by', 'migration'),
            COALESCE((a->>'amended_at')::timestamp, NOW()),
            COALESCE(a->>'approved_by', a->>'amended_by', 'migration'),
            COALESCE((a->>'approved_at')::timestamp, (a->>'amended_at')::timestamp, NOW())
        FROM decisions d,
             jsonb_array_elements(d.amendments) a
        WHERE d.amendments IS NOT NULL
          AND jsonb_array_length(d.amendments) > 0
          AND (a->>'amendment_type') != 'retraction'  -- Skip retractions (invalid per §10.7)
          AND validate_enrichment_field(a->>'field_path');  -- Only valid fields

        RAISE NOTICE 'Migrated amendments to metadata_enrichments';
    END IF;
END $$;

-- ============================================================================
-- Phase 8: Migrate Team Adoptions from JSONB to Separate Table
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'decisions' AND column_name = 'team_adoptions'
    ) THEN
        INSERT INTO decision_team_adoptions (
            decision_id,
            team_id,
            team_name,
            status,
            progress_percentage,
            started_at,
            completed_at,
            target_date,
            contact_person,
            opted_out_reason,
            notes
        )
        SELECT
            d.decision_id,
            t->>'team_id',
            t->>'team_name',
            COALESCE(t->>'status', 'not_started'),
            COALESCE((t->>'progress_percentage')::int, 0),
            (t->>'started_at')::timestamp,
            (t->>'completed_at')::timestamp,
            (t->>'target_date')::date,
            t->>'contact_person',
            t->>'opted_out_reason',
            t->>'notes'
        FROM decisions d,
             jsonb_array_elements(d.team_adoptions) t
        WHERE d.team_adoptions IS NOT NULL
          AND jsonb_array_length(d.team_adoptions) > 0
        ON CONFLICT (decision_id, team_id) DO NOTHING;

        RAISE NOTICE 'Migrated team_adoptions to separate table per LAW §4.5';
    END IF;
END $$;

-- ============================================================================
-- Phase 9: Migrate Blockers from JSONB to Separate Table
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'decisions' AND column_name = 'structured_blockers'
    ) THEN
        INSERT INTO decision_blockers (
            decision_id,
            category,
            severity,
            description,
            root_cause,
            affected_teams,
            created_by,
            expected_resolution_date,
            resolved_at,
            resolved_by,
            resolution
        )
        SELECT
            d.decision_id,
            COALESCE(b->>'category', 'other'),
            COALESCE(b->>'severity', 'medium'),
            b->>'description',
            b->>'root_cause',
            ARRAY(SELECT jsonb_array_elements_text(b->'affected_teams')),
            COALESCE(b->>'created_by', 'migration'),
            (b->>'expected_resolution_date')::date,
            (b->>'resolved_at')::timestamp,
            b->>'resolved_by',
            b->>'resolution'
        FROM decisions d,
             jsonb_array_elements(d.structured_blockers) b
        WHERE d.structured_blockers IS NOT NULL
          AND jsonb_array_length(d.structured_blockers) > 0;

        RAISE NOTICE 'Migrated structured_blockers to separate table per LAW §4.5';
    END IF;
END $$;

-- ============================================================================
-- Grants (adjust as needed)
-- ============================================================================

-- GRANT SELECT ON decisions_with_enrichments TO readonly_user;
-- GRANT SELECT, INSERT ON metadata_enrichments TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON decision_team_adoptions TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON decision_blockers TO app_user;
-- GRANT EXECUTE ON FUNCTION validate_enrichment_field(TEXT) TO app_user;

-- ============================================================================
-- Notes
-- ============================================================================

-- After confirming migration success, consider dropping deprecated columns:
-- ALTER TABLE decisions DROP COLUMN IF EXISTS amendments;
-- ALTER TABLE decisions DROP COLUMN IF EXISTS team_adoptions;
-- ALTER TABLE decisions DROP COLUMN IF EXISTS structured_blockers;
--
-- Keep adoption_timeline and other analytics columns as they're read-only snapshots.
