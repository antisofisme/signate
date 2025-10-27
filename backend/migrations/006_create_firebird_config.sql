-- Migration: 006_create_firebird_config.sql
-- Purpose: Create table for Firebird database integration
-- Author: System Architect
-- Date: 2025-10-27
-- Updated: Simplified schema to match FirebirdConfig model

-- ============================================================
-- Firebird Configuration Table
-- ============================================================
-- Stores connection settings and configuration for external
-- Firebird databases. Supports both server and embedded modes.
-- ============================================================

CREATE TABLE IF NOT EXISTS firebird_config (
    id SERIAL PRIMARY KEY,

    -- Unique identifier for this configuration
    config_key VARCHAR(50) UNIQUE NOT NULL,

    -- Connection Settings
    -- api_endpoint: DSN format
    --   Server mode: "host:port/path/to/db.gdb"
    --   Embedded: "/path/to/db.fdb"
    api_endpoint VARCHAR(500) NOT NULL,

    -- api_key: Encrypted "username:password" string
    api_key VARCHAR(255) NOT NULL,

    -- Operational Settings
    refresh_interval INTEGER DEFAULT 300,       -- Data refresh interval in seconds
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Health Monitoring Fields
    last_sync TIMESTAMP WITH TIME ZONE,

    -- Additional Configuration (JSON)
    -- Can store table mappings, query templates, etc.
    config_json TEXT,

    -- Administrative Notes
    notes TEXT,

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_firebird_config_active ON firebird_config(is_active);
CREATE INDEX IF NOT EXISTS idx_firebird_config_key ON firebird_config(config_key);

-- ============================================================
-- Helper Functions
-- ============================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_firebird_config_updated_at_fn()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at column
DROP TRIGGER IF EXISTS update_firebird_config_updated_at ON firebird_config;
CREATE TRIGGER update_firebird_config_updated_at
    BEFORE UPDATE ON firebird_config
    FOR EACH ROW
    EXECUTE FUNCTION update_firebird_config_updated_at_fn();

-- ============================================================
-- Default Data (Optional)
-- ============================================================

-- Insert a sample configuration (commented out by default)
-- Before using, encrypt the password using the application's encryption service
--
-- INSERT INTO firebird_config (
--     config_key,
--     api_endpoint,
--     api_key,
--     refresh_interval,
--     is_active,
--     notes
-- ) VALUES (
--     'hotel_pms',
--     '192.168.1.100:3050/opt/databases/powerfo.gdb',
--     'ENCRYPTED_USERNAME_PASSWORD_HERE',  -- Must be encrypted!
--     300,
--     true,
--     'Hotel PMS database connection'
-- );

-- ============================================================
-- Migration Notes
-- ============================================================
--
-- Schema Design:
-- - Simplified from previous design to match FastAPI model
-- - api_endpoint: Combined DSN string (host:port/path or just path)
-- - api_key: Encrypted credentials (username:password)
-- - No separate tables for logs/cache/templates (can be added later)
--
-- Security:
-- - api_key must be encrypted using Fernet encryption
-- - Encryption key should be stored in environment variable
-- - Use firebird_service.encrypt_api_key() to encrypt before insert
--
-- Usage:
-- 1. Create configuration via API endpoint POST /api/firebird/configs
-- 2. Test connection via POST /api/firebird/configs/{id}/test
-- 3. Execute queries via POST /api/firebird/configs/{id}/query
-- 4. Monitor health via GET /api/firebird/configs/{id}/health
--
-- ============================================================
-- Rollback Script
-- ============================================================
-- To rollback this migration, run:
-- DROP TRIGGER IF EXISTS update_firebird_config_updated_at ON firebird_config;
-- DROP FUNCTION IF EXISTS update_firebird_config_updated_at_fn() CASCADE;
-- DROP TABLE IF EXISTS firebird_config CASCADE;
