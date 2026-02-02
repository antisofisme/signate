-- Migration: 005
-- Description: Add Configuration master data tables and governance features
-- Date: 2026-01-11
-- Purpose: Implement customer-defined master data and rule lifecycle governance

BEGIN;

-- ============================================================================
-- CONFIGURATION MASTER DATA TABLES
-- ============================================================================

-- Functional Areas (Customer-Defined)
-- Purpose: UI grouping, governance boundary, NOT for decision evaluation
CREATE TABLE IF NOT EXISTS functional_areas (
    functional_area_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    -- Master data
    code VARCHAR(50) NOT NULL,  -- e.g., "FINANCE", "HR", "IT"
    name VARCHAR(200) NOT NULL,  -- e.g., "Finance & Accounting"
    description TEXT,

    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Audit trail
    created_by_id UUID,
    updated_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_functional_area_code_tenant UNIQUE (tenant_id, code)
);

CREATE INDEX idx_functional_areas_tenant ON functional_areas(tenant_id);
CREATE INDEX idx_functional_areas_active ON functional_areas(is_active);

COMMENT ON TABLE functional_areas IS 'Customer-defined functional areas for UI grouping and governance (NOT for decision logic)';
COMMENT ON COLUMN functional_areas.code IS 'Unique code within tenant (uppercase, snake_case)';


-- Decision Types (System-Defined Contracts)
-- Purpose: Runtime evaluation contracts, hard-coded in backend
CREATE TABLE IF NOT EXISTS decision_types (
    decision_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    -- Contract definition
    type_code VARCHAR(100) NOT NULL,  -- e.g., "purchase_request"
    type_name VARCHAR(200) NOT NULL,  -- e.g., "Purchase Request"
    description TEXT,

    -- Schema definition (JSON Schema for context validation)
    context_schema JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Metadata
    is_system_defined BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = cannot delete
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit trail
    created_by_id UUID,
    updated_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_decision_type_code_tenant UNIQUE (tenant_id, type_code)
);

CREATE INDEX idx_decision_types_tenant ON decision_types(tenant_id);
CREATE INDEX idx_decision_types_active ON decision_types(is_active);

COMMENT ON TABLE decision_types IS 'System-defined decision type contracts (runtime evaluation)';
COMMENT ON COLUMN decision_types.is_system_defined IS 'System-defined types cannot be deleted';


-- Approver Roles (Customer-Defined)
-- Purpose: Role definitions for approval workflows
CREATE TABLE IF NOT EXISTS approver_roles (
    approver_role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    -- Role definition
    role_code VARCHAR(100) NOT NULL,  -- e.g., "finance_manager"
    role_name VARCHAR(200) NOT NULL,  -- e.g., "Finance Manager"
    description TEXT,

    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Audit trail
    created_by_id UUID,
    updated_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_approver_role_code_tenant UNIQUE (tenant_id, role_code)
);

CREATE INDEX idx_approver_roles_tenant ON approver_roles(tenant_id);
CREATE INDEX idx_approver_roles_active ON approver_roles(is_active);

COMMENT ON TABLE approver_roles IS 'Customer-defined approver role definitions';


-- ============================================================================
-- GOVERNANCE: Rule Status Changes Audit
-- ============================================================================

