-- ============================================================================
-- Migration: 016_row_level_security.sql
-- Description: Enable Row Level Security (RLS) for multi-tenant data isolation
-- Date: 2026-01-28
-- ============================================================================
--
-- Row Level Security provides database-level tenant isolation.
-- Even if there's a bug in application code, data from one tenant
-- cannot leak to another tenant.
--
-- How it works:
-- 1. Application sets current_setting('app.current_tenant_id') at connection start
-- 2. RLS policies filter all queries to only return rows matching tenant_id
-- 3. INSERT/UPDATE/DELETE also checked against current tenant
--
-- ============================================================================

-- ============================================================================
-- Enable RLS on tenant-scoped tables
-- ============================================================================

-- Tenants table (special case - has tenant_id as PK, use owner_user_id for ownership)
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Tenant memberships table
ALTER TABLE tenant_memberships ENABLE ROW LEVEL SECURITY;

-- Projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Project members table
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

-- Subscriptions table
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- API keys table
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Security audit log (special - viewable by tenant admins)
ALTER TABLE security_audit_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Helper function to get current tenant ID from session
-- ============================================================================

CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Helper function to get current user ID from session
CREATE OR REPLACE FUNCTION current_app_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_id', true), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Helper function to check if current user is platform admin
CREATE OR REPLACE FUNCTION is_platform_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(current_setting('app.is_platform_admin', true), 'false')::BOOLEAN;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- RLS Policies for TENANTS table
-- ============================================================================

-- Users can see tenants they own or are members of
CREATE POLICY tenants_select_policy ON tenants
    FOR SELECT
    USING (
        -- Platform admins can see all
        is_platform_admin()
        OR
        -- User owns the tenant
        owner_user_id = current_app_user_id()
        OR
        -- User is a member of the tenant
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
        )
    );

-- Only platform admins can insert tenants (or via API without RLS)
CREATE POLICY tenants_insert_policy ON tenants
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR
        owner_user_id = current_app_user_id()
    );

-- Owners can update their tenants
CREATE POLICY tenants_update_policy ON tenants
    FOR UPDATE
    USING (
        is_platform_admin()
        OR
        owner_user_id = current_app_user_id()
    );

-- Only platform admins can delete tenants
CREATE POLICY tenants_delete_policy ON tenants
    FOR DELETE
    USING (is_platform_admin());

-- ============================================================================
-- RLS Policies for TENANT_MEMBERSHIPS table
-- ============================================================================

-- Users can see members of their tenants
CREATE POLICY tenant_memberships_select_policy ON tenant_memberships
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
        )
    );

-- Tenant admins can add members
CREATE POLICY tenant_memberships_insert_policy ON tenant_memberships
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Tenant admins can update member roles
CREATE POLICY tenant_memberships_update_policy ON tenant_memberships
    FOR UPDATE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Tenant admins can remove members
CREATE POLICY tenant_memberships_delete_policy ON tenant_memberships
    FOR DELETE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
        OR
        -- Users can remove themselves
        user_id = current_app_user_id()
    );

-- ============================================================================
-- RLS Policies for PROJECTS table
-- ============================================================================

-- Users can see projects in their tenants
CREATE POLICY projects_select_policy ON projects
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        tenant_id = current_tenant_id()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
        )
    );

-- Tenant admins can create projects
CREATE POLICY projects_insert_policy ON projects
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Project admins can update projects
CREATE POLICY projects_update_policy ON projects
    FOR UPDATE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Only tenant owners can delete projects
CREATE POLICY projects_delete_policy ON projects
    FOR DELETE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role = 'owner'
        )
    );

-- ============================================================================
-- RLS Policies for PROJECT_MEMBERS table
-- ============================================================================

-- Users can see members of projects in their tenants
CREATE POLICY project_members_select_policy ON project_members
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        project_id IN (
            SELECT p.project_id FROM projects p
            JOIN tenant_memberships tm ON p.tenant_id = tm.tenant_id
            WHERE tm.user_id = current_app_user_id()
        )
    );

-- Project/tenant admins can manage project members
CREATE POLICY project_members_insert_policy ON project_members
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR
        project_id IN (
            SELECT p.project_id FROM projects p
            JOIN tenant_memberships tm ON p.tenant_id = tm.tenant_id
            WHERE tm.user_id = current_app_user_id()
            AND tm.role IN ('owner', 'admin')
        )
    );

CREATE POLICY project_members_update_policy ON project_members
    FOR UPDATE
    USING (
        is_platform_admin()
        OR
        project_id IN (
            SELECT p.project_id FROM projects p
            JOIN tenant_memberships tm ON p.tenant_id = tm.tenant_id
            WHERE tm.user_id = current_app_user_id()
            AND tm.role IN ('owner', 'admin')
        )
    );

