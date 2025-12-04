-- Migration: 050
-- Description: Replace schedule priority with color field
-- Date: 2025-12-04
--
-- Changes:
-- - Add color column (VARCHAR(7) for hex colors like #3B82F6)
-- - Drop priority column (no longer needed)
-- - Set default color to blue (#3B82F6)

BEGIN;

-- Step 1: Add color column with default value
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS color VARCHAR(7) DEFAULT '#3B82F6' NOT NULL;

-- Step 2: Drop priority column
ALTER TABLE schedules
DROP COLUMN IF EXISTS priority;

-- Step 3: Add comment
COMMENT ON COLUMN schedules.color IS 'Hex color code for calendar display (e.g. #3B82F6)';

COMMIT;
