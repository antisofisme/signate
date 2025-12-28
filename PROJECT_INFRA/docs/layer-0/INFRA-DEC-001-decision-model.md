# INFRA-DEC-001: Decision Model Definition

**VERSION**: Layer 0 DRAFT
**STATUS**: LOCKED (with revisions: decision_type naming, single rule_matched, fail-closed)
**DATE**: 2025-12-27

---

## Decision Definition

```
DECISION = atomic authorization/permission query answered by Infra
```

A **Decision** adalah jawaban terhadap kontekstual pertanyaan bisnis,
yang dikembalikan oleh Infra berdasarkan rules yang dikonfigurasi.

**Structure:**
```
Decision {
  decision_id: string           // Unique identifier (uuid)
  decision_type: string         // e.g., "accounting.journal_approval"
  tenant_id: string             // Multi-tenant isolation
  requester_user_id: string     // Who asked for decision

  requested_at: timestamp       // When decision was requested
  decided_at: timestamp         // When decision was made

  context: object               // What Infra used to decide
  outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"

  rule_matched: string          // Single rule name (v1)
  rule_version: string          // Rule version used

  approval_workflow_id?: string // If outcome = REQUIRE_APPROVAL
}
```

---

## Decision Outcome (Only 3 States)

| Outcome | Meaning | Next Action |
|---------|---------|-------------|
| `ALLOWED` | No rule blocks this. Proceed. | SDK executes in app |
| `DENIED` | Rule explicitly forbids. Stop. | SDK rejects user request |
| `REQUIRE_APPROVAL` | Allowed but needs approval. | SDK creates approval workflow |

**CRITICAL**: Infra does NOT execute. Does NOT mutate state. Only decides.

---

## Decision Lifecycle

```
REQUESTED
    │
    ├─ Rule evaluation (sync, < 100ms)
    │
    ├─ Outcome determined: ALLOWED | DENIED | REQUIRE_APPROVAL
    │
    ├─ If ALLOWED or DENIED:
    │  └─ Decision COMPLETE (immutable)
    │
    └─ If REQUIRE_APPROVAL:
       └─ Workflow INITIATED (enters approval state machine)
          ├─ PENDING_APPROVAL
          ├─ APPROVED | REJECTED
          └─ Decision COMPLETE (immutable)
```

**GUARANTEE**: Once decided, decision is immutable. Workflow can change state, but decision_outcome never changes.

---

## Decision Type Naming Convention (LOCKED)

```
Format: {module}.{entity}.{action}

Valid Examples:
  accounting.journal_approval
  accounting.period_posting
  pms.room_reassignment
  inventory.stock_movement
  procurement.po_approval

Rules:
  - lowercase only
  - snake_case components
  - max 3 parts (module.entity.action)
  - NO special characters
  - NO version suffix (versioning via rule_version, not decision_type)

Validation:
  IF decision_type does NOT match pattern ^[a-z_]+\.[a-z_]+\.[a-z_]+$
  THEN request REJECTED
       error: "Invalid decision_type format. Use {module}.{entity}.{action}"
```

---

## 5 Concrete Decision Examples

### Decision 1: Accounting Journal Approval

```yaml
Type: accounting.journal_approval

Context:
  journal_entry_amount: 15000        # numeric
  journal_entry_type: "correction"   # string
  requester_role: "staff"            # string
  approval_authority: "accounting_manager"

Rules:
  - IF amount > 10000 AND type = "correction"
    THEN REQUIRE_APPROVAL (authority: CFO)

  - IF amount > 5000 AND amount <= 10000 AND type = "correction"
    THEN REQUIRE_APPROVAL (authority: accounting_manager)

  - IF amount <= 5000
    THEN ALLOWED

Decision Flow:
  context → rule engine → match rule 1 (amount 15000 > 10000)
  → outcome = REQUIRE_APPROVAL (authority: CFO)
  → create approval workflow with CFO as approver
  → response returned immediately with workflow_id

Infra Stores:
  - decision_id, decision_type, tenant_id, requester_user_id
  - context (sanitized: amount only, no journal_entry_id or account codes)
  - rule_matched: "correction_amount_15000_cfo"
  - workflow_id (if applicable)
  - timestamps

Infra DOES NOT Store:
  - account codes, GL details, revenue amounts
  - requester name, email
  - full journal entry payload
```

### Decision 2: Accounting Period Lock

