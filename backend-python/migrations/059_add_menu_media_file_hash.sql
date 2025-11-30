-- Migration: 059
-- Description: Add file_hash column to menu_media for deduplication
-- Date: 2025-11-30

BEGIN;

-- Add file_hash column for file deduplication
ALTER TABLE menu_media ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Create index for fast hash lookups
CREATE INDEX IF NOT EXISTS idx_menu_media_file_hash ON menu_media(file_hash) WHERE file_hash IS NOT NULL;

-- Add comment
COMMENT ON COLUMN menu_media.file_hash IS 'SHA-256 hash of file content for deduplication';

COMMIT;
