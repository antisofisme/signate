-- Migration: 053
-- Description: Add updated_at column to tags table
-- Date: 2025-11-27
-- Issue: Model has updated_at but database doesn't

BEGIN;

-- Add updated_at column to tags table
ALTER TABLE tags
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Add comment
COMMENT ON COLUMN tags.updated_at IS 'Timestamp when tag was last updated';

COMMIT;
