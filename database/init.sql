-- =============================================================================
-- SMART TV DIGITAL SIGNAGE - DATABASE SCHEMA
-- =============================================================================
-- PostgreSQL 15+
-- Created: October 21, 2025
-- =============================================================================

-- Drop tables if exists (for clean reinstall)
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS content_assignments CASCADE;
DROP TABLE IF EXISTS device_tags CASCADE;
DROP TABLE IF EXISTS firebird_config CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS content CASCADE;
DROP TABLE IF EXISTS devices CASCADE;

-- Enable UUID extension (for unique codes)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE: devices
-- Purpose: Registry untuk TV & Monitor devices
-- =============================================================================
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('tv', 'monitor')),
    device_name VARCHAR(100) NOT NULL,

    -- For TV: IP address & passphrase (pairing)
    ip_address VARCHAR(45), -- IPv4 or IPv6
    passphrase VARCHAR(50),  -- 6-digit code dari Developer Mode

    -- For Monitor: unique activation code
    unique_code VARCHAR(20) UNIQUE, -- 6-digit activation code
    code_expires_at TIMESTAMP, -- Code expiry (10 minutes)

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'inactive')),
    last_seen TIMESTAMP, -- Last heartbeat timestamp

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT device_tv_requires_ip_passphrase
        CHECK (device_type != 'tv' OR (ip_address IS NOT NULL AND passphrase IS NOT NULL)),
    CONSTRAINT device_monitor_requires_code
        CHECK (device_type != 'monitor' OR unique_code IS NOT NULL)
);

-- Indexes for devices
CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_ip_address ON devices(ip_address);
CREATE INDEX idx_devices_unique_code ON devices(unique_code);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);

COMMENT ON TABLE devices IS 'Registry TV dan Monitor devices';
COMMENT ON COLUMN devices.device_type IS 'tv atau monitor';
COMMENT ON COLUMN devices.ip_address IS 'IP address untuk TV (pairing dengan passphrase)';
COMMENT ON COLUMN devices.passphrase IS '6-digit code dari WebOS Developer Mode';
COMMENT ON COLUMN devices.unique_code IS 'Activation code untuk Monitor (generated)';
COMMENT ON COLUMN devices.status IS 'pending (belum connect), active, inactive';
COMMENT ON COLUMN devices.last_seen IS 'Timestamp terakhir heartbeat dari device';

-- =============================================================================
-- TABLE: content
-- Purpose: Metadata konten (image/video) - FILE DISIMPAN DI ANTHIAS!
-- =============================================================================
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Content type
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('image', 'video')),

    -- IMPORTANT: anthias_url berisi URL ke Anthias, BUKAN file binary!
    -- Example: http://192.168.5.12:8000/asset/abc123.jpg
    anthias_url VARCHAR(500) NOT NULL,
    anthias_asset_id VARCHAR(100), -- Asset ID dari Anthias (untuk delete)

    -- Display duration (seconds)
    duration INTEGER NOT NULL DEFAULT 10 CHECK (duration > 0),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    file_size BIGINT, -- File size in bytes (optional)
    mime_type VARCHAR(100), -- image/jpeg, video/mp4, etc.

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for content
CREATE INDEX idx_content_type ON content(content_type);
CREATE INDEX idx_content_is_active ON content(is_active);
CREATE INDEX idx_content_anthias_asset_id ON content(anthias_asset_id);

COMMENT ON TABLE content IS 'Metadata konten - FILE ASLI DISIMPAN DI ANTHIAS';
COMMENT ON COLUMN content.anthias_url IS 'URL ke asset di Anthias (bukan file binary!)';
COMMENT ON COLUMN content.anthias_asset_id IS 'Asset ID dari Anthias untuk delete/update';
COMMENT ON COLUMN content.duration IS 'Durasi display dalam detik';

-- =============================================================================
-- TABLE: tags
-- Purpose: Groups/categories untuk devices (untuk assign content ke banyak device)
-- =============================================================================
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for tags
CREATE INDEX idx_tags_name ON tags(tag_name);

COMMENT ON TABLE tags IS 'Groups/tags untuk grouping devices';
COMMENT ON COLUMN tags.tag_name IS 'Nama tag (unique), contoh: "Lobby", "Restaurant", "Room"';

