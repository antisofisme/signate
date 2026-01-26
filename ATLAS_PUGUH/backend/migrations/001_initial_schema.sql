-- Migration: 001
-- Description: Initial schema creation for ATLAS_PUGUH Control Plane
-- Date: 2026-01-07
-- Phase: 1
-- Layer: 3 (Implementation)
-- Source: INFRA-LAY3-004 (Data Layer Implementation Standards)

-- =============================================================================
-- PHASE 1 INITIAL SCHEMA
-- =============================================================================

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE 1: decisions (Immutable)
-- =============================================================================

CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL,
  decision_type VARCHAR(256) NOT NULL,
  context JSONB NOT NULL,                    -- sanitized context snapshot
  outcome VARCHAR(32) NOT NULL,              -- ALLOWED, DENIED, REQUIRE_APPROVAL
  rule_matched_id UUID,                      -- which rule matched (nullable for default deny)
  rule_version VARCHAR(32),                  -- version of rule used (e.g., "1.0")
  approval_workflow_id UUID,                 -- link to workflow (if REQUIRE_APPROVAL)
  idempotency_key VARCHAR(256),              -- for deduplication
  latency_ms INTEGER,                        -- SDK → Core latency
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,  -- immutable, decided_at
  metadata JSONB,                            -- trace_id, requester_user_id, source
  archived_at TIMESTAMP WITH TIME ZONE,      -- when archived to warm storage
  archive_location VARCHAR(512),             -- URI to archived data

  -- Constraints
  CONSTRAINT outcome_valid CHECK (outcome IN ('ALLOWED', 'DENIED', 'REQUIRE_APPROVAL')),
  CONSTRAINT outcome_not_null CHECK (outcome IS NOT NULL),
  CONSTRAINT context_not_null CHECK (context IS NOT NULL),
  CONSTRAINT decision_type_not_empty CHECK (length(decision_type) > 0)
);

