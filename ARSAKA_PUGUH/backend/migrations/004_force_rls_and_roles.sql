-- Migration: 004
-- Description: FORCE Row-Level Security and Role Hardening
-- Date: 2026-01-24
-- Phase: 2
-- Source: Phase 2 Requirements - Database Hardening

-- =============================================================================
-- PHASE 2: FORCE ROW LEVEL SECURITY + ROLE SEPARATION
-- =============================================================================
--
-- PRINCIPLE: Defense in depth - even if application is compromised,
-- database-level enforcement prevents bypass.
--
-- ROLES:
--   1. app_runtime_role - Application runtime (NO BYPASS capabilities)
--   2. migration_role   - Schema migrations only (limited use)
--   3. postgres         - Superuser (admin only, never used by app)
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: CREATE ROLES WITH STRICT PERMISSIONS
-- =============================================================================

-- Drop existing role if exists (clean state)
DO $$
BEGIN
    -- Revoke all existing grants first
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_runtime_role';
        EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_runtime_role';
        EXECUTE 'REVOKE ALL ON SCHEMA public FROM app_runtime_role';
    END IF;

    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'migration_role') THEN
        EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM migration_role';
        EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM migration_role';
        EXECUTE 'REVOKE ALL ON SCHEMA public FROM migration_role';
    END IF;
END
$$;

-- Drop roles if exist
DROP ROLE IF EXISTS app_runtime_role;
DROP ROLE IF EXISTS migration_role;

-- -----------------------------------------------------------------------------
-- app_runtime_role: Application Runtime
-- -----------------------------------------------------------------------------
-- CRITICAL: This role is used by the application at runtime.
-- It CANNOT:
--   - Be superuser
--   - Create databases
--   - Create roles
--   - Bypass RLS
--   - Inherit other role privileges
-- -----------------------------------------------------------------------------

CREATE ROLE app_runtime_role
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOBYPASSRLS        -- CRITICAL: Cannot bypass Row-Level Security
    NOINHERIT          -- Cannot inherit privileges from other roles
    LOGIN
    PASSWORD 'CHANGE_IN_PRODUCTION';  -- MUST be changed in production

COMMENT ON ROLE app_runtime_role IS
    'Application runtime role - NO BYPASS capabilities. Used by Core service.';

-- -----------------------------------------------------------------------------
-- migration_role: Schema Migrations Only
-- -----------------------------------------------------------------------------
-- Used ONLY for running migrations. Never used by application at runtime.
-- Has more privileges but is tightly controlled.
-- -----------------------------------------------------------------------------

CREATE ROLE migration_role
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOBYPASSRLS        -- Still cannot bypass RLS
    NOINHERIT
    LOGIN
    PASSWORD 'MIGRATION_ONLY_CHANGE_IN_PRODUCTION';

COMMENT ON ROLE migration_role IS
    'Migration role - Used only for schema changes, never at runtime.';

-- =============================================================================
-- STEP 2: GRANT SCHEMA ACCESS
-- =============================================================================

-- app_runtime_role: Schema usage only
GRANT USAGE ON SCHEMA public TO app_runtime_role;

-- migration_role: Schema usage + create (for migrations)
GRANT USAGE, CREATE ON SCHEMA public TO migration_role;

-- =============================================================================
-- STEP 3: GRANT TABLE PERMISSIONS (MINIMAL REQUIRED)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- app_runtime_role: Table Permissions
-- -----------------------------------------------------------------------------
-- PRINCIPLE: Minimum necessary permissions only

-- IMMUTABLE TABLES: SELECT + INSERT only (no UPDATE, no DELETE)
GRANT SELECT, INSERT ON decisions TO app_runtime_role;
GRANT SELECT, INSERT ON event_log TO app_runtime_role;
GRANT SELECT, INSERT ON workflow_transitions TO app_runtime_role;
GRANT SELECT, INSERT ON operations_audit TO app_runtime_role;
GRANT SELECT, INSERT ON idempotency_cache TO app_runtime_role;

-- MUTABLE TABLES: SELECT + INSERT + UPDATE (no DELETE)
GRANT SELECT, INSERT, UPDATE ON workflows TO app_runtime_role;
GRANT SELECT, INSERT, UPDATE ON rules TO app_runtime_role;

