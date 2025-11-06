-- ============================================================================
-- Migration 008: Add Anthias Features to Content Model
-- ============================================================================
-- Author: Backend Architect
-- Date: 2025-10-28
-- Purpose: Add missing Anthias features to content table for enhanced campaign
--          management, playback control, and file integrity verification
--
-- New Fields:
-- 1. play_order (int): Sequence/order for content playback within playlists
-- 2. start_date (timestamp): Campaign start date for time-based activation
-- 3. end_date (timestamp): Campaign end date for time-based expiration
-- 4. is_enabled (bool): Enable/disable content without deletion (soft delete)
-- 5. shuffle (bool): Random playback mode for content rotation
-- 6. md5_checksum (string): File integrity verification (from Anthias)
--
-- Database Changes:
-- - Add 6 new columns to contents table
-- - Create indexes for play_order, start_date, end_date, is_enabled
-- - Add default values for proper data initialization
-- - Add column comments for documentation
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Add new columns to contents table
-- ============================================================================

-- Add play_order: Controls sequence for content playback within playlists
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS play_order INTEGER NOT NULL DEFAULT 0;

-- Add start_date: Campaign activation start date
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITH TIME ZONE;

-- Add end_date: Campaign expiration end date
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITH TIME ZONE;

-- Add is_enabled: Soft delete flag (False = disabled but not deleted)
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN NOT NULL DEFAULT TRUE;

-- Add shuffle: Enable random/shuffle playback mode
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS shuffle BOOLEAN NOT NULL DEFAULT FALSE;

-- Add md5_checksum: File integrity verification (from Anthias assets)
ALTER TABLE contents
ADD COLUMN IF NOT EXISTS md5_checksum VARCHAR(32);

-- ============================================================================
-- Step 2: Create indexes for frequently queried columns
-- ============================================================================

-- Index for play_order: Used when ordering content in playlists
CREATE INDEX IF NOT EXISTS idx_contents_play_order ON contents(play_order);

-- Index for start_date: Used for time-based content activation queries
CREATE INDEX IF NOT EXISTS idx_contents_start_date ON contents(start_date);

-- Index for end_date: Used for time-based content expiration queries
CREATE INDEX IF NOT EXISTS idx_contents_end_date ON contents(end_date);

-- Index for is_enabled: Used to filter disabled content
CREATE INDEX IF NOT EXISTS idx_contents_is_enabled ON contents(is_enabled);

-- Composite index for campaign date range queries
CREATE INDEX IF NOT EXISTS idx_contents_date_range ON contents(start_date, end_date);

-- Composite index for active content queries
CREATE INDEX IF NOT EXISTS idx_contents_active ON contents(is_enabled, start_date, end_date);

-- ============================================================================
-- Step 3: Add column comments for documentation
-- ============================================================================

COMMENT ON COLUMN contents.play_order IS 'Sequence/order for content playback within playlists (0-indexed, higher = later)';
COMMENT ON COLUMN contents.start_date IS 'Campaign start date - content activation begins at this timestamp (UTC)';
COMMENT ON COLUMN contents.end_date IS 'Campaign end date - content expires after this timestamp (UTC)';
COMMENT ON COLUMN contents.is_enabled IS 'Soft delete flag - FALSE disables content without deletion, TRUE = active';
COMMENT ON COLUMN contents.shuffle IS 'Enable shuffle/random playback mode for rotating content';
COMMENT ON COLUMN contents.md5_checksum IS 'MD5 checksum for file integrity verification (32 character hex string)';

-- ============================================================================
-- Step 4: Set default values for existing records
-- ============================================================================

-- Initialize play_order based on creation order (maintaining existing order)
UPDATE contents
SET play_order = sub.row_num
FROM (
    SELECT id,
           ROW_NUMBER() OVER (ORDER BY created_at ASC) - 1 AS row_num
    FROM contents
    WHERE play_order = 0
) sub
WHERE contents.id = sub.id
AND contents.play_order = 0;

-- Existing records are enabled by default (is_enabled already defaults to TRUE)

-- ============================================================================
-- Step 5: Create helper function for active content check
-- ============================================================================

-- Function to check if content is currently active based on campaign dates
CREATE OR REPLACE FUNCTION is_content_active(
    p_is_enabled BOOLEAN,
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Content must be enabled
    IF NOT p_is_enabled THEN
        RETURN FALSE;
    END IF;

    -- Check campaign date range if dates are set
    IF p_start_date IS NOT NULL AND p_end_date IS NOT NULL THEN
        RETURN (NOW() AT TIME ZONE 'UTC') BETWEEN p_start_date AND p_end_date;
    END IF;

    -- If no campaign dates, content is active if enabled
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Step 6: Update model timestamp
-- ============================================================================

-- Update the updated_at timestamp for contents to reflect this schema change
UPDATE contents
SET updated_at = NOW()
WHERE updated_at IS NULL OR updated_at < NOW() - INTERVAL '1 day';

-- ============================================================================
-- VERIFICATION QUERIES (Run these after migration to ensure success)
-- ============================================================================

-- 1. Verify all new columns were added
SELECT
    'Column Addition Check' as check_type,
    COUNT(CASE WHEN column_name = 'play_order' THEN 1 END) as play_order_exists,
    COUNT(CASE WHEN column_name = 'start_date' THEN 1 END) as start_date_exists,
    COUNT(CASE WHEN column_name = 'end_date' THEN 1 END) as end_date_exists,
    COUNT(CASE WHEN column_name = 'is_enabled' THEN 1 END) as is_enabled_exists,
    COUNT(CASE WHEN column_name = 'shuffle' THEN 1 END) as shuffle_exists,
    COUNT(CASE WHEN column_name = 'md5_checksum' THEN 1 END) as md5_checksum_exists
FROM information_schema.columns
WHERE table_name = 'contents';

-- 2. Verify column data types and defaults
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'contents'
AND column_name IN ('play_order', 'start_date', 'end_date', 'is_enabled', 'shuffle', 'md5_checksum')
ORDER BY ordinal_position;

-- 3. Verify indexes were created
SELECT
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE tablename = 'contents'
AND indexname LIKE 'idx_contents_%'
ORDER BY indexname;

-- 4. Sample data check
SELECT
    id,
    title,
    play_order,
    start_date,
    end_date,
    is_enabled,
    shuffle,
    md5_checksum
FROM contents
LIMIT 5;

-- 5. Verify function creation
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_name = 'is_content_active';

COMMIT;

-- ============================================================================
-- Migration Summary
-- ============================================================================
-- This migration successfully:
-- 1. Added 6 new columns to contents table with proper defaults
-- 2. Created 6 indexes for query optimization (play_order, dates, is_enabled, active)
-- 3. Added comprehensive column comments for documentation
-- 4. Initialized play_order based on creation order for existing records
-- 5. Created helper function for active content checks
-- 6. Maintained backward compatibility (all fields are optional/have defaults)
--
-- Use case:
-- - play_order: Sequence content within playlists
-- - start_date/end_date: Time-limited campaigns or promotions
-- - is_enabled: Soft delete content without losing data
-- - shuffle: Randomize content rotation
-- - md5_checksum: Verify file integrity from Anthias integration
-- ============================================================================
