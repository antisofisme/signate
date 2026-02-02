-- ============================================================================
-- ARSAKA_PUGUH Phase A - Seed Data
-- ============================================================================
-- Description: Minimal test data for Phase A visibility and debugging
-- Tenant: Single tenant (550e8400-e29b-41d4-a716-446655440000)
-- Users: Hardcoded in JWT (no users table)
--   - admin@example.com (admin role)
--   - approver@example.com (approver role)
-- Date: 2026-01-09
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- CONSTANTS FOR PHASE A
-- ----------------------------------------------------------------------------

-- Hardcoded tenant ID (matches .env ALLOWED_TENANT_IDS)
-- UUID: 550e8400-e29b-41d4-a716-446655440000

-- Hardcoded user IDs (for JWT claims, not in database)
-- Admin: user-admin-001
-- Approver: user-approver-001

-- ----------------------------------------------------------------------------
-- SEED DATA: Rules (Governance Policies)
-- ----------------------------------------------------------------------------

-- Rule 1: Auto-approve small expenses (< $100)
INSERT INTO rules (
  tenant_id,
  rule_name,
  decision_type,
  conditions,
  action,
  version,
  status,
  evaluation_sequence,
  created_at,
  updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Auto-approve small expenses',
  'expense.approval',
  '{"amount": {"operator": "less_than", "value": 100}}',
  '{"outcome": "ALLOWED", "reason": "Auto-approved: amount under $100"}',
  '1.0',
  'ACTIVE',
  10,
  NOW(),
  NOW()
);

-- Rule 2: Require approval for medium expenses ($100 - $1000)
INSERT INTO rules (
  tenant_id,
  rule_name,
  decision_type,
  conditions,
  action,
  version,
  status,
  evaluation_sequence,
  created_at,
  updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Require approval for medium expenses',
  'expense.approval',
  '{
    "amount": {
      "operator": "between",
      "min": 100,
      "max": 1000
    }
  }',
  '{
    "outcome": "REQUIRE_APPROVAL",
    "approver_role": "finance_manager",
    "timeout_hours": 72
  }',
  '1.0',
  'ACTIVE',
  20,
  NOW(),
  NOW()
);

-- Rule 3: Deny large expenses (> $1000) - requires CFO approval in Phase B
INSERT INTO rules (
  tenant_id,
  rule_name,
  decision_type,
  conditions,
  action,
  version,
  status,
  evaluation_sequence,
  created_at,
  updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Require CFO approval for large expenses',
  'expense.approval',
  '{"amount": {"operator": "greater_than_or_equal", "value": 1000}}',
  '{
    "outcome": "REQUIRE_APPROVAL",
    "approver_role": "CFO",
    "timeout_hours": 168
  }',
  '1.0',
  'ACTIVE',
  30,
  NOW(),
  NOW()
);

-- Rule 4: Purchase Order Approval (Example for multi-condition rule)
INSERT INTO rules (
  tenant_id,
  rule_name,
  decision_type,
  conditions,
  action,
  version,
  status,
  evaluation_sequence,
  created_at,
  updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Purchase order requires approval',
  'purchase_order.approval',
  '{
    "total_amount": {"operator": "greater_than", "value": 500},
    "vendor_verified": {"operator": "equals", "value": false}
  }',
  '{
    "outcome": "REQUIRE_APPROVAL",
    "approver_role": "procurement_manager",
    "timeout_hours": 48
  }',
  '1.0',
  'ACTIVE',
  10,
  NOW(),
  NOW()
);

-- ----------------------------------------------------------------------------
-- SEED DATA: Sample Decisions (For Testing)
-- ----------------------------------------------------------------------------

-- Sample Decision 1: Auto-approved expense (small amount)
INSERT INTO decisions (
  tenant_id,
  decision_type,
  context,
  outcome,
  rule_matched_id,
  rule_version,
  latency_ms,
  created_at,
  metadata
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'expense.approval',
  '{
    "amount": 50,
    "description": "Office supplies",
    "department": "engineering",
    "requester": "user-admin-001"
  }',
  'ALLOWED',
  (SELECT rule_id FROM rules WHERE rule_name = 'Auto-approve small expenses' LIMIT 1),
  '1.0',
  12,
  NOW(),
  '{
    "trace_id": "test-trace-001",
    "requester_user_id": "user-admin-001",
    "source": "phase_a_seed_data"
  }'
);

