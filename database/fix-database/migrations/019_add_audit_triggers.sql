-- ============================================================================
-- Migration 019: Add Automated Audit Triggers
-- Description: Automatic audit logging for all critical table changes
-- Created: 2025-01-09
-- Priority: MEDIUM
-- ============================================================================

BEGIN;

-- ============================================================================
-- USE CASE & BENEFITS
-- ============================================================================
-- Problem: Manual audit logging is error-prone and incomplete
-- Solution: Database triggers automatically log all changes
--
-- Benefits:
-- 1. Complete audit trail: Never miss a change
-- 2. Compliance: Regulatory requirements (GDPR, SOC2, HIPAA)
-- 3. Security: Detect unauthorized changes
-- 4. Debugging: Track down when/who/what changed
-- 5. Analytics: User activity patterns
--
-- What gets logged:
-- - INSERT: New record created
-- - UPDATE: Record modified (with before/after values)
-- - DELETE: Record deleted (soft or hard)
-- ============================================================================

-- ============================================================================
-- 1. ENHANCE AUDIT_LOGS TABLE (if not already complete)
-- ============================================================================

-- Check if audit_logs table exists, if not create it
CREATE TABLE IF NOT EXISTS audit_logs (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- What happened
    action VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    entity_type VARCHAR(50) NOT NULL, -- table name
    entity_id INTEGER NOT NULL, -- record ID

    -- Multi-tenant
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,

    -- Who did it
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100), -- Snapshot (in case user deleted)
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    -- Changes (JSON diff)
    old_values JSONB, -- Before UPDATE/DELETE
    new_values JSONB, -- After INSERT/UPDATE

    -- Context
    request_id VARCHAR(100), -- For tracing across services
    session_id VARCHAR(100),

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- 2. CREATE INDEXES FOR AUDIT_LOGS
-- ============================================================================

-- Query by entity
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id, created_at DESC);

-- Query by organization
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id, created_at DESC);

-- Query by user
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at DESC);

-- Query by action type
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- Time-series queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_date ON audit_logs(created_at DESC);

-- JSONB search on changes
CREATE INDEX IF NOT EXISTS idx_audit_logs_old_values ON audit_logs USING gin(old_values);
CREATE INDEX IF NOT EXISTS idx_audit_logs_new_values ON audit_logs USING gin(new_values);

-- ============================================================================
-- 3. CREATE GENERIC AUDIT TRIGGER FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    v_old_values JSONB;
    v_new_values JSONB;
    v_organization_id INTEGER;
    v_user_id INTEGER;
    v_username VARCHAR(100);
BEGIN
    -- Get current user context (from RLS session variables)
    BEGIN
        v_user_id := current_setting('app.current_user_id', true)::INTEGER;
        v_username := current_setting('app.current_username', true);
        v_organization_id := current_setting('app.current_organization_id', true)::INTEGER;
    EXCEPTION
        WHEN OTHERS THEN
            v_user_id := NULL;
            v_username := 'system';
    END;

    -- Build JSON values based on operation
    CASE TG_OP
        WHEN 'INSERT' THEN
            v_old_values := NULL;
            v_new_values := row_to_json(NEW)::JSONB;

            -- Try to get organization_id from new record
            IF v_organization_id IS NULL THEN
                BEGIN
                    v_organization_id := (NEW::JSONB->>'organization_id')::INTEGER;
                EXCEPTION WHEN OTHERS THEN
                    v_organization_id := NULL;
                END;
            END IF;

        WHEN 'UPDATE' THEN
            v_old_values := row_to_json(OLD)::JSONB;
            v_new_values := row_to_json(NEW)::JSONB;

            -- Try to get organization_id from record
            IF v_organization_id IS NULL THEN
                BEGIN
                    v_organization_id := (NEW::JSONB->>'organization_id')::INTEGER;
                EXCEPTION WHEN OTHERS THEN
                    v_organization_id := NULL;
                END;
            END IF;

        WHEN 'DELETE' THEN
            v_old_values := row_to_json(OLD)::JSONB;
            v_new_values := NULL;

            -- Try to get organization_id from old record
            IF v_organization_id IS NULL THEN
                BEGIN
                    v_organization_id := (OLD::JSONB->>'organization_id')::INTEGER;
                EXCEPTION WHEN OTHERS THEN
                    v_organization_id := NULL;
                END;
            END IF;
    END CASE;

    -- Insert audit log
    INSERT INTO audit_logs (
        action,
        entity_type,
        entity_id,
        organization_id,
        user_id,
        username,
        old_values,
        new_values,
        request_id,
        created_at
    ) VALUES (
        TG_OP,
        TG_TABLE_NAME,
        COALESCE((NEW::JSONB->>'id')::INTEGER, (OLD::JSONB->>'id')::INTEGER),
        v_organization_id,
        v_user_id,
        v_username,
        v_old_values,
        v_new_values,
        current_setting('app.request_id', true),
        NOW()
    );

    -- Return appropriate value
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION audit_trigger_function() IS
    'Generic trigger function for automatic audit logging';

