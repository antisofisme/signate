-- ============================================================================
-- Post-Migration Verification Script for Migration 007
-- Rename content table to contents
-- ============================================================================
-- Purpose: Verify migration success and data integrity
-- Run this AFTER executing migration 007
-- ============================================================================

\echo '============================================================================'
\echo 'POST-MIGRATION VERIFICATION FOR MIGRATION 007'
\echo 'Testing Date:' `date`
\echo '============================================================================'
\echo ''

-- ============================================================================
-- TEST 1: Verify table renamed to 'contents'
-- ============================================================================
\echo '--- TEST 1: Verify table renamed to "contents" ---'
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'contents'
        ) THEN 'PASS: Table "contents" exists'
        ELSE 'FAIL: Table "contents" does not exist!'
    END as test_result;

SELECT
    CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'content'
        ) THEN 'PASS: Old table "content" no longer exists (expected)'
        ELSE 'FAIL: Old table "content" still exists! Migration incomplete.'
    END as test_result;

\echo ''

-- ============================================================================
-- TEST 2: Verify record count matches pre-migration baseline
-- ============================================================================
\echo '--- TEST 2: Verify record count integrity ---'
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active_records,
    COUNT(*) FILTER (WHERE is_active = false) as inactive_records,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as soft_deleted_records,
    COUNT(*) FILTER (WHERE fallback_content_id IS NOT NULL) as records_with_fallback,
    COALESCE(SUM(file_size), 0) as total_file_size
FROM contents;

\echo ''
\echo 'IMPORTANT: Compare these counts with pre-migration output'
\echo 'All counts should match exactly!'
\echo ''

-- ============================================================================
-- TEST 3: Verify all 4 foreign keys recreated correctly
-- ============================================================================
\echo '--- TEST 3: Foreign key constraints on "contents" ---'
SELECT
    conname as constraint_name,
    conrelid::regclass as source_table,
    confrelid::regclass as referenced_table,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE confrelid = 'contents'::regclass
ORDER BY conrelid::regclass::text, conname;

\echo ''

-- Count foreign keys
SELECT
    COUNT(*) as fk_count,
    CASE
        WHEN COUNT(*) = 4 THEN 'PASS: All 4 foreign keys exist'
        ELSE 'FAIL: Expected 4 foreign keys, found ' || COUNT(*)
    END as test_result
FROM pg_constraint
WHERE confrelid = 'contents'::regclass;

\echo ''
\echo 'Expected foreign keys:'
\echo '  1. content_assignments_content_id_fkey (content_assignments -> contents)'
\echo '  2. playlist_content_content_id_fkey (playlist_content -> contents)'
\echo '  3. schedules_content_id_fkey (schedules -> contents)'
\echo '  4. content_fallback_content_id_fkey (contents -> contents) [SELF-REFERENTIAL]'
\echo ''

-- ============================================================================
-- TEST 4: Verify each foreign key individually
-- ============================================================================
\echo '--- TEST 4: Individual FK verification ---'

-- FK 1: content_assignments
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'content_assignments'::regclass
              AND confrelid = 'contents'::regclass
              AND conname = 'content_assignments_content_id_fkey'
        ) THEN 'PASS: content_assignments FK exists'
        ELSE 'FAIL: content_assignments FK missing!'
    END as test_result;

-- FK 2: playlist_content
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'playlist_content'::regclass
              AND confrelid = 'contents'::regclass
              AND conname = 'playlist_content_content_id_fkey'
        ) THEN 'PASS: playlist_content FK exists'
        ELSE 'FAIL: playlist_content FK missing!'
    END as test_result;

-- FK 3: schedules
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'schedules'::regclass
              AND confrelid = 'contents'::regclass
              AND conname = 'schedules_content_id_fkey'
        ) THEN 'PASS: schedules FK exists'
        ELSE 'FAIL: schedules FK missing!'
    END as test_result;

-- FK 4: self-referential
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'contents'::regclass
              AND confrelid = 'contents'::regclass
              AND conname = 'content_fallback_content_id_fkey'
        ) THEN 'PASS: Self-referential FK exists'
        ELSE 'FAIL: Self-referential FK missing!'
    END as test_result;

\echo ''

-- ============================================================================
-- TEST 5: Verify CASCADE DELETE behavior on FKs
-- ============================================================================
\echo '--- TEST 5: Verify CASCADE DELETE behavior ---'
SELECT
    conname as constraint_name,
    conrelid::regclass as source_table,
    confdeltype as delete_action,
    CASE confdeltype
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'a' THEN 'NO ACTION'
        ELSE 'UNKNOWN'
    END as delete_action_name
