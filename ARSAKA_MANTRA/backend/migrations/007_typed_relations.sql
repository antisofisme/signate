-- Migration: 007
-- Description: Add typed relations to decisions table
-- Date: 2026-01-26
--
-- RATIONALE:
--   Current `related_decisions` is just List[UUID] - no semantic meaning.
--   Typed relations provide:
--   - depends_on: this decision depends on target
--   - conflicts_with: this decision conflicts with target
--   - informed_by: this decision is informed by target
--
--   Note: `supersedes` remains a separate field (special semantic)

BEGIN;

-- ============================================================================
-- Step 1: Create relation_type enum
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE relation_type AS ENUM ('depends_on', 'conflicts_with', 'informed_by');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- Step 2: Add relations column (JSONB array of typed relations)
-- Format: [{"target_id": "uuid", "type": "depends_on"}, ...]
-- ============================================================================

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS relations JSONB DEFAULT '[]';

-- ============================================================================
-- Step 3: Create index for efficient relation queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_decisions_relations ON decisions USING GIN (relations);

-- ============================================================================
-- Step 4: Comments
-- ============================================================================

COMMENT ON COLUMN decisions.relations IS
    'Typed relations: [{target_id, type: depends_on|conflicts_with|informed_by}]. '
    'Supersedes relation remains in separate field.';

COMMIT;
