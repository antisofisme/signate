# INFRA-LAY2-003: Data Persistence Model

**VERSION**: Layer 2 DRAFT
**STATUS**: READY FOR LOCKING (7 mandatory amendments applied)
**DATE**: 2025-12-27

**AMENDMENTS APPLIED**:
1. ✅ Immutability Enforcement (hardened: 3-layer protection)
2. ✅ Event Log Reclassification (raw storage, projections only)
3. ✅ Tenant Isolation Enforcement (database-level: RLS/schema)
4. ✅ Workflow Persistence Clarification (workflow_transitions table added)
5. ✅ Event Persistence Atomicity (event_log in same transaction)
6. ✅ Index Correction (approval_workflow_id index marked MANDATORY)
7. ✅ Archival Operational Guardrails (ownership, SLA, automation)

---

## Overview

This document defines **data persistence strategy** for Infra:
- Append-only immutability
- Tenant-based partitioning
- Query performance (indexes)
- Retention & archival
- Backup & recovery

**Focus**: Storage architecture, NOT implementation (no SQL/NoSQL choice).

---

## 1. Core Principles

### 1.1 Append-Only, Never Mutate

```
PRINCIPLE: Once written, data NEVER changes.

Decision Record:
  - Created at T0
  - outcome = ALLOWED
  - outcome never changes (no UPDATE)
  - No DELETE (record preserved forever)
  - New decision_id for retry (not mutation)

Workflow Record:
  - state transitions recorded as events
  - state field mutable DURING transition
  - After transition complete: immutable
  - state history preserved in audit log

Event Log:
  - Only INSERT (never UPDATE, DELETE)
  - Immutable forever
  - Ordered by timestamp
  - Complete audit trail
```

### 1.2 Tenant Partitioning

```
PRINCIPLE: Data physically partitioned by tenant_id.

All queries MUST include tenant_id filter:
  SELECT * FROM decisions
  WHERE tenant_id = 'hotel-123'
  AND decision_id = 'dec-xyz'

Partition Key: tenant_id
  - Hard boundary (no cross-tenant queries)
  - Scaling: independent per tenant
  - Isolation: accidental leaks impossible
  - Performance: queries scoped to single tenant

Example:
  Partition 1: tenant_id = 'hotel-123' (10M decisions)
  Partition 2: tenant_id = 'restaurant-456' (5M decisions)
  Partition 3: tenant_id = 'hospital-789' (50M decisions)

  Each partition independent, scales separately
```

### 1.3 Immutable Snapshots

```
PRINCIPLE: Data stored as immutable snapshots.

Decision Record snapshot:
  {
    decision_id: "dec-xyz-789",
    tenant_id: "hotel-123",
    decision_type: "accounting.journal_approval",
    requester_user_id: "user-456",
    outcome: "ALLOWED",
    rule_matched: "rule_name_xyz",
    rule_version: "1.2",
    context_snapshot: { /* full context at decision time */ },
    requested_at: "2025-12-27T10:30:01Z",
    decided_at: "2025-12-27T10:30:01.050Z",
    created_at: "2025-12-27T10:30:01.100Z"
  }

  NEVER mutate this record.
  If decision needs "change", create NEW decision_id.

Workflow Record snapshot:
  {
    workflow_id: "wf-abc-123",
    decision_id: "dec-xyz-789",
    tenant_id: "hotel-123",
    initial_state: "PENDING_APPROVAL",
    current_state: "APPROVED",  // Mutable during lifecycle
    approver_role: "CFO",
    created_at: "2025-12-27T10:30:01Z",
    state_transitions: [
      { from: "PENDING_APPROVAL", to: "APPROVED", at: "...", by_user: "..." }
    ]
  }

  State field mutable until terminal state.
  After terminal state: immutable.
```

---

## 2. Data Model: Core Tables

### 2.1 Decisions Table

