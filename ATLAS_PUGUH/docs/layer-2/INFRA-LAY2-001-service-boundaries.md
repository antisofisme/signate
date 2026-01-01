# INFRA-LAY2-001: Service Boundaries & Responsibility Map

**VERSION**: Layer 2 DRAFT
**STATUS**: READY FOR LOCKING (3 clarifications applied)
**DATE**: 2025-12-27

---

## Overview

This document defines four services and their **exclusive responsibilities**.

**Core Principle**: Boundaries are hard. Services do NOT overlap, do NOT call each other outside critical path.

---

## 1. Service Definitions

### 1.1 Infra Core

**What it is**: The decision engine. Evaluates rules, makes decisions, manages workflows.

**Owns**:
- Rule evaluation (first-match-wins, deterministic)
- Decision immutability (outcome never changes)
- Workflow state machine (PENDING → APPROVED/REJECTED/ESCALATED/DELEGATED)
- Workflow state transitions (atomic, immutable)
- Tenant isolation enforcement (hard boundary at every operation)
- Guard rail enforcement (fail-closed, context validation)
- Event emission (immutable facts, append-only log)
- Audit trail recording (who did what, when)

**Does NOT own**:
- User identity management (does NOT know user names, emails, roles)
- Rule configuration/CRUD (CMS owns this)
- Business logic execution (Application owns this)
- Entity ownership validation (Application Adapter owns this)
- Approver notification (Application Adapter owns this)
- Event consumption (Applications own this)

**Deployment**: Internal service, not exposed to applications directly.

---

### 1.2 Infra CMS

**What it is**: The configuration & management plane. Rules, rule versioning, audit querying.

**Owns**:
- Rule CRUD (create, read, update, delete, version)
- Rule activation/deactivation (which version is live)
- Rule testing & simulation (before activation)
- Rule deployment workflows (development → staging → production)
- Tenant rule configuration (rules scoped by tenant)
- Audit log querying (historical decisions, approvals)
- Configuration audit trail (who changed rules, when)
- User access control (who can manage rules in CMS)

**Does NOT own**:
- Rule evaluation (Core owns this)
- Decision creation (Core owns this)
- Workflow state management (Core owns this)
- Business logic (Application owns this)
- User identity management (Application owns this)
- Event emission (Core owns this)

**Deployment**: Can be internal or SaaS. Not in critical decision path.

---

### 1.3 SDK

**What it is**: The application-facing entry point. Only way to create decisions and manage workflows.

**Owns**:
- Request validation (tenant_id, decision_type format, context shape)
- Context sanitization (removing PII before transmission)
- Auth context forwarding (opaque metadata only, does NOT assert identity)
- API contracts (request/response structures)
- Idempotency handling (deduplication by idempotency_key)
- Error classification (retriable vs non-retriable)
- Tenant isolation enforcement (tenant_id in every call)
- Decision immutability enforcement (reject modification attempts)
- Role-based approval enforcement (only roles, not user IDs)

**Does NOT own**:
- Rule evaluation (Core owns this)
- User identity resolution (Application Adapter owns this)
- Business logic (Application owns this)
- Entity ownership validation (Application Adapter owns this)
- Event consumption (Applications own this)
- User management (Application owns this)
- Auth assertion or validation (Core or Application owns this)

**Deployment**: Language-specific SDK (TypeScript, Python, Go, Java, etc.). Embedded in application.

**CLARIFICATION 1: Auth Context is Opaque Metadata**:
```
SDK receives auth context from application:
  {
    user_id: "user-456",        // From JWT/session
    tenant_id: "hotel-123",     // From JWT/session
    roles: ["staff"]            // From JWT/session
  }

SDK forwards auth context to Core as-is (opaque):
  - SDK does NOT validate user_id exists
  - SDK does NOT validate tenant_id matches JWT
  - SDK does NOT validate roles match user
  - SDK does NOT assert identity

Core receives auth context and decides:
  - Accept it as-is (trust application auth)
  - OR validate it (if Core has auth service)
  - OR ignore it (depends on deployment model)

SDK responsibility: Forward metadata exactly as received
Core responsibility: Trust or validate, depending on deployment
Application responsibility: Provide valid auth context

This prevents SDK from becoming an identity validator.
```

---

### 1.4 Application Adapter

**What it is**: The glue between Infra and the application. Handles what Infra does NOT own.

**Owns**:
- User identity resolution (role → actual user list)
- Entity ownership validation (entity → tenant verification)
- Approver notification sending (email, SMS, webhooks)
- Business logic execution (what happens after approval)
- Event consumption (subscribing to decision/workflow events)
- Retry logic (if approval needed, allow retry with modified context)
- Escalation handling (custom behavior on escalation)
- Error handling (what to do if decision is DENIED)

**Does NOT own**:
- Rule evaluation (Core owns this)
- Decision creation (Core owns this)
- Workflow state management (Core owns this)
- Rule configuration (CMS owns this)
- Tenant isolation (Core owns this)
- Request validation (SDK owns this)

**Deployment**: Part of the application codebase, not a separate service.

**CLARIFICATION 3: Retry Semantics = NEW Decision Only**:
```
Scenario: User requests operation, decision outcome = DENIED

WRONG (NOT retrying the same decision):
  1. Get decision-123 (outcome=DENIED)
  2. "Retry" decision-123 with modified context
  3. Expect different outcome

WHY WRONG:
  - Decisions are immutable (outcome never changes)
  - Cannot replay the same decision_id
  - Cannot modify decision after creation

CORRECT (Create NEW decision):
  1. Get decision-123 (outcome=DENIED)
  2. Create NEW decision with modified context
  3. Get decision-456 (new decision_id)
  4. New decision evaluates with new context
  5. Outcome may be different (new rules evaluation)

Example:
  User tries to approve $15,000 journal entry
    → Decision-1: outcome=REQUIRE_APPROVAL (CFO approval needed)

  User modifies request to $4,000
    → Create Decision-2 (new decision_id) with amount=4,000
    → Decision-2: outcome=ALLOWED (no approval needed)

  Decision-1 remains REQUIRE_APPROVAL (immutable, untouched)
  Decision-2 is new evaluation, new outcome

Application Adapter handles:
  1. Check decision.outcome
  2. If DENIED: ask user to modify context
  3. Create NEW decision with modified context (new SDK call)
  4. Handle new decision outcome
  5. Never attempts to "re-evaluate" existing decision

Key principle:
  Decisions are IMMUTABLE. Retries are NEW DECISIONS.
  Same decision_id + different outcome = IMPOSSIBLE.
```

---

## 2. Responsibility Matrix

| Responsibility | Core | CMS | SDK | Adapter |
|---|---|---|---|---|
| Rule evaluation | ✅ | ❌ | ❌ | ❌ |
| Decision creation | ✅ | ❌ | ❌ | ❌ |
| Workflow state mgmt | ✅ | ❌ | ❌ | ❌ |
| Rule CRUD | ❌ | ✅ | ❌ | ❌ |
| Rule activation | ❌ | ✅ | ❌ | ❌ |
| Request validation | ❌ | ❌ | ✅ | ❌ |
| Context sanitization | ❌ | ❌ | ✅ | ❌ |
| Tenant isolation | ✅ | ✅ | ✅ | ❌ |
| Auth context injection | ❌ | ❌ | ✅ | ❌ |
| User identity resolution | ❌ | ❌ | ❌ | ✅ |
| Entity ownership validation | ❌ | ❌ | ❌ | ✅ |
| Approver notification | ❌ | ❌ | ❌ | ✅ |
| Business logic execution | ❌ | ❌ | ❌ | ✅ |
| Event emission | ✅ | ❌ | ❌ | ❌ |
| Event consumption | ❌ | ❌ | ❌ | ✅ |
| Guard rail enforcement | ✅ | ✅ | ✅ | ❌ |
| Audit trail | ✅ | ✅ | ❌ | ❌ |

---

## 3. Critical Path: SDK → Core → SDK

**Definition**: The synchronous happy path for decision creation and workflow approval.

### 3.1 Decision Creation Critical Path

```
Step 1: Application calls SDK
  createDecision(decision_type, context, tenant_id)
  ↓

Step 2: SDK Validates
  - tenant_id present & non-empty
  - decision_type matches {module}.{entity}.{action}
  - context is non-empty object
  - Validate auth context (user_id, tenant_id match)
  ↓

Step 3: SDK Sanitizes Context
  - Remove PII (email, phone, ssn, password, etc.)
  - Keep only audit-safe fields (IDs, enums, numbers, booleans)
  ↓

Step 4: SDK Injects Auth Context
  - approved_by_user_id = auth.user_id (from JWT/session)
  - approver_role = auth.roles[0] (optional)
  ↓

Step 5: SDK Calls Core (HTTP POST)
  POST /v1/decisions
  {
    decision_type: string,
    context: object (sanitized),
    tenant_id: string,
    requester_user_id: string (from auth),
    idempotency_key?: string
  }
  ↓

Step 6: Core Validates Request
  - tenant_id non-empty
  - decision_type valid format
  - context non-empty
  - Verify tenant_id matches auth context (if Core has auth)
  ↓

Step 7: Core Fetches Rules
  - Load rules for (decision_type, tenant_id)
  - If no rules → fail-closed (DENIED)
  - If unknown decision_type → fail-closed (DENIED)
  ↓

Step 8: Core Evaluates Rules
  - Iterate rules in order (first-match-wins)
  - Evaluate condition against context
  - First match → outcome determined
  ↓

Step 9: Core Creates Decision
  - decision_id = uuid()
  - Store decision (immutable)
  - If outcome = REQUIRE_APPROVAL → create workflow
  ↓

Step 10: Core Emits Events (async, non-blocking)
  - decision.created
  - decision.allowed | decision.denied | decision.requires_approval
  - workflow.created (if approval needed)
  ↓

Step 11: Core Returns Decision
  HTTP 200
  {
    status: "success",
    decision: {
      decision_id: uuid,
      outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL",
      rule_matched: string,
      rule_version: string,
      approval_workflow_id?: string
    }
  }
  ↓

Step 12: SDK Returns Decision
  Promise resolves with decision
  ↓

Step 13: Application Handles Decision
  IF outcome = ALLOWED:
    Proceed with operation
  ELSE IF outcome = DENIED:
    Show error to user
  ELSE IF outcome = REQUIRE_APPROVAL:
    Show approval UI, with workflow_id
    Application Adapter handles approver notification
```

**SLA**: < 100ms (SDK + Core combined), p95 < 200ms

**Guarantees**:
- Synchronous (blocking)
- Idempotent (same idempotency_key = same decision_id)
- Immutable (decision never changes after this)
- Atomic (no partial states)

**CLARIFICATION 2: SDK Validation Errors vs Core DENIED Decisions**:
```
TWO DIFFERENT FAILURE MODES:

SDK Validation Error (400 Bad Request):
  - tenant_id missing → ERROR_400 (not a decision)
  - decision_type invalid format → ERROR_400 (not a decision)
  - context contains PII → ERROR_400 (not a decision)
  - context is empty → ERROR_400 (not a decision)
  - Request REJECTED before transmission to Core

  Example response:
  {
    status: "error",
    error_code: "INVALID_REQUEST",
    message: "context contains prohibited fields: email"
  }

  Application handles: Fix request and retry

Core DENIED Decision (200 Success):
  - No rules configured → status=success, error_code=NO_RULES_CONFIGURED
  - All rules evaluated, none match → outcome=DENIED (fail-closed)
  - Unknown decision_type → status=success, error_code=UNKNOWN_DECISION_TYPE

  Example response:
  {
    status: "success",
    decision: {
      decision_id: "dec-xyz",
      outcome: "DENIED",
      rule_matched: "period_closed_forbidden",
      rule_version: "2.0"
    }
  }

  Application handles: Show error to user (decision was made, result is NO)

KEY DISTINCTION:
  400 = Request failed (SDK job), fix and retry same logic
  200 = Decision succeeded (Core job), outcome is DENIED (final answer)
```

---

### 3.2 Workflow Approval Critical Path

```
Step 1: Approver (via UI) calls SDK
  approveWorkflow(workflow_id, approver_role, tenant_id, comment)
  ↓

Step 2: SDK Validates
  - tenant_id present
  - workflow_id valid UUID
  - approver_role non-empty string (role identifier)
  - Verify auth context tenant_id matches request
  ↓

Step 3: SDK Calls Core (HTTP POST)
  POST /v1/workflows/{workflow_id}/approve
  {
    approver_role: string,
    tenant_id: string,
    comment?: string,
    approved_by_user_id: string (from auth)
  }
  ↓

Step 4: Core Validates
  - Fetch workflow (filtered by tenant_id)
  - Verify workflow.state = PENDING_APPROVAL
  - Verify approver_role matches workflow.approver_role
  ↓

Step 5: Core Transitions State
  - workflow.state = PENDING_APPROVAL → APPROVED
  - Record approval action (immutable)
  ↓

Step 6: Core Emits Events (async, non-blocking)
  - workflow.approved
  - workflow.completed
  ↓

Step 7: Core Returns Updated Workflow
  HTTP 200
  {
    status: "success",
    workflow: {
      workflow_id: uuid,
      state: "APPROVED",
      approvals: [...]
    }
  }
  ↓

Step 8: SDK Returns Workflow
  Promise resolves
  ↓

Step 9: Application Handles Approval
  - Application Adapter consumes workflow.approved event
  - Application Adapter executes business logic
  - Application Adapter handles success/error
```

**SLA**: < 100ms (SDK + Core combined), p95 < 200ms

**Guarantees**:
- Synchronous (blocking)
- Idempotent (approving same workflow twice → same state, no error)
- Immutable (workflow state immutable after transition)

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION                                │
│  (Decision creation, approval handling, event consumption)      │
└──────────────┬──────────────────────────────┬──────────────────┘
               │                              │
          ┌────▼────┐                   ┌─────▼─────┐
          │   SDK   │                   │ Adapter   │
          │ (in-app)│                   │ (in-app)  │
          └────┬────┘                   └─────▲─────┘
               │                              │
      Validate │                              │ Event consumption
      Sanitize │                              │ User resolution
      Inject   │                              │ Entity validation
               │                              │ Notif sending
          ┌────▼──────────────────────────────┴─────┐
          │                                         │
          │           INFRA CORE                    │
          │  (Rule eval, Decision, Workflow)       │
          │                                         │
          │  - Rules (in Core, not app)            │
          │  - Decision creation                   │
          │  - Workflow state machine              │
          │  - Event emission                      │
          │  - Tenant isolation                    │
          │                                         │
          └──────────────────┬──────────────────────┘
                             │
                        ┌────▼───────────────┐
                        │   INFRA CMS        │
                        │ (Config & Audit)   │
                        │                    │
                        │ - Rule CRUD        │
                        │ - Rule activation  │
                        │ - Audit querying   │
                        │ - NOT in critical  │
                        │   path             │
                        └────────────────────┘

KEY FLOWS:
  Critical Path (SDK → Core):
    Application → SDK: createDecision()
    SDK → Core: POST /v1/decisions
    Core → SDK: Decision (outcome)
    SDK → Application: Decision

  Approval Path (SDK → Core):
    Approver → SDK: approveWorkflow()
    SDK → Core: POST /v1/workflows/{id}/approve
    Core → SDK: Updated Workflow
    SDK → Approver: Updated Workflow

  Async Event Path (Core → Adapter):
    Core emits: decision.created, workflow.approved, etc.
    Adapter consumes: handles notifications, business logic
    (NO blocking, NO waiting for adapter response)

  Config Path (CMS → Core, NOT in critical path):
    Admin → CMS: Update rule
    CMS → Core: Rule version pushed (async)
    Core loads rule: next decision uses new version
    (NOT triggered by SDK)
```

---

## 5. Service Boundaries (Hard Lines)

### 5.1 Core Boundary

**INSIDE Core**:
- Rule evaluation engine
- Decision creation & immutability
- Workflow state machine
- Tenant isolation checks
- Event emission (immutable log)
- Guard rail enforcement

**OUTSIDE Core** (never call into these):
- User management
- Business logic execution
- Entity ownership validation
- Approver notification
- Configuration changes (handled by CMS)
- External APIs

---

### 5.2 CMS Boundary

**INSIDE CMS**:
- Rule configuration (CRUD)
- Rule versioning
- Rule activation/deactivation
- Rule testing/simulation
- Audit log querying
- Configuration audit trail

**OUTSIDE CMS** (never call into these):
- Rule evaluation
- Decision creation
- Business logic
- User management
- Event emission

---

### 5.3 SDK Boundary

**INSIDE SDK**:
- Request validation
- Context sanitization
- Auth context injection
- Idempotency handling
- Decision/workflow querying
- Error classification

**OUTSIDE SDK** (never do this):
- Rule evaluation
- Business logic
- User identity resolution
- Entity ownership validation
- Event consumption (Application owns this)

---

### 5.4 Application Adapter Boundary

**INSIDE Adapter**:
- User identity resolution (role → users)
- Entity ownership validation
- Approver notification
- Business logic execution
- Event consumption
- Error handling & retry

**OUTSIDE Adapter** (never do this):
- Rule evaluation
- Decision creation
- Workflow state management
- Request validation
- Tenant isolation checks

---

## 6. Forbidden Couplings (Explicit Rejections)

| Coupling | Why Forbidden | Violation |
|----------|---------------|-----------|
| CMS calls Core rule eval | CMS is config, not eval | Separation of concerns |
| Core calls Adapter | Core has no knowledge of Adapter | Decoupling |
| SDK evaluates rules | Rule eval is Core's exclusive job | Centralization |
| App calls Core directly | SDK is only entry point | Bypass prevention |
| Infra manages user IDs | User mgmt is Application's job | Scope isolation |
| Core executes business logic | Core is decision only | Separation |
| Rules trigger API calls | Rules are declarative | No side effects |
| Adapter calls Core | Would break async semantics | Tight coupling |
| CMS directly modifies rules in Core | Rules go through versioning | No direct mutation |
| Infra resolves approver roles | Application Adapter does this | Scope isolation |

---

## 7. Deployment Boundary

### 7.1 Service Independence

**Core**:
- Deployed as: Internal service (behind VPC)
- Scaling: Independent (horizontal scaling based on decision volume)
- Upgrading: Can upgrade independently (backward compatible APIs)
- Database: Separate from CMS

**CMS**:
- Deployed as: Internal or SaaS
- Scaling: Independent (not in critical path, can be slower)
- Upgrading: Can upgrade independently
- Database: Separate from Core

**SDK**:
- Deployed as: Embedded in application (language-specific)
- Scaling: Scales with application
- Upgrading: Application controls upgrade (versioned)
- No separate database

**Adapter**:
- Deployed as: Part of application
- Scaling: Scales with application
- Upgrading: Application controls upgrade
- No separate service

### 7.2 Network Boundaries

```
┌────────────────────────────────────────────┐
│           APPLICATION TIER                 │
│  (SDK + Adapter, same deployment)          │
└────────────────────────────────────────────┘
                    │ HTTP
                    │
┌────────────────────────────────────────────┐
│          INFRA CORE TIER                   │
│  (Internal, behind VPC)                    │
└────────────────────────────────────────────┘
                    │ HTTP
                    │
┌────────────────────────────────────────────┐
│           INFRA CMS TIER                   │
│  (Internal or SaaS, not in critical path) │
└────────────────────────────────────────────┘

Network Boundaries:
  - Applications communicate with Core via HTTPS
  - Applications do NOT communicate with CMS (async only)
  - CMS communicates with Core (rule push, audit pull)
  - No direct app-to-app communication
  - All inter-service calls are HTTP (REST or gRPC)
```

---

## 8. Information Flow Across Boundaries

### 8.1 SDK → Core (Critical Path)

**SDK sends to Core**:
- `decision_type`: string (validated format)
- `context`: object (sanitized, no PII)
- `tenant_id`: string (mandatory)
- `requester_user_id`: string (from auth context)
- `idempotency_key`: string (optional, for dedup)

**Core returns to SDK**:
- `decision_id`: UUID
- `outcome`: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
- `rule_matched`: string (single rule name)
- `rule_version`: string
- `approval_workflow_id`: string (if approval needed)

**What SDK does NOT see**:
- Internal rule evaluation steps
- Why specific rule matched (only that it matched)
- User identities (not in response)
- Business context beyond decision

---

### 8.2 Core → Adapter (Async Event Path)

**Core emits (async, fire-and-forget)**:
- `decision.created`
- `workflow.approved`
- `workflow.rejected`
- `workflow.escalated`
- etc.

**Adapter receives and handles**:
- Resolve approver_role → actual users
- Send notifications
- Execute business logic
- Handle failures independently (no callback to Core)

**Guarantee**: Core does NOT wait for Adapter. Events are fire-and-forget.

---

### 8.3 CMS → Core (Config Push, NOT Critical Path)

**CMS sends to Core**:
- `rule_id`: string
- `decision_type`: string
- `rule_definition`: object (condition, action, version)
- `status`: "ACTIVE" | "DRAFT" | "DEPRECATED"

**Core loads and caches**:
- Rules indexed by (tenant_id, decision_type)
- New decisions use latest active rule version
- Old decisions keep rule version from their time

**What Core does NOT do**:
- Call back to CMS
- Validate rule syntax (CMS does this)
- Notify CMS of rule usage

---

## 9. Guard Rails at Service Boundaries

### GR-1: SDK Enforces tenant_id Mandatory

```
IF SDK call missing tenant_id:
  REJECT (400)
  do NOT call Core

IF SDK auth context tenant_id ≠ request tenant_id:
  REJECT (403)
  do NOT call Core
```

### GR-2: Core Enforces tenant_id on Every Operation

```
IF Core receives request without tenant_id:
  REJECT (400)

IF decision.tenant_id ≠ request.tenant_id:
  REJECT (404, no "tenant mismatch" message)

IF workflow.tenant_id ≠ request.tenant_id:
  REJECT (404, no "tenant mismatch" message)
```

### GR-3: Core Does NOT Call Adapter

```
Core MUST NOT call Adapter methods
Core MUST NOT wait for Adapter responses
Core emits events only (async, fire-and-forget)
```

### GR-4: SDK Does NOT Evaluate Rules

```
SDK MUST NOT load rules
SDK MUST NOT evaluate conditions
SDK MUST NOT determine outcome
Core is exclusive owner of rule evaluation
```

### GR-5: CMS Does NOT Evaluate Decisions

```
CMS rule testing is simulation only
CMS does NOT create real decisions
CMS does NOT call Core decision creation
```

### GR-6: Adapter Does NOT Call Core Directly

```
Adapter receives decisions via SDK (during approval)
Adapter consumes events (async)
Adapter MUST NOT make additional Core calls
Adapter MUST NOT trigger new decisions from events
```

### GR-7: No Circular Dependencies

```
Core → does NOT call SDK, CMS, Adapter
SDK → calls Core only (no back-calls to Adapter)
CMS → calls Core (rule push only), does NOT call SDK or Adapter
Adapter → consumes events, does NOT call Core or CMS

NO circular calls. Unidirectional except SDK ↔ Core (request-response).
```

### GR-8: Auth Context Does NOT Cross Boundaries

```
SDK injects auth context (user_id, tenant_id)
Auth context STAYS in request headers
Core reads auth context from headers
Core does NOT pass auth context to Adapter
Adapter gets user_id only from events (for audit)
```

---

## 10. Responsibility Summary Table

| Activity | Core | CMS | SDK | Adapter | Notes |
|----------|------|-----|-----|---------|-------|
| Validate request format | - | - | ✅ | - | tenant_id, decision_type |
| Sanitize context (remove PII) | - | - | ✅ | - | Before transmission |
| Load rules for decision | ✅ | - | - | - | Core responsibility |
| Evaluate rules (condition) | ✅ | - | - | - | First-match-wins |
| Determine outcome | ✅ | - | - | - | ALLOWED/DENIED/REQUIRE_APPROVAL |
| Create decision record | ✅ | - | - | - | Immutable after creation |
| Create workflow | ✅ | - | - | - | If outcome = REQUIRE_APPROVAL |
| Transition workflow state | ✅ | - | - | - | PENDING → APPROVED/REJECTED/etc |
| Emit events | ✅ | - | - | - | Async, immutable log |
| Consume events | - | - | - | ✅ | Handle notifications, business logic |
| Resolve approver role → users | - | - | - | ✅ | Adapter knows user service |
| Validate entity ownership | - | - | - | ✅ | Entity → tenant check |
| Send notifications | - | - | - | ✅ | Email, SMS, webhooks |
| Execute business logic | - | - | - | ✅ | After approval |
| Configure rules (CRUD) | - | ✅ | - | - | CMS UI |
| Activate rule version | - | ✅ | - | - | Push to Core |
| Test rule (simulation) | - | ✅ | - | - | Before activation |
| Query audit logs | - | ✅ | - | - | CMS UI |
| Manage access control | - | ✅ | - | - | CMS users, not Infra users |

---

## 11. Violation Detection (Guard Rails)

### How to Detect Service Boundary Violations

1. **Rule Evaluation Calls**:
   - ❌ SDK loading rule conditions
   - ❌ CMS calling rule evaluation
   - ❌ Application evaluating rules locally

2. **Core → Adapter Calls**:
   - ❌ Core invoking Adapter methods
   - ❌ Core sending approver notifications
   - ❌ Core executing business logic

3. **User Management in Core**:
   - ❌ Core storing user IDs with approvals (only for audit)
   - ❌ Core resolving role → user
   - ❌ Core querying user service

4. **Rule Mutations**:
   - ❌ CMS directly modifying Core rules
   - ❌ Core changing rules without CMS

5. **SDK Bypasses**:
   - ❌ Application calling Core directly
   - ❌ Adapter creating decisions without SDK

---

## Summary: Boundaries Are Hard

✅ Core: Rule evaluation, Decision creation, Workflow state, Event emission
✅ CMS: Rule configuration, Audit querying, NOT in critical path
✅ SDK: Request validation, Context sanitization, Entry point only
✅ Adapter: User resolution, Notifications, Business logic, Event consumption

❌ Core does NOT call Adapter
❌ SDK does NOT evaluate rules
❌ CMS does NOT determine outcomes
❌ Adapter does NOT call Core directly
❌ No circular dependencies
❌ No user management in Infra
❌ No business logic in Core

**Status**: Service Boundaries defined, ready for review.

**Next**: Await feedback, then lock, then move to Layer 2.2 (Critical Path Sequences) if needed.
