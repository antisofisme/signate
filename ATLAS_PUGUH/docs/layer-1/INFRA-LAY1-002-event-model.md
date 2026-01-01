# INFRA-LAY1-002: Event Model & Contracts

**VERSION**: Layer 1 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-27

---

## Overview

Infra emits **immutable events** representing decision and workflow state transitions.

**Events are FACTS, not commands**:
- Events record what happened (immutable snapshots)
- Events do NOT trigger actions in Infra
- Events do NOT orchestrate workflows
- Events do NOT execute business logic
- Application consumers decide what to do with events

---

## 1. Event Model Fundamentals

### 1.1 Event Definition

**Event** = immutable fact derived from Decision or Workflow state transition.

```typescript
Event {
  event_id: string                          // UUID (unique per event)
  event_type: string                        // "decision.created", "workflow.approved"
  tenant_id: string                         // Hard isolation (mandatory)

  aggregate_id: string                      // decision_id or workflow_id
  aggregate_type: "decision" | "workflow"   // What changed

  occurred_at: timestamp                    // When change happened
  recorded_at: timestamp                    // When Infra recorded event

  payload: object                           // Event-specific data (immutable snapshot)
  metadata: {
    source: string                          // "sdk", "cms", "core"
    caused_by_user_id?: string              // Who triggered change (if applicable)
    idempotency_key?: string                // For deduplication
    trace_id?: string                       // For distributed tracing
  }

  schema_version: string                    // Event schema version (for evolution)
}
```

### 1.2 Core Event Guarantees

| Guarantee | Meaning | Enforcement |
|-----------|---------|-------------|
| **Immutable** | Event content never changes after emission | Stored in append-only log |
| **Audit Trail** | Full context captured for replay/debugging | payload + metadata complete |
| **Tenant Isolated** | Events partitioned by tenant_id | Query by tenant_id always |
| **Ordered** | Events ordered by occurred_at within tenant | Timestamp immutable |
| **At-Least-Once** | Event delivered ≥ 1 time (idempotent consumption) | Consumer deduplicates by event_id |
| **Schema Versioned** | Event schema can evolve safely | schema_version in event |

### 1.3 Event Scope (What IS Emitted)

```
✅ EMITTED (state transitions):
- Decision created (outcome determined)
- Workflow created (approval initiated)
- Workflow state changed (approved, rejected, escalated, delegated)
- Approval action recorded (approval/rejection with details)

✅ EMITTED (configuration changes):
- Rule activated (new rule version live)
- Rule deactivated (rule disabled)

❌ NOT EMITTED (internal operations):
- Rule evaluation steps
- Context validation steps
- Extension hook invocations
- Tenant context checks
```

---

## 2. Decision Events

### 2.1 Event: decision.created

**Triggers**: Decision made (outcome determined by Core)

**Semantics**:
- Emitted exactly once per decision
- Immutable - decision_outcome never changes after this
- Outcome determined at this moment

**Payload**:
```json
{
  "event_id": "evt-abc-123",
  "event_type": "decision.created",
  "tenant_id": "hotel-123",
  "aggregate_id": "dec-xyz-789",
  "aggregate_type": "decision",
  "occurred_at": "2025-12-27T10:30:01Z",
  "recorded_at": "2025-12-27T10:30:01.050Z",

  "payload": {
    "decision_id": "dec-xyz-789",
    "decision_type": "accounting.journal_approval",
    "requester_user_id": "user-456",
    "outcome": "REQUIRE_APPROVAL",
    "rule_matched": "correction_amount_15000_cfo",
    "rule_version": "1.2",
    "approval_workflow_id": "wf-pqr-456",
    "context_summary": {
      "journal_entry_amount": 15000,
      "journal_entry_type": "correction",
      "requester_role": "staff"
    }
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-456",
    "trace_id": "trace-abc-123"
  },

  "schema_version": "1.0"
}
```

**Payload Fields**:
- `decision_id`: UUID (from decision.decision_id)
- `decision_type`: Format {module}.{entity}.{action}
- `requester_user_id`: Audit metadata (who requested decision)
- `outcome`: One of 3 values (ALLOWED | DENIED | REQUIRE_APPROVAL)
- `rule_matched`: Name of first matching rule (single rule)
- `rule_version`: Version of matched rule
- `approval_workflow_id`: Only if outcome = REQUIRE_APPROVAL
- `context_summary`: Sanitized context snapshot (no PII)

