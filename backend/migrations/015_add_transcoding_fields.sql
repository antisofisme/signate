-- Migration: Add transcoding fields to contents table
-- Phase: Video Transcoding Infrastructure Phase 1
-- Purpose: Add columns to track video transcoding status, progress, and HLS output
-- Author: Database Architect
-- Date: 2025-10-29
--
-- BREAKING CHANGES:
-- - None (backward compatible - adds new nullable columns with sensible defaults)
--
-- DEPLOYMENT NOTES:
-- 1. Run this migration BEFORE deploying transcoding service code
-- 2. After migration, existing content will have NULL transcoding fields
-- 3. Only video content will populate these fields
-- 4. Image/HTML content will remain NULL (no transcoding needed)
-- 5. Estimated execution time: < 1 second
--
-- PERFORMANCE IMPACT:
-- - Adds 6 columns (minimal storage overhead ~50 bytes per row)
-- - Adds 2 indexes for query optimization (transcoding status lookup)
-- - No impact on existing queries - all columns are nullable
-- - Slightly increases UPDATE time when transcoding status changes
--
-- SCHEMA CONTEXT:
-- The transcoding workflow:
-- 1. Video uploaded → transcoding_status = 'pending', transcoding_job_id = UUID
-- 2. Job processing → transcoding_progress = 0-99
-- 3. Job complete → transcoding_status = 'completed', hls_master_playlist_path set
-- 4. Job failed → transcoding_status = 'failed', transcoding_error = error message

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Step 1: Add transcoding_status column
-- Tracks the state of video transcoding: pending, processing, completed, failed, skipped
ALTER TABLE contents
ADD COLUMN transcoding_status VARCHAR(50) NULL
DEFAULT NULL;

COMMENT ON COLUMN contents.transcoding_status IS
'Status of video transcoding job. Values: pending, processing, completed, failed, skipped.
NULL for non-video content or legacy content uploaded before transcoding support.';

-- Step 2: Add transcoding_job_id column
-- Stores the external job ID from transcoding service (e.g., AWS MediaConvert, FFmpeg service)
-- Format: UUID or service-specific ID
ALTER TABLE contents
ADD COLUMN transcoding_job_id VARCHAR(200) NULL
DEFAULT NULL;

COMMENT ON COLUMN contents.transcoding_job_id IS
'External transcoding job ID from the transcoding service provider.
Used to track job status and retrieve results. NULL if transcoding not initiated.';

-- Step 3: Add transcoding_progress column
-- Tracks transcoding progress as percentage (0-100)
-- Updated in real-time as job progresses
ALTER TABLE contents
ADD COLUMN transcoding_progress INTEGER DEFAULT 0 CHECK (transcoding_progress >= 0 AND transcoding_progress <= 100);

COMMENT ON COLUMN contents.transcoding_progress IS
'Transcoding progress as percentage (0-100). Updated in real-time during processing.
0 = not started, 1-99 = processing, 100 = completed (check transcoding_status for result).';

-- Step 4: Add transcoding_error column
-- Stores detailed error message if transcoding fails
-- Important for debugging and user notification
ALTER TABLE contents
ADD COLUMN transcoding_error TEXT NULL
DEFAULT NULL;

COMMENT ON COLUMN contents.transcoding_error IS
'Error message if transcoding job failed. NULL if no error occurred.
Contains details for debugging and user notification (e.g., codec unsupported, file corrupted).';

-- Step 5: Add hls_master_playlist_path column
-- Stores the path to the master .m3u8 playlist file
-- Path relative to CDN root or absolute S3 path
ALTER TABLE contents
ADD COLUMN hls_master_playlist_path VARCHAR(500) NULL
DEFAULT NULL;

COMMENT ON COLUMN contents.hls_master_playlist_path IS
'Path to HLS master playlist (.m3u8) after transcoding completes.
Format: /hls/content-{id}/master.m3u8 or S3 path: s3://bucket/hls/content-{id}/master.m3u8
NULL until transcoding is completed successfully.';

-- Step 6: Add hls_variants column
-- Stores JSONB with metadata about HLS variants (bitrate ladder)
-- Structure: {"variants": [{"bitrate": 1000, "resolution": "1280x720", "path": "variant_1000.m3u8"}]}
-- Allows flexible bitrate ladder configuration
ALTER TABLE contents
ADD COLUMN hls_variants JSONB NULL
DEFAULT NULL;

