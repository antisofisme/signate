-- Migration: 003
-- Description: Row-Level Security (RLS) policies for tenant isolation
-- Date: 2026-01-07
-- Phase: 1
-- Layer: 3 (Implementation)
-- Source: INFRA-LAY3-004 Section 2.2 (RLS Policy Setup)

-- =============================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
-- Purpose: Enforce tenant isolation at database level
-- Enforcement: All queries automatically filtered by tenant_id
-- Guarantee: Cross-tenant queries return 0 rows (hard boundary)
-- =============================================================================

BEGIN;

-- =============================================================================
-- DATABASE ROLES
-- =============================================================================

-- Create application role for Core service
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'infra_core_app') THEN
    CREATE ROLE infra_core_app;
  END IF;
END
$$;

-- Grant permissions to application role
GRANT CONNECT ON DATABASE postgres TO infra_core_app;  -- Update database name as needed
GRANT USAGE ON SCHEMA public TO infra_core_app;

-- Grant table permissions (SELECT, INSERT only - no UPDATE/DELETE per immutability)
GRANT SELECT, INSERT ON decisions TO infra_core_app;
GRANT SELECT, INSERT ON workflows TO infra_core_app;
GRANT SELECT, INSERT ON workflow_transitions TO infra_core_app;
GRANT SELECT, INSERT ON rules TO infra_core_app;
GRANT SELECT, INSERT ON event_log TO infra_core_app;
GRANT SELECT, INSERT ON operations_audit TO infra_core_app;
GRANT SELECT, INSERT ON idempotency_cache TO infra_core_app;
GRANT SELECT, INSERT ON schema_migrations TO infra_core_core_app;

-- Special: Allow UPDATE on workflows (mutable until terminal state)
GRANT UPDATE ON workflows TO infra_core_app;

-- Special: Allow UPDATE on rules (for activation/deactivation)
GRANT UPDATE ON rules TO infra_core_app;

-- REVOKE UPDATE/DELETE explicitly on immutable tables
REVOKE UPDATE, DELETE ON decisions FROM infra_core_app;
REVOKE UPDATE, DELETE ON event_log FROM infra_core_app;
REVOKE UPDATE, DELETE ON workflow_transitions FROM infra_core_app;
REVOKE UPDATE, DELETE ON operations_audit FROM infra_core_app;
REVOKE UPDATE, DELETE ON idempotency_cache FROM infra_core_app;

-- Grant sequence permissions for UUID generation
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO infra_core_app;

-- Comments
COMMENT ON ROLE infra_core_app IS
  'Application role for ATLAS_PUGUH Core service - limited to SELECT and INSERT on immutable tables';

-- =============================================================================
-- ENABLE ROW-LEVEL SECURITY
-- =============================================================================

ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE operations_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_cache ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- RLS POLICY: decisions
-- =============================================================================

CREATE POLICY decisions_tenant_isolation ON decisions
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY decisions_tenant_isolation ON decisions IS
  'Enforces tenant isolation: users can only access decisions for their tenant_id';

-- =============================================================================
-- RLS POLICY: workflows
-- =============================================================================

CREATE POLICY workflows_tenant_isolation ON workflows
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY workflows_tenant_isolation ON workflows IS
  'Enforces tenant isolation: users can only access workflows for their tenant_id';

-- =============================================================================
-- RLS POLICY: workflow_transitions
-- =============================================================================

CREATE POLICY workflow_transitions_tenant_isolation ON workflow_transitions
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY workflow_transitions_tenant_isolation ON workflow_transitions IS
  'Enforces tenant isolation: users can only access workflow transitions for their tenant_id';

-- =============================================================================
-- RLS POLICY: rules
-- =============================================================================

CREATE POLICY rules_tenant_isolation ON rules
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY rules_tenant_isolation ON rules IS
  'Enforces tenant isolation: users can only access rules for their tenant_id';

-- =============================================================================
-- RLS POLICY: event_log
-- =============================================================================

CREATE POLICY event_log_tenant_isolation ON event_log
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY event_log_tenant_isolation ON event_log IS
  'Enforces tenant isolation: users can only access events for their tenant_id';

-- =============================================================================
-- RLS POLICY: operations_audit
-- =============================================================================

CREATE POLICY operations_audit_tenant_isolation ON operations_audit
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY operations_audit_tenant_isolation ON operations_audit IS
  'Enforces tenant isolation: users can only access audit records for their tenant_id';

-- =============================================================================
-- RLS POLICY: idempotency_cache
-- =============================================================================

CREATE POLICY idempotency_cache_tenant_isolation ON idempotency_cache
  FOR ALL
  TO infra_core_app
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

COMMENT ON POLICY idempotency_cache_tenant_isolation ON idempotency_cache IS
  'Enforces tenant isolation: users can only access idempotency cache for their tenant_id';

-- =============================================================================
-- SUPERUSER BYPASS (For administrative access)
-- =============================================================================
-- Note: Superusers bypass RLS by default
-- To force RLS even for superusers, use: ALTER TABLE table_name FORCE ROW LEVEL SECURITY;
-- Phase 1: Not forcing RLS for superusers (administrative flexibility)
-- Phase 2+: Consider FORCE ROW LEVEL SECURITY for production

-- Example (commented out for Phase 1):
-- ALTER TABLE decisions FORCE ROW LEVEL SECURITY;
-- ALTER TABLE workflows FORCE ROW LEVEL SECURITY;
-- ... (repeat for all tables)

-- =============================================================================
-- USAGE INSTRUCTIONS
-- =============================================================================
-- Before executing queries, application MUST set tenant context:
--
-- SET app.current_tenant_id = '<tenant_uuid>';
--
-- Example:
-- SET app.current_tenant_id = '123e4567-e89b-12d3-a456-426614174000';
-- SELECT * FROM decisions;
-- -- Returns only decisions for tenant '123e4567-e89b-12d3-a456-426614174000'
--
-- Without setting tenant context:
-- SELECT * FROM decisions;
-- -- Returns 0 rows (RLS filters all results)
--
-- To verify current tenant context:
-- SELECT current_setting('app.current_tenant_id', true);
-- =============================================================================

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- List all RLS policies
-- SELECT
--   schemaname,
--   tablename,
--   policyname,
--   permissive,
--   roles,
--   cmd,
--   qual,
--   with_check
-- FROM pg_policies
-- WHERE tablename IN (
--   'decisions', 'workflows', 'workflow_transitions',
--   'rules', 'event_log', 'operations_audit', 'idempotency_cache'
-- )
-- ORDER BY tablename, policyname;

-- Verify RLS is enabled on all tables
-- SELECT
--   schemaname,
--   tablename,
--   rowsecurity
-- FROM pg_tables
-- WHERE tablename IN (
--   'decisions', 'workflows', 'workflow_transitions',
--   'rules', 'event_log', 'operations_audit', 'idempotency_cache'
-- )
-- ORDER BY tablename;

-- =============================================================================
-- RECORD MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (3, '003_rls_policies');

COMMIT;

-- =============================================================================
-- END OF MIGRATION 003
-- =============================================================================