**Consumption Pattern**:
```typescript
// Application listens to decision.created
on("decision.created", (event) => {
  const decision = event.payload;

  if (decision.outcome === "ALLOWED") {
    // Proceed with operation
  } else if (decision.outcome === "DENIED") {
    // Reject request, show error to user
  } else if (decision.outcome === "REQUIRE_APPROVAL") {
    // Create approval UI, show workflow_id to user
  }
});
```

**Guard Rails**:
```typescript
// GR-1: Emitted exactly once per decision
// Cannot re-emit decision.created for same decision_id

// GR-2: Immutable after emission
// Event content never changes

// GR-3: Outcome in event matches Decision.outcome
// event.payload.outcome === decision.outcome (always)

// GR-4: Context is sanitized (no PII)
// Only audit-safe fields in context_summary
```

---

### 2.2 Event: decision.allowed

**Triggers**: Decision outcome = ALLOWED

**Semantics**:
- Specialized event for ALLOWED outcome
- Convenience for applications interested in approvals not needed
- Payload is subset of decision.created

**Payload**:
```json
{
  "event_id": "evt-def-456",
  "event_type": "decision.allowed",
  "tenant_id": "hotel-123",
  "aggregate_id": "dec-abc-111",
  "aggregate_type": "decision",
  "occurred_at": "2025-12-27T10:30:01Z",
  "recorded_at": "2025-12-27T10:30:01.050Z",

  "payload": {
    "decision_id": "dec-abc-111",
    "decision_type": "inventory.stock_movement_allowed",
    "requester_user_id": "user-789",
    "outcome": "ALLOWED",
    "rule_matched": "inbound_movement_allowed",
    "rule_version": "1.0"
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-789",
    "trace_id": "trace-def-456"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application listens only to decisions that don't need approval
on("decision.allowed", (event) => {
  // No workflow needed, proceed directly
  executeOperation(event.payload.decision_id);
});
```

---

### 2.3 Event: decision.denied

**Triggers**: Decision outcome = DENIED

**Semantics**:
- Specialized event for DENIED outcome
- Includes failure reason (no rule matched, configuration error, etc.)

**Payload**:
```json
{
  "event_id": "evt-ghi-789",
  "event_type": "decision.denied",
  "tenant_id": "hotel-123",
  "aggregate_id": "dec-xyz-222",
  "aggregate_type": "decision",
  "occurred_at": "2025-12-27T10:30:02Z",
  "recorded_at": "2025-12-27T10:30:02.050Z",

  "payload": {
    "decision_id": "dec-xyz-222",
    "decision_type": "accounting.period_posting_allowed",
    "requester_user_id": "user-999",
    "outcome": "DENIED",
    "rule_matched": "period_closed_forbidden",
    "rule_version": "2.0",
    "denial_reason": "Period status is CLOSED"
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-999",
    "trace_id": "trace-ghi-789"
  },

  "schema_version": "1.0"
}
```

**Payload Fields**:
- `denial_reason`: Human-readable reason (for audit trail)

**Consumption Pattern**:
```typescript
// Application listens to denied decisions (for alerting/monitoring)
on("decision.denied", (event) => {
  logger.warn("Decision denied", {
    decision_type: event.payload.decision_type,
    reason: event.payload.denial_reason,
    requester: event.payload.requester_user_id
  });

  // Possibly alert on high frequency of denials
});
```

---

### 2.4 Event: decision.requires_approval

**Triggers**: Decision outcome = REQUIRE_APPROVAL (workflow initiated)

**Semantics**:
- Specialized event for approval-required decisions
- Includes workflow_id and approver role

