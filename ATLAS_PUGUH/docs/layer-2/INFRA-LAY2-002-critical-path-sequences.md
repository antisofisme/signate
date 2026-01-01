# INFRA-LAY2-002: Critical Path Sequences & Failure Modes

**VERSION**: Layer 2 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-27

---

## Overview

This document defines the **exact sequence** of operations for critical paths, **failure modes** at each step, and **recovery patterns**.

**Focus**: Timing, ordering, state consistency, idempotency, failure handling.

---

## 1. Decision Creation Critical Path (Detailed)

### 1.1 Full Sequence with Timing & State

```
╔════════════════════════════════════════════════════════════════╗
║ DECISION CREATION CRITICAL PATH                                ║
║ From: Application / SDK                                        ║
║ To: Core                                                       ║
║ SLA: < 100ms (p95: < 200ms)                                   ║
╚════════════════════════════════════════════════════════════════╝

TIME  STEP  ACTOR       ACTION                           STATE
────  ────  ──────      ────────────────────────────     ─────
T0    1     App         Calls SDK:                       App sends request
            (Thread)    createDecision(
                          decision_type,
                          context,
                          tenant_id
                        )

      2     SDK         Validate request                 Request in-flight
                        - tenant_id non-empty?
                        - decision_type matches pattern?
                        - context non-empty object?

T0+1ms 3    SDK        If validation FAILS:             SDK returns 400
                       return ERROR_400                 (no Core call)

      4     SDK        If validation PASSES:            Request approved
                       - Sanitize context (remove PII)
                       - Extract auth context
                       - Build Core request

T0+2ms 5    SDK        Call Core (HTTP POST)            Request in-flight
                       POST /v1/decisions
                       {
                         decision_type: string,
                         context: object (sanitized),
                         tenant_id: string,
                         requester_user_id: string,
                         idempotency_key?: string
                       }

                       [NETWORK LATENCY]

T0+10ms 6   Core       Receive request                  Request received
                       (from network)

      7     Core       Validate request                 Validating...
                       - tenant_id present?
                       - decision_type valid?
                       - context non-empty?

T0+11ms 8   Core       If validation FAILS:             Core returns error
                       return ERROR_400/409             (no decision created)

      9     Core       If validation PASSES:            Proceeding to eval
                       - Verify idempotency key
                       - Check if decision already created
                         with this key
                       - If yes: return cached decision
                         (idempotency guaranteed)

T0+12ms 10  Core       If NOT idempotent match:         Creating new decision
                       - Fetch rules for
                         (decision_type, tenant_id)
                       - If no rules: fail-closed
                         outcome = DENIED

      11    Core       Evaluate rules                   Rule evaluation
            (Eval)     - Iterate rules in order         in progress
                       - For each rule:
                         - Evaluate condition
                           against context
                         - If condition true:
                           outcome = rule.action
                           rule_matched = rule.name
                           STOP (first-match-wins)

T0+45ms 12   Core      Rule evaluation complete        Decision determined
                       outcome ∈ {
                         ALLOWED,
                         DENIED,
                         REQUIRE_APPROVAL
                       }

      13    Core       Create Decision record:          Decision immutable
                       - decision_id = uuid()
                       - Store in DB (immutable)
                       - Record timestamp
                       - Mark idempotency_key
                         as processed

T0+50ms 14   Core      If outcome = REQUIRE_APPROVAL:   Workflow creating
                       - Create Workflow:
                         - workflow_id = uuid()
                         - state = PENDING_APPROVAL
                         - approver_role = from rule
                         - escalation_timeout_at = +24h
                       - Store in DB

T0+55ms 15   Core      Emit events (async):             Events queued
                       - decision.created (async)
                       - decision.{allowed|denied|requires_approval}
                       - workflow.created (if approval)
                       (NO WAIT for events)

      16    Core       Build response                   Response building
                       {
                         status: "success",
                         decision: {
                           decision_id,
                           outcome,
                           rule_matched,
                           rule_version,
                           approval_workflow_id?
                         }
                       }

T0+60ms 17   Core      Return response (HTTP 200)       Response in-flight
                       [NETWORK LATENCY]

T0+70ms 18   SDK       Receive response                 Response received
                       Parse and return to App

T0+75ms 19   App       Handle decision                  App gets outcome
                       IF outcome = ALLOWED:
                         Proceed with operation
                       ELSE IF outcome = DENIED:
                         Show error to user
                       ELSE IF outcome = REQUIRE_APPROVAL:
                         Show approval UI
                         with workflow_id

T0+80ms ✓    COMPLETE  Decision created                 LOCKED & IMMUTABLE
                       immutable forever                (decision.outcome
                                                        never changes)

────────────────────────────────────────────────────────────────
TOTAL TIME: ~80ms (best case: ~50ms, p95: ~150-200ms)
STATE PERSISTED: Decision record + Workflow (if approval needed)
IDEMPOTENCY: By idempotency_key (same key = same decision_id)
EVENTS: Emitted async (no waiting)
────────────────────────────────────────────────────────────────
```

