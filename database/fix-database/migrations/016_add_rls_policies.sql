-- ============================================================================
-- Migration 016: Add Row-Level Security (RLS) Policies
-- Description: Implement RLS for multi-tenant data isolation and security
-- Created: 2025-01-09
-- Priority: HIGH
-- ============================================================================

BEGIN;

-- ============================================================================
-- RLS OVERVIEW
-- ============================================================================
-- Row-Level Security (RLS) ensures that users can only access data from their
-- own organization, even if application-level checks fail.
--
-- Benefits:
-- 1. Defense in depth - Database-level security
-- 2. Prevents data leaks from application bugs
-- 3. Compliance with data isolation requirements
-- 4. Audit-friendly (PostgreSQL logs RLS policy usage)
--
-- Implementation:
-- - Use session variable: current_setting('app.current_organization_id')
-- - Set by application on each request after authentication
-- - Policies enforce organization_id matching
-- ============================================================================

-- ============================================================================
-- 1. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to get current organization ID from session
CREATE OR REPLACE FUNCTION get_current_organization_id()
RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true)::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_current_organization_id() IS
    'Returns the organization_id set in session variable by application';

-- Function to check if user is super admin
CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_setting('app.is_super_admin', true)::BOOLEAN;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION is_super_admin() IS
    'Returns TRUE if current user is SUPER_ADMIN (can access all organizations)';

-- ============================================================================
-- 2. ENABLE RLS ON MULTI-TENANT TABLES
-- ============================================================================

-- Core multi-tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;

-- Junction tables
ALTER TABLE content_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_assignments ENABLE ROW LEVEL SECURITY;

-- Support tables
ALTER TABLE device_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_speed_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_playback_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3. CREATE RLS POLICIES - USERS TABLE
-- ============================================================================

-- Users can see users from their organization (or all if super admin)
CREATE POLICY users_isolation ON users
    FOR SELECT
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

-- Users can insert users into their organization
CREATE POLICY users_insert ON users
    FOR INSERT
    WITH CHECK (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

-- Users can update users in their organization
CREATE POLICY users_update ON users
    FOR UPDATE
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

-- Users can delete users in their organization (soft delete)
CREATE POLICY users_delete ON users
    FOR DELETE
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY users_isolation ON users IS
    'Users can only see users from their organization (or all if super admin)';

-- ============================================================================
-- 4. CREATE RLS POLICIES - ROLES TABLE
-- ============================================================================

-- Roles: see system roles + organization-specific roles
CREATE POLICY roles_isolation ON roles
    FOR SELECT
    USING (
        is_super_admin() OR
        is_system_role = TRUE OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY roles_insert ON roles
    FOR INSERT
    WITH CHECK (
        is_super_admin() OR
        (is_system_role = FALSE AND organization_id = get_current_organization_id())
    );

CREATE POLICY roles_update ON roles
    FOR UPDATE
    USING (
        is_super_admin() OR
        (is_system_role = FALSE AND organization_id = get_current_organization_id())
    );

CREATE POLICY roles_delete ON roles
    FOR DELETE
    USING (
        is_super_admin() OR
        (is_system_role = FALSE AND organization_id = get_current_organization_id())
    );

COMMENT ON POLICY roles_isolation ON roles IS
    'Users can see system roles + their organization roles';

-- ============================================================================
-- 5. CREATE RLS POLICIES - USER_SESSIONS TABLE
-- ============================================================================

-- Sessions: see only sessions from their organization
CREATE POLICY sessions_isolation ON user_sessions
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY sessions_isolation ON user_sessions IS
    'Users can only see sessions from their organization';

-- ============================================================================
-- 6. CREATE RLS POLICIES - CONTENTS TABLE
-- ============================================================================

CREATE POLICY contents_isolation ON contents
    FOR SELECT
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY contents_insert ON contents
    FOR INSERT
    WITH CHECK (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY contents_update ON contents
    FOR UPDATE
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY contents_delete ON contents
    FOR DELETE
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY contents_isolation ON contents IS
    'Multi-tenant isolation for contents table';

-- ============================================================================
-- 7. CREATE RLS POLICIES - TAGS TABLE
-- ============================================================================

CREATE POLICY tags_isolation ON tags
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY tags_isolation ON tags IS
    'Multi-tenant isolation for tags table';

-- ============================================================================
-- 8. CREATE RLS POLICIES - DEVICES TABLE
-- ============================================================================

-- Devices: Allow unactivated devices (organization_id = NULL) to be seen
CREATE POLICY devices_isolation ON devices
    FOR SELECT
    USING (
        is_super_admin() OR
        organization_id IS NULL OR
        organization_id = get_current_organization_id()
    );

-- Only allow inserting devices with correct organization
CREATE POLICY devices_insert ON devices
    FOR INSERT
    WITH CHECK (
        is_super_admin() OR
        organization_id IS NULL OR
        organization_id = get_current_organization_id()
    );

-- Only allow updating devices from same organization
CREATE POLICY devices_update ON devices
    FOR UPDATE
    USING (
        is_super_admin() OR
        organization_id IS NULL OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY devices_delete ON devices
    FOR DELETE
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY devices_isolation ON devices IS
    'Multi-tenant isolation for devices (allows unactivated devices)';

-- ============================================================================
-- 9. CREATE RLS POLICIES - PLAYLISTS TABLE
-- ============================================================================

CREATE POLICY playlists_isolation ON playlists
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY playlists_isolation ON playlists IS
    'Multi-tenant isolation for playlists table';

-- ============================================================================
-- 10. CREATE RLS POLICIES - JUNCTION TABLES
-- ============================================================================

-- Content Tags: inherit from contents and tags
CREATE POLICY content_tags_isolation ON content_tags
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM contents
            WHERE contents.id = content_tags.content_id
              AND contents.organization_id = get_current_organization_id()
        )
    );

-- Device Tags: inherit from devices and tags
CREATE POLICY device_tags_isolation ON device_tags
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM devices
            WHERE devices.id = device_tags.device_id
              AND (devices.organization_id = get_current_organization_id()
                   OR devices.organization_id IS NULL)
        )
    );

