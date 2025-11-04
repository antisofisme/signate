-- =============================================================================
-- SMART TV DIGITAL SIGNAGE - DATABASE SCHEMA (PHASE 1: AUTH)
-- =============================================================================
-- Phase 1: Authentication & Authorization
-- Tables: organizations, users
-- =============================================================================

-- =============================================================================
-- TABLE: organizations
-- Purpose: Multi-tenant organization management
-- =============================================================================
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    organization_pin CHAR(6) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_pin ON organizations(organization_pin);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);

COMMENT ON TABLE organizations IS 'Multi-tenant organizations';
COMMENT ON COLUMN organizations.organization_pin IS '6-digit PIN untuk device registration';

-- =============================================================================
-- TABLE: users
-- Purpose: User authentication dan role-based access control
-- =============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE,
    full_name VARCHAR(200),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('super_admin', 'admin', 'user')),
    is_active BOOLEAN DEFAULT TRUE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_organization_id ON users(organization_id);

COMMENT ON TABLE users IS 'System users dengan RBAC';
COMMENT ON COLUMN users.role IS 'super_admin: global access, admin: organization admin, user: regular user';

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto update updated_at on organizations
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto update updated_at on users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SEED DATA (PHASE 1)
-- =============================================================================

-- Insert default organization
INSERT INTO organizations (name, organization_pin) VALUES
('Default Organization', '123456');

-- Insert default admin user
-- Password: admin123 (hashed with bcrypt)
-- IMPORTANT: Change this password in production!
INSERT INTO users (username, password_hash, email, full_name, role, organization_id) VALUES
('admin', '$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2', 'admin@signage.local', 'System Administrator', 'super_admin', 1);

-- Insert test organization admin
INSERT INTO organizations (name, organization_pin) VALUES
('Test Hotel', '654321');

INSERT INTO users (username, password_hash, email, full_name, role, organization_id) VALUES
('hotel_admin', '$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2', 'admin@testhotel.com', 'Hotel Administrator', 'admin', 2);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these to verify the setup:
-- SELECT * FROM organizations;
-- SELECT username, email, role, organization_id FROM users;