**Payload**:
```json
{
  "event_id": "evt-jkl-012",
  "event_type": "decision.requires_approval",
  "tenant_id": "hotel-123",
  "aggregate_id": "dec-pqr-333",
  "aggregate_type": "decision",
  "occurred_at": "2025-12-27T10:30:03Z",
  "recorded_at": "2025-12-27T10:30:03.050Z",

  "payload": {
    "decision_id": "dec-pqr-333",
    "decision_type": "accounting.journal_approval",
    "requester_user_id": "user-456",
    "outcome": "REQUIRE_APPROVAL",
    "rule_matched": "correction_amount_15000_cfo",
    "rule_version": "1.2",
    "approval_workflow_id": "wf-stu-444",
    "approver_role": "CFO",
    "escalation_timeout_hours": 24
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-456",
    "trace_id": "trace-jkl-012"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application listens to approval-required decisions
on("decision.requires_approval", (event) => {
  const workflow = event.payload;

  // Create approval task UI
  createApprovalTask({
    workflow_id: workflow.approval_workflow_id,
    approver_role: workflow.approver_role,
    decision_type: workflow.decision_type,
    escalation_in_hours: workflow.escalation_timeout_hours
  });
});
```

---

## 3. Workflow Events

### 3.1 Event: workflow.created

**Triggers**: Workflow initiated (decision outcome = REQUIRE_APPROVAL)

**Semantics**:
- Emitted when approval workflow starts
- Initial state = PENDING_APPROVAL
- Immutable - workflow_created never changes

**Payload**:
```json
{
  "event_id": "evt-mno-345",
  "event_type": "workflow.created",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T10:30:03Z",
  "recorded_at": "2025-12-27T10:30:03.100Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "decision_type": "accounting.journal_approval",
    "initial_state": "PENDING_APPROVAL",
    "approver_role": "CFO",
    "escalation_target_role": "chief_finance_officer",
    "escalation_timeout_at": "2025-12-28T10:30:03Z"
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-456",
    "trace_id": "trace-mno-345"
  },

  "schema_version": "1.0"
}
```

---

### 3.2 Event: workflow.pending_approval

**Triggers**: Workflow enters PENDING_APPROVAL state

**Semantics**:
- Emitted when workflow is ready for approval
- Approver role is identified
- Application should notify approver(s)

**Payload**:
```json
{
  "event_id": "evt-pqr-678",
  "event_type": "workflow.pending_approval",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T10:30:03Z",
  "recorded_at": "2025-12-27T10:30:03.100Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "approver_role": "CFO",
    "decision_summary": {
      "decision_type": "accounting.journal_approval",
      "amount": 15000,
      "type": "correction"
    }
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-456",
    "trace_id": "trace-pqr-678"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application notifies approver(s)
on("workflow.pending_approval", (event) => {
  const { approver_role, decision_summary } = event.payload;

  // Resolve approver_role to actual users (application adapter)
  const approvers = await resolveApproverUsers(approver_role, event.tenant_id);

  // Send notification
  for (const approver of approvers) {
    await sendNotification(approver.email, {
      subject: `Approval Required: ${decision_summary.decision_type}`,
      workflow_id: event.payload.workflow_id,
      decision: decision_summary
    });
  }
});
```

---

### 3.3 Event: workflow.approved

**Triggers**: Workflow transitions to APPROVED state

**Semantics**:
- Approver approved the request
- Immutable - approval action recorded
- Decision outcome still REQUIRE_APPROVAL (unchanged)

**Payload**:
```json
{
  "event_id": "evt-stu-901",
  "event_type": "workflow.approved",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T14:45:00Z",
  "recorded_at": "2025-12-27T14:45:00.150Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "approver_role": "CFO",
    "approved_by_user_id": "user-cfo-001",
    "approval_timestamp": "2025-12-27T14:45:00Z",
    "comment": "Approved per policy"
  },

  "metadata": {
    "source": "sdk",
    "caused_by_user_id": "user-cfo-001",
    "trace_id": "trace-stu-901"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application proceeds with operation (approval granted)
on("workflow.approved", (event) => {
  const { decision_id } = event.payload;

  // Fetch original decision
  const decision = await getDecision(decision_id);

  // Proceed with operation
  await executeApprovedOperation(decision);
});
```

---

### 3.4 Event: workflow.rejected

**Triggers**: Workflow transitions to REJECTED state

**Semantics**:
- Approver rejected the request
- Application decides whether to retry, modify context, or fail
- Decision outcome still REQUIRE_APPROVAL (unchanged)

