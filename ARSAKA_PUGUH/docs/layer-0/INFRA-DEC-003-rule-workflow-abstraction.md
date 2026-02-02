# INFRA-DEC-003: Rule & Workflow Abstraction (Domain-Agnostic)

**VERSION**: Layer 0 BASELINE
**STATUS**: LOCKED (with 4 tightening: explicit rule order, role-only approvers, async hooks, depth limit rationale)
**DATE**: 2025-12-27

---

## Rule Definition & Structure

A **Rule** adalah declarative statement yang maps context → outcome.

```typescript
Rule {
  id: string                          // Unique within tenant
  rule_name: string                   // Human-readable (e.g., "critical_vendor_50k_allowed")
  tenant_id: string                   // Tenant-scoped
  decision_type: string               // Which decision type uses this rule

  description: string                 // Purpose, not executable

  condition: object                   // WHAT to match
  action: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"  // THEN what

  approval_config?: {                 // If action = REQUIRE_APPROVAL
    approver_roles: string[],         // Role identifiers only (e.g., "CFO", "inventory_manager")
    escalation_timeout_hours: number,
    escalation_target: string         // Role identifier for escalation
  }

  version: string                     // For rule versioning (v1.0, v1.1, etc.)
  created_at: timestamp
  updated_at: timestamp
  created_by: string
  status: "ACTIVE" | "DRAFT" | "DEPRECATED"
}
```

**CRITICAL**: Rule is CONFIGURATION, not CODE.
- Non-technical users (operators, business analysts) configure rules via CMS
- NO coding required
- Form-based, declarative syntax

---

## Rule Evaluation Order: Explicit List (NOT Priority Field)

**TIGHTENING 1: No `priority` field. Order by explicit list.**

```typescript
RuleSet {
  decision_type: "accounting.journal_approval"
  tenant_id: "hotel-123"
  rules: [
    "correction_amount_15000_cfo",    // ← Evaluated FIRST
    "correction_amount_5k_10k_manager", // ← Evaluated SECOND
    "correction_amount_below_5k"      // ← Evaluated THIRD
  ]
}
```

**WHY?**
- Priority fields can be accidentally reordered in UI (confusing)
- Explicit list is declarative & inspectable
- CMS shows evaluation order as drag-and-drop list (visual, not numeric)
- First-match-wins is CLEARER with explicit list order

**Implementation:**
```typescript
async function evaluateDecision(tenant_id: string, decision_type: string, context: object): Decision {
  // Get explicit rule list (ordered)
  const ruleList = await getRuleList(tenant_id, decision_type);

  // Evaluate in order (explicit, not by priority number)
  for (const rule_id of ruleList.rules) {  // ← Iteration order is rule list order
    const rule = await getRule(tenant_id, rule_id);

    if (rule.condition.evaluate(context)) {
      return {
        decision_id: uuid(),
        rule_matched: rule.rule_name,
        outcome: rule.action
      };
    }
  }

  // No match → fail-closed
  return { outcome: "DENIED" };
}
```

**CMS Visualization:**
```
Rule Order for "accounting.journal_approval":

┌─ correction_amount_15000_cfo [⬆️ ⬇️]
├─ correction_amount_5k_10k_manager [⬆️ ⬇️]
└─ correction_amount_below_5k [⬆️ ⬇️]

[Drag to reorder]
```

---

## Rule Condition: Deterministic & Simple (V1)

Conditions in V1 are SIMPLE & DETERMINISTIC (no aggregations, ML, or side effects).

**Supported Condition Types:**

