-- ============================================================================
-- ATLAS_MANTRA: DB Conformance Behavioral Tests
-- ============================================================================
-- Authority: Implementation Conformance Audit
-- Date: 2025-01-24
--
-- IMPORTANT: This script MUST be run as mantra_app to verify restrictions!
-- Run with: psql -U mantra_app -d atlas_mantra -f verify_db_conformance_behavioral.sql
--
-- All tests should FAIL (raise errors). Success = the app cannot violate constitution.
-- ============================================================================

\echo '=============================================='
\echo 'ATLAS_MANTRA BEHAVIORAL CONFORMANCE TESTS'
\echo '=============================================='
\echo ''
\echo 'NOTE: Each test should produce an ERROR.'
\echo 'If a test succeeds without error, CONFORMANCE FAILED.'
\echo ''

-- ============================================================================
-- SETUP: Insert a test decision (should succeed)
-- ============================================================================
\echo '[SETUP] Inserting test decision (should SUCCEED)'
\echo '-------------------------------------------------'

INSERT INTO decisions (
    title,
    description,
    category,
    created_by
) VALUES (
    'Test Decision for Conformance Audit',
    'This decision tests constitutional enforcement',
    'AUDIT_TEST',
    'conformance_auditor'
) RETURNING decision_id, title;

\echo ''
\echo 'SUCCESS: INSERT worked. This is expected.'
\echo ''

-- Store the decision_id for subsequent tests
\set test_decision_id '(SELECT decision_id FROM decisions WHERE category = ''AUDIT_TEST'' LIMIT 1)'

-- ============================================================================
-- TEST 1: UPDATE MUST FAIL (Trigger Enforcement)
-- ============================================================================
\echo '[TEST 1] UPDATE MUST FAIL - Trigger enforcement'
\echo '------------------------------------------------'
\echo 'Attempting: UPDATE decisions SET title = ''Modified'''
\echo ''

-- This should raise: CONSTITUTIONAL VIOLATION: Decision records are ABSOLUTELY IMMUTABLE
UPDATE decisions
SET title = 'Modified Title - THIS SHOULD FAIL'
WHERE category = 'AUDIT_TEST';

\echo ''
\echo 'ERROR: If you see this, UPDATE should have failed above!'
\echo ''

-- ============================================================================
-- TEST 2: DELETE MUST FAIL (Trigger Enforcement)
-- ============================================================================
\echo '[TEST 2] DELETE MUST FAIL - Trigger enforcement'
\echo '------------------------------------------------'
\echo 'Attempting: DELETE FROM decisions WHERE category = AUDIT_TEST'
\echo ''

-- This should raise: CONSTITUTIONAL VIOLATION: Decision records are ABSOLUTELY IMMUTABLE
DELETE FROM decisions
WHERE category = 'AUDIT_TEST';

\echo ''
\echo 'ERROR: If you see this, DELETE should have failed above!'
\echo ''

-- ============================================================================
-- TEST 3: DISABLE TRIGGER MUST FAIL (Privilege Restriction)
-- ============================================================================
\echo '[TEST 3] DISABLE TRIGGER MUST FAIL - Privilege restriction'
\echo '-----------------------------------------------------------'
\echo 'Attempting: ALTER TABLE decisions DISABLE TRIGGER trigger_reject_all_updates'
\echo ''

-- This should raise: permission denied or must be owner
ALTER TABLE decisions DISABLE TRIGGER trigger_reject_all_updates;

\echo ''
\echo 'ERROR: If you see this, DISABLE TRIGGER should have failed above!'
\echo ''

-- ============================================================================
-- TEST 4: TRUNCATE MUST FAIL (Privilege Restriction)
-- ============================================================================
\echo '[TEST 4] TRUNCATE MUST FAIL - Privilege restriction'
\echo '----------------------------------------------------'
\echo 'Attempting: TRUNCATE decisions'
\echo ''

-- This should raise: permission denied
TRUNCATE decisions;

\echo ''
\echo 'ERROR: If you see this, TRUNCATE should have failed above!'
\echo ''

-- ============================================================================
-- TEST 5: DROP TABLE MUST FAIL (Privilege Restriction)
-- ============================================================================
\echo '[TEST 5] DROP TABLE MUST FAIL - Privilege restriction'
\echo '------------------------------------------------------'
\echo 'Attempting: DROP TABLE decisions'
\echo ''

-- This should raise: permission denied or must be owner
DROP TABLE decisions;

\echo ''
\echo 'ERROR: If you see this, DROP TABLE should have failed above!'
\echo ''

-- ============================================================================
-- TEST 6: CREATE TABLE MUST FAIL (Privilege Restriction)
-- ============================================================================
\echo '[TEST 6] CREATE TABLE MUST FAIL - Privilege restriction'
\echo '--------------------------------------------------------'
\echo 'Attempting: CREATE TABLE test_illegal (id INT)'
\echo ''

-- This should raise: permission denied
CREATE TABLE test_illegal (id INT);

\echo ''
\echo 'ERROR: If you see this, CREATE TABLE should have failed above!'
\echo ''

\echo '=============================================='
\echo 'BEHAVIORAL TESTS COMPLETE'
\echo '=============================================='
\echo ''
\echo 'CONFORMANCE SUMMARY:'
\echo '  - If all 6 tests raised errors: PASS'
\echo '  - If any test succeeded: FAIL - CONSTITUTIONAL VIOLATION'
\echo ''
\echo 'The test decision with category=AUDIT_TEST remains in DB.'
\echo 'It cannot be deleted (by design). Use new version + supersedes.'