COMMENT ON COLUMN contents.hls_variants IS
'JSONB containing HLS variant (bitrate ladder) metadata after transcoding.
Structure: {"variants": [{"bitrate": 1000, "resolution": "1280x720", "path": "variant_1000.m3u8"}, ...]}.
Enables adaptive bitrate streaming - player selects best quality based on network speed.
NULL until transcoding is completed successfully.';

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index 1: For querying content by transcoding status
-- Common queries: "Get all videos in processing", "Get failed transcoding jobs"
CREATE INDEX IF NOT EXISTS idx_contents_transcoding_status
ON contents(transcoding_status)
WHERE transcoding_status IS NOT NULL;

COMMENT ON INDEX idx_contents_transcoding_status IS
'Index for fast lookups of content by transcoding status.
Useful for dashboard queries: pending jobs, failed transcoding, etc.';

-- Index 2: For querying content by job ID
-- Common queries: "Find content by transcoding job ID", "Update status by job ID"
CREATE INDEX IF NOT EXISTS idx_contents_transcoding_job_id
ON contents(transcoding_job_id)
WHERE transcoding_job_id IS NOT NULL;

COMMENT ON INDEX idx_contents_transcoding_job_id IS
'Index for fast lookups of content by external transcoding job ID.
Useful for job status updates from transcoding service webhooks.';

-- Index 3: Combined index for status and progress queries
-- Useful for dashboard: "Show all processing jobs with progress"
CREATE INDEX IF NOT EXISTS idx_contents_transcoding_status_progress
ON contents(transcoding_status, transcoding_progress)
WHERE transcoding_status IN ('pending', 'processing');

COMMENT ON INDEX idx_contents_transcoding_status_progress IS
'Composite index for querying processing/pending transcoding jobs with progress.
Optimizes dashboard queries showing job progress.';

-- ============================================================================
-- MIGRATION LOG FUNCTION
-- ============================================================================

-- Step 7: Log migration completion with detailed metadata
DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Migration 015_add_transcoding_fields completed';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Added 6 new columns to contents table:';
    RAISE NOTICE '  1. transcoding_status (VARCHAR(50), NULL)';
    RAISE NOTICE '  2. transcoding_job_id (VARCHAR(200), NULL)';
    RAISE NOTICE '  3. transcoding_progress (INTEGER, DEFAULT 0)';
    RAISE NOTICE '  4. transcoding_error (TEXT, NULL)';
    RAISE NOTICE '  5. hls_master_playlist_path (VARCHAR(500), NULL)';
    RAISE NOTICE '  6. hls_variants (JSONB, NULL)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 indexes for performance:';
    RAISE NOTICE '  1. idx_contents_transcoding_status';
    RAISE NOTICE '  2. idx_contents_transcoding_job_id';
    RAISE NOTICE '  3. idx_contents_transcoding_status_progress';
    RAISE NOTICE '';
    RAISE NOTICE 'Backward compatible: Existing content unaffected';
    RAISE NOTICE 'Storage overhead: ~50 bytes per row';
    RAISE NOTICE '===============================================';
END $$;

-- ============================================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================================

-- Uncomment below to rollback all changes (remove in reverse order)
-- IMPORTANT: Ensure no application code references these columns before rollback!

/*
-- Step 1: Drop indexes (in reverse order)
DROP INDEX IF EXISTS idx_contents_transcoding_status_progress;
DROP INDEX IF EXISTS idx_contents_transcoding_job_id;
DROP INDEX IF EXISTS idx_contents_transcoding_status;

-- Step 2: Drop columns (all at once is safe after dropping dependent objects)
ALTER TABLE contents
DROP COLUMN IF EXISTS transcoding_status,
DROP COLUMN IF EXISTS transcoding_job_id,
DROP COLUMN IF EXISTS transcoding_progress,
DROP COLUMN IF EXISTS transcoding_error,
DROP COLUMN IF EXISTS hls_master_playlist_path,
DROP COLUMN IF EXISTS hls_variants;

-- Step 3: Log rollback completion
DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Migration 015_add_transcoding_fields rolled back';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Removed 6 columns from contents table';
    RAISE NOTICE 'Removed 3 indexes';
    RAISE NOTICE '===============================================';
END $$;
*/

