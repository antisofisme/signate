# SPEC-09: Workflow Engine - Approval System

This document specifies the **Workflow Engine** that manages approval workflows, state transitions, and notifications across ARSAKA_PANDAWA. The Workflow Engine is a foundational service used by multiple modules (Accounting, Procurement, Approvals, etc.) to enforce business logic around approvals.

**Prerequisite**: SEC-03 (Authorization, Approval & Audit), REF-01 (Identity & Membership)

**Related**: SEC-03 mentions "Workflow Engine" as enforcement mechanism. This document defines its contract.

---

## Core Principles (Locked)

### Principle 1: Workflow is Business Logic, Not UI
- Approval workflow defined as explicit state machine (not hardcoded UI logic)
- State transitions trigger events and change domain state
- Approval can happen via API, webhook, or UI (channel-agnostic)

### Principle 2: One Workflow Engine Per Tenant
- Each tenant has isolated workflow instances
- No cross-tenant workflow sharing
- Workflow rules stored per tenant

### Principle 3: Idempotency & Durability
- Approval actions are idempotent (approving twice = same result)
- Workflow state persisted before events published
- State recovered from database, not event stream

### Principle 4: Audit Trail
- Every state transition logged with: who, when, what, before/after state
- Approval decisions immutable (approval cannot be revoked, only reversed)
- Audit trail maintained for 7 years (compliance)

### Principle 5: Extensibility
- New workflow types added without modifying engine
- Workflow templates can be customized per tenant
- Business rules stored as data, not code

---

## Workflow Engine Architecture

### Core Entities

#### 1. Workflow Definition
```
WorkflowDefinition {
  id: UUID,
  tenant_id: UUID,
  name: string,                    // e.g., "Invoice Approval"
  type: enum,                      // INVOICE_APPROVAL, PO_APPROVAL, ADJUSTMENT, etc.
  version: int,                    // Allows workflow updates
  states: [WorkflowState],
  transitions: [WorkflowTransition],
  created_at: timestamp,
  updated_at: timestamp
}
```

**Workflow Types**:
- `INVOICE_APPROVAL` - Accounting invoice approval
- `PO_APPROVAL` - Procurement purchase order approval
- `EXPENSE_APPROVAL` - HR expense approval
- `ADJUSTMENT_APPROVAL` - Accounting adjustments
- `REVERSAL_APPROVAL` - GL entry reversals

#### 2. Workflow State
```
WorkflowState {
  id: UUID,
  workflow_definition_id: UUID,
  name: enum,                      // DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED
  description: string,
  is_terminal: boolean,            // No transitions allowed
  notification_template: string,   // Which template to send
  auto_expire_days: int,           // Auto-reject if not approved in N days
  created_at: timestamp
}
```

**Standard States**:
- `DRAFT` - Created but not submitted
- `SUBMITTED` - Ready for review
- `PENDING_APPROVAL` - Awaiting approval
- `APPROVED` - Approved by authority
- `REJECTED` - Rejected with reason
- `ARCHIVED` - Closed/historical

#### 3. Workflow Instance
```
WorkflowInstance {
  id: UUID,
  tenant_id: UUID,
  workflow_definition_id: UUID,
  entity_type: string,             // "Invoice", "PurchaseOrder", etc.
  entity_id: UUID,                 // The actual invoice/PO id
  current_state: enum,
  current_approver_id: UUID,       // Who needs to approve now (null if no one)
  version: int NOT NULL DEFAULT 1, // ← OPTIMISTIC LOCKING: Incremented on every state change
  created_by: UUID,
  created_at: timestamp,
  submitted_at: timestamp,
  expired_at: timestamp,           // Auto-expiry time
  completed_at: timestamp
}
```

**Optimistic Locking Requirement**:
All state transition updates MUST include version check to prevent concurrent approval race conditions.

#### 4. Workflow Transition
```
WorkflowTransition {
  id: UUID,
  workflow_definition_id: UUID,
  from_state: enum,
  to_state: enum,
  trigger: enum,                   // SUBMIT, APPROVE, REJECT, REASSIGN, AUTO_EXPIRE
  required_permission: string,     // e.g., "invoice.approve"
  auto_trigger_condition: string,  // Optional: condition for automatic transition
  created_at: timestamp
}
```

#### 5. Workflow Step (Approval Record)
```
WorkflowStep {
  id: UUID,
  tenant_id: UUID,
  workflow_instance_id: UUID,
  step_number: int,                // 1st, 2nd, etc. approval
  approver_id: UUID,               // User who approved/rejected
  action: enum,                    // APPROVED, REJECTED, REASSIGNED
  action_reason: string,           // Why approved/rejected
  action_at: timestamp,
  is_immutable: true               // Cannot change approval decision
}
```

---

## Workflow State Machine

