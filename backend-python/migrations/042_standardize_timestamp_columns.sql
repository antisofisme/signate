-- Migration 042: Standardize Timestamp Column Naming
-- Purpose: Rename timestamp columns across tables to follow consistent naming convention
-- Convention: Use explicit *_at suffix for all timestamp columns (e.g., created_at, updated_at, last_seen_at)
-- Author: System Migration
-- Date: 2025-11-13

-- ============================================================================
-- PHASE 1: RENAME COLUMNS
-- ============================================================================

-- 1. devices.last_seen → last_seen_at
-- Tracks when device last sent heartbeat/communication
ALTER TABLE devices
    RENAME COLUMN last_seen TO last_seen_at;

COMMENT ON COLUMN devices.last_seen_at IS
    'Timestamp when device last sent heartbeat or communication (renamed from last_seen)';

-- 2. user_sessions.last_activity → last_activity_at
-- Tracks most recent user activity in session
ALTER TABLE user_sessions
    RENAME COLUMN last_activity TO last_activity_at;

COMMENT ON COLUMN user_sessions.last_activity_at IS
    'Timestamp of most recent user activity in this session (renamed from last_activity)';

-- 3. contents.last_updated → updated_at
-- Tracks when content metadata was last modified
ALTER TABLE contents
    RENAME COLUMN last_updated TO updated_at;

COMMENT ON COLUMN contents.updated_at IS
    'Timestamp when content was last modified (renamed from last_updated)';

-- 4. pms_guests.last_updated → updated_at
-- Tracks when guest record was last modified
ALTER TABLE pms_guests
    RENAME COLUMN last_updated TO updated_at;

COMMENT ON COLUMN pms_guests.updated_at IS
    'Timestamp when guest record was last modified (renamed from last_updated)';

-- 5. pms_configurations.last_sync → last_synced_at
-- Tracks when PMS configuration last synced with external system
ALTER TABLE pms_configurations
    RENAME COLUMN last_sync TO last_synced_at;

COMMENT ON COLUMN pms_configurations.last_synced_at IS
    'Timestamp of last successful sync with PMS system (renamed from last_sync)';

-- 6. device_logs.timestamp → recorded_at
-- Tracks when log entry was recorded
ALTER TABLE device_logs
    RENAME COLUMN timestamp TO recorded_at;

COMMENT ON COLUMN device_logs.recorded_at IS
    'Timestamp when log entry was recorded (renamed from timestamp)';

-- Note: device_logs.last_error_at already follows convention, no change needed