-- Indexes for decisions (MANDATORY per INFRA-LAY2-003)
CREATE INDEX idx_decisions_tenant_id ON decisions(tenant_id);
CREATE INDEX idx_decisions_tenant_decision_type ON decisions(tenant_id, decision_type);
CREATE INDEX idx_decisions_tenant_created_at ON decisions(tenant_id, created_at DESC);
CREATE INDEX idx_decisions_idempotency_key ON decisions(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Unique index for idempotency
CREATE UNIQUE INDEX idx_decisions_idempotency_unique ON decisions(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Comments
COMMENT ON TABLE decisions IS 'Immutable decision records - all governance decisions with outcome, context snapshot, and rule matched';
COMMENT ON COLUMN decisions.decision_id IS 'Unique decision identifier (UUID)';
COMMENT ON COLUMN decisions.tenant_id IS 'Tenant identifier for multi-tenancy isolation';
COMMENT ON COLUMN decisions.decision_type IS 'Type of decision (e.g., purchase_order.approval, expense.threshold_check)';
COMMENT ON COLUMN decisions.context IS 'Sanitized context snapshot at decision time (JSONB)';
COMMENT ON COLUMN decisions.outcome IS 'Decision outcome: ALLOWED, DENIED, or REQUIRE_APPROVAL';
COMMENT ON COLUMN decisions.rule_matched_id IS 'UUID of rule that matched (NULL for default deny)';
COMMENT ON COLUMN decisions.rule_version IS 'Version of rule used (e.g., "1.0")';
COMMENT ON COLUMN decisions.idempotency_key IS 'Application-provided idempotency key for deduplication';

-- =============================================================================
-- TABLE 2: workflows (Mutable until terminal state)
-- =============================================================================

CREATE TABLE workflows (
  workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  decision_id UUID NOT NULL,                 -- link to decision (immutable)
  tenant_id UUID NOT NULL,                   -- partition key
  current_state VARCHAR(32) NOT NULL,        -- PENDING_APPROVAL, APPROVED, REJECTED, DELEGATED, ESCALATED
  approver_role VARCHAR(256) NOT NULL,       -- role identifier (e.g., CFO)
  delegated_to_user_id UUID,                 -- if delegated
  escalated_to_user_id UUID,                 -- if escalated
  escalation_timeout_at TIMESTAMP WITH TIME ZONE,  -- when escalation triggers
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,     -- when terminal state reached
  metadata JSONB,                            -- trace_id, etc.

  -- Constraints
  CONSTRAINT state_valid CHECK (current_state IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'DELEGATED', 'ESCALATED')),
  CONSTRAINT decision_fk FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE RESTRICT,
  CONSTRAINT terminal_state_immutable CHECK (completed_at IS NULL OR current_state IN ('APPROVED', 'REJECTED')),
  CONSTRAINT approver_role_not_empty CHECK (length(approver_role) > 0)
);

-- Indexes for workflows (MANDATORY)
CREATE INDEX idx_workflows_tenant_id ON workflows(tenant_id);
CREATE INDEX idx_workflows_decision_id ON workflows(decision_id);
CREATE INDEX idx_workflows_tenant_decision_id ON workflows(tenant_id, decision_id);
CREATE INDEX idx_workflows_escalation_timeout ON workflows(tenant_id, escalation_timeout_at) WHERE escalation_timeout_at IS NOT NULL;

-- Comments
COMMENT ON TABLE workflows IS 'Mutable workflow records for approval processes - mutable until terminal state';
COMMENT ON COLUMN workflows.workflow_id IS 'Unique workflow identifier (UUID)';
COMMENT ON COLUMN workflows.decision_id IS 'Link to parent decision (immutable)';
COMMENT ON COLUMN workflows.current_state IS 'Current workflow state: PENDING_APPROVAL, APPROVED, REJECTED, DELEGATED, ESCALATED';
COMMENT ON COLUMN workflows.approver_role IS 'Role identifier for approver (e.g., CFO, manager.finance)';
COMMENT ON COLUMN workflows.completed_at IS 'Timestamp when workflow reached terminal state (APPROVED or REJECTED)';

-- =============================================================================
-- TABLE 3: workflow_transitions (Append-Only, Immutable)
-- =============================================================================

CREATE TABLE workflow_transitions (
  transition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL,                 -- link to workflow
  tenant_id UUID NOT NULL,                   -- partition key
  from_state VARCHAR(32) NOT NULL,
  to_state VARCHAR(32) NOT NULL,
  action VARCHAR(32),                        -- APPROVED, REJECTED, DELEGATED, ESCALATED
  acted_by_user_id UUID,                     -- who made change
  approver_role VARCHAR(256),                -- approver role
  comment TEXT,                              -- optional reason
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT workflow_fk FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE RESTRICT,
  CONSTRAINT from_state_not_empty CHECK (length(from_state) > 0),
  CONSTRAINT to_state_not_empty CHECK (length(to_state) > 0)
);

-- Indexes for workflow_transitions (MANDATORY)
CREATE INDEX idx_workflow_transitions_workflow_id ON workflow_transitions(workflow_id);
CREATE INDEX idx_workflow_transitions_tenant_created ON workflow_transitions(tenant_id, created_at DESC);

-- Comments
COMMENT ON TABLE workflow_transitions IS 'Immutable audit trail of workflow state transitions';
COMMENT ON COLUMN workflow_transitions.transition_id IS 'Unique transition identifier (UUID)';
COMMENT ON COLUMN workflow_transitions.workflow_id IS 'Link to parent workflow';
COMMENT ON COLUMN workflow_transitions.from_state IS 'Previous workflow state';
COMMENT ON COLUMN workflow_transitions.to_state IS 'New workflow state';
COMMENT ON COLUMN workflow_transitions.action IS 'Action taken: APPROVED, REJECTED, DELEGATED, ESCALATED';
COMMENT ON COLUMN workflow_transitions.acted_by_user_id IS 'User ID who performed the action';

-- =============================================================================
-- TABLE 4: rules (Rule configuration with versioning)
-- =============================================================================

CREATE TABLE rules (
  rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL,
  decision_type VARCHAR(256) NOT NULL,
  rule_name VARCHAR(256) NOT NULL,
  description TEXT,
  conditions JSONB NOT NULL,                 -- condition definition
  action JSONB NOT NULL,                     -- action (outcome, approval_config)
  extension_hooks JSONB,                     -- async hooks (Phase 2+)
  version VARCHAR(32) NOT NULL,              -- e.g., "1.0", "1.1"
  status VARCHAR(32) NOT NULL,               -- DRAFT, ACTIVE, DEPRECATED, DELETED
  evaluation_sequence INTEGER NOT NULL DEFAULT 0,  -- PHASE 1 CLARIFICATION: Explicit rule evaluation order
  created_by_user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  activated_at TIMESTAMP WITH TIME ZONE,     -- when activated
  deactivated_at TIMESTAMP WITH TIME ZONE,   -- when deactivated
  deactivation_reason TEXT,
  deleted_at TIMESTAMP WITH TIME ZONE,
  final_audit_report_uri VARCHAR(512),       -- link to archived audit report
  archived_at TIMESTAMP WITH TIME ZONE,
  archive_location VARCHAR(512),             -- URI to archived rule definition

  -- Constraints
  CONSTRAINT status_valid CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED', 'DELETED')),
  CONSTRAINT version_not_empty CHECK (length(version) > 0),
  CONSTRAINT rule_name_not_empty CHECK (length(rule_name) > 0),
  CONSTRAINT conditions_not_null CHECK (conditions IS NOT NULL),
  CONSTRAINT action_not_null CHECK (action IS NOT NULL)
);

-- Unique constraint: only one ACTIVE rule per (tenant, decision_type, rule_name)
CREATE UNIQUE INDEX idx_rules_unique_active_per_type ON rules(tenant_id, decision_type, rule_name) WHERE status = 'ACTIVE';

-- Indexes for rules (MANDATORY)
CREATE INDEX idx_rules_tenant_id ON rules(tenant_id);
CREATE INDEX idx_rules_tenant_decision_type_status ON rules(tenant_id, decision_type, status);
CREATE INDEX idx_rules_tenant_decision_type_active ON rules(tenant_id, decision_type) WHERE status = 'ACTIVE';

-- PHASE 1 CLARIFICATION: Deterministic rule ordering
CREATE INDEX idx_rules_evaluation_order ON rules(tenant_id, decision_type, evaluation_sequence) WHERE status = 'ACTIVE';

-- Comments
COMMENT ON TABLE rules IS 'Rule configurations with versioning - defines governance rules';
COMMENT ON COLUMN rules.rule_id IS 'Unique rule identifier (UUID)';
COMMENT ON COLUMN rules.tenant_id IS 'Tenant identifier for multi-tenancy isolation';
COMMENT ON COLUMN rules.decision_type IS 'Type of decision this rule applies to';
COMMENT ON COLUMN rules.rule_name IS 'Human-readable rule name (unique per tenant+decision_type when ACTIVE)';
COMMENT ON COLUMN rules.conditions IS 'Rule conditions (JSONB) - evaluated against context';
COMMENT ON COLUMN rules.action IS 'Rule action (JSONB) - outcome and approval config';
COMMENT ON COLUMN rules.version IS 'Rule version (e.g., "1.0", "1.1") - identifier only, not SemVer contract';
COMMENT ON COLUMN rules.status IS 'Rule status: DRAFT, ACTIVE, DEPRECATED, DELETED';
COMMENT ON COLUMN rules.evaluation_sequence IS 'Evaluation order (lower = evaluated first)';

-- =============================================================================
-- TABLE 5: event_log (Append-Only, Immutable, Source of Truth)
-- =============================================================================

CREATE TABLE event_log (
  event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- globally unique forever
  event_type VARCHAR(256) NOT NULL,          -- e.g., "decision.created"
  tenant_id UUID NOT NULL,                   -- partition key
  aggregate_id UUID NOT NULL,                -- decision_id or workflow_id
  aggregate_type VARCHAR(32) NOT NULL,       -- "decision" or "workflow"
  payload JSONB NOT NULL,                    -- event-specific data
  metadata JSONB,                            -- source, caused_by_user_id, trace_id
  occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,  -- when event occurred (immutable)
  recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,  -- when persisted
  schema_version VARCHAR(32) DEFAULT '1.0',
  archived_at TIMESTAMP WITH TIME ZONE,
  archive_location VARCHAR(512),

  -- Constraints
  CONSTRAINT event_type_valid CHECK (event_type IN (
    'decision.created', 'decision.allowed', 'decision.denied', 'decision.requires_approval',
    'workflow.created', 'workflow.pending_approval', 'workflow.approved', 'workflow.rejected',
    'workflow.delegated', 'workflow.escalated', 'workflow.completed'
  )),
  CONSTRAINT aggregate_type_valid CHECK (aggregate_type IN ('decision', 'workflow')),
  CONSTRAINT payload_not_null CHECK (payload IS NOT NULL)
);

-- Indexes for event_log (MANDATORY)
CREATE INDEX idx_event_log_tenant_occurred ON event_log(tenant_id, occurred_at DESC);
CREATE INDEX idx_event_log_aggregate ON event_log(tenant_id, aggregate_id);
CREATE INDEX idx_event_log_type ON event_log(tenant_id, event_type);

-- Comments
COMMENT ON TABLE event_log IS 'Immutable event log - source of truth for all state changes';
COMMENT ON COLUMN event_log.event_id IS 'Globally unique event identifier (UUID)';
COMMENT ON COLUMN event_log.event_type IS 'Event type (e.g., decision.created, workflow.approved)';
COMMENT ON COLUMN event_log.aggregate_id IS 'ID of the aggregate (decision_id or workflow_id)';
COMMENT ON COLUMN event_log.aggregate_type IS 'Type of aggregate: decision or workflow';
COMMENT ON COLUMN event_log.payload IS 'Event-specific data (JSONB)';
COMMENT ON COLUMN event_log.occurred_at IS 'When event occurred (immutable)';
COMMENT ON COLUMN event_log.recorded_at IS 'When event was persisted to database';

-- =============================================================================
-- TABLE 6: operations_audit (Audit Trail, Immutable)
-- =============================================================================

CREATE TABLE operations_audit (
  audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL,
  operation_type VARCHAR(32) NOT NULL,       -- CREATE, READ, UPDATE_ATTEMPT, DELETE_ATTEMPT
  resource_type VARCHAR(32) NOT NULL,        -- decision, workflow, rule, event_log
  resource_id UUID,
  actor_user_id UUID,                        -- who made the operation
  actor_role VARCHAR(256),
  action_status VARCHAR(32),                 -- SUCCESS, FAILURE, DENIED
  reason_if_denied TEXT,                     -- why denied
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  trace_id UUID,

  -- Constraints
  CONSTRAINT operation_type_valid CHECK (operation_type IN (
    'CREATE', 'READ', 'UPDATE_ATTEMPT', 'DELETE_ATTEMPT', 'ACTIVATE', 'DEACTIVATE'
  )),
  CONSTRAINT resource_type_valid CHECK (resource_type IN ('decision', 'workflow', 'rule', 'event_log')),
  CONSTRAINT action_status_valid CHECK (action_status IN ('SUCCESS', 'FAILURE', 'DENIED'))
);

-- Indexes for operations_audit (MANDATORY)
CREATE INDEX idx_operations_audit_tenant_timestamp ON operations_audit(tenant_id, timestamp DESC);
CREATE INDEX idx_operations_audit_resource ON operations_audit(tenant_id, resource_id) WHERE resource_id IS NOT NULL;

-- Comments
COMMENT ON TABLE operations_audit IS 'Immutable audit trail of all operations (including failed attempts)';
COMMENT ON COLUMN operations_audit.audit_id IS 'Unique audit record identifier (UUID)';
COMMENT ON COLUMN operations_audit.operation_type IS 'Type of operation: CREATE, READ, UPDATE_ATTEMPT, DELETE_ATTEMPT, ACTIVATE, DEACTIVATE';
COMMENT ON COLUMN operations_audit.resource_type IS 'Type of resource: decision, workflow, rule, event_log';
COMMENT ON COLUMN operations_audit.action_status IS 'Operation result: SUCCESS, FAILURE, DENIED';
COMMENT ON COLUMN operations_audit.reason_if_denied IS 'Reason for denial (if status=DENIED)';

-- =============================================================================
-- TABLE 7: idempotency_cache (Deduplication, Hot storage only)
-- =============================================================================

CREATE TABLE idempotency_cache (
  tenant_id UUID NOT NULL,
  idempotency_key VARCHAR(256) NOT NULL,
  decision_id UUID NOT NULL,
  context_hash VARCHAR(64) NOT NULL,         -- SHA256 hash of canonicalized context
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  ttl TIMESTAMP WITH TIME ZONE,              -- cache expiration (24h default)

  -- Primary key
  PRIMARY KEY (tenant_id, idempotency_key),

  -- Foreign key
  CONSTRAINT idempotency_decision_fk FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE RESTRICT
);

-- Index for cleanup job
CREATE INDEX idx_idempotency_cache_ttl ON idempotency_cache(ttl) WHERE ttl IS NOT NULL;

-- Comments
COMMENT ON TABLE idempotency_cache IS 'Idempotency deduplication cache - prevents duplicate decisions';
COMMENT ON COLUMN idempotency_cache.tenant_id IS 'Tenant identifier for multi-tenancy isolation';
COMMENT ON COLUMN idempotency_cache.idempotency_key IS 'Application-provided idempotency key (max 256 chars)';
COMMENT ON COLUMN idempotency_cache.decision_id IS 'Existing decision ID for this idempotency key';
COMMENT ON COLUMN idempotency_cache.context_hash IS 'SHA256 hash of canonicalized context for conflict detection';
COMMENT ON COLUMN idempotency_cache.ttl IS 'Cache expiration timestamp (default: created_at + 24 hours)';

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

CREATE TABLE schema_migrations (
  migration_id INTEGER PRIMARY KEY,
  migration_name VARCHAR(256) NOT NULL,
  applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Record this migration
INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (1, '001_initial_schema');

COMMIT;

-- =============================================================================
-- END OF MIGRATION 001
-- =============================================================================