### 1.2 State Transitions During Decision Creation

```
PERSISTENCE POINTS (what is written to DB):

Point 1 (T0+50ms): Decision Record Created
  {
    decision_id: "dec-abc-123",
    tenant_id: "hotel-123",
    decision_type: "accounting.journal_approval",
    requester_user_id: "user-456",
    outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL",
    rule_matched: "rule_name_xyz",
    rule_version: "1.2",
    context_snapshot: { /* sanitized context */ },
    requested_at: "2025-12-27T10:30:01Z",
    decided_at: "2025-12-27T10:30:01.050Z",
    status: "COMPLETED"  // Immutable from this point
  }
  GUARANTEE: Never changes, never deleted

Point 2 (T0+55ms): Workflow Record Created (if approval needed)
  {
    workflow_id: "wf-xyz-789",
    decision_id: "dec-abc-123",
    tenant_id: "hotel-123",
    state: "PENDING_APPROVAL",
    approver_role: "CFO",
    escalation_target_role: "chief_finance_officer",
    escalation_timeout_at: "2025-12-28T10:30:01Z",
    created_at: "2025-12-27T10:30:01.055Z"
  }
  GUARANTEE: State mutable, but outcome=REQUIRE_APPROVAL immutable

Point 3 (T0+60ms): Events Queued (async, fire-and-forget)
  - decision.created
  - decision.{allowed|denied|requires_approval}
  - workflow.created (if approval)
  GUARANTEE: At-least-once delivery (no waiting for completion)
```

---

## 2. Failure Modes: Decision Creation

### 2.1 Failure at SDK Validation (T0+1ms)

**When**: SDK validation fails before Core call

**Failure Scenario**:
```
App sends: createDecision("accounting.journal_approval", {}, "")
           ↓ (empty context, missing tenant_id)

SDK validates:
  - context.length === 0? YES → FAIL
  - tenant_id present? NO → FAIL

SDK returns (immediate):
  {
    status: "error",
    error_code: "INVALID_REQUEST",
    message: "tenant_id is required and non-empty",
    details: { field: "tenant_id", reason: "MISSING" }
  }
```

**HTTP Status**: 400 Bad Request

**Recovery**:
- App fixes request (add tenant_id, populate context)
- App retries with corrected request
- Core never called (no wasted resources)
- No decision created (expected)

**Idempotency**: N/A (no decision created)

**Event Emission**: NONE

---

### 2.2 Failure at Core Validation (T0+11ms)

**When**: Core validation fails after receiving request

**Failure Scenario**:
```
SDK sends valid request to Core
  ↓
Core receives:
  decision_type: "invalid..type"  (malformed)

Core validates:
  - decision_type matches pattern? NO

Core returns (immediate):
  {
    status: "error",
    error_code: "INVALID_DECISION_TYPE",
    message: "decision_type format invalid",
    details: { expected: "{module}.{entity}.{action}" }
  }
```

