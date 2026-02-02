-- ============================================================================
-- Migration: 020_iam_roles_permissions.sql
-- Description: Add IAM tables for roles, permissions, and role assignments
-- Date: 2026-01-29
-- Phase: Backend completion for PUGUH Control Plane
-- ============================================================================
--
-- This migration adds IAM (Identity and Access Management) tables to support
-- the frontend IAM domain screens. It works alongside existing tables:
-- - users (from 007_identity_auth_tables.sql)
-- - tenant_members (from 008_tenant_module_additions.sql)
--
-- New tables:
-- - roles: Role definitions per tenant
-- - permissions: Permission definitions
-- - role_permissions: Many-to-many role-permission mapping
-- - user_roles: User role assignments per tenant
-- - service_accounts: Service account credentials
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- TABLE: roles
-- Role definitions per tenant
-- ============================================================================

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,  -- System roles cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Unique role name per tenant
    CONSTRAINT roles_tenant_name_unique UNIQUE (tenant_id, name)
);

-- Indexes
CREATE INDEX idx_roles_tenant_id ON roles(tenant_id);

-- Comments
COMMENT ON TABLE roles IS 'Role definitions for IAM - one set per tenant';
COMMENT ON COLUMN roles.is_system IS 'System roles (owner, admin, member) cannot be deleted';

-- ============================================================================
-- TABLE: permissions
-- Permission definitions (global, not per-tenant)
-- ============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,  -- e.g., "rules", "workflows", "users"
    action VARCHAR(100) NOT NULL,    -- e.g., "read", "create", "update", "delete", "approve"
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Unique permission per resource+action
    CONSTRAINT permissions_resource_action_unique UNIQUE (resource, action)
);

-- Comments
COMMENT ON TABLE permissions IS 'Permission definitions - global list of all possible permissions';
COMMENT ON COLUMN permissions.resource IS 'Resource type (rules, workflows, users, etc.)';
COMMENT ON COLUMN permissions.action IS 'Action type (read, create, update, delete, approve)';

-- ============================================================================
-- TABLE: role_permissions
-- Many-to-many mapping of roles to permissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    PRIMARY KEY (role_id, permission_id)
);

-- Indexes
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Comments
COMMENT ON TABLE role_permissions IS 'Many-to-many mapping of roles to permissions';

-- ============================================================================
-- TABLE: user_roles
-- User role assignments per tenant
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(user_id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- User can only have each role once per tenant
    CONSTRAINT user_roles_unique UNIQUE (user_id, role_id, tenant_id)
);

-- Indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_tenant_id ON user_roles(tenant_id);

-- Comments
COMMENT ON TABLE user_roles IS 'User role assignments - which users have which roles in which tenants';

-- ============================================================================
-- TABLE: service_accounts
-- Service account credentials for SDK/API access
-- ============================================================================

CREATE TABLE IF NOT EXISTS service_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    client_id VARCHAR(64) NOT NULL UNIQUE,  -- Public identifier
    -- Note: client_secret is stored hashed, not plaintext
    client_secret_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,  -- active, suspended, revoked
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    CONSTRAINT service_accounts_status_valid CHECK (status IN ('active', 'suspended', 'revoked'))
);

-- Indexes
CREATE INDEX idx_service_accounts_tenant_id ON service_accounts(tenant_id);
CREATE INDEX idx_service_accounts_client_id ON service_accounts(client_id);

-- Comments
COMMENT ON TABLE service_accounts IS 'Service accounts for SDK/API authentication';
COMMENT ON COLUMN service_accounts.client_id IS 'Public client identifier (shown to user)';
COMMENT ON COLUMN service_accounts.client_secret_hash IS 'Hashed client secret (never store plaintext)';

-- ============================================================================
-- SEED DATA: Default permissions
-- ============================================================================

INSERT INTO permissions (resource, action, description) VALUES
    -- Rules permissions
    ('rules', 'read', 'View rules'),
    ('rules', 'create', 'Create new rule drafts'),
    ('rules', 'update', 'Update rule drafts'),
    ('rules', 'delete', 'Delete rule drafts'),
    ('rules', 'activate', 'Request rule activation'),

    -- Decisions permissions
    ('decisions', 'read', 'View decision history'),

    -- Workflows permissions
    ('workflows', 'read', 'View workflows'),
    ('workflows', 'approve', 'Approve workflows'),
    ('workflows', 'reject', 'Reject workflows'),
    ('workflows', 'delegate', 'Delegate workflows'),
    ('workflows', 'escalate', 'Escalate workflows'),

    -- Audit permissions
    ('audit', 'read', 'View audit trail'),

    -- Events permissions
    ('events', 'read', 'View event log'),

    -- Metrics permissions
    ('metrics', 'read', 'View system metrics'),

    -- Users permissions (IAM)
    ('users', 'read', 'View users in tenant'),
    ('users', 'manage', 'Manage user roles'),

    -- Roles permissions (IAM)
    ('roles', 'read', 'View roles'),
    ('roles', 'create', 'Create custom roles'),
    ('roles', 'update', 'Update roles'),
    ('roles', 'delete', 'Delete custom roles'),

    -- Service accounts permissions
    ('service_accounts', 'read', 'View service accounts'),
    ('service_accounts', 'create', 'Create service accounts'),
    ('service_accounts', 'update', 'Update service accounts'),
    ('service_accounts', 'delete', 'Delete service accounts')
ON CONFLICT (resource, action) DO NOTHING;

-- ============================================================================
-- RLS Policies for new tables (simplified for Phase A)
-- Note: Full RLS will be added when helper functions are created
-- ============================================================================

-- For now, we skip RLS policies since helper functions don't exist yet
-- The backend uses explicit tenant_id filtering in queries

-- ============================================================================
-- Record migration
-- ============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (20, '020_iam_roles_permissions')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;

-- ============================================================================
-- END OF MIGRATION 020
-- ============================================================================
