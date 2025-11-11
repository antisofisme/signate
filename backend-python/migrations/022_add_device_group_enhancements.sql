-- ============================================================================
-- 022_add_device_group_enhancements.sql
-- Add device group hierarchy and stats tables
-- ============================================================================

-- Device group hierarchy for nested groups
CREATE TABLE IF NOT EXISTS device_group_hierarchy (
    id SERIAL PRIMARY KEY,
    parent_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE,
    child_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_group_id, child_group_id)
);

-- Device group statistics
CREATE TABLE IF NOT EXISTS device_group_stats (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,
    total_devices INTEGER DEFAULT 0,
    online_devices INTEGER DEFAULT 0,
    offline_devices INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id)
);