-- Migration: 077
-- Description: Fix data types for better performance and data integrity
-- Date: 2025-12-04
-- Impact: Minor backend model updates required

BEGIN;

-- ============================================================================
-- 1. STRING SIZING - Prevent truncation for file paths
-- ============================================================================

-- Content file paths (500 → 1000)
ALTER TABLE contents ALTER COLUMN file_path TYPE VARCHAR(1000);
ALTER TABLE contents ALTER COLUMN file_url TYPE VARCHAR(1000);
ALTER TABLE contents ALTER COLUMN thumbnail_path TYPE VARCHAR(1000);
ALTER TABLE contents ALTER COLUMN thumbnail_url TYPE VARCHAR(1000);
ALTER TABLE contents ALTER COLUMN hls_master_playlist_path TYPE VARCHAR(1000);
ALTER TABLE contents ALTER COLUMN hls_master_playlist_url TYPE VARCHAR(1000);

-- MIME type expansion (100 → 200)
ALTER TABLE contents ALTER COLUMN mime_type TYPE VARCHAR(200);

-- User agent to TEXT (500 → unlimited)
ALTER TABLE devices ALTER COLUMN user_agent TYPE TEXT;

-- ============================================================================
-- 2. JSON TO JSONB - 3-5x faster queries
-- ============================================================================

-- Organization settings
ALTER TABLE organizations ALTER COLUMN settings TYPE JSONB USING settings::jsonb;

-- Audit log details
ALTER TABLE audit_logs ALTER COLUMN details TYPE JSONB USING details::jsonb;

-- Content HLS variants
ALTER TABLE contents ALTER COLUMN hls_variants TYPE JSONB USING hls_variants::jsonb;

-- ============================================================================
-- 3. NUMERIC PRECISION - Video timing accuracy
-- ============================================================================

-- FPS: Float → NUMERIC(5,3) for exact frame rates like 23.976
ALTER TABLE contents ALTER COLUMN fps TYPE NUMERIC(5,3);

-- Media duration: Float → DOUBLE PRECISION for better timing
ALTER TABLE contents ALTER COLUMN media_duration TYPE DOUBLE PRECISION;
ALTER TABLE contents ALTER COLUMN video_start_time TYPE DOUBLE PRECISION;
ALTER TABLE contents ALTER COLUMN video_end_time TYPE DOUBLE PRECISION;

-- ============================================================================
-- 4. CHECK CONSTRAINTS - Data integrity
-- ============================================================================

-- Volume level must be 0-100
ALTER TABLE devices DROP CONSTRAINT IF EXISTS chk_volume_level;
ALTER TABLE devices ADD CONSTRAINT chk_volume_level
    CHECK (volume_level >= 0 AND volume_level <= 100);

-- Rotation must be valid values
ALTER TABLE devices DROP CONSTRAINT IF EXISTS chk_rotation;
ALTER TABLE devices ADD CONSTRAINT chk_rotation
    CHECK (rotation IN (0, 90, 180, 270));

-- Device status validation
ALTER TABLE devices DROP CONSTRAINT IF EXISTS chk_status;
ALTER TABLE devices ADD CONSTRAINT chk_status
    CHECK (status IN ('pending', 'active', 'inactive', 'released'));

-- Content upload status validation
ALTER TABLE contents DROP CONSTRAINT IF EXISTS chk_upload_status;
ALTER TABLE contents ADD CONSTRAINT chk_upload_status
    CHECK (upload_status IN ('pending', 'processing', 'completed', 'failed'));

-- Content transcoding status validation
ALTER TABLE contents DROP CONSTRAINT IF EXISTS chk_transcoding_status;
ALTER TABLE contents ADD CONSTRAINT chk_transcoding_status
    CHECK (transcoding_status IN ('pending', 'processing', 'completed', 'failed', 'not_required'));

-- Content type validation
ALTER TABLE contents DROP CONSTRAINT IF EXISTS chk_content_type;
ALTER TABLE contents ADD CONSTRAINT chk_content_type
    CHECK (content_type IN ('image', 'video', 'audio', 'html', 'url', 'pdf'));

-- Privacy mode validation
ALTER TABLE devices DROP CONSTRAINT IF EXISTS chk_privacy_mode;
ALTER TABLE devices ADD CONSTRAINT chk_privacy_mode
    CHECK (privacy_mode IN ('none', 'limited', 'full'));

-- FPS must be positive if set
ALTER TABLE contents DROP CONSTRAINT IF EXISTS chk_fps;
ALTER TABLE contents ADD CONSTRAINT chk_fps
    CHECK (fps IS NULL OR fps > 0);

-- Transcoding progress 0-100
ALTER TABLE contents DROP CONSTRAINT IF EXISTS chk_transcoding_progress;
ALTER TABLE contents ADD CONSTRAINT chk_transcoding_progress
    CHECK (transcoding_progress >= 0 AND transcoding_progress <= 100);

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed):
-- ALTER TABLE contents ALTER COLUMN file_path TYPE VARCHAR(500);
-- ALTER TABLE contents ALTER COLUMN thumbnail_path TYPE VARCHAR(500);
-- ALTER TABLE contents ALTER COLUMN mime_type TYPE VARCHAR(100);
-- ALTER TABLE devices ALTER COLUMN user_agent TYPE VARCHAR(500);
-- ALTER TABLE organizations ALTER COLUMN settings TYPE JSON;
-- ALTER TABLE audit_logs ALTER COLUMN details TYPE JSON;
-- ALTER TABLE contents ALTER COLUMN hls_variants TYPE JSON;
-- ALTER TABLE contents ALTER COLUMN fps TYPE FLOAT;
-- ALTER TABLE contents ALTER COLUMN media_duration TYPE FLOAT;
-- DROP CONSTRAINT checks...
-- ============================================================================