**HTTP Status**: 400 Bad Request

**Recovery**:
- App fixes decision_type format
- App retries
- No decision created
- No workflow created

**Idempotency**: Not applicable (request never reached DB)

**Event Emission**: NONE

---

### 2.3 Failure: No Rules Configured (T0+45ms)

**When**: Core fetches rules, none found for decision_type in tenant

**Failure Scenario**:
```
Core loads rules for:
  decision_type: "unknown.decision_type"
  tenant_id: "hotel-123"

Rules not found in CMS/Core
  ↓
Core applies fail-closed guarantee:
  outcome = DENIED
```

**HTTP Status**: 200 Success (decision made)

**Response**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-xyz-789",
    "outcome": "DENIED",
    "rule_matched": null,
    "rule_matched_reason": "NO_RULES_CONFIGURED"
  }
}
```

**Recovery**:
- Admin/CMS must configure rules for decision_type
- Next decision with same decision_type will use new rules
- **Old decision remains DENIED** (immutable)

**Idempotency**: Idempotency key marks this decision as processed. Retrying with same key returns same decision_id (not re-evaluated).

**Event Emission**:
- decision.created (with outcome=DENIED)
- decision.denied (with reason="NO_RULES_CONFIGURED")

---

### 2.4 Failure: Rule Evaluation Error (T0+45ms)

**When**: Rule condition evaluation throws error (e.g., invalid syntax, null pointer)

**Failure Scenario**:
```
Core evaluates rule:
  condition: { field: "amount", operator: ">", value: 10000 }

Context missing "amount" field
  ↓
Rule condition evaluation throws error
  ↓
Core catches error, applies fail-closed:
  outcome = DENIED
```

**HTTP Status**: 200 Success (decision made)

**Response**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-xyz-789",
    "outcome": "DENIED",
    "rule_matched": null,
    "rule_matched_reason": "RULE_EVALUATION_ERROR",
    "error_detail": "Field 'amount' not found in context"
  }
}
```

**Recovery**:
- App provides context with required fields
- App creates NEW decision with corrected context
- Old decision remains DENIED (immutable)

**Idempotency**: Same idempotency_key = same decision_id (with error)

**Event Emission**:
- decision.created (with outcome=DENIED)
- decision.denied (with reason=error)

---

### 2.5 Failure: Network Timeout (T0+10ms → T0+300ms)

**When**: SDK → Core communication fails (network down, Core unreachable, timeout)

**Failure Scenario**:
```
SDK sends HTTP POST to Core
  ↓
No response after 10s timeout
  ↓
SDK times out (default 10s, configurable)
```

**HTTP Status**: 503 Service Unavailable (or timeout)

**Response**:
```json
{
  "status": "error",
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "Core unreachable (timeout after 10s)",
  "retriable": true,
  "retry_after_seconds": 5
}
```

**State at Core**:
- If request reached Core BEFORE timeout: decision may or may not be created
  - Core may have created decision but response was lost
  - **Idempotency key prevents duplicates** (if SDK retries with same key)

- If request never reached Core: no decision created

**Recovery** (Application/SDK responsibility):
```
1. SDK returns error to App
2. App can retry with SAME idempotency_key
3. If decision created: returns same decision_id (idempotent)
4. If decision not created: creates new one
5. Result: exactly-once semantics despite retry
```

**Idempotency**: CRITICAL
- Same idempotency_key + same request = same decision_id
- SDK/App retries safely
- No duplicates

**Event Emission**:
- If decision created: emitted (possibly late, but eventually consistent)
- If decision not created: none

---

### 2.6 Failure: Core Crashes After Decision Persisted (T0+55ms)

**When**: Core crashes after writing decision to DB but before response sent