**Payload**:
```json
{
  "event_id": "evt-vwx-234",
  "event_type": "workflow.rejected",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T15:00:00Z",
  "recorded_at": "2025-12-27T15:00:00.200Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "approver_role": "CFO",
    "rejected_by_user_id": "user-cfo-001",
    "rejection_timestamp": "2025-12-27T15:00:00Z",
    "reason": "Amount exceeds policy limit for this month"
  },

  "metadata": {
    "source": "sdk",
    "caused_by_user_id": "user-cfo-001",
    "trace_id": "trace-vwx-234"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application notifies requester of rejection
on("workflow.rejected", (event) => {
  const { decision_id, reason } = event.payload;

  // Notify original requester
  await notifyRejection({
    requester_id: event.metadata.caused_by_user_id,
    reason: reason,
    decision_id: decision_id
  });
});
```

---

### 3.5 Event: workflow.delegated

**Triggers**: Workflow transitions to DELEGATED_TO_* state

**Semantics**:
- Current approver delegated to different user (same role)
- Delegated user can now approve/reject/escalate
- Workflow returns to PENDING_APPROVAL semantically (awaiting different user)

**Payload**:
```json
{
  "event_id": "evt-yza-567",
  "event_type": "workflow.delegated",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T11:00:00Z",
  "recorded_at": "2025-12-27T11:00:00.250Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "approver_role": "CFO",
    "delegated_by_user_id": "user-cfo-001",
    "delegated_to_user_id": "user-cfo-backup",
    "delegation_timestamp": "2025-12-27T11:00:00Z",
    "reason": "CFO on leave"
  },

  "metadata": {
    "source": "sdk",
    "caused_by_user_id": "user-cfo-001",
    "trace_id": "trace-yza-567"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application notifies delegated user
on("workflow.delegated", (event) => {
  const { delegated_to_user_id, reason } = event.payload;

  // Notify new approver
  await sendNotification(delegated_to_user_id, {
    message: `Workflow delegated to you: ${reason}`,
    workflow_id: event.payload.workflow_id
  });
});
```

---

### 3.6 Event: workflow.escalated

**Triggers**: Workflow transitions to ESCALATED state

**Semantics**:
- Approval timeout or manual escalation
- New approver role takes over (escalation_target_role)
- Application may send urgent notification

**Payload**:
```json
{
  "event_id": "evt-bcd-890",
  "event_type": "workflow.escalated",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-28T10:30:03Z",
  "recorded_at": "2025-12-28T10:30:03.300Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "previous_approver_role": "CFO",
    "escalation_target_role": "chief_finance_officer",
    "escalation_reason": "Approval timeout (24 hours)",
    "escalated_at": "2025-12-28T10:30:03Z"
  },

  "metadata": {
    "source": "core",
    "trace_id": "trace-bcd-890"
  },

  "schema_version": "1.0"
}
```

**Consumption Pattern**:
```typescript
// Application escalates urgency
on("workflow.escalated", (event) => {
  const { escalation_target_role, escalation_reason } = event.payload;

  // Send urgent notification to escalation target role
  const approvers = await resolveApproverUsers(
    escalation_target_role,
    event.tenant_id
  );

  for (const approver of approvers) {
    await sendUrgentNotification(approver.email, {
      subject: "URGENT: Approval Required - Escalated",
      reason: escalation_reason,
      workflow_id: event.payload.workflow_id
    });
  }
});
```

---

### 3.7 Event: workflow.completed

**Triggers**: Workflow reaches terminal state (APPROVED, REJECTED)

**Semantics**:
- Workflow lifecycle complete
- Final state and outcome recorded
- Idempotent - emitted once per workflow completion

**Payload**:
```json
{
  "event_id": "evt-efg-123",
  "event_type": "workflow.completed",
  "tenant_id": "hotel-123",
  "aggregate_id": "wf-stu-444",
  "aggregate_type": "workflow",
  "occurred_at": "2025-12-27T14:45:00Z",
  "recorded_at": "2025-12-27T14:45:00.400Z",

  "payload": {
    "workflow_id": "wf-stu-444",
    "decision_id": "dec-pqr-333",
    "final_state": "APPROVED",
    "final_approver_role": "CFO",
    "final_approver_user_id": "user-cfo-001",
    "completion_timestamp": "2025-12-27T14:45:00Z",
    "total_duration_seconds": 16697,
    "state_transitions": [
      {
        "from": "PENDING_APPROVAL",
        "to": "APPROVED",
        "timestamp": "2025-12-27T14:45:00Z"
      }
    ]
  },

  "metadata": {
    "source": "core",
    "caused_by_user_id": "user-cfo-001",
    "trace_id": "trace-efg-123"
  },

  "schema_version": "1.0"
}
```

