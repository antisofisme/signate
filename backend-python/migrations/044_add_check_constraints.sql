-- ============================================================================
-- Migration 044: Add CHECK Constraints for Data Validation
-- Created: 2025-11-13
-- Purpose: Add CHECK constraints to enforce data integrity and business rules
-- ============================================================================

-- ============================================================================
-- PHASE 1: VALIDATE EXISTING DATA
-- ============================================================================
-- This phase checks for any data that would violate the new constraints
-- Run these queries manually before applying the migration to identify issues

-- 1. Check devices table for invalid data
DO $$
BEGIN
    RAISE NOTICE 'Validating devices table...';

    -- Check screen dimensions
    IF EXISTS (
        SELECT 1 FROM devices
        WHERE (screen_width IS NOT NULL AND screen_width <= 0)
           OR (screen_height IS NOT NULL AND screen_height <= 0)
    ) THEN
        RAISE WARNING 'Found devices with invalid screen dimensions (width or height <= 0)';
    END IF;

    -- Check rotation values (should be covered by existing constraint but verify)
    IF EXISTS (
        SELECT 1 FROM devices
        WHERE rotation NOT IN (0, 90, 180, 270)
    ) THEN
        RAISE WARNING 'Found devices with invalid rotation values';
    END IF;

    -- Check viewport dimensions
    IF EXISTS (
        SELECT 1 FROM devices
        WHERE (viewport_width IS NOT NULL AND viewport_width <= 0)
           OR (viewport_height IS NOT NULL AND viewport_height <= 0)
    ) THEN
        RAISE WARNING 'Found devices with invalid viewport dimensions';
    END IF;

    RAISE NOTICE 'Devices validation complete';
END $$;

-- 2. Check contents table for invalid data
DO $$
BEGIN
    RAISE NOTICE 'Validating contents table...';

    -- Check file size
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE file_size IS NOT NULL AND file_size <= 0
    ) THEN
        RAISE WARNING 'Found contents with invalid file_size (<= 0)';
    END IF;

    -- Check duration (media_duration is the actual duration column)
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE media_duration IS NOT NULL AND media_duration <= 0
    ) THEN
        RAISE WARNING 'Found contents with invalid media_duration (<= 0)';
    END IF;

    -- Check display duration
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE duration IS NOT NULL AND duration <= 0
    ) THEN
        RAISE WARNING 'Found contents with invalid duration (<= 0)';
    END IF;

    -- Check dimensions
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE (width IS NOT NULL AND width <= 0)
           OR (height IS NOT NULL AND height <= 0)
    ) THEN
        RAISE WARNING 'Found contents with invalid dimensions (width or height <= 0)';
    END IF;

    -- Check bitrates
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE (bitrate IS NOT NULL AND bitrate <= 0)
           OR (audio_bitrate IS NOT NULL AND audio_bitrate <= 0)
    ) THEN
        RAISE WARNING 'Found contents with invalid bitrate values';
    END IF;

    -- Check transcoding progress
    IF EXISTS (
        SELECT 1 FROM contents
        WHERE transcoding_progress < 0 OR transcoding_progress > 100
    ) THEN
        RAISE WARNING 'Found contents with invalid transcoding_progress (not in 0-100 range)';
    END IF;

    RAISE NOTICE 'Contents validation complete';
END $$;

-- 3. Check schedules table for invalid data
DO $$
BEGIN
    RAISE NOTICE 'Validating schedules table...';

    -- Check date ranges
    IF EXISTS (
        SELECT 1 FROM schedules
        WHERE end_date IS NOT NULL AND end_date < start_date
    ) THEN
        RAISE WARNING 'Found schedules with end_date before start_date';
    END IF;

    -- Check time ranges (only when on same day)
    IF EXISTS (
        SELECT 1 FROM schedules
        WHERE end_time IS NOT NULL
          AND start_time IS NOT NULL
          AND end_time <= start_time
          AND (end_date IS NULL OR end_date = start_date)
    ) THEN
        RAISE WARNING 'Found schedules with end_time before or equal to start_time on same day';
    END IF;

    -- Check priority
    IF EXISTS (
        SELECT 1 FROM schedules
        WHERE priority IS NOT NULL AND priority < 0
    ) THEN
        RAISE WARNING 'Found schedules with negative priority';
    END IF;

    RAISE NOTICE 'Schedules validation complete';
END $$;

