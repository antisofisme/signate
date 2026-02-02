-- Migration: 010
-- Description: Rename "group" to "domain" and "feature" to "aspect"
-- Date: 2026-01-27
--
-- RATIONALE:
--   Terminology alignment:
--   - "group" -> "domain" (more semantic: INT, ARCH, CTL, EVO are architectural domains)
--   - "feature" -> "aspect" (F01-F16 -> A01-A16, represents aspects of each domain)
--
--   This migration:
--   1. Renames enum types: group_id -> domain_id, feature_id -> aspect_id
--   2. Renames columns in decisions table
--   3. Updates aspect_id enum values: F01-F16 -> A01-A16
--   4. Updates decision_sequences table (feature_id -> aspect_id)
--   5. Recreates views that reference renamed columns
--   6. Recreates indexes with new names
--   7. Updates existing decision_code values (replace F with A)

BEGIN;

-- ============================================================================
-- Step 1: Drop views that depend on columns we're renaming
-- ============================================================================

-- Drop the decisions_with_code view (we'll recreate it after renaming)
DROP VIEW IF EXISTS decisions_with_code;

-- ============================================================================
-- Step 2: Drop indexes that reference columns we're renaming
-- These will be recreated with new names
-- ============================================================================

DROP INDEX IF EXISTS idx_decisions_group_id;
DROP INDEX IF EXISTS idx_decisions_feature_id;
DROP INDEX IF EXISTS idx_decisions_group_feature;

-- ============================================================================
-- Step 3: Rename columns in decisions table
-- Note: Column rename does NOT require dropping constraints
-- ============================================================================

-- Rename group_id -> domain_id
ALTER TABLE decisions RENAME COLUMN group_id TO domain_id;

-- Rename feature_id -> aspect_id
ALTER TABLE decisions RENAME COLUMN feature_id TO aspect_id;

-- ============================================================================
-- Step 4: Rename enum types
-- PostgreSQL requires casting to text, creating new type, then casting back
-- ============================================================================

-- 4a. Rename group_id enum type to domain_id
ALTER TYPE group_id RENAME TO domain_id;

-- 4b. For feature_id -> aspect_id, we need to:
--     - Create new enum with A01-A16 values
--     - Alter column to use new enum (with conversion)
--     - Drop old enum

-- Create new aspect_id enum with A-prefix values
CREATE TYPE aspect_id AS ENUM (
    'A01', 'A02', 'A03', 'A04',
    'A05', 'A06', 'A07', 'A08',
    'A09', 'A10', 'A11', 'A12',
    'A13', 'A14', 'A15', 'A16'
);

-- Temporarily change column to text to allow conversion
ALTER TABLE decisions
    ALTER COLUMN aspect_id TYPE text;

-- Convert F values to A values
UPDATE decisions
SET aspect_id = REPLACE(aspect_id, 'F', 'A');

-- Cast back to new enum type
ALTER TABLE decisions
    ALTER COLUMN aspect_id TYPE aspect_id USING aspect_id::aspect_id;

-- Drop old feature_id enum
DROP TYPE feature_id;

-- ============================================================================
-- Step 5: Update decision_sequences table
-- Rename feature_id column to aspect_id and update values
-- ============================================================================

-- Rename the column
ALTER TABLE decision_sequences RENAME COLUMN feature_id TO aspect_id;

-- Update values from F to A
UPDATE decision_sequences
SET aspect_id = REPLACE(aspect_id, 'F', 'A');

-- ============================================================================
-- Step 6: Update existing decision_code values
-- Replace F with A in the feature portion (2nd segment)
-- Format: {domain}-{aspect}-{seq}-v{version}
-- Example: INT-F01-001-v1.0.0 -> INT-A01-001-v1.0.0
-- ============================================================================

UPDATE decisions
SET decision_code = REGEXP_REPLACE(decision_code, '-F([0-9]{2})-', '-A\1-', 'g')
WHERE decision_code IS NOT NULL
  AND decision_code LIKE '%-F%-%';

-- ============================================================================
-- Step 7: Recreate indexes with new column names
-- ============================================================================

CREATE INDEX idx_decisions_domain_id ON decisions(domain_id);
CREATE INDEX idx_decisions_aspect_id ON decisions(aspect_id);
CREATE INDEX idx_decisions_domain_aspect ON decisions(domain_id, aspect_id);

-- ============================================================================
-- Step 8: Recreate the decisions_with_code view with renamed columns
-- ============================================================================

CREATE OR REPLACE VIEW decisions_with_code AS
SELECT
    d.*,
    -- Generate decision_code: {domain}-{aspect}-{seq:03d}-v{version}
    COALESCE(
        d.decision_code,
        CONCAT(
            d.domain_id::text, '-',
            d.aspect_id::text, '-',
            LPAD(
                (ROW_NUMBER() OVER (
                    PARTITION BY d.aspect_id
                    ORDER BY d.created_at ASC
                ))::text,
                3, '0'
            ),
            '-v', d.version
        )
    ) AS generated_code
FROM decisions d;

-- ============================================================================
-- Step 9: Update comments to reflect new terminology
-- ============================================================================

COMMENT ON VIEW decisions_with_code IS
    'View with auto-generated decision_code. Use generated_code column. '
    'Format: {domain}-{aspect}-{seq:03d}-v{version}';

COMMENT ON TABLE decision_sequences IS
    'Sequence tracking for aspect-based numbering (append-only)';

COMMENT ON COLUMN decisions.domain_id IS
    'Architectural domain: INT (Integration), ARCH (Architecture), CTL (Control), EVO (Evolution)';

COMMENT ON COLUMN decisions.aspect_id IS
    'Domain aspect: A01-A16. Each domain has 16 possible aspects.';

-- ============================================================================
-- Step 10: Log migration summary
-- ============================================================================

DO $$
DECLARE
    decisions_count INTEGER;
    sequences_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO decisions_count FROM decisions;
    SELECT COUNT(*) INTO sequences_count FROM decision_sequences;

    RAISE NOTICE 'Migration 010 complete:';
    RAISE NOTICE '  - Renamed group_id -> domain_id';
    RAISE NOTICE '  - Renamed feature_id -> aspect_id';
    RAISE NOTICE '  - Converted F01-F16 values to A01-A16';
    RAISE NOTICE '  - Updated % decisions', decisions_count;
    RAISE NOTICE '  - Updated % sequence records', sequences_count;
    RAISE NOTICE '  - Recreated indexes and views';
END $$;

COMMIT;
