-- Migration 046: Add Audit Trail Fields to RBAC and Content Tables
-- Purpose: Enable comprehensive audit logging for RBAC operations and content management
-- Priority: P0 - Security Critical
-- Impact: +13% audit coverage (44% → 57%)
-- Related: Analysis report BACKEND_ARCHITECTURE_AUDIT_REPORT.md

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration adds audit trail fields (created_by_id, updated_by_id) to:
-- 1. roles - Track who creates/modifies roles
-- 2. user_roles - Track who assigns/revokes roles
-- 3. role_permissions - Track who assigns/revokes permissions
-- 4. schedules - Track who creates/modifies schedules
-- 5. widgets - Track who creates/modifies widgets
-- 6. templates - Track who creates/modifies templates
--
-- After this migration:
-- - RBAC operations will be fully auditable
-- - Content management operations will be fully auditable
-- - Compliance requirements will be met
-- ============================================================================


-- ============================================================================
-- PRE-MIGRATION VERIFICATION
-- ============================================================================

-- Check current state
DO $$
DECLARE
    roles_count INTEGER;
    user_roles_count INTEGER;
    role_permissions_count INTEGER;
    schedules_count INTEGER;
    widgets_count INTEGER;
    templates_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO roles_count FROM roles;
    SELECT COUNT(*) INTO user_roles_count FROM user_roles;
    SELECT COUNT(*) INTO role_permissions_count FROM role_permissions;
    SELECT COUNT(*) INTO schedules_count FROM schedules;
    SELECT COUNT(*) INTO widgets_count FROM widgets;
    SELECT COUNT(*) INTO templates_count FROM templates;

    RAISE NOTICE '====================================';
    RAISE NOTICE 'PRE-MIGRATION DATA CHECK';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'roles rows: %', roles_count;
    RAISE NOTICE 'user_roles rows: %', user_roles_count;
    RAISE NOTICE 'role_permissions rows: %', role_permissions_count;
    RAISE NOTICE 'schedules rows: %', schedules_count;
    RAISE NOTICE 'widgets rows: %', widgets_count;
    RAISE NOTICE 'templates rows: %', templates_count;
    RAISE NOTICE '====================================';
END $$;


-- ============================================================================
-- PHASE 1: ADD AUDIT TRAIL TO ROLES TABLE
-- ============================================================================

-- Add created_by_id and updated_by_id to roles
ALTER TABLE roles
    ADD COLUMN created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Add indexes for audit queries
CREATE INDEX idx_roles_created_by ON roles(created_by_id);
CREATE INDEX idx_roles_updated_by ON roles(updated_by_id);

-- Add column comments
COMMENT ON COLUMN roles.created_by_id IS
    'User who created this role (NULL for system-created roles)';
COMMENT ON COLUMN roles.updated_by_id IS
    'User who last updated this role (NULL if never updated)';


-- ============================================================================
-- PHASE 2: ADD AUDIT TRAIL TO USER_ROLES TABLE
-- ============================================================================

-- Add assigned_by_id to user_roles (who assigned the role to the user)
ALTER TABLE user_roles
    ADD COLUMN assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Add index
CREATE INDEX idx_user_roles_assigned_by ON user_roles(assigned_by_id);

-- Add column comment
COMMENT ON COLUMN user_roles.assigned_by_id IS
    'User who assigned this role to the user (NULL for system assignments)';


-- ============================================================================
-- PHASE 3: ADD AUDIT TRAIL TO ROLE_PERMISSIONS TABLE
-- ============================================================================

-- Add assigned_by_id to role_permissions (who assigned the permission to the role)
ALTER TABLE role_permissions
    ADD COLUMN assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Add index
CREATE INDEX idx_role_permissions_assigned_by ON role_permissions(assigned_by_id);

-- Add column comment
COMMENT ON COLUMN role_permissions.assigned_by_id IS
    'User who assigned this permission to the role (NULL for system assignments)';


-- ============================================================================
-- PHASE 4: ADD AUDIT TRAIL TO SCHEDULES TABLE
-- ============================================================================