CREATE TABLE IF NOT EXISTS rule_status_changes (
    change_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES rules(rule_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,

    -- Status transition
    old_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,

    -- MANDATORY: Change reason
    change_reason TEXT NOT NULL CHECK (length(trim(change_reason)) > 0),

    -- Audit
    changed_by_id UUID,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rule_status_changes_rule ON rule_status_changes(rule_id);
CREATE INDEX idx_rule_status_changes_tenant ON rule_status_changes(tenant_id);
CREATE INDEX idx_rule_status_changes_date ON rule_status_changes(changed_at DESC);

COMMENT ON TABLE rule_status_changes IS 'Audit trail for rule status transitions with mandatory change_reason';
COMMENT ON COLUMN rule_status_changes.change_reason IS 'MANDATORY: Why this status change happened (governance requirement)';


-- ============================================================================
-- ALTER EXISTING TABLES
-- ============================================================================

-- Add functional_area to rules (governance only, NOT for evaluation)
ALTER TABLE rules
ADD COLUMN IF NOT EXISTS functional_area_id UUID REFERENCES functional_areas(functional_area_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_rules_functional_area ON rules(functional_area_id);

COMMENT ON COLUMN rules.functional_area_id IS 'UI grouping and governance boundary (NOT used in decision evaluation)';


-- Add evaluation_trace to decisions (explainability)
ALTER TABLE decisions
ADD COLUMN IF NOT EXISTS evaluation_trace JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN decisions.evaluation_trace IS 'Step-by-step rule evaluation trace for explainability';


-- ============================================================================
-- SEED DATA: System-Defined Decision Types
-- ============================================================================

INSERT INTO decision_types (tenant_id, type_code, type_name, description, is_system_defined, context_schema)
VALUES
    (
        '550e8400-e29b-41d4-a716-446655440000',
        'purchase_request',
        'Purchase Request',
        'Financial purchase approval workflow',
        TRUE,
        '{
            "type": "object",
            "required": ["amount"],
            "properties": {
                "amount": {"type": "number", "minimum": 0},
                "item": {"type": "string"},
                "vendor": {"type": "string"}
            }
        }'::jsonb
    ),
    (
        '550e8400-e29b-41d4-a716-446655440000',
        'leave_request',
        'Leave Request',
        'Employee leave approval workflow',
        TRUE,
        '{
            "type": "object",
            "required": ["days", "leave_type"],
            "properties": {
                "days": {"type": "integer", "minimum": 1},
                "leave_type": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            }
        }'::jsonb
    ),
    (
        '550e8400-e29b-41d4-a716-446655440000',
        'access_request',
        'Access Request',
        'System/resource access approval workflow',
        TRUE,
        '{
            "type": "object",
            "required": ["resource", "access_level"],
            "properties": {
                "resource": {"type": "string"},
                "access_level": {"type": "string"},
                "justification": {"type": "string"}
            }
        }'::jsonb
    )
ON CONFLICT (tenant_id, type_code) DO NOTHING;


-- ============================================================================
-- SEED DATA: Default Functional Areas
-- ============================================================================

INSERT INTO functional_areas (tenant_id, code, name, description, display_order)
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'FINANCE', 'Finance & Accounting', 'Financial operations and accounting policies', 1),
    ('550e8400-e29b-41d4-a716-446655440000', 'HR', 'Human Resources', 'Employee management and HR policies', 2),
    ('550e8400-e29b-41d4-a716-446655440000', 'IT', 'Information Technology', 'IT systems and security policies', 3),
    ('550e8400-e29b-41d4-a716-446655440000', 'PROCUREMENT', 'Procurement', 'Purchasing and vendor management', 4),
    ('550e8400-e29b-41d4-a716-446655440000', 'OPERATIONS', 'Operations', 'Operational policies and procedures', 5)
ON CONFLICT (tenant_id, code) DO NOTHING;


-- ============================================================================
-- SEED DATA: Default Approver Roles
-- ============================================================================

INSERT INTO approver_roles (tenant_id, role_code, role_name, description, display_order)
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'finance_manager', 'Finance Manager', 'Financial approval authority', 1),
    ('550e8400-e29b-41d4-a716-446655440000', 'cfo', 'Chief Financial Officer', 'Executive financial approval authority', 2),
    ('550e8400-e29b-41d4-a716-446655440000', 'department_manager', 'Department Manager', 'Departmental approval authority', 3),
    ('550e8400-e29b-41d4-a716-446655440000', 'it_security', 'IT Security Team', 'Security and access approval authority', 4),
    ('550e8400-e29b-41d4-a716-446655440000', 'hr_manager', 'HR Manager', 'Human resources approval authority', 5)
ON CONFLICT (tenant_id, role_code) DO NOTHING;

COMMIT;
