-- Migration: 005b (Corrective)
-- Description: Complete configuration master data tables (missing from 005 rollback)
-- Date: 2026-01-11
-- Author: ATLAS_PUGUH Team
--
-- Context: Migration 005 partially succeeded (functional_areas created), but rolled back
-- due to index conflict. This migration adds the remaining tables.

BEGIN;

-- ============================================================================
-- DECISION TYPES (System-Defined Contracts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_types (
    decision_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type_code VARCHAR(100) NOT NULL,
    type_name VARCHAR(200) NOT NULL,
    description TEXT,
    context_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_system_defined BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_id UUID,
    updated_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_decision_type_code_tenant UNIQUE (tenant_id, type_code)
);

CREATE INDEX IF NOT EXISTS idx_decision_types_tenant ON decision_types(tenant_id);
CREATE INDEX IF NOT EXISTS idx_decision_types_active ON decision_types(is_active);

COMMENT ON TABLE decision_types IS 'Decision type contracts that define context schema for rule evaluation';
COMMENT ON COLUMN decision_types.type_code IS 'Unique decision type code (e.g., PURCHASE_REQUEST)';
COMMENT ON COLUMN decision_types.context_schema IS 'JSON schema defining expected context fields for this decision type';
COMMENT ON COLUMN decision_types.is_system_defined IS 'TRUE if system-defined (protected from editing/deletion)';

-- ============================================================================
-- APPROVER ROLES (Customer-Defined)
-- ============================================================================

CREATE TABLE IF NOT EXISTS approver_roles (
    approver_role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    role_code VARCHAR(100) NOT NULL,
    role_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_by_id UUID,
    updated_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_approver_role_code_tenant UNIQUE (tenant_id, role_code)
);

CREATE INDEX IF NOT EXISTS idx_approver_roles_tenant ON approver_roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_approver_roles_active ON approver_roles(is_active);

COMMENT ON TABLE approver_roles IS 'Customer-defined approver roles used in approval workflow rules';
COMMENT ON COLUMN approver_roles.role_code IS 'Unique role code (e.g., CFO, CEO, MANAGER)';
COMMENT ON COLUMN approver_roles.display_order IS 'Display order for UI lists (lower = higher priority)';

-- ============================================================================
-- RULE STATUS CHANGES (Audit Trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rule_status_changes (
    change_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES rules(rule_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    old_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,
    change_reason TEXT NOT NULL CHECK (length(trim(change_reason)) > 0),
    changed_by_id UUID,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_status_changes_rule ON rule_status_changes(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_status_changes_tenant ON rule_status_changes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rule_status_changes_changed_at ON rule_status_changes(changed_at DESC);

COMMENT ON TABLE rule_status_changes IS 'Audit trail for rule status changes with mandatory change_reason';
COMMENT ON COLUMN rule_status_changes.change_reason IS 'MANDATORY: Explanation of why rule status changed';

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Seed Decision Types (System-Defined)
INSERT INTO decision_types (tenant_id, type_code, type_name, description, context_schema, is_system_defined, is_active)
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'PURCHASE_REQUEST', 'Purchase Request', 'Purchase request approval decision', '{"amount": "number", "category": "string", "vendor": "string"}'::jsonb, TRUE, TRUE),
    ('550e8400-e29b-41d4-a716-446655440000', 'LEAVE_REQUEST', 'Leave Request', 'Employee leave request decision', '{"days": "number", "leave_type": "string", "start_date": "string"}'::jsonb, TRUE, TRUE),
    ('550e8400-e29b-41d4-a716-446655440000', 'ACCESS_REQUEST', 'Access Request', 'System access request decision', '{"resource": "string", "permission_level": "string"}'::jsonb, TRUE, TRUE)
ON CONFLICT (tenant_id, type_code) DO NOTHING;

-- Seed Approver Roles
INSERT INTO approver_roles (tenant_id, role_code, role_name, description, is_active, display_order)
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'CEO', 'Chief Executive Officer', 'Top-level executive approval', TRUE, 1),
    ('550e8400-e29b-41d4-a716-446655440000', 'CFO', 'Chief Financial Officer', 'Financial approval authority', TRUE, 2),
    ('550e8400-e29b-41d4-a716-446655440000', 'MANAGER', 'Department Manager', 'Department-level approval', TRUE, 3),
    ('550e8400-e29b-41d4-a716-446655440000', 'SUPERVISOR', 'Supervisor', 'Team-level approval', TRUE, 4),
    ('550e8400-e29b-41d4-a716-446655440000', 'HR_HEAD', 'HR Department Head', 'HR-related approvals', TRUE, 5)
ON CONFLICT (tenant_id, role_code) DO NOTHING;

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables exist
\dt+ decision_types
\dt+ approver_roles
\dt+ rule_status_changes

-- Verify seed data
SELECT COUNT(*) AS decision_types_count FROM decision_types;
SELECT COUNT(*) AS approver_roles_count FROM approver_roles;