FROM pg_constraint
WHERE confrelid = 'contents'::regclass
ORDER BY conrelid::regclass::text;

\echo ''
\echo 'Expected delete actions:'
\echo '  - content_assignments: CASCADE'
\echo '  - playlist_content: CASCADE'
\echo '  - schedules: CASCADE'
\echo '  - contents (self-ref): SET NULL'
\echo ''

-- ============================================================================
-- TEST 6: Verify indexes still exist
-- ============================================================================
\echo '--- TEST 6: Indexes on contents table ---'
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'contents'
ORDER BY indexname;

\echo ''

SELECT
    COUNT(*) as index_count,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS: Indexes exist on contents table'
        ELSE 'WARNING: No indexes found on contents table'
    END as test_result
FROM pg_indexes
WHERE tablename = 'contents';

\echo ''

-- ============================================================================
-- TEST 7: Verify self-referential FK works (data integrity)
-- ============================================================================
\echo '--- TEST 7: Self-referential FK data integrity ---'
SELECT
    c1.id as content_id,
    c1.file_name as content_name,
    c1.fallback_content_id,
    c2.file_name as fallback_content_name
FROM contents c1
LEFT JOIN contents c2 ON c1.fallback_content_id = c2.id
WHERE c1.fallback_content_id IS NOT NULL
LIMIT 5;

\echo ''

SELECT
    COUNT(*) as records_with_fallback,
    COUNT(c2.id) as valid_fallback_references,
    CASE
        WHEN COUNT(*) = COUNT(c2.id) THEN 'PASS: All fallback references are valid'
        ELSE 'WARNING: Some fallback references are invalid'
    END as test_result
FROM contents c1
LEFT JOIN contents c2 ON c1.fallback_content_id = c2.id
WHERE c1.fallback_content_id IS NOT NULL;

\echo ''

-- ============================================================================
-- TEST 8: Test CASCADE DELETE behavior (simulation)
-- ============================================================================
\echo '--- TEST 8: CASCADE DELETE simulation (read-only check) ---'
\echo 'This test checks relationships that would be deleted by CASCADE'
\echo ''

-- Count related records for sample contents
SELECT
    'content_assignments' as related_table,
    COUNT(*) as would_be_deleted
FROM content_assignments
WHERE content_id IN (SELECT id FROM contents LIMIT 10)
UNION ALL
SELECT
    'playlist_content' as related_table,
    COUNT(*) as would_be_deleted
FROM playlist_content
WHERE content_id IN (SELECT id FROM contents LIMIT 10)
UNION ALL
SELECT
    'schedules' as related_table,
    COUNT(*) as would_be_deleted
FROM schedules
WHERE content_id IN (SELECT id FROM contents LIMIT 10);

\echo ''
\echo 'NOTE: CASCADE DELETE not actually executed - this is a read-only check'
\echo ''

-- ============================================================================
-- TEST 9: Verify table schema is intact
-- ============================================================================
\echo '--- TEST 9: Table schema verification ---'
\d contents

\echo ''

-- ============================================================================
-- TEST 10: Verify column definitions unchanged
-- ============================================================================
\echo '--- TEST 10: Column definitions ---'
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'contents'
ORDER BY ordinal_position;

\echo ''

-- ============================================================================
-- TEST 11: Sample data integrity check
-- ============================================================================
\echo '--- TEST 11: Sample data integrity ---'
SELECT
    id,
    content_type,
    file_name,
    file_size,
    is_active,
    fallback_content_id,
    created_at
FROM contents
ORDER BY id
LIMIT 5;

\echo ''
\echo 'IMPORTANT: Compare this data with pre-migration output'
\echo 'Data should be identical!'
\echo ''

-- ============================================================================
-- TEST 12: Verify related tables still reference correctly
-- ============================================================================
\echo '--- TEST 12: Related tables referential integrity ---'

-- Test JOIN with content_assignments
SELECT
    'content_assignments JOIN' as test_case,
    COUNT(*) as successful_joins,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS: Can join content_assignments with contents'
        ELSE 'WARNING: No records to join'
    END as test_result
FROM content_assignments ca
INNER JOIN contents c ON ca.content_id = c.id
LIMIT 1;

-- Test JOIN with playlist_content
SELECT
    'playlist_content JOIN' as test_case,
    COUNT(*) as successful_joins,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS: Can join playlist_content with contents'
        ELSE 'WARNING: No records to join'
    END as test_result
FROM playlist_content pc
INNER JOIN contents c ON pc.content_id = c.id
LIMIT 1;

