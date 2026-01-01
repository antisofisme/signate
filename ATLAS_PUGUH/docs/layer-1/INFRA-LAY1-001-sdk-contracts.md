# INFRA-LAY1-001: SDK Contracts & Entry Point Design

**VERSION**: Layer 1 DRAFT
**STATUS**: READY FOR LOCKING (3 clarifications applied)
**DATE**: 2025-12-27

---

## Overview

The SDK is the **ONLY entry point** for applications to interact with Infra. It is the **gatekeeper** for Layer 0 constraints:
- tenant_id validation (mandatory, every request)
- Context sanitization (no PII)
- Decision immutability enforcement
- Role-based approval (not user-based)
- Fail-closed behavior

---

## 1. SDK Scope & Responsibilities

### 1.1 SDK MUST Enforce

| Constraint | Why | How |
|-----------|-----|-----|
| tenant_id mandatory | Hard isolation | Reject requests without tenant_id |
| Context sanitization | Security/audit | Filter PII before transmission to Core |
| Decision immutability | Guarantee | Return 400 if attempt to modify decision_outcome |
| Role-based approval | Architecture | Accept only role identifiers in approver fields |
| Fail-closed default | Safety | If rule evaluation finds no match, outcome = DENIED (not proceed) |
| First-match-wins | Determinism | No retry/re-eval after decision made |

### 1.2 SDK Scope: Decision Lifecycle Only

**IN SCOPE**:
```
Application
    ↓
  SDK
    ├─ createDecision(decision_type, context, tenant_id)
    ├─ getDecision(decision_id, tenant_id)
    ├─ queryDecisions(filters, tenant_id)
    ├─ getWorkflow(workflow_id, tenant_id)
    ├─ approveWorkflow(workflow_id, approver_role, tenant_id)
    ├─ rejectWorkflow(workflow_id, approver_role, tenant_id)
    ├─ delegateWorkflow(workflow_id, delegated_to_user_id, tenant_id)
    └─ escalateWorkflow(workflow_id, tenant_id)
```

**NOT IN SCOPE**:
- Rule management (CMS only)
- User identity resolution (Application adapter only)
- Rule execution engine (Core only)
- Audit log querying (CMS only, with audit trail)
- Extension hook invocation (Core async only)

---

## 2. SDK Method Contracts

### 2.1 Create Decision

**Method**:
```typescript
createDecision(
  decision_type: string,
  context: object,
  tenant_id: string,
  idempotency_key?: string
): Promise<DecisionResponse>
```

**Request**:
```json
{
  "decision_type": "accounting.journal_approval",
  "context": {
    "journal_entry_amount": 15000,
    "journal_entry_type": "correction",
    "requester_role": "staff",
    "approval_authority": "accounting_manager"
  },
  "tenant_id": "hotel-123",
  "idempotency_key": "req-abc-123"
}
```

**Request Validation** (SDK MUST enforce):
```typescript
// STEP 1: tenant_id present and non-empty
if (!request.tenant_id || request.tenant_id.trim() === "") {
  return ERROR_400("tenant_id is required and non-empty");
}

// STEP 2: decision_type matches pattern
if (!/^[a-z_]+\.[a-z_]+\.[a-z_]+$/.test(request.decision_type)) {
  return ERROR_400(
    "Invalid decision_type. Format: {module}.{entity}.{action}. " +
    "Example: accounting.journal_approval"
  );
}

// STEP 3: context is object, not empty
if (!request.context || typeof request.context !== "object" ||
    Object.keys(request.context).length === 0) {
  return ERROR_400("context is required and must be non-empty object");
}

// STEP 4: Sanitize context (remove PII)
const sanitized_context = sanitizeContext(request.context);
// REJECT if sanitization found prohibited fields
if (sanitized_context.rejected_fields.length > 0) {
  return ERROR_400(
    "Context contains prohibited fields: " +
    sanitized_context.rejected_fields.join(", ") +
    ". Allowed: IDs, enums, numeric thresholds, booleans, timestamps"
  );
}
```

**Context Sanitization Rules**:
```typescript
interface ContextSanitization {
  ALLOWED: [
    "IDs (user_id, entity_id, org_id)",
    "Enum values (status, role, category)",
    "Numeric thresholds (amounts, quantities, counts)",
    "Boolean flags",
    "Timestamps (RFC3339)"
  ],

  PROHIBITED: [
    "PII (names, emails, phone_numbers, SSN)",
    "Full payloads (transaction data, documents)",
    "Sensitive strings (API keys, credentials, secrets)",
    "Granular financial details (account_codes, GL entries)",
    "Personal data that identifies individuals"
  ],

  DETECTION: [
    "email", "phone", "ssn", "password",
    "credit_card", "account_code", "secret",
    "private_key", "token", "api_key"
  ],

  ACTION: "REJECT + return 400 with list of prohibited fields"
}
```

**Response (Success - ALLOWED)**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-abc-123",
    "decision_type": "accounting.journal_approval",
    "tenant_id": "hotel-123",
    "requester_user_id": "user-456",
    "requested_at": "2025-12-27T10:30:00Z",
    "decided_at": "2025-12-27T10:30:01Z",
    "context": {
      "journal_entry_amount": 15000,
      "journal_entry_type": "correction",
      "requester_role": "staff"
    },
    "outcome": "ALLOWED",
    "rule_matched": "correction_amount_below_5k",
    "rule_version": "1.2",
    "approval_workflow_id": null
  }
}
```

**Response (Success - REQUIRE_APPROVAL)**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-xyz-789",
    "decision_type": "accounting.journal_approval",
    "tenant_id": "hotel-123",
    "requester_user_id": "user-456",
    "requested_at": "2025-12-27T10:30:00Z",
    "decided_at": "2025-12-27T10:30:01Z",
    "context": {
      "journal_entry_amount": 15000,
      "journal_entry_type": "correction",
      "requester_role": "staff"
    },
    "outcome": "REQUIRE_APPROVAL",
    "rule_matched": "correction_amount_15000_cfo",
    "rule_version": "1.2",
    "approval_workflow_id": "wf-pqr-456"
  }
}
```