-- ============================================================================
-- 4. ATTACH AUDIT TRIGGERS TO CRITICAL TABLES
-- ============================================================================

-- Helper function to add audit trigger to a table
CREATE OR REPLACE FUNCTION add_audit_trigger(p_table_name TEXT)
RETURNS VOID AS $$
DECLARE
    v_trigger_name TEXT;
BEGIN
    v_trigger_name := 'trigger_audit_' || p_table_name;

    -- Drop existing trigger if exists
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', v_trigger_name, p_table_name);

    -- Create trigger
    EXECUTE format(
        'CREATE TRIGGER %I
        AFTER INSERT OR UPDATE OR DELETE ON %I
        FOR EACH ROW
        WHEN (pg_trigger_depth() < 2)
        EXECUTE FUNCTION audit_trigger_function()',
        v_trigger_name,
        p_table_name
    );

    RAISE NOTICE 'Audit trigger added to table: %', p_table_name;
END;
$$ LANGUAGE plpgsql;

-- Add audit triggers to all critical tables
SELECT add_audit_trigger('organizations');
SELECT add_audit_trigger('users');
SELECT add_audit_trigger('roles');
SELECT add_audit_trigger('contents');
SELECT add_audit_trigger('tags');
SELECT add_audit_trigger('devices');
SELECT add_audit_trigger('playlists');
SELECT add_audit_trigger('playlist_contents');
SELECT add_audit_trigger('playlist_assignments');
SELECT add_audit_trigger('content_assignments');
SELECT add_audit_trigger('device_groups');
SELECT add_audit_trigger('device_group_members');

-- ============================================================================
-- 5. CREATE AUDIT QUERY HELPER FUNCTIONS
-- ============================================================================

