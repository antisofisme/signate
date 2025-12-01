-- Migration: 067
-- Description: Remove device_group_id from playlist_assignments and schedules
--              Device Groups are for VIEW MANAGEMENT ONLY (organizing devices visually)
--              NOT for assigning playlists, content, or tags
-- Date: 2025-12-01

BEGIN;

-- =============================================================================
-- ARCHITECTURE DECISION:
-- Device Groups should ONLY be used for visual organization of devices in the UI.
-- Content assignment flows:
--   1. Direct: Content/Playlist -> Device
--   2. Tag-based: Content -> Tag -> Device (devices inherit content from their tags)
-- Device Groups should NOT be a content assignment target.
-- =============================================================================

-- Check if column exists and has data before dropping
DO $$
DECLARE
    group_assignment_count INTEGER;
    schedule_group_count INTEGER;
BEGIN
    -- Check playlist_assignments for device_group_id data
    SELECT COUNT(*) INTO group_assignment_count
    FROM playlist_assignments
    WHERE device_group_id IS NOT NULL;

    IF group_assignment_count > 0 THEN
        RAISE NOTICE 'WARNING: Found % playlist assignments with device_group_id. These will be orphaned.', group_assignment_count;
    END IF;

    -- Check schedules for device_group_id data
    SELECT COUNT(*) INTO schedule_group_count
    FROM schedules
    WHERE device_group_id IS NOT NULL;

    IF schedule_group_count > 0 THEN
        RAISE NOTICE 'WARNING: Found % schedules with device_group_id. These will be orphaned.', schedule_group_count;
    END IF;
END $$;

-- Remove device_group_id from playlist_assignments
-- This column was added in migration 012 but should not exist based on architecture
ALTER TABLE playlist_assignments DROP COLUMN IF EXISTS device_group_id;

-- Remove device_group_id from schedules
-- Schedules should target devices directly, not device groups
ALTER TABLE schedules DROP COLUMN IF EXISTS device_group_id;

-- Update comments
COMMENT ON TABLE playlist_assignments IS 'Assigns playlists to devices (device_id only). Tag assignments have been deprecated.';
COMMENT ON TABLE device_groups IS 'Device groups for VISUAL ORGANIZATION only. Cannot be assigned playlists or content.';

-- Record migration
INSERT INTO _migrations (name) VALUES ('067_remove_device_group_assignments')
ON CONFLICT (name) DO NOTHING;

COMMIT;