```
TABLE: decisions
PARTITION KEY: tenant_id
SORT KEY: decision_id (or occurred_at, depending on access patterns)

SCHEMA:
  tenant_id (string, NOT NULL)
    ↓ partition key
  decision_id (string, UUID, NOT NULL)
    ↓ primary key (within tenant)
  decision_type (string, NOT NULL)
    Example: "accounting.journal_approval"
  requester_user_id (string)
    User who requested decision (audit only)
  outcome (string, NOT NULL)
    Enum: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
  rule_matched (string, nullable)
    Single rule name (first-match-wins)
  rule_version (string, nullable)
    Version of matched rule
  approval_workflow_id (string, nullable)
    If outcome = REQUIRE_APPROVAL
  context_snapshot (object, NOT NULL)
    Full sanitized context used for evaluation
    Immutable snapshot (for audit/replay)
  requested_at (timestamp, NOT NULL)
    When decision was requested
  decided_at (timestamp, NOT NULL)
    When decision was made
  created_at (timestamp, NOT NULL)
    When record was persisted
  idempotency_key (string, nullable, UNIQUE within tenant)
    For deduplication (same key = cached decision_id)

CONSTRAINTS:
  - decision_id: UNIQUE within tenant
  - idempotency_key: UNIQUE within tenant (if present)
  - outcome: IMMUTABLE (can only set once, never UPDATE)
  - context_snapshot: IMMUTABLE
  - No DELETE (append-only)

INDEXES:
  1. PRIMARY: (tenant_id, decision_id)
  2. QUERY: (tenant_id, decision_type, requested_at DESC)
     ↓ for querying decisions by type
  3. QUERY: (tenant_id, outcome, requested_at DESC)
     ↓ for querying DENIED/ALLOWED decisions
  4. QUERY: (tenant_id, idempotency_key)
     ↓ for idempotency deduplication (MANDATORY for performance)
  5. QUERY: (tenant_id, approval_workflow_id)
     ↓ for finding decision from workflow (MANDATORY, critical path)
  6. AUDIT: (tenant_id, created_at DESC)
     ↓ for audit trail queries

SIZE ESTIMATE:
  Per decision: ~2KB (with context_snapshot)
  1B decisions/year: ~2TB storage
```

### 2.2 Workflows Table

```
TABLE: workflows
PARTITION KEY: tenant_id
SORT KEY: workflow_id

SCHEMA:
  tenant_id (string, NOT NULL)
    ↓ partition key
  workflow_id (string, UUID, NOT NULL)
    ↓ primary key (within tenant)
  decision_id (string, UUID, NOT NULL)
    Link to decision (immutable)
  decision_type (string, NOT NULL)
    From decision (for querying)
  current_state (string, NOT NULL)
    Current state: PENDING_APPROVAL | APPROVED | REJECTED | ESCALATED | DELEGATED_TO_*
  initial_state (string, NOT NULL)
    Initial state (for audit)
  approver_role (string, NOT NULL)
    Role responsible for approval (immutable)
  escalation_target_role (string, nullable)
    Role for escalation (immutable)
  escalation_timeout_at (timestamp, nullable)
    When escalation timeout expires
  created_at (timestamp, NOT NULL)
    When workflow created
  updated_at (timestamp, NOT NULL)
    When state last changed
  state_transitions (list of objects)
    History of state changes:
      [
        {
          from_state: "PENDING_APPROVAL",
          to_state: "APPROVED",
          timestamp: "...",
          approver_role: "CFO",
          approved_by_user_id: "user-cfo-001",
          reason: "Approved per policy"
        }
      ]
    IMMUTABLE once recorded

CONSTRAINTS:
  - workflow_id: UNIQUE within tenant
  - decision_id: UNIQUE (one workflow per decision)
  - current_state: MUTABLE (updates allowed until terminal state)
  - Approval_role: IMMUTABLE
  - state_transitions: APPEND-ONLY (never delete entries)
  - No DELETE

INDEXES:
  1. PRIMARY: (tenant_id, workflow_id)
  2. QUERY: (tenant_id, current_state, created_at DESC)
     ↓ for finding pending approvals
  3. QUERY: (tenant_id, decision_id)
     ↓ for finding workflow from decision
  4. QUERY: (tenant_id, approver_role, current_state)
     ↓ for finding approvals for specific role
  5. QUERY: (tenant_id, escalation_timeout_at)
     ↓ for finding workflows needing escalation
  6. AUDIT: (tenant_id, updated_at DESC)
     ↓ for audit trail

SIZE ESTIMATE:
  Per workflow: ~1KB
  500M workflows/year: ~500GB storage
```

### 2.3 Workflow Transitions Table (Append-Only Immutable Audit Trail)

