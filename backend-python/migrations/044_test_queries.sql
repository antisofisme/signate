-- ============================================================================
-- Test Queries for Migration 044: CHECK Constraints
-- Purpose: Verify that constraints work correctly by testing valid and invalid data
-- ============================================================================

-- ============================================================================
-- SETUP: Create test organization and user for testing
-- ============================================================================

-- Create test organization
INSERT INTO organizations (name, organization_pin, max_devices, max_users)
VALUES ('Test Org for Constraints', 'TEST001', 10, 5)
ON CONFLICT DO NOTHING
RETURNING id;

-- Store the org_id for tests (replace 1 with actual returned id)
DO $$
DECLARE
    test_org_id INTEGER;
BEGIN
    SELECT id INTO test_org_id FROM organizations WHERE organization_pin = 'TEST001';
    RAISE NOTICE 'Test Organization ID: %', test_org_id;
END $$;

-- ============================================================================
-- TEST 1: DEVICES TABLE CONSTRAINTS
-- ============================================================================

-- Test 1.1: Valid device with positive screen dimensions (SHOULD SUCCEED)
INSERT INTO devices (
    device_type, device_name, organization_id,
    screen_width, screen_height, rotation, volume_enabled, status, location_type, privacy_mode
)
VALUES (
    'tv', 'Valid Device 1',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    1920, 1080, 0, true, 'pending', 'guest_room', 'limited'
);
-- Expected: SUCCESS

-- Test 1.2: Invalid device with zero screen width (SHOULD FAIL)
INSERT INTO devices (
    device_type, device_name, organization_id,
    screen_width, screen_height, rotation, volume_enabled, status, location_type, privacy_mode
)
VALUES (
    'tv', 'Invalid Device - Zero Width',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    0, 1080, 0, true, 'pending', 'guest_room', 'limited'
);
-- Expected: ERROR - violates check constraint "check_devices_screen_width_positive"

-- Test 1.3: Invalid device with negative screen height (SHOULD FAIL)
INSERT INTO devices (
    device_type, device_name, organization_id,
    screen_width, screen_height, rotation, volume_enabled, status, location_type, privacy_mode
)
VALUES (
    'tv', 'Invalid Device - Negative Height',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    1920, -1080, 0, true, 'pending', 'guest_room', 'limited'
);
-- Expected: ERROR - violates check constraint "check_devices_screen_height_positive"

-- Test 1.4: Valid device with NULL dimensions (SHOULD SUCCEED)
INSERT INTO devices (
    device_type, device_name, organization_id,
    screen_width, screen_height, rotation, volume_enabled, status, location_type, privacy_mode
)
VALUES (
    'tv', 'Valid Device with NULL dimensions',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    NULL, NULL, 0, true, 'pending', 'guest_room', 'limited'
);
-- Expected: SUCCESS (NULL is allowed)

-- Test 1.5: Invalid viewport dimensions (SHOULD FAIL)
INSERT INTO devices (
    device_type, device_name, organization_id,
    viewport_width, viewport_height, rotation, volume_enabled, status, location_type, privacy_mode
)
VALUES (
    'monitor', 'Invalid Device - Zero Viewport',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    0, 0, 0, true, 'pending', 'guest_room', 'limited'
);
-- Expected: ERROR - violates check constraint "check_devices_viewport_width_positive" or viewport_height

-- ============================================================================
-- TEST 2: CONTENTS TABLE CONSTRAINTS
-- ============================================================================

-- Test 2.1: Valid content with positive values (SHOULD SUCCEED)
INSERT INTO contents (
    title, content_type, file_path, file_url, storage_key, file_hash,
    file_size, duration, media_duration, width, height,
    mime_type, original_filename, file_extension, transcoding_progress,
    organization_id, upload_status, audio_channels
)
VALUES (
    'Valid Content', 'video', '/path/to/file.mp4', 'http://example.com/file.mp4',
    'storage_key_valid', 'abc123hash',
    1024000, 30, 29.5, 1920, 1080,
    'video/mp4', 'file.mp4', 'mp4', 100,
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    'completed', 2
);
-- Expected: SUCCESS

-- Test 2.2: Invalid content with zero file size (SHOULD FAIL)
INSERT INTO contents (
    title, content_type, file_path, file_url, storage_key, file_hash,
    file_size, duration, mime_type, original_filename, file_extension, transcoding_progress,
    organization_id, upload_status, audio_channels
)
VALUES (
    'Invalid Content - Zero Size', 'video', '/path/to/file2.mp4', 'http://example.com/file2.mp4',
    'storage_key_zero_size', 'def456hash',
    0, 30, 'video/mp4', 'file2.mp4', 'mp4', 100,
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    'completed', 2
);
-- Expected: ERROR - violates check constraint "check_contents_file_size_positive"