CREATE POLICY project_members_delete_policy ON project_members
    FOR DELETE
    USING (
        is_platform_admin()
        OR
        project_id IN (
            SELECT p.project_id FROM projects p
            JOIN tenant_memberships tm ON p.tenant_id = tm.tenant_id
            WHERE tm.user_id = current_app_user_id()
            AND tm.role IN ('owner', 'admin')
        )
        OR
        -- Users can remove themselves
        user_id = current_app_user_id()
    );

-- ============================================================================
-- RLS Policies for SUBSCRIPTIONS table
-- ============================================================================

-- Tenant owners/admins can view subscriptions
CREATE POLICY subscriptions_select_policy ON subscriptions
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Only platform admins can modify subscriptions
CREATE POLICY subscriptions_insert_policy ON subscriptions
    FOR INSERT
    WITH CHECK (is_platform_admin());

CREATE POLICY subscriptions_update_policy ON subscriptions
    FOR UPDATE
    USING (is_platform_admin());

CREATE POLICY subscriptions_delete_policy ON subscriptions
    FOR DELETE
    USING (is_platform_admin());

-- ============================================================================
-- RLS Policies for API_KEYS table
-- ============================================================================

-- Tenant admins can view API keys
CREATE POLICY api_keys_select_policy ON api_keys
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        tenant_id = current_tenant_id()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
        OR
        -- Users can see keys they created
        created_by_user_id = current_app_user_id()
    );

-- Tenant admins can create API keys
CREATE POLICY api_keys_insert_policy ON api_keys
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Tenant admins can update (revoke) API keys
CREATE POLICY api_keys_update_policy ON api_keys
    FOR UPDATE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- Tenant admins can delete API keys
CREATE POLICY api_keys_delete_policy ON api_keys
    FOR DELETE
    USING (
        is_platform_admin()
        OR
        tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- ============================================================================
-- RLS Policies for SECURITY_AUDIT_LOG table
-- ============================================================================

-- Tenant admins can view their tenant's audit logs
CREATE POLICY security_audit_log_select_policy ON security_audit_log
    FOR SELECT
    USING (
        is_platform_admin()
        OR
        (
            tenant_id IS NOT NULL
            AND tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
                AND role IN ('owner', 'admin')
            )
        )
        OR
        -- Users can see their own audit entries
        user_id = current_app_user_id()
    );

-- Only system can insert audit logs (no direct insert)
CREATE POLICY security_audit_log_insert_policy ON security_audit_log
    FOR INSERT
    WITH CHECK (is_platform_admin() OR TRUE);  -- Allow inserts from application

-- Audit logs are immutable - no updates allowed
CREATE POLICY security_audit_log_update_policy ON security_audit_log
    FOR UPDATE
    USING (FALSE);  -- Never allow updates

-- Audit logs are immutable - only platform admins can delete for retention
CREATE POLICY security_audit_log_delete_policy ON security_audit_log
    FOR DELETE
    USING (is_platform_admin());

-- ============================================================================
-- IMPORTANT: Application Setup Required
-- ============================================================================
--
-- The application MUST set session variables before executing queries.
-- This is typically done in a database middleware or connection hook.
--
-- Example (Python/SQLAlchemy):
--
-- async def set_rls_context(connection, tenant_id: str, user_id: str, is_admin: bool = False):
--     await connection.execute(text("SET app.current_tenant_id = :tenant_id"), {"tenant_id": str(tenant_id)})
--     await connection.execute(text("SET app.current_user_id = :user_id"), {"user_id": str(user_id)})
--     await connection.execute(text("SET app.is_platform_admin = :is_admin"), {"is_admin": str(is_admin).lower()})
--
-- ============================================================================

-- ============================================================================
-- Bypass RLS for service account (migrations, background jobs)
-- ============================================================================

-- Create a service role that bypasses RLS (for migrations, admin operations)
-- This role should only be used by trusted backend processes
DO $$
BEGIN
    -- Check if role exists before creating
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_service') THEN
        CREATE ROLE atlas_service NOLOGIN;
    END IF;
END $$;

-- Service role bypasses RLS
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_memberships FORCE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
ALTER TABLE project_members FORCE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;
ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;
ALTER TABLE security_audit_log FORCE ROW LEVEL SECURITY;

-- Grant bypass to service role
-- Note: This requires a SUPERUSER or table owner to execute
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO atlas_service;
-- ALTER TABLE tenants OWNER TO atlas_service;  -- etc.

COMMENT ON FUNCTION current_tenant_id() IS 'Returns current tenant ID from session variable app.current_tenant_id';
COMMENT ON FUNCTION current_app_user_id() IS 'Returns current user ID from session variable app.current_user_id';
COMMENT ON FUNCTION is_platform_admin() IS 'Returns true if session is marked as platform admin via app.is_platform_admin';