```
TABLE: workflow_transitions
PARTITION KEY: tenant_id
SORT KEY: (workflow_id, timestamp)

CRITICAL: All state transitions recorded here (IMMUTABLE).
          Workflows table stores current_state only (mutable during transition).
          All changes tracked in this append-only table.

SCHEMA:
  transition_id (string, UUID, NOT NULL)
    Unique identifier
  workflow_id (string, UUID, NOT NULL)
    Link to workflow
  tenant_id (string, NOT NULL)
    ↓ partition key
  from_state (string, NOT NULL)
    Previous state
  to_state (string, NOT NULL)
    New state
  approver_role (string, NOT NULL)
    Role that performed transition
  approved_by_user_id (string, nullable)
    User who performed action (for audit)
  action (string, NOT NULL)
    "APPROVED" | "REJECTED" | "DELEGATED" | "ESCALATED"
  comment (string, nullable)
    Human comment
  timestamp (timestamp, NOT NULL)
    When transition occurred
  created_at (timestamp, NOT NULL)
    When record persisted

CONSTRAINTS:
  - transition_id: UNIQUE
  - No UPDATE, No DELETE
  - APPEND-ONLY (immutable)
  - Every workflow state change → one record here

INDEXES:
  1. PRIMARY: (tenant_id, workflow_id, timestamp DESC)
  2. QUERY: (tenant_id, workflow_id)
     ↓ for full state history

SIZE ESTIMATE:
  Per transition: ~200 bytes
  500M workflows × 3 transitions avg: ~300GB/year
```

### 2.4 Rules Table

```
TABLE: rules
PARTITION KEY: tenant_id
SORT KEY: (decision_type, version DESC)

SCHEMA:
  tenant_id (string, NOT NULL)
    ↓ partition key
  rule_id (string, NOT NULL)
    Unique rule identifier
  rule_name (string, NOT NULL)
    Human-readable name (e.g., "correction_amount_15000_cfo")
  decision_type (string, NOT NULL)
    Scoped by decision type
  version (string, NOT NULL)
    Rule version (e.g., "1.2", "2.0")
  status (string, NOT NULL)
    Enum: "DRAFT" | "ACTIVE" | "DEPRECATED"
  priority (integer)
    Evaluation order (lower = earlier) within decision_type
  condition (object, NOT NULL)
    Rule condition (deterministic, no side effects)
  action (string, NOT NULL)
    Outcome if condition matches: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
  approval_config (object, nullable)
    If action = REQUIRE_APPROVAL:
      {
        approver_roles: ["CFO", "manager"],
        escalation_timeout_hours: 24,
        escalation_target_role: "chief_finance_officer"
      }
  description (string)
    Human-readable rule description
  created_by_user_id (string)
    Who created this rule
  created_at (timestamp, NOT NULL)
  updated_at (timestamp, NOT NULL)
  activated_at (timestamp, nullable)
    When rule became ACTIVE
  deactivated_at (timestamp, nullable)
    When rule became DEPRECATED

CONSTRAINTS:
  - rule_id: UNIQUE within tenant
  - (tenant_id, decision_type, version): UNIQUE
  - status: IMMUTABLE once ACTIVE (can only move to DEPRECATED)
  - condition: IMMUTABLE after activation
  - No DELETE (versions preserved for audit)

INDEXES:
  1. PRIMARY: (tenant_id, rule_id)
  2. QUERY: (tenant_id, decision_type, status, priority)
     ↓ for loading active rules for evaluation
  3. QUERY: (tenant_id, decision_type, version DESC)
     ↓ for finding latest rule version
  4. QUERY: (tenant_id, status, activated_at DESC)
     ↓ for rule audit trail
  5. AUDIT: (tenant_id, created_at DESC)
     ↓ for rule change history

SIZE ESTIMATE:
  Per rule: ~500 bytes
  100K rules/tenant across versions: ~50MB/tenant
```

### 2.4 Event Log Table (Write-Optimized Raw Storage, NOT Queryable Directly)

**CRITICAL**: event_log is **raw append-only storage only**.
- Direct querying by CMS/UI is **FORBIDDEN**.
- All reads occur via **projections / read models**.
- Projections are **rebuildable** from event_log (idempotent).

```
TABLE: event_log
PARTITION KEY: tenant_id
SORT KEY: (occurred_at, event_id)

PURPOSE: Write-optimized raw append-only storage
         Source of truth for all state
         Used to rebuild projections only

SCHEMA:
  event_id (string, UUID, NOT NULL)
    ↓ unique forever (immutable)
  event_type (string, NOT NULL)
    "decision.created", "workflow.approved", "rule.activated", etc.
  tenant_id (string, NOT NULL)
    ↓ partition key
  aggregate_id (string, NOT NULL)
    decision_id or workflow_id or rule_id
  aggregate_type (string, NOT NULL)
    "decision" | "workflow" | "rule"
  occurred_at (timestamp, NOT NULL)
    When event happened
  recorded_at (timestamp, NOT NULL)
    When event was persisted
  payload (object, NOT NULL)
    Event-specific data (immutable snapshot)
  metadata (object)
    source, caused_by_user_id, trace_id, etc.
  schema_version (string, NOT NULL)
    Event schema version (for evolution)

CONSTRAINTS:
  - event_id: UNIQUE (immutable)
  - No UPDATE, No DELETE
  - APPEND-ONLY (insert only)

INDEXES:
  1. PRIMARY: (tenant_id, occurred_at, event_id)
     ↓ for event stream queries
  2. QUERY: (tenant_id, event_type, occurred_at DESC)
     ↓ for filtering by event type
  3. QUERY: (tenant_id, aggregate_id, occurred_at)
     ↓ for event history of decision/workflow
  4. QUERY: (tenant_id, occurred_at DESC)
     ↓ for chronological audit trail

SIZE ESTIMATE:
  Per event: ~500 bytes
  1B events/year: ~500TB storage (hot) + archival
```

### 2.5 Approvals Record Table

```
TABLE: approvals
PARTITION KEY: tenant_id
SORT KEY: workflow_id, timestamp

SCHEMA:
  approval_id (string, UUID, NOT NULL)
  workflow_id (string, UUID, NOT NULL)
  tenant_id (string, NOT NULL)
    ↓ partition key
  decision_id (string, UUID, NOT NULL)
  approver_role (string, NOT NULL)
    Role identifier ("CFO", "manager", etc.)
  approved_by_user_id (string, nullable)
    User who performed action (for audit)
  action (string, NOT NULL)
    "APPROVED" | "REJECTED" | "DELEGATED" | "ESCALATED"
  comment (string, nullable)
    Human comment (for audit)
  timestamp (timestamp, NOT NULL)
    When action occurred
  created_at (timestamp, NOT NULL)
    When record persisted

CONSTRAINTS:
  - approval_id: UNIQUE
  - No UPDATE, No DELETE
  - APPEND-ONLY (record immutable)

INDEXES:
  1. PRIMARY: (tenant_id, workflow_id, timestamp DESC)
  2. QUERY: (tenant_id, approver_role, timestamp DESC)
     ↓ for finding approvals by role
  3. QUERY: (tenant_id, action, timestamp DESC)
     ↓ for audit trail filtering
  4. QUERY: (tenant_id, decision_id)
     ↓ for audit trail of decision

SIZE ESTIMATE:
  Per approval: ~200 bytes
  500M approvals/year: ~100GB storage
```

---

## 3. Query Patterns & Performance

### 3.1 Critical Path Queries

**Query 1: Load Rules for Evaluation** (during decision creation)
```
SELECT rule_id, rule_name, priority, condition, action, approval_config
FROM rules
WHERE tenant_id = 'hotel-123'
  AND decision_type = 'accounting.journal_approval'
  AND status = 'ACTIVE'
ORDER BY priority ASC

Index: (tenant_id, decision_type, status, priority)
SLA: < 10ms
Critical: Must be fast (called per decision)
```

**Query 2: Check Idempotency** (prevent duplicates)
```
SELECT decision_id
FROM decisions
WHERE tenant_id = 'hotel-123'
  AND idempotency_key = 'req-abc-123'

Index: (tenant_id, idempotency_key)
SLA: < 5ms
Critical: Must prevent duplicates
```

**Query 3: Fetch Workflow State** (for approval)
```
SELECT workflow_id, current_state, approver_role, state_transitions
FROM workflows
WHERE tenant_id = 'hotel-123'
  AND workflow_id = 'wf-xyz-789'

Index: (tenant_id, workflow_id)
SLA: < 5ms
Critical: Must be instant
```

**Query 4: Find Pending Approvals** (for UI)
```
SELECT workflow_id, decision_id, decision_type, created_at
FROM workflows
WHERE tenant_id = 'hotel-123'
  AND current_state = 'PENDING_APPROVAL'
  AND approver_role = 'CFO'
ORDER BY created_at ASC

Index: (tenant_id, current_state, approver_role, created_at)
SLA: < 100ms
Critical: Used for approval list UI
```

**Query 5: Find Workflows Needing Escalation** (timeout-based)
```
SELECT workflow_id, escalation_target_role
FROM workflows
WHERE tenant_id = 'hotel-123'
  AND escalation_timeout_at < now()
  AND current_state = 'PENDING_APPROVAL'

Index: (tenant_id, escalation_timeout_at, current_state)
SLA: < 1s (batch job, not critical path)
Non-critical: Background escalation job
```

### 3.2 Audit Queries

**Query: Decision Audit Trail**
```
SELECT * FROM decisions
WHERE tenant_id = 'hotel-123'
  AND decision_type = 'accounting.journal_approval'
  AND created_at >= '2025-12-01'
  AND created_at <= '2025-12-31'
ORDER BY created_at DESC

Index: (tenant_id, decision_type, created_at DESC)
SLA: < 5s (not critical path, batch-friendly)
```

**Query: Event History for Decision**
```
SELECT * FROM event_log
WHERE tenant_id = 'hotel-123'
  AND aggregate_id = 'dec-xyz-789'
ORDER BY occurred_at ASC

Index: (tenant_id, aggregate_id, occurred_at)
SLA: < 1s (audit query, not time-sensitive)
```

**Query: Approval Audit Trail**
```
SELECT * FROM approvals
WHERE tenant_id = 'hotel-123'
  AND workflow_id = 'wf-xyz-789'
ORDER BY timestamp ASC

Index: (tenant_id, workflow_id, timestamp DESC)
SLA: < 1s (audit query)
```

---

## 4. Tenant Partitioning Strategy

### 4.1 Tenant Isolation Enforcement (Database-Level, Not by Convention)

```
TENANT ISOLATION ENFORCED AT DATABASE LAYER (MANDATORY):

Option A: Row-Level Security (RLS) - Recommended
  - PostgreSQL: CREATE POLICY to filter by tenant_id
  - All queries automatically scoped by tenant_id
  - Query without tenant context returns 0 rows (fail-safe)
  - Example:
    CREATE POLICY tenant_isolation ON decisions
      USING (tenant_id = current_setting('app.tenant_id'))
      WITH CHECK (tenant_id = current_setting('app.tenant_id'))

Option B: Schema-Per-Tenant (Hot Tenants Only)
  - Separate schema per tenant (e.g., schema_hotel_123, schema_restaurant_456)
  - Used for tenants with high transaction volume
  - Highest isolation, scales independently
  - Requires routing logic (application knows which schema)

Option C: Database-Per-Tenant (Enterprise Only)
  - Separate database instance per tenant
  - Highest isolation, highest cost
  - Used only for dedicated high-security tenants

MANDATORY ENFORCEMENT:
  ALL queries MUST be scoped to tenant at database layer.
  No application-level filtering only (insufficient).
  Query without tenant scope FAILS (not returns all, fails).

GUARD RAILS:
  - RLS policies enforce tenant_id in WHERE clause
  - Query: SELECT * FROM decisions WHERE tenant_id = X
  - Query fails if tenant_id missing (exception raised)
  - 404 returned by application (not exposed to client)
  - No accidental cross-tenant leaks possible
```

### 4.2 Physical Partitioning (Optional, Implementation Detail)

```
Option 1: Separate Database per Tenant
  - Highest isolation
  - Scale independently
  - Higher operational overhead

Option 2: Separate Schema per Tenant (PostgreSQL)
  - Good isolation
  - Shared infrastructure
  - Moderate operational overhead

Option 3: Logical Partitioning (tenant_id column)
  - Lowest overhead
  - Requires application-level filtering
  - Must enforce at query layer

Infra Requirement: Logical partitioning (all options implement it)
No cross-tenant leaks possible (with proper indexes)
```

---

## 5. Immutability & Consistency

### 5.1 Write-Once Guarantee (Multi-Layer Enforcement)

```
IMMUTABILITY ENFORCED AT THREE INDEPENDENT LAYERS:

Layer 1: Database Role Permissions (First Line)
  - Append-only tables have INSERT-only role
  - REVOKE UPDATE on immutable tables (explicit)
  - REVOKE DELETE on immutable tables (explicit)
  - Only schema owner can emergency-modify

Layer 2: Database Triggers (Second Line Safeguard)
  - TRIGGER rejects UPDATE on immutable columns
  - TRIGGER rejects DELETE on immutable tables
  - Acts as safeguard if role-based control bypassed

Layer 3: Storage Immutability (Third Line, Cold Tier)
  - Warm/Cold tiers use WORM (Write-Once-Read-Many)
  - Object Lock (AWS S3, Azure Blob, etc.)
  - Physical immutability at storage layer
  - Prevents deletion/modification even with admin access

DECISION:
  INSERT decision (T0+50ms, INSERT-only role)
    ↓
  Decision immutable forever
  UPDATE rejected by: (role permissions) + (trigger) + (storage lock)
  DELETE rejected by: (role permissions) + (trigger) + (storage lock)

WORKFLOW:
  INSERT workflow (T0+55ms, INSERT-only role)
    ↓
  Workflow state mutable until terminal (role-controlled UPDATE)
  State transitions recorded in workflow_transitions (append-only)
    ↓
  Once terminal (APPROVED/REJECTED): state immutable
  DELETE rejected by: (role permissions) + (trigger)

WORKFLOW_TRANSITIONS:
  APPEND transition record (INSERT-only role)
    ↓
  Transitions immutable forever
  UPDATE rejected by: (role permissions) + (trigger)
  DELETE rejected by: (role permissions) + (trigger)
  Immutable audit trail of all state changes

RULES:
  INSERT rule version (by CMS, INSERT-only role)
    ↓
  Rule immutable after creation
  Status field UPDATE allowed (ACTIVE → DEPRECATED, role-controlled)
  DELETE rejected by: (role permissions) + (trigger)

EVENT_LOG:
  INSERT event (same DB transaction as decision, INSERT-only role)
    ↓
  Event immutable forever
  UPDATE rejected by: (role permissions) + (trigger) + (storage lock)
  DELETE rejected by: (role permissions) + (trigger) + (storage lock)
  Source of truth for all projections

ENFORCEMENT GUARANTEE:
  Immutability protected by 3 independent layers.
  Breach of one layer does NOT compromise immutability (2 remain).
  Breach of two layers extremely unlikely (requires multiple compromises).
  Breach of all 3 layers requires simultaneous compromise of:
    (DB access control) + (DB logic) + (Storage layer)
```

### 5.2 Transactional Consistency (Event Persistence Atomic)

```
CRITICAL: event_log INSERT occurs IN THE SAME DATABASE TRANSACTION
          as decision/workflow creation (NOT async queue).
          This makes event_log the source of truth.
          External event bus publishing remains async (best-effort).

DECISION CREATION: ATOMIC TRANSACTION

BEGIN TRANSACTION
  1. INSERT decision record
  2. INSERT workflow record (if outcome = REQUIRE_APPROVAL)
  3. INSERT workflow_transitions record (if workflow created)
  4. INSERT event_log records (SAME TRANSACTION)
       - decision.created
       - decision.{allowed|denied|requires_approval}
       - workflow.created (if applicable)
COMMIT
  ↓ (after commit only)
External event bus publishing (async, best-effort):
  - Event bus delivers to subscribers
  - Failures logged, no rollback
  - Retries handled by event bus

Result:
  - All-or-nothing (no partial state)
  - Atomicity guaranteed at database level
  - event_log is source of truth
  - External event bus is eventual-consistency layer

FAILURE HANDLING:
  - If any INSERT fails: ROLLBACK (entire transaction)
  - Application retries with same idempotency_key
  - Idempotency key ensures no duplicate

WORKFLOW STATE TRANSITION: ATOMIC

BEGIN TRANSACTION
  1. UPDATE workflow.current_state
  2. APPEND workflow_transitions record
  3. INSERT approval record
  4. INSERT event_log records (SAME TRANSACTION)
       - workflow.approved | rejected | delegated | escalated
       - workflow.completed (if terminal state)
COMMIT
  ↓ (after commit only)
External event bus publishing (async, best-effort)

Result:
  - State transition atomic
  - Transitions immutable (stored in workflow_transitions)
  - Event log immutable (stored in event_log)
  - External bus notifies subscribers asynchronously

GUARANTEE:
  event_log is ALWAYS consistent with decision/workflow state.
  No event loss (stored in database transaction).
  External bus may have failures (retries handled separately).
```

---

## 6. Retention & Archival

### 6.1 Hot/Warm/Cold Storage Strategy

```
HOT STORAGE (Recent, Fast):
  Duration: Last 90 days
  Access: Milliseconds (indexed, in-memory cache)
  Use: SDK queries, CMS audit queries
  Storage: SSD or in-memory
  Cost: High

WARM STORAGE (Archive, Slower):
  Duration: 90 days - 7 years
  Access: Seconds (batch jobs, background queries)
  Use: Long-term audit, compliance
  Storage: Object storage or cold tier
  Cost: Medium

COLD STORAGE (Compliance, Archived):
  Duration: 7 years - retention limit
  Access: Minutes-hours (rare, compliance only)
  Use: Legal hold, compliance reporting
  Storage: Immutable archive (S3 Glacier, etc.)
  Cost: Low

DELETION:
  After retention period: DELETE (encrypted deletion, audit trail)
  Before deletion: immutable (cannot tamper)
```

### 6.2 Archival Operational Guardrails (Ownership, SLA, Automation)

```
ARCHIVAL OWNERSHIP (Explicit):
  - CMS owns archival automation (scheduled jobs)
  - CMS responsible for Hot → Warm → Cold migration
  - CMS tracks archival status (metadata table)
  - CMS enforces SLA (alerts if migration delayed)

DECISION ARCHIVAL (MANDATORY):
  Trigger: created_at < NOW() - 90 days
  Target: Move from hot (SSD) to warm (object storage)
  Action: COPY (retain in hot for 90d overlap, then delete)
  SLA: Migration completed within 24 hours of trigger
  Owner: CMS Archival Job

  After 7 years: Move from warm to cold (immutable archive)
  SLA: Migration completed within 7 days
  Owner: CMS Archival Job

WORKFLOW ARCHIVAL (MANDATORY):
  Trigger: updated_at < NOW() - 90 days
  Target: Move from hot to warm
  Action: COPY + verify + DELETE from hot
  SLA: Migration completed within 24 hours
  Owner: CMS Archival Job

EVENT ARCHIVAL (MANDATORY):
  Trigger: recorded_at < NOW() - 90 days
  Target: Move from hot to warm (complete audit trail)
  Action: COPY + verify (critical for compliance)
  SLA: Migration completed within 24 hours
  Owner: CMS Archival Job

  After 7 years: Move from warm to cold
  Action: COPY to immutable archive + verify + DELETE warm copy
  SLA: Migration completed within 7 days

WORKFLOW_TRANSITIONS ARCHIVAL (MANDATORY):
  Trigger: created_at < NOW() - 90 days
  Target: Move from hot to warm (audit trail)
  Action: COPY + verify + DELETE from hot
  SLA: Migration completed within 24 hours

CMS AUDIT TRAIL (DATA-TIER AWARE):
  - CMS logs all archival operations (start, completion, errors)
  - Tracks migration status per table per tenant
  - Alerts on migration failures or SLA violations
  - Verifies data integrity before hot deletion

TENANT-SCOPED REHYDRATION (If Needed):
  If tenant requests data from cold storage:
    1. CMS locates data in cold archive
    2. Restores to warm storage (object storage)
    3. Application queries via warm storage
    4. SLA: < 1 hour to available for query
    5. CMS tracks rehydration for cost billing

QUERY BEHAVIOR (SLA):
  Hot storage: < 100ms (indexed, in-memory cache)
  Warm storage: < 5s (object storage, scan-friendly)
  Cold storage: < 1 hour (archive retrieval, manual approval)

IMMUTABILITY GUARANTEE:
  - Hot: Multi-layer enforcement (roles, triggers, storage)
  - Warm: WORM (Write-Once-Read-Many) storage
  - Cold: Object Lock (immutable archive)
  - Archival process does NOT modify data (copy only)
  - Delete from hot ONLY after cold copy verified
```

---

## 7. Backup & Disaster Recovery

### 7.1 Backup Strategy

```
BACKUP FREQUENCY:
  Hot storage: Hourly snapshots
  Warm storage: Daily snapshots
  Cold storage: Monthly verification

BACKUP LOCATION:
  Primary region: Real-time replication (RPO < 1s)
  Secondary region: Daily backup (RPO < 24h)
  Off-site: Monthly archive (compliance)

IMMUTABILITY PROTECTION:
  Backups stored in immutable vaults
  Cannot be deleted or modified
  Compliance with data retention laws

RECOVERY TIME OBJECTIVE (RTO):
  < 1 hour: Full restoration to hot storage
  < 24 hours: Full restoration to warm storage
  < 7 days: Full restoration from cold storage
```

### 7.2 Disaster Recovery Guarantees

```
SCENARIO: Data loss in hot storage

Recovery Steps:
  1. Detect data loss (via checksums, consistency checks)
  2. Query secondary region (warm storage)
  3. Restore to primary region
  4. Verify immutability (all records intact)

Guarantee:
  - Decision outcomes unchanged
  - Workflow states unchanged
  - Event log complete
  - Audit trail intact

Time: < 1 hour recovery
Data Loss: Zero (immutability protection)
```

