-- Migration: 065
-- Description: Add image optimization columns to menu_media table
-- Date: 2025-12-01
-- Purpose: Support WebP variants for performance optimization

BEGIN;

-- Add variants column to store WebP image variants
-- Structure: {"thumb": {...}, "small": {...}, "hd": {...}, "4k": {...}, "original": {...}, "fallback": {...}}
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS variants JSONB DEFAULT NULL;

-- Add content_hash for cache invalidation (different from file_hash which is for deduplication)
-- This hash is recalculated after optimization
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

-- Add processing status to track optimization state
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';

-- Add timestamp for when optimization was completed
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS optimized_at TIMESTAMP WITH TIME ZONE;

-- Add original dimensions (before any processing)
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS original_width INTEGER;

ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS original_height INTEGER;

-- Add is_animated flag for GIF detection
ALTER TABLE menu_media
  ADD COLUMN IF NOT EXISTS is_animated BOOLEAN DEFAULT FALSE;

-- Add index on processing_status for batch operations
CREATE INDEX IF NOT EXISTS idx_menu_media_processing_status
  ON menu_media(processing_status);

-- Add index on content_hash for cache validation
CREATE INDEX IF NOT EXISTS idx_menu_media_content_hash
  ON menu_media(content_hash);

-- Add comments
COMMENT ON COLUMN menu_media.variants IS 'WebP variant URLs: {thumb, small, hd, 4k, original, fallback}';
COMMENT ON COLUMN menu_media.content_hash IS 'SHA-256 hash for cache invalidation (post-optimization)';
COMMENT ON COLUMN menu_media.processing_status IS 'Status: pending, processing, completed, failed';
COMMENT ON COLUMN menu_media.optimized_at IS 'When image optimization was completed';
COMMENT ON COLUMN menu_media.original_width IS 'Original image width before processing';
COMMENT ON COLUMN menu_media.original_height IS 'Original image height before processing';
COMMENT ON COLUMN menu_media.is_animated IS 'True if animated GIF';

-- Update existing records to have completed status (they use original files)
UPDATE menu_media
SET processing_status = 'completed',
    original_width = width,
    original_height = height
WHERE processing_status IS NULL OR processing_status = 'pending';

COMMIT;
