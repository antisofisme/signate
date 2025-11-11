-- ============================================================================
-- COMPLETE DATABASE SCHEMA FOR DIGITAL SIGNAGE SYSTEM
-- Generated: 2024-11-11
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. ORGANIZATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true NOT NULL,
    max_devices INTEGER DEFAULT 10,
    max_users INTEGER DEFAULT 5,
    pin VARCHAR(8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. ROLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
    ('super_admin', 'Super Administrator', '{"all": true}'),
    ('admin', 'Administrator', '{"manage_users": true, "manage_content": true, "manage_devices": true}'),
    ('user', 'Regular User', '{"view_content": true, "manage_own_content": true}')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 3. USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20),
    role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    organization_id INTEGER REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);

-- ============================================================================
-- 4. USER SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active, expires_at);

-- ============================================================================
-- 5. DEVICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    device_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    organization_id INTEGER REFERENCES organizations(id),
    status VARCHAR(20) DEFAULT 'offline',
    last_seen TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    screen_resolution VARCHAR(20),
    orientation VARCHAR(20) DEFAULT 'landscape',
    hardware_info JSONB DEFAULT '{}',
    volume INTEGER DEFAULT 50,
    brightness INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    activation_code VARCHAR(10),
    activation_expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_devices_org ON devices(organization_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);

-- ============================================================================
-- 6. DEVICE GROUPS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_groups_org ON device_groups(organization_id);

-- ============================================================================
-- 7. DEVICE GROUP MEMBERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    added_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, device_id)
);

-- ============================================================================
-- 8. CONTENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS contents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    duration INTEGER,
    width INTEGER,
    height INTEGER,
    mime_type VARCHAR(100),
    organization_id INTEGER REFERENCES organizations(id),
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    thumbnail_path VARCHAR(500),
    anthias_asset_id VARCHAR(255),
    md5_hash VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_contents_org ON contents(organization_id);
CREATE INDEX IF NOT EXISTS idx_contents_type ON contents(content_type);
CREATE INDEX IF NOT EXISTS idx_contents_active ON contents(is_active);

-- ============================================================================
-- 9. TAGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, organization_id)
);

-- ============================================================================
-- 10. CONTENT TAGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_tags (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(content_id, tag_id)
);

-- ============================================================================
-- 11. DEVICE TAGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_tags (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, tag_id)
);

-- ============================================================================
-- 12. PLAYLISTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true NOT NULL,
    priority INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_playlists_org ON playlists(organization_id);
CREATE INDEX IF NOT EXISTS idx_playlists_active ON playlists(is_active);

-- ============================================================================
-- 13. PLAYLIST CONTENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlist_contents (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    duration_override INTEGER,
    transition_type VARCHAR(50),
    transition_duration INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_playlist_contents_playlist ON playlist_contents(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_contents_position ON playlist_contents(position);

-- ============================================================================
-- 14. PLAYLIST ASSIGNMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlist_assignments (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    device_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_assignment_target CHECK (
        (device_id IS NOT NULL)::int + 
        (device_group_id IS NOT NULL)::int + 
        (tag_id IS NOT NULL)::int = 1
    )
);

-- ============================================================================
-- 15. CONTENT ASSIGNMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_assignments (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    duration_override INTEGER,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT check_assignment_target CHECK (
        (device_id IS NOT NULL AND tag_id IS NULL) OR 
        (device_id IS NULL AND tag_id IS NOT NULL)
    )
);

-- ============================================================================
-- 16. SCHEDULES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    device_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    recurrence_type VARCHAR(20) DEFAULT 'once',
    recurrence_pattern JSONB,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedules_org ON schedules(organization_id);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_schedules_dates ON schedules(start_date, end_date);

-- ============================================================================
-- 17. DEVICE COMMANDS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_commands (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL,
    command_data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    result TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_device_commands_device ON device_commands(device_id);
CREATE INDEX IF NOT EXISTS idx_device_commands_status ON device_commands(status);

-- ============================================================================
-- 18. DEVICE HEALTH METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_health_metrics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    cpu_usage NUMERIC(5,2),
    memory_usage NUMERIC(5,2),
    disk_usage NUMERIC(5,2),
    temperature NUMERIC(5,2),
    network_latency INTEGER,
    uptime_seconds BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_health_device ON device_health_metrics(device_id);
CREATE INDEX IF NOT EXISTS idx_device_health_created ON device_health_metrics(created_at);

-- ============================================================================
-- 19. DEVICE LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_logs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_logs_device ON device_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_device_logs_timestamp ON device_logs(timestamp);

-- ============================================================================
-- 20. DEVICE SPEED TESTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_speed_tests (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    download_speed NUMERIC(10,2),
    upload_speed NUMERIC(10,2),
    ping INTEGER,
    test_server VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 21. CONTENT PLAYBACK LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_playback_logs (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    completed BOOLEAN DEFAULT false,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_playback_logs_content ON content_playback_logs(content_id);
CREATE INDEX IF NOT EXISTS idx_playback_logs_device ON content_playback_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_playback_logs_started ON content_playback_logs(started_at);

-- ============================================================================
-- 22. TEMPLATES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    template_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    preview_image VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_templates_org ON templates(organization_id);

-- ============================================================================
-- 23. TRANSLATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    key VARCHAR(255) NOT NULL,
    language VARCHAR(10) NOT NULL,
    value TEXT NOT NULL,
    context VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, key, language)
);

CREATE INDEX IF NOT EXISTS idx_translations_org_lang ON translations(organization_id, language);

-- ============================================================================
-- 24. WIDGETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS widgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    widget_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_widgets_org ON widgets(organization_id);

-- ============================================================================
-- 25. PLAYLIST WIDGETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlist_widgets (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    widget_id INTEGER NOT NULL REFERENCES widgets(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    duration INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 26. PMS CONFIGURATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS pms_configurations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    pms_type VARCHAR(50) NOT NULL,
    connection_string TEXT NOT NULL,
    sync_interval INTEGER DEFAULT 300,
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 27. PMS ROOMS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS pms_rooms (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    room_number VARCHAR(50) NOT NULL,
    room_type VARCHAR(50),
    floor INTEGER,
    building VARCHAR(50),
    status VARCHAR(20),
    device_id INTEGER REFERENCES devices(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, room_number)
);

-- ============================================================================
-- 28. PMS GUESTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS pms_guests (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    room_id INTEGER REFERENCES pms_rooms(id),
    guest_name VARCHAR(255),
    guest_title VARCHAR(50),
    company VARCHAR(255),
    nationality VARCHAR(50),
    language VARCHAR(10),
    check_in_date DATE,
    check_out_date DATE,
    vip_status BOOLEAN DEFAULT false,
    special_requests TEXT,
    pms_guest_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pms_guests_room ON pms_guests(room_id);
CREATE INDEX IF NOT EXISTS idx_pms_guests_dates ON pms_guests(check_in_date, check_out_date);

-- ============================================================================
-- 29. AUDIT LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    organization_id INTEGER REFERENCES organizations(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================================
-- UPDATE TRIGGERS FOR TIMESTAMPS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all tables with updated_at column
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at 
            BEFORE UPDATE ON %I 
            FOR EACH ROW 
            EXECUTE PROCEDURE update_updated_at_column();
        ', t, t);
    END LOOP;
END $$;