-- ============================================================================
-- Migration 012: Fix Device Defaults Consistency
-- Description: Standardize device table default values (conflicting migrations 004 & 006)
-- Created: 2025-01-09
-- Priority: CRITICAL
-- ============================================================================

BEGIN;

-- ============================================================================
-- ISSUE SUMMARY
-- ============================================================================
-- Migration 004 (004_allow_null_organization_id.sql) set defaults:
--   - location_type = 'lobby'
--   - privacy_mode = 'normal'
--   - supports_personalization = FALSE
--   - volume_enabled = FALSE
--
-- Migration 006 (006_create_devices_table.sql) had original defaults:
--   - location_type = 'guest_room'
--   - privacy_mode = 'limited'
--   - supports_personalization = TRUE
--   - volume_enabled = TRUE
--
-- Decision: Use Migration 006 defaults (original design intent)
-- ============================================================================

-- ============================================================================
-- 1. FIX DEFAULT VALUES
-- ============================================================================

-- Fix location_type default
ALTER TABLE devices
    ALTER COLUMN location_type SET DEFAULT 'guest_room';

-- Fix privacy_mode default
ALTER TABLE devices
    ALTER COLUMN privacy_mode SET DEFAULT 'limited';

-- Fix supports_personalization default
ALTER TABLE devices
    ALTER COLUMN supports_personalization SET DEFAULT TRUE;

-- Fix volume_enabled default
ALTER TABLE devices
    ALTER COLUMN volume_enabled SET DEFAULT TRUE;

-- Fix rotation default (ensure consistency)
ALTER TABLE devices
    ALTER COLUMN rotation SET DEFAULT 0;

-- ============================================================================
-- 2. UPDATE COMMENTS TO REFLECT CORRECT DEFAULTS
-- ============================================================================

COMMENT ON COLUMN devices.location_type IS
    'Device location type in hotel (guest_room, lobby, restaurant, etc.) - DEFAULT: guest_room';

COMMENT ON COLUMN devices.privacy_mode IS
    'Privacy level: none (full access), limited (restricted), full (maximum privacy) - DEFAULT: limited';

COMMENT ON COLUMN devices.supports_personalization IS
    'Supports personalized content - DEFAULT: TRUE';

COMMENT ON COLUMN devices.volume_enabled IS
    'Audio enabled - DEFAULT: TRUE';

COMMENT ON COLUMN devices.rotation IS
    'Screen rotation in degrees (0, 90, 180, 270) - DEFAULT: 0';

-- ============================================================================
-- 3. UPDATE EXISTING NULL VALUES (Optional - apply defaults retroactively)
-- ============================================================================

-- Only update rows where values are NULL (don't override explicit values)

UPDATE devices
SET location_type = 'guest_room'
WHERE location_type IS NULL;

UPDATE devices
SET privacy_mode = 'limited'
WHERE privacy_mode IS NULL;

UPDATE devices
SET supports_personalization = TRUE
WHERE supports_personalization IS NULL;

UPDATE devices
SET volume_enabled = TRUE
WHERE volume_enabled IS NULL;

UPDATE devices
SET rotation = 0
WHERE rotation IS NULL;

-- ============================================================================
-- 4. VERIFICATION QUERY
-- ============================================================================

-- Verify default values
SELECT
    column_name,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'devices'
  AND column_name IN ('location_type', 'privacy_mode', 'supports_personalization', 'volume_enabled', 'rotation')
ORDER BY column_name;

-- Count affected rows (should be 0 if migration ran on fresh database)
SELECT
    'location_type' as column_name,
    count(*) FILTER (WHERE location_type = 'guest_room') as default_value_count,
    count(*) FILTER (WHERE location_type IS NULL) as null_count
FROM devices
UNION ALL
SELECT
    'privacy_mode',
    count(*) FILTER (WHERE privacy_mode = 'limited'),
    count(*) FILTER (WHERE privacy_mode IS NULL)
FROM devices
UNION ALL
SELECT
    'supports_personalization',
    count(*) FILTER (WHERE supports_personalization = TRUE),
    count(*) FILTER (WHERE supports_personalization IS NULL)
FROM devices
UNION ALL
SELECT
    'volume_enabled',
    count(*) FILTER (WHERE volume_enabled = TRUE),
    count(*) FILTER (WHERE volume_enabled IS NULL)
FROM devices;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

-- To rollback to Migration 004 defaults:
/*
BEGIN;

ALTER TABLE devices ALTER COLUMN location_type SET DEFAULT 'lobby';
ALTER TABLE devices ALTER COLUMN privacy_mode SET DEFAULT 'normal';
ALTER TABLE devices ALTER COLUMN supports_personalization SET DEFAULT FALSE;
ALTER TABLE devices ALTER COLUMN volume_enabled SET DEFAULT FALSE;

COMMIT;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/012_fix_device_defaults_consistency.sql
