-- Migration: 079
-- Description: Migrate existing schedule targeting data from JSONB to junction tables
-- Date: 2025-12-04
-- Impact: Data migration only - run AFTER 078 and backend/CMS/player updates
-- Note: Run this ONLY after all apps support the new junction tables

BEGIN;

-- ============================================================================
-- 1. MIGRATE device_ids JSONB ARRAY TO schedule_device_targeting
-- ============================================================================

INSERT INTO schedule_device_targeting (schedule_id, device_id, created_at)
SELECT
    s.id AS schedule_id,
    (jsonb_array_elements_text(s.device_ids))::integer AS device_id,
    COALESCE(s.created_at, NOW()) AS created_at
FROM schedules s
WHERE s.device_ids IS NOT NULL
  AND s.device_ids != '[]'::jsonb
  AND s.device_ids != 'null'::jsonb
  AND jsonb_typeof(s.device_ids) = 'array'
  AND jsonb_array_length(s.device_ids) > 0
ON CONFLICT (schedule_id, device_id) DO NOTHING;

-- ============================================================================
-- 2. MIGRATE tag_ids JSONB ARRAY TO schedule_tag_targeting
-- ============================================================================

INSERT INTO schedule_tag_targeting (schedule_id, tag_id, created_at)
SELECT
    s.id AS schedule_id,
    (jsonb_array_elements_text(s.tag_ids))::integer AS tag_id,
    COALESCE(s.created_at, NOW()) AS created_at
FROM schedules s
WHERE s.tag_ids IS NOT NULL
  AND s.tag_ids != '[]'::jsonb
  AND s.tag_ids != 'null'::jsonb
  AND jsonb_typeof(s.tag_ids) = 'array'
  AND jsonb_array_length(s.tag_ids) > 0
ON CONFLICT (schedule_id, tag_id) DO NOTHING;

-- ============================================================================
-- 3. VERIFICATION QUERIES (run manually to verify migration)
-- ============================================================================

-- Check device targeting migration count
-- SELECT
--     (SELECT COUNT(*) FROM schedules WHERE device_ids IS NOT NULL AND jsonb_array_length(device_ids) > 0) AS source_schedules,
--     (SELECT COUNT(DISTINCT schedule_id) FROM schedule_device_targeting) AS migrated_schedules,
--     (SELECT COUNT(*) FROM schedule_device_targeting) AS total_device_targets;

-- Check tag targeting migration count
-- SELECT
--     (SELECT COUNT(*) FROM schedules WHERE tag_ids IS NOT NULL AND jsonb_array_length(tag_ids) > 0) AS source_schedules,
--     (SELECT COUNT(DISTINCT schedule_id) FROM schedule_tag_targeting) AS migrated_schedules,
--     (SELECT COUNT(*) FROM schedule_tag_targeting) AS total_tag_targets;

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed):
-- TRUNCATE TABLE schedule_device_targeting;
-- TRUNCATE TABLE schedule_tag_targeting;
-- ============================================================================
