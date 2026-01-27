-- Migration: 002
-- Description: Add tags and tech_stack columns to decisions table
-- Date: 2026-01-26

BEGIN;

-- Add tags column for categorization
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';

-- Add tech_stack column for technology references
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS tech_stack JSONB DEFAULT '[]';

-- Add decision_code column for human-readable identifier
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS decision_code VARCHAR(50);

-- Create index for tags search
CREATE INDEX IF NOT EXISTS idx_decisions_tags ON decisions USING GIN (tags);

-- Comments
COMMENT ON COLUMN decisions.tags IS 'Categorization tags for the decision';
COMMENT ON COLUMN decisions.tech_stack IS 'Technology stack references';
COMMENT ON COLUMN decisions.decision_code IS 'Human-readable decision code (e.g., INT-F01-001-v1.0.0)';

COMMIT;