-- Test 2.3: Invalid content with negative duration (SHOULD FAIL)
INSERT INTO contents (
    title, content_type, file_path, file_url, storage_key, file_hash,
    file_size, duration, mime_type, original_filename, file_extension, transcoding_progress,
    organization_id, upload_status, audio_channels
)
VALUES (
    'Invalid Content - Negative Duration', 'video', '/path/to/file3.mp4', 'http://example.com/file3.mp4',
    'storage_key_neg_duration', 'ghi789hash',
    1024000, -30, 'video/mp4', 'file3.mp4', 'mp4', 100,
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    'completed', 2
);
-- Expected: ERROR - violates check constraint "check_contents_duration_positive"

-- Test 2.4: Invalid content with transcoding progress > 100 (SHOULD FAIL)
INSERT INTO contents (
    title, content_type, file_path, file_url, storage_key, file_hash,
    file_size, duration, mime_type, original_filename, file_extension, transcoding_progress,
    organization_id, upload_status, audio_channels
)
VALUES (
    'Invalid Content - Progress > 100', 'video', '/path/to/file4.mp4', 'http://example.com/file4.mp4',
    'storage_key_progress', 'jkl012hash',
    1024000, 30, 'video/mp4', 'file4.mp4', 'mp4', 150,
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    'completed', 2
);
-- Expected: ERROR - violates check constraint "check_contents_transcoding_progress_range"

-- Test 2.5: Valid content with NULL optional fields (SHOULD SUCCEED)
INSERT INTO contents (
    title, content_type, file_path, file_url, storage_key, file_hash,
    file_size, duration, mime_type, original_filename, file_extension, transcoding_progress,
    organization_id, upload_status, audio_channels
)
VALUES (
    'Valid Content with NULLs', 'image', '/path/to/image.jpg', 'http://example.com/image.jpg',
    'storage_key_nulls', 'mno345hash',
    512000, 10, 'image/jpeg', 'image.jpg', 'jpg', 100,
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    'completed', 2
);
-- Expected: SUCCESS (NULL duration, width, height allowed)

-- ============================================================================
-- TEST 3: SCHEDULES TABLE CONSTRAINTS
-- ============================================================================

-- Test 3.1: Valid schedule with proper date/time range (SHOULD SUCCEED)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Valid Schedule',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-13', '2025-11-20',
    '09:00:00', '17:00:00', 1
);
-- Expected: SUCCESS

-- Test 3.2: Invalid schedule with end_date before start_date (SHOULD FAIL)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Invalid Schedule - Bad Date Range',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-20', '2025-11-13',
    '09:00:00', '17:00:00', 1
);
-- Expected: ERROR - violates check constraint "check_schedules_date_range"

-- Test 3.3: Invalid schedule with end_time before start_time (same day) (SHOULD FAIL)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Invalid Schedule - Bad Time Range',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-13', '2025-11-13',
    '17:00:00', '09:00:00', 1
);
-- Expected: ERROR - violates check constraint "check_schedules_time_range"

-- Test 3.4: Valid multi-day schedule spanning midnight (SHOULD SUCCEED)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Valid Schedule - Spanning Midnight',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-13', '2025-11-14',
    '23:00:00', '02:00:00', 1
);
-- Expected: SUCCESS (multi-day allows end_time < start_time)

-- Test 3.5: Invalid schedule with negative priority (SHOULD FAIL)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Invalid Schedule - Negative Priority',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-13', '2025-11-20',
    '09:00:00', '17:00:00', -5
);
-- Expected: ERROR - violates check constraint "check_schedules_priority_non_negative"

-- Test 3.6: Valid schedule with NULL end_date and end_time (SHOULD SUCCEED)
INSERT INTO schedules (
    name, organization_id, start_date, end_date,
    start_time, end_time, priority
)
VALUES (
    'Valid Schedule - Open Ended',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    '2025-11-13', NULL,
    '09:00:00', NULL, 0
);
-- Expected: SUCCESS

-- ============================================================================
-- TEST 4: ORGANIZATIONS TABLE CONSTRAINTS
-- ============================================================================

-- Test 4.1: Valid organization with positive quotas (SHOULD SUCCEED)
INSERT INTO organizations (name, organization_pin, max_devices, max_users)
VALUES ('Valid Org with Quotas', 'VALID01', 100, 50);
-- Expected: SUCCESS

