-- ============================================================================
-- Migration: 021_rls_helper_functions.sql
-- Description: Add RLS helper functions for tenant isolation
-- Date: 2026-01-29
-- Phase: Backend completion for PUGUH Control Plane
-- ============================================================================
--
-- This migration creates helper functions used by Row Level Security policies.
-- These functions allow RLS policies to check:
-- - Current tenant context (from app settings)
-- - Current user context (from app settings)
-- - Platform admin status
--
-- The app must set these session variables before queries:
-- - SET LOCAL app.current_tenant_id = 'uuid';
-- - SET LOCAL app.current_user_id = 'uuid';
-- - SET LOCAL app.is_platform_admin = 'true/false';
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- FUNCTION: current_tenant_id()
-- Returns the current tenant ID from session settings
-- ============================================================================

CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
DECLARE
    tenant_id_str TEXT;
BEGIN
    -- Get tenant ID from session setting
    tenant_id_str := current_setting('app.current_tenant_id', true);

    -- Return NULL if not set
    IF tenant_id_str IS NULL OR tenant_id_str = '' THEN
        RETURN NULL;
    END IF;

    -- Cast to UUID
    RETURN tenant_id_str::UUID;
EXCEPTION
    WHEN invalid_text_representation THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION current_tenant_id() IS 'Returns the current tenant ID from session settings (app.current_tenant_id)';

-- ============================================================================
-- FUNCTION: current_app_user_id()
-- Returns the current user ID from session settings
-- ============================================================================

CREATE OR REPLACE FUNCTION current_app_user_id()
RETURNS UUID AS $$
DECLARE
    user_id_str TEXT;
BEGIN
    -- Get user ID from session setting
    user_id_str := current_setting('app.current_user_id', true);

    -- Return NULL if not set
    IF user_id_str IS NULL OR user_id_str = '' THEN
        RETURN NULL;
    END IF;

    -- Cast to UUID
    RETURN user_id_str::UUID;
EXCEPTION
    WHEN invalid_text_representation THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION current_app_user_id() IS 'Returns the current user ID from session settings (app.current_user_id)';

-- ============================================================================
-- FUNCTION: is_platform_admin()
-- Returns TRUE if the current user is a platform admin
-- ============================================================================

CREATE OR REPLACE FUNCTION is_platform_admin()
RETURNS BOOLEAN AS $$
DECLARE
    is_admin_str TEXT;
BEGIN
    -- Get platform admin flag from session setting
    is_admin_str := current_setting('app.is_platform_admin', true);

    -- Return FALSE if not set
    IF is_admin_str IS NULL OR is_admin_str = '' THEN
        RETURN FALSE;
    END IF;

    -- Check if 'true' (case insensitive)
    RETURN LOWER(is_admin_str) = 'true' OR is_admin_str = '1';
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_platform_admin() IS 'Returns TRUE if the current user is a platform admin (app.is_platform_admin = true)';

-- ============================================================================
-- FUNCTION: set_tenant_context(tenant_id, user_id, is_admin)
-- Convenience function to set all context variables at once
-- ============================================================================

CREATE OR REPLACE FUNCTION set_tenant_context(
    p_tenant_id UUID,
    p_user_id UUID DEFAULT NULL,
    p_is_platform_admin BOOLEAN DEFAULT FALSE
)
RETURNS VOID AS $$
BEGIN
    -- Set tenant context
    IF p_tenant_id IS NOT NULL THEN
        PERFORM set_config('app.current_tenant_id', p_tenant_id::TEXT, true);
    END IF;

    -- Set user context
    IF p_user_id IS NOT NULL THEN
        PERFORM set_config('app.current_user_id', p_user_id::TEXT, true);
    END IF;

    -- Set admin flag
    PERFORM set_config('app.is_platform_admin', p_is_platform_admin::TEXT, true);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_tenant_context(UUID, UUID, BOOLEAN) IS 'Convenience function to set tenant context variables for RLS';

-- ============================================================================
-- FUNCTION: clear_tenant_context()
-- Clears all tenant context variables
-- ============================================================================

CREATE OR REPLACE FUNCTION clear_tenant_context()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', '', true);
    PERFORM set_config('app.current_user_id', '', true);
    PERFORM set_config('app.is_platform_admin', 'false', true);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clear_tenant_context() IS 'Clears all tenant context variables';

-- ============================================================================
-- Record migration
-- ============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (21, '021_rls_helper_functions')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;

-- ============================================================================
-- END OF MIGRATION 021
-- ============================================================================
