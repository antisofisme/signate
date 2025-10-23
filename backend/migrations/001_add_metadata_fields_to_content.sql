-- =============================================================================
-- Migration: Add Media Metadata Fields to Content Table
-- Description: Adds FFprobe-extracted metadata fields for video and image content
-- Date: 2025-10-23
-- =============================================================================

-- Add metadata columns to content table
ALTER TABLE content ADD COLUMN IF NOT EXISTS resolution VARCHAR(50);
ALTER TABLE content ADD COLUMN IF NOT EXISTS width INTEGER;
ALTER TABLE content ADD COLUMN IF NOT EXISTS height INTEGER;
ALTER TABLE content ADD COLUMN IF NOT EXISTS codec VARCHAR(50);
ALTER TABLE content ADD COLUMN IF NOT EXISTS fps DOUBLE PRECISION;
ALTER TABLE content ADD COLUMN IF NOT EXISTS bitrate INTEGER;
ALTER TABLE content ADD COLUMN IF NOT EXISTS video_duration DOUBLE PRECISION;
ALTER TABLE content ADD COLUMN IF NOT EXISTS audio_codec VARCHAR(50);
ALTER TABLE content ADD COLUMN IF NOT EXISTS audio_bitrate INTEGER;
ALTER TABLE content ADD COLUMN IF NOT EXISTS audio_sample_rate INTEGER;

-- Add comments to columns for documentation
COMMENT ON COLUMN content.resolution IS 'Media resolution (e.g., "1920x1080")';
COMMENT ON COLUMN content.width IS 'Media width in pixels';
COMMENT ON COLUMN content.height IS 'Media height in pixels';
COMMENT ON COLUMN content.codec IS 'Video/image codec name (e.g., "h264", "jpeg")';
COMMENT ON COLUMN content.fps IS 'Frame rate for videos (e.g., 30.00)';
COMMENT ON COLUMN content.bitrate IS 'Video bitrate in kbps';
COMMENT ON COLUMN content.video_duration IS 'Actual video duration in seconds (from metadata)';
COMMENT ON COLUMN content.audio_codec IS 'Audio codec name (e.g., "aac", "mp3")';
COMMENT ON COLUMN content.audio_bitrate IS 'Audio bitrate in kbps';
COMMENT ON COLUMN content.audio_sample_rate IS 'Audio sample rate in Hz (e.g., 44100)';

-- Verify migration
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