-- 4. Check organizations table for invalid data
DO $$
BEGIN
    RAISE NOTICE 'Validating organizations table...';

    -- Check max_devices
    IF EXISTS (
        SELECT 1 FROM organizations
        WHERE max_devices <= 0
    ) THEN
        RAISE WARNING 'Found organizations with max_devices <= 0';
    END IF;

    -- Check max_users
    IF EXISTS (
        SELECT 1 FROM organizations
        WHERE max_users <= 0
    ) THEN
        RAISE WARNING 'Found organizations with max_users <= 0';
    END IF;

    RAISE NOTICE 'Organizations validation complete';
END $$;

-- 5. Check playlists table for invalid data
DO $$
BEGIN
    RAISE NOTICE 'Validating playlists table...';

    -- Check priority
    IF EXISTS (
        SELECT 1 FROM playlists
        WHERE priority < 0
    ) THEN
        RAISE WARNING 'Found playlists with negative priority';
    END IF;

    RAISE NOTICE 'Playlists validation complete';
END $$;

-- ============================================================================
-- PHASE 2: ADD CHECK CONSTRAINTS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DEVICES TABLE CONSTRAINTS
-- ----------------------------------------------------------------------------

-- Screen dimensions must be positive when specified
ALTER TABLE devices
ADD CONSTRAINT check_devices_screen_width_positive
CHECK (screen_width IS NULL OR screen_width > 0);

ALTER TABLE devices
ADD CONSTRAINT check_devices_screen_height_positive
CHECK (screen_height IS NULL OR screen_height > 0);

-- Viewport dimensions must be positive when specified
ALTER TABLE devices
ADD CONSTRAINT check_devices_viewport_width_positive
CHECK (viewport_width IS NULL OR viewport_width > 0);

ALTER TABLE devices
ADD CONSTRAINT check_devices_viewport_height_positive
CHECK (viewport_height IS NULL OR viewport_height > 0);

-- Note: rotation constraint already exists from table creation (0, 90, 180, 270)
-- Note: volume constraint not added as volume_enabled is boolean (no volume level stored)

COMMENT ON CONSTRAINT check_devices_screen_width_positive ON devices
IS 'Ensures screen width is positive when specified';

COMMENT ON CONSTRAINT check_devices_screen_height_positive ON devices
IS 'Ensures screen height is positive when specified';

COMMENT ON CONSTRAINT check_devices_viewport_width_positive ON devices
IS 'Ensures viewport width is positive when specified';

COMMENT ON CONSTRAINT check_devices_viewport_height_positive ON devices
IS 'Ensures viewport height is positive when specified';

-- ----------------------------------------------------------------------------
-- 2. CONTENTS TABLE CONSTRAINTS
-- ----------------------------------------------------------------------------

-- File size must be positive
ALTER TABLE contents
ADD CONSTRAINT check_contents_file_size_positive
CHECK (file_size IS NULL OR file_size > 0);

-- Display duration must be positive (duration column - display time in seconds)
ALTER TABLE contents
ADD CONSTRAINT check_contents_duration_positive
CHECK (duration IS NULL OR duration > 0);

-- Media duration must be positive (actual media length)
ALTER TABLE contents
ADD CONSTRAINT check_contents_media_duration_positive
CHECK (media_duration IS NULL OR media_duration > 0);

-- Width and height must be positive when specified
ALTER TABLE contents
ADD CONSTRAINT check_contents_width_positive
CHECK (width IS NULL OR width > 0);

ALTER TABLE contents
ADD CONSTRAINT check_contents_height_positive
CHECK (height IS NULL OR height > 0);

-- Bitrates must be positive
ALTER TABLE contents
ADD CONSTRAINT check_contents_bitrate_positive
CHECK (bitrate IS NULL OR bitrate > 0);

ALTER TABLE contents
ADD CONSTRAINT check_contents_audio_bitrate_positive
CHECK (audio_bitrate IS NULL OR audio_bitrate > 0);

-- Transcoding progress must be between 0 and 100
ALTER TABLE contents
ADD CONSTRAINT check_contents_transcoding_progress_range
CHECK (transcoding_progress >= 0 AND transcoding_progress <= 100);

COMMENT ON CONSTRAINT check_contents_file_size_positive ON contents
IS 'Ensures file size is positive when specified';

COMMENT ON CONSTRAINT check_contents_duration_positive ON contents
IS 'Ensures display duration is positive when specified';

COMMENT ON CONSTRAINT check_contents_media_duration_positive ON contents
IS 'Ensures media duration (actual length) is positive when specified';

COMMENT ON CONSTRAINT check_contents_transcoding_progress_range ON contents
IS 'Ensures transcoding progress is between 0 and 100 percent';

-- ----------------------------------------------------------------------------
-- 3. SCHEDULES TABLE CONSTRAINTS
-- ----------------------------------------------------------------------------