**Failure Scenario**:
```
Core writes Decision to DB (T0+50ms)
  ↓
Core writes Workflow to DB (T0+55ms)
  ↓
Core crashes before sending HTTP response
  ↓
SDK times out waiting for response
```

**SDK observes**: Timeout (same as 2.5)

**Actual state**: Decision EXISTS in Core DB (persisted, immutable)

**Recovery**:
```
1. SDK timeout, returns error to App
2. App can retry with same idempotency_key
3. Core restarts
4. SDK retries: POST /v1/decisions with idempotency_key
5. Core checks: idempotency_key already processed? YES
6. Core returns cached decision (same decision_id)
7. Result: Decision delivered to App despite crash
```

**Guarantee**: **Idempotency key ensures at-most-once decision creation**

**Event Emission**:
- Decision stored (immutable)
- Events may be queued but not yet delivered (eventual consistency)
- App may need to consume events separately

---

### 2.7 Failure: Duplicate Request (T0 & T0+100ms)

**When**: App sends same request twice (network retry, user double-click, etc.)

**Failure Scenario**:
```
App sends:
  createDecision(
    "accounting.journal_approval",
    { amount: 15000 },
    "hotel-123",
    idempotency_key="req-123"
  )
  ↓ T0: SDK → Core (request 1)
  ↓
  [Network delay, SDK timeout]
  ↓ T0+5s: App retries with SAME idempotency_key
  ↓ T0+5s: SDK → Core (request 2, same key)
```

**Core behavior**:
```
Request 1: Creates decision-xyz
  - Marks idempotency_key="req-123" as processed
  - Stores decision immutably

Request 2 (same key):
  - Core checks: key already processed? YES
  - Return cached decision-xyz
  - Do NOT create new decision
```

**Result**:
- Both requests return SAME decision_id
- Decision created exactly once (idempotent)
- No duplicates

**HTTP Status**: 200 Success (both)

**Response** (both identical):
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-xyz-789",  // SAME in both responses
    "outcome": "ALLOWED"
  }
}
```

**Guarantee**: **Exactly-once semantics** (despite multiple requests)

---

## 3. Workflow Approval Critical Path (Detailed)

### 3.1 Full Sequence with Timing & State

```
╔════════════════════════════════════════════════════════════════╗
║ WORKFLOW APPROVAL CRITICAL PATH                                ║
║ From: Approver / SDK                                           ║
║ To: Core                                                       ║
║ SLA: < 100ms (p95: < 200ms)                                   ║
╚════════════════════════════════════════════════════════════════╝

TIME  STEP  ACTOR       ACTION                           STATE
────  ────  ──────      ────────────────────────────     ─────
T0    1     Approver    Clicks "Approve" button          Approval request
            (UI)        in approval UI

      2     UI/App      Call SDK:                        Request sent
                        approveWorkflow(
                          workflow_id,
                          approver_role="CFO",
                          tenant_id,
                          comment="Approved"
                        )

      3     SDK         Validate request                 Request in-flight
                        - workflow_id valid UUID?
                        - approver_role non-empty?
                        - tenant_id present?
                        - auth_context.tenant_id
                          === request.tenant_id?

T0+2ms 4    SDK        If validation FAILS:             SDK returns 400
                       return ERROR_400                 (no Core call)

      5     SDK        If validation PASSES:            Request approved
                       - Extract auth context
                       - Build Core request

T0+3ms 6    SDK        Call Core (HTTP POST)            Request in-flight
                       POST /v1/workflows/{workflow_id}/approve
                       {
                         approver_role: string,
                         tenant_id: string,
                         comment?: string,
                         approved_by_user_id: string
                       }

T0+10ms 7   Core       Receive request                  Request received

      8     Core       Validate request                 Validating...
                       - tenant_id present?
                       - workflow_id valid UUID?
                       - Fetch workflow from DB
                         (filtered by tenant_id)