**Response (Success - DENIED)**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-ijk-456",
    "decision_type": "accounting.journal_approval",
    "tenant_id": "hotel-123",
    "requester_user_id": "user-456",
    "requested_at": "2025-12-27T10:30:00Z",
    "decided_at": "2025-12-27T10:30:01Z",
    "context": {
      "period_status": "CLOSED"
    },
    "outcome": "DENIED",
    "rule_matched": "period_closed_forbidden",
    "rule_version": "2.0",
    "approval_workflow_id": null
  }
}
```

**Response (Validation Error)**:
```json
{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "tenant_id is required and non-empty",
  "details": {
    "field": "tenant_id",
    "reason": "MISSING"
  }
}
```

**Response (Configuration Error - No Rules)**:
```json
{
  "status": "error",
  "error_code": "NO_RULES_CONFIGURED",
  "message": "No rules configured for decision_type in tenant",
  "details": {
    "decision_type": "accounting.journal_approval",
    "tenant_id": "hotel-123"
  }
}
```

**Response (Unknown decision_type)**:
```json
{
  "status": "error",
  "error_code": "UNKNOWN_DECISION_TYPE",
  "message": "decision_type not registered",
  "details": {
    "decision_type": "invalid.type.here",
    "valid_pattern": "{module}.{entity}.{action}"
  }
}
```

**Semantics**:
- Synchronous call, < 100ms p95
- Idempotent if `idempotency_key` provided (same key → same decision_id)
- Returns immediately (does NOT wait for workflow completion)
- decision_outcome NEVER changes after this call returns
- If REQUIRE_APPROVAL → workflow_id populated, application handles approval UX

**CLARIFICATION 1: Fail-Closed Applies Only After Rule Evaluation**:
```
SDK Validation Errors (400 - Bad Request):
  - Missing tenant_id → ERROR_400 (not a decision)
  - Invalid decision_type format → ERROR_400 (not a decision)
  - Context contains PII → ERROR_400 (not a decision)
  - Empty context → ERROR_400 (not a decision)

  These are request validation failures. SDK rejects request before
  transmission to Core.

Rule Evaluation Errors (200 - Success with outcome):
  - No rules configured for decision_type → status=success, error_code=NO_RULES_CONFIGURED
  - All rules evaluated, none match → decision.outcome = DENIED (fail-closed)
  - Unknown decision_type → status=success, error_code=UNKNOWN_DECISION_TYPE

  After SDK validation passes, Core evaluates rules. If no rule matches
  (or rules are misconfigured), outcome = DENIED (fail-closed guarantee).
```

**CLARIFICATION 2: requester_user_id is Audit Metadata Only**:
```
requester_user_id field:
  - Injected by SDK from auth context (JWT/session)
  - Used ONLY for audit trail ("who requested this?")
  - NOT used in any decision logic, rule evaluation, or approvals
  - NOT used to resolve approver roles
  - NOT stored in rule conditions

Example:
  User staff-123 requests decision for accounting.journal_approval
  → decision.requester_user_id = "staff-123" (for audit only)
  → Rules evaluate context.requester_role = "staff" (not user_id)
  → Rules may check IF requester_role IN ["manager", "cfo"] (not user identity)
```

**Guard Rails**:
```typescript
// GR-1: tenant_id immutable in request
// If request.tenant_id differs from auth context, REJECT

// GR-2: No decision_id in request (system-generated)
// If request contains decision_id, REJECT as invalid field

// GR-3: Context cannot be modified after creation
// Decision is immutable, context is immutable

// GR-4: requester_user_id derived from auth context
// SDK injects from JWT/session, not from request body

// GR-5: Idempotency only for creation
// If same idempotency_key + different context → REJECT as error
```

---

### 2.2 Get Decision

**Method**:
```typescript
getDecision(
  decision_id: string,
  tenant_id: string
): Promise<DecisionResponse>
```

**Request**:
```json
{
  "decision_id": "dec-abc-123",
  "tenant_id": "hotel-123"
}
```

**Request Validation**:
```typescript
// STEP 1: tenant_id non-empty
if (!request.tenant_id) {
  return ERROR_400("tenant_id required");
}

// STEP 2: decision_id valid UUID format
if (!isValidUUID(request.decision_id)) {
  return ERROR_400("decision_id must be valid UUID");
}

// STEP 3: Check tenant ownership
const decision = await core.getDecision(request.decision_id);
if (!decision || decision.tenant_id !== request.tenant_id) {
  return ERROR_404("Decision not found or tenant mismatch");
}