-- Playlist Contents: inherit from playlists
CREATE POLICY playlist_contents_isolation ON playlist_contents
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM playlists
            WHERE playlists.id = playlist_contents.playlist_id
              AND playlists.organization_id = get_current_organization_id()
        )
    );

-- Playlist Assignments: inherit from playlists
CREATE POLICY playlist_assignments_isolation ON playlist_assignments
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM playlists
            WHERE playlists.id = playlist_assignments.playlist_id
              AND playlists.organization_id = get_current_organization_id()
        )
    );

-- Content Assignments: inherit from devices
CREATE POLICY content_assignments_isolation ON content_assignments
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM devices
            WHERE devices.id = content_assignments.device_id
              AND (devices.organization_id = get_current_organization_id()
                   OR devices.organization_id IS NULL)
        )
    );

COMMENT ON POLICY content_tags_isolation ON content_tags IS
    'Junction table RLS - inherits from parent tables';

-- ============================================================================
-- 11. CREATE RLS POLICIES - SUPPORT TABLES
-- ============================================================================

-- Device Commands
CREATE POLICY device_commands_isolation ON device_commands
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM devices
            WHERE devices.id = device_commands.device_id
              AND (devices.organization_id = get_current_organization_id()
                   OR devices.organization_id IS NULL)
        )
    );

-- Device Logs
CREATE POLICY device_logs_isolation ON device_logs
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM devices
            WHERE devices.id = device_logs.device_id
              AND (devices.organization_id = get_current_organization_id()
                   OR devices.organization_id IS NULL)
        )
    );

-- Device Speed Tests
CREATE POLICY device_speed_tests_isolation ON device_speed_tests
    FOR ALL
    USING (
        is_super_admin() OR
        EXISTS (
            SELECT 1 FROM devices
            WHERE devices.id = device_speed_tests.device_id
              AND (devices.organization_id = get_current_organization_id()
                   OR devices.organization_id IS NULL)
        )
    );

-- Content Playback Logs
CREATE POLICY playback_logs_isolation ON content_playback_logs
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