T0+12ms 9   Core       If workflow not found:           Core returns 404
                       return ERROR_404                 (NOT approval)

      10    Core       Verify workflow state            Checking state...
                       - workflow.state ===
                         PENDING_APPROVAL?

T0+13ms 11  Core       If NOT PENDING_APPROVAL:         Core returns 409
                       return ERROR_409                 (wrong state)
                       message: "Cannot approve
                               workflow in state
                               ESCALATED"

      12    Core       Verify approver_role             Checking auth...
                       - workflow.approver_role
                         === request.approver_role?

T0+14ms 13  Core       If role mismatch:                Core returns 403
                       return ERROR_403                 (not authorized)
                       message: "Role manager
                               not authorized.
                               Expected: CFO"

      14    Core       All checks passed:               Transitioning...
                       - Transition workflow state:
                         PENDING_APPROVAL → APPROVED
                       - Record approval action
                       - approved_by_user_id from auth
                       - timestamp = now()
                       - comment stored

T0+45ms 15   Core      Persist workflow state           State updated
            (DB)       to database (immutable after)

      16    Core       Emit events (async):             Events queued
                       - workflow.approved
                       - workflow.completed
                       (NO WAIT for events)

      17    Core       Build response                   Response building
                       {
                         status: "success",
                         workflow: {
                           workflow_id,
                           state: "APPROVED",
                           approvals: [...]
                         }
                       }

T0+50ms 18   Core      Return response (HTTP 200)       Response in-flight

T0+60ms 19   SDK       Receive response                 Response received
                       Parse and return to Approver

      20    UI/App     Handle approval                  Approval confirmed
                       Show "Approved" message
                       Trigger event consumption

T0+65ms ✓    COMPLETE  Workflow approved                STATE IMMUTABLE
                       state = APPROVED (locked)        (decision still
                       (decision.outcome unchanged)     REQUIRE_APPROVAL)

────────────────────────────────────────────────────────────────
TOTAL TIME: ~65ms (best case: ~45ms, p95: ~100-150ms)
STATE PERSISTED: Workflow state transition + approval record
IDEMPOTENCY: Approving same workflow twice = idempotent
EVENTS: Emitted async (no waiting)
────────────────────────────────────────────────────────────────
```

---

## 4. Failure Modes: Workflow Approval

### 4.1 Failure: Workflow Not Found (T0+12ms)

**When**: Workflow ID doesn't exist in tenant

**Scenario**:
```
SDK sends: approveWorkflow("wf-invalid-123", "CFO", "hotel-123")

Core fetches workflow:
  WHERE workflow_id = "wf-invalid-123"
  AND tenant_id = "hotel-123"
  Result: NOT FOUND
```

**HTTP Status**: 404 Not Found

**Response**:
```json
{
  "status": "error",
  "error_code": "NOT_FOUND",
  "message": "Workflow not found or tenant mismatch"
}
```

**Recovery**:
- Verify workflow_id is correct
- Verify workflow belongs to tenant
- Check if workflow was deleted/archived

**State**: Unchanged (no approval recorded)

---

### 4.2 Failure: Wrong Workflow State (T0+13ms)

**When**: Workflow is NOT in PENDING_APPROVAL state

**Scenario**:
```
Workflow.state = "ESCALATED"  (already escalated)

SDK tries to approve:
  approveWorkflow("wf-xyz", "CFO", ...)

Core validates:
  workflow.state === PENDING_APPROVAL? NO

Core returns ERROR_409
```

**HTTP Status**: 409 Conflict

**Response**:
```json
{
  "status": "error",
  "error_code": "INVALID_STATE",
  "message": "Cannot approve workflow in state ESCALATED",
  "details": {
    "current_state": "ESCALATED",
    "allowed_states": ["PENDING_APPROVAL", "DELEGATED_TO_*"]
  }
}
```

**Recovery**:
- Check current workflow state
- If delegated, approver must ask delegate to handle
- If escalated, use escalated role to approve

**State**: Unchanged (no approval recorded)

---

### 4.3 Failure: Role Not Authorized (T0+14ms)

**When**: Approver role doesn't match workflow assignment

**Scenario**:
```
Workflow.approver_role = "CFO"

