-- ============================================================================
-- Migration 018: Add Content Versions (Version Control & Rollback)
-- Description: Track content changes and enable rollback to previous versions
-- Created: 2025-01-09
-- Priority: MEDIUM
-- ============================================================================

BEGIN;

-- ============================================================================
-- USE CASE & BENEFITS
-- ============================================================================
-- Problem: Content gets updated/replaced, no way to undo or see history
-- Solution: Version control for content metadata + file references
--
-- Benefits:
-- 1. Rollback: Restore previous versions if update goes wrong
-- 2. Audit trail: See all changes made to content
-- 3. A/B testing: Compare performance of different versions
-- 4. Compliance: Regulatory requirement to track content changes
--
-- Note: This tracks METADATA versions, not physical file copies (storage cost)
-- Physical files are only versioned if storage_key changes
-- ============================================================================

-- ============================================================================
-- 1. CREATE CONTENT_VERSIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_versions (
    -- Identity
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,

    -- Version tracking
    version_number INTEGER NOT NULL,
    is_current BOOLEAN DEFAULT FALSE NOT NULL,

    -- Snapshot of content metadata at this version
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL,

    -- File reference (may be same across versions if file unchanged)
    storage_key VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    duration INTEGER, -- seconds

    -- Display metadata snapshot
    thumbnail_url VARCHAR(500),
    width INTEGER,
    height INTEGER,

    -- Change tracking
    change_type VARCHAR(20) NOT NULL, -- 'created', 'updated', 'replaced', 'reverted'
    change_summary VARCHAR(500), -- Human-readable change description

    -- Audit
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT unique_content_version UNIQUE (content_id, version_number),
    CONSTRAINT check_version_number CHECK (version_number > 0)
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

-- Content version history
CREATE INDEX idx_content_versions_content ON content_versions(content_id, version_number DESC);

-- Current version lookup
CREATE INDEX idx_content_versions_current ON content_versions(content_id, is_current)
    WHERE is_current = TRUE;

-- Version audit trail
CREATE INDEX idx_content_versions_created ON content_versions(content_id, created_at DESC);

-- Change type analysis
CREATE INDEX idx_content_versions_change_type ON content_versions(change_type, created_at DESC);

-- Creator audit
CREATE INDEX idx_content_versions_creator ON content_versions(created_by, created_at DESC);

-- ============================================================================
-- 3. CREATE TRIGGER TO AUTO-VERSION CONTENT CHANGES
-- ============================================================================

-- Function: Create new version on content update
CREATE OR REPLACE FUNCTION create_content_version()
RETURNS TRIGGER AS $$
DECLARE
    v_next_version INTEGER;
    v_change_type VARCHAR(20);
BEGIN
    -- Determine change type
    IF TG_OP = 'INSERT' THEN
        v_next_version := 1;
        v_change_type := 'created';
    ELSE
        -- Get next version number
        SELECT COALESCE(MAX(version_number), 0) + 1
        INTO v_next_version
        FROM content_versions
        WHERE content_id = NEW.id;

        -- Determine change type based on what changed
        IF OLD.storage_key != NEW.storage_key THEN
            v_change_type := 'replaced';
        ELSE
            v_change_type := 'updated';
        END IF;

        -- Mark old version as not current
        UPDATE content_versions
        SET is_current = FALSE
        WHERE content_id = NEW.id AND is_current = TRUE;
    END IF;

    -- Create new version snapshot
    INSERT INTO content_versions (
        content_id,
        version_number,
        is_current,
        title,
        description,
        content_type,
        storage_key,
        file_size,
        mime_type,
        duration,
        thumbnail_url,
        width,
        height,
        change_type,
        created_by,
        created_at
    ) VALUES (
        NEW.id,
        v_next_version,
        TRUE,
        NEW.title,
        NEW.description,
        NEW.content_type,
        NEW.storage_key,
        NEW.file_size,
        NEW.mime_type,
        NEW.duration,
        NEW.thumbnail_url,
        NEW.width,
        NEW.height,
        v_change_type,
        NEW.updated_by,  -- Assuming updated_by exists on contents table
        NOW()
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-create version on INSERT/UPDATE
CREATE TRIGGER trigger_content_version
    AFTER INSERT OR UPDATE ON contents
    FOR EACH ROW
    WHEN (pg_trigger_depth() = 0)  -- Prevent recursion
    EXECUTE FUNCTION create_content_version();

COMMENT ON TRIGGER trigger_content_version ON contents IS
    'Automatically creates content version on INSERT/UPDATE';

-- ============================================================================
-- 4. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function: Revert content to specific version
CREATE OR REPLACE FUNCTION revert_to_version(
    p_content_id INTEGER,
    p_version_number INTEGER,
    p_reverted_by INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_version RECORD;
BEGIN
    -- Get the version to revert to
    SELECT *
    INTO v_version
    FROM content_versions
    WHERE content_id = p_content_id
      AND version_number = p_version_number;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Version % not found for content %', p_version_number, p_content_id;
    END IF;

    -- Update content table with version data
    UPDATE contents
    SET
        title = v_version.title,
        description = v_version.description,
        content_type = v_version.content_type,
        storage_key = v_version.storage_key,
        file_size = v_version.file_size,
        mime_type = v_version.mime_type,
        duration = v_version.duration,
        thumbnail_url = v_version.thumbnail_url,
        width = v_version.width,
        height = v_version.height,
        updated_by = p_reverted_by,
        updated_at = NOW()
    WHERE id = p_content_id;

    -- Mark reverted version as current (trigger will create new version with change_type='reverted')
    UPDATE content_versions
    SET is_current = FALSE
    WHERE content_id = p_content_id AND is_current = TRUE;

    UPDATE content_versions
    SET
        is_current = TRUE,
        change_type = 'reverted'
    WHERE content_id = p_content_id
      AND version_number = p_version_number;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION revert_to_version(INTEGER, INTEGER, INTEGER) IS
    'Reverts content to a specific version number';

-- Function: Get version diff (show what changed)
CREATE OR REPLACE FUNCTION get_version_diff(
    p_content_id INTEGER,
    p_from_version INTEGER,
    p_to_version INTEGER
)
RETURNS TABLE (
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    changed BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH v_from AS (
        SELECT * FROM content_versions
        WHERE content_id = p_content_id AND version_number = p_from_version
    ),
    v_to AS (
        SELECT * FROM content_versions
        WHERE content_id = p_content_id AND version_number = p_to_version
    )
    SELECT
        'title'::TEXT as field_name,
        v_from.title::TEXT as old_value,
        v_to.title::TEXT as new_value,
        (v_from.title != v_to.title) as changed
    FROM v_from, v_to
    UNION ALL
    SELECT
        'storage_key'::TEXT,
        v_from.storage_key::TEXT,
        v_to.storage_key::TEXT,
        (v_from.storage_key != v_to.storage_key)
    FROM v_from, v_to
    UNION ALL
    SELECT
        'file_size'::TEXT,
        v_from.file_size::TEXT,
        v_to.file_size::TEXT,
        (COALESCE(v_from.file_size, 0) != COALESCE(v_to.file_size, 0))
    FROM v_from, v_to;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_version_diff(INTEGER, INTEGER, INTEGER) IS
    'Shows what changed between two versions';

-- ============================================================================
-- 5. CREATE ANALYTICS VIEWS
-- ============================================================================

-- View: Content version history with change summary
CREATE OR REPLACE VIEW content_version_history AS
SELECT
    cv.id,
    cv.content_id,
    c.title as current_title,
    cv.version_number,
    cv.is_current,
    cv.title as version_title,
    cv.change_type,
    cv.change_summary,
    cv.storage_key,
    u.username as changed_by,
    cv.created_at as changed_at,
    LAG(cv.version_number) OVER (PARTITION BY cv.content_id ORDER BY cv.version_number) as previous_version
FROM content_versions cv
LEFT JOIN contents c ON c.id = cv.content_id
LEFT JOIN users u ON u.id = cv.created_by
ORDER BY cv.content_id, cv.version_number DESC;

COMMENT ON VIEW content_version_history IS
    'Complete version history with change tracking';

-- View: Recent content changes
CREATE OR REPLACE VIEW recent_content_changes AS
SELECT
    cv.content_id,
    c.title,
    c.organization_id,
    cv.version_number,
    cv.change_type,
    u.username as changed_by,
    cv.created_at as changed_at
FROM content_versions cv
JOIN contents c ON c.id = cv.content_id
LEFT JOIN users u ON u.id = cv.created_by
WHERE cv.created_at > NOW() - INTERVAL '30 days'
ORDER BY cv.created_at DESC;

COMMENT ON VIEW recent_content_changes IS
    'Content changes in the last 30 days';

-- ============================================================================
-- 6. ADD RLS POLICIES (if Migration 016 was run)
-- ============================================================================

-- Enable RLS
ALTER TABLE content_versions ENABLE ROW LEVEL SECURITY;

-- Content Versions: inherit from contents
CREATE POLICY content_versions_isolation ON content_versions
    FOR ALL
    USING (
        EXISTS (SELECT 1 FROM current_setting('app.is_super_admin', true) WHERE current_setting('app.is_super_admin', true)::BOOLEAN = TRUE)
        OR EXISTS (
            SELECT 1 FROM contents
            WHERE contents.id = content_versions.content_id
              AND contents.organization_id = current_setting('app.current_organization_id', true)::INTEGER
        )
    );

COMMENT ON POLICY content_versions_isolation ON content_versions IS
    'Multi-tenant isolation - inherits from contents table';

-- ============================================================================
-- 7. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE content_versions IS 'Version control for content metadata and file references';

COMMENT ON COLUMN content_versions.version_number IS 'Sequential version number (starts at 1)';
COMMENT ON COLUMN content_versions.is_current IS 'TRUE if this is the active version';
COMMENT ON COLUMN content_versions.change_type IS 'created, updated, replaced, reverted';
COMMENT ON COLUMN content_versions.change_summary IS 'Human-readable description of what changed';
COMMENT ON COLUMN content_versions.storage_key IS 'File reference - unchanged if only metadata updated';

-- ============================================================================
-- 8. VERIFICATION QUERIES
-- ============================================================================

-- Verify table created
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'content_versions';

-- Verify trigger created
SELECT trigger_name, event_manipulation
FROM information_schema.triggers
WHERE trigger_name = 'trigger_content_version';

-- Verify functions created
SELECT proname
FROM pg_proc
WHERE proname IN ('create_content_version', 'revert_to_version', 'get_version_diff');

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;

-- Drop RLS policy
DROP POLICY IF EXISTS content_versions_isolation ON content_versions;

-- Drop views
DROP VIEW IF EXISTS content_version_history;
DROP VIEW IF EXISTS recent_content_changes;

-- Drop functions
DROP FUNCTION IF EXISTS get_version_diff(INTEGER, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS revert_to_version(INTEGER, INTEGER, INTEGER);

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_content_version ON contents;
DROP FUNCTION IF EXISTS create_content_version();

-- Drop indexes
DROP INDEX IF EXISTS idx_content_versions_content;
DROP INDEX IF EXISTS idx_content_versions_current;
DROP INDEX IF EXISTS idx_content_versions_created;
DROP INDEX IF EXISTS idx_content_versions_change_type;
DROP INDEX IF EXISTS idx_content_versions_creator;

-- Drop table
DROP TABLE IF EXISTS content_versions;

COMMIT;
*/

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- View version history for content
/*
SELECT * FROM content_version_history
WHERE content_id = 123
ORDER BY version_number DESC;
*/

-- Revert to previous version
/*
SELECT revert_to_version(123, 2, 1);  -- content_id, version_number, reverted_by_user_id
*/

-- Compare two versions
/*
SELECT * FROM get_version_diff(123, 1, 2);  -- content_id, from_version, to_version
*/

-- See recent changes across all content
/*
SELECT * FROM recent_content_changes
WHERE organization_id = 1
LIMIT 20;
*/

-- ============================================================================
-- STORAGE CONSIDERATIONS
-- ============================================================================
/*
Storage Impact:
- Metadata versions: ~500 bytes per version
- For 10,000 content items with avg 5 versions each: ~25MB
- Minimal storage cost, huge operational benefit

Cleanup Strategy (optional):
- Keep all versions for active content
- For deleted content, keep versions for 90 days
- Then archive to cold storage or purge old versions

CREATE INDEX idx_content_versions_cleanup ON content_versions(created_at)
    WHERE is_current = FALSE;

-- Cleanup query (run monthly):
DELETE FROM content_versions
WHERE is_current = FALSE
  AND created_at < NOW() - INTERVAL '90 days'
  AND content_id IN (
      SELECT id FROM contents WHERE deleted_at IS NOT NULL
  );
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/018_add_content_versions.sql