---

## 4. Configuration Events

### 4.1 Event: rule.activated

**Triggers**: Rule version activated (becomes live for decisions)

**Semantics**:
- New rule version is now used for evaluations
- Existing decisions unaffected (use rule version from their time)
- CMS operation, recorded for audit

**Payload**:
```json
{
  "event_id": "evt-hij-456",
  "event_type": "rule.activated",
  "tenant_id": "hotel-123",
  "aggregate_id": "correction_amount_15000_cfo",
  "aggregate_type": "rule",
  "occurred_at": "2025-12-27T09:00:00Z",
  "recorded_at": "2025-12-27T09:00:00.500Z",

  "payload": {
    "rule_id": "correction_amount_15000_cfo",
    "rule_name": "correction_amount_15000_cfo",
    "decision_type": "accounting.journal_approval",
    "version": "1.3",
    "previous_version": "1.2",
    "status": "ACTIVE",
    "activated_by_user_id": "user-admin-001",
    "change_summary": "Updated escalation target from CFO to chief_finance_officer"
  },

  "metadata": {
    "source": "cms",
    "caused_by_user_id": "user-admin-001",
    "trace_id": "trace-hij-456"
  },

  "schema_version": "1.0"
}
```

---

### 4.2 Event: rule.deactivated

**Triggers**: Rule version deactivated (no longer used for new decisions)

**Semantics**:
- Rule no longer used for new evaluations
- Existing decisions with this rule remain unchanged
- Audit trail of configuration changes

**Payload**:
```json
{
  "event_id": "evt-klm-789",
  "event_type": "rule.deactivated",
  "tenant_id": "hotel-123",
  "aggregate_id": "correction_amount_15000_cfo",
  "aggregate_type": "rule",
  "occurred_at": "2025-12-27T10:00:00Z",
  "recorded_at": "2025-12-27T10:00:00.550Z",

  "payload": {
    "rule_id": "correction_amount_15000_cfo",
    "rule_name": "correction_amount_15000_cfo",
    "decision_type": "accounting.journal_approval",
    "version": "1.2",
    "status": "DEPRECATED",
    "deactivated_by_user_id": "user-admin-001",
    "deactivated_at": "2025-12-27T10:00:00Z",
    "reason": "Superseded by v1.3"
  },

  "metadata": {
    "source": "cms",
    "caused_by_user_id": "user-admin-001",
    "trace_id": "trace-klm-789"
  },

  "schema_version": "1.0"
}
```

---

## 5. Event Guarantees & Contracts

### 5.1 Immutability Guarantee

```
ONCE emitted, event content NEVER changes:
  - event_id is unique forever
  - event_type never changes
  - payload never changes
  - metadata never changes

Events are stored in append-only log.
No updates, no deletes, no corrections to events.
```

### 5.2 Tenant Isolation Guarantee

```
EVERY event MUST have tenant_id:
  - Events partitioned by tenant_id
  - Applications cannot query other tenants' events
  - Event queries require tenant_id filter

EventQuery {
  tenant_id: string  // REQUIRED, not optional
  filters?: {
    event_type?: string,
    aggregate_id?: string,
    occurred_after?: timestamp,
    occurred_before?: timestamp
  }
}
```

### 5.3 Ordering Guarantee

```
Within a single tenant:
  Events ordered by occurred_at (immutable timestamp)

  Time T1: decision.created → event-1
  Time T2: workflow.created → event-2
  Time T3: workflow.approved → event-3

  Query order is always T1, T2, T3 (never reordered)
```

### 5.4 At-Least-Once Delivery

```
Event emitted ≥ 1 time:
  - Network retry may cause duplicates
  - Consumer MUST be idempotent (dedup by event_id)

Consumer Idempotency:
  processed_events = Set()

  on(event):
    IF event.event_id in processed_events:
      return  // Already processed, skip
    ELSE:
      process(event)
      processed_events.add(event.event_id)
```