-- SCHEMA MIGRATIONS: SELECT only (app doesn't modify)
GRANT SELECT ON schema_migrations TO app_runtime_role;

-- Explicitly REVOKE dangerous permissions
REVOKE DELETE ON decisions FROM app_runtime_role;
REVOKE DELETE ON event_log FROM app_runtime_role;
REVOKE DELETE ON workflow_transitions FROM app_runtime_role;
REVOKE DELETE ON operations_audit FROM app_runtime_role;
REVOKE DELETE ON idempotency_cache FROM app_runtime_role;
REVOKE DELETE ON workflows FROM app_runtime_role;
REVOKE DELETE ON rules FROM app_runtime_role;

-- REVOKE UPDATE on immutable tables (double protection)
REVOKE UPDATE ON decisions FROM app_runtime_role;
REVOKE UPDATE ON event_log FROM app_runtime_role;
REVOKE UPDATE ON workflow_transitions FROM app_runtime_role;
REVOKE UPDATE ON operations_audit FROM app_runtime_role;
REVOKE UPDATE ON idempotency_cache FROM app_runtime_role;

-- -----------------------------------------------------------------------------
-- migration_role: Table Permissions
-- -----------------------------------------------------------------------------
-- Full DDL permissions for schema changes

GRANT ALL ON ALL TABLES IN SCHEMA public TO migration_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO migration_role;

-- =============================================================================
-- STEP 4: GRANT SEQUENCE PERMISSIONS
-- =============================================================================

-- app_runtime_role needs sequence usage for UUID generation (if using serial)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_runtime_role;

-- =============================================================================
-- STEP 5: FORCE ROW-LEVEL SECURITY ON ALL TENANT-BOUND TABLES
-- =============================================================================
-- CRITICAL: FORCE RLS means even table owners must obey RLS policies.
-- This prevents bypass via SET ROLE or privilege escalation.
-- =============================================================================

-- Ensure RLS is enabled (may already be from migration 003)
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE operations_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_cache ENABLE ROW LEVEL SECURITY;

-- FORCE RLS - even table owners must obey policies
ALTER TABLE decisions FORCE ROW LEVEL SECURITY;
ALTER TABLE workflows FORCE ROW LEVEL SECURITY;
ALTER TABLE workflow_transitions FORCE ROW LEVEL SECURITY;
ALTER TABLE rules FORCE ROW LEVEL SECURITY;
ALTER TABLE event_log FORCE ROW LEVEL SECURITY;
ALTER TABLE operations_audit FORCE ROW LEVEL SECURITY;
ALTER TABLE idempotency_cache FORCE ROW LEVEL SECURITY;

-- =============================================================================
-- STEP 6: CREATE RLS POLICIES FOR app_runtime_role
-- =============================================================================
-- Note: Policies from migration 003 were for infra_core_app role.
-- We need policies for app_runtime_role.
-- =============================================================================

-- Drop existing policies if they target old role
DROP POLICY IF EXISTS decisions_tenant_isolation ON decisions;
DROP POLICY IF EXISTS workflows_tenant_isolation ON workflows;
DROP POLICY IF EXISTS workflow_transitions_tenant_isolation ON workflow_transitions;
DROP POLICY IF EXISTS rules_tenant_isolation ON rules;
DROP POLICY IF EXISTS event_log_tenant_isolation ON event_log;
DROP POLICY IF EXISTS operations_audit_tenant_isolation ON operations_audit;
DROP POLICY IF EXISTS idempotency_cache_tenant_isolation ON idempotency_cache;

-- Create new policies for app_runtime_role

CREATE POLICY decisions_runtime_isolation ON decisions
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY workflows_runtime_isolation ON workflows
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY workflow_transitions_runtime_isolation ON workflow_transitions
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rules_runtime_isolation ON rules
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY event_log_runtime_isolation ON event_log
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY operations_audit_runtime_isolation ON operations_audit
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY idempotency_cache_runtime_isolation ON idempotency_cache
    FOR ALL
    TO app_runtime_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- =============================================================================
-- STEP 7: VERIFICATION FUNCTIONS
-- =============================================================================

-- Function to verify role cannot bypass RLS
CREATE OR REPLACE FUNCTION verify_role_cannot_bypass_rls(role_name text)
RETURNS boolean AS $$
DECLARE
    can_bypass boolean;
BEGIN
    SELECT rolbypassrls INTO can_bypass
    FROM pg_roles
    WHERE rolname = role_name;

    RETURN NOT COALESCE(can_bypass, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify RLS is FORCED on table
CREATE OR REPLACE FUNCTION verify_rls_forced(table_name text)
RETURNS boolean AS $$
DECLARE
    is_forced boolean;
BEGIN
    SELECT relforcerowsecurity INTO is_forced
    FROM pg_class
    WHERE relname = table_name;

    RETURN COALESCE(is_forced, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION verify_role_cannot_bypass_rls IS
    'Returns TRUE if the role cannot bypass RLS (safe)';

COMMENT ON FUNCTION verify_rls_forced IS
    'Returns TRUE if the table has FORCE ROW LEVEL SECURITY enabled';

-- =============================================================================
-- STEP 8: RECORD MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (4, '004_force_rls_and_roles');

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES (Run manually after migration)
-- =============================================================================

-- Verify app_runtime_role cannot bypass RLS:
-- SELECT verify_role_cannot_bypass_rls('app_runtime_role');  -- Should return TRUE

-- Verify all tables have FORCE RLS:
-- SELECT verify_rls_forced('decisions');
-- SELECT verify_rls_forced('workflows');
-- SELECT verify_rls_forced('event_log');
-- ... (repeat for all tables)

-- Verify role privileges:
-- SELECT grantee, table_name, privilege_type
-- FROM information_schema.role_table_grants
-- WHERE grantee = 'app_runtime_role'
-- ORDER BY table_name, privilege_type;

-- Test bypass attempt (should fail):
-- SET ROLE app_runtime_role;
-- SET app.current_tenant_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
-- INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome, created_at)
-- VALUES (gen_random_uuid(), 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'test', '{}', 'DENIED', NOW());
-- -- Should fail: tenant_id doesn't match app.current_tenant_id

-- =============================================================================
-- END OF MIGRATION 004
-- =============================================================================