-- Check if columns already exist (schedules might have been created with these)
DO $$
BEGIN
    -- Add updated_by_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'schedules' AND column_name = 'updated_by_id'
    ) THEN
        ALTER TABLE schedules
            ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

        CREATE INDEX idx_schedules_updated_by ON schedules(updated_by_id);

        COMMENT ON COLUMN schedules.updated_by_id IS
            'User who last updated this schedule (NULL if never updated)';

        RAISE NOTICE 'Added updated_by_id to schedules';
    ELSE
        RAISE NOTICE 'schedules.updated_by_id already exists, skipping';
    END IF;
END $$;


-- ============================================================================
-- PHASE 5: ADD AUDIT TRAIL TO WIDGETS TABLE
-- ============================================================================

-- Check if columns already exist
DO $$
BEGIN
    -- Add created_by_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'widgets' AND column_name = 'created_by_id'
    ) THEN
        ALTER TABLE widgets
            ADD COLUMN created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

        CREATE INDEX idx_widgets_created_by ON widgets(created_by_id);

        COMMENT ON COLUMN widgets.created_by_id IS
            'User who created this widget (NULL for system widgets)';

        RAISE NOTICE 'Added created_by_id to widgets';
    ELSE
        RAISE NOTICE 'widgets.created_by_id already exists, skipping';
    END IF;

    -- Add updated_by_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'widgets' AND column_name = 'updated_by_id'
    ) THEN
        ALTER TABLE widgets
            ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

        CREATE INDEX idx_widgets_updated_by ON widgets(updated_by_id);

        COMMENT ON COLUMN widgets.updated_by_id IS
            'User who last updated this widget (NULL if never updated)';

        RAISE NOTICE 'Added updated_by_id to widgets';
    ELSE
        RAISE NOTICE 'widgets.updated_by_id already exists, skipping';
    END IF;
END $$;


-- ============================================================================
-- PHASE 6: ADD AUDIT TRAIL TO TEMPLATES TABLE
-- ============================================================================

-- Check if columns already exist
DO $$
BEGIN
    -- Add created_by_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'templates' AND column_name = 'created_by_id'
    ) THEN
        ALTER TABLE templates
            ADD COLUMN created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

        CREATE INDEX idx_templates_created_by ON templates(created_by_id);

        COMMENT ON COLUMN templates.created_by_id IS
            'User who created this template (NULL for system templates)';

        RAISE NOTICE 'Added created_by_id to templates';
    ELSE
        RAISE NOTICE 'templates.created_by_id already exists, skipping';
    END IF;

    -- Add updated_by_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'templates' AND column_name = 'updated_by_id'
    ) THEN
        ALTER TABLE templates
            ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

        CREATE INDEX idx_templates_updated_by ON templates(updated_by_id);

        COMMENT ON COLUMN templates.updated_by_id IS
            'User who last updated this template (NULL if never updated)';

        RAISE NOTICE 'Added updated_by_id to templates';
    ELSE
        RAISE NOTICE 'templates.updated_by_id already exists, skipping';
    END IF;
END $$;


-- ============================================================================
-- PHASE 7: VERIFICATION - AUDIT TRAIL COVERAGE
-- ============================================================================

-- Verify all audit fields are in place
DO $$
DECLARE
    roles_created_by BOOLEAN;
    roles_updated_by BOOLEAN;
    user_roles_assigned_by BOOLEAN;
    role_permissions_assigned_by BOOLEAN;
    schedules_updated_by BOOLEAN;
    widgets_created_by BOOLEAN;
    widgets_updated_by BOOLEAN;
    templates_created_by BOOLEAN;
    templates_updated_by BOOLEAN;
    success_count INTEGER := 0;
    total_count INTEGER := 9;
