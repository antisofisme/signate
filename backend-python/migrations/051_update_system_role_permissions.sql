-- Migration: 051
-- Description: Update system role permissions with granular {resource: [actions]} format
-- Date: 2025-11-27
-- Author: Claude Code

BEGIN;

-- =============================================================================
-- UPDATE SYSTEM ROLE PERMISSIONS
-- =============================================================================

-- Update SUPER_ADMIN: Full system access
UPDATE roles
SET permissions = '{
  "dashboard": ["view", "manage"],
  "devices": ["view", "create", "edit", "delete", "manage"],
  "device_groups": ["view", "create", "edit", "delete", "manage"],
  "contents": ["view", "create", "edit", "delete", "manage"],
  "playlists": ["view", "create", "edit", "delete", "manage"],
  "schedules": ["view", "create", "edit", "delete", "manage"],
  "tags": ["view", "create", "edit", "delete", "manage"],
  "menus": ["view", "create", "edit", "delete", "manage"],
  "analytics": ["view", "manage"],
  "audit_logs": ["view", "manage"],
  "users": ["view", "create", "edit", "delete", "manage"],
  "organizations": ["view", "create", "edit", "delete", "manage"],
  "roles": ["view", "create", "edit", "delete", "manage"],
  "sessions": ["view", "manage"],
  "settings": ["view", "edit", "manage"],
  "system": ["view", "manage"]
}'::jsonb,
    updated_at = NOW()
WHERE name = 'SUPER_ADMIN' AND is_system_role = TRUE;

-- Update ADMIN: Organization-level management (no system-level access)
UPDATE roles
SET permissions = '{
  "dashboard": ["view"],
  "devices": ["view", "create", "edit", "delete"],
  "device_groups": ["view", "create", "edit", "delete"],
  "contents": ["view", "create", "edit", "delete"],
  "playlists": ["view", "create", "edit", "delete"],
  "schedules": ["view", "create", "edit", "delete"],
  "tags": ["view", "create", "edit", "delete"],
  "menus": ["view", "create", "edit", "delete"],
  "analytics": ["view"],
  "audit_logs": ["view"],
  "users": ["view", "create", "edit", "delete"],
  "organizations": ["view", "edit"],
  "roles": ["view", "create", "edit", "delete"],
  "sessions": ["view"],
  "settings": ["view", "edit"]
}'::jsonb,
    updated_at = NOW()
WHERE name = 'ADMIN' AND is_system_role = TRUE;

-- Update CONTENT_MANAGER: Content-focused permissions
UPDATE roles
SET permissions = '{
  "dashboard": ["view"],
  "devices": ["view"],
  "contents": ["view", "create", "edit", "delete"],
  "playlists": ["view", "create", "edit", "delete"],
  "schedules": ["view", "create", "edit"],
  "tags": ["view", "create", "edit"],
  "menus": ["view", "create", "edit"]
}'::jsonb,
    updated_at = NOW()
WHERE name = 'CONTENT_MANAGER' AND is_system_role = TRUE;

-- Update VIEWER: Read-only access
UPDATE roles
SET permissions = '{
  "dashboard": ["view"],
  "devices": ["view"],
  "contents": ["view"],
  "playlists": ["view"],
  "schedules": ["view"],
  "analytics": ["view"]
}'::jsonb,
    updated_at = NOW()
WHERE name = 'VIEWER' AND is_system_role = TRUE;

-- =============================================================================
-- VERIFICATION QUERIES (for manual check after migration)
-- =============================================================================

-- Verify all system roles have been updated:
-- SELECT name, permissions, updated_at FROM roles WHERE is_system_role = TRUE;

-- Count permissions per role:
-- SELECT name,
--        jsonb_object_keys(permissions) as resource,
--        jsonb_array_length(permissions->jsonb_object_keys(permissions)) as action_count
-- FROM roles WHERE is_system_role = TRUE;

COMMIT;

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================
-- To rollback, run:
-- UPDATE roles SET permissions = '{"all": true}'::jsonb WHERE is_system_role = TRUE;