-- End date must be on or after start date when specified
ALTER TABLE schedules
ADD CONSTRAINT check_schedules_date_range
CHECK (end_date IS NULL OR end_date >= start_date);

-- End time must be after start time when on same day
-- Note: This is a simplified check. For multi-day schedules spanning midnight,
-- end_time can be before start_time (e.g., 23:00 to 02:00 next day)
ALTER TABLE schedules
ADD CONSTRAINT check_schedules_time_range
CHECK (
    end_time IS NULL
    OR start_time IS NULL
    OR end_date IS NOT NULL
    OR end_time > start_time
);

-- Priority must be non-negative
ALTER TABLE schedules
ADD CONSTRAINT check_schedules_priority_non_negative
CHECK (priority IS NULL OR priority >= 0);

COMMENT ON CONSTRAINT check_schedules_date_range ON schedules
IS 'Ensures end date is on or after start date';

COMMENT ON CONSTRAINT check_schedules_time_range ON schedules
IS 'Ensures end time is after start time for same-day schedules';

COMMENT ON CONSTRAINT check_schedules_priority_non_negative ON schedules
IS 'Ensures priority is non-negative (higher priority = higher number)';

-- ----------------------------------------------------------------------------
-- 4. ORGANIZATIONS TABLE CONSTRAINTS
-- ----------------------------------------------------------------------------

-- Max devices must be positive
ALTER TABLE organizations
ADD CONSTRAINT check_organizations_max_devices_positive
CHECK (max_devices > 0);

-- Max users must be positive
ALTER TABLE organizations
ADD CONSTRAINT check_organizations_max_users_positive
CHECK (max_users > 0);

COMMENT ON CONSTRAINT check_organizations_max_devices_positive ON organizations
IS 'Ensures organization can have at least 1 device (business rule)';

COMMENT ON CONSTRAINT check_organizations_max_users_positive ON organizations
IS 'Ensures organization can have at least 1 user (business rule)';

-- ----------------------------------------------------------------------------
-- 5. PLAYLISTS TABLE CONSTRAINTS
-- ----------------------------------------------------------------------------

-- Priority must be non-negative
ALTER TABLE playlists
ADD CONSTRAINT check_playlists_priority_non_negative
CHECK (priority >= 0);

COMMENT ON CONSTRAINT check_playlists_priority_non_negative ON playlists
IS 'Ensures priority is non-negative (higher priority = higher number)';

-- ============================================================================
-- PHASE 3: VERIFICATION
-- ============================================================================

-- Verify all constraints were created successfully
DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    RAISE NOTICE 'Verifying CHECK constraints...';

    -- Count CHECK constraints added by this migration
    SELECT COUNT(*) INTO constraint_count
    FROM pg_constraint
    WHERE contype = 'c'
    AND conname LIKE 'check_%'
    AND conrelid IN (
        'devices'::regclass,
        'contents'::regclass,
        'schedules'::regclass,
        'organizations'::regclass,
        'playlists'::regclass
    );

    RAISE NOTICE 'Total CHECK constraints on target tables: %', constraint_count;

    -- List all CHECK constraints
    RAISE NOTICE 'Listing all CHECK constraints:';
    FOR constraint_count IN (
        SELECT conname
        FROM pg_constraint
        WHERE contype = 'c'
        AND conrelid IN (
            'devices'::regclass,
            'contents'::regclass,
            'schedules'::regclass,
            'organizations'::regclass,
            'playlists'::regclass
        )
        ORDER BY conrelid, conname
    ) LOOP
        NULL;
    END LOOP;

    RAISE NOTICE 'Verification complete';
END $$;

-- Display constraint details
SELECT
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
AND tc.table_name IN ('devices', 'contents', 'schedules', 'organizations', 'playlists')
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- PHASE 4: ROLLBACK INSTRUCTIONS
-- ============================================================================

-- To rollback this migration, run the following:
/*
-- Devices table
ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_screen_width_positive;
ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_screen_height_positive;
ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_viewport_width_positive;
ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_viewport_height_positive;

-- Contents table
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_file_size_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_duration_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_media_duration_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_width_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_height_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_bitrate_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_audio_bitrate_positive;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS check_contents_transcoding_progress_range;

-- Schedules table
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS check_schedules_date_range;
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS check_schedules_time_range;
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS check_schedules_priority_non_negative;

-- Organizations table
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS check_organizations_max_devices_positive;
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS check_organizations_max_users_positive;

-- Playlists table
ALTER TABLE playlists DROP CONSTRAINT IF EXISTS check_playlists_priority_non_negative;
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