SDK sends: approveWorkflow("wf-xyz", "manager", ...)

Core validates:
  "manager" === "CFO"? NO
```

**HTTP Status**: 403 Forbidden

**Response**:
```json
{
  "status": "error",
  "error_code": "UNAUTHORIZED_ROLE",
  "message": "Role manager is not authorized",
  "details": {
    "requested_role": "manager",
    "assigned_role": "CFO"
  }
}
```

**Recovery**:
- User with CFO role must approve
- Or, workflow must be delegated to manager first

**State**: Unchanged (no approval recorded)

---

### 4.4 Failure: Idempotent Approval (Retry)

**When**: Same approval request sent twice

**Scenario**:
```
T0: approveWorkflow("wf-xyz", "CFO", ..., idempotency_key="app-123")
    → Core creates approval record
    → Response sent (but network delayed)

T0+10s: App times out, retries same request
    → Core receives same idempotency_key

Core behavior:
    → Checks: key already approved? YES
    → Returns same result (idempotent)
    → Does NOT create duplicate approval
```

**HTTP Status**: 200 Success (both)

**Response** (both identical):
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-xyz",
    "state": "APPROVED",
    "approvals": [...]
  }
}
```

**Guarantee**: **Exactly-once approval semantics**

---

### 4.5 Failure: Network Timeout (T0+10ms → T0+60ms+)

**When**: SDK → Core communication fails

**State at Core**:
- If approval persisted: state = APPROVED (immutable)
- If approval not persisted: state = PENDING_APPROVAL (unchanged)

**SDK observes**: Timeout

**Recovery**:
```
1. SDK returns error to App
2. App retries with SAME idempotency_key
3. Core: already approved? YES → return cached result
4. Core: not approved? NO → approve now
5. Result: Approval succeeds despite network issues
```

**Guarantee**: **Idempotency key prevents double-approval**

---

## 5. State Consistency & Guarantees

### 5.1 Decision Immutability Timeline

```
T0: Decision created
    - decision_id generated
    - outcome determined (ALLOWED | DENIED | REQUIRE_APPROVAL)
    - Stored in DB (immutable)

T0+ε: Decision LOCKED forever
    - outcome NEVER changes
    - Even if rules updated later
    - Even if retry attempted
    - Even if cascade requested

T0+∞: Decision query returns same outcome
    - Always ALLOWED (if created ALLOWED)
    - Always DENIED (if created DENIED)
    - Always REQUIRE_APPROVAL (if created that)
```

### 5.2 Workflow State Mutability & Decision Immutability

```
T0: Decision created
    decision.outcome = REQUIRE_APPROVAL (IMMUTABLE)
    workflow.state = PENDING_APPROVAL (MUTABLE)

T0+1h: Approver approves
    decision.outcome = REQUIRE_APPROVAL (UNCHANGED)
    workflow.state = APPROVED (changed, immutable after)

T0+2h: Query decision
    Result: outcome = REQUIRE_APPROVAL
            (not changed by approval)

Key principle:
    Workflow state changes
    Decision outcome stays same (immutable)
```

### 5.3 Tenant Isolation: State Consistency

```
Tenant A creates decision-X
    → stored with tenant_id = "tenant-a"
    → immutable

Tenant B tries to access decision-X
    Core checks: decision.tenant_id === request.tenant_id?
    "tenant-a" === "tenant-b"? NO
    → returns 404 (not found)

Result: Decision completely isolated by tenant
        No accidental cross-tenant leaks
```

---

## 6. Idempotency Guarantees

### 6.1 Idempotency Key Semantics

```
DECISION CREATION:

Request A: createDecision(..., idempotency_key="key-123")
    → Creates decision-abc-456
    → Stores mapping: key-123 → decision-abc-456

Request B: createDecision(..., idempotency_key="key-123")
    → Same context? YES
    → Returns cached decision-abc-456
    → DOES NOT create new decision

Request C: createDecision(..., idempotency_key="key-123", context={DIFFERENT})
    → Same key, different context?
    → ERROR 409 (Idempotency violation)
    → Prevents accidental different decisions with same key
```

### 6.2 Workflow Approval Idempotency

```
Request A: approveWorkflow("wf-xyz", "CFO", ...)
    → Transitions state: PENDING → APPROVED
    → Records approval
    → Returns workflow (state=APPROVED)

Request B: approveWorkflow("wf-xyz", "CFO", ...)
    → Same parameters, same approver role
    → Workflow already APPROVED
    → Returns same workflow (state=APPROVED)
    → DOES NOT create duplicate approval
    → Idempotent (safe to retry)
```

---

## 7. Event Emission Timing

### 7.1 Event Emission is NOT Blocking

```
DECISION CREATION:

Core writes decision to DB (T0+50ms)
    ↓
Core writes workflow to DB (T0+55ms)
    ↓
Core queues events (T0+56ms):
    - decision.created
    - decision.{outcome_type}
    - workflow.created
    ↓
Core returns response immediately (T0+60ms)
    (NO waiting for events to be consumed)
    ↓
Events delivered asynchronously to subscribers
    (App receives event notification after response)

Guarantee:
    - Decision created synchronously (blocking)
    - Events emitted asynchronously (non-blocking)
    - App gets decision outcome before event consumption
```

### 7.2 Event Delivery Guarantees

```
Event Emission: AT-LEAST-ONCE

- Event emitted to Infra event bus
- Event bus delivers to subscribers (retries)
- Subscribers may receive duplicate
- Subscribers MUST be idempotent (dedup by event_id)

NO GUARANTEE:
- Event delivery before decision response
- Ordering across events (only within single aggregate)
- Subscriber delivery (consumer responsible for retries)
```

---

## 8. Timeouts & Circuit Breakers

### 8.1 SDK Request Timeout

```
SDK sends request to Core:
    POST /v1/decisions

If no response after 10s (default):
    → SDK times out
    → Returns ERROR_SERVICE_UNAVAILABLE
    → Marked retriable=true
    → App can retry with idempotency_key

Timeout is CONSERVATIVE:
    - Allows Core to process (may succeed despite timeout)
    - Idempotency key prevents duplicates on retry
    - Application can safely retry
```

### 8.2 Core Processing Timeout

```
Core evaluates rules:
    - Per rule: max 100ms timeout
    - Total decision creation: max 1s hard timeout

If rule evaluation exceeds timeout:
    → Core aborts
    → Returns outcome = DENIED (fail-closed)
    → Logged as SECURITY_EVENT
    → Decision immutable (DENIED persisted)

If total time exceeds 1s:
    → Core aborts
    → Returns outcome = DENIED (fail-closed)
```

---

## 9. Summary: Critical Path Guarantees

| Guarantee | Mechanism | Enforcement |
|-----------|-----------|------------|
| **Immutability** | Append-only DB writes | Once persisted, no updates |
| **Atomicity** | Single DB transaction | Decision + Workflow or nothing |
| **Idempotency** | Idempotency key caching | Same request = same outcome |
| **Tenant Isolation** | Tenant filter on all queries | 404 on mismatch (no leaks) |
| **Ordering** | Timestamps immutable | Events ordered by occurred_at |
| **Fail-Closed** | Default outcome=DENIED | No rule match = DENIED |
| **Non-Blocking Events** | Async emission | Decision response before events |
| **At-Least-Once Events** | Event bus delivery | Consumer deduplicates |
| **SLA Compliance** | Timeout limits | < 100ms target, < 200ms p95 |

**Status**: Critical Path Sequences complete, ready for review.

**Next**: Await feedback before locking.