-- =============================================================================
-- TABLE: device_tags (Many-to-Many)
-- Purpose: Relationship antara devices dan tags
-- =============================================================================
CREATE TABLE device_tags (
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (device_id, tag_id)
);

-- Indexes for device_tags
CREATE INDEX idx_device_tags_device_id ON device_tags(device_id);
CREATE INDEX idx_device_tags_tag_id ON device_tags(tag_id);

COMMENT ON TABLE device_tags IS 'Many-to-many relationship: devices <-> tags';

-- =============================================================================
-- TABLE: content_assignments
-- Purpose: Assign content ke device atau tag
-- =============================================================================
CREATE TABLE content_assignments (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,

    -- Assign ke device OR tag (salah satu, tidak boleh keduanya)
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    -- Priority untuk sorting playlist
    priority INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: harus assign ke device ATAU tag (tidak boleh keduanya atau kosong)
    CONSTRAINT assignment_target_check
        CHECK (
            (device_id IS NOT NULL AND tag_id IS NULL) OR
            (device_id IS NULL AND tag_id IS NOT NULL)
        )
);

-- Indexes for content_assignments
CREATE INDEX idx_assignments_content_id ON content_assignments(content_id);
CREATE INDEX idx_assignments_device_id ON content_assignments(device_id);
CREATE INDEX idx_assignments_tag_id ON content_assignments(tag_id);
CREATE INDEX idx_assignments_priority ON content_assignments(priority);

COMMENT ON TABLE content_assignments IS 'Assignment content ke device atau tag';
COMMENT ON COLUMN content_assignments.device_id IS 'Assign ke specific device (null jika assign ke tag)';
COMMENT ON COLUMN content_assignments.tag_id IS 'Assign ke tag (semua device di tag ini, null jika assign ke device)';
COMMENT ON COLUMN content_assignments.priority IS 'Priority untuk sorting playlist (higher = first)';

-- =============================================================================
-- TABLE: schedules
-- Purpose: Time-based scheduling untuk content
-- =============================================================================
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,

    -- Schedule untuk device OR tag
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    -- Time schedule
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    -- Days of week (1=Monday, 7=Sunday)
    -- Stored as JSON array: [1,2,3,4,5] untuk weekdays
    days_of_week JSONB NOT NULL DEFAULT '[]',

    -- Date range
    start_date DATE NOT NULL,
    end_date DATE, -- NULL = indefinite

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: harus schedule untuk device ATAU tag
    CONSTRAINT schedule_target_check
        CHECK (
            (device_id IS NOT NULL AND tag_id IS NULL) OR
            (device_id IS NULL AND tag_id IS NOT NULL)
        ),

    -- Constraint: end_time harus setelah start_time
    CONSTRAINT schedule_time_check CHECK (end_time > start_time)
);

-- Indexes for schedules
CREATE INDEX idx_schedules_content_id ON schedules(content_id);
CREATE INDEX idx_schedules_device_id ON schedules(device_id);
CREATE INDEX idx_schedules_tag_id ON schedules(tag_id);
CREATE INDEX idx_schedules_is_active ON schedules(is_active);
CREATE INDEX idx_schedules_start_date ON schedules(start_date);
CREATE INDEX idx_schedules_end_date ON schedules(end_date);
CREATE INDEX idx_schedules_days_of_week ON schedules USING gin(days_of_week);

COMMENT ON TABLE schedules IS 'Time-based scheduling untuk content';
COMMENT ON COLUMN schedules.days_of_week IS 'JSON array hari dalam seminggu [1-7], 1=Monday';
COMMENT ON COLUMN schedules.start_date IS 'Tanggal mulai schedule';
COMMENT ON COLUMN schedules.end_date IS 'Tanggal akhir (NULL = indefinite)';

-- =============================================================================
-- TABLE: users
-- Purpose: Admin accounts untuk Web Admin
-- =============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    email VARCHAR(100) NOT NULL UNIQUE,

    -- Role-based access
    role VARCHAR(20) NOT NULL DEFAULT 'viewer'
        CHECK (role IN ('admin', 'editor', 'viewer')),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Indexes for users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

COMMENT ON TABLE users IS 'Admin user accounts untuk Web Admin';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hash dari password';
COMMENT ON COLUMN users.role IS 'admin (full access), editor (manage content), viewer (read only)';