// STEP 4: Return full decision (immutable)
return {
  status: "success",
  decision: {
    decision_id,
    outcome,
    rule_matched,
    context,
    // ... all fields
  }
};
```

**Response**:
```json
{
  "status": "success",
  "decision": {
    "decision_id": "dec-abc-123",
    "decision_type": "accounting.journal_approval",
    "tenant_id": "hotel-123",
    "requester_user_id": "user-456",
    "requested_at": "2025-12-27T10:30:00Z",
    "decided_at": "2025-12-27T10:30:01Z",
    "outcome": "ALLOWED",
    "rule_matched": "correction_amount_below_5k",
    "rule_version": "1.2",
    "context": { /* sanitized */ },
    "approval_workflow_id": null
  }
}
```

**Semantics**:
- Synchronous, read-only
- Returns immutable decision snapshot
- Tenant isolation enforced (404 if tenant_id mismatch)
- No modification possible

---

### 2.3 Query Decisions

**Method**:
```typescript
queryDecisions(
  tenant_id: string,
  filters?: {
    decision_type?: string,
    outcome?: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL",
    requested_by_user_id?: string,
    requested_after?: timestamp,
    requested_before?: timestamp,
    limit?: number,
    offset?: number
  }
): Promise<QueryDecisionsResponse>
```

**Request**:
```json
{
  "tenant_id": "hotel-123",
  "filters": {
    "decision_type": "accounting.journal_approval",
    "outcome": "REQUIRE_APPROVAL",
    "requested_after": "2025-12-20T00:00:00Z",
    "limit": 50,
    "offset": 0
  }
}
```

**Request Validation**:
```typescript
// STEP 1: tenant_id mandatory
if (!request.tenant_id) {
  return ERROR_400("tenant_id required");
}

// STEP 2: Validate filter values (if provided)
if (request.filters.decision_type &&
    !/^[a-z_]+\.[a-z_]+\.[a-z_]+$/.test(request.filters.decision_type)) {
  return ERROR_400("Invalid decision_type format");
}

if (request.filters.outcome &&
    !["ALLOWED", "DENIED", "REQUIRE_APPROVAL"].includes(request.filters.outcome)) {
  return ERROR_400("Invalid outcome value");
}

// STEP 3: Validate pagination
const limit = Math.min(request.filters.limit || 20, 500);  // max 500
const offset = request.filters.offset || 0;

if (limit < 1 || offset < 0) {
  return ERROR_400("Invalid pagination");
}

// STEP 4: Query with tenant isolation
const decisions = await core.queryDecisions(request.tenant_id, filters, limit, offset);

return {
  status: "success",
  decisions,
  pagination: { limit, offset, total: decisions.length }
};
```

**Response**:
```json
{
  "status": "success",
  "decisions": [
    {
      "decision_id": "dec-abc-123",
      "decision_type": "accounting.journal_approval",
      "outcome": "REQUIRE_APPROVAL",
      "rule_matched": "correction_amount_15000_cfo",
      "requested_at": "2025-12-27T10:30:00Z",
      "decided_at": "2025-12-27T10:30:01Z",
      "requester_user_id": "user-456",
      "approval_workflow_id": "wf-pqr-456"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 127
  }
}
```

**Semantics**:
- Tenant-scoped (cannot query other tenants)
- Maximum 500 results per page
- Results sorted by requested_at DESC (most recent first)
- Outcome filter is optional but recommended for large datasets

---

### 2.4 Get Workflow

**Method**:
```typescript
getWorkflow(
  workflow_id: string,
  tenant_id: string
): Promise<WorkflowResponse>
```

**Request**:
```json
{
  "workflow_id": "wf-pqr-456",
  "tenant_id": "hotel-123"
}
```

**Response**:
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-pqr-456",
    "decision_id": "dec-abc-123",
    "tenant_id": "hotel-123",
    "state": "PENDING_APPROVAL",
    "approver_role": "CFO",
    "created_at": "2025-12-27T10:30:01Z",
    "escalation_timeout_at": "2025-12-28T10:30:01Z",
    "escalation_target_role": "chief_finance_officer",
    "delegated_to_user_id": null,
    "approvals": [
      {
        "timestamp": "2025-12-27T10:30:01Z",
        "approver_role": "CFO",
        "approved_by_user_id": "user-cfo-001",
        "action": "PENDING",
        "comment": ""
      }
    ],
    "state_transitions": [
      {
        "from_state": "CREATED",
        "to_state": "PENDING_APPROVAL",
        "timestamp": "2025-12-27T10:30:01Z",
        "reason": "WORKFLOW_INITIATED"
      }
    ]
  }
}
```

**Semantics**:
- Read-only (no mutations on returned object)
- Tenant isolation enforced
- Complete state history included
- Used to check approval progress

---

### 2.5 Approve Workflow

**Method**:
```typescript
approveWorkflow(
  workflow_id: string,
  approver_role: string,
  tenant_id: string,
  comment?: string
): Promise<WorkflowResponse>
```

**Request**:
```json
{
  "workflow_id": "wf-pqr-456",
  "approver_role": "CFO",
  "tenant_id": "hotel-123",
  "comment": "Approved per policy"
}
```

**Request Validation**:
```typescript
// STEP 1: tenant_id non-empty
if (!request.tenant_id) {
  return ERROR_400("tenant_id required");
}

// STEP 2: workflow_id valid UUID
if (!isValidUUID(request.workflow_id)) {
  return ERROR_400("workflow_id must be valid UUID");
}

// STEP 3: approver_role non-empty string
if (!request.approver_role || typeof request.approver_role !== "string") {
  return ERROR_400("approver_role must be non-empty string (role identifier)");
}

// STEP 4: Fetch workflow with tenant check
const workflow = await core.getWorkflow(request.workflow_id);
if (!workflow || workflow.tenant_id !== request.tenant_id) {
  return ERROR_404("Workflow not found or tenant mismatch");
}

// STEP 5: Verify workflow is in PENDING_APPROVAL state
if (workflow.state !== "PENDING_APPROVAL") {
  return ERROR_409(
    `Cannot approve workflow in state ${workflow.state}. ` +
    `Expected PENDING_APPROVAL`
  );
}

// STEP 6: Verify approver_role matches assigned role
if (workflow.approver_role !== request.approver_role) {
  return ERROR_403(
    `Role ${request.approver_role} is not authorized to approve. ` +
    `Expected role: ${workflow.approver_role}`
  );
}

// STEP 7: Transition to APPROVED state
const updated_workflow = await core.transitionWorkflow(
  workflow_id,
  "PENDING_APPROVAL",
  "APPROVED",
  {
    approver_role: request.approver_role,
    approved_by_user_id: auth_context.user_id,  // From auth, not request
    comment: request.comment || "",
    timestamp: now()
  }
);

// STEP 8: Return updated workflow (immutable after transition)
return {
  status: "success",
  workflow: updated_workflow
};
```

**Response (Success)**:
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-pqr-456",
    "state": "APPROVED",
    "approvals": [
      {
        "timestamp": "2025-12-27T10:30:01Z",
        "approver_role": "CFO",
        "approved_by_user_id": "user-cfo-001",
        "action": "APPROVED",
        "comment": "Approved per policy"
      }
    ]
  }
}
```

**Response (Wrong State)**:
```json
{
  "status": "error",
  "error_code": "INVALID_STATE",
  "message": "Cannot approve workflow in state ESCALATED. Expected PENDING_APPROVAL or DELEGATED_TO_*",
  "details": {
    "workflow_id": "wf-pqr-456",
    "current_state": "ESCALATED"
  }
}
```

**Response (Role Not Authorized)**:
```json
{
  "status": "error",
  "error_code": "UNAUTHORIZED_ROLE",
  "message": "Role manager is not authorized. Expected role: CFO",
  "details": {
    "requested_role": "manager",
    "assigned_role": "CFO"
  }
}
```

**Semantics**:
- Synchronous
- Idempotent: approving same workflow twice with same role → second call returns same state (no error)
- approved_by_user_id injected from auth context (NOT from request)
- Comment is optional, for audit trail
- Workflow transitions to APPROVED (immutable after)
- Decision outcome does NOT change (still REQUIRE_APPROVAL)

**Guard Rails**:
```typescript
// GR-1: Role-based, not user-based
// approver_role is string identifier ("CFO"), not user_id
// SDK does NOT resolve user; application adapter does