-- ============================================================================
-- PHASE 2: VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_count INTEGER;
    v_missing_columns TEXT[] := ARRAY[]::TEXT[];
    v_old_columns TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check new columns exist
    SELECT COUNT(*) INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
        AND (
            (table_name = 'devices' AND column_name = 'last_seen_at') OR
            (table_name = 'user_sessions' AND column_name = 'last_activity_at') OR
            (table_name = 'contents' AND column_name = 'updated_at') OR
            (table_name = 'pms_guests' AND column_name = 'updated_at') OR
            (table_name = 'pms_configurations' AND column_name = 'last_synced_at') OR
            (table_name = 'device_logs' AND column_name = 'recorded_at')
        );

    IF v_count != 6 THEN
        -- Find which columns are missing
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'devices' AND column_name = 'last_seen_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'devices.last_seen_at');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'user_sessions' AND column_name = 'last_activity_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'user_sessions.last_activity_at');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'contents' AND column_name = 'updated_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'contents.updated_at');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'pms_guests' AND column_name = 'updated_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'pms_guests.updated_at');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'pms_configurations' AND column_name = 'last_synced_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'pms_configurations.last_synced_at');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'device_logs' AND column_name = 'recorded_at'
        ) THEN
            v_missing_columns := array_append(v_missing_columns, 'device_logs.recorded_at');
        END IF;

        RAISE EXCEPTION 'Migration verification failed: Expected 6 renamed columns, found %. Missing: %',
            v_count, array_to_string(v_missing_columns, ', ');
    END IF;

    -- Check old columns no longer exist
    SELECT COUNT(*) INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
        AND (
            (table_name = 'devices' AND column_name = 'last_seen') OR
            (table_name = 'user_sessions' AND column_name = 'last_activity') OR
            (table_name = 'contents' AND column_name = 'last_updated') OR
            (table_name = 'pms_guests' AND column_name = 'last_updated') OR
            (table_name = 'pms_configurations' AND column_name = 'last_sync') OR
            (table_name = 'device_logs' AND column_name = 'timestamp')
        );

    IF v_count > 0 THEN
        -- Find which old columns still exist
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'devices' AND column_name = 'last_seen'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'devices.last_seen');
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'user_sessions' AND column_name = 'last_activity'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'user_sessions.last_activity');
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'contents' AND column_name = 'last_updated'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'contents.last_updated');
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'pms_guests' AND column_name = 'last_updated'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'pms_guests.last_updated');
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'pms_configurations' AND column_name = 'last_sync'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'pms_configurations.last_sync');
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'device_logs' AND column_name = 'timestamp'
        ) THEN
            v_old_columns := array_append(v_old_columns, 'device_logs.timestamp');
        END IF;

        RAISE EXCEPTION 'Migration verification failed: Old columns still exist: %',
            array_to_string(v_old_columns, ', ');
    END IF;

    -- Verify data types are correct (all should be TIMESTAMP WITH TIME ZONE)
    SELECT COUNT(*) INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
        AND data_type = 'timestamp with time zone'
        AND (
            (table_name = 'devices' AND column_name = 'last_seen_at') OR
            (table_name = 'user_sessions' AND column_name = 'last_activity_at') OR
            (table_name = 'contents' AND column_name = 'updated_at') OR
            (table_name = 'pms_guests' AND column_name = 'updated_at') OR
            (table_name = 'pms_configurations' AND column_name = 'last_synced_at') OR
            (table_name = 'device_logs' AND column_name = 'recorded_at')
        );

    IF v_count != 6 THEN
        RAISE EXCEPTION 'Migration verification failed: Expected all 6 columns to be TIMESTAMP WITH TIME ZONE, found % with correct type', v_count;
    END IF;

    RAISE NOTICE 'Migration 042 verification successful: All 6 timestamp columns renamed and verified';
END $$;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================

/*
-- To rollback this migration, run the following:

ALTER TABLE devices RENAME COLUMN last_seen_at TO last_seen;
ALTER TABLE user_sessions RENAME COLUMN last_activity_at TO last_activity;
ALTER TABLE contents RENAME COLUMN updated_at TO last_updated;
ALTER TABLE pms_guests RENAME COLUMN updated_at TO last_updated;
ALTER TABLE pms_configurations RENAME COLUMN last_synced_at TO last_sync;
ALTER TABLE device_logs RENAME COLUMN recorded_at TO timestamp;

-- Then restore original comments if needed
*/

-- ============================================================================
-- SUMMARY
-- ============================================================================

/*
Tables affected: 5
  - devices
  - user_sessions
  - contents
  - pms_guests
  - pms_configurations
  - device_logs

Columns renamed: 6
  1. devices.last_seen → last_seen_at
  2. user_sessions.last_activity → last_activity_at
  3. contents.last_updated → updated_at
  4. pms_guests.last_updated → updated_at
  5. pms_configurations.last_sync → last_synced_at
  6. device_logs.timestamp → recorded_at

Note: device_logs.last_error_at already follows naming convention, no change needed

Code Impact:
  - All SQLAlchemy models must be updated
  - All DTOs/schemas referencing these columns must be updated
  - All use cases/repositories accessing these columns must be updated
  - See 042_affected_files.txt for complete list of files requiring updates
*/
