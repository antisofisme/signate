-- =====================================================================
-- Migration: Add Multi-Tenant Support
-- Version: 006
-- Date: 2024
-- Description: Add organizations, roles, and multi-tenant data isolation
-- =====================================================================

-- 1. Create organizations table
-- =====================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    settings JSONB DEFAULT '{}',
    max_devices INTEGER DEFAULT 10,
    max_users INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 10,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_active ON organizations(is_active);
CREATE INDEX idx_organizations_subscription ON organizations(subscription_tier);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. Create roles table
-- =====================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    description VARCHAR(500),
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, organization_id)
);

-- Add indexes
CREATE INDEX idx_roles_org ON roles(organization_id);
CREATE INDEX idx_roles_system ON roles(is_system_role);

-- 3. Create user_organizations junction table
-- =====================================================================
CREATE TABLE IF NOT EXISTS user_organizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    invited_by INTEGER REFERENCES users(id),
    invitation_token VARCHAR(100),
    invitation_expires_at TIMESTAMP,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    UNIQUE(user_id, organization_id)
);

-- Add indexes
CREATE INDEX idx_user_orgs_user ON user_organizations(user_id);
CREATE INDEX idx_user_orgs_org ON user_organizations(organization_id);
CREATE INDEX idx_user_orgs_role ON user_organizations(role_id);
CREATE INDEX idx_user_orgs_active ON user_organizations(is_active);
CREATE INDEX idx_user_orgs_primary ON user_organizations(is_primary);

-- 4. Add is_super_admin column to users table
-- =====================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- 5. Create default organization for existing data
-- =====================================================================
INSERT INTO organizations (name, slug, description, max_devices, max_users, max_storage_gb)
VALUES ('Default Organization', 'default', 'Migrated from single-tenant system', 100, 50, 500)
ON CONFLICT (slug) DO NOTHING;

-- 6. Create default system roles
-- =====================================================================
INSERT INTO roles (name, display_name, description, is_system_role, permissions)
VALUES
    ('super_admin', 'Super Admin', 'Full system access', TRUE,
     '{"*": ["*"]}'),
    ('admin', 'Admin', 'Organization administrator', TRUE,
     '{"organizations": ["read", "update"], "users": ["create", "read", "update", "delete"], "roles": ["read"], "devices": ["create", "read", "update", "delete"], "content": ["create", "read", "update", "delete"], "playlists": ["create", "read", "update", "delete"], "tags": ["create", "read", "update", "delete"], "logs": ["read"], "settings": ["read", "update"]}'),
    ('editor', 'Editor', 'Content editor', TRUE,
     '{"devices": ["read", "update"], "content": ["create", "read", "update", "delete"], "playlists": ["create", "read", "update", "delete"], "tags": ["create", "read", "update"], "logs": ["read"]}'),
    ('viewer', 'Viewer', 'Read-only access', TRUE,
     '{"devices": ["read"], "content": ["read"], "playlists": ["read"], "tags": ["read"], "logs": ["read"]}')
ON CONFLICT (name, organization_id) DO NOTHING;

-- 7. Add organization_id to existing tables (if not exists)
-- =====================================================================
ALTER TABLE devices ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE content ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE playlists ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE tags ADD COLUMN IF NOT EXISTS organization_id INTEGER;

-- Add created_by columns for audit trail
ALTER TABLE devices ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE content ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE playlists ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE tags ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);

-- 8. Migrate existing data to default organization
-- =====================================================================
UPDATE devices SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE content SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE playlists SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE tags SET organization_id = 1 WHERE organization_id IS NULL;

-- 9. Migrate existing users to default organization with appropriate roles
-- =====================================================================
-- First, set super admin flag for existing admin users
UPDATE users SET is_super_admin = TRUE WHERE role = 'admin';

-- Create user-organization relationships
INSERT INTO user_organizations (user_id, organization_id, role_id, is_primary, is_active)
SELECT
    u.id,
    1,  -- Default organization
    CASE
        WHEN u.role = 'admin' THEN (SELECT id FROM roles WHERE name = 'admin' AND is_system_role = TRUE LIMIT 1)
        WHEN u.role = 'editor' THEN (SELECT id FROM roles WHERE name = 'editor' AND is_system_role = TRUE LIMIT 1)
        ELSE (SELECT id FROM roles WHERE name = 'viewer' AND is_system_role = TRUE LIMIT 1)
    END,
    TRUE,  -- Set as primary organization
    TRUE   -- Active
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_organizations uo
    WHERE uo.user_id = u.id AND uo.organization_id = 1
);