// GR-2: approved_by_user_id from auth context
// If request contains approved_by_user_id, REJECT (invalid field)
// SDK injects from JWT/session

// GR-3: Workflow state immutable after transition
// Once APPROVED, cannot change back to PENDING

// GR-4: Role authorization strict
// If workflow.approver_role ≠ request.approver_role → ERROR_403

// GR-5: Escalation not bypassed
// Cannot approve escalated workflow with original approver role
// Must use escalation_target_role
```

---

### 2.6 Reject Workflow

**Method**:
```typescript
rejectWorkflow(
  workflow_id: string,
  approver_role: string,
  tenant_id: string,
  reason?: string
): Promise<WorkflowResponse>
```

**Request Validation** (Similar to approveWorkflow):
```typescript
// Same validation as approve:
// - tenant_id non-empty
// - workflow_id valid UUID
// - approver_role must match assigned role
// - workflow state must be PENDING_APPROVAL or DELEGATED_TO_*

// Additional check:
// - reason must be < 500 characters (audit trail)

const updated_workflow = await core.transitionWorkflow(
  workflow_id,
  "PENDING_APPROVAL",
  "REJECTED",
  {
    approver_role: request.approver_role,
    rejected_by_user_id: auth_context.user_id,
    reason: request.reason || "",
    timestamp: now()
  }
);

return {
  status: "success",
  workflow: updated_workflow
};
```

**Response (Success)**:
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-pqr-456",
    "state": "REJECTED",
    "approvals": [
      {
        "timestamp": "2025-12-27T10:30:01Z",
        "approver_role": "CFO",
        "rejected_by_user_id": "user-cfo-001",
        "action": "REJECTED",
        "reason": "Amount exceeds policy limit"
      }
    ]
  }
}
```

**Semantics**:
- Synchronous
- Idempotent (same rejection twice → same workflow state)
- rejected_by_user_id from auth context
- Workflow transitions to REJECTED (immutable)
- Application handles rejection UX (e.g., retry with modified context)

---

### 2.7 Delegate Workflow

**Method**:
```typescript
delegateWorkflow(
  workflow_id: string,
  approver_role: string,
  delegated_to_user_id: string,
  tenant_id: string,
  reason?: string
): Promise<WorkflowResponse>
```

**Request**:
```json
{
  "workflow_id": "wf-pqr-456",
  "approver_role": "CFO",
  "delegated_to_user_id": "user-cfo-backup",
  "tenant_id": "hotel-123",
  "reason": "CFO on leave"
}
```

**Request Validation**:
```typescript
// STEP 1: All basic validations (tenant_id, workflow_id, approver_role)

// STEP 2: delegated_to_user_id non-empty string
if (!request.delegated_to_user_id ||
    typeof request.delegated_to_user_id !== "string") {
  return ERROR_400("delegated_to_user_id must be non-empty string");
}

// STEP 3: Verify approver_role matches assigned
// (same as approve/reject)

// STEP 4: Verify workflow state is PENDING_APPROVAL
// (same as approve/reject)

// STEP 5: Transition to DELEGATED_TO_* state
const updated_workflow = await core.transitionWorkflow(
  workflow_id,
  "PENDING_APPROVAL",
  "DELEGATED_TO_" + request.delegated_to_user_id,
  {
    approver_role: request.approver_role,
    delegated_by_user_id: auth_context.user_id,
    delegated_to_user_id: request.delegated_to_user_id,
    reason: request.reason || "",
    timestamp: now()
  }
);

return {
  status: "success",
  workflow: updated_workflow
};
```

