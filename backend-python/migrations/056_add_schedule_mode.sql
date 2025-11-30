-- Migration 056: Add Schedule Mode (OVERRIDE/ROTATE)
-- Date: 2025-11-29
-- Description: Add mode column to schedules table for controlling playback behavior

BEGIN;

-- Add mode column with default 'rotate'
-- 'override' = Stop all other content when this schedule is active
-- 'rotate' = Play alongside other content, take turns in rotation
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'rotate';

-- Add check constraint to ensure valid mode values
ALTER TABLE schedules
ADD CONSTRAINT schedules_mode_check
CHECK (mode IN ('override', 'rotate'));

-- Add comment for documentation
COMMENT ON COLUMN schedules.mode IS 'Schedule playback mode: override (exclusive) or rotate (join rotation)';

-- Create index for mode filtering
CREATE INDEX IF NOT EXISTS idx_schedules_mode ON schedules(mode);

COMMIT;