-- Audit Logs
CREATE POLICY audit_logs_isolation ON audit_logs
    FOR SELECT
    USING (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

CREATE POLICY audit_logs_insert ON audit_logs
    FOR INSERT
    WITH CHECK (
        is_super_admin() OR
        organization_id = get_current_organization_id()
    );

COMMENT ON POLICY device_commands_isolation ON device_commands IS
    'RLS for device commands - inherits from devices table';
COMMENT ON POLICY audit_logs_isolation ON audit_logs IS
    'Audit logs RLS - users can only see logs from their organization';

-- ============================================================================
-- 12. GRANT PERMISSIONS TO APPLICATION USER
-- ============================================================================

-- Ensure signage_user can bypass RLS when needed (for system operations)
-- Application should still set organization_id for normal operations

-- Grant ability to set session variables
GRANT SET ON PARAMETER app.current_organization_id TO signage_user;
GRANT SET ON PARAMETER app.is_super_admin TO signage_user;

-- ============================================================================
-- 13. VERIFICATION QUERIES
-- ============================================================================

-- List all tables with RLS enabled
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = true
ORDER BY tablename;

-- List all RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

COMMIT;

-- ============================================================================
-- TESTING RLS POLICIES
-- ============================================================================
/*
-- Test RLS policies (run as signage_user)

-- 1. Set organization context
SET app.current_organization_id = '1';
SET app.is_super_admin = 'false';

-- 2. Test SELECT - should only see org 1 data
SELECT count(*) FROM contents;  -- Only org 1 contents
SELECT count(*) FROM devices;   -- Only org 1 devices + unactivated

-- 3. Test INSERT - should only allow org 1 data
INSERT INTO contents (title, organization_id) VALUES ('Test', 1);  -- OK
INSERT INTO contents (title, organization_id) VALUES ('Test', 2);  -- FAIL

-- 4. Test as super admin
SET app.is_super_admin = 'true';
SELECT count(*) FROM contents;  -- See ALL organizations

-- 5. Reset session
RESET app.current_organization_id;
RESET app.is_super_admin;
*/

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================
/*
BEGIN;

-- Disable RLS on all tables
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE contents DISABLE ROW LEVEL SECURITY;
ALTER TABLE tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE devices DISABLE ROW LEVEL SECURITY;
ALTER TABLE playlists DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE device_tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_contents DISABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_assignments DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_assignments DISABLE ROW LEVEL SECURITY;
ALTER TABLE device_commands DISABLE ROW LEVEL SECURITY;
ALTER TABLE device_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE device_speed_tests DISABLE ROW LEVEL SECURITY;
ALTER TABLE content_playback_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;

-- Drop all policies (they will be auto-dropped when RLS is disabled)
-- But for completeness:
DROP POLICY IF EXISTS users_isolation ON users;
DROP POLICY IF EXISTS users_insert ON users;
DROP POLICY IF EXISTS users_update ON users;
DROP POLICY IF EXISTS users_delete ON users;
-- ... (repeat for all policies)

-- Drop helper functions
DROP FUNCTION IF EXISTS get_current_organization_id();
DROP FUNCTION IF EXISTS is_super_admin();

COMMIT;
*/

-- ============================================================================
-- APPLICATION INTEGRATION GUIDE
-- ============================================================================
/*
Backend (FastAPI) integration:

1. Add middleware to set session variables on each request:

```python
from fastapi import Request
from sqlalchemy import text

@app.middleware("http")
async def set_rls_context(request: Request, call_next):
    # Get user from JWT token
    user = get_current_user(request)

    # Set session variables
    async with database.session() as session:
        await session.execute(
            text("SET app.current_organization_id = :org_id"),
            {"org_id": user.organization_id}
        )
        await session.execute(
            text("SET app.is_super_admin = :is_admin"),
            {"is_admin": user.role == "SUPER_ADMIN"}
        )

    response = await call_next(request)
    return response
```

2. For super admin operations, temporarily override:

```python
async def get_all_organizations():
    async with database.session() as session:
        # Temporarily set as super admin
        await session.execute(text("SET app.is_super_admin = 'true'"))

        # Query will now see all organizations
        result = await session.execute(select(Organization))

        # Reset after query
        await session.execute(text("RESET app.is_super_admin"))

        return result.all()
```

3. For system operations (migrations, cron jobs):
   - Use a dedicated database user with BYPASSRLS privilege
   - OR temporarily disable RLS: ALTER TABLE x DISABLE ROW LEVEL SECURITY
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- To run this migration on server:
-- docker exec -i signage-postgres psql -U signage_user -d signage_db < database/fix-database/migrations/016_add_rls_policies.sql