-- Function: Get audit trail for specific entity
CREATE OR REPLACE FUNCTION get_entity_audit_trail(
    p_entity_type VARCHAR,
    p_entity_id INTEGER
)
RETURNS TABLE (
    id INTEGER,
    action VARCHAR,
    username VARCHAR,
    changed_at TIMESTAMP WITH TIME ZONE,
    old_values JSONB,
    new_values JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        al.id,
        al.action,
        COALESCE(al.username, 'system'),
        al.created_at,
        al.old_values,
        al.new_values
    FROM audit_logs al
    WHERE al.entity_type = p_entity_type
      AND al.entity_id = p_entity_id
    ORDER BY al.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_entity_audit_trail(VARCHAR, INTEGER) IS
    'Get complete audit history for a specific entity';

-- Function: Get field-level changes for an entity
CREATE OR REPLACE FUNCTION get_field_changes(
    p_entity_type VARCHAR,
    p_entity_id INTEGER,
    p_field_name VARCHAR
)
RETURNS TABLE (
    changed_at TIMESTAMP WITH TIME ZONE,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        al.created_at,
        (al.old_values->>p_field_name)::TEXT,
        (al.new_values->>p_field_name)::TEXT,
        COALESCE(al.username, 'system')
    FROM audit_logs al
    WHERE al.entity_type = p_entity_type
      AND al.entity_id = p_entity_id
      AND al.action = 'UPDATE'
      AND (
          (al.old_values ? p_field_name AND al.new_values ? p_field_name)
          AND (al.old_values->>p_field_name != al.new_values->>p_field_name)
      )
    ORDER BY al.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_field_changes(VARCHAR, INTEGER, VARCHAR) IS
    'Get history of changes to a specific field';

-- ============================================================================
-- 6. CREATE AUDIT ANALYTICS VIEWS
-- ============================================================================

-- View: Recent activity across all entities
CREATE OR REPLACE VIEW recent_audit_activity AS
SELECT
    al.id,
    al.action,
    al.entity_type,
    al.entity_id,
    al.username,
    al.organization_id,
    al.created_at,
    CASE
        WHEN al.action = 'INSERT' THEN al.new_values->>'title'
        WHEN al.action = 'UPDATE' THEN al.new_values->>'title'
        WHEN al.action = 'DELETE' THEN al.old_values->>'title'
    END as entity_name
FROM audit_logs al
WHERE al.created_at > NOW() - INTERVAL '7 days'
ORDER BY al.created_at DESC;

COMMENT ON VIEW recent_audit_activity IS
    'Recent activity across all audited entities (last 7 days)';

-- View: User activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    al.user_id,
    al.username,
    al.organization_id,
    count(*) as total_actions,
    count(*) FILTER (WHERE al.action = 'INSERT') as inserts,
    count(*) FILTER (WHERE al.action = 'UPDATE') as updates,
    count(*) FILTER (WHERE al.action = 'DELETE') as deletes,
    max(al.created_at) as last_activity
FROM audit_logs al
WHERE al.created_at > NOW() - INTERVAL '30 days'
GROUP BY al.user_id, al.username, al.organization_id
ORDER BY total_actions DESC;

COMMENT ON VIEW user_activity_summary IS
    'User activity summary for the last 30 days';

-- View: Entity modification frequency
CREATE OR REPLACE VIEW entity_modification_frequency AS
SELECT
    al.entity_type,
    al.entity_id,
    count(*) as modification_count,
    count(DISTINCT al.user_id) as unique_modifiers,
    min(al.created_at) as first_modification,
    max(al.created_at) as last_modification
FROM audit_logs al
WHERE al.action IN ('UPDATE', 'DELETE')
GROUP BY al.entity_type, al.entity_id
HAVING count(*) > 5  -- Entities modified more than 5 times
ORDER BY modification_count DESC;

COMMENT ON VIEW entity_modification_frequency IS
    'Entities with high modification frequency (potential issues)';

-- ============================================================================
-- 7. ADD RLS POLICY FOR AUDIT_LOGS
-- ============================================================================

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Audit logs: organization isolation
CREATE POLICY audit_logs_isolation_read ON audit_logs
    FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM current_setting('app.is_super_admin', true) WHERE current_setting('app.is_super_admin', true)::BOOLEAN = TRUE)
        OR organization_id = current_setting('app.current_organization_id', true)::INTEGER
    );

-- Allow INSERT without restriction (system triggers)
CREATE POLICY audit_logs_insert ON audit_logs
    FOR INSERT
    WITH CHECK (TRUE);

COMMENT ON POLICY audit_logs_isolation_read ON audit_logs IS
    'Users can only read audit logs from their organization';

-- ============================================================================
-- 8. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE audit_logs IS 'Automatic audit trail for all critical table changes';
COMMENT ON COLUMN audit_logs.old_values IS 'JSONB snapshot before UPDATE/DELETE';
COMMENT ON COLUMN audit_logs.new_values IS 'JSONB snapshot after INSERT/UPDATE';
COMMENT ON COLUMN audit_logs.request_id IS 'For tracing across microservices';

-- ============================================================================
-- 9. VERIFICATION QUERIES
-- ============================================================================

-- List all audit triggers
SELECT
    trigger_name,
    event_manipulation,
    event_object_table