```yaml
Type: accounting.period_posting_allowed

Context:
  period_id: "2025-12"               # string
  current_date: 2025-12-28           # date
  period_status: "CLOSED"            # enum: OPEN | LOCKED | CLOSED

Rules:
  - IF period_status = "CLOSED"
    THEN DENIED

  - IF period_status = "LOCKED" AND requester_role NOT IN ["CFO", "Finance Director"]
    THEN DENIED

  - IF period_status = "LOCKED" AND requester_role IN ["CFO", "Finance Director"]
    THEN ALLOWED

  - IF period_status = "OPEN"
    THEN ALLOWED

Decision Flow:
  context → rule engine → match rule (period_status = CLOSED)
  → outcome = DENIED
  → response immediately (no workflow)

Infra Stores:
  - decision_id, period_id, requester_role, period_status
  - rule_matched: "period_closed_denied"
  - outcome: DENIED

Infra DOES NOT Store:
  - period transactions, GL entries
  - requester identity details
```

### Decision 3: PMS Room Reassignment

```yaml
Type: pms.room_reassignment_allowed

Context:
  room_id: "room-101"                # string
  current_reservation_id: "res-abc"  # string
  current_status: "OCCUPIED"         # enum: VACANT | OCCUPIED | IN_CHECKIN
  requested_by_role: "front_desk"    # string

Rules:
  - IF current_status = "OCCUPIED" AND requested_by_role NOT IN ["manager", "owner"]
    THEN DENIED

  - IF current_status = "OCCUPIED" AND requested_by_role IN ["manager", "owner"]
    THEN REQUIRE_APPROVAL (authority: manager)

  - IF current_status IN ["VACANT", "IN_CHECKIN"]
    THEN ALLOWED

Decision Flow:
  context → rule engine → match rule (OCCUPIED + front_desk role)
  → outcome = DENIED
  → response immediately

Infra Stores:
  - decision_id, room_id, current_status, requested_by_role
  - rule_matched: "occupied_frontdesk_denied"
  - outcome: DENIED

Infra DOES NOT Store:
  - guest names, reservation details
  - room rate or pricing
```

### Decision 4: Inventory Stock Movement

```yaml
Type: inventory.stock_movement_allowed

Context:
  sku: "ITEM-001"                    # string
  current_stock: 5                   # numeric
  safety_threshold: 10               # numeric
  movement_quantity: 3               # numeric
  movement_type: "outbound"          # enum: inbound | outbound

Rules:
  - IF movement_type = "outbound" AND (current_stock - movement_qty) < safety_threshold
    THEN REQUIRE_APPROVAL (authority: inventory_manager)

  - IF movement_type = "outbound" AND (current_stock - movement_qty) >= safety_threshold
    THEN ALLOWED

  - IF movement_type = "inbound"
    THEN ALLOWED

Decision Flow:
  context → rule engine
  → check: 5 - 3 = 2, which is < 10 (threshold)
  → match rule (below safety threshold)
  → outcome = REQUIRE_APPROVAL
  → create workflow with inventory_manager

Infra Stores:
  - decision_id, sku, current_stock, safety_threshold, movement_qty
  - rule_matched: "outbound_below_threshold"
  - workflow_id

Infra DOES NOT Store:
  - warehouse location, bin details
  - SKU full name or supplier info
  - full inventory transaction
```

### Decision 5: Procurement PO Approval

```yaml
Type: procurement.po_approval_required

Context:
  vendor_id: "vendor-xyz"            # string
  po_amount: 50000                   # numeric
  vendor_category: "critical"        # string
  vendor_payment_history: "good"     # enum: good | warning | bad

Rules:
  - IF vendor_category = "critical" AND po_amount > 100000
    THEN REQUIRE_APPROVAL (authority: CFO)

  - IF vendor_category = "critical" AND po_amount <= 100000 AND po_amount > 50000
    THEN REQUIRE_APPROVAL (authority: procurement_manager)

  - IF vendor_category = "critical" AND po_amount <= 50000
    THEN ALLOWED

  - IF vendor_category != "critical" AND po_amount > 200000
    THEN REQUIRE_APPROVAL (authority: CFO)

  - IF vendor_category != "critical" AND po_amount <= 200000
    THEN ALLOWED

  - IF vendor_payment_history = "bad"
    THEN DENIED

Decision Flow:
  context → rule engine
  → check vendor_category = "critical", amount = 50000
  → match rule (critical + amount <= 50000)
  → outcome = ALLOWED
  → response immediately

Infra Stores:
  - decision_id, vendor_id, po_amount, vendor_category
  - rule_matched: "critical_vendor_50k_allowed"
  - outcome: ALLOWED

Infra DOES NOT Store:
  - vendor financial details, contract terms
  - PO line items, pricing details
  - supplier relationship history
```

