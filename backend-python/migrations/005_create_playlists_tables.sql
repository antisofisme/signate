-- Migration 005: Create Playlist Tables
-- Created: 2025-01-07
-- Description: Playlists, playlist contents, and device/tag assignments with multi-tenancy

-- ============================================================================
-- 1. PLAYLISTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    priority INTEGER DEFAULT 0 NOT NULL,
    schedule JSONB,  -- Flexible schedule configuration

    -- Multi-tenancy & User tracking
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT unique_playlist_name_per_org UNIQUE (organization_id, name, deleted_at)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_playlists_organization ON playlists(organization_id);
CREATE INDEX IF NOT EXISTS idx_playlists_created_by ON playlists(created_by);
CREATE INDEX IF NOT EXISTS idx_playlists_is_active ON playlists(is_active);
CREATE INDEX IF NOT EXISTS idx_playlists_deleted_at ON playlists(deleted_at);

-- ============================================================================
-- 2. PLAYLIST_CONTENTS TABLE (Junction table for playlists + contents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlist_contents (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,

    -- Order and duration override
    order_index INTEGER NOT NULL DEFAULT 0,
    duration INTEGER,  -- Override content's default duration (in seconds)

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints: prevent duplicate content in same playlist
    CONSTRAINT unique_playlist_content UNIQUE (playlist_id, content_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_playlist_contents_playlist ON playlist_contents(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_contents_content ON playlist_contents(content_id);
CREATE INDEX IF NOT EXISTS idx_playlist_contents_order ON playlist_contents(playlist_id, order_index);

-- ============================================================================
-- 3. PLAYLIST_ASSIGNMENTS TABLE (Polymorphic: device OR tag)
-- ============================================================================
CREATE TABLE IF NOT EXISTS playlist_assignments (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,

    -- Polymorphic assignment (one of these must be set)
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints: must assign to either device OR tag, not both
    CONSTRAINT check_assignment_type CHECK (
        (device_id IS NOT NULL AND tag_id IS NULL) OR
        (device_id IS NULL AND tag_id IS NOT NULL)
    ),

    -- Prevent duplicate assignments
    CONSTRAINT unique_playlist_device UNIQUE (playlist_id, device_id),
    CONSTRAINT unique_playlist_tag UNIQUE (playlist_id, tag_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_playlist ON playlist_assignments(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_device ON playlist_assignments(device_id);
CREATE INDEX IF NOT EXISTS idx_playlist_assignments_tag ON playlist_assignments(tag_id);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE playlists IS 'Playlists for organizing content playback with multi-tenant support';
COMMENT ON COLUMN playlists.schedule IS 'JSONB schedule configuration (days, time ranges, etc.)';
COMMENT ON COLUMN playlists.organization_id IS 'Multi-tenant: isolates playlists by organization';
COMMENT ON COLUMN playlists.created_by IS 'User who created the playlist';
COMMENT ON COLUMN playlists.priority IS 'Playlist priority for conflict resolution (higher = more priority)';

COMMENT ON TABLE playlist_contents IS 'Junction table: many-to-many relationship between playlists and contents';
COMMENT ON COLUMN playlist_contents.order_index IS 'Display order in playlist (0-based)';
COMMENT ON COLUMN playlist_contents.duration IS 'Override content duration for this playlist (optional)';

COMMENT ON TABLE playlist_assignments IS 'Polymorphic assignments: playlist can be assigned to devices OR tags';
COMMENT ON CONSTRAINT check_assignment_type ON playlist_assignments IS 'Ensures assignment is to device OR tag, not both';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables created
SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('playlists', 'playlist_contents', 'playlist_assignments')
ORDER BY table_name;

-- Verify indexes created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('playlists', 'playlist_contents', 'playlist_assignments')
ORDER BY tablename, indexname;
