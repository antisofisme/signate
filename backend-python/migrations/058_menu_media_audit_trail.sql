-- Migration: 058
-- Description: Add deleted_by_id audit trail to menu_media table
-- Date: 2025-11-30

BEGIN;

-- Add deleted_by_id for complete audit trail
ALTER TABLE menu_media
ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_menu_media_deleted_by ON menu_media(deleted_by_id);

-- Comment on column
COMMENT ON COLUMN menu_media.deleted_by_id IS 'User who deleted this media (for audit trail)';

COMMIT;