### Standard Invoice Approval Flow

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│ DRAFT ──[submit]--> PENDING_APPROVAL ──[approve/reject] │
│                            │                             │
│                      [auto_expire]                       │
│                            ↓                             │
│                       ARCHIVED                           │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ APPROVED: Post to GL, publish Invoice.Approved.v1 │  │
│ │ REJECTED: Notify creator, await resubmission      │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### State Transition Rules

| From State | Trigger | To State | Permission | Notes |
|-----------|---------|----------|-----------|-------|
| DRAFT | Submit | PENDING_APPROVAL | `invoice.submit` | User submits for approval |
| PENDING_APPROVAL | Approve | APPROVED | `invoice.approve` | Approver accepts |
| PENDING_APPROVAL | Reject | REJECTED | `invoice.approve` | Approver rejects |
| PENDING_APPROVAL | Auto-expire | ARCHIVED | (system) | After N days, auto-reject |
| REJECTED | Submit | PENDING_APPROVAL | `invoice.submit` | Resubmit after changes |
| APPROVED | (terminal) | - | - | No further transitions |
| ARCHIVED | (terminal) | - | - | No further transitions |

---

## Concurrency Control: Preventing Duplicate Approvals

**Problem**: Two approvers might simultaneously approve the same workflow instance, creating conflicting decisions.

**Solution**: Optimistic locking on WorkflowInstance.version field.

### State Transition Implementation (SQL Example)

```sql
-- CORRECT: Optimistic locking prevents duplicate approvals
UPDATE workflow_instances
SET
  current_state = 'APPROVED',
  version = version + 1,        -- Increment version on success
  completed_at = NOW()
WHERE
  id = $workflow_id
  AND tenant_id = $tenant_id
  AND current_state = 'PENDING_APPROVAL'  -- Check from_state
  AND version = $expected_version         -- CRITICAL: Version check
RETURNING version;

-- If no rows updated, version mismatch occurred
-- → Workflow state changed between read and write
-- → Return 409 Conflict to client
```

### Application Logic (TypeScript Example)

```typescript
async function approveWorkflow(workflowId: string, approverId: string, reason: string) {
  // Step 1: Read current workflow state
  const workflow = await getWorkflowInstance(workflowId);

  // Check if workflow can be approved
  if (workflow.current_state !== 'PENDING_APPROVAL') {
    throw new ConflictError('INVALID_STATE',
      `Cannot approve workflow in state ${workflow.current_state}`);
  }

  if (workflow.current_approver_id !== approverId) {
    throw new ForbiddenError('NOT_CURRENT_APPROVER',
      `User ${approverId} is not current approver`);
  }

  // Step 2: Attempt state transition with version check
  const result = await db.query(
    `UPDATE workflow_instances
     SET current_state = 'APPROVED', version = version + 1, completed_at = NOW()
     WHERE id = $1 AND tenant_id = $2 AND version = $3 AND current_state = 'PENDING_APPROVAL'
     RETURNING version`,
    [workflowId, workflow.tenant_id, workflow.version]
  );

  // Step 3: Check if update succeeded
  if (result.rowCount === 0) {
    // Version mismatch = workflow changed since we read it
    throw new ConflictError('WORKFLOW_CHANGED',
      'Workflow state changed during approval. Another user may have acted. Retry.'
    );
  }

  // Step 4: Record approval action (immutable)
  await createWorkflowStep({
    workflow_instance_id: workflowId,
    approver_id: approverId,
    action: 'APPROVED',
    action_reason: reason,
    action_at: new Date(),
    is_immutable: true
  });

  // Step 5: Publish approval event
  await publishEvent({
    event_type: 'Approval.Approved.v1',
    workflow_instance_id: workflowId,
    approved_by: approverId,
    approval_reason: reason
  });

  return { status: 'APPROVED', version: result.rows[0].version };
}
```

### Race Condition Handled

```
Timeline of concurrent approval race (NOW PREVENTED):

T1: Approver A reads workflow (version=5, state=PENDING_APPROVAL)
T2: Approver B reads workflow (version=5, state=PENDING_APPROVAL)
T3: Approver A clicks "Approve"
    → UPDATE ... WHERE version = 5 (succeeds)
    → version becomes 6
T4: Approver B clicks "Reject"
    → UPDATE ... WHERE version = 5 (FAILS - version now 6)
    → Returns 409 Conflict
    → Approver B sees: "Workflow already approved, refresh to see details"

Result: Only A's approval accepted. B's action rejected with clear error.
```

### Client-Side Retry Logic

```typescript
async function approveWithRetry(workflowId: string, maxRetries: number = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await approveWorkflow(workflowId, userId, reason);
    } catch (error) {
      if (error.code === 'WORKFLOW_CHANGED' && attempt < maxRetries) {
        // Workflow changed, wait and retry
        await delay(1000 * attempt);  // Exponential backoff
        continue;
      }
      throw error;  // Other errors or max retries reached
    }
  }
}
```