**Response (Success)**:
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-pqr-456",
    "state": "DELEGATED_TO_user-cfo-backup",
    "delegated_to_user_id": "user-cfo-backup",
    "approvals": [
      {
        "timestamp": "2025-12-27T10:45:00Z",
        "approver_role": "CFO",
        "delegated_by_user_id": "user-cfo-001",
        "delegated_to_user_id": "user-cfo-backup",
        "action": "DELEGATED",
        "reason": "CFO on leave"
      }
    ]
  }
}
```

**Semantics**:
- Workflow state becomes DELEGATED_TO_{user_id}
- delegated_to_user_id MUST be valid (SDK does NOT validate; application adapter does)
- delegated_by_user_id from auth context
- Delegated user can now approve/reject/escalate
- Not a redirect to different role; same role, different user

**CLARIFICATION 3: delegated_to_user_id is Opaque Audit Field**:
```
delegated_to_user_id:
  - Stored as-is from request (opaque string identifier)
  - Infra does NOT validate it's a real user in system
  - Infra does NOT resolve roles for this user
  - Infra does NOT check if user has approver_role permissions
  - Used ONLY for audit trail ("delegated to whom?")
  - Application adapter responsible for validating user exists
  - Application adapter responsible for notifying user of delegation

Example:
  POST /workflows/wf-abc/delegate {
    approver_role: "CFO",
    delegated_to_user_id: "user-cfo-backup"  // ← Opaque string
  }

  Infra stores: delegated_to_user_id = "user-cfo-backup"
  Infra does NOT:
    - Validate user-cfo-backup exists
    - Check if user-cfo-backup has CFO role
    - Resolve user-cfo-backup's actual permissions

  Application adapter (after workflow returned):
    - Verifies user-cfo-backup exists in user service
    - Verifies user-cfo-backup has CFO role
    - Sends notification to user-cfo-backup
    - Handles case if user not found
```

**Guard Rails**:
```typescript
// GR-1: delegated_to_user_id from request (application validates it's real user)
// SDK accepts string, application ensures it's valid

// GR-2: delegated_by_user_id from auth context
// If request contains this field, REJECT

// GR-3: Only one delegation at a time
// Cannot delegate to multiple users in chain

// GR-4: Delegated user has same approver_role
// Cannot delegate to user with different role

// GR-5: delegated_to_user_id is opaque
// SDK does NOT validate, resolve, or check user permissions
// Application adapter validates after receiving workflow
```

---

### 2.8 Escalate Workflow

**Method**:
```typescript
escalateWorkflow(
  workflow_id: string,
  tenant_id: string,
  reason?: string
): Promise<WorkflowResponse>
```

**Request**:
```json
{
  "workflow_id": "wf-pqr-456",
  "tenant_id": "hotel-123",
  "reason": "Approval timeout, escalating to CFO"
}
```

**Request Validation**:
```typescript
// STEP 1: tenant_id non-empty
if (!request.tenant_id) {
  return ERROR_400("tenant_id required");
}

// STEP 2: workflow_id valid UUID
if (!isValidUUID(request.workflow_id)) {
  return ERROR_400("workflow_id must be valid UUID");
}

// STEP 3: Fetch workflow
const workflow = await core.getWorkflow(request.workflow_id);
if (!workflow || workflow.tenant_id !== request.tenant_id) {
  return ERROR_404("Workflow not found or tenant mismatch");
}

// STEP 4: Verify not already escalated
if (workflow.state === "ESCALATED") {
  return ERROR_409("Workflow already escalated");
}

// STEP 5: Verify escalation_target_role exists
if (!workflow.escalation_target_role) {
  return ERROR_400(
    "Workflow has no escalation_target_role configured. " +
    "Cannot escalate."
  );
}

// STEP 6: Transition to ESCALATED state
const updated_workflow = await core.transitionWorkflow(
  workflow_id,
  workflow.state,  // from current state (PENDING or DELEGATED)
  "ESCALATED",
  {
    escalated_by_user_id: auth_context.user_id,
    escalation_target_role: workflow.escalation_target_role,
    reason: request.reason || "",
    timestamp: now()
  }
);

// STEP 7: async trigger escalation hooks (fire-and-forget)
invokeEscalationHooksAsync(workflow_id, workflow.escalation_target_role);