-- 10. Add NOT NULL constraints and foreign keys
-- =====================================================================
-- Make organization_id required
ALTER TABLE devices
    ALTER COLUMN organization_id SET NOT NULL,
    ADD CONSTRAINT fk_devices_organization FOREIGN KEY (organization_id)
    REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE content
    ALTER COLUMN organization_id SET NOT NULL,
    ADD CONSTRAINT fk_content_organization FOREIGN KEY (organization_id)
    REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE playlists
    ALTER COLUMN organization_id SET NOT NULL,
    ADD CONSTRAINT fk_playlists_organization FOREIGN KEY (organization_id)
    REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE tags
    ALTER COLUMN organization_id SET NOT NULL,
    ADD CONSTRAINT fk_tags_organization FOREIGN KEY (organization_id)
    REFERENCES organizations(id) ON DELETE CASCADE;

-- 11. Add indexes for performance
-- =====================================================================
CREATE INDEX idx_devices_org ON devices(organization_id);
CREATE INDEX idx_content_org ON content(organization_id);
CREATE INDEX idx_playlists_org ON playlists(organization_id);
CREATE INDEX idx_tags_org ON tags(organization_id);

CREATE INDEX idx_devices_created_by ON devices(created_by);
CREATE INDEX idx_content_created_by ON content(created_by);
CREATE INDEX idx_playlists_created_by ON playlists(created_by);
CREATE INDEX idx_tags_created_by ON tags(created_by);

-- 12. Create audit log table for tracking changes
-- =====================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- 13. Create session tracking table
-- =====================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_refresh ON user_sessions(refresh_token);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, expires_at);

-- 14. Update existing relationships for multi-tenancy
-- =====================================================================
-- Update device_tags relationship
ALTER TABLE device_tags ADD COLUMN IF NOT EXISTS organization_id INTEGER;
UPDATE device_tags dt SET organization_id = d.organization_id
FROM devices d WHERE dt.device_id = d.id AND dt.organization_id IS NULL;
ALTER TABLE device_tags ALTER COLUMN organization_id SET NOT NULL;

-- Update content_assignments
ALTER TABLE content_assignments ADD COLUMN IF NOT EXISTS organization_id INTEGER;
UPDATE content_assignments ca SET organization_id = d.organization_id
FROM devices d WHERE ca.device_id = d.id AND ca.organization_id IS NULL;
ALTER TABLE content_assignments ALTER COLUMN organization_id SET NOT NULL;

-- Update playlist_assignments
ALTER TABLE playlist_assignments ADD COLUMN IF NOT EXISTS organization_id INTEGER;
UPDATE playlist_assignments pa SET organization_id = d.organization_id
FROM devices d WHERE pa.device_id = d.id AND pa.organization_id IS NULL;
ALTER TABLE playlist_assignments ALTER COLUMN organization_id SET NOT NULL;

-- 15. Create views for common queries
-- =====================================================================
-- View for user's accessible organizations
CREATE OR REPLACE VIEW user_accessible_organizations AS
SELECT
    uo.user_id,
    o.id AS organization_id,
    o.name AS organization_name,
    o.slug AS organization_slug,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.permissions,
    uo.is_primary,
    uo.joined_at
FROM user_organizations uo
JOIN organizations o ON uo.organization_id = o.id
JOIN roles r ON uo.role_id = r.id
WHERE uo.is_active = TRUE AND o.is_active = TRUE;

-- View for organization statistics
CREATE OR REPLACE VIEW organization_statistics AS
SELECT
    o.id AS organization_id,
    o.name AS organization_name,
    COUNT(DISTINCT d.id) AS device_count,
    COUNT(DISTINCT c.id) AS content_count,
    COUNT(DISTINCT p.id) AS playlist_count,
    COUNT(DISTINCT uo.user_id) AS user_count
FROM organizations o
LEFT JOIN devices d ON o.id = d.organization_id
LEFT JOIN content c ON o.id = c.organization_id
LEFT JOIN playlists p ON o.id = p.organization_id
LEFT JOIN user_organizations uo ON o.id = uo.organization_id AND uo.is_active = TRUE
GROUP BY o.id, o.name;

-- 16. Grant appropriate permissions (adjust based on your database user)
-- =====================================================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- 17. Add comments for documentation
-- =====================================================================
COMMENT ON TABLE organizations IS 'Multi-tenant organizations';
COMMENT ON TABLE roles IS 'Role definitions for RBAC';
COMMENT ON TABLE user_organizations IS 'User membership in organizations';
COMMENT ON TABLE audit_logs IS 'Audit trail for all system actions';
COMMENT ON TABLE user_sessions IS 'Active user sessions tracking';

COMMENT ON COLUMN organizations.slug IS 'URL-friendly unique identifier';
COMMENT ON COLUMN organizations.settings IS 'Organization-specific configuration as JSON';
COMMENT ON COLUMN roles.permissions IS 'Permission matrix as JSON';
COMMENT ON COLUMN user_organizations.is_primary IS 'User default organization';

-- =====================================================================
-- Migration completed successfully
-- To rollback, run migration 006_rollback_multi_tenancy.sql
-- =====================================================================