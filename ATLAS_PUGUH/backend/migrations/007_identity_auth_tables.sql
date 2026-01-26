-- ============================================================================
-- Migration 007: Identity & Auth Tables for SaaS Transformation
-- ============================================================================
-- Source: INFRA-DEC-007-identity-model.md
-- Source: INFRA-DEC-008-auth-flow.md
--
-- This migration creates:
-- 1. users - Global user identity
-- 2. tenants - Organization/workspace (updated from existing)
-- 3. tenant_memberships - User-to-tenant relationship
-- 4. projects - Sub-workspace within tenant
-- 5. auth_tokens - Verification, reset, refresh tokens
-- 6. token_blacklist - Revoked JWTs
-- 7. subscriptions - Billing subscriptions
-- 8. subscription_plans - Plan definitions
-- 9. invoices - Payment invoices
-- 10. payment_methods - Stored payment methods
-- ============================================================================

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),

    -- Authentication
    auth_provider VARCHAR(20) NOT NULL DEFAULT 'local',
    oauth_provider_id VARCHAR(255),

    -- Profile (metadata)
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),

    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending_verification',
    email_verified_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_check_auth_provider CHECK (
        auth_provider IN ('local', 'google', 'github')
    ),
    CONSTRAINT users_check_status CHECK (
        status IN ('active', 'suspended', 'pending_verification')
    ),
    CONSTRAINT users_check_local_password CHECK (
        auth_provider != 'local' OR password_hash IS NOT NULL
    )
);

-- Case-insensitive email lookup
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_oauth ON users(auth_provider, oauth_provider_id) WHERE oauth_provider_id IS NOT NULL;

COMMENT ON TABLE users IS 'Global user identity for SaaS platform';
COMMENT ON COLUMN users.auth_provider IS 'Primary authentication method: local, google, github';
COMMENT ON COLUMN users.status IS 'active=can login, pending_verification=needs email verify, suspended=blocked';

-- ============================================================================
-- 2. TENANTS TABLE (Updated)
-- ============================================================================

-- Note: If tenants table already exists from earlier migrations, alter it
-- For clean install, create fresh

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL,

    -- Ownership
    owner_user_id UUID REFERENCES users(user_id),

    -- Subscription
    plan VARCHAR(20) NOT NULL DEFAULT 'free',

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    trial_ends_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT tenants_slug_unique UNIQUE (slug),
    CONSTRAINT tenants_check_plan CHECK (
        plan IN ('free', 'starter', 'pro', 'enterprise')
    ),
    CONSTRAINT tenants_check_status CHECK (
        status IN ('active', 'suspended', 'trial')
    ),
    CONSTRAINT tenants_check_slug_format CHECK (
        slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' AND
        LENGTH(slug) >= 3 AND
        LENGTH(slug) <= 50
    )
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_owner ON tenants(owner_user_id);
CREATE INDEX idx_tenants_plan ON tenants(plan);

COMMENT ON TABLE tenants IS 'Organization/workspace boundary for multi-tenancy';
COMMENT ON COLUMN tenants.slug IS 'URL-safe identifier, must be globally unique';

-- ============================================================================
-- 3. TENANT MEMBERSHIPS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_memberships (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Role
    role VARCHAR(20) NOT NULL DEFAULT 'member',

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'invited',
    invited_by_user_id UUID REFERENCES users(user_id),
    invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Primary key
    PRIMARY KEY (user_id, tenant_id),

    -- Constraints
    CONSTRAINT memberships_check_role CHECK (
        role IN ('owner', 'admin', 'member', 'viewer')
    ),
    CONSTRAINT memberships_check_status CHECK (
        status IN ('active', 'invited', 'suspended')
    )
);

CREATE INDEX idx_memberships_user ON tenant_memberships(user_id);
CREATE INDEX idx_memberships_tenant ON tenant_memberships(tenant_id);
CREATE INDEX idx_memberships_role ON tenant_memberships(tenant_id, role);

-- Enforce exactly one owner per tenant
CREATE UNIQUE INDEX idx_memberships_owner ON tenant_memberships(tenant_id)
    WHERE role = 'owner';

COMMENT ON TABLE tenant_memberships IS 'User-to-tenant relationship with roles';
COMMENT ON COLUMN tenant_memberships.role IS 'owner=full control, admin=manage members, member=standard access, viewer=read-only';