### 5.5 Schema Evolution

```
Events include schema_version:
  schema_version: "1.0"  // Allows safe evolution

Future versions:
  schema_version: "1.1"  // Additive fields only
  schema_version: "2.0"  // Major breaking change

Consumers MUST handle schema versions:
  if (event.schema_version === "1.0") {
    // Handle v1 payload
  } else if (event.schema_version === "1.1") {
    // Handle v1.1 payload (superset of v1)
  }
```

---

## 6. Event Publishing

### 6.1 Publishing Flow

```
1. State Transition in Core
   decision.outcome = ALLOWED
   workflow.state = APPROVED

2. Event Immutably Recorded
   event_id = uuid()
   event created with immutable payload
   stored in Event Log (append-only)

3. Event Emitted to Subscribers
   Infra publishes to event bus
   All subscribed applications notified

4. Delivery Semantics
   At-least-once delivery
   Subscribers handle idempotency
   No guaranteed order across events
   (order guaranteed within single aggregate)
```

### 6.2 Event Publishing SLA

| Event Type | Latency Target | P95 |
|-----------|-----------------|-----|
| Decision events (created, allowed, denied, requires_approval) | < 100ms | < 200ms |
| Workflow state events (approved, rejected, delegated, escalated) | < 100ms | < 200ms |
| Configuration events (rule activation) | < 500ms | < 1000ms |

**Best effort, not guaranteed hard real-time.**

---

## 7. Event Consumption

### 7.1 Event Subscription Pattern

```typescript
// Application subscribes to events
const infraEvents = new InfraEventSubscriber({
  infra_url: "https://events.infra.internal",
  tenant_id: "hotel-123",

  handlers: {
    "decision.created": async (event) => {
      // Handle decision creation
    },
    "decision.allowed": async (event) => {
      // Handle allowed decision
    },
    "workflow.approved": async (event) => {
      // Handle approval
    }
  }
});

// Subscriber ensures idempotency
infraEvents.on("*", async (event) => {
  // Deduplication by event_id
  const processed = await db.getProcessedEvent(event.event_id);
  if (processed) {
    return;  // Skip duplicate
  }

  // Process event
  await handleEvent(event);

  // Mark as processed
  await db.markEventProcessed(event.event_id);
});
```

### 7.2 Event Query Pattern

```typescript
// Application queries event history
const events = await infraEvents.query({
  tenant_id: "hotel-123",
  filters: {
    event_type: "decision.created",
    aggregate_id: "dec-xyz-789",
    occurred_after: "2025-12-20T00:00:00Z"
  }
});

// Returns: Event[]
// Ordered by occurred_at
```

---

## 8. What Events Are NOT

### ❌ Events Are NOT Commands

```
WRONG: Event causes action in Infra
"decision.created" → Core executes business logic

CORRECT: Event records fact, application consumes
"decision.created" → Application receives event
                  → Application decides action
```

### ❌ Events Are NOT Orchestration

```
WRONG: Events chain together workflows
decision.created → triggers workflow
workflow.approved → triggers next workflow

CORRECT: Events are facts, no chaining
workflow.approved → application consumes
                 → application decides next step
                 → application creates next decision
```

### ❌ Events Are NOT Execution Triggers

```
WRONG: workflow.approved → Infra executes business operation

CORRECT: workflow.approved → Application receives event
                          → Application executes operation
                          → Infra never executes
```

### ❌ Events Do NOT Contain PII

```
ALLOWED in event payload:
- IDs (decision_id, workflow_id, user_id for audit)
- Enum values (role, status, outcome)
- Amounts, counts, thresholds
- Timestamps

PROHIBITED in event payload:
- Names, emails, phone numbers
- Full payloads (account details, transaction data)
- Sensitive strings (API keys, credentials)
```

---

## 9. Event Retention & Archival

### 9.1 Retention Policy

```
Hot Storage (recent events):
  - Last 90 days: Full fidelity, queryable, indexed
  - SLA: < 500ms query response

Warm Storage (archive):
  - 90 days - 7 years: Compressed, slower queries
  - SLA: < 5s query response (batch job)

Deletion:
  - After 7 years: Events deleted per regulation
  - Immutable before deletion (no modifications)
```

