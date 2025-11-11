-- ============================================================================
-- Migration 017: Add Device Groups (Hierarchical Organization)
-- Description: Hierarchical device grouping for large-scale deployments
-- Created: 2025-01-09
-- Priority: MEDIUM
-- ============================================================================

BEGIN;

-- ============================================================================
-- USE CASE & BENEFITS
-- ============================================================================
-- Problem: In large hotels/chains, managing hundreds of devices individually is hard
-- Solution: Hierarchical groups (e.g., Floor 1 > Lobby > Screens)
--
-- Benefits:
-- 1. Bulk operations: Assign content/playlists to entire groups
-- 2. Hierarchy: Groups can have parent groups (unlimited depth)
-- 3. Analytics: Group-level performance metrics
-- 4. Management: Easier organization for large deployments
--
-- Example hierarchy:
-- Hotel Chain
-- └── Hotel A
--     ├── Floor 1
--     │   ├── Lobby
--     │   │   ├── Device 001
--     │   │   └── Device 002
--     │   └── Restaurant
--     │       ├── Device 003
--     │       └── Device 004
--     └── Floor 2
--         └── Gym
--             ├── Device 005
--             └── Device 006
-- ============================================================================

-- ============================================================================
-- 1. CREATE DEVICE_GROUPS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_groups (
    -- Identity
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),

    -- Hierarchy (self-referencing)
    parent_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE,

    -- Multi-tenant
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Metadata
    group_type VARCHAR(50), -- 'chain', 'hotel', 'floor', 'location', 'custom'
    sort_order INTEGER DEFAULT 0,

    -- Settings (inherited by child groups if NULL)
    default_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,

    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT unique_group_name_per_org UNIQUE (organization_id, name, deleted_at)
);