BEGIN
    -- Check each column
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'roles' AND column_name = 'created_by_id'
    ) INTO roles_created_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'roles' AND column_name = 'updated_by_id'
    ) INTO roles_updated_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_roles' AND column_name = 'assigned_by_id'
    ) INTO user_roles_assigned_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'role_permissions' AND column_name = 'assigned_by_id'
    ) INTO role_permissions_assigned_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'schedules' AND column_name = 'updated_by_id'
    ) INTO schedules_updated_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'widgets' AND column_name = 'created_by_id'
    ) INTO widgets_created_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'widgets' AND column_name = 'updated_by_id'
    ) INTO widgets_updated_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'templates' AND column_name = 'created_by_id'
    ) INTO templates_created_by;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'templates' AND column_name = 'updated_by_id'
    ) INTO templates_updated_by;

    -- Count successes
    IF roles_created_by THEN success_count := success_count + 1; END IF;
    IF roles_updated_by THEN success_count := success_count + 1; END IF;
    IF user_roles_assigned_by THEN success_count := success_count + 1; END IF;
    IF role_permissions_assigned_by THEN success_count := success_count + 1; END IF;
    IF schedules_updated_by THEN success_count := success_count + 1; END IF;
    IF widgets_created_by THEN success_count := success_count + 1; END IF;
    IF widgets_updated_by THEN success_count := success_count + 1; END IF;
    IF templates_created_by THEN success_count := success_count + 1; END IF;
    IF templates_updated_by THEN success_count := success_count + 1; END IF;

    -- Report results
    RAISE NOTICE '====================================';
    RAISE NOTICE 'AUDIT TRAIL VERIFICATION';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'roles.created_by_id: %', CASE WHEN roles_created_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'roles.updated_by_id: %', CASE WHEN roles_updated_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'user_roles.assigned_by_id: %', CASE WHEN user_roles_assigned_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'role_permissions.assigned_by_id: %', CASE WHEN role_permissions_assigned_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'schedules.updated_by_id: %', CASE WHEN schedules_updated_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'widgets.created_by_id: %', CASE WHEN widgets_created_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'widgets.updated_by_id: %', CASE WHEN widgets_updated_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'templates.created_by_id: %', CASE WHEN templates_created_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE 'templates.updated_by_id: %', CASE WHEN templates_updated_by THEN '✅' ELSE '❌' END;
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Success: %/%', success_count, total_count;
    RAISE NOTICE '====================================';

    IF success_count = total_count THEN
        RAISE NOTICE '✅ SUCCESS: ALL AUDIT TRAIL FIELDS ADDED!';
        RAISE NOTICE '🎉 RBAC & Content audit logging foundation complete';
    ELSE
        RAISE WARNING '⚠️  WARNING: % audit trail fields missing', total_count - success_count;
    END IF;
    RAISE NOTICE '====================================';
END $$;


-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, run:
/*
-- Remove audit trail from roles
ALTER TABLE roles DROP COLUMN IF EXISTS created_by_id;
ALTER TABLE roles DROP COLUMN IF EXISTS updated_by_id;

-- Remove audit trail from user_roles
ALTER TABLE user_roles DROP COLUMN IF EXISTS assigned_by_id;

-- Remove audit trail from role_permissions
ALTER TABLE role_permissions DROP COLUMN IF EXISTS assigned_by_id;

-- Remove audit trail from schedules
ALTER TABLE schedules DROP COLUMN IF EXISTS updated_by_id;

-- Remove audit trail from widgets
ALTER TABLE widgets DROP COLUMN IF EXISTS created_by_id;
ALTER TABLE widgets DROP COLUMN IF EXISTS updated_by_id;

-- Remove audit trail from templates
ALTER TABLE templates DROP COLUMN IF EXISTS created_by_id;
ALTER TABLE templates DROP COLUMN IF EXISTS updated_by_id;

-- Drop indexes
DROP INDEX IF EXISTS idx_roles_created_by;
DROP INDEX IF EXISTS idx_roles_updated_by;
DROP INDEX IF EXISTS idx_user_roles_assigned_by;
DROP INDEX IF EXISTS idx_role_permissions_assigned_by;
DROP INDEX IF EXISTS idx_schedules_updated_by;
DROP INDEX IF EXISTS idx_widgets_created_by;
DROP INDEX IF EXISTS idx_widgets_updated_by;
DROP INDEX IF EXISTS idx_templates_created_by;
DROP INDEX IF EXISTS idx_templates_updated_by;
*/