return {
  status: "success",
  workflow: updated_workflow
};
```

**Response (Success)**:
```json
{
  "status": "success",
  "workflow": {
    "workflow_id": "wf-pqr-456",
    "state": "ESCALATED",
    "escalation_target_role": "chief_finance_officer",
    "approvals": [
      {
        "timestamp": "2025-12-27T11:00:00Z",
        "approver_role": "CFO",
        "escalated_by_user_id": "system",
        "action": "ESCALATED",
        "reason": "Approval timeout"
      }
    ]
  }
}
```

**Response (Already Escalated)**:
```json
{
  "status": "error",
  "error_code": "INVALID_STATE",
  "message": "Workflow already escalated",
  "details": {
    "workflow_id": "wf-pqr-456",
    "current_state": "ESCALATED"
  }
}
```

**Semantics**:
- Manual escalation (not automatic timeout-based)
- Workflow state becomes ESCALATED
- escalation_target_role now responsible for approval
- Async hooks invoked (fire-and-forget)
- Escalation cannot be reversed (no de-escalation)

---

## 3. SDK Error Codes & Semantics

### 3.1 Error Classification

| Code | HTTP | Meaning | Retriable |
|------|------|---------|-----------|
| `INVALID_REQUEST` | 400 | SDK validation failed (tenant_id, context, format) | NO |
| `UNAUTHORIZED` | 401 | Auth context invalid or missing | YES (refresh auth) |
| `FORBIDDEN` | 403 | Role not authorized for operation | NO |
| `NOT_FOUND` | 404 | Resource not found or tenant mismatch | NO |
| `CONFLICT` | 409 | Invalid state transition (e.g., can't approve non-PENDING) | NO |
| `INVALID_CONTEXT` | 400 | Context contains prohibited fields (PII) | NO |
| `NO_RULES_CONFIGURED` | 400 | No rules for decision_type in tenant | NO |
| `UNKNOWN_DECISION_TYPE` | 400 | decision_type not registered | NO |
| `RULE_EVALUATION_ERROR` | 500 | Internal rule evaluation failed | YES |
| `INTERNAL_ERROR` | 500 | Unexpected error in Core or CMS | YES |
| `SERVICE_UNAVAILABLE` | 503 | Core or CMS temporarily down | YES |

### 3.2 Retriable vs Non-Retriable

```typescript
const RETRIABLE_CODES = [
  "UNAUTHORIZED",  // Refresh token and retry
  "RULE_EVALUATION_ERROR",  // May be transient
  "INTERNAL_ERROR",  // Transient infrastructure issue
  "SERVICE_UNAVAILABLE"  // Temporary outage
];

const NON_RETRIABLE_CODES = [
  "INVALID_REQUEST",  // Fix request, don't retry
  "FORBIDDEN",  // Role issue, don't retry
  "NOT_FOUND",  // Resource doesn't exist
  "CONFLICT",  // State issue, don't retry
  "INVALID_CONTEXT",  // Remove PII, don't retry
  "NO_RULES_CONFIGURED",  // Configure rules, don't retry
  "UNKNOWN_DECISION_TYPE"  // Register type, don't retry
];

// SDK MUST recommend:
// - Retriable errors: exponential backoff (2s, 4s, 8s max 32s)
// - Non-retriable errors: fail fast, don't retry
```

### 3.3 Error Response Structure

```json
{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "Human-readable error message",
  "details": {
    "field": "tenant_id",
    "reason": "MISSING",
    "hint": "tenant_id must be provided in every request"
  },
  "request_id": "req-trace-abc-123",
  "retriable": false,
  "retry_after_seconds": null
}
```

---

## 4. SDK Tenant Isolation Enforcement

### 4.1 Every Request Must Carry tenant_id

```typescript
// ALL SDK methods signature pattern:
sdkMethod(
  // ... method-specific params
  tenant_id: string  // ALWAYS REQUIRED, ALWAYS LAST
)

// Examples:
createDecision(decision_type, context, tenant_id)  // ✅ CORRECT
getDecision(decision_id, tenant_id)  // ✅ CORRECT
approveWorkflow(workflow_id, approver_role, tenant_id)  // ✅ CORRECT

// Wrong:
createDecision(decision_type, context)  // ❌ MISSING tenant_id
approveWorkflow(workflow_id, approver_role)  // ❌ MISSING tenant_id
```

### 4.2 Tenant Ownership Validation

```typescript
// VALIDATION SEQUENCE FOR EVERY OPERATION:

class SDKValidator {
  validateTenantIsolation(request, auth_context) {
    // 1. tenant_id MUST be provided
    if (!request.tenant_id) {
      throw ERROR_400("tenant_id required");
    }

    // 2. tenant_id MUST match auth context
    if (auth_context.tenant_id !== request.tenant_id) {
      throw ERROR_403(
        "Tenant mismatch: request belongs to different tenant"
      );
    }

    // 3. All resource lookups MUST filter by tenant_id
    const resource = await core.getResource(resource_id, request.tenant_id);
    if (!resource || resource.tenant_id !== request.tenant_id) {
      throw ERROR_404("Resource not found or tenant mismatch");
    }

    // 4. Return validated resource
    return resource;
  }
}
```

### 4.3 Cross-Tenant Attack Prevention

```typescript
// Attack Pattern: Try to approve workflow from different tenant
{
  "workflow_id": "wf-pqr-456",  // Belongs to hotel-123
  "approver_role": "CFO",
  "tenant_id": "competitor-456"  // ❌ ATTACKER tries different tenant
}

// SDK Defense:
// 1. Check auth_context.tenant_id === request.tenant_id
// 2. Fetch workflow filtered by request.tenant_id
// 3. If workflow not found or tenant mismatch → ERROR_404
// 4. Do NOT return "workflow belongs to other tenant" message
//    (leaks information)
```

---

## 5. SDK Decision Immutability Enforcement

### 5.1 No Modifications Allowed

```typescript
// Attempt: Modify decision_outcome
PATCH /decisions/{decision_id}
{
  "outcome": "ALLOWED"  // ❌ FORBIDDEN
}

// SDK response:
{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "Decision is immutable. Cannot modify decision_outcome.",
  "details": {
    "field": "outcome",
    "reason": "IMMUTABLE"
  }
}

// Reason: Decisions are immutable per Layer 0 guarantee.
// Workflows can change state, but decision outcome never changes.
```

### 5.2 Decision Outcome Immutability Pattern

```typescript
// Create decision:
{
  "outcome": "REQUIRE_APPROVAL",
  "rule_matched": "correction_amount_15000_cfo",
  "approval_workflow_id": "wf-xyz"
}

