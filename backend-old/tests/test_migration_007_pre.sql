-- ============================================================================
-- Pre-Migration Test Script for Migration 007
-- Rename content table to contents
-- ============================================================================
-- Purpose: Capture current state before migration for comparison
-- Run this BEFORE executing migration 007
-- ============================================================================

\echo '============================================================================'
\echo 'PRE-MIGRATION VERIFICATION FOR MIGRATION 007'
\echo 'Testing Date:' `date`
\echo '============================================================================'
\echo ''

-- ============================================================================
-- TEST 1: Verify current table name is 'content' (not 'contents')
-- ============================================================================
\echo '--- TEST 1: Verify table name is "content" ---'
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'content'
        ) THEN 'PASS: Table "content" exists'
        ELSE 'FAIL: Table "content" does not exist!'
    END as test_result;

SELECT
    CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'contents'
        ) THEN 'PASS: Table "contents" does not exist yet (expected)'
        ELSE 'FAIL: Table "contents" already exists! Migration may have already run.'
    END as test_result;

\echo ''

-- ============================================================================
-- TEST 2: Count records in content table (baseline)
-- ============================================================================
\echo '--- TEST 2: Count records in content table ---'
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active_records,
    COUNT(*) FILTER (WHERE is_active = false) as inactive_records,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as soft_deleted_records,
    COUNT(*) FILTER (WHERE fallback_content_id IS NOT NULL) as records_with_fallback
FROM content;

\echo ''
\echo 'Storing record count for post-migration comparison...'
CREATE TEMP TABLE pre_migration_counts AS
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active_records,
    COUNT(*) FILTER (WHERE is_active = false) as inactive_records,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as soft_deleted_records,
    COUNT(*) FILTER (WHERE fallback_content_id IS NOT NULL) as records_with_fallback,
    COALESCE(SUM(file_size), 0) as total_file_size
FROM content;

SELECT 'Baseline counts stored in temp table' as status;
\echo ''

-- ============================================================================
-- TEST 3: List all foreign key constraints referencing content table
-- ============================================================================
\echo '--- TEST 3: Foreign key constraints referencing "content" ---'
SELECT
    conname as constraint_name,
    conrelid::regclass as source_table,
    confrelid::regclass as referenced_table,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE confrelid = 'content'::regclass
ORDER BY conrelid::regclass::text, conname;

\echo ''
\echo 'Expected foreign keys:'
\echo '  1. content_assignments_content_id_fkey (content_assignments -> content)'
\echo '  2. playlist_content_content_id_fkey (playlist_content -> content)'
\echo '  3. schedules_content_id_fkey (schedules -> content)'
\echo '  4. content_fallback_content_id_fkey (content -> content) [SELF-REFERENTIAL]'
\echo ''

-- Store FK count for verification
CREATE TEMP TABLE pre_migration_fk_count AS
SELECT COUNT(*) as fk_count
FROM pg_constraint
WHERE confrelid = 'content'::regclass;

SELECT
    fk_count,
    CASE
        WHEN fk_count = 4 THEN 'PASS: All 4 foreign keys exist'
        ELSE 'WARNING: Expected 4 foreign keys, found ' || fk_count
    END as test_result
FROM pre_migration_fk_count;

\echo ''

-- ============================================================================
-- TEST 4: Verify self-referential foreign key exists
-- ============================================================================
\echo '--- TEST 4: Verify self-referential FK (fallback_content_id) ---'
SELECT
    conname as constraint_name,
    conrelid::regclass as source_table,
    confrelid::regclass as referenced_table,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE conrelid = 'content'::regclass
  AND confrelid = 'content'::regclass
  AND conname LIKE '%fallback%';

SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'content'::regclass
              AND confrelid = 'content'::regclass
              AND conname = 'content_fallback_content_id_fkey'
        ) THEN 'PASS: Self-referential FK exists'
        ELSE 'FAIL: Self-referential FK not found!'
    END as test_result;

\echo ''

-- ============================================================================
-- TEST 5: List all indexes on content table
-- ============================================================================
\echo '--- TEST 5: Indexes on content table ---'
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'content'
ORDER BY indexname;

\echo ''

-- Store index count
CREATE TEMP TABLE pre_migration_index_count AS
SELECT COUNT(*) as index_count
FROM pg_indexes
WHERE tablename = 'content';

SELECT
    index_count,
    'Indexes counted for post-migration comparison' as status
FROM pre_migration_index_count;

\echo ''

-- ============================================================================
-- TEST 6: Sample content data (first 5 records)
-- ============================================================================
\echo '--- TEST 6: Sample content records ---'
SELECT
    id,
    content_type,
    file_name,
    file_size,
    is_active,
    fallback_content_id,
    created_at
FROM content
ORDER BY id
LIMIT 5;

\echo ''

-- ============================================================================
-- TEST 7: Check cascade relationships
-- ============================================================================
\echo '--- TEST 7: Related records in dependent tables ---'
SELECT
    'content_assignments' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT content_id) as unique_content_ids
FROM content_assignments
UNION ALL
SELECT
    'playlist_content' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT content_id) as unique_content_ids
FROM playlist_content
UNION ALL
SELECT
    'schedules' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT content_id) as unique_content_ids
FROM schedules;

\echo ''

-- ============================================================================
-- TEST 8: Export current schema definition
-- ============================================================================
\echo '--- TEST 8: Current table schema ---'
\d content

\echo ''

-- ============================================================================
-- TEST 9: Verify column types and constraints
-- ============================================================================
\echo '--- TEST 9: Column definitions ---'
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'content'
ORDER BY ordinal_position;

\echo ''

-- ============================================================================
-- TEST 10: Check for any views or functions using 'content' table
-- ============================================================================
\echo '--- TEST 10: Views and functions referencing content table ---'
SELECT
    'View' as object_type,
    schemaname || '.' || viewname as object_name,
    definition
FROM pg_views
WHERE definition ILIKE '%content%'
  AND schemaname = 'public';

\echo ''

-- ============================================================================
-- SUMMARY REPORT
-- ============================================================================
\echo '============================================================================'
\echo 'PRE-MIGRATION SUMMARY'
\echo '============================================================================'

SELECT
    'Total Records' as metric,
    total_records::text as value
FROM pre_migration_counts
UNION ALL
SELECT
    'Active Records',
    active_records::text
FROM pre_migration_counts
UNION ALL
SELECT
    'Foreign Keys',
    fk_count::text
FROM pre_migration_fk_count
UNION ALL
SELECT
    'Indexes',
    index_count::text
FROM pre_migration_index_count
UNION ALL
SELECT
    'Total File Size (bytes)',
    total_file_size::text
FROM pre_migration_counts;

\echo ''
\echo 'PRE-MIGRATION VERIFICATION COMPLETE'
\echo 'Save this output for comparison with post-migration tests'
\echo '============================================================================'