### 9.2 Event Archival API

```typescript
// Application archives old events
const archived = await infraEvents.archiveOldEvents({
  tenant_id: "hotel-123",
  older_than: "2025-06-27T00:00:00Z",  // 6 months old
  destination: "s3://tenant-backups/events/"
});

// Returns count of archived events
// Original events remain in cold storage (queryable but slower)
```

---

## 10. Event Examples: End-to-End Flow

### Example: Journal Entry Approval

```
Time T1: Application calls SDK
  → createDecision(
      "accounting.journal_approval",
      { amount: 15000, type: "correction" },
      "hotel-123"
    )

Time T2: Core evaluates rules
  → Rule match: "correction_amount_15000_cfo"
  → Outcome: REQUIRE_APPROVAL
  → Workflow created (wf-123)

Time T3: Infra emits decision.created
  {
    event_type: "decision.created",
    decision_id: "dec-123",
    outcome: "REQUIRE_APPROVAL",
    approval_workflow_id: "wf-123"
  }

Time T4: Infra emits decision.requires_approval
  {
    event_type: "decision.requires_approval",
    approver_role: "CFO"
  }

Time T5: Infra emits workflow.created
  {
    event_type: "workflow.created",
    workflow_id: "wf-123",
    initial_state: "PENDING_APPROVAL"
  }

Time T6: Infra emits workflow.pending_approval
  {
    event_type: "workflow.pending_approval",
    approver_role: "CFO"
  }

  [Application notifies CFO]

Time T7: CFO approves (via SDK)
  → approveWorkflow("wf-123", "CFO", "hotel-123")

Time T8: Infra emits workflow.approved
  {
    event_type: "workflow.approved",
    final_approver_user_id: "user-cfo-001"
  }

Time T9: Infra emits workflow.completed
  {
    event_type: "workflow.completed",
    final_state: "APPROVED"
  }

  [Application proceeds with operation]
```

---

## 11. Event Guard Rails (Explicit, Testable)

### GR-1: Immutable Events

```
IF attempt to modify event after emission
THEN REJECT (events are immutable, append-only log)
```

### GR-2: Tenant Isolation

```
IF event query missing tenant_id
THEN REJECT (tenant_id mandatory)

IF event.tenant_id ≠ query.tenant_id
THEN REJECT (404, tenant mismatch)
```

### GR-3: Single Emission Per State

```
IF decision already created
THEN do NOT re-emit decision.created

IF workflow already approved
THEN do NOT re-emit workflow.approved
```

### GR-4: No PII in Payload

```
IF event.payload contains [email, phone, ssn, password]
THEN REJECT event before emission
```

### GR-5: Schema Versioning

```
IF event.schema_version NOT in [supported_versions]
THEN consumer MUST handle gracefully
     (ignore unknown versions, log warning)
```

### GR-6: At-Least-Once Delivery

```
Consumer MUST:
  - Deduplicate by event_id
  - Process idempotently
  - Handle duplicate events without error
```

### GR-7: Ordering Within Aggregate

```
Events for same aggregate ordered by occurred_at:
  decision-123:
    event-1 (T1): decision.created
    event-2 (T2): decision.allowed

  NEVER:
    event-2 (T2): decision.allowed
    event-1 (T1): decision.created
```

### GR-8: No Cascading Events

```
Event emission does NOT trigger other events in Infra:
  decision.created emitted
    ↓
  [Application consumes, decides action]
    ↓
  [Application creates new decision if needed]
    ↓
  New decision.created emitted

NOT:
  decision.created emitted
    ↓
  [Core auto-triggers next workflow]
    ↓
  [Cascading event emissions]
```

---

## Summary: Event Model is Layer 0-Locked

✅ Events are immutable facts (append-only log)
✅ Events derived from Decision & Workflow state transitions
✅ Events do NOT trigger actions (application consumes)
✅ Events do NOT orchestrate (no cascading)
✅ Events do NOT execute logic
✅ Events are tenant-isolated (hard boundary)
✅ Events support at-least-once delivery (idempotent consumption)
✅ Events include full audit trail (for replay)
✅ 8 explicit guard rails (immutability, isolation, ordering, etc.)

**Status**: Ready for review
**Next**: Await user feedback before locking
