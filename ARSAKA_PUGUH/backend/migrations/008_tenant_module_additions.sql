-- ============================================================================
-- Migration 008: Tenant Module Additions
-- ============================================================================
-- Adds missing columns and tables for Phase 2 tenant management:
-- 1. Add missing columns to tenants table
-- 2. Add membership_id to tenant_memberships
-- 3. Create invitations table
-- ============================================================================

-- ============================================================================
-- 1. ADD MISSING COLUMNS TO TENANTS
-- ============================================================================

-- Add settings JSONB column
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS settings JSONB NOT NULL DEFAULT '{}';

-- Add billing_email column
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255);

-- Add soft delete columns
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Add index for active tenants
CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(is_deleted) WHERE is_deleted = FALSE;

COMMENT ON COLUMN tenants.settings IS 'Tenant-specific settings as JSON';
COMMENT ON COLUMN tenants.billing_email IS 'Email for billing notifications';
COMMENT ON COLUMN tenants.is_deleted IS 'Soft delete flag';
COMMENT ON COLUMN tenants.deleted_at IS 'Timestamp when tenant was soft deleted';

-- ============================================================================
-- 2. ADD MEMBERSHIP_ID TO TENANT_MEMBERSHIPS
-- ============================================================================

-- Note: We need to handle the transition from composite PK to UUID PK
-- First, add the new column
ALTER TABLE tenant_memberships ADD COLUMN IF NOT EXISTS membership_id UUID DEFAULT gen_random_uuid();

-- Add joined_at column (alias for accepted_at)
ALTER TABLE tenant_memberships ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ;

-- Sync joined_at with accepted_at for existing records
UPDATE tenant_memberships SET joined_at = accepted_at WHERE joined_at IS NULL AND accepted_at IS NOT NULL;

-- Create index on membership_id
CREATE INDEX IF NOT EXISTS idx_memberships_id ON tenant_memberships(membership_id);

COMMENT ON COLUMN tenant_memberships.membership_id IS 'Unique identifier for membership (for API operations)';
COMMENT ON COLUMN tenant_memberships.joined_at IS 'When user accepted and joined the tenant';

-- ============================================================================
-- 3. CREATE INVITATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Target
    email VARCHAR(255) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Token for accepting
    token VARCHAR(100) NOT NULL,

    -- Assignment
    role VARCHAR(20) NOT NULL DEFAULT 'member',

    -- Inviter
    invited_by_user_id UUID NOT NULL REFERENCES users(user_id),

    -- Target user (if email already registered)
    target_user_id UUID REFERENCES users(user_id),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Message
    message TEXT,

    -- Expiry
    expires_at TIMESTAMPTZ NOT NULL,

    -- Status timestamps
    accepted_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT invitations_token_unique UNIQUE (token),
    CONSTRAINT invitations_check_role CHECK (
        role IN ('owner', 'admin', 'member', 'viewer')
    ),
    CONSTRAINT invitations_check_status CHECK (
        status IN ('pending', 'accepted', 'rejected', 'expired', 'cancelled')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_invitations_tenant ON invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON invitations(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_invitations_target ON invitations(target_user_id) WHERE target_user_id IS NOT NULL;

-- Unique pending invitation per email per tenant
CREATE UNIQUE INDEX IF NOT EXISTS idx_invitations_pending_unique ON invitations(LOWER(email), tenant_id)
    WHERE status = 'pending';

COMMENT ON TABLE invitations IS 'Email invitations to join a tenant';
COMMENT ON COLUMN invitations.token IS 'Secure token for accepting invitation via link';
COMMENT ON COLUMN invitations.target_user_id IS 'Linked user ID (set when email is already registered or when user registers)';

-- ============================================================================
-- 4. ADD TRIGGER FOR INVITATIONS UPDATED_AT
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_update_invitations_updated_at ON invitations;
CREATE TRIGGER trigger_update_invitations_updated_at
    BEFORE UPDATE ON invitations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. GRANTS
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON invitations TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ARSAKA_PUGUH SaaS Platform - Migration 008: Tenant module additions';
