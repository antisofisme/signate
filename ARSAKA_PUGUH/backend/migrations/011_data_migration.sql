-- Migration 011: Data Migration for SaaS Transformation
-- Migrates existing single-tenant data to multi-tenant + multi-project structure
-- Run this AFTER all schema migrations (001-010) are applied

-- ============================================================================
-- STEP 1: Create default admin user if not exists
-- ============================================================================

INSERT INTO users (user_id, email, password_hash, name, email_verified, status, auth_provider, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000000001'::uuid,
    'admin@atlashub.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYqJqJqJqJqJ', -- 'admin123' hashed
    'System Administrator',
    true,
    'active',
    'local',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'admin@atlashub.com'
);

-- ============================================================================
-- STEP 2: Create default tenant if not exists
-- ============================================================================

INSERT INTO tenants (tenant_id, name, slug, owner_user_id, plan, status, created_at, updated_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000'::uuid,
    'ATLAS Hub',
    'atlashub',
    '00000000-0000-0000-0000-000000000001'::uuid,
    'enterprise',
    'active',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM tenants WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid
);

-- ============================================================================
-- STEP 3: Create tenant membership for admin
-- ============================================================================

INSERT INTO tenant_memberships (user_id, tenant_id, role, status, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000000001'::uuid,
    '550e8400-e29b-41d4-a716-446655440000'::uuid,
    'owner',
    'active',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM tenant_memberships
    WHERE user_id = '00000000-0000-0000-0000-000000000001'::uuid
    AND tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid
);

-- ============================================================================
-- STEP 4: Create default project
-- ============================================================================

INSERT INTO projects (project_id, tenant_id, name, slug, description, environment, is_active, created_by, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000000010'::uuid,
    '550e8400-e29b-41d4-a716-446655440000'::uuid,
    'Default Project',
    'default',
    'Default project for migrated data',
    'production',
    true,
    '00000000-0000-0000-0000-000000000001'::uuid,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM projects WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid
);

-- ============================================================================
-- STEP 5: Backfill project_id on existing rules (if column exists)
-- ============================================================================

-- Update rules without project_id to use default project
UPDATE rules
SET project_id = '00000000-0000-0000-0000-000000000010'::uuid
WHERE project_id IS NULL
AND tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- ============================================================================
-- STEP 6: Backfill project_id on existing decisions (if column exists)
-- ============================================================================

UPDATE decisions
SET project_id = '00000000-0000-0000-0000-000000000010'::uuid
WHERE project_id IS NULL
AND tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- ============================================================================
-- STEP 7: Backfill project_id on existing workflows (if column exists)
-- ============================================================================

UPDATE workflows
SET project_id = '00000000-0000-0000-0000-000000000010'::uuid
WHERE project_id IS NULL
AND tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- ============================================================================
-- STEP 8: Create default subscription for the tenant
-- ============================================================================

INSERT INTO subscriptions (subscription_id, tenant_id, plan_id, status, current_period_start, current_period_end, created_at, updated_at)
SELECT
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440000'::uuid,
    'enterprise',
    'active',
    NOW(),
    NOW() + INTERVAL '1 year',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM subscriptions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid
);

-- ============================================================================
-- STEP 9: Add project membership for admin
-- ============================================================================

INSERT INTO project_memberships (project_id, user_id, role, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000000010'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'admin',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM project_memberships
    WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid
    AND user_id = '00000000-0000-0000-0000-000000000001'::uuid
);

-- ============================================================================
-- VERIFICATION QUERIES (run manually to verify migration)
-- ============================================================================

-- Check users
-- SELECT * FROM users WHERE user_id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Check tenants
-- SELECT * FROM tenants WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- Check tenant memberships
-- SELECT * FROM tenant_memberships WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- Check projects
-- SELECT * FROM projects WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;

-- Check rules with project_id
-- SELECT COUNT(*), project_id FROM rules GROUP BY project_id;

-- Check decisions with project_id
-- SELECT COUNT(*), project_id FROM decisions GROUP BY project_id;

-- Check workflows with project_id
-- SELECT COUNT(*), project_id FROM workflows GROUP BY project_id;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To rollback, run:
-- UPDATE rules SET project_id = NULL WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid;
-- UPDATE decisions SET project_id = NULL WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid;
-- UPDATE workflows SET project_id = NULL WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid;
-- DELETE FROM project_memberships WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid;
-- DELETE FROM projects WHERE project_id = '00000000-0000-0000-0000-000000000010'::uuid;
-- DELETE FROM subscriptions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'::uuid;
-- (Be careful with user/tenant deletion as they may have other dependencies)