```
TYPE 1: Numeric Comparison
  { field: "amount", operator: ">", value: 10000 }
  { field: "stock", operator: "<=", value: 100 }
  Operators: > | >= | < | <= | == | !=

TYPE 2: String Matching
  { field: "status", operator: "==", value: "LOCKED" }
  { field: "vendor_category", operator: "IN", values: ["critical", "strategic"] }
  Operators: == | != | IN | NOT_IN

TYPE 3: Boolean
  { field: "is_locked", operator: "==", value: true }
  Operators: == | !=

TYPE 4: Compound (AND / OR)
  {
    AND: [
      { field: "amount", operator: ">", value: 10000 },
      { field: "type", operator: "==", value: "correction" }
    ]
  }

  {
    OR: [
      { field: "status", operator: "==", value: "SUSPENDED" },
      { field: "vendor_payment_history", operator: "==", value: "bad" }
    ]
  }

Nesting allowed (depth limit: 3 levels - see rationale below).
```

**NOT Allowed in V1:**
```
❌ Aggregation (sum, avg, count, group by)
❌ Time-series logic (compare with historical data)
❌ Cross-entity logic (join with other entities)
❌ Math operations (calculate, formula)
❌ ML/AI models
❌ Side effects (call external API, write to database)
❌ Variables from outside context
```

---

## Condition Nesting Depth Limit: Max 3 Levels (TIGHTENING 4 - RATIONALE)

**RULE**: Condition nesting depth MUST NOT exceed 3 levels.

```
ALLOWED (depth 3):
  AND [
    { field: "amount", operator: ">", value: 10000 }
    OR [
      { field: "status", operator: "==", value: "LOCKED" }
      AND [
        { field: "role", operator: "==", value: "staff" }
        { field: "type", operator: "==", value: "correction" }
      ]  ← Depth: 3 ✅
    ]
  ]

NOT ALLOWED (depth 4):
  AND [
    OR [
      AND [
        OR [
          { ... }  ← Depth: 4 ❌
        ]
      ]
    ]
  ]
```

**RATIONALE (4 factors):**

### 1. **Comprehensibility**
- Rule creators (business analysts) must understand logic visually
- Depth > 3 becomes hard to reason about in human mind
- CMS UI can display depth 3 clearly in a single view
- Depth 4+ requires scrolling/nesting visualization = confusion
- **Goal**: operators can write rules without logic training

### 2. **Maintainability**
- Deep nesting = hard to modify later
- Changing one condition in depth 4 = high risk of logic error (unintended scope change)
- Shallow rules = easier to review, update, debug
- **Goal**: future maintainers can confidently update rules

### 3. **Performance**
- Condition evaluation is tree-walk algorithm
- Depth 3 = max 3^3 = 27 nodes (balanced tree)
- Depth 5 = could have 3^5 = 243 nodes, evaluation slower
- Target: condition evaluation < 1ms per rule
- **Goal**: decisions stay under 100ms p95 SLA

### 4. **Risk Mitigation**
- Deep nesting = higher risk of misconfiguration bugs
- CMS validation: if depth > 3, reject with clear error message
- Encourages "shallow rules" philosophy = safer rules
- **Goal**: prevent subtle bugs in rule logic

**Implementation Guard Rail:**

```typescript
function validateConditionDepth(condition: object, maxDepth: number = 3, currentDepth: number = 0): boolean {
  if (currentDepth > maxDepth) {
    throw new Error(
      `Condition nesting too deep. Current: ${currentDepth}, Max: ${maxDepth}. ` +
      `Simplify by breaking into multiple rules. ` +
      `Example: Instead of 1 rule with AND[OR[AND[...]]], create 2 rules at depth 2.`
    );
  }

  if (condition.AND) {
    for (const subCondition of condition.AND) {
      validateConditionDepth(subCondition, maxDepth, currentDepth + 1);
    }
  } else if (condition.OR) {
    for (const subCondition of condition.OR) {
      validateConditionDepth(subCondition, maxDepth, currentDepth + 1);
    }
  }

  return true;
}

// CMS rule validation
async function saveRule(rule: Rule): void {
  // Validate condition depth BEFORE saving
  validateConditionDepth(rule.condition, 3);

  // If valid, save
  await rulesDb.insert(rule);
}
```