// Later, workflow is approved:
Workflow state: PENDING_APPROVAL → APPROVED

// But decision remains:
{
  "outcome": "REQUIRE_APPROVAL",  // ← UNCHANGED
  "rule_matched": "correction_amount_15000_cfo",  // ← UNCHANGED
  "approval_workflow_id": "wf-xyz"  // ← UNCHANGED
}

// Decision outcome is FOREVER immutable.
// Only workflow state changes.
```

---

## 6. SDK Guard Rails (Explicit, Testable)

### GR-1: tenant_id Mandatory & Validated

```
IF request.tenant_id is missing or empty
THEN return ERROR_400("tenant_id required")

IF auth_context.tenant_id ≠ request.tenant_id
THEN return ERROR_403("Tenant mismatch")
```

### GR-2: Context Sanitization (No PII)

```
IF context contains [email, phone, ssn, password, account_code, secret]
THEN return ERROR_400("Prohibited fields: " + list)

ALLOWED in context:
- IDs (user_id, entity_id, org_id)
- Enums (status, role, category)
- Numeric thresholds (amounts, quantities)
- Booleans (flags)
- Timestamps (RFC3339)
```

### GR-3: Decision Type Validation

```
IF decision_type does NOT match ^[a-z_]+\.[a-z_]+\.[a-z_]+$
THEN return ERROR_400("Invalid format: {module}.{entity}.{action}")
```

### GR-4: Decision Immutability

```
IF request attempts to modify decision_outcome or rule_matched
THEN return ERROR_400("Decision is immutable")
```

### GR-5: Role-Based Approval (Not User-Based)

```
IF approveWorkflow request contains approved_by_user_id
THEN return ERROR_400("Invalid field: approved_by_user_id. SDK injects from auth context")

IF approver_role is not a string (e.g., user_id format)
THEN return ERROR_400("approver_role must be role identifier (string), not user_id")
```

### GR-6: Workflow State Validation

```
IF attempt to approve workflow NOT in PENDING_APPROVAL state
THEN return ERROR_409("Cannot approve. Current state: {state}")

IF attempt to escalate ESCALATED workflow
THEN return ERROR_409("Workflow already escalated")
```

### GR-7: Idempotency & Determinism

```
IF idempotency_key provided + same context
THEN return same decision_id (idempotent)

IF idempotency_key provided + different context
THEN return ERROR_409("Idempotency violation: key with different context")
```

### GR-8: Fail-Closed on Configuration Error

```
IF no rules configured for decision_type
THEN return error code NO_RULES_CONFIGURED
     do NOT attempt to guess outcome

IF decision_type not registered
THEN return error code UNKNOWN_DECISION_TYPE
     do NOT create fallback decision
```

---

## 7. SDK Does NOT Do

### ❌ SDK Does NOT Execute Rules
```
Rule evaluation happens in Core, not SDK.
SDK passes context to Core.
Core evaluates, returns outcome.
SDK returns outcome to application.
```

### ❌ SDK Does NOT Store User Identity
```
SDK does NOT store user_id, username, email.
SDK stores only user_id in decision.requester_user_id (for audit).
Application handles user lookup/resolution.
```

### ❌ SDK Does NOT Resolve Approver Users
```
SDK stores approver_role (string: "CFO", "manager").
Application adapter resolves role → user_id.
SDK does NOT call user service.
SDK does NOT know who "CFO" actually is.
```

### ❌ SDK Does NOT Invoke Extension Hooks
```
Extension hooks are invoked ASYNC by Core, not SDK.
Hooks are fire-and-forget, non-blocking.
SDK does NOT wait for hook completion.
SDK does NOT know hook results.
```

### ❌ SDK Does NOT Manage Rules
```
Rule CRUD is CMS-only, not SDK.
SDK reads rules (Core fetches from CMS).
SDK does NOT create, update, delete rules.
SDK does NOT validate rule syntax.
```

### ❌ SDK Does NOT Query Audit Logs
```
Audit log querying is CMS-only.
SDK can only query decisions (filtered by tenant).
SDK cannot query workflow approval history (except via getWorkflow).
SDK cannot access raw audit events.
```

---

## 8. SDK Configuration & Initialization

### 8.1 SDK Constructor

```typescript
const infra = new InfraSDK({
  core_url: "https://core.infra.internal",
  core_api_key: "sk_live_...",  // Issued by Infra

  tenant_id: "hotel-123",  // Set once, used in all requests

  timeout_ms: 10000,  // Default 10s
  max_retries: 3,  // For retriable errors
  retry_backoff_ms: 1000,  // Exponential starting point

  request_id_header: "X-Request-ID",  // For tracing

  // Optional: tracing/logging
  on_request: (method, path, body) => {},  // Hook before send
  on_response: (method, path, status, body) => {},  // Hook after response
  on_error: (method, path, error) => {}  // Hook on error
});
```

### 8.2 Auth Context Injection

```typescript
// SDK gets auth context from application at runtime:
const decision = await infra.createDecision(
  "accounting.journal_approval",
  context,
  "hotel-123",
  {
    auth_context: {
      user_id: "user-456",  // From JWT/session
      tenant_id: "hotel-123",  // Must match request.tenant_id
      roles: ["staff"]  // User's roles (for audit)
    }
  }
);

// Or via middleware:
infra.setAuthContext({
  user_id: "user-456",
  tenant_id: "hotel-123",
  roles: ["staff"]
});