FROM information_schema.triggers
WHERE trigger_name LIKE 'trigger_audit_%'
ORDER BY event_object_table;

-- Count audit logs
SELECT count(*) as total_audit_logs FROM audit_logs;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;

-- Drop RLS policies
DROP POLICY IF EXISTS audit_logs_isolation_read ON audit_logs;
DROP POLICY IF EXISTS audit_logs_insert ON audit_logs;

-- Drop views
DROP VIEW IF EXISTS recent_audit_activity;
DROP VIEW IF EXISTS user_activity_summary;
DROP VIEW IF EXISTS entity_modification_frequency;

-- Drop helper functions
DROP FUNCTION IF EXISTS get_entity_audit_trail(VARCHAR, INTEGER);
DROP FUNCTION IF EXISTS get_field_changes(VARCHAR, INTEGER, VARCHAR);
DROP FUNCTION IF EXISTS add_audit_trigger(TEXT);

-- Drop all audit triggers
DROP TRIGGER IF EXISTS trigger_audit_organizations ON organizations;
DROP TRIGGER IF EXISTS trigger_audit_users ON users;
DROP TRIGGER IF EXISTS trigger_audit_roles ON roles;
DROP TRIGGER IF EXISTS trigger_audit_contents ON contents;
DROP TRIGGER IF EXISTS trigger_audit_tags ON tags;
DROP TRIGGER IF EXISTS trigger_audit_devices ON devices;
DROP TRIGGER IF EXISTS trigger_audit_playlists ON playlists;
DROP TRIGGER IF EXISTS trigger_audit_playlist_contents ON playlist_contents;
DROP TRIGGER IF EXISTS trigger_audit_playlist_assignments ON playlist_assignments;
DROP TRIGGER IF EXISTS trigger_audit_content_assignments ON content_assignments;
DROP TRIGGER IF EXISTS trigger_audit_device_groups ON device_groups;
DROP TRIGGER IF EXISTS trigger_audit_device_group_members ON device_group_members;

-- Drop trigger function
DROP FUNCTION IF EXISTS audit_trigger_function();

-- Drop indexes
DROP INDEX IF EXISTS idx_audit_logs_entity;
DROP INDEX IF EXISTS idx_audit_logs_org;
DROP INDEX IF EXISTS idx_audit_logs_user;
DROP INDEX IF EXISTS idx_audit_logs_action;
DROP INDEX IF EXISTS idx_audit_logs_date;
DROP INDEX IF EXISTS idx_audit_logs_old_values;
DROP INDEX IF EXISTS idx_audit_logs_new_values;

-- Optionally drop table (WARNING: loses all audit history!)
-- DROP TABLE IF EXISTS audit_logs;

COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- View audit trail for specific content
/*
SELECT * FROM get_entity_audit_trail('contents', 123);
*/

-- See who changed a content title
/*
SELECT * FROM get_field_changes('contents', 123, 'title');
*/

-- Recent activity in organization
/*
SELECT * FROM recent_audit_activity
WHERE organization_id = 1
LIMIT 20;
*/

-- Most active users
/*
SELECT * FROM user_activity_summary
WHERE organization_id = 1
ORDER BY total_actions DESC
LIMIT 10;
*/

-- Find frequently modified entities (potential issues)
/*
SELECT * FROM entity_modification_frequency
WHERE entity_type = 'playlists';
*/

-- ============================================================================
-- MAINTENANCE & CLEANUP
-- ============================================================================
/*
-- Archive old audit logs (run monthly)
-- Keep 90 days of audit logs in main table, archive older

CREATE TABLE IF NOT EXISTS audit_logs_archive (LIKE audit_logs INCLUDING ALL);

BEGIN;

-- Move old logs to archive
INSERT INTO audit_logs_archive
SELECT * FROM audit_logs
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete from main table
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '90 days';

COMMIT;

-- Vacuum to reclaim space
VACUUM ANALYZE audit_logs;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/019_add_audit_triggers.sql