**CMS Error Feedback:**
```
CMS Form Error:
  ❌ "Condition too complex. Maximum nesting: 3 levels.
     Current nesting depth: 4.

     Suggestion: Break complex logic into multiple rules.
     Example:
       Rule A: IF (condition_1 AND condition_2) THEN REQUIRE_APPROVAL
       Rule B: IF (condition_3 OR condition_4) THEN REQUIRE_APPROVAL"
```

---

## Rule Action: Three Outcomes

```typescript
IF condition matches:
  THEN action = one of:
    1. "ALLOWED"
    2. "DENIED"
    3. "REQUIRE_APPROVAL"
```

**Action Examples from 5 Decisions:**

```yaml
Rule: correction_amount_15000_cfo
  IF: amount > 10000 AND type = "correction"
  THEN: action = "REQUIRE_APPROVAL"
    approver_roles: ["CFO"]
    escalation_timeout_hours: 24
    escalation_target: "chief_finance_officer"

Rule: period_closed_denied
  IF: period_status = "CLOSED"
  THEN: action = "DENIED"

Rule: occupied_frontdesk_denied
  IF: current_status = "OCCUPIED" AND requested_by_role = "front_desk"
  THEN: action = "DENIED"

Rule: outbound_below_threshold
  IF: movement_type = "outbound" AND (current_stock - movement_qty) < safety_threshold
  THEN: action = "REQUIRE_APPROVAL"
    approver_roles: ["inventory_manager"]
    escalation_timeout_hours: 8
    escalation_target: "warehouse_manager"

Rule: critical_vendor_50k_allowed
  IF: vendor_category = "critical" AND po_amount <= 50000
  THEN: action = "ALLOWED"
```

---

## Approvers: ROLE Identifiers Only (TIGHTENING 2 - CRITICAL)

**TIGHTENING 2: Approvers are ROLE identifiers, NOT user IDs.**

```typescript
approval_config: {
  approver_roles: string[],          // ← ROLE identifiers only
  // Example: ["CFO", "inventory_manager", "warehouse_manager"]
  // NOT: ["user_123", "user_456"]  ❌ WRONG
}
```

**PRINCIPLE**: Infra stores & manages ROLES, not users. User resolution is APPLICATION responsibility.

**Flow:**

```
Time T0: Rule created in Infra
  {
    rule_name: "correction_amount_15000_cfo",
    approval_config: {
      approver_roles: ["CFO"]  // ← Just role name
    }
  }

Time T1: Decision requires approval
  Infra creates Workflow:
    {
      current_approver: "CFO"  // ← Role, not user ID
    }

Time T1: Infra sends notification event
  Infra event:
    {
      event: "ApprovalRequired.v1",
      workflow_id: "wf-123",
      approver_role: "CFO"  // ← Role identifier
    }

Time T1: APPLICATION receives notification event
  Application's notification handler:
    ├─ Receives: approver_role = "CFO"
    ├─ Resolves: "Who is CFO in tenant-123?"
    │  → Query application database
    │  → Get actual user: "user_id_456"
    ├─ Sends notification to user_id_456
    └─ User gets: "You have pending approval..."

Time T2: CFO approves
  Application sends to Infra:
    {
      workflow_id: "wf-123",
      approver_role: "CFO",
      approved_by_user_id: "user_id_456"  // ← Application provides user context
    }
```

**Guard Rail: Role-Only Storage**

```typescript
// Infra stores roles, NOT users
Workflow {
  current_approver: string      // "CFO", "inventory_manager", etc. (role)
  approver_list: string[]       // ["CFO"], ["manager"], etc. (roles)

  // NOT:
  // current_approver_user_id: "user_123"  ❌ WRONG
}

// When storing approval decision, include user for audit but mark role as primary
ApprovalRecord {
  timestamp: timestamp
  approver_role: string         // ← Primary identifier ("CFO")
  approved_by_user_id?: string  // ← User context (optional, for audit)
  action: "APPROVED" | "REJECTED"
}
```

**Application Adapter Contract:**

