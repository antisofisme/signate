-- ============================================================================
-- 012_add_device_groups.sql
-- Add device groups and device group members tables
-- ============================================================================

-- Device groups table
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

-- Device group members table
CREATE TABLE IF NOT EXISTS device_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    added_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, device_id)
);

-- Add device_group_id to schedules table
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS device_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE;

-- Add device_group_id to playlist_assignments table
ALTER TABLE playlist_assignments ADD COLUMN IF NOT EXISTS device_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE;