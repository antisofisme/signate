# INFRA-LAY3-002: Core Service Implementation Standards

**VERSION**: Layer 3 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-28

---

## Overview

This document defines **implementation standards** for Infra Core service.

- **Scope**: Rule evaluation, decision creation, workflow state machine, event emission, transaction handling
- **Source of Truth**: INFRA-LAY1-001 (SDK Contracts), INFRA-DEC-001/002/003 (decision/tenancy/rule models)
- **Constraint**: Core is single source of truth for decisions and workflows; all reads use data persistence layer

**Key Principle**: Core is the **decision engine**, not an orchestrator. It evaluates rules, creates decisions, manages workflow state, and emits immutable events.

---

## 1. Rule Evaluation Engine Standards

### 1.1 Rule Evaluation Semantics

```
REQUIREMENT: Rule evaluation MUST be deterministic and reproducible.

Definition: Deterministic
  - Same (rule_set, context) = same outcome, every time
  - No random behavior, no time-based logic, no external state
  - Outcome must be logged and auditable

Evaluation Order:
  - Rules evaluated in explicit list order (INFRA-DEC-003)
  - No priority field (priority would violate determinism)
  - First rule that matches → outcome determined
  - Remaining rules skipped

Example (3-rule RuleSet):
  Rule 1: "amount > 10000" → DENY
  Rule 2: "department == 'accounting'" → ALLOW
  Rule 3: "default rule" → REQUIRE_APPROVAL

  Context: {amount: 15000, department: "accounting"}
    → Rule 1 matches (amount > 10000) → outcome = DENY
    → Rules 2, 3 skipped
    → Result: DENY (rule_matched: "Rule 1")
```

### 1.2 Condition Evaluation Standards

```
REQUIREMENT: Conditions MUST support scalar operations only.

Supported Condition Types:

1. Numeric Comparisons
   - context.amount > 10000
   - context.approval_level == 3
   - context.retry_count <= 5
   - Operators: ==, !=, <, <=, >, >=

2. String Comparisons
   - context.department == "accounting"
   - context.request_type != "void"
   - Case-sensitive matching only
   - Operators: ==, !=, contains (substring match)

3. Boolean Conditions
   - context.is_override == true
   - context.is_final_approval == false
   - Operators: ==, !=

4. Null Checks
   - context.approver_user_id == null  (field missing)
   - context.approver_user_id != null  (field present)

5. Compound Conditions
   - (context.amount > 10000) AND (context.department == "accounting")
   - (context.approval_level >= 2) OR (context.is_final == true)
   - NOT (context.is_void == true)
   - Operators: AND, OR, NOT (boolean logic)

6. Nesting Limits
   - Maximum nesting depth: 3
   - Example: ((A AND B) OR (C AND D)) - depth 2 (valid)
   - Example: (((A AND B) OR C) AND D) - depth 3 (valid)
   - Example: ((((A AND B) OR C) AND D)) - depth 4 (INVALID)
   - Rationale: comprehensibility, maintainability, performance, risk mitigation

NOT Supported:
  ❌ Regex matching (too expressive, performance risk)
  ❌ Range operations (use AND instead)
  ❌ List/array operations (context is flat)
  ❌ Time-based logic (would violate determinism)
  ❌ External API calls (would violate determinism)
```

### 1.3 Rule Evaluation Error Handling

```
SCENARIO 1: Condition evaluation succeeds
  Rule: "context.amount > 10000" AND "context.department == 'accounting'"
  Context: {amount: 15000, department: "accounting"}
  Result: Condition TRUE → Rule matches → Apply action

SCENARIO 2: Missing field in context
  Rule: "context.approver_id == 'user-123'"
  Context: {} (missing approver_id field)
  Result: Condition FALSE (null != 'user-123') → Rule does NOT match
  Action: Continue to next rule
  Outcome: If no rules match → DENIED (fail-closed)

SCENARIO 3: Type mismatch (context field is wrong type)
  Rule: "context.amount > 10000"
  Context: {amount: "fifteen thousand"} (string, not number)
  Result: Condition evaluation ERROR
  Status: Rule evaluation fails, outcome → DENIED + log error
  Alert: rule_evaluation_error (CMS admin notified)

SCENARIO 4: Null dereference
  Rule: "context.user.id == 'user-123'"
  Context: {user: null}
  Result: Error (object nesting not supported)
  Status: Invalid rule definition
  Action: CMS must provide flat rule conditions only

SCENARIO 5: Context field is null
  Rule: "context.amount > 10000"
  Context: {amount: null}
  Result: Condition FALSE (null > 10000 is false)
  Action: Continue to next rule
  Outcome: If no rules match → DENIED (fail-closed)
```

### 1.4 Rule Evaluation Performance Standards

```
REQUIREMENT: Rule evaluation MUST complete within SLA.

SLA Targets (from INFRA-LAY2-002):
  - p95: < 45ms
  - p99: < 75ms

Performance Standards:

RULE 1: Evaluation Algorithm Efficiency
  - Linear evaluation (O(n) where n = number of rules)
  - No nested loops, no exponential operations
  - Short-circuit on first match (no evaluation of remaining rules)
  - Typical: 1,000 rules evaluated in < 40ms

RULE 2: Context Access Speed
  - Context lookup: O(1) (direct field access)
  - No sequential search, no index building
  - All context fields available immediately

RULE 3: Caching Considerations
  - Rule definitions CACHED in-memory (per tenant, per decision_type)
  - Cache invalidation: < 2 seconds after CMS rule change
  - Stale reads possible but bounded (2 second window)

RULE 4: Timeout Protection
  - Individual rule evaluation: max 5 seconds per rule
  - Total decision latency: max 100ms (p95 target)
  - If any rule exceeds timeout → rule evaluation error → outcome DENIED

EXAMPLE: Decision Latency Breakdown (80ms total)
  T0: SDK call received
  T0+2ms: Request validation
  T0+3ms: Tenant isolation check
  T0+4ms: Load rule set from cache (or database)
  T0+45ms: Evaluate rules (worst case: all rules, no early match)
  T0+50ms: Decision persisted (atomic with event_log INSERT)
  T0+70ms: Event emitted (async, non-blocking)
  T0+80ms: Response returned
  → Latency: 80ms (within p95 < 100ms SLA)
```

---

## 2. Decision Creation Transaction Standards

### 2.1 Decision Record Structure & Immutability

```
REQUIREMENT: Decision record MUST be immutable and internally consistent.

Decision Schema (at time of creation):
{
  decision_id: uuid,                    // immutable, globally unique
  tenant_id: uuid,                      // immutable, partition key
  decision_type: string,                // immutable, e.g., "accounting.journal_approval"
  created_at: timestamp,                // immutable, decided_at
  context: object,                      // immutable, sanitized context
  outcome: ALLOWED | DENIED | REQUIRE_APPROVAL,  // immutable
  rule_matched: string,                 // immutable, which rule matched (or null if none)
  rule_version: string,                 // immutable, rule version used
  approval_workflow_id: uuid | null,    // immutable, link to workflow if outcome = REQUIRE_APPROVAL
  idempotency_key: string,              // immutable, for deduplication
  latency_ms: number,                   // immutable, SDK→Core latency
  metadata: object                      // immutable, trace_id, requester_user_id
}

Immutability Enforcement (INFRA-LAY2-003):
  Layer 1: DB role permissions (REVOKE UPDATE, REVOKE DELETE)
  Layer 2: Database triggers (reject any UPDATE/DELETE attempts)
  Layer 3: Storage immutability (WORM on warm, Object Lock on cold)

Critical Field: outcome
  - LOCKED at creation time
  - NEVER changes, even if rules change later
  - Proof: compare decided_at with rule version → explains outcome
```

### 2.2 Idempotency Deduplication

```
REQUIREMENT: Same (idempotency_key, tenant_id, decision_type) → same decision_id.

Idempotency Semantics:

REQUEST 1 (First time):
  POST /decisions
  {
    decision_type: "accounting.journal_approval",
    tenant_id: "hotel-123",
    context: {journal_id: "j-123", amount: 5000},
    idempotency_key: "req-abc-123"
  }
  → Core evaluates rules
  → Decision created: {decision_id: "dec-xyz-789", outcome: "ALLOWED"}
  → Idempotency key stored: (idempotency_key: "req-abc-123", decision_id: "dec-xyz-789")

REQUEST 2 (Retry, identical):
  POST /decisions
  {
    decision_type: "accounting.journal_approval",
    tenant_id: "hotel-123",
    context: {journal_id: "j-123", amount: 5000},
    idempotency_key: "req-abc-123"
  }
  → Core checks: Is idempotency_key "req-abc-123" in cache?
  → YES: Return cached decision_id: "dec-xyz-789"
  → Latency: 1-10ms (cache hit)
  → No new decision created

REQUEST 3 (Retry, same key, different context):
  POST /decisions
  {
    decision_type: "accounting.journal_approval",
    tenant_id: "hotel-123",
    context: {journal_id: "j-123", amount: 10000},  // ← different amount
    idempotency_key: "req-abc-123"
  }
  → Core checks: Is idempotency_key "req-abc-123" in cache?
  → YES, but context is different
  → Return 409 Conflict
  {
    "error_code": "CONFLICT",
    "existing_decision_id": "dec-xyz-789",
    "message": "Idempotency key used with different context"
  }
  → SDK raises ConflictError to caller
  → Caller should NOT retry (indicates application bug)

Idempotency Cache Strategy:
  - In-memory cache (hot storage, 90 days)
  - Key: (tenant_id, idempotency_key)
  - Value: decision_id
  - TTL: 24 hours (minimum, configurable)
  - Eviction: LRU or time-based
  - Backup: database table for durability (optional, but recommended)

PHASE 1 CLARIFICATION: Idempotency Contract
  - Idempotency enforced via UNIQUE(tenant_id, idempotency_key) database constraint
  - On retry (same idempotency_key):
    * Check database: SELECT decision_id FROM idempotency_cache
    * If found: return cached decision_id (no new decision created)
    * If not found: evaluate rules, create new decision (idempotency_key was not previously used)
  - On conflict (same idempotency_key, different context):
    * Database lookup returns existing decision_id
    * Compare context: if different, return 409 Conflict
  - Phase 1 uses database idempotency_cache table (persistent)
  - Phase 2 will add Redis caching layer on top of database guarantee
  - TTL semantics deferred to Phase 2 (Phase 1: cache persists until data retention expires)
```

### 2.3 Decision Creation Transaction

```
REQUIREMENT: Decision creation MUST be atomic.

Transaction Steps (ACID guarantee):

BEGIN TRANSACTION

STEP 1: Validate tenant isolation
  - Verify tenant_id exists and is active
  - Verify requester has access to this tenant
  - Error: 403 Forbidden (cross-tenant access attempt)

STEP 2: Load rule set
  - Query rule_sets table WHERE tenant_id = ? AND decision_type = ?
  - If not found: outcome = DENIED (fail-closed, per INFRA-DEC-001)
  - If found: load rule definitions in order

STEP 3: Evaluate rules
  - For each rule in order:
    - Evaluate condition(s)
    - If condition TRUE: action.outcome = rule action, break
    - If condition FALSE: continue to next rule
  - If no rule matches: outcome = DENIED (fail-closed)

STEP 4: Create decision record
  INSERT INTO decisions (
    decision_id, tenant_id, decision_type, context, outcome,
    rule_matched, rule_version, approval_workflow_id,
    idempotency_key, latency_ms, created_at, metadata
  )
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

STEP 5: If outcome = REQUIRE_APPROVAL, create workflow
  INSERT INTO workflows (
    workflow_id, decision_id, tenant_id, current_state, created_at, approver_role
  )
  VALUES ('PENDING_APPROVAL', ?, ?, ?, ?, ?)

STEP 6: Emit event (atomic with decision)
  INSERT INTO event_log (
    event_id, event_type, tenant_id, aggregate_id, payload, occurred_at
  )
  VALUES (
    uuid(),
    'decision.created' or 'workflow.created',
    ?, ?, {...}, now()
  )

STEP 7: Store idempotency key (durability)
  INSERT INTO idempotency_cache (
    tenant_id, idempotency_key, decision_id, created_at
  )
  VALUES (?, ?, ?, now())

COMMIT TRANSACTION

Critical: All steps MUST succeed together or ALL roll back.
  - No partial creation (decision without event)
  - No partial creation (workflow without decision)
  - Atomicity guaranteed at database level

PHASE 1 CLARIFICATION: Transaction Discipline Rule (Code Review Checklist)
  ✓ All state mutations (decision, workflow, event_log) occur in ONE transaction
  ✓ No background jobs or deferred operations
  ✓ No cross-transaction dependencies (e.g., "first insert decision, later insert event")
  ✓ BEGIN TRANSACTION at method start, COMMIT at method end
  ✓ All database writes within transaction
  ✓ Immutable record checks (outcome != NULL, event_id != NULL, etc.) done after transaction

  Code Review Checklist:
    [ ] Does this method insert to decisions table?
    [ ] Does this method insert to event_log table?
    [ ] Are BOTH inserts in the SAME transaction?
    [ ] Are there any external service calls (webhooks, API calls) INSIDE the transaction?
        (If yes: move outside transaction, do after COMMIT)
    [ ] Are there any cache writes INSIDE the transaction?
        (If yes: move outside transaction or use database as source of truth)
```

### 2.4 Decision Retrieval & Immutability Verification

```
REQUIREMENT: Decisions retrieved from storage MUST be immutable and unchanged.

Retrieval Pattern:

GET /decisions/{decision_id}
  1. Validate tenant_id in request
  2. Query decisions table:
     SELECT * FROM decisions
     WHERE decision_id = ? AND tenant_id = ?
  3. Verify outcome != NULL (proof of immutability)
  4. Return decision record (read-only)

Immutability Verification Checks:

CHECK 1: Outcome is populated
  - outcome IN (ALLOWED, DENIED, REQUIRE_APPROVAL)
  - If NULL: data corruption detected (alert immediately)

CHECK 2: created_at timestamp is immutable
  - created_at <= now()
  - created_at matches event_log entry
  - If mismatch: data corruption detected

CHECK 3: context snapshot matches original
  - context is JSON snapshot (no changes after creation)
  - If modified: UPDATE attempt detected (trigger should have prevented)

CHECK 4: No UPDATE/DELETE operations detected
  - Query operations_audit table
  - SELECT COUNT(*) WHERE resource_id = ? AND operation_type IN (UPDATE, DELETE)
  - Expected: 0 (all should be rejected by trigger)
```

---

## 3. Workflow State Machine Standards

### 3.1 Workflow State Transitions

```
REQUIREMENT: Workflow transitions MUST follow explicit state machine.

State Diagram:

               ┌─ APPROVED ─┐
               │            │
PENDING_APPROVAL ┤ REJECTED ─┤→ TERMINAL
               │            │
               │ DELEGATED ─┤
               │            │
               └─ ESCALATED─┘

States:
  - PENDING_APPROVAL: Initial state (awaiting approval decision)
  - APPROVED: Terminal state (approval granted)
  - REJECTED: Terminal state (approval denied)
  - DELEGATED: Intermediate state (delegated to another approver, then PENDING_APPROVAL)
  - ESCALATED: Intermediate state (escalated to higher authority, then PENDING_APPROVAL or terminal)

Allowed Transitions:

From PENDING_APPROVAL:
  → APPROVED (approver approved)
  → REJECTED (approver rejected)
  → DELEGATED (approver delegated to another user/role, then → PENDING_APPROVAL)
  → ESCALATED (approval timeout exceeded, escalate to higher authority, then → PENDING_APPROVAL)

From DELEGATED:
  → PENDING_APPROVAL (delegate flow complete, back to approval wait)

From ESCALATED:
  → PENDING_APPROVAL (escalation complete, awaiting new approver)

Terminal States:
  - APPROVED (workflow complete, decision outcome = REQUIRE_APPROVAL + workflow approved)
  - REJECTED (workflow complete, decision outcome = REQUIRE_APPROVAL + workflow rejected)

Forbidden Transitions:
  ❌ APPROVED → REJECTED (terminal, no reversal)
  ❌ APPROVED → PENDING_APPROVAL (terminal, no reversal)
  ❌ REJECTED → APPROVED (terminal, no reversal)
  ❌ Terminal → Terminal (only one terminal state reached)
  ❌ Direct PENDING_APPROVAL → DELEGATED → APPROVED (must go through PENDING_APPROVAL between delegation)
```

### 3.2 Workflow Approval Action Standards

```
REQUIREMENT: Approval actions MUST enforce role-based access.

Approval Action: approveWorkflow

Input:
{
  workflow_id: uuid,
  approver_role: string (e.g., "CFO"),
  tenant_id: uuid,
  comment: string (optional)
}

Validation:
  1. Verify workflow exists: WHERE workflow_id = ? AND tenant_id = ?
  2. Verify current_state = PENDING_APPROVAL
  3. Verify approver_role matches workflow.approver_role
     - If mismatch: Error 403 Forbidden (wrong role)
  4. Verify requester_user_id has role approver_role
     - Delegated to Application Adapter (Core does NOT validate)
     - Core trusts Adapter to resolve role → user_id correctly

Execution:
  1. Create workflow_transition record (append-only):
     INSERT INTO workflow_transitions (
       workflow_id, from_state, to_state, action, acted_by_user_id, comment, created_at
     )
     VALUES ('PENDING_APPROVAL', 'APPROVED', 'APPROVED', ?, ?, now())

  2. Update workflow current_state:
     UPDATE workflows SET current_state = 'APPROVED' WHERE workflow_id = ?

  3. Emit event:
     INSERT INTO event_log (
       event_type, aggregate_id, payload
     )
     VALUES ('workflow.approved', ?, {...})

  4. Return success
     {workflow_id, current_state: 'APPROVED', timestamp}

Reject Workflow: Similar flow, but state → REJECTED

Delegate Workflow: More complex (see 3.3)

Escalate Workflow: Automatic on timeout (see 3.4)
```

### 3.3 Delegation & Escalation Standards

```
REQUIREMENT: Delegation and escalation MUST preserve audit trail.

Delegation Flow:

Input:
{
  workflow_id: uuid,
  approver_role: "CFO",
  delegated_to_user_id: "user-cfo-backup",
  tenant_id: uuid,
  reason: "Primary CFO on leave"
}

Execution:
  1. Verify workflow exists and current_state = PENDING_APPROVAL
  2. Verify delegated_to_user_id has approver_role
     - Delegated to Application Adapter
  3. Create workflow_transition (from_state=PENDING_APPROVAL, to_state=DELEGATED):
     INSERT INTO workflow_transitions (...)
     VALUES ('PENDING_APPROVAL', 'DELEGATED', 'DELEGATED', ...)
  4. Update workflow (still PENDING_APPROVAL, but track delegation):
     UPDATE workflows SET delegated_to_user_id = ? WHERE workflow_id = ?
  5. Emit event: workflow.delegated
  6. Return success

Escalation Flow (Automatic):

Trigger: workflow_pending_duration > escalation_timeout

Process:
  1. Scheduled job: Check all PENDING_APPROVAL workflows
     SELECT * FROM workflows
     WHERE current_state = 'PENDING_APPROVAL'
       AND created_at < now() - escalation_timeout
  2. For each stale workflow:
     a. Look up escalation_path (from rule or config)
     b. Create workflow_transition (from_state=PENDING_APPROVAL, to_state=ESCALATED)
     c. Update workflow: escalated_to_user_id = ?
     d. Emit event: workflow.escalated
  3. Alert: Escalation occurred (PagerDuty, email, etc.)

Transition to New Approver (after delegation/escalation):
  1. Workflow remains in PENDING_APPROVAL (after delegate/escalate completes)
  2. New approver_role set (if escalation)
  3. Notification sent to new approver
  4. New approver can approve/reject/delegate/escalate
```

### 3.4 Workflow Terminal State Verification

```
REQUIREMENT: Terminal states MUST be final and immutable.

Terminal State Check:

GET /workflows/{workflow_id}
  - Current_state must be APPROVED, REJECTED, ESCALATED (if stuck), or DELEGATED (if stuck)
  - If terminal (APPROVED or REJECTED): no further transitions possible
  - If stuck (ESCALATED or DELEGATED): indicates operational issue

Verification:
  - Terminal workflows have completed_at timestamp
  - Terminal workflows cannot transition further
  - Query workflow_transitions to see full audit trail
  - Decision outcome + workflow state together tell complete story

Example Query:
  SELECT d.decision_id, d.outcome, w.workflow_id, w.current_state, wt.*
  FROM decisions d
  LEFT JOIN workflows w ON d.approval_workflow_id = w.workflow_id
  LEFT JOIN workflow_transitions wt ON w.workflow_id = wt.workflow_id
  WHERE d.decision_id = ? AND d.tenant_id = ?
  ORDER BY wt.created_at

  Result:
    - Decision: outcome=REQUIRE_APPROVAL
    - Workflow: state=APPROVED
    - Transitions: PENDING_APPROVAL → DELEGATED → PENDING_APPROVAL → APPROVED
    - Audit trail: Complete history of all state changes
```

---

## 4. Event Emission Standards

### 4.1 Event Schema & Atomicity

```
REQUIREMENT: Event MUST be emitted atomically with decision/workflow.

Event Schema:
{
  event_id: uuid,                    // globally unique, immutable
  event_type: string,                // (decision.created | decision.allowed | ...)
  tenant_id: uuid,                   // partition key, immutable
  aggregate_id: uuid,                // decision_id or workflow_id
  aggregate_type: 'decision' | 'workflow',
  occurred_at: timestamp,            // immutable, time of event
  recorded_at: timestamp,            // when persisted
  payload: object,                   // event-specific data
  metadata: {
    source: 'core' | 'cms' | 'adapter',
    caused_by_user_id: uuid,
    trace_id: uuid,
    schema_version: string
  },
  schema_version: string             // for schema evolution
}

Atomicity Requirement:

Event MUST be inserted in SAME transaction as decision/workflow:

BEGIN TRANSACTION
  1. Insert decision record
  2. Insert workflow record (if REQUIRE_APPROVAL)
  3. Insert event record into event_log
COMMIT TRANSACTION

Guarantee:
  - No decision without event (event_log is source of truth)
  - No workflow without decision (workflow links to decision_id)
  - No partial state (all-or-nothing semantics)
  - event_log is immutable (APPEND-ONLY, no UPDATE/DELETE)
```

### 4.2 Event Ordering & Delivery

```
REQUIREMENT: Events MUST be ordered per tenant and retrievable.

Event Ordering:

Events are ordered by:
  1. Primary: tenant_id (partition)
  2. Secondary: occurred_at (timestamp)
  3. Tertiary: event_id (tiebreaker, if same timestamp)

Ordering Guarantee:
  - Events for same tenant retrieved in chronological order
  - No reordering across tenants (parallel streams)
  - Timestamp resolution: millisecond precision

Delivery Semantics:

Core publishes events to external bus (asynchronously):
  - Persistence: event_log (database, reliable)
  - Delivery: event bus (Kafka, RabbitMQ, Pub/Sub, best-effort)
  - SLA: at-least-once delivery (consumer deduplicates by event_id)

Event Publication Flow:
  1. Event inserted into event_log (transaction commit)
  2. Core publishes event to bus (async, non-blocking)
  3. External bus delivers to subscribers
  4. Subscribers process event, deduplicate by event_id
  5. If failure: subscriber retries (bus guarantees delivery, or subscriber manual retry)

Event Availability:
  - event_log is source of truth (always available)
  - External bus is best-effort (may lose events, subscriber must re-query event_log)
  - Consumers can re-query event_log by timestamp range if bus fails
```

### 4.3 Event Types & Payloads

```
REQUIREMENT: All event types MUST be defined with schema.

Decision Events:

EVENT 1: decision.created
  Trigger: Decision record created (all outcomes)
  Payload:
  {
    "decision_id": uuid,
    "tenant_id": uuid,
    "decision_type": string,
    "outcome": "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL",
    "rule_matched": string | null,
    "context_summary": object (sanitized),
    "latency_ms": number
  }

Workflow Events:

EVENT 2: workflow.pending_approval
  Trigger: Workflow created (outcome=REQUIRE_APPROVAL)
  Payload:
  {
    "workflow_id": uuid,
    "decision_id": uuid,
    "approver_role": string,
    "created_at": timestamp
  }

EVENT 3: workflow.approved
  Trigger: approveWorkflow called
  Payload:
  {
    "workflow_id": uuid,
    "decision_id": uuid,
    "approver_role": string,
    "acted_by_user_id": uuid,
    "comment": string | null,
    "approved_at": timestamp
  }

EVENT 4: workflow.rejected
  Trigger: rejectWorkflow called
  Payload:
  {
    "workflow_id": uuid,
    "decision_id": uuid,
    "approver_role": string,
    "acted_by_user_id": uuid,
    "reason": string | null,
    "rejected_at": timestamp
  }

EVENT 5: workflow.delegated
  Trigger: delegateWorkflow called
  Payload:
  {
    "workflow_id": uuid,
    "decision_id": uuid,
    "from_approver_role": string,
    "delegated_to_user_id": uuid,
    "acted_by_user_id": uuid,
    "reason": string,
    "delegated_at": timestamp
  }

EVENT 6: workflow.escalated
  Trigger: Escalation timeout exceeded
  Payload:
  {
    "workflow_id": uuid,
    "decision_id": uuid,
    "from_approver_role": string,
    "escalated_to_role": string,
    "escalation_reason": string,
    "escalated_at": timestamp
  }

Additional Events:

EVENT 7: security_event.immutability_violation_attempted
  Trigger: UPDATE/DELETE attempt on immutable record
  Payload:
  {
    "violation_type": "UPDATE_ATTEMPT" | "DELETE_ATTEMPT",
    "resource_type": "decision" | "workflow" | "event_log",
    "resource_id": uuid,
    "attempted_by_user_id": uuid | null,
    "timestamp": timestamp
  }

EVENT 8: security_event.tenant_isolation_violation
  Trigger: Cross-tenant access attempt detected
  Payload:
  {
    "source_tenant_id": uuid,
    "target_tenant_id": uuid,
    "attempted_by_user_id": uuid | null,
    "query_type": string,
    "timestamp": timestamp
  }
```

---

## 5. Tenant Isolation Enforcement Standards

### 5.1 Database-Level Isolation

```
REQUIREMENT: Tenant isolation MUST be enforced at database layer (not application convention).

Option A: Row-Level Security (RLS) — Recommended

Setup:
  1. Create RLS policy on all tables (decisions, workflows, event_log, rules, etc.)
  2. Policy rule: WHERE tenant_id = current_tenant_id()
  3. current_tenant_id() = SET BY application (session variable or connection context)

Implementation:
  -- PostgreSQL example
  ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;

  CREATE POLICY decisions_tenant_isolation ON decisions
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

  -- Before each query, set tenant context
  SET app.current_tenant_id = 'hotel-123';

  -- Now all queries automatically filtered
  SELECT * FROM decisions;  -- implicit WHERE tenant_id = 'hotel-123'

Enforcement:
  - Query without tenant_id filter: RLS still applies
  - Query for wrong tenant: RLS returns 0 rows (not error, transparent)
  - Attempt to INSERT cross-tenant: RLS rejects (CHECK constraint)

Option B: Schema-per-Tenant (for hot tenants)

Setup:
  1. Each tenant has separate schema (schema_hotel-123, schema_restaurant-456)
  2. Tables replicated per schema
  3. Connection string includes schema name
  4. Queries automatically scoped to schema

Implementation:
  -- Create tenant schema
  CREATE SCHEMA schema_hotel-123;
  CREATE TABLE schema_hotel-123.decisions (...);
  CREATE TABLE schema_hotel-123.workflows (...);

  -- Application connection
  SET search_path = schema_hotel-123;

  -- Now all queries scoped to schema
  SELECT * FROM decisions;  -- implicit FROM schema_hotel-123.decisions

Enforcement:
  - Schema provides hard boundary
  - Cross-schema access requires explicit schema.table notation
  - No implicit cross-tenant queries possible

Option C: Database-per-Tenant (for enterprise)

Setup:
  1. Each tenant has separate database instance
  2. Connection string includes database name
  3. Complete isolation (no shared infrastructure)

Implementation:
  -- Connection pool per tenant
  database_pools = {
    'hotel-123': postgresql://host/db_hotel_123,
    'restaurant-456': postgresql://host/db_restaurant_456
  }

  -- Application routing
  db = database_pools[current_tenant_id]
  result = db.query("SELECT * FROM decisions")

Enforcement:
  - Database isolation is strongest (no shared resources)
  - No RLS policy possible (databases are isolated)
  - Higher operational complexity
```

### 5.2 Tenant Isolation Validation

```
REQUIREMENT: All requests MUST include tenant_id and validate isolation.

Request Validation:
  1. Extract tenant_id from request header (X-Tenant-ID)
  2. Validate tenant_id format (pattern: ^[a-z0-9_-]{3,64}$)
  3. Verify tenant is active (not deleted, not suspended)
  4. Set session context: SET app.current_tenant_id = tenant_id

Query Validation:
  - All queries MUST include tenant_id in WHERE clause (as backup to RLS)
  - SELECT * FROM decisions WHERE tenant_id = ? AND ...
  - Never: SELECT * FROM decisions WHERE ... (missing tenant_id filter)

Query Audit:
  - Log all queries with tenant_id
  - Alert if query missing tenant_id filter
  - Alert if RLS policy violated (cross-tenant data returned)

Verification:
  - Query operations_audit to verify no cross-tenant access
  - Metric: cross_tenant_access_attempts (must be 0)
  - Alert: CRITICAL if any cross-tenant attempt detected
```

---

## 6. Guard Rails: Core Service Constraints

### 6.1 Non-Negotiable Guard Rails

```
GUARDRAIL 1: Decision Immutability
  - Outcome locked at creation time
  - No UPDATE/DELETE operations allowed
  - Trigger enforces (BEFORE UPDATE/DELETE RAISE EXCEPTION)
  - Multi-layer enforcement (DB roles + triggers + storage locks)

GUARDRAIL 2: Rule Determinism
  - Same context = same outcome, every time
  - No random, no time-based, no external state
  - Reproducible for audit and verification

GUARDRAIL 3: Tenant Isolation (Hard)
  - Database-enforced (RLS, schema, or database-per-tenant)
  - Not application convention
  - Query without tenant_id filter → RLS rejects
  - Cross-tenant attempt → FORBIDDEN (403)

GUARDRAIL 4: Event Atomicity
  - Event persisted in SAME transaction as decision/workflow
  - No decision without event
  - event_log is source of truth (append-only)

GUARDRAIL 5: Workflow State Machine
  - Only allowed transitions per state machine
  - No reversal of terminal states
  - Transitions logged in workflow_transitions (append-only)

GUARDRAIL 6: Idempotency Deduplication
  - Same idempotency_key = same decision_id (no duplicates)
  - Conflict on key reuse with different context (409)
  - Cache durability: at least 24 hours

GUARDRAIL 7: Fail-Closed Security
  - No matching rule → outcome DENIED
  - No exceptions, no default ALLOW
  - Rationale: Deny by default (secure)

GUARDRAIL 8: Audit Trail Immutability
  - All state changes logged (workflow_transitions)
  - All security events logged (immutability violations, cross-tenant attempts)
  - Logs are append-only, no modification
```

### 6.2 Delegated Responsibilities (NOT Core)

```
Core does NOT implement:

❌ Business logic (rule logic is business config, not Core code)
❌ User identity validation (delegated to Application Adapter)
❌ Permission checking (delegated to Application Adapter)
❌ Role resolution (user_id for role, delegated to Adapter)
❌ Notification sending (delegated to Adapter)
❌ Event consumption (delegated to subscribers)
❌ Approval workflow orchestration beyond state machine (no choreography)
❌ External API calls from rules (would violate determinism)
```

---

## 7. Core Service Implementation Checklist

```
Before releasing Core, verify:

RULE EVALUATION:
  ✓ Deterministic (same context = same outcome)
  ✓ First-match-wins semantics
  ✓ No random, no time-based logic
  ✓ Condition nesting max 3 levels
  ✓ Error handling (type mismatch → outcome DENIED, log error)
  ✓ Performance < 45ms p95 (SLA target)

DECISION CREATION:
  ✓ Atomic transaction (all-or-nothing)
  ✓ Immutability locked at creation
  ✓ outcome != NULL (proof of immutability)
  ✓ Idempotency deduplication (same key → same decision_id)
  ✓ Conflict detection (key reuse with different context)
  ✓ Latency < 100ms p95 (SLA target)

WORKFLOW STATE MACHINE:
  ✓ State transitions follow explicit state machine
  ✓ No reversal of terminal states
  ✓ workflow_transitions logged (append-only)
  ✓ Approval validation (role matches workflow.approver_role)
  ✓ Delegation flow (preserve audit trail)
  ✓ Escalation on timeout (automatic job)

EVENT EMISSION:
  ✓ Event atomic with decision/workflow (same transaction)
  ✓ event_log is append-only (no UPDATE/DELETE)
  ✓ event_id unique (no duplicates)
  ✓ Event ordering per tenant (by occurred_at)
  ✓ Event publication (async to external bus)
  ✓ Event schema versioning

TENANT ISOLATION:
  ✓ Database-enforced (RLS, schema, or database-per-tenant)
  ✓ RLS policy on all tables
  ✓ Query validation (tenant_id in WHERE clause)
  ✓ Cross-tenant attempt detection (403 Forbidden)
  ✓ Audit logging (cross_tenant_access_attempts metric)

SECURITY & AUDIT:
  ✓ Immutability triggers (BEFORE UPDATE/DELETE RAISE EXCEPTION)
  ✓ Update/Delete attempt logging (security_violation_attempt event)
  ✓ Immutability metric (must be 0)
  ✓ operations_audit table logging
  ✓ Trace ID propagation (X-Trace-ID header → logs)

TESTING:
  ✓ Unit tests for rule evaluation (determinism, nesting, conditions)
  ✓ Unit tests for decision creation (transaction, immutability, idempotency)
  ✓ Unit tests for workflow state machine (valid/invalid transitions)
  ✓ Integration tests with SDK (happy path, error cases)
  ✓ Integration tests with idempotency (cache hits, conflicts)
  ✓ Integration tests with tenant isolation (RLS enforcement)
  ✓ Load tests (p95 < 100ms latency under 1000 rps)
  ✓ Security tests (immutability enforcement, cross-tenant prevention)
```

---

## 8. Summary: Core as Decision Engine

✅ **Rule Evaluation**: Deterministic, first-match-wins, fail-closed
✅ **Decision Creation**: Atomic, immutable, idempotent
✅ **Workflow State Machine**: Explicit states, audit trail, no reversal
✅ **Event Emission**: Atomic with decision/workflow, append-only
✅ **Tenant Isolation**: Database-enforced (RLS/schema/database-per-tenant)
✅ **Guard Rails**: Immutability, determinism, fail-closed, audit trail

**Status**: Layer 3.2 DRAFT, ready for review.

**Next**: CMS Implementation Standards (INFRA-LAY3-003).
