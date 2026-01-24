-- Migration: 003
-- Description: Remove status field, enforce absolute immutability
-- Date: 2025-01-24
-- Authority: Human Decision 1 (DECISION IMMUTABILITY)
--
-- BINDING DECISION:
--   Decision records are ABSOLUTELY IMMUTABLE.
--   NO field of a stored decision may be modified after insertion.
--   Lifecycle MUST be expressed ONLY via versioning + supersedes.
--   Status field is ILLEGAL.

BEGIN;

-- ============================================================================
-- STEP 1: Remove status-related objects
-- ============================================================================

-- Drop the update trigger that had status transition loophole
DROP TRIGGER IF EXISTS trigger_prevent_decision_update ON decisions;
DROP FUNCTION IF EXISTS prevent_decision_update();

-- Remove status column
ALTER TABLE decisions DROP COLUMN IF EXISTS status;

-- Remove status enum type
DROP TYPE IF EXISTS decision_status;

-- Remove is_immutable flag (was a design smell - immutability is unconditional)
ALTER TABLE decisions DROP COLUMN IF EXISTS is_immutable;

-- ============================================================================
-- STEP 2: Create ABSOLUTE immutability trigger
-- Per Human Decision 1: NO modification permitted. No exceptions.
-- ============================================================================

CREATE OR REPLACE FUNCTION reject_all_updates()
RETURNS TRIGGER AS $$
BEGIN
    -- ABSOLUTE REJECTION. No conditions. No exceptions.
    -- Per MANTRA-LAW-001 §10 and Human Decision 1.
    RAISE EXCEPTION
        'CONSTITUTIONAL VIOLATION: Decision records are ABSOLUTELY IMMUTABLE. '
        'Modification attempt on decision_id=% is INVALID and REJECTED. '
        'Lifecycle changes MUST use versioning and supersedes relationships.',
        OLD.decision_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger fires on ANY update attempt
CREATE TRIGGER trigger_reject_all_updates
    BEFORE UPDATE ON decisions
    FOR EACH ROW
    EXECUTE FUNCTION reject_all_updates();

-- ============================================================================
-- STEP 3: Ensure DELETE trigger is unconditional
-- ============================================================================

-- Drop and recreate to ensure no legacy conditions
DROP TRIGGER IF EXISTS trigger_prevent_decision_delete ON decisions;
DROP FUNCTION IF EXISTS prevent_decision_delete();

CREATE OR REPLACE FUNCTION reject_all_deletes()
RETURNS TRIGGER AS $$
BEGIN
    -- ABSOLUTE REJECTION. No conditions. No exceptions.
    RAISE EXCEPTION
        'CONSTITUTIONAL VIOLATION: Decision records are ABSOLUTELY IMMUTABLE. '
        'Deletion attempt on decision_id=% is INVALID and REJECTED. '
        'Decisions are permanent historical records.',
        OLD.decision_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_reject_all_deletes
    BEFORE DELETE ON decisions
    FOR EACH ROW
    EXECUTE FUNCTION reject_all_deletes();

-- ============================================================================
-- STEP 4: Add comment documenting constitutional basis
-- ============================================================================

COMMENT ON TABLE decisions IS
    'IMMUTABLE decision storage per MANTRA-LAW-001 §10 and Human Decision 1. '
    'NO UPDATE. NO DELETE. INSERT ONLY. '
    'Lifecycle via versioning + supersedes.';

COMMENT ON TRIGGER trigger_reject_all_updates ON decisions IS
    'CONSTITUTIONAL ENFORCEMENT: Rejects ALL update attempts unconditionally.';

COMMENT ON TRIGGER trigger_reject_all_deletes ON decisions IS
    'CONSTITUTIONAL ENFORCEMENT: Rejects ALL delete attempts unconditionally.';

COMMIT;
