-- ============================================================================
-- ATLAS_MANTRA: DB Conformance Re-Audit Script
-- ============================================================================
-- Authority: Implementation Conformance Audit
-- Date: 2025-01-24
--
-- This script MUST be run as mantra_owner to execute all tests.
-- It verifies constitutional enforcement at database level.
-- ============================================================================

\echo '=============================================='
\echo 'ATLAS_MANTRA DB CONFORMANCE RE-AUDIT'
\echo '=============================================='
\echo ''

-- ============================================================================
-- TEST 1: Role Matrix Verification
-- ============================================================================
\echo '[TEST 1] ROLE MATRIX - mantra_app privileges'
\echo '----------------------------------------------'

SELECT
    grantee,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'mantra_app'
  AND table_schema = 'public'
ORDER BY table_name, privilege_type;

\echo ''
\echo 'EXPECTED: Only SELECT and INSERT for each table.'
\echo 'FAIL IF: UPDATE, DELETE, TRUNCATE, TRIGGER appears.'
\echo ''

-- ============================================================================
-- TEST 2: Role Attributes Verification
-- ============================================================================
\echo '[TEST 2] ROLE ATTRIBUTES - mantra_app must have NO admin privileges'
\echo '--------------------------------------------------------------------'

SELECT
    rolname,
    rolsuper AS is_superuser,
    rolcreatedb AS can_createdb,
    rolcreaterole AS can_createrole,
    rolreplication AS can_replicate
FROM pg_roles
WHERE rolname = 'mantra_app';

\echo ''
\echo 'EXPECTED: All FALSE'
\echo ''

-- ============================================================================
-- TEST 3: Trigger Existence Verification
-- ============================================================================
\echo '[TEST 3] TRIGGER EXISTENCE - Constitutional enforcement triggers'
\echo '-----------------------------------------------------------------'

SELECT
    trigger_name,
    event_manipulation,
    action_timing
FROM information_schema.triggers
WHERE event_object_table = 'decisions'
ORDER BY trigger_name;

\echo ''
\echo 'EXPECTED: trigger_reject_all_updates (UPDATE), trigger_reject_all_deletes (DELETE)'
\echo ''

-- ============================================================================
-- TEST 4: Trigger Function Review
-- ============================================================================
\echo '[TEST 4] TRIGGER FUNCTIONS - Must have NO conditional logic'
\echo '------------------------------------------------------------'

SELECT
    proname AS function_name,
    prosrc AS function_body
FROM pg_proc
WHERE proname IN ('reject_all_updates', 'reject_all_deletes');

\echo ''
\echo 'EXPECTED: RAISE EXCEPTION without any IF conditions'
\echo ''

-- ============================================================================
-- TEST 5: Table Structure - No Status Column
-- ============================================================================
\echo '[TEST 5] TABLE STRUCTURE - status column must NOT exist'
\echo '--------------------------------------------------------'

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'decisions'
  AND column_name IN ('status', 'is_immutable')
ORDER BY column_name;

\echo ''
\echo 'EXPECTED: Zero rows (no status or is_immutable column)'
\echo ''

-- ============================================================================
-- TEST 6: Status Enum Type - Must Not Exist
-- ============================================================================
\echo '[TEST 6] ENUM TYPE - decision_status must NOT exist'
\echo '----------------------------------------------------'

SELECT typname
FROM pg_type
WHERE typname = 'decision_status';

\echo ''
\echo 'EXPECTED: Zero rows'
\echo ''

\echo '=============================================='
\echo 'CONFORMANCE TESTS COMPLETE'
\echo '=============================================='
\echo ''
\echo 'To run behavioral tests (UPDATE/DELETE/DISABLE TRIGGER fail),'
\echo 'use: verify_db_conformance_behavioral.sql'
