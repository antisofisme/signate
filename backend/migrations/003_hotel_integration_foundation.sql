-- Migration: Hotel Integration Foundation
-- Date: 2025-10-26
-- Description: Add hotel-specific features including PMS integration, guest mapping, templates, and security
-- Phase: 0 - Hotel Integration Foundation

-- ===========================================================================
-- PART 1: External Data Sources (PMS/POS Integration)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS external_data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('pms', 'pos', 'crm', 'other')),
    api_endpoint VARCHAR(500),
    api_key_encrypted TEXT,
    auth_type VARCHAR(50) CHECK (auth_type IN ('oauth2', 'api_key', 'basic', 'custom')),
    is_active BOOLEAN DEFAULT TRUE,
    sync_interval INTEGER DEFAULT 30,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_data_sources_type ON external_data_sources(type);
CREATE INDEX IF NOT EXISTS idx_external_data_sources_active ON external_data_sources(is_active);

COMMENT ON TABLE external_data_sources IS 'External API integrations (PMS, POS, CRM systems)';
COMMENT ON COLUMN external_data_sources.sync_interval IS 'Sync interval in seconds';
COMMENT ON COLUMN external_data_sources.config IS 'JSON configuration including field mappings';

-- ===========================================================================
-- PART 2: Device-Guest Mappings
-- ===========================================================================

