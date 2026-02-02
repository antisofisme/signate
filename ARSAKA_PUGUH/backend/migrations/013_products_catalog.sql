-- ============================================================================
-- Migration 013: Products Catalog & Product Subscriptions
-- ============================================================================
-- Source: PLATFORM_ARCHITECTURE.md - Product Switcher
--
-- This migration creates:
-- 1. products - Product catalog (MANTRA, future products)
-- 2. product_subscriptions - Tenant subscriptions to products
-- ============================================================================

-- ============================================================================
-- 1. PRODUCTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    code VARCHAR(50) NOT NULL,          -- "mantra", "future_product"
    name VARCHAR(100) NOT NULL,         -- "MANTRA"
    description TEXT,
    tagline VARCHAR(200),               -- Short tagline for cards

    -- Visual
    icon_url VARCHAR(500),              -- Product icon
    logo_url VARCHAR(500),              -- Full logo
    color_primary VARCHAR(7),           -- Hex color (#2563EB)
    color_secondary VARCHAR(7),

    -- URLs
    app_url VARCHAR(500),               -- Product app URL
    docs_url VARCHAR(500),              -- Documentation URL
    support_url VARCHAR(500),           -- Support URL

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,

    -- Features (JSON)
    features JSONB NOT NULL DEFAULT '{}',

    -- Display
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT products_code_unique UNIQUE (code),
    CONSTRAINT products_check_status CHECK (
        status IN ('active', 'coming_soon', 'beta', 'deprecated', 'disabled')
    ),
    CONSTRAINT products_check_code_format CHECK (
        code ~ '^[a-z][a-z0-9_]*$' AND
        LENGTH(code) >= 2 AND
        LENGTH(code) <= 50
    )
);

CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_display ON products(display_order, status);

COMMENT ON TABLE products IS 'Product catalog for PUGUH platform';
COMMENT ON COLUMN products.code IS 'Unique lowercase identifier for the product';
COMMENT ON COLUMN products.status IS 'active=available, coming_soon=announced, beta=beta testers, deprecated=no new subs, disabled=hidden';

-- ============================================================================
-- 2. PRODUCT SUBSCRIPTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,

    -- Denormalized for quick lookup
    product_code VARCHAR(50) NOT NULL,

    -- Plan (references subscription_plans.plan_id)
    plan_id VARCHAR(20) NOT NULL DEFAULT 'free',

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Trial
    trial_ends_at TIMESTAMPTZ,
    is_trial BOOLEAN NOT NULL DEFAULT FALSE,

    -- Billing period
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,

    -- Usage tracking
    usage_this_period INTEGER NOT NULL DEFAULT 0,
    usage_limit INTEGER,  -- NULL = unlimited

    -- Cancellation
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT product_subs_tenant_product_unique UNIQUE (tenant_id, product_id),
    CONSTRAINT product_subs_check_status CHECK (
        status IN ('active', 'trialing', 'cancelled', 'expired', 'suspended')
    )
);

CREATE INDEX idx_product_subs_tenant ON product_subscriptions(tenant_id);
CREATE INDEX idx_product_subs_product ON product_subscriptions(product_id);
CREATE INDEX idx_product_subs_status ON product_subscriptions(tenant_id, status);
CREATE INDEX idx_product_subs_code ON product_subscriptions(tenant_id, product_code);

COMMENT ON TABLE product_subscriptions IS 'Tenant subscriptions to products';
COMMENT ON COLUMN product_subscriptions.product_code IS 'Denormalized product code for quick lookup without join';

-- ============================================================================
-- 3. SEED MANTRA PRODUCT
-- ============================================================================

INSERT INTO products (
    product_id,
    code,
    name,
    description,
    tagline,
    color_primary,
    status,
    is_featured,
    features,
    display_order
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'mantra',
    'MANTRA',
    'Decision Governance Platform - Record, validate, and enforce architectural decisions using constitutional law principles.',
    'Constitutional Law for Software Decisions',
    '#2563EB',
    'active',
    true,
    '{"mcp_integration": true, "api_access": true, "webhooks": true}'::jsonb,
    1
) ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    tagline = EXCLUDED.tagline,
    color_primary = EXCLUDED.color_primary,
    status = EXCLUDED.status,
    is_featured = EXCLUDED.is_featured,
    features = EXCLUDED.features,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

-- ============================================================================
-- 4. TRIGGERS FOR UPDATED_AT
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_update_products_updated_at ON products;
CREATE TRIGGER trigger_update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_product_subs_updated_at ON product_subscriptions;
CREATE TRIGGER trigger_update_product_subs_updated_at
    BEFORE UPDATE ON product_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. GRANTS (for app_runtime_role)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT ON products TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON product_subscriptions TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- 6. AUTO-SUBSCRIBE NEW TENANTS TO FREE MANTRA
-- ============================================================================

-- Function to auto-subscribe new tenant to free MANTRA
CREATE OR REPLACE FUNCTION auto_subscribe_mantra()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO product_subscriptions (
        tenant_id,
        product_id,
        product_code,
        plan_id,
        status,
        current_period_start
    ) VALUES (
        NEW.tenant_id,
        '00000000-0000-0000-0000-000000000001',
        'mantra',
        'free',
        'active',
        NOW()
    ) ON CONFLICT (tenant_id, product_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-subscribe on tenant creation
DROP TRIGGER IF EXISTS trigger_auto_subscribe_mantra ON tenants;
CREATE TRIGGER trigger_auto_subscribe_mantra
    AFTER INSERT ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION auto_subscribe_mantra();

-- ============================================================================
-- 7. SUBSCRIBE EXISTING TENANTS TO FREE MANTRA
-- ============================================================================

-- Auto-subscribe existing tenants that don't have MANTRA subscription
INSERT INTO product_subscriptions (
    tenant_id,
    product_id,
    product_code,
    plan_id,
    status,
    current_period_start
)
SELECT
    t.tenant_id,
    '00000000-0000-0000-0000-000000000001',
    'mantra',
    'free',
    'active',
    NOW()
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM product_subscriptions ps
    WHERE ps.tenant_id = t.tenant_id
    AND ps.product_code = 'mantra'
)
ON CONFLICT (tenant_id, product_id) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ARSAKA_PUGUH SaaS Platform - Migration 013: Products catalog and product subscriptions';
