-- ============================================================================
-- Migration 009: Billing Tables
-- ============================================================================
-- Creates tables for subscription billing and payment processing:
-- 1. subscription_plans - Plan definitions (Free, Starter, Pro, Enterprise)
-- 2. subscriptions - Tenant subscriptions
-- 3. invoices - Payment invoices
-- 4. payment_methods - Stored payment methods
-- 5. webhook_logs - Midtrans webhook audit trail
-- ============================================================================

-- ============================================================================
-- 1. SUBSCRIPTION PLANS
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscription_plans (
    plan_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,

    -- Pricing
    price_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
    billing_interval VARCHAR(10) NOT NULL DEFAULT 'month',

    -- Limits (NULL = unlimited)
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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_billing_interval CHECK (
        billing_interval IN ('month', 'year')
    )
);

-- Seed initial plans
INSERT INTO subscription_plans (plan_id, name, price_cents, max_projects, max_decisions_per_month, max_team_members, max_rules, audit_retention_days, trial_days, features, display_order)
VALUES
    ('free', 'Free', 0, 1, 1000, 3, 10, 30, 0, '{"api_access": false, "sso": false}', 1),
    ('starter', 'Starter', 29000000, 5, 10000, 10, 50, 90, 14, '{"api_access": true, "sso": false}', 2),
    ('pro', 'Pro', 99000000, NULL, 100000, 50, NULL, 365, 14, '{"api_access": true, "sso": false, "priority_support": true, "sla_guarantee": true}', 3),
    ('enterprise', 'Enterprise', 0, NULL, NULL, NULL, NULL, 730, 0, '{"api_access": true, "sso": true, "priority_support": true, "dedicated_support": true, "sla_guarantee": true, "custom_branding": true}', 4)
ON CONFLICT (plan_id) DO NOTHING;

-- ============================================================================
-- 2. SUBSCRIPTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(tenant_id) ON DELETE CASCADE,

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

    -- Usage (denormalized for quick checks)
    decisions_this_month INTEGER NOT NULL DEFAULT 0,
    usage_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Scheduled plan change
    scheduled_plan_id VARCHAR(20) REFERENCES subscription_plans(plan_id),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_subscription_status CHECK (
        status IN ('trialing', 'active', 'past_due', 'cancelled', 'paused')
    )
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan_id);

-- ============================================================================
-- 3. INVOICES
-- ============================================================================

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id),

    -- Invoice details
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
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
    snap_token VARCHAR(255),
    snap_redirect_url TEXT,

    -- Dates
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_invoice_status CHECK (
        status IN ('draft', 'pending', 'paid', 'failed', 'cancelled', 'refunded')
    )
);

CREATE INDEX IF NOT EXISTS idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);

-- ============================================================================
-- 4. PAYMENT METHODS
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

    -- Default
    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_payment_type CHECK (
        type IN ('card', 'bank_transfer', 'gopay', 'ovo', 'dana', 'shopeepay')
    )
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_tenant ON payment_methods(tenant_id);

-- Only one default per tenant
CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_methods_default ON payment_methods(tenant_id)
    WHERE is_default = TRUE;

-- ============================================================================
-- 5. WEBHOOK LOGS (Audit Trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source
    provider VARCHAR(20) NOT NULL,

    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'POST',
    headers JSONB,
    payload JSONB NOT NULL,

    -- Extracted data
    order_id VARCHAR(255),
    transaction_status VARCHAR(50),
    transaction_id VARCHAR(255),

    -- Verification
    signature_valid BOOLEAN,
    verification_error TEXT,

    -- Processing
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    process_error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_provider ON webhook_logs(provider);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_order_id ON webhook_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_created ON webhook_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_unprocessed ON webhook_logs(processed) WHERE processed = FALSE;

-- ============================================================================
-- 6. INVOICE NUMBER SEQUENCE
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START WITH 1;

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    seq_val INTEGER;
    year_part VARCHAR(4);
BEGIN
    SELECT nextval('invoice_number_seq') INTO seq_val;
    year_part := to_char(NOW(), 'YYYY');
    RETURN 'INV-' || year_part || '-' || LPAD(seq_val::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

-- Update timestamps
DROP TRIGGER IF EXISTS trigger_update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER trigger_update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_invoices_updated_at ON invoices;
CREATE TRIGGER trigger_update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_payment_methods_updated_at ON payment_methods;
CREATE TRIGGER trigger_update_payment_methods_updated_at
    BEFORE UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_subscription_plans_updated_at ON subscription_plans;
CREATE TRIGGER trigger_update_subscription_plans_updated_at
    BEFORE UPDATE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 8. GRANTS
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON subscriptions TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON invoices TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON payment_methods TO app_runtime_role;
        GRANT SELECT ON subscription_plans TO app_runtime_role;
        GRANT INSERT ON webhook_logs TO app_runtime_role;
        GRANT SELECT, UPDATE ON webhook_logs TO app_runtime_role;
        GRANT USAGE, SELECT ON SEQUENCE invoice_number_seq TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE subscription_plans IS 'Available subscription plans with pricing and limits';
COMMENT ON TABLE subscriptions IS 'Tenant subscriptions (one per tenant)';
COMMENT ON TABLE invoices IS 'Payment invoices with line items';
COMMENT ON TABLE payment_methods IS 'Stored payment methods for tenants';
COMMENT ON TABLE webhook_logs IS 'Audit trail for payment webhooks';

COMMENT ON COLUMN subscriptions.decisions_this_month IS 'Counter for usage metering, reset monthly';
COMMENT ON COLUMN subscriptions.scheduled_plan_id IS 'Plan to switch to at next billing cycle (for downgrades)';
COMMENT ON COLUMN invoices.snap_token IS 'Midtrans Snap token for payment popup';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ATLAS_PUGUH SaaS Platform - Migration 009: Billing tables';