```typescript
interface ApprovalAdapter {
  /**
   * Given approver_role + tenant_id, resolve actual user(s).
   *
   * Example:
   *   resolveApproverUser("CFO", "hotel-123")
   *   → "user_456"  (the person who is CFO in this hotel)
   */
  resolveApproverUser(
    approver_role: string,
    tenant_id: string
  ): Promise<string>;  // Returns user_id

  /**
   * When approval happens, log which user approved (for audit).
   * Role was already stored in Workflow.
   */
  recordApprovalUser(
    workflow_id: string,
    approved_by_user_id: string
  ): Promise<void>;
}
```

---

## Rule Configuration via CMS (Form-Based)

CMS MUST use form-based, not code-based configuration:

```
Form: Create Rule
┌─────────────────────────────────────────────────────┐
│ Rule Name: critical_vendor_50k_allowed              │
│ Tenant: hotel-123                                   │
│ Decision Type: procurement.po_approval_required     │
│ Status: ACTIVE                                      │
│                                                      │
│ Description:                                        │
│ [POs from critical vendors up to $50K auto-allow]   │
│                                                      │
│ CONDITION:                                          │
│ ┌──────────────────────────────────────────────────┐│
│ │ Match Type: AND                                  ││
│ │                                                   ││
│ │ Condition 1:                                     ││
│ │ Field: vendor_category  [dropdown]               ││
│ │ Operator: == [dropdown]                          ││
│ │ Value: critical [text/dropdown]                  ││
│ │                                                   ││
│ │ Condition 2:                                     ││
│ │ Field: po_amount [dropdown]                      ││
│ │ Operator: <= [dropdown]                          ││
│ │ Value: 50000 [numeric]                           ││
│ │                                                   ││
│ │ [+ADD MORE CONDITIONS]                           ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ ACTION:                                             │
│ ┌──────────────────────────────────────────────────┐│
│ │ Outcome: ALLOWED [dropdown]                      ││
│ │ (no further config needed for ALLOWED)           ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ [SAVE]  [PREVIEW]  [CANCEL]                         │
└─────────────────────────────────────────────────────┘

Form: Create Rule (REQUIRE_APPROVAL)
┌─────────────────────────────────────────────────────┐
│ Rule Name: correction_amount_15000_cfo              │
│ Tenant: hotel-123                                   │
│ Decision Type: accounting.journal_approval          │
│ Status: ACTIVE                                      │
│                                                      │
│ CONDITION: [as above]                              │
│                                                      │
│ ACTION:                                             │
│ ┌──────────────────────────────────────────────────┐│
│ │ Outcome: REQUIRE_APPROVAL [dropdown]             ││
│ │                                                   ││
│ │ Approver Roles: [multiple select]                ││
│ │   ✓ CFO                                          ││
│ │   ✓ Finance Director                            ││
│ │   ☐ Accounting Manager                          ││
│ │                                                   ││
│ │ Escalation Timeout: 24 [numeric] hours          ││
│ │ Escalation Target Role: chief_finance_officer   ││
│ │ [dropdown - role options]                         ││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ [SAVE]  [PREVIEW]  [CANCEL]                         │
└─────────────────────────────────────────────────────┘
```

---

## Workflow = Approval Chain (NOT Orchestration)

A **Workflow** in Infra is ONLY approval management, nothing more.

```
Workflow Scope (V1):
  ✅ Sequential approval (user → manager → CFO)
  ✅ Escalation after timeout
  ✅ Delegation (I can't approve, delegate to someone else)
  ✅ Approval history (who approved, when, comment)
  ✅ Notifications (approver gets alert)

Workflow NOT Scope (Never in Infra):
  ❌ Orchestration (invoke APIs, run jobs)
  ❌ Parallel approvals (voting, consensus)
  ❌ Complex routing (if A approved then B, else C)
  ❌ Compensations (undo previous approval)
  ❌ Task assignment (create tasks in separate system)
  ❌ Conditional workflows (depend on other decisions)
```

**WHY?** Domain logic stays in application. Infra is "boring approval, nothing else."

---

## Approval State Machine (V1)

```
DECISION OUTCOME = "REQUIRE_APPROVAL"
  │
  ├─ Workflow created with status = PENDING_APPROVAL
  │
  └─ Workflow state transitions:

     PENDING_APPROVAL
       │
       ├─ [Approver approves]
       │  └─ Workflow state = APPROVED
       │     └─ Application executes decision
       │
       ├─ [Approver rejects]
       │  └─ Workflow state = REJECTED
       │     └─ Application cancels decision
       │
       ├─ [Timeout escalation]
       │  └─ Escalation notification sent to escalation_target role
       │     Workflow state = ESCALATED
       │     (waiting for escalated approver)
       │
       └─ [Delegate to someone else]
          └─ Workflow state = DELEGATED_TO_X
             (waiting for delegated approver)

Final states:
  - APPROVED (decision proceeds)
  - REJECTED (decision cancelled)
  - CANCELLED (requester cancelled before approval)
```

**Workflow Object:**

```typescript
Workflow {
  id: string                          // UUID
  decision_id: string                 // Which decision triggered this
  tenant_id: string

  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "CANCELLED" | "ESCALATED" | "DELEGATED_TO_X"

  current_approver_role: string       // Role awaiting approval ("CFO", "manager", etc.)
  approver_role_list: string[]        // Original approval chain (roles)

  escalation_config: {
    escalation_timeout_hours: number
    escalation_target_role: string    // Role for escalation (e.g., "CFO")
    escalated_at?: timestamp
  }

  delegation?: {
    original_approver_role: string
    delegated_to_user_id: string      // Delegate to specific user
    delegated_at: timestamp
  }

  history: ApprovalRecord[]           // Audit trail
  created_at: timestamp
  created_by: string                  // User who requested approval
  decided_at?: timestamp
  decided_by_user_id?: string
}

ApprovalRecord {
  timestamp: timestamp
  approver_role: string               // Role that acted
  approver_user_id?: string           // User who acted (if known)
  action: "APPROVED" | "REJECTED" | "DELEGATED" | "ESCALATED"
  comment?: string
  previous_state: string
  new_state: string
}
```

---

## Extension Hooks: Async, Non-Blocking, Fire-and-Forget (TIGHTENING 3)

**TIGHTENING 3: Extension hooks are async, non-blocking, fire-and-forget.**

```typescript
interface ApprovalExtensionHooks {
  /**
   * Called AFTER workflow state is updated to APPROVED.
   * Async, non-blocking, fire-and-forget.
   *
   * ⚠️ If hook fails, it does NOT affect approval state.
   * ⚠️ Failures logged separately.
   * ⚠️ Infra does NOT wait for hook completion.
   */
  onApprovalCompleted?(
    workflow: Workflow,
    decision: Decision
  ): Promise<void>;

  /**
   * Called BEFORE notification is sent.
   * Async, non-blocking.
   * Returns enriched notification context.
   *
   * ⚠️ If hook fails, notification still sent (with default context).
   * ⚠️ Hook failures do NOT block notification.
   */
  enrichApprovalNotification?(
    workflow: Workflow,
    decision: Decision
  ): Promise<NotificationContext>;

  /**
   * Called AFTER escalation timeout triggers.
   * Async, non-blocking.
   *
   * ⚠️ If hook fails, escalation still proceeds (notification still sent).
   * ⚠️ Hook failures do NOT block escalation.
   */
  onEscalationTriggered?(
    workflow: Workflow,
    escalation_target_role: string
  ): Promise<void>;
}
```

**Implementation Pattern:**

```typescript
async function approveWorkflow(workflow_id: string, approver_role: string): void {
  // STEP 1: Update workflow state (SYNCHRONOUS, BLOCKING)
  await updateWorkflowState(workflow_id, {
    status: "APPROVED",
    approver_role: approver_role,
    decided_at: now()
  });

  // STEP 2: Return immediately to caller
  // Caller gets response: "Approval recorded"
  // Caller does NOT wait for hooks

  // STEP 3: Call hooks in BACKGROUND (async, non-blocking)
  // Do NOT await these in approval API response
  invokeHooksInBackground(workflow_id);  // Fire-and-forget
}

async function invokeHooksInBackground(workflow_id: string): void {
  try {
    const workflow = await getWorkflow(workflow_id);
    const decision = await getDecision(workflow.decision_id);
    const adapter = getApprovalAdapter(workflow.tenant_id);

    // Call hook 1 (fire-and-forget)
    if (adapter.onApprovalCompleted) {
      adapter.onApprovalCompleted(workflow, decision)
        .catch(error => {
          // Log failure, but do NOT re-throw
          // Hook failure does NOT affect approval
          logger.error("Hook onApprovalCompleted failed", {
            error,
            workflow_id,
            severity: "warning"  // Not critical
          });
        });
    }

  } catch (error) {
    // Log hook invocation failure (separate from approval)
    logger.error("Failed to invoke hooks", {
      error,
      workflow_id,
      severity: "warning"  // Not critical
    });
    // Do NOT propagate error to approver
  }
}
```

**Guarantees:**

```
✅ Hook failures do NOT affect approval state
✅ Hook failures do NOT affect notification sending
✅ Hook failures do NOT block API response
✅ Hook failures logged separately (for debugging)
✅ Hooks execute in background (best-effort)
✅ If hook takes 1 hour, approver still gets response immediately
✅ If hook crashes, approval is already persisted
```

**CMS Visibility:**

```
CMS: Workflow Details
┌──────────────────────────────────────────────┐
│ Workflow ID: wf-abc123                       │
│ Status: APPROVED ✅                          │
│ Approved by: CFO                             │
│ Approved at: 2025-12-27 10:30 UTC           │
│                                              │
│ HOOKS EXECUTED (background):                │
│ • onApprovalCompleted                       │
│   Status: PENDING (async, fire-and-forget) │
│                                              │
│ • enrichApprovalNotification                │
│   Status: COMPLETED ✅ (2025-12-27 10:30:05)│
│   Result: Notification sent to CFO          │
│                                              │
│ [RELOAD] to see updated hook status         │
└──────────────────────────────────────────────┘
```

---

## Workflow + Decision Relationship (CRITICAL)

```
One Decision can have AT MOST one Workflow.

Decision {
  id: "dec-123",
  outcome: "REQUIRE_APPROVAL",
  approval_workflow_id: "wf-456"
}

Workflow {
  id: "wf-456",
  decision_id: "dec-123",
  status: "PENDING_APPROVAL"
}

GUARANTEE:
  - If decision.outcome = "ALLOWED" → NO workflow
  - If decision.outcome = "DENIED" → NO workflow
  - If decision.outcome = "REQUIRE_APPROVAL" → EXACTLY one workflow
  - Workflow can change state, but decision.outcome NEVER changes
  - Decision is IMMUTABLE, workflow is MUTABLE (state only, not outcome)
```

---

## Rule Versioning & Testing

**Scenario: Rule Updated, Old Decision Unaffected**

```
Time T1: Rule v1.0 created
  Rule: "amount > 10000 → REQUIRE_APPROVAL"
  Decision D1 evaluated with v1.0 → outcome = REQUIRE_APPROVAL

Time T2: Rule updated to v1.1
  Rule: "amount > 20000 → REQUIRE_APPROVAL"  (threshold raised)

Time T3: New decision D2 evaluated
  Uses Rule v1.1 → amount = 15000 → outcome = ALLOWED (new threshold)

RESULT:
  D1: outcome = REQUIRE_APPROVAL (v1.0 applied)
  D2: outcome = ALLOWED (v1.1 applied)

  Old decisions NOT re-evaluated
  Audit trail shows which rule version was used
```

**CMS: Rule Simulation**

```
CMS Feature: "Test Rule Before Activating"

Form: Simulate Rule
┌──────────────────────────────────────────────┐
│ Rule Name: correction_amount_15000_cfo       │
│ Test Context:                                │
│                                              │
│ Field: journal_entry_amount                  │
│ Value: [15000]                               │
│                                              │
│ Field: journal_entry_type                    │
│ Value: [correction]                          │
│                                              │
│ [RUN SIMULATION]                             │
│                                              │
│ Result:                                      │
│ ✅ Rule matched!                             │
│ → Outcome: REQUIRE_APPROVAL                  │
│ → Approver Roles: ["CFO"]                    │
│ → Escalation Target: chief_finance_officer  │
│                                              │
│ [ACTIVATE RULE]                              │
└──────────────────────────────────────────────┘
```

---

## Guard Rails: Rule & Workflow (CRITICAL)

**GR-RUL-1: Rule condition MUST be deterministic**
```
IF rule condition has side effects (calls API, writes to DB)
THEN rule validation FAILS
     error: "Rule condition must be pure & deterministic"
```

**GR-RUL-2: Condition nesting depth MAX 3 levels**
```
IF condition depth > 3
THEN rule upload REJECTED
     error: "Condition too complex. Maximum nesting: 3 levels."
```

**GR-RUL-3: No rule can call another rule**
```
IF rule A references rule B
THEN validation FAILS
     error: "Rules cannot have dependencies. Use AND/OR conditions instead."
```

**GR-RUL-4: Approver roles are STRINGS, not user IDs**
```
IF approver_config contains user_id instead of role
THEN validation FAILS
     error: "Use role identifiers (e.g., 'CFO'), not user IDs"
```

**GR-RUL-5: Rule evaluation order is EXPLICIT list**
```
IF rule priority field present
THEN rejected as legacy format
     error: "Use explicit rule list ordering, not priority field"
```

**GR-WF-1: One decision = max one workflow**
```
IF attempt to create second workflow for same decision
THEN error: "Decision already has workflow"
```

**GR-WF-2: Workflow state is mutable, decision is immutable**
```
IF attempt to change decision.outcome
THEN error: "Cannot change decision outcome"
     (only workflow state can change)
```

**GR-WF-3: Approval can only be given by assigned approver role**
```
IF user with role X tries to approve but current_approver_role = role Y
THEN approval REJECTED
     error: "You do not have the approver role for this workflow"
```

**GR-WF-4: Extension hooks must be non-blocking**
```
IF hook result blocks approval API response
THEN hook integration FAILS code review
     error: "Hooks must be async, non-blocking, fire-and-forget"
```

---

## Checklist: Rule & Workflow Abstraction (LOCKED)

- ✅ Rule structure & form-based configuration
- ✅ Condition syntax (simple, deterministic, no aggregations)
- ✅ Condition nesting depth = 3 max (with rationale: comprehensibility, maintainability, performance, risk)
- ✅ Rule action (3 outcomes: ALLOWED, DENIED, REQUIRE_APPROVAL)
- ✅ Rule evaluation order = explicit list (no priority field)
- ✅ Approvers = role identifiers only (user resolution via adapter)
- ✅ Workflow = approval chain only (no orchestration)
- ✅ Approval state machine (PENDING → APPROVED/REJECTED/ESCALATED/DELEGATED)
- ✅ Extension hooks async, non-blocking, fire-and-forget (3 hooks: onApprovalCompleted, enrichNotification, onEscalation)
- ✅ Decision ↔ Workflow relationship (1:0 or 1:1, immutable outcome)
- ✅ Rule versioning & immutability
- ✅ Workflow simulation/testing in CMS
- ✅ Guard rails explicit (8 rules)
- ✅ CMS forms for rule configuration (no code)

---

**INFRA-DEC-003: LAYER 0 BASELINE - LOCKED**
