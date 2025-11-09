-- ============================================================================
-- Migration 010: Create Roles Table (RBAC System)
-- Description: Implement Role-Based Access Control for multi-tenant system
-- Created: 2025-01-09
-- Priority: CRITICAL
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE ROLES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS roles (
    -- Identity
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(200),

    -- Multi-tenancy (NULL for system roles)
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,

    -- System role flag
    is_system_role BOOLEAN DEFAULT FALSE NOT NULL,

    -- Permissions (JSONB for flexibility)
    permissions JSONB NOT NULL DEFAULT '{}',

    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT unique_role_name_per_org UNIQUE (organization_id, name),
    CONSTRAINT check_system_role_no_org CHECK (
        (is_system_role = TRUE AND organization_id IS NULL) OR
        (is_system_role = FALSE AND organization_id IS NOT NULL) OR
        (is_system_role = FALSE AND organization_id IS NULL)
    )
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

-- Organization lookup
CREATE INDEX idx_roles_organization ON roles(organization_id);

-- System roles lookup
CREATE INDEX idx_roles_system ON roles(is_system_role) WHERE is_system_role = TRUE;

-- Name search within organization
CREATE INDEX idx_roles_org_name ON roles(organization_id, name);

-- ============================================================================
-- 3. INSERT DEFAULT SYSTEM ROLES
-- ============================================================================

-- SUPER_ADMIN - Full system access (cross-organization)
INSERT INTO roles (name, description, is_system_role, permissions) VALUES (
    'SUPER_ADMIN',
    'System administrator with full access to all organizations',
    TRUE,
    '{
        "users": ["create", "read", "update", "delete"],
        "organizations": ["create", "read", "update", "delete"],
        "devices": ["create", "read", "update", "delete"],
        "contents": ["create", "read", "update", "delete"],
        "playlists": ["create", "read", "update", "delete"],
        "tags": ["create", "read", "update", "delete"],
        "settings": ["read", "update"],
        "analytics": ["read"],
        "audit_logs": ["read"]
    }'::jsonb
);

-- ADMIN - Organization administrator
INSERT INTO roles (name, description, is_system_role, permissions) VALUES (
    'ADMIN',
    'Organization administrator with full organization access',
    TRUE,
    '{
        "users": ["create", "read", "update", "delete"],
        "devices": ["create", "read", "update", "delete"],
        "contents": ["create", "read", "update", "delete"],
        "playlists": ["create", "read", "update", "delete"],
        "tags": ["create", "read", "update", "delete"],
        "settings": ["read", "update"],
        "analytics": ["read"]
    }'::jsonb
);

-- CONTENT_MANAGER - Content management only
INSERT INTO roles (name, description, is_system_role, permissions) VALUES (
    'CONTENT_MANAGER',
    'Content manager with content and playlist management',
    TRUE,
    '{
        "contents": ["create", "read", "update", "delete"],
        "playlists": ["create", "read", "update", "delete"],
        "tags": ["create", "read", "update"],
        "devices": ["read"],
        "analytics": ["read"]
    }'::jsonb
);

-- VIEWER - Read-only access
INSERT INTO roles (name, description, is_system_role, permissions) VALUES (
    'VIEWER',
    'Read-only access to view content and devices',
    TRUE,
    '{
        "users": ["read"],
        "devices": ["read"],
        "contents": ["read"],
        "playlists": ["read"],
        "tags": ["read"],
        "analytics": ["read"]
    }'::jsonb
);

-- ============================================================================
-- 4. ALTER USERS TABLE (Add role_id foreign key)
-- ============================================================================

-- Add role_id column
ALTER TABLE users
    ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL;

-- Create index for role lookup
CREATE INDEX idx_users_role ON users(role_id);

-- ============================================================================
-- 5. MIGRATE EXISTING USER ROLES
-- ============================================================================

-- Migrate existing users to new RBAC system
-- Map old role string to new role_id

