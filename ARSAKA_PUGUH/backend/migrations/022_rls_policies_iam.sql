-- ============================================================================
-- Migration: 022_rls_policies_iam.sql
-- Description: Add RLS policies for IAM tables
-- Date: 2026-01-29
-- Phase: Backend completion for PUGUH Control Plane
-- Depends: 021_rls_helper_functions.sql
-- ============================================================================
--
-- This migration adds Row Level Security policies to IAM tables:
-- - roles
-- - role_permissions
-- - user_roles
-- - service_accounts
--
-- Policies enforce:
-- - Tenant isolation (users can only see data in their tenant)
-- - Platform admin bypass (can see all data)
-- - Role-based write permissions (only owners/admins can modify)
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- Enable RLS on tables
-- ============================================================================

ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_accounts ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ROLES policies
-- ============================================================================

-- SELECT: Users can see roles in their tenant
CREATE POLICY roles_select_policy ON roles
    FOR SELECT
    USING (
        is_platform_admin()
        OR tenant_id = current_tenant_id()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
        )
    );

-- INSERT: Only tenant admins can create roles
CREATE POLICY roles_insert_policy ON roles
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- UPDATE: Only tenant admins can update roles (except system roles)
CREATE POLICY roles_update_policy ON roles
    FOR UPDATE
    USING (
        NOT is_system  -- Cannot update system roles
        AND (
            is_platform_admin()
            OR tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
                AND role IN ('owner', 'admin')
            )
        )
    );

-- DELETE: Only tenant owners can delete roles (except system roles)
CREATE POLICY roles_delete_policy ON roles
    FOR DELETE
    USING (
        NOT is_system  -- Cannot delete system roles
        AND (
            is_platform_admin()
            OR tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
                AND role = 'owner'
            )
        )
    );

-- ============================================================================
-- ROLE_PERMISSIONS policies
-- ============================================================================

-- SELECT: Same visibility as roles
CREATE POLICY role_permissions_select_policy ON role_permissions
    FOR SELECT
    USING (
        is_platform_admin()
        OR role_id IN (
            SELECT id FROM roles
            WHERE tenant_id = current_tenant_id()
            OR tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
            )
        )
    );

-- INSERT: Only for roles user can manage
CREATE POLICY role_permissions_insert_policy ON role_permissions
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR role_id IN (
            SELECT id FROM roles r
            WHERE NOT r.is_system
            AND r.tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
                AND role IN ('owner', 'admin')
            )
        )
    );

-- DELETE: Only for roles user can manage
CREATE POLICY role_permissions_delete_policy ON role_permissions
    FOR DELETE
    USING (
        is_platform_admin()
        OR role_id IN (
            SELECT id FROM roles r
            WHERE NOT r.is_system
            AND r.tenant_id IN (
                SELECT tenant_id FROM tenant_memberships
                WHERE user_id = current_app_user_id()
                AND role IN ('owner', 'admin')
            )
        )
    );

-- ============================================================================
-- USER_ROLES policies
-- ============================================================================

-- SELECT: Users can see role assignments in their tenant
CREATE POLICY user_roles_select_policy ON user_roles
    FOR SELECT
    USING (
        is_platform_admin()
        OR tenant_id = current_tenant_id()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
        )
    );

-- INSERT: Only tenant admins can assign roles
CREATE POLICY user_roles_insert_policy ON user_roles
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- DELETE: Only tenant admins can remove role assignments
CREATE POLICY user_roles_delete_policy ON user_roles
    FOR DELETE
    USING (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- ============================================================================
-- SERVICE_ACCOUNTS policies
-- ============================================================================

-- SELECT: Only tenant admins can see service accounts
CREATE POLICY service_accounts_select_policy ON service_accounts
    FOR SELECT
    USING (
        is_platform_admin()
        OR tenant_id = current_tenant_id()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- INSERT: Only tenant admins can create service accounts
CREATE POLICY service_accounts_insert_policy ON service_accounts
    FOR INSERT
    WITH CHECK (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- UPDATE: Only tenant admins can update service accounts
CREATE POLICY service_accounts_update_policy ON service_accounts
    FOR UPDATE
    USING (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role IN ('owner', 'admin')
        )
    );

-- DELETE: Only tenant owners can delete service accounts
CREATE POLICY service_accounts_delete_policy ON service_accounts
    FOR DELETE
    USING (
        is_platform_admin()
        OR tenant_id IN (
            SELECT tenant_id FROM tenant_memberships
            WHERE user_id = current_app_user_id()
            AND role = 'owner'
        )
    );

-- ============================================================================
-- Force RLS (apply even to table owner)
-- ============================================================================

ALTER TABLE roles FORCE ROW LEVEL SECURITY;
ALTER TABLE role_permissions FORCE ROW LEVEL SECURITY;
ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;
ALTER TABLE service_accounts FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- Record migration
-- ============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (22, '022_rls_policies_iam')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;

-- ============================================================================
-- END OF MIGRATION 022
-- ============================================================================
