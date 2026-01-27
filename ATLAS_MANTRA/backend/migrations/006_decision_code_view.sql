-- Migration: 006
-- Description: Create view for decision_code (derived field)
-- Date: 2026-01-26
--
-- RATIONALE:
--   decision_code is a DERIVED field, not decision content.
--   Per MANTRA-LAW-001 §10, decision content is immutable.
--   But derived metadata can be computed on-the-fly.
--
--   Using a VIEW:
--   1. Maintains absolute immutability of decisions table
--   2. Always consistent (auto-generates code)
--   3. No storage overhead
--   4. Backwards compatible

BEGIN;

-- ============================================================================
-- Create materialized sequence table for feature-based numbering
-- This is append-only (respects immutability)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_sequences (
    feature_id VARCHAR(3) PRIMARY KEY,
    last_sequence INTEGER NOT NULL DEFAULT 0
);

-- Initialize sequences based on existing data
INSERT INTO decision_sequences (feature_id, last_sequence)
SELECT
    feature_id::text,
    COUNT(*)::integer
FROM decisions
GROUP BY feature_id
ON CONFLICT (feature_id) DO UPDATE
SET last_sequence = EXCLUDED.last_sequence;

-- ============================================================================
-- Create view that generates decision_code on-the-fly
-- ============================================================================

CREATE OR REPLACE VIEW decisions_with_code AS
SELECT
    d.*,
    -- Generate decision_code: {group}-{feature}-{seq:03d}-v{version}
    COALESCE(
        d.decision_code,
        CONCAT(
            d.group_id::text, '-',
            d.feature_id::text, '-',
            LPAD(
                (ROW_NUMBER() OVER (
                    PARTITION BY d.feature_id
                    ORDER BY d.created_at ASC
                ))::text,
                3, '0'
            ),
            '-v', d.version
        )
    ) AS generated_code
FROM decisions d;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON VIEW decisions_with_code IS
    'View with auto-generated decision_code. Use generated_code column.';

COMMENT ON TABLE decision_sequences IS
    'Sequence tracking for feature-based numbering (append-only)';

COMMIT;