-- ============================================================================
-- VERIFICATION QUERIES (Run after migration to confirm success)
-- ============================================================================

-- Query 1: Verify all columns were added
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'contents'
AND column_name IN (
    'transcoding_status',
    'transcoding_job_id',
    'transcoding_progress',
    'transcoding_error',
    'hls_master_playlist_path',
    'hls_variants'
)
ORDER BY ordinal_position DESC;

-- Query 2: Verify all indexes were created
SELECT
    indexname,
    indexdef,
    tablename
FROM pg_indexes
WHERE tablename = 'contents'
AND indexname LIKE 'idx_contents_transcoding%'
ORDER BY indexname;

-- Query 3: Check for any existing transcoding data (should be empty after initial migration)
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE transcoding_status IS NOT NULL) as with_status,
    COUNT(*) FILTER (WHERE transcoding_job_id IS NOT NULL) as with_job_id,
    COUNT(*) FILTER (WHERE transcoding_progress > 0) as with_progress,
    COUNT(*) FILTER (WHERE transcoding_error IS NOT NULL) as with_error,
    COUNT(*) FILTER (WHERE hls_master_playlist_path IS NOT NULL) as with_hls_path,
    COUNT(*) FILTER (WHERE hls_variants IS NOT NULL) as with_hls_variants
FROM contents;

-- Query 4: Sample content records with new fields (should be all NULLs initially)
SELECT
    id,
    title,
    content_type,
    transcoding_status,
    transcoding_job_id,
    transcoding_progress,
    transcoding_error,
    hls_master_playlist_path,
    created_at
FROM contents
ORDER BY created_at DESC
LIMIT 10;

-- Query 5: Check constraints on transcoding_progress
SELECT
    constraint_name,
    table_name,
    column_name,
    check_clause
FROM information_schema.check_constraints
WHERE table_name = 'contents'
AND column_name = 'transcoding_progress';

-- ============================================================================
-- MIGRATION METADATA & DOCUMENTATION
-- ============================================================================

-- Migration ID: 015
-- Migration Name: 015_add_transcoding_fields.sql
-- Phase: Video Transcoding Infrastructure Phase 1
-- Dependencies: 014_add_uri_caching.sql
-- Dependent: (Future transcoding service code)
--
-- Rollback: See DOWN MIGRATION section above (uncomment to execute)
--
-- Testing Checklist:
-- [ ] 1. Run migration - should complete in < 1 second
-- [ ] 2. Run verification queries - all should show new columns
-- [ ] 3. Verify no impact on existing SELECT queries
-- [ ] 4. Test INSERT on contents - should work normally
-- [ ] 5. Test UPDATE on transcoding_status - verify index works
-- [ ] 6. Query pending jobs - performance should be fast
-- [ ] 7. Check disk space usage - should be minimal
--
-- API Integration Points:
-- - POST /api/contents/upload → Set transcoding_status = 'pending'
-- - POST /api/transcoding/webhook → Update status/progress/error/hls_*
-- - GET /api/contents/{id} → Include hls_variants in response
-- - GET /api/contents?transcoding_status=processing → Show dashboard
--
-- Expected Workflow:
-- 1. Video uploaded → status='pending', job_id=UUID
-- 2. Transcoding service fetches job → starts processing
-- 3. Service updates progress every N seconds
-- 4. Service completes → status='completed', hls_master_playlist_path=/...
-- 5. Service on error → status='failed', transcoding_error=message
--
-- Bitrate Ladder Example (hls_variants):
-- {
--   "variants": [
--     {"bitrate": 500, "resolution": "854x480", "path": "variant_500k.m3u8"},
--     {"bitrate": 1000, "resolution": "1280x720", "path": "variant_1000k.m3u8"},
--     {"bitrate": 2500, "resolution": "1920x1080", "path": "variant_2500k.m3u8"}
--   ]
-- }
--
-- Documentation: See TRANSCODING_ARCHITECTURE.md for full details
-- ============================================================================