-- Test JOIN with schedules
SELECT
    'schedules JOIN' as test_case,
    COUNT(*) as successful_joins,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS: Can join schedules with contents'
        ELSE 'WARNING: No records to join'
    END as test_result
FROM schedules s
INNER JOIN contents c ON s.content_id = c.id
LIMIT 1;

\echo ''

-- ============================================================================
-- TEST 13: Verify no orphaned records in related tables
-- ============================================================================
\echo '--- TEST 13: Check for orphaned records ---'

-- Check content_assignments for orphans
SELECT
    'content_assignments' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) as orphaned_records,
    CASE
        WHEN COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) = 0
        THEN 'PASS: No orphaned records'
        ELSE 'FAIL: Orphaned records found!'
    END as test_result
FROM content_assignments;

-- Check playlist_content for orphans
SELECT
    'playlist_content' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) as orphaned_records,
    CASE
        WHEN COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) = 0
        THEN 'PASS: No orphaned records'
        ELSE 'FAIL: Orphaned records found!'
    END as test_result
FROM playlist_content;

-- Check schedules for orphans
SELECT
    'schedules' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) as orphaned_records,
    CASE
        WHEN COUNT(*) FILTER (WHERE content_id NOT IN (SELECT id FROM contents)) = 0
        THEN 'PASS: No orphaned records'
        ELSE 'FAIL: Orphaned records found!'
    END as test_result
FROM schedules;

\echo ''

-- ============================================================================
-- TEST 14: Verify constraint names are correct
-- ============================================================================
\echo '--- TEST 14: Constraint name verification ---'
SELECT
    conname as constraint_name,
    CASE
        WHEN conname IN (
            'content_assignments_content_id_fkey',
            'playlist_content_content_id_fkey',
            'schedules_content_id_fkey',
            'content_fallback_content_id_fkey'
        ) THEN 'PASS'
        ELSE 'WARNING: Unexpected constraint name'
    END as test_result
FROM pg_constraint
WHERE confrelid = 'contents'::regclass
ORDER BY conname;

\echo ''

-- ============================================================================
-- COMPREHENSIVE SUMMARY REPORT
-- ============================================================================
\echo '============================================================================'
\echo 'POST-MIGRATION SUMMARY REPORT'
\echo '============================================================================'

-- Create summary table
CREATE TEMP TABLE post_migration_summary AS
SELECT
    'Table Renamed' as check_item,
    CASE
        WHEN EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'contents')
        THEN 'PASS'
        ELSE 'FAIL'
    END as status
UNION ALL
SELECT
    'Old Table Removed',
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'content')
        THEN 'PASS'
        ELSE 'FAIL'
    END
UNION ALL
SELECT
    'Foreign Keys Count',
    CASE
        WHEN (SELECT COUNT(*) FROM pg_constraint WHERE confrelid = 'contents'::regclass) = 4
        THEN 'PASS (4/4)'
        ELSE 'FAIL (' || (SELECT COUNT(*) FROM pg_constraint WHERE confrelid = 'contents'::regclass) || '/4)'
    END
UNION ALL
SELECT
    'Indexes Preserved',
    CASE
        WHEN (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'contents') > 0
        THEN 'PASS'
        ELSE 'WARNING'
    END
UNION ALL
SELECT
    'Self-Referential FK',
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'contents'::regclass
              AND confrelid = 'contents'::regclass
        ) THEN 'PASS'
        ELSE 'FAIL'
    END
UNION ALL
SELECT
    'No Orphaned Records',
    CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM content_assignments
            WHERE content_id NOT IN (SELECT id FROM contents)
        ) AND NOT EXISTS (
            SELECT 1 FROM playlist_content
            WHERE content_id NOT IN (SELECT id FROM contents)
        ) AND NOT EXISTS (
            SELECT 1 FROM schedules
            WHERE content_id NOT IN (SELECT id FROM contents)
        ) THEN 'PASS'
        ELSE 'FAIL'
    END;

-- Display summary
SELECT * FROM post_migration_summary;

\echo ''
\echo 'Data Integrity Summary:'
SELECT
    COUNT(*) as total_contents,
    COUNT(*) FILTER (WHERE is_active = true) as active_contents,
    COALESCE(SUM(file_size), 0) as total_file_size_bytes
FROM contents;

\echo ''
\echo '============================================================================'
\echo 'POST-MIGRATION VERIFICATION COMPLETE'
\echo ''
\echo 'Next Steps:'
\echo '  1. Compare record counts with pre-migration output'
\echo '  2. If all tests PASS, proceed to API endpoint testing'
\echo '  3. If any tests FAIL, review migration and consider rollback'
\echo '============================================================================'