---

## Decision Input Sanitization

Context sent from SDK MUST be sanitized before stored in audit log:

```
ALLOWED in context:
  - IDs (user_id, entity_id, etc.)
  - Enum values (status, role, category)
  - Numeric thresholds (amounts, quantities)
  - Boolean flags
  - Timestamps

NOT ALLOWED in context:
  - PII (names, emails, phone numbers)
  - Full payloads (complete transaction data)
  - Sensitive strings (API keys, credentials)
  - Granular financial details (account codes, revenue amounts)
  - Personal data that can identify individuals

Redaction Rule:
  IF context_value contains ["email", "phone", "ssn", "account_code", "password"]
  THEN mask_or_reject(context_value)
```

---

## Decision Atomicity & Immutability

**GUARANTEE 1**: Decision outcome NEVER changes after decided.
```
decision.outcome = "ALLOWED"  (immutable, forever)
decision.outcome = "DENIED"   (immutable, forever)
decision.outcome = "REQUIRE_APPROVAL" with workflow (immutable)
```

**GUARANTEE 2**: If workflow changes state, decision_outcome stays same.
```
Initial Decision:
  outcome: "REQUIRE_APPROVAL"
  workflow_id: "wf-123"

Later, Workflow state changes:
  wf-123.state: PENDING → APPROVED

But:
  decision.outcome: "REQUIRE_APPROVAL" ← STILL THE SAME
  (only workflow state changed, not decision)
```

**GUARANTEE 3**: Rules evaluated at decision time. If rules change later, OLD decision is not re-evaluated.
```
Time T1: Decision made with Rule v1.0
         outcome = ALLOWED

Time T2: Rule updated to v1.1 (different logic)

T1 Decision: Still ALLOWED (Rule v1.0 applied)
New Decision: Uses Rule v1.1

Old decision is NEVER re-evaluated.
```

---

## Decision Response Time SLA

| Scenario | Target | P95 | Guarantee |
|----------|--------|-----|-----------|
| Simple rule match (ALLOWED/DENIED) | < 50ms | < 100ms | Best effort |
| REQUIRE_APPROVAL decision | < 50ms | < 100ms | Best effort |
| Workflow creation (if needed) | < 100ms | < 200ms | Best effort |

**CRITICAL**: Infra does NOT guarantee hard real-time. Response within tens of milliseconds is acceptable. If SDK needs response in < 5ms, that's NOT Infra's use case.

---

## rule_matched = Single Rule (V1 - LOCKED)

**CLARIFICATION**: In V1, `rule_matched` contains EXACTLY ONE rule (the first matching rule).

```typescript
Decision {
  rule_matched: string  // NOT array. Single rule only.
  rule_version: string  // Version of THAT rule
}

Example:
  rule_matched: "critical_vendor_50k_allowed"
  rule_version: "1.2"

NOT:
  rule_matched: ["rule_1", "rule_2", "rule_3"]  // ❌ V1 forbids this
```

**WHY?**
- Keep decision logic predictable & explainable
- "Which rule fired?" has single answer, not array of possibles
- Rule evaluation is FIRST-MATCH-WINS (deterministic)
- V2 can support multi-rule matching & scoring if needed

**Implementation**:
```
Rule evaluation algorithm (V1):
  FOR EACH rule IN config.rules (in order):
    IF rule.condition.evaluate(context) == true:
      RETURN {
        decision_id: uuid(),
        rule_matched: rule.name,
        rule_version: rule.version,
        outcome: rule.action,
        rule_evaluation_time_ms: elapsed
      }

  // No rule matched → fail-closed (below)
```

---

## Fail-Closed Behavior (CRITICAL - LOCKED)

**GUARD RAIL**: If NO rule matches, outcome = DENIED (fail-closed).

```typescript
Decision Outcome When No Rule Matches:

{
  decision_id: uuid(),
  outcome: "DENIED",
  rule_matched: null,
  rule_matched_reason: "NO_MATCHING_RULE",
  logged_as: "SECURITY_EVENT"  // Track in audit log
}
```

**Scenarios:**