---

## 8. Data Constraints & Invariants

### 8.1 Constraints (Immutable)

| Table | Column | Constraint | Enforcement |
|-------|--------|-----------|------------|
| decisions | decision_id | UNIQUE within tenant | PK (tenant_id, decision_id) |
| decisions | outcome | IMMUTABLE after insert | TRIGGER (reject UPDATE) |
| decisions | idempotency_key | UNIQUE within tenant | UNIQUE index |
| workflows | workflow_id | UNIQUE within tenant | PK (tenant_id, workflow_id) |
| workflows | current_state | MUTABLE until terminal | Application-enforced |
| rules | rule_id | UNIQUE within tenant | PK (tenant_id, rule_id) |
| rules | status | IMMUTABLE (ACTIVE→DEPRECATED only) | TRIGGER (reject invalid transitions) |
| event_log | event_id | UNIQUE forever | PK (event_id) |
| event_log | * | INSERT only | TRIGGER (reject UPDATE, DELETE) |
| approvals | approval_id | UNIQUE | PK (approval_id) |
| approvals | * | INSERT only | TRIGGER (reject UPDATE, DELETE) |

### 8.2 Cross-Table Invariants

```
INVARIANT 1: Decision ↔ Workflow Relationship
  If decision.outcome = REQUIRE_APPROVAL:
    MUST have workflow with same decision_id
  If decision.outcome = ALLOWED or DENIED:
    MUST NOT have workflow

Enforcement: Application-enforced (single atomic transaction)

INVARIANT 2: Workflow ↔ Approval Records
  If workflow.state = APPROVED:
    MUST have approval record with action = "APPROVED"
  If workflow.state = REJECTED:
    MUST have approval record with action = "REJECTED"

Enforcement: Application-enforced (single atomic transaction)

INVARIANT 3: Tenant Isolation
  decision.tenant_id = workflow.tenant_id (if related)
  approval.tenant_id = workflow.tenant_id
  event.tenant_id = aggregate's tenant_id

Enforcement: Query-level (no cross-tenant access possible)

INVARIANT 4: Immutability of Outcomes
  decision.outcome never changes (no UPDATE allowed)
  decision.rule_matched never changes
  workflow.state immutable after terminal state

Enforcement: Triggers (reject UPDATE operations)
```

---

## 9. Data Size & Growth Estimates

### 9.1 Storage Projections (1M Tenants, Mixed Scale)

| Component | Per Year | Total 7-Year | Notes |
|-----------|----------|--------------|-------|
| Decisions | 100B @ 2KB = 200TB | 1.4PB | Hot: 90d, rest archived |
| Workflows | 50B @ 1KB = 50TB | 350TB | Sequential approval only |
| Events | 150B @ 500B = 75TB | 525TB | Append-only, immutable |
| Rules | 1M @ 500B = 500MB | 3.5GB | Reference data, slow growth |
| Approvals | 50B @ 200B = 10TB | 70TB | Immutable approval history |
| **TOTAL** | | **~2.5PB** | Includes replicas, backups |

### 9.2 Growth Rate (Per Tenant)

```
Small Tenant (100 decisions/day):
  Decisions: ~2GB/year
  Workflows: ~500MB/year
  Events: ~1GB/year
  Total: ~3.5GB/year

Medium Tenant (10K decisions/day):
  Decisions: ~200GB/year
  Workflows: ~50GB/year
  Events: ~100GB/year
  Total: ~350GB/year

Large Tenant (1M decisions/day):
  Decisions: ~20TB/year
  Workflows: ~5TB/year
  Events: ~10TB/year
  Total: ~35TB/year
```

---

## 10. Summary: Data Model is Append-Only & Immutable

✅ **Append-Only**: Decisions, Workflows, Events, Approvals never mutated
✅ **Tenant-Partitioned**: Hard isolation boundary (no cross-tenant leaks)
✅ **Indexed for Performance**: Critical path queries < 10ms
✅ **Immutable Snapshots**: Context, outcomes, state history preserved
✅ **Audit Trail**: Complete event log for compliance
✅ **Archival Strategy**: Hot/Warm/Cold with retention policies
✅ **Backup Protected**: Immutable vaults, RTO < 1 hour
✅ **Constraints Enforced**: Triggers prevent corruption

**Status**: Data Persistence Model complete, ready for review.

**Next**: Await feedback before locking.