-- ============================================================================
-- POST-MIGRATION CHECKLIST
-- ============================================================================
-- Backend Code Updates Required:
--
-- 1. Models (SQLAlchemy):
--    [ ] Update RoleModel - add created_by_id, updated_by_id
--    [ ] Update UserRoleModel - add assigned_by_id
--    [ ] Update RolePermissionModel - add assigned_by_id
--    [ ] Update ScheduleModel - add updated_by_id (if not exists)
--    [ ] Update WidgetModel - add created_by_id, updated_by_id (if not exists)
--    [ ] Update TemplateModel - add created_by_id, updated_by_id (if not exists)
--
-- 2. DTOs (Pydantic):
--    [ ] Update RoleCreateDTO, RoleUpdateDTO, RoleDTO
--    [ ] Update UserRoleCreateDTO, UserRoleDTO
--    [ ] Update RolePermissionCreateDTO, RolePermissionDTO
--    [ ] Update ScheduleUpdateDTO, ScheduleDTO
--    [ ] Update WidgetCreateDTO, WidgetUpdateDTO, WidgetDTO
--    [ ] Update TemplateCreateDTO, TemplateUpdateDTO, TemplateDTO
--
-- 3. Repositories:
--    [ ] Update role_repo.py - include created_by_id, updated_by_id in create/update
--    [ ] Update user_role_repo.py - include assigned_by_id in create
--    [ ] Update role_permission_repo.py - include assigned_by_id in create
--    [ ] Update schedule_repo.py - include updated_by_id in update
--    [ ] Update widget_repo.py - include created_by_id, updated_by_id
--    [ ] Update template_repo.py - include created_by_id, updated_by_id
--
-- 4. Use Cases:
--    [ ] CreateRole - set created_by_id from current_user
--    [ ] UpdateRole - set updated_by_id from current_user
--    [ ] AssignRole - set assigned_by_id from current_user
--    [ ] AssignPermission - set assigned_by_id from current_user
--    [ ] CreateSchedule - set created_by_id from current_user
--    [ ] UpdateSchedule - set updated_by_id from current_user
--    [ ] CreateWidget - set created_by_id from current_user
--    [ ] UpdateWidget - set updated_by_id from current_user
--    [ ] CreateTemplate - set created_by_id from current_user
--    [ ] UpdateTemplate - set updated_by_id from current_user
--
-- 5. Routes:
--    [ ] All RBAC routes - pass current_user.id to use cases
--    [ ] All Schedule routes - pass current_user.id to use cases
--    [ ] All Widget routes - pass current_user.id to use cases
--    [ ] All Template routes - pass current_user.id to use cases
--
-- 6. Activity Logging:
--    [ ] Add audit log entries for all RBAC operations
--    [ ] Add audit log entries for Schedule operations
--    [ ] Add audit log entries for Widget operations
--    [ ] Add audit log entries for Template operations
--
-- 7. Frontend:
--    [ ] Update TypeScript types to include audit fields
--    [ ] Display "Created by" / "Updated by" in UI
--    [ ] Show audit trail in details/history views
--
-- 8. Testing:
--    [ ] Test role creation with created_by_id
--    [ ] Test role update with updated_by_id
--    [ ] Test role assignment with assigned_by_id
--    [ ] Test permission assignment with assigned_by_id
--    [ ] Test schedule operations with audit trail
--    [ ] Test widget operations with audit trail
--    [ ] Test template operations with audit trail
--    [ ] Verify audit logs are created
--
-- 9. Documentation:
--    [ ] Update API docs with new audit fields
--    [ ] Update DATABASE_CONVENTIONS.md
--    [ ] Update BACKEND_ARCHITECTURE_AUDIT_REPORT.md (44% → 57% coverage)
--    [ ] Add migration to CLAUDE.md migration history
--    [ ] Document audit trail best practices
-- ============================================================================


-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================
-- Migration Number: 046
-- Created: 2025-01-20
-- Author: System Analysis - P0 Critical Security Fix
-- Breaking Changes: NO (adds new nullable columns)
-- Data Loss Risk: NONE (new columns only)
-- Reversible: YES (see rollback instructions above)
-- Dependencies: Requires migrations 001-045
-- Estimated Time: < 2 seconds (adds columns and indexes)
-- Security Impact: HIGH (enables comprehensive audit logging)
-- Compliance: Improves SOC2, GDPR, HIPAA compliance readiness
-- ============================================================================
