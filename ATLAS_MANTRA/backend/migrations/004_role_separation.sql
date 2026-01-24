-- Migration: 004
-- Description: Create role separation - owner vs app role
-- Date: 2025-01-24
-- Authority: Implementation Conformance Audit - DB Privilege Fix
--
-- SECURITY MODEL:
--   mantra_owner: Schema management only. Never used at runtime.
--   mantra_app: SELECT + INSERT only. Used by application.
--
-- PROHIBITED for mantra_app:
--   - UPDATE
--   - DELETE
--   - ALTER
--   - TRIGGER
--   - TRUNCATE
--   - REFERENCES
--   - ANY admin operation

BEGIN;

-- ============================================================================
-- STEP 1: Create application role (if not exists)
-- ============================================================================

-- NOTE: Password must be set via ALTER ROLE after migration
-- or via environment variable in production deployment.
-- Never commit real passwords to migration files.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mantra_app') THEN
        -- Create with a placeholder - MUST be changed in production
        CREATE ROLE mantra_app WITH LOGIN PASSWORD 'TEMPORARY_CHANGE_IMMEDIATELY';
        RAISE NOTICE 'SECURITY: mantra_app role created. Change password immediately!';
    END IF;
END
$$;

-- Ensure role has no superuser privileges
ALTER ROLE mantra_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

-- ============================================================================
-- STEP 2: Revoke ALL default privileges first (clean slate)
-- ============================================================================

-- Revoke everything from public
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Revoke everything from mantra_app (clean slate)
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM mantra_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM mantra_app;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM mantra_app;
REVOKE ALL ON SCHEMA public FROM mantra_app;

-- ============================================================================
-- STEP 3: Grant MINIMAL privileges to mantra_app
-- ============================================================================

-- Schema access (required for any operation)
GRANT USAGE ON SCHEMA public TO mantra_app;

-- DECISIONS table: SELECT + INSERT only
-- NO UPDATE. NO DELETE. NO TRUNCATE. NO REFERENCES.
GRANT SELECT, INSERT ON TABLE decisions TO mantra_app;

-- DECISION_EVENTS table: SELECT + INSERT only (audit log)
GRANT SELECT, INSERT ON TABLE decision_events TO mantra_app;

-- VALIDATION_RESULTS table: SELECT + INSERT only
GRANT SELECT, INSERT ON TABLE validation_results TO mantra_app;

-- Sequences: USAGE only (for INSERT with generated IDs)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mantra_app;

-- ============================================================================
-- STEP 4: Explicitly DENY dangerous operations
-- (These should already be denied, but explicit is safer)
-- ============================================================================

-- Revoke trigger privilege (cannot disable triggers)
REVOKE TRIGGER ON ALL TABLES IN SCHEMA public FROM mantra_app;

-- Revoke truncate privilege
REVOKE TRUNCATE ON ALL TABLES IN SCHEMA public FROM mantra_app;

-- Revoke references privilege
REVOKE REFERENCES ON ALL TABLES IN SCHEMA public FROM mantra_app;

-- ============================================================================
-- STEP 5: Set default privileges for future tables
-- ============================================================================

-- Future tables created by owner: app gets SELECT + INSERT only
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT ON TABLES TO mantra_app;

-- Future sequences: app gets USAGE only
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO mantra_app;

-- ============================================================================
-- STEP 6: Document the security model
-- ============================================================================

COMMENT ON ROLE mantra_app IS
    'RESTRICTED APPLICATION ROLE. '
    'SELECT + INSERT only. '
    'NO UPDATE. NO DELETE. NO ALTER. NO TRIGGER. '
    'Per Implementation Conformance Audit.';

-- ============================================================================
-- VERIFICATION QUERIES (run manually to confirm)
-- ============================================================================

-- To verify privileges after migration:
--
-- SELECT grantee, table_name, privilege_type
-- FROM information_schema.table_privileges
-- WHERE grantee = 'mantra_app'
-- ORDER BY table_name, privilege_type;
--
-- Expected output:
--   mantra_app | decisions          | INSERT
--   mantra_app | decisions          | SELECT
--   mantra_app | decision_events    | INSERT
--   mantra_app | decision_events    | SELECT
--   mantra_app | validation_results | INSERT
--   mantra_app | validation_results | SELECT
--
-- If UPDATE or DELETE appears: MIGRATION FAILED

COMMIT;