-- ============================================================================
-- 4. PROJECTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Identity
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL,
    description TEXT,

    -- Environment
    environment VARCHAR(20) NOT NULL DEFAULT 'production',

    -- Default flag
    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT projects_tenant_slug_unique UNIQUE (tenant_id, slug),
    CONSTRAINT projects_check_environment CHECK (
        environment IN ('production', 'staging', 'development')
    ),
    CONSTRAINT projects_check_slug_format CHECK (
        slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' AND
        LENGTH(slug) >= 3 AND
        LENGTH(slug) <= 50
    )
);

CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_projects_environment ON projects(tenant_id, environment);

-- Enforce exactly one default project per tenant
CREATE UNIQUE INDEX idx_projects_default ON projects(tenant_id)
    WHERE is_default = TRUE;

COMMENT ON TABLE projects IS 'Sub-workspace within tenant for resource isolation';
COMMENT ON COLUMN projects.is_default IS 'Each tenant has exactly one default project';

-- ============================================================================
-- 5. AUTH TOKENS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token details
    token_hash VARCHAR(255) NOT NULL,
    token_type VARCHAR(30) NOT NULL,

    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT auth_tokens_check_type CHECK (
        token_type IN ('email_verification', 'password_reset', 'refresh', 'invitation')
    )
);

CREATE INDEX idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_type ON auth_tokens(token_type, expires_at);
CREATE INDEX idx_auth_tokens_hash ON auth_tokens(token_hash);

COMMENT ON TABLE auth_tokens IS 'Verification, reset, and refresh tokens';
COMMENT ON COLUMN auth_tokens.token_hash IS 'SHA256 hash of actual token for security';

-- ============================================================================
-- 6. TOKEN BLACKLIST TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS token_blacklist (
    jti VARCHAR(100) PRIMARY KEY,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blacklist_expires ON token_blacklist(expires_at);

COMMENT ON TABLE token_blacklist IS 'Revoked JWT tokens (for logout)';

-- ============================================================================
-- 7. SUBSCRIPTION PLANS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscription_plans (
    plan_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,

    -- Pricing
    price_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
    billing_interval VARCHAR(10) NOT NULL DEFAULT 'month',

    -- Limits
    max_projects INTEGER,
    max_decisions_per_month INTEGER,
    max_team_members INTEGER,
    max_rules INTEGER,
    audit_retention_days INTEGER NOT NULL DEFAULT 30,

    -- Features
    features JSONB NOT NULL DEFAULT '{}',

    -- Trial
    trial_days INTEGER NOT NULL DEFAULT 0,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE subscription_plans IS 'Subscription plan definitions (Free, Starter, Pro, Enterprise)';

-- Seed default plans
INSERT INTO subscription_plans (plan_id, name, price_cents, max_projects, max_decisions_per_month, max_team_members, max_rules, audit_retention_days, trial_days, features, display_order) VALUES
    ('free', 'Free', 0, 1, 1000, 3, 10, 30, 0, '{"api_access": false, "sso": false}', 1),
    ('starter', 'Starter', 29000000, 5, 10000, 10, 50, 90, 14, '{"api_access": true, "sso": false}', 2),
    ('pro', 'Pro', 99000000, NULL, 100000, 50, NULL, 365, 14, '{"api_access": true, "sso": false, "priority_support": true, "sla_guarantee": true}', 3),
    ('enterprise', 'Enterprise', 0, NULL, NULL, NULL, NULL, 730, 0, '{"api_access": true, "sso": true, "priority_support": true, "dedicated_support": true, "sla_guarantee": true, "custom_branding": true}', 4)
ON CONFLICT (plan_id) DO UPDATE SET
    name = EXCLUDED.name,
    price_cents = EXCLUDED.price_cents,
    max_projects = EXCLUDED.max_projects,
    max_decisions_per_month = EXCLUDED.max_decisions_per_month,
    max_team_members = EXCLUDED.max_team_members,
    max_rules = EXCLUDED.max_rules,
    audit_retention_days = EXCLUDED.audit_retention_days,
    trial_days = EXCLUDED.trial_days,
    features = EXCLUDED.features,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

-- ============================================================================
-- 8. SUBSCRIPTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Plan
    plan_id VARCHAR(20) NOT NULL REFERENCES subscription_plans(plan_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Payment provider
    payment_provider VARCHAR(20) NOT NULL DEFAULT 'manual',
    provider_subscription_id VARCHAR(255),

    -- Billing period
    current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    current_period_end TIMESTAMPTZ NOT NULL,

    -- Trial
    trial_end_at TIMESTAMPTZ,

    -- Cancellation
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,

    -- Usage (denormalized)
    decisions_this_month INTEGER NOT NULL DEFAULT 0,
    usage_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT subscriptions_tenant_unique UNIQUE (tenant_id),
    CONSTRAINT subscriptions_check_status CHECK (
        status IN ('trialing', 'active', 'past_due', 'cancelled', 'paused')
    )
);

CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

COMMENT ON TABLE subscriptions IS 'Tenant subscription for billing';

-- ============================================================================
-- 9. INVOICES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id),

    -- Invoice details
    invoice_number VARCHAR(50) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR',

    -- Line items
    line_items JSONB NOT NULL DEFAULT '[]',

    -- Tax
    tax_rate DECIMAL(5,4) NOT NULL DEFAULT 0,
    tax_amount_cents INTEGER NOT NULL DEFAULT 0,
    total_cents INTEGER NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    -- Payment provider
    payment_provider VARCHAR(20) NOT NULL DEFAULT 'midtrans',
    provider_invoice_id VARCHAR(255),
    provider_payment_id VARCHAR(255),

    -- Dates
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT invoices_number_unique UNIQUE (invoice_number),
    CONSTRAINT invoices_check_status CHECK (
        status IN ('draft', 'pending', 'paid', 'failed', 'cancelled', 'refunded')
    )
);

CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);

COMMENT ON TABLE invoices IS 'Payment invoices for subscriptions';

-- ============================================================================
-- 10. PAYMENT METHODS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS payment_methods (
    payment_method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Provider
    payment_provider VARCHAR(20) NOT NULL DEFAULT 'midtrans',
    provider_method_id VARCHAR(255),

    -- Type
    type VARCHAR(30) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',

    -- Default flag
    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT payment_methods_check_type CHECK (
        type IN ('card', 'bank_transfer', 'gopay', 'ovo', 'dana', 'shopeepay')
    )
);

CREATE INDEX idx_payment_methods_tenant ON payment_methods(tenant_id);

-- Only one default per tenant
CREATE UNIQUE INDEX idx_payment_methods_default ON payment_methods(tenant_id)
    WHERE is_default = TRUE;

COMMENT ON TABLE payment_methods IS 'Saved payment methods for recurring billing';

-- ============================================================================
-- 11. ADD PROJECT_ID TO EXISTING TABLES (if they exist)
-- ============================================================================

-- Add project_id to decisions (required)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'decisions') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'decisions' AND column_name = 'project_id') THEN
            ALTER TABLE decisions ADD COLUMN project_id UUID REFERENCES projects(project_id);
            CREATE INDEX idx_decisions_project ON decisions(tenant_id, project_id);
            COMMENT ON COLUMN decisions.project_id IS 'Project scope for decision (required for new records)';
        END IF;
    END IF;
END $$;

-- Add project_id to workflows (required)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflows') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'workflows' AND column_name = 'project_id') THEN
            ALTER TABLE workflows ADD COLUMN project_id UUID REFERENCES projects(project_id);
            CREATE INDEX idx_workflows_project ON workflows(tenant_id, project_id);
            COMMENT ON COLUMN workflows.project_id IS 'Project scope for workflow (required for new records)';
        END IF;
    END IF;
END $$;

-- Add project_id to rules (nullable = tenant-level)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'rules') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rules' AND column_name = 'project_id') THEN
            ALTER TABLE rules ADD COLUMN project_id UUID REFERENCES projects(project_id);
            CREATE INDEX idx_rules_project ON rules(tenant_id, project_id);
            COMMENT ON COLUMN rules.project_id IS 'Project scope for rule (NULL = tenant-level, shared across projects)';
        END IF;
    END IF;
END $$;

-- Add project_id to event_log (required)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'event_log') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'event_log' AND column_name = 'project_id') THEN
            ALTER TABLE event_log ADD COLUMN project_id UUID REFERENCES projects(project_id);
            CREATE INDEX idx_events_project ON event_log(tenant_id, project_id);
            COMMENT ON COLUMN event_log.project_id IS 'Project scope for event (required for new records)';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- 12. TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all new tables
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY['users', 'tenants', 'tenant_memberships', 'projects', 'subscriptions', 'invoices', 'payment_methods', 'subscription_plans'])
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trigger_update_%s_updated_at ON %I', tbl, tbl);
        EXECUTE format('CREATE TRIGGER trigger_update_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', tbl, tbl);
    END LOOP;
END $$;

-- ============================================================================
-- 13. GRANTS (for app_runtime_role)
-- ============================================================================

-- Grant permissions to app_runtime_role if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON users TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_memberships TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON auth_tokens TO app_runtime_role;
        GRANT SELECT, INSERT, DELETE ON token_blacklist TO app_runtime_role;
        GRANT SELECT ON subscription_plans TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE ON invoices TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON payment_methods TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ATLAS_PUGUH SaaS Platform - Migration 007: Identity & Auth tables created';