-- SUPER_ADMIN users
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'SUPER_ADMIN' AND is_system_role = TRUE)
WHERE role = 'SUPER_ADMIN';

-- ADMIN users
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'ADMIN' AND is_system_role = TRUE)
WHERE role = 'ADMIN';

-- VIEWER users (if any)
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'VIEWER' AND is_system_role = TRUE)
WHERE role = 'VIEWER';

-- Default fallback: unmapped users become VIEWER
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'VIEWER' AND is_system_role = TRUE)
WHERE role_id IS NULL;

-- ============================================================================
-- 6. DEPRECATE OLD ROLE COLUMN (Keep for backward compatibility)
-- ============================================================================

-- Add comment to mark as deprecated
COMMENT ON COLUMN users.role IS 'DEPRECATED - Use role_id instead. Kept for backward compatibility only.';

-- Make old role column nullable (no longer enforced)
ALTER TABLE users ALTER COLUMN role DROP NOT NULL;

-- ============================================================================
-- 7. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE roles IS 'Role-Based Access Control (RBAC) system for multi-tenant permissions';
COMMENT ON COLUMN roles.name IS 'Role name (unique per organization, system roles have NULL organization_id)';
COMMENT ON COLUMN roles.is_system_role IS 'TRUE for built-in system roles (SUPER_ADMIN, ADMIN, VIEWER, etc.)';
COMMENT ON COLUMN roles.permissions IS 'JSONB permissions map: {"resource": ["action1", "action2"]}';
COMMENT ON COLUMN roles.organization_id IS 'NULL for system roles, organization ID for custom roles';
COMMENT ON CONSTRAINT unique_role_name_per_org ON roles IS 'Role names must be unique within organization (system roles share namespace)';

COMMENT ON COLUMN users.role_id IS 'Foreign key to roles table (new RBAC system)';

-- ============================================================================
-- 8. VERIFICATION QUERY
-- ============================================================================

-- Verify roles table created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = 'roles') as column_count
FROM information_schema.tables
WHERE table_name = 'roles';

-- Verify default roles inserted
SELECT
    name,
    is_system_role,
    description,
    jsonb_object_keys(permissions) as resources
FROM roles
WHERE is_system_role = TRUE
ORDER BY
    CASE name
        WHEN 'SUPER_ADMIN' THEN 1
        WHEN 'ADMIN' THEN 2
        WHEN 'CONTENT_MANAGER' THEN 3
        WHEN 'VIEWER' THEN 4
        ELSE 5
    END;

-- Verify users migrated
SELECT
    role as old_role,
    count(*) as user_count,
    count(role_id) as migrated_count
FROM users
GROUP BY role;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

-- To rollback this migration:
/*
BEGIN;

-- Remove role_id from users
ALTER TABLE users DROP COLUMN role_id;

-- Drop indexes
DROP INDEX IF EXISTS idx_users_role;
DROP INDEX IF EXISTS idx_roles_organization;
DROP INDEX IF EXISTS idx_roles_system;
DROP INDEX IF EXISTS idx_roles_org_name;

-- Drop roles table
DROP TABLE IF EXISTS roles;

-- Restore old role column constraints
ALTER TABLE users ALTER COLUMN role SET NOT NULL;
COMMENT ON COLUMN users.role IS 'User role: SUPER_ADMIN, ADMIN, VIEWER';

COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Create custom role for specific organization
/*
INSERT INTO roles (name, description, organization_id, permissions) VALUES (
    'HOTEL_STAFF',
    'Hotel staff with device management only',
    1, -- organization_id
    '{
        "devices": ["read", "update"],
        "contents": ["read"],
        "playlists": ["read"]
    }'::jsonb
);
*/

-- Assign role to user
/*
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'CONTENT_MANAGER' AND is_system_role = TRUE)
WHERE id = 123;
*/

-- Check user permissions
/*
SELECT
    u.username,
    r.name as role_name,
    r.permissions
FROM users u
JOIN roles r ON r.id = u.role_id
WHERE u.id = 123;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/010_create_roles_table.sql