| Scenario | Behavior | Outcome | Logged |
|----------|----------|---------|--------|
| Rule config missing | No rules defined | DENIED | SECURITY_EVENT |
| Rule config corrupted | Rules parse error | DENIED | SECURITY_EVENT |
| Unknown decision_type | No rules for type | DENIED | SECURITY_EVENT |
| All rules evaluated, none match | Normal evaluation | DENIED | DEBUG |
| Context incomplete | Cannot evaluate | DENIED | SECURITY_EVENT |

**Code:**
```typescript
async function evaluateDecision(decision_type: string, context: object): Decision {

  // STEP 1: Validate context exists
  if (!context || Object.keys(context).length === 0) {
    return {
      outcome: "DENIED",
      reason: "EMPTY_CONTEXT",
      logged_as: "SECURITY_EVENT"
    };
  }

  // STEP 2: Load rules for decision_type
  const rules = await rulesEngine.getRulesByType(decision_type);

  if (!rules || rules.length === 0) {
    return {
      outcome: "DENIED",
      reason: "NO_RULES_CONFIGURED",
      logged_as: "SECURITY_EVENT"
    };
  }

  // STEP 3: Evaluate rules (first match wins)
  for (const rule of rules) {
    try {
      const matches = rule.condition.evaluate(context);
      if (matches) {
        return {
          outcome: rule.action,  // ALLOWED | DENIED | REQUIRE_APPROVAL
          rule_matched: rule.name,
          rule_version: rule.version
        };
      }
    } catch (error) {
      // Rule evaluation error → fail-closed
      return {
        outcome: "DENIED",
        reason: "RULE_EVALUATION_ERROR",
        error_detail: error.message,
        logged_as: "SECURITY_EVENT"
      };
    }
  }

  // STEP 4: No rule matched → fail-closed
  return {
    outcome: "DENIED",
    reason: "NO_MATCHING_RULE",
    logged_as: "DEBUG"  // Less urgent, but still logged
  };
}
```

**Audit Trail:**
```
ALL scenarios that result in DENIED due to missing/unknown rule
MUST be logged with:
  - decision_id
  - decision_type
  - context (sanitized)
  - reason_code (NO_MATCHING_RULE, NO_RULES_CONFIGURED, etc.)
  - timestamp
  - tagged: "SECURITY_EVENT" atau "DEBUG"

CMS search MUST show:
  - Filter by reason_code
  - Alert if high frequency of "NO_MATCHING_RULE" → indicates misconfiguration
```

---

## Edge Cases & Guard Rails

**GR-1**: Unknown or missing rule → DENIED (fail-closed)

```
IF rule engine encounters unknown/missing rule
THEN decision outcome = DENIED (immediately)
     logged as SECURITY_EVENT
     no fallthrough to other rules ✅ CORRECT
```

**GR-2**: Rule evaluation order is deterministic
```
Rules are evaluated in config-defined order (not random).
First rule that matches → decision outcome determined.
Remaining rules are NOT evaluated.
```

**GR-3**: Circular rule dependency is forbidden
```
IF rule A references rule B, and rule B references rule A
THEN rule upload REJECTED
   error: "Circular rule dependency detected"
```

**GR-4**: Decision without context is invalid
```
IF context is null or empty object
THEN decision request REJECTED
   error: "Context required"
```

**GR-5**: Tenant context mismatch is DENIED (security)
```
IF decision.tenant_id != context.tenant_id
THEN decision is DENIED (logged as security violation)
   outcome: DENIED
   reason: "Tenant mismatch"
```

---

## Decision Query & Tracing (Explainability)

CMS MUST support querying decisions:

```
Query: List decisions for [tenant_id, decision_type, requester, date_range]
Output:
  - decision_id
  - outcome
  - rule_matched (which rule matched)
  - rule_version
  - requester
  - timestamp
  - if REQUIRE_APPROVAL: workflow status

Query: Explain decision [decision_id]
Output:
  - Rule evaluation steps (rule 1 matched? no. rule 2 matched? yes → ALLOWED)
  - Context used
  - Why this outcome
  - Audit trail (who reviewed if approval needed)
```

---

## Summary: Decision Model is LOCKED

- ✅ 3 outcomes only (ALLOWED, DENIED, REQUIRE_APPROVAL)
- ✅ Immutable after decided
- ✅ Rule version captured (for explainability)
- ✅ Context sanitized (no sensitive data)
- ✅ Atomicity guaranteed
- ✅ decision_type naming convention locked
- ✅ Single rule_matched (v1)
- ✅ Fail-closed behavior explicit
- ✅ Edge cases explicit
- ✅ SLA realistic
- ✅ 5 concrete examples defined