---

## Workflow Events (Authoritative Approval Events)

> **Standard**: These are the AUTHORITATIVE approval events used throughout ARSAKA_PANDAWA (referenced in CORE-STD-20)

The Workflow Engine publishes events for all state transitions. All approval workflows MUST use these standard event types:

**Event Types**:
- `Approval.Submitted.v1` — Request submitted for approval (entity moves to PENDING_APPROVAL)
- `Approval.Approved.v1` — Approved by authorized user (entity moves to APPROVED)
- `Approval.Rejected.v1` — Rejected with reason (entity moves to REJECTED)
- `Approval.Expired.v1` — Auto-expired after timeout (entity moves to ARCHIVED)

**Format**: All approval events follow pattern `Approval.{Action}.v1` with consistent payload structure.

### Approval.Submitted.v1
```json
{
  "event_type": "Approval.Submitted.v1",
  "correlation_id": "inv-12345",
  "tenant_id": "hotel-001",
  "payload": {
    "workflow_instance_id": "wf-001",
    "entity_type": "Invoice",
    "entity_id": "inv-12345",
    "submitted_by": "user-789",
    "submitted_at": "2025-12-24T10:00:00Z",
    "amount": 50000.00,
    "approval_authority": "CFO"
  }
}
```

### Approval.Approved.v1
```json
{
  "event_type": "Approval.Approved.v1",
  "correlation_id": "inv-12345",
  "tenant_id": "hotel-001",
  "payload": {
    "workflow_instance_id": "wf-001",
    "entity_type": "Invoice",
    "entity_id": "inv-12345",
    "approved_by": "cfo-user-123",
    "approved_at": "2025-12-24T14:30:00Z",
    "approval_reason": "Budget approved by CFO"
  }
}
```

### Approval.Rejected.v1
```json
{
  "event_type": "Approval.Rejected.v1",
  "correlation_id": "inv-12345",
  "tenant_id": "hotel-001",
  "payload": {
    "workflow_instance_id": "wf-001",
    "entity_type": "Invoice",
    "entity_id": "inv-12345",
    "rejected_by": "manager-456",
    "rejected_at": "2025-12-24T15:00:00Z",
    "rejection_reason": "Missing supporting documentation"
  }
}
```

### Approval.Expired.v1
```json
{
  "event_type": "Approval.Expired.v1",
  "correlation_id": "inv-12345",
  "tenant_id": "hotel-001",
  "payload": {
    "workflow_instance_id": "wf-001",
    "entity_type": "Invoice",
    "entity_id": "inv-12345",
    "expired_at": "2025-12-31T23:59:59Z",
    "days_waiting": 7,
    "auto_archived": true
  }
}
```

---

## Workflow Configuration Examples

### Example 1: Simple Approval (< $5,000)
```typescript
const simpleApprovalWorkflow = {
  id: 'wf-template-simple',
  tenant_id: 'hotel-001',
  name: 'Simple Invoice Approval',
  type: 'INVOICE_APPROVAL',
  states: [
    { name: 'DRAFT', is_terminal: false },
    { name: 'SUBMITTED', is_terminal: false },
    { name: 'APPROVED', is_terminal: true },
    { name: 'REJECTED', is_terminal: true }
  ],
  transitions: [
    {
      from_state: 'DRAFT',
      to_state: 'SUBMITTED',
      trigger: 'SUBMIT',
      required_permission: 'invoice.submit',
      auto_trigger_condition: null
    },
    {
      from_state: 'SUBMITTED',
      to_state: 'APPROVED',
      trigger: 'APPROVE',
      required_permission: 'invoice.approve_low',
      auto_trigger_condition: null
    }
  ]
};
```

### Example 2: Escalation Approval (> $50,000)
```typescript
const escalationApprovalWorkflow = {
  name: 'High-Value Invoice Approval',
  states: [
    { name: 'DRAFT' },
    { name: 'PENDING_MANAGER', auto_expire_days: 3 },
    { name: 'PENDING_CFO', auto_expire_days: 5 },
    { name: 'APPROVED', is_terminal: true },
    { name: 'REJECTED', is_terminal: true }
  ],
  transitions: [
    {
      from_state: 'DRAFT',
      to_state: 'PENDING_MANAGER',
      trigger: 'SUBMIT',
      required_permission: 'invoice.submit'
    },
    {
      from_state: 'PENDING_MANAGER',
      to_state: 'PENDING_CFO',
      trigger: 'APPROVE',
      required_permission: 'invoice.approve_manager',
      auto_trigger_condition: null  // Manager must explicitly approve
    },
    {
      from_state: 'PENDING_CFO',
      to_state: 'APPROVED',
      trigger: 'APPROVE',
      required_permission: 'invoice.approve_cfo',
      auto_trigger_condition: null  // CFO must explicitly approve
    }
  ]
};
```

