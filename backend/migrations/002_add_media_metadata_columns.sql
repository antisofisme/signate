-- =============================================================================
-- Migration 002: Add Media Metadata Columns to Content Table
-- =============================================================================
-- Created: October 23, 2025
-- Purpose: Add FFprobe-extracted media metadata fields to content table
-- =============================================================================

BEGIN;

-- Add media metadata columns to content table
ALTER TABLE content
    ADD COLUMN IF NOT EXISTS resolution VARCHAR(50),
    ADD COLUMN IF NOT EXISTS width INTEGER,
    ADD COLUMN IF NOT EXISTS height INTEGER,
    ADD COLUMN IF NOT EXISTS codec VARCHAR(50),
    ADD COLUMN IF NOT EXISTS fps DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS bitrate INTEGER,
    ADD COLUMN IF NOT EXISTS video_duration DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS audio_codec VARCHAR(50),
    ADD COLUMN IF NOT EXISTS audio_bitrate INTEGER,
    ADD COLUMN IF NOT EXISTS audio_sample_rate INTEGER;

-- Add comments for documentation
COMMENT ON COLUMN content.resolution IS 'Media resolution (e.g., "1920x1080")';
COMMENT ON COLUMN content.width IS 'Media width in pixels';
COMMENT ON COLUMN content.height IS 'Media height in pixels';
COMMENT ON COLUMN content.codec IS 'Video/image codec name';
COMMENT ON COLUMN content.fps IS 'Frame rate (video only)';
COMMENT ON COLUMN content.bitrate IS 'Video bitrate in kbps';
COMMENT ON COLUMN content.video_duration IS 'Actual video duration in seconds (from metadata)';
COMMENT ON COLUMN content.audio_codec IS 'Audio codec name (video only)';
COMMENT ON COLUMN content.audio_bitrate IS 'Audio bitrate in kbps (video only)';
COMMENT ON COLUMN content.audio_sample_rate IS 'Audio sample rate in Hz (video only)';

-- Verify columns were added
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'content'
    AND column_name IN (
        'resolution', 'width', 'height', 'codec', 'fps',
        'bitrate', 'video_duration', 'audio_codec',
        'audio_bitrate', 'audio_sample_rate'
    )
ORDER BY column_name;

COMMIT;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
