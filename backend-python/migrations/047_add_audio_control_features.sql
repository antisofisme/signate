-- Migration: 047
-- Description: Add audio control features (per-content mute, background audio, volume level)
-- Date: 2025-01-18
-- Purpose: Support per-content mute control, background audio loops, and device volume settings

BEGIN;

-- ============================================================================
-- STEP 1: Add volume_level to devices table
-- ============================================================================

-- Add volume_level (0-100) for device volume control
ALTER TABLE devices
ADD COLUMN volume_level INTEGER DEFAULT 75 NOT NULL CHECK (volume_level >= 0 AND volume_level <= 100);

COMMENT ON COLUMN devices.volume_level IS 'Device volume level (0-100), default 75%';

-- ============================================================================
-- STEP 2: Add background_audio_id to devices table
-- ============================================================================

-- Add background_audio_id for looping background audio (optional)
-- Background audio will loop continuously on the device, independent of visual content
ALTER TABLE devices
ADD COLUMN background_audio_id INTEGER REFERENCES contents(id) ON DELETE SET NULL;

COMMENT ON COLUMN devices.background_audio_id IS 'Background audio content to loop continuously (optional)';

-- Index for background audio queries
CREATE INDEX idx_devices_background_audio ON devices(background_audio_id) WHERE background_audio_id IS NOT NULL;

-- ============================================================================
-- STEP 3: Add background_audio_id to playlists table
-- ============================================================================

-- Add background_audio_id for playlist-level background audio
-- When playlist is active, this audio will loop
ALTER TABLE playlists
ADD COLUMN background_audio_id INTEGER REFERENCES contents(id) ON DELETE SET NULL;

COMMENT ON COLUMN playlists.background_audio_id IS 'Background audio for this playlist (loops when playlist is active)';

-- Index for playlist background audio
CREATE INDEX idx_playlists_background_audio ON playlists(background_audio_id) WHERE background_audio_id IS NOT NULL;

-- ============================================================================
-- STEP 4: Add is_muted to playlist_contents table
-- ============================================================================

-- Add is_muted flag for per-content mute control in playlists
-- When true, content audio will be muted (useful for videos with unwanted audio)
ALTER TABLE playlist_contents
ADD COLUMN is_muted BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN playlist_contents.is_muted IS 'Mute this content in playlist (true = no audio)';

-- ============================================================================
-- STEP 5: Add is_muted to content_assignments table
-- ============================================================================

-- Add is_muted flag for direct content assignments
-- When true, content audio will be muted
ALTER TABLE content_assignments
ADD COLUMN is_muted BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN content_assignments.is_muted IS 'Mute this content assignment (true = no audio)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_volume_level_exists BOOLEAN;
    v_device_background_audio_exists BOOLEAN;
    v_playlist_background_audio_exists BOOLEAN;
    v_playlist_contents_muted_exists BOOLEAN;
    v_content_assignments_muted_exists BOOLEAN;
BEGIN
    -- Check devices.volume_level
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'devices' AND column_name = 'volume_level'
    ) INTO v_volume_level_exists;

    -- Check devices.background_audio_id
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'devices' AND column_name = 'background_audio_id'
    ) INTO v_device_background_audio_exists;

    -- Check playlists.background_audio_id
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'playlists' AND column_name = 'background_audio_id'
    ) INTO v_playlist_background_audio_exists;

    -- Check playlist_contents.is_muted
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'playlist_contents' AND column_name = 'is_muted'
    ) INTO v_playlist_contents_muted_exists;

    -- Check content_assignments.is_muted
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'content_assignments' AND column_name = 'is_muted'
    ) INTO v_content_assignments_muted_exists;

    -- Verify all columns created
    IF NOT v_volume_level_exists THEN
        RAISE EXCEPTION 'Migration failed: devices.volume_level not created';
    END IF;

    IF NOT v_device_background_audio_exists THEN
        RAISE EXCEPTION 'Migration failed: devices.background_audio_id not created';
    END IF;

    IF NOT v_playlist_background_audio_exists THEN
        RAISE EXCEPTION 'Migration failed: playlists.background_audio_id not created';
    END IF;

    IF NOT v_playlist_contents_muted_exists THEN
        RAISE EXCEPTION 'Migration failed: playlist_contents.is_muted not created';
    END IF;

    IF NOT v_content_assignments_muted_exists THEN
        RAISE EXCEPTION 'Migration failed: content_assignments.is_muted not created';
    END IF;

    RAISE NOTICE '✓ Migration 047 completed successfully';
    RAISE NOTICE '✓ devices.volume_level added (0-100 volume control)';
    RAISE NOTICE '✓ devices.background_audio_id added (device-level background audio)';
    RAISE NOTICE '✓ playlists.background_audio_id added (playlist-level background audio)';
    RAISE NOTICE '✓ playlist_contents.is_muted added (per-content mute in playlists)';
    RAISE NOTICE '✓ content_assignments.is_muted added (per-content mute in direct assignments)';
    RAISE NOTICE '✓ Indexes created for performance';
END $$;

COMMIT;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Set device volume to 50%
-- UPDATE devices SET volume_level = 50 WHERE id = 1;

-- Example 2: Assign background audio to device (will loop continuously)
-- UPDATE devices SET background_audio_id = 123 WHERE id = 1;

-- Example 3: Assign background audio to playlist (loops when playlist active)
-- UPDATE playlists SET background_audio_id = 456 WHERE id = 5;

-- Example 4: Mute specific content in playlist
-- UPDATE playlist_contents SET is_muted = TRUE WHERE playlist_id = 5 AND content_id = 10;

-- Example 5: Mute content in direct assignment
-- UPDATE content_assignments SET is_muted = TRUE WHERE device_id = 1 AND content_id = 20;

-- ============================================================================
-- MIGRATION INSTRUCTIONS
-- ============================================================================

-- To run this migration on server:
-- 1. Backup database first
-- 2. Stop backend: docker-compose -f docker/docker-compose.yml stop backend-api
-- 3. Upload migration file
-- 4. Run: docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/047_add_audio_control_features.sql
-- 5. Verify output shows all checkmarks (✓)
-- 6. Restart backend: docker-compose -f docker/docker-compose.yml start backend-api