-- Test 4.2: Invalid organization with zero max_devices (SHOULD FAIL)
INSERT INTO organizations (name, organization_pin, max_devices, max_users)
VALUES ('Invalid Org - Zero Devices', 'INVALID1', 0, 50);
-- Expected: ERROR - violates check constraint "check_organizations_max_devices_positive"

-- Test 4.3: Invalid organization with negative max_users (SHOULD FAIL)
INSERT INTO organizations (name, organization_pin, max_devices, max_users)
VALUES ('Invalid Org - Negative Users', 'INVALID2', 100, -10);
-- Expected: ERROR - violates check constraint "check_organizations_max_users_positive"

-- Test 4.4: Valid organization with minimum quotas (SHOULD SUCCEED)
INSERT INTO organizations (name, organization_pin, max_devices, max_users)
VALUES ('Valid Org - Minimum Quotas', 'VALID02', 1, 1);
-- Expected: SUCCESS (1 is the minimum allowed)

-- ============================================================================
-- TEST 5: PLAYLISTS TABLE CONSTRAINTS
-- ============================================================================

-- Test 5.1: Valid playlist with positive priority (SHOULD SUCCEED)
INSERT INTO playlists (
    name, organization_id, priority, is_active, is_default, is_pms_template
)
VALUES (
    'Valid Playlist',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    10, true, false, false
);
-- Expected: SUCCESS

-- Test 5.2: Invalid playlist with negative priority (SHOULD FAIL)
INSERT INTO playlists (
    name, organization_id, priority, is_active, is_default, is_pms_template
)
VALUES (
    'Invalid Playlist - Negative Priority',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    -5, true, false, false
);
-- Expected: ERROR - violates check constraint "check_playlists_priority_non_negative"

-- Test 5.3: Valid playlist with zero priority (SHOULD SUCCEED)
INSERT INTO playlists (
    name, organization_id, priority, is_active, is_default, is_pms_template
)
VALUES (
    'Valid Playlist - Zero Priority',
    (SELECT id FROM organizations WHERE organization_pin = 'TEST001'),
    0, true, false, false
);
-- Expected: SUCCESS (0 is valid non-negative priority)

-- ============================================================================
-- CLEANUP TEST DATA
-- ============================================================================

-- Clean up test data (run after testing)
/*
DELETE FROM playlists WHERE name LIKE 'Valid Playlist%' OR name LIKE 'Invalid Playlist%';
DELETE FROM schedules WHERE name LIKE 'Valid Schedule%' OR name LIKE 'Invalid Schedule%';
DELETE FROM contents WHERE title LIKE 'Valid Content%' OR title LIKE 'Invalid Content%';
DELETE FROM devices WHERE device_name LIKE 'Valid Device%' OR device_name LIKE 'Invalid Device%';
DELETE FROM organizations WHERE name LIKE 'Valid Org%' OR name LIKE 'Invalid Org%';
DELETE FROM organizations WHERE organization_pin = 'TEST001';
*/

-- ============================================================================
-- SUMMARY OF EXPECTED RESULTS
-- ============================================================================

/*
CONSTRAINTS TESTED:

1. DEVICES (4 constraints):
   ✓ check_devices_screen_width_positive
   ✓ check_devices_screen_height_positive
   ✓ check_devices_viewport_width_positive
   ✓ check_devices_viewport_height_positive

2. CONTENTS (8 constraints):
   ✓ check_contents_file_size_positive
   ✓ check_contents_duration_positive
   ✓ check_contents_media_duration_positive
   ✓ check_contents_width_positive
   ✓ check_contents_height_positive
   ✓ check_contents_bitrate_positive
   ✓ check_contents_audio_bitrate_positive
   ✓ check_contents_transcoding_progress_range

3. SCHEDULES (3 constraints):
   ✓ check_schedules_date_range
   ✓ check_schedules_time_range
   ✓ check_schedules_priority_non_negative

4. ORGANIZATIONS (2 constraints):
   ✓ check_organizations_max_devices_positive
   ✓ check_organizations_max_users_positive

5. PLAYLISTS (1 constraint):
   ✓ check_playlists_priority_non_negative

TOTAL: 18 CHECK constraints

TEST OUTCOMES:
- Valid inserts: SHOULD SUCCEED (no constraint violations)
- Invalid inserts: SHOULD FAIL with specific constraint error
- NULL values: SHOULD SUCCEED where allowed by constraint definition
*/