// All subsequent calls use this auth context
const decision = await infra.createDecision(
  "accounting.journal_approval",
  context,
  "hotel-123"
);
```

---

## 9. SDK Transport & Protocol

### 9.1 HTTP Semantics

```typescript
// All SDK calls → HTTP calls to Core API:

createDecision()
  → POST /v1/decisions
     Request: { decision_type, context, tenant_id, idempotency_key }
     Response: { decision }
     Status: 200 (success) | 4xx/5xx (error)

getDecision(decision_id)
  → GET /v1/decisions/{decision_id}?tenant_id={tenant_id}
     Response: { decision }
     Status: 200 | 404 | 403

queryDecisions()
  → GET /v1/decisions?tenant_id={tenant_id}&filters=...
     Response: { decisions, pagination }
     Status: 200 | 400

approveWorkflow()
  → POST /v1/workflows/{workflow_id}/approve
     Request: { approver_role, tenant_id, comment }
     Response: { workflow }
     Status: 200 | 409 | 403

escalateWorkflow()
  → POST /v1/workflows/{workflow_id}/escalate
     Request: { tenant_id, reason }
     Response: { workflow }
     Status: 200 | 409
```

### 9.2 Headers & Tracing

```
Required Headers (SDK adds):
  Authorization: Bearer {api_key}
  X-Tenant-ID: {tenant_id}
  X-Request-ID: {uuid}  (for tracing)
  Content-Type: application/json
  User-Agent: infra-sdk/{version}

Optional Headers:
  X-Idempotency-Key: {uuid}  (for idempotency)
  X-Request-Timeout-Ms: {ms}  (override default)
```

---

## 10. SDK Testing & Validation

### 10.1 Testability: Each Guard Rail Must Be Testable

```typescript
// Test: tenant_id mandatory
test("SDK rejects createDecision without tenant_id", async () => {
  const response = await infra.createDecision(
    "accounting.journal_approval",
    { amount: 5000 },
    ""  // Missing tenant_id
  );

  expect(response.status).toBe("error");
  expect(response.error_code).toBe("INVALID_REQUEST");
  expect(response.details.field).toBe("tenant_id");
});

// Test: Context sanitization
test("SDK rejects context with email", async () => {
  const response = await infra.createDecision(
    "accounting.journal_approval",
    {
      amount: 5000,
      approver_email: "cfo@example.com"  // ❌ PII
    },
    "hotel-123"
  );

  expect(response.status).toBe("error");
  expect(response.error_code).toBe("INVALID_CONTEXT");
  expect(response.details.rejected_fields).toContain("approver_email");
});

// Test: Decision immutability
test("SDK rejects modification of decision_outcome", async () => {
  const decision = await infra.createDecision(...);

  // SDK does NOT expose PATCH method for decisions
  // Would be test of Core API, not SDK
  expect(() => {
    infra.updateDecision(decision.decision_id, {
      outcome: "ALLOWED"
    });
  }).toThrow("Method not supported");
});

// Test: Role-based approval
test("SDK rejects approved_by_user_id in request", async () => {
  const response = await infra.approveWorkflow(
    "wf-abc",
    "CFO",
    "hotel-123",
    {
      approved_by_user_id: "user-123"  // ❌ SDK injects from auth
    }
  );

  expect(response.status).toBe("error");
  expect(response.error_code).toBe("INVALID_REQUEST");
  expect(response.details.field).toBe("approved_by_user_id");
});

// Test: Fail-closed on no rules
test("SDK handles NO_RULES_CONFIGURED gracefully", async () => {
  const response = await infra.createDecision(
    "unknown.decision_type",
    { context: true },
    "hotel-123"
  );

  expect(response.status).toBe("error");
  expect(response.error_code).toBe("UNKNOWN_DECISION_TYPE");
});
```

---

## 11. SDK Method Summary Table

| Method | Endpoint | HTTP | Request | Response | Idempotent |
|--------|----------|------|---------|----------|-----------|
| createDecision | /v1/decisions | POST | decision_type, context, tenant_id, idempotency_key? | Decision | Yes (key) |
| getDecision | /v1/decisions/{id} | GET | decision_id, tenant_id | Decision | Yes |
| queryDecisions | /v1/decisions | GET | tenant_id, filters? | Decision[] + pagination | Yes |
| getWorkflow | /v1/workflows/{id} | GET | workflow_id, tenant_id | Workflow | Yes |
| approveWorkflow | /v1/workflows/{id}/approve | POST | workflow_id, approver_role, tenant_id, comment? | Workflow | Yes |
| rejectWorkflow | /v1/workflows/{id}/reject | POST | workflow_id, approver_role, tenant_id, reason? | Workflow | Yes |
| delegateWorkflow | /v1/workflows/{id}/delegate | POST | workflow_id, approver_role, delegated_to_user_id, tenant_id, reason? | Workflow | No |
| escalateWorkflow | /v1/workflows/{id}/escalate | POST | workflow_id, tenant_id, reason? | Workflow | Yes |

---

## Summary: SDK Contracts are Layer 0 Enforcement Points

✅ **tenant_id** mandatory & validated in every request
✅ **Context sanitization** (no PII) enforced before transmission
✅ **Decision immutability** enforced (no modifications)
✅ **Role-based approval** (not user-based) enforced
✅ **Fail-closed** on configuration errors
✅ **Guard rails** explicit & testable (8 guard rails)
✅ **Error codes** clearly classified (retriable vs non-retriable)
✅ **Tenant isolation** validation at every boundary

**Status**: Ready for review
**Next**: Await user feedback before locking