---

## Approval Authority Rules

The Workflow Engine enforces approval authority (who can approve and for how much):

```
ApprovalAuthority {
  id: UUID,
  tenant_id: UUID,
  user_id: UUID,
  resource_type: string,           // "Invoice", "PurchaseOrder", etc.
  max_amount: decimal,             // Max amount they can approve
  approval_level: int,             // 1=lowest, 5=highest
  effective_date: date,
  expiry_date: date
}
```

**Example**:
- Manager: Can approve invoices < $5,000
- Director: Can approve invoices < $50,000
- CFO: Can approve invoices < unlimited

---

## API Endpoints

### 1. Submit for Approval
```
POST /api/v1/workflows/submit

Request:
{
  "entity_type": "Invoice",
  "entity_id": "inv-12345",
  "message": "Ready for approval"
}

Response:
{
  "workflow_instance_id": "wf-001",
  "current_state": "SUBMITTED",
  "current_approver_id": "user-123",
  "created_event": "Approval.Submitted.v1"
}
```

### 2. Approve
```
POST /api/v1/workflows/{workflow_instance_id}/approve

Request:
{
  "approval_reason": "Budget approved"
}

Response:
{
  "workflow_instance_id": "wf-001",
  "current_state": "APPROVED",
  "published_event": "Approval.Approved.v1"
}
```

### 3. Reject
```
POST /api/v1/workflows/{workflow_instance_id}/reject

Request:
{
  "rejection_reason": "Missing documentation"
}

Response:
{
  "workflow_instance_id": "wf-001",
  "current_state": "REJECTED",
  "published_event": "Approval.Rejected.v1"
}
```

### 4. Get Workflow Status
```
GET /api/v1/workflows/{workflow_instance_id}

Response:
{
  "workflow_instance_id": "wf-001",
  "entity_type": "Invoice",
  "entity_id": "inv-12345",
  "current_state": "PENDING_APPROVAL",
  "current_approver": {
    "id": "user-123",
    "name": "Alice Manager",
    "approval_authority": "< $50,000"
  },
  "created_at": "2025-12-24T10:00:00Z",
  "submitted_at": "2025-12-24T10:05:00Z",
  "expires_at": "2025-12-27T10:05:00Z",
  "approval_history": [
    {
      "step": 1,
      "state": "SUBMITTED",
      "changed_by": "user-789",
      "changed_at": "2025-12-24T10:05:00Z",
      "reason": null
    }
  ]
}
```

---

## Integration Points

### How Accounting Uses Workflow Engine

```
User creates invoice (DRAFT state)
    ↓
User clicks "Submit for Approval"
    ↓ Workflow Engine transitions to PENDING_APPROVAL
    ↓ Publishes Approval.Submitted.v1
    ↓
Accounting.Adapter listens to Approval.Submitted
    ↓ Prevents GL posting (invoice locked)
    ↓
Approver reviews and clicks "Approve"
    ↓ Workflow Engine transitions to APPROVED
    ↓ Publishes Approval.Approved.v1
    ↓
Accounting.Adapter listens to Approval.Approved
    ↓ Posts journal entries to GL
    ↓ Publishes Accounting.Invoice.Finalized.v1
```

---

## Compliance & Audit Trail

### Audit Log for Approvals
```
AuditLog {
  id: UUID,
  tenant_id: UUID,
  workflow_instance_id: UUID,
  action: "APPROVAL_STATE_CHANGE",
  state_from: "SUBMITTED",
  state_to: "APPROVED",
  actor_id: "cfo-user-123",
  actor_name: "Alice CFO",
  action_at: "2025-12-24T14:30:00Z",
  metadata: {
    approval_reason: "Budget confirmed",
    entity_type: "Invoice",
    entity_id: "inv-12345",
    amount: 50000.00
  },
  is_immutable: true
}
```

All approval decisions are immutable. To reverse an approval decision, create a new reversal workflow (not by modifying the original approval).

---

## Implementation Checklist

- [ ] WorkflowDefinition CRUD endpoints
- [ ] WorkflowInstance creation and state management
- [ ] State transition validation (permissions + authority)
- [ ] Event publishing for all state changes
- [ ] Notification system (email/SMS for approvers)
- [ ] Auto-expiry job (reject after N days)
- [ ] Audit trail logging
- [ ] API endpoints (submit, approve, reject, status)
- [ ] Integration with Accounting module
- [ ] Integration with Procurement module
- [ ] Dashboard: pending approvals list
- [ ] Admin: configure workflows per tenant
