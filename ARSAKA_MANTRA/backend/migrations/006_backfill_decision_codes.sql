-- Migration: 006
-- Description: Backfill decision_code for existing decisions
-- Date: 2026-01-26
-- Per: MANTRA UX Enhancement - Human-readable decision codes

BEGIN;

-- Backfill decision_code for all existing decisions that have NULL
-- Format: {group}-{feature}-{seq:03d}-v{version}
-- Example: INT-F01-001-v1.0.0

-- Use a CTE to calculate sequence numbers per feature (ordered by created_at)
WITH numbered_decisions AS (
    SELECT
        decision_id,
        group_id,
        feature_id,
        version,
        ROW_NUMBER() OVER (
            PARTITION BY feature_id
            ORDER BY created_at ASC
        ) as seq
    FROM decisions
    WHERE decision_code IS NULL
)
UPDATE decisions d
SET decision_code = CONCAT(
    nd.group_id::text, '-',
    nd.feature_id::text, '-',
    LPAD(nd.seq::text, 3, '0'), '-v',
    nd.version
)
FROM numbered_decisions nd
WHERE d.decision_id = nd.decision_id
  AND d.decision_code IS NULL;

-- Add unique index on decision_code (allow NULL for backwards compat)
CREATE UNIQUE INDEX IF NOT EXISTS idx_decisions_code_unique
ON decisions(decision_code)
WHERE decision_code IS NOT NULL;

-- Log the backfill
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO updated_count
    FROM decisions
    WHERE decision_code IS NOT NULL;

    RAISE NOTICE 'Backfilled decision_code for % decisions', updated_count;
END $$;

COMMIT;