-- =============================================================================
-- TABLE: firebird_config
-- Purpose: Configuration untuk Firebird API (external hotel guest data)
-- =============================================================================
CREATE TABLE firebird_config (
    id SERIAL PRIMARY KEY,
    api_endpoint VARCHAR(500) NOT NULL,

    -- API key (encrypted di application layer sebelum save)
    api_key TEXT NOT NULL,

    -- Refresh interval (seconds)
    refresh_interval INTEGER DEFAULT 300 CHECK (refresh_interval > 0),

    -- Query parameters (JSON)
    -- Example: {"status": "checked_in", "limit": 100}
    query_params JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Last fetch
    last_fetched_at TIMESTAMP,
    last_fetch_status VARCHAR(20), -- success, error
    last_fetch_error TEXT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for firebird_config
CREATE INDEX idx_firebird_is_active ON firebird_config(is_active);

COMMENT ON TABLE firebird_config IS 'Configuration Firebird API untuk data tamu hotel';
COMMENT ON COLUMN firebird_config.api_key IS 'API key (encrypted di app layer)';
COMMENT ON COLUMN firebird_config.refresh_interval IS 'Interval fetch data (seconds)';
COMMENT ON COLUMN firebird_config.query_params IS 'Query parameters sebagai JSON';

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Insert default admin user
-- Password: admin123 (hashed with bcrypt)
-- IMPORTANT: Ganti password ini di production!
INSERT INTO users (username, password_hash, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyJpVO7v0ZbG', 'admin@signage.local', 'admin');

-- Insert sample tags
INSERT INTO tags (tag_name, description) VALUES
('Lobby', 'TV/Monitor di area lobby'),
('Restaurant', 'TV/Monitor di restaurant'),
('Room', 'TV di kamar hotel'),
('Meeting Room', 'TV di meeting room');

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

-- Trigger: Auto update updated_at on devices
CREATE TRIGGER update_devices_updated_at
    BEFORE UPDATE ON devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto update updated_at on content
CREATE TRIGGER update_content_updated_at
    BEFORE UPDATE ON content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto update updated_at on firebird_config
CREATE TRIGGER update_firebird_config_updated_at
    BEFORE UPDATE ON firebird_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS (Optional - untuk query convenience)
-- =============================================================================

-- View: Active devices dengan tag info
CREATE OR REPLACE VIEW v_devices_with_tags AS
SELECT
    d.id,
    d.device_type,
    d.device_name,
    d.ip_address,
    d.status,
    d.last_seen,
    COALESCE(
        JSON_AGG(
            JSON_BUILD_OBJECT('tag_id', t.id, 'tag_name', t.tag_name)
        ) FILTER (WHERE t.id IS NOT NULL),
        '[]'::json
    ) AS tags
FROM devices d
LEFT JOIN device_tags dt ON d.id = dt.device_id
LEFT JOIN tags t ON dt.tag_id = t.id
GROUP BY d.id, d.device_type, d.device_name, d.ip_address, d.status, d.last_seen;

COMMENT ON VIEW v_devices_with_tags IS 'Devices dengan list tags (JSON aggregation)';

-- View: Content dengan assignment info
CREATE OR REPLACE VIEW v_content_with_assignments AS
SELECT
    c.id,
    c.title,
    c.content_type,
    c.anthias_url,
    c.duration,
    c.is_active,
    COUNT(DISTINCT ca.device_id) AS assigned_devices_count,
    COUNT(DISTINCT ca.tag_id) AS assigned_tags_count
FROM content c
LEFT JOIN content_assignments ca ON c.id = ca.content_id
GROUP BY c.id, c.title, c.content_type, c.anthias_url, c.duration, c.is_active;

COMMENT ON VIEW v_content_with_assignments IS 'Content dengan jumlah assignments ke devices/tags';

-- =============================================================================
-- GRANT PERMISSIONS (untuk production)
-- =============================================================================

-- Uncomment untuk production dengan dedicated database user:
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO signage_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO signage_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO signage_user;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check all tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check admin user seeded
SELECT id, username, email, role, is_active, created_at
FROM users
WHERE role = 'admin';

-- Check tags seeded
SELECT id, tag_name, description
FROM tags;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