-- Sample Decision 2: Requires approval (medium amount)
INSERT INTO decisions (
  tenant_id,
  decision_type,
  context,
  outcome,
  rule_matched_id,
  rule_version,
  approval_workflow_id,
  latency_ms,
  created_at,
  metadata
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'expense.approval',
  '{
    "amount": 500,
    "description": "New laptop",
    "department": "engineering",
    "requester": "user-admin-001"
  }',
  'REQUIRE_APPROVAL',
  (SELECT rule_id FROM rules WHERE rule_name = 'Require approval for medium expenses' LIMIT 1),
  '1.0',
  uuid_generate_v4(),
  15,
  NOW(),
  '{
    "trace_id": "test-trace-002",
    "requester_user_id": "user-admin-001",
    "source": "phase_a_seed_data"
  }'
);

-- ----------------------------------------------------------------------------
-- SEED DATA: Sample Workflow (Pending Approval)
-- ----------------------------------------------------------------------------

-- Workflow for Decision 2 (pending approval)
INSERT INTO workflows (
  decision_id,
  tenant_id,
  current_state,
  approver_role,
  escalation_timeout_at,
  created_at,
  metadata
) SELECT
  d.decision_id,
  '550e8400-e29b-41d4-a716-446655440000',
  'PENDING_APPROVAL',
  'finance_manager',
  NOW() + INTERVAL '72 hours',
  NOW(),
  '{
    "trace_id": "test-trace-002",
    "escalation_enabled": true
  }'
FROM decisions d
WHERE d.context->>'description' = 'New laptop'
LIMIT 1;

-- ----------------------------------------------------------------------------
-- SEED DATA: Sample Events (Event Log)
-- ----------------------------------------------------------------------------

-- Event 1: Decision created (auto-approved)
INSERT INTO event_log (
  event_type,
  aggregate_id,
  aggregate_type,
  tenant_id,
  payload,
  occurred_at,
  recorded_at
) SELECT
  'decision.created',
  d.decision_id,
  'decision',
  '550e8400-e29b-41d4-a716-446655440000',
  jsonb_build_object(
    'outcome', 'ALLOWED',
    'amount', 50,
    'auto_approved', true
  ),
  d.created_at,
  NOW()
FROM decisions d
WHERE d.context->>'description' = 'Office supplies'
LIMIT 1;

-- Event 2: Workflow created
INSERT INTO event_log (
  event_type,
  aggregate_id,
  aggregate_type,
  tenant_id,
  payload,
  occurred_at,
  recorded_at
) SELECT
  'workflow.created',
  w.workflow_id,
  'workflow',
  '550e8400-e29b-41d4-a716-446655440000',
  jsonb_build_object(
    'state', 'PENDING_APPROVAL',
    'approver_role', 'finance_manager',
    'amount', 500
  ),
  w.created_at,
  NOW()
FROM workflows w
LIMIT 1;

-- ----------------------------------------------------------------------------
-- VERIFICATION QUERIES (For Testing)
-- ----------------------------------------------------------------------------

-- Verify seed data loaded
DO $$
DECLARE
  rule_count INTEGER;
  decision_count INTEGER;
  workflow_count INTEGER;
  event_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO rule_count FROM rules WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
  SELECT COUNT(*) INTO decision_count FROM decisions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
  SELECT COUNT(*) INTO workflow_count FROM workflows WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
  SELECT COUNT(*) INTO event_count FROM event_log WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';

  RAISE NOTICE '✅ Phase A Seed Data Loaded:';
  RAISE NOTICE '   - Rules: %', rule_count;
  RAISE NOTICE '   - Decisions: %', decision_count;
  RAISE NOTICE '   - Workflows: %', workflow_count;
  RAISE NOTICE '   - Events: %', event_count;
END $$;

COMMIT;

-- ============================================================================
-- PHASE A TEST CREDENTIALS
-- ============================================================================
--
-- Authentication: JWT tokens with hardcoded claims (no users table)
--
-- Admin User (for testing):
--   user_id: "user-admin-001"
--   email: "admin@example.com"
--   role: "admin"
--   tenant_id: "550e8400-e29b-41d4-a716-446655440000"
--
-- Approver User (for testing):
--   user_id: "user-approver-001"
--   email: "approver@example.com"
--   role: "finance_manager"
--   tenant_id: "550e8400-e29b-41d4-a716-446655440000"
--
-- JWT Generation:
--   Use JWT_SECRET_KEY from .env
--   Algorithm: HS256
--   Expiration: 60 minutes
--
-- ============================================================================
-- END OF PHASE A SEED DATA
-- ============================================================================