CREATE TABLE IF NOT EXISTS device_guest_mappings (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

    -- Guest Info (from PMS)
    guest_id VARCHAR(100),
    guest_name VARCHAR(200),
    guest_name_encrypted BYTEA,
    guest_nationality VARCHAR(10),
    guest_language VARCHAR(10),
    loyalty_tier VARCHAR(50),

    -- Reservation Info
    room_number VARCHAR(20),
    check_in_date TIMESTAMP WITH TIME ZONE,
    check_out_date TIMESTAMP WITH TIME ZONE,

    -- Preferences (JSONB for flexibility)
    preferences JSONB,
    special_requests TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit & Sync
    synced_from VARCHAR(50),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    encryption_key_id VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_device_guest_mappings_device_id ON device_guest_mappings(device_id);
CREATE INDEX IF NOT EXISTS idx_device_guest_mappings_guest_id ON device_guest_mappings(guest_id);
CREATE INDEX IF NOT EXISTS idx_device_guest_mappings_room ON device_guest_mappings(room_number);
CREATE INDEX IF NOT EXISTS idx_device_guest_mappings_active ON device_guest_mappings(is_active);
CREATE INDEX IF NOT EXISTS idx_device_guest_mappings_checkout ON device_guest_mappings(check_out_date) WHERE is_active = TRUE;

COMMENT ON TABLE device_guest_mappings IS 'Maps devices to current guests for personalization';
COMMENT ON COLUMN device_guest_mappings.guest_name_encrypted IS 'Encrypted guest name for GDPR compliance';
COMMENT ON COLUMN device_guest_mappings.preferences IS 'JSON: dietary, temperature, pillow type, etc.';
COMMENT ON COLUMN device_guest_mappings.deleted_at IS 'Soft delete timestamp for retention policy';

-- ===========================================================================
-- PART 3: Room Configurations
-- ===========================================================================

CREATE TABLE IF NOT EXISTS room_configurations (
    id SERIAL PRIMARY KEY,
    room_number VARCHAR(20) UNIQUE NOT NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,

    -- Room Info
    room_type VARCHAR(50),
    floor INTEGER,
    building VARCHAR(50),

    -- Content Defaults
    default_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,
    default_language VARCHAR(10) DEFAULT 'en',

    -- Features
    has_minibar BOOLEAN DEFAULT FALSE,
    has_balcony BOOLEAN DEFAULT FALSE,
    max_occupancy INTEGER DEFAULT 2,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_room_configurations_number ON room_configurations(room_number);
CREATE INDEX IF NOT EXISTS idx_room_configurations_device ON room_configurations(device_id);
CREATE INDEX IF NOT EXISTS idx_room_configurations_type ON room_configurations(room_type);

COMMENT ON TABLE room_configurations IS 'Room-specific settings and device mappings';

-- ===========================================================================
-- PART 4: Enhance devices table for hotel features
-- ===========================================================================

ALTER TABLE devices
ADD COLUMN IF NOT EXISTS room_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS location_type VARCHAR(50) DEFAULT 'guest_room' CHECK (location_type IN ('guest_room', 'public_area', 'staff_area', 'meeting_room')),
ADD COLUMN IF NOT EXISTS supports_personalization BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS privacy_mode VARCHAR(50) DEFAULT 'limited' CHECK (privacy_mode IN ('full', 'limited', 'none'));

CREATE INDEX IF NOT EXISTS idx_devices_room_number ON devices(room_number);
CREATE INDEX IF NOT EXISTS idx_devices_location_type ON devices(location_type);

COMMENT ON COLUMN devices.room_number IS 'Room number for guest room devices';
COMMENT ON COLUMN devices.location_type IS 'Type of location (guest_room, public_area, staff_area, meeting_room)';
COMMENT ON COLUMN devices.supports_personalization IS 'Whether device supports guest personalization';
COMMENT ON COLUMN devices.privacy_mode IS 'full: show all PII, limited: welcome only, none: generic';

-- ===========================================================================
-- PART 5: Enhance content table for templates and multi-language
-- ===========================================================================

ALTER TABLE content
ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS template_variables JSONB,
ADD COLUMN IF NOT EXISTS language_code VARCHAR(10),
ADD COLUMN IF NOT EXISTS content_group_id INTEGER,
ADD COLUMN IF NOT EXISTS fallback_content_id INTEGER REFERENCES content(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_content_is_template ON content(is_template);
CREATE INDEX IF NOT EXISTS idx_content_language ON content(language_code);
CREATE INDEX IF NOT EXISTS idx_content_group ON content(content_group_id);

COMMENT ON COLUMN content.is_template IS 'Whether this content uses template variables';
COMMENT ON COLUMN content.template_variables IS 'JSON array of variable names used in template';
COMMENT ON COLUMN content.language_code IS 'ISO language code (en, zh, ja, etc.)';
COMMENT ON COLUMN content.content_group_id IS 'Groups translations together';
COMMENT ON COLUMN content.fallback_content_id IS 'Fallback content if template fails';

-- ===========================================================================
-- PART 6: Widgets table (for future widget system)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS widgets (
    id SERIAL PRIMARY KEY,
    widget_type VARCHAR(50) NOT NULL,
    widget_name VARCHAR(100) NOT NULL,

    -- Data Source
    data_source_type VARCHAR(50) DEFAULT 'internal' CHECK (data_source_type IN ('internal', 'external', 'mixed')),
    data_source_id INTEGER REFERENCES external_data_sources(id) ON DELETE SET NULL,

    -- Rendering
    template TEXT,
    styles JSONB,
    position VARCHAR(50) DEFAULT 'top-left',

    -- Behavior
    is_overlay BOOLEAN DEFAULT TRUE,
    refresh_interval INTEGER DEFAULT 300,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_widgets_type ON widgets(widget_type);
CREATE INDEX IF NOT EXISTS idx_widgets_active ON widgets(is_active);

COMMENT ON TABLE widgets IS 'Widget definitions for overlays and dynamic content';
COMMENT ON COLUMN widgets.refresh_interval IS 'Refresh interval in seconds';
COMMENT ON COLUMN widgets.is_overlay IS 'TRUE: overlay on content, FALSE: in sequence';

-- ===========================================================================
-- PART 7: Data Access Policies (Security & RBAC)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS data_access_policies (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    allowed_fields JSONB,
    denied_fields JSONB,
    conditions JSONB,
    can_read BOOLEAN DEFAULT FALSE,
    can_write BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_access_policies_role ON data_access_policies(role);
CREATE INDEX IF NOT EXISTS idx_data_access_policies_resource ON data_access_policies(resource_type);

COMMENT ON TABLE data_access_policies IS 'RBAC policies for guest data access';

-- Insert default policies
INSERT INTO data_access_policies (role, resource_type, allowed_fields, denied_fields, can_read, can_write)
VALUES
    ('admin', 'device_guest_mapping', '["*"]', '[]', TRUE, TRUE),
    ('manager', 'device_guest_mapping', '["room_number", "check_in_date", "check_out_date", "is_active"]', '["guest_name", "preferences"]', TRUE, FALSE),
    ('staff', 'device_guest_mapping', '["room_number", "is_active"]', '["guest_name", "guest_nationality", "loyalty_tier", "preferences"]', TRUE, FALSE)
ON CONFLICT DO NOTHING;

-- ===========================================================================
-- PART 8: Audit Logs (Security & Compliance)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS data_access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    guest_id VARCHAR(100),
    ip_address VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retention_days INTEGER DEFAULT 90
);

CREATE INDEX IF NOT EXISTS idx_data_access_logs_user ON data_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_timestamp ON data_access_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_guest ON data_access_logs(guest_id);

COMMENT ON TABLE data_access_logs IS 'Audit log for PII access (GDPR compliance)';
COMMENT ON COLUMN data_access_logs.retention_days IS 'Auto-delete after this many days';

-- ===========================================================================
-- PART 9: Triggers for auto-update timestamps
-- ===========================================================================

-- External Data Sources
CREATE OR REPLACE FUNCTION update_external_data_source_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_external_data_source_updated_at
BEFORE UPDATE ON external_data_sources
FOR EACH ROW
EXECUTE FUNCTION update_external_data_source_updated_at();

-- Device Guest Mappings
CREATE OR REPLACE FUNCTION update_device_guest_mapping_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_device_guest_mapping_updated_at
BEFORE UPDATE ON device_guest_mappings
FOR EACH ROW
EXECUTE FUNCTION update_device_guest_mapping_updated_at();

-- Room Configurations
CREATE OR REPLACE FUNCTION update_room_configuration_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_room_configuration_updated_at
BEFORE UPDATE ON room_configurations
FOR EACH ROW
EXECUTE FUNCTION update_room_configuration_updated_at();

-- Widgets
CREATE OR REPLACE FUNCTION update_widget_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_widget_updated_at
BEFORE UPDATE ON widgets
FOR EACH ROW
EXECUTE FUNCTION update_widget_updated_at();

-- ===========================================================================
-- PART 10: Data Cleanup Function (GDPR Compliance)
-- ===========================================================================

CREATE OR REPLACE FUNCTION cleanup_guest_data()
RETURNS void AS $$
BEGIN
    -- Soft delete guest mappings 7 days after checkout
    UPDATE device_guest_mappings
    SET
        guest_name = '[REDACTED]',
        guest_name_encrypted = NULL,
        guest_nationality = NULL,
        preferences = NULL,
        is_active = FALSE,
        deleted_at = NOW()
    WHERE
        check_out_date < NOW() - INTERVAL '7 days'
        AND deleted_at IS NULL;

    -- Hard delete after 90 days (compliance)
    DELETE FROM device_guest_mappings
    WHERE deleted_at < NOW() - INTERVAL '90 days';

    -- Cleanup audit logs older than retention policy
    DELETE FROM data_access_logs
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;

    RAISE NOTICE 'Guest data cleanup completed';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_guest_data() IS 'Auto-cleanup guest PII for GDPR compliance (run daily via cron)';

-- ===========================================================================
-- VERIFICATION QUERIES (for testing)
-- ===========================================================================

-- Uncomment to verify tables were created
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('external_data_sources', 'device_guest_mappings', 'room_configurations', 'widgets', 'data_access_policies', 'data_access_logs')
-- ORDER BY table_name;

COMMIT;