-- ============================================================================
-- 2. CREATE DEVICE_GROUP_MEMBERS TABLE (Many-to-Many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_group_members (
    -- Identity
    id SERIAL PRIMARY KEY,

    -- Relations
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,

    -- Membership metadata
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    added_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT unique_device_per_group UNIQUE (device_id, group_id)
);

-- ============================================================================
-- 3. CREATE INDEXES
-- ============================================================================

-- Device Groups
CREATE INDEX idx_device_groups_org ON device_groups(organization_id, deleted_at);
CREATE INDEX idx_device_groups_parent ON device_groups(parent_group_id) WHERE parent_group_id IS NOT NULL;
CREATE INDEX idx_device_groups_type ON device_groups(organization_id, group_type) WHERE deleted_at IS NULL;

-- Device Group Members
CREATE INDEX idx_device_group_members_device ON device_group_members(device_id);
CREATE INDEX idx_device_group_members_group ON device_group_members(group_id);

-- ============================================================================
-- 4. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function: Get all child groups recursively (including self)
CREATE OR REPLACE FUNCTION get_child_groups(p_group_id INTEGER)
RETURNS TABLE (group_id INTEGER, depth INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE group_tree AS (
        -- Base case: the group itself
        SELECT id, 0 as depth
        FROM device_groups
        WHERE id = p_group_id

        UNION ALL

        -- Recursive case: child groups
        SELECT dg.id, gt.depth + 1
        FROM device_groups dg
        INNER JOIN group_tree gt ON dg.parent_group_id = gt.id
        WHERE dg.deleted_at IS NULL
    )
    SELECT id, depth FROM group_tree;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_child_groups(INTEGER) IS
    'Returns all child groups recursively (including the group itself)';

-- Function: Get all devices in a group (including child groups)
CREATE OR REPLACE FUNCTION get_devices_in_group(p_group_id INTEGER)
RETURNS TABLE (device_id INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT dgm.device_id
    FROM device_group_members dgm
    WHERE dgm.group_id IN (
        SELECT group_id FROM get_child_groups(p_group_id)
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_devices_in_group(INTEGER) IS
    'Returns all devices in a group and its child groups';

-- Function: Get group path (breadcrumb trail)
CREATE OR REPLACE FUNCTION get_group_path(p_group_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    v_path TEXT;
BEGIN
    WITH RECURSIVE group_path AS (
        -- Base case: the group itself
        SELECT id, name, parent_group_id, ARRAY[name] as path
        FROM device_groups
        WHERE id = p_group_id

        UNION ALL

        -- Recursive case: parent groups
        SELECT dg.id, dg.name, dg.parent_group_id, dg.name || gp.path
        FROM device_groups dg
        INNER JOIN group_path gp ON gp.parent_group_id = dg.id
    )
    SELECT array_to_string(path, ' > ')
    INTO v_path
    FROM group_path
    WHERE parent_group_id IS NULL;

    RETURN v_path;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_group_path(INTEGER) IS
    'Returns breadcrumb path: "Hotel A > Floor 1 > Lobby"';

-- ============================================================================
-- 5. CREATE ANALYTICS VIEWS
-- ============================================================================

-- View: Group device statistics
CREATE OR REPLACE VIEW device_group_stats AS
SELECT
    dg.id as group_id,
    dg.name as group_name,
    dg.organization_id,
    count(DISTINCT dgm.device_id) as total_devices,
    count(DISTINCT dgm.device_id) FILTER (WHERE d.status = 'online') as online_devices,
    count(DISTINCT dgm.device_id) FILTER (WHERE d.status = 'offline') as offline_devices
FROM device_groups dg
LEFT JOIN device_group_members dgm ON dgm.group_id = dg.id
LEFT JOIN devices d ON d.id = dgm.device_id
WHERE dg.deleted_at IS NULL
GROUP BY dg.id, dg.name, dg.organization_id;

COMMENT ON VIEW device_group_stats IS
    'Device count and status per group';

-- View: Group hierarchy visualization
CREATE OR REPLACE VIEW device_group_hierarchy AS
SELECT
    dg.id,
    dg.name,
    dg.group_type,
    dg.parent_group_id,
    pg.name as parent_name,
    get_group_path(dg.id) as full_path,
    count(dgm.device_id) as direct_devices
FROM device_groups dg
LEFT JOIN device_groups pg ON pg.id = dg.parent_group_id
LEFT JOIN device_group_members dgm ON dgm.group_id = dg.id
WHERE dg.deleted_at IS NULL
GROUP BY dg.id, dg.name, dg.group_type, dg.parent_group_id, pg.name;

COMMENT ON VIEW device_group_hierarchy IS
    'Hierarchical view of all device groups with breadcrumb paths';

-- ============================================================================
-- 6. ADD RLS POLICIES (if Migration 016 was run)
-- ============================================================================

-- Enable RLS on new tables
ALTER TABLE device_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_group_members ENABLE ROW LEVEL SECURITY;

-- Device Groups: organization isolation
CREATE POLICY device_groups_isolation ON device_groups
    FOR ALL
    USING (
        EXISTS (SELECT 1 FROM current_setting('app.is_super_admin', true) WHERE current_setting('app.is_super_admin', true)::BOOLEAN = TRUE)
        OR organization_id = current_setting('app.current_organization_id', true)::INTEGER
    );

-- Device Group Members: inherit from device_groups
CREATE POLICY device_group_members_isolation ON device_group_members
    FOR ALL
    USING (
        EXISTS (SELECT 1 FROM current_setting('app.is_super_admin', true) WHERE current_setting('app.is_super_admin', true)::BOOLEAN = TRUE)
        OR EXISTS (
            SELECT 1 FROM device_groups
            WHERE device_groups.id = device_group_members.group_id
              AND device_groups.organization_id = current_setting('app.current_organization_id', true)::INTEGER
        )
    );

COMMENT ON POLICY device_groups_isolation ON device_groups IS
    'Multi-tenant isolation for device groups';

-- ============================================================================
-- 7. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE device_groups IS 'Hierarchical device groups for large-scale deployments';
COMMENT ON TABLE device_group_members IS 'Many-to-many: devices can belong to multiple groups';

COMMENT ON COLUMN device_groups.parent_group_id IS 'Self-referencing: allows unlimited depth hierarchy';
COMMENT ON COLUMN device_groups.group_type IS 'Suggested types: chain, hotel, floor, location, custom';
COMMENT ON COLUMN device_groups.default_playlist_id IS 'Playlist inherited by child groups (if NULL, check parent)';
COMMENT ON COLUMN device_group_members.added_by IS 'User who added device to this group';

-- ============================================================================
-- 8. VERIFICATION QUERIES
-- ============================================================================

-- Verify tables created
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('device_groups', 'device_group_members')
ORDER BY table_name;

-- Verify functions created
SELECT proname
FROM pg_proc
WHERE proname IN ('get_child_groups', 'get_devices_in_group', 'get_group_path');

-- Verify views created
SELECT table_name
FROM information_schema.views
WHERE table_name IN ('device_group_stats', 'device_group_hierarchy');

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;

-- Drop RLS policies
DROP POLICY IF EXISTS device_groups_isolation ON device_groups;
DROP POLICY IF EXISTS device_group_members_isolation ON device_group_members;

-- Drop views
DROP VIEW IF EXISTS device_group_stats;
DROP VIEW IF EXISTS device_group_hierarchy;

-- Drop functions
DROP FUNCTION IF EXISTS get_child_groups(INTEGER);
DROP FUNCTION IF EXISTS get_devices_in_group(INTEGER);
DROP FUNCTION IF EXISTS get_group_path(INTEGER);

-- Drop indexes
DROP INDEX IF EXISTS idx_device_groups_org;
DROP INDEX IF EXISTS idx_device_groups_parent;
DROP INDEX IF EXISTS idx_device_groups_type;
DROP INDEX IF EXISTS idx_device_group_members_device;
DROP INDEX IF EXISTS idx_device_group_members_group;

-- Drop tables
DROP TABLE IF EXISTS device_group_members;
DROP TABLE IF EXISTS device_groups;

COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Create group hierarchy
/*
-- 1. Create root group
INSERT INTO device_groups (name, organization_id, group_type)
VALUES ('Hotel A', 1, 'hotel') RETURNING id;  -- Returns 100

-- 2. Create child groups
INSERT INTO device_groups (name, parent_group_id, organization_id, group_type)
VALUES
    ('Floor 1', 100, 1, 'floor'),
    ('Floor 2', 100, 1, 'floor');

-- 3. Create location groups
INSERT INTO device_groups (name, parent_group_id, organization_id, group_type)
VALUES ('Lobby', 101, 1, 'location');

-- 4. Add devices to group
INSERT INTO device_group_members (device_id, group_id, added_by)
VALUES
    (1, 103, 1),
    (2, 103, 1);

-- 5. Get all devices in "Floor 1" (including child groups)
SELECT * FROM get_devices_in_group(101);

-- 6. Get group path
SELECT get_group_path(103);  -- Returns: "Hotel A > Floor 1 > Lobby"

-- 7. Get group statistics
SELECT * FROM device_group_stats WHERE group_id = 101;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/017_add_device_groups.sql
