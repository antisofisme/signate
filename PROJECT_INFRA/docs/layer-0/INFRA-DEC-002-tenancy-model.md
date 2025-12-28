# INFRA-DEC-002: Tenancy Model & Isolation Boundaries

**VERSION**: Layer 0 DRAFT
**STATUS**: LOCKED (with revisions: organization_name metadata, entity ownership to adapter)
**DATE**: 2025-12-27

---

## Tenant Definition

A **Tenant** is an independent organizational boundary within Infra.
Each tenant has:
- Isolated decision space (rules, workflows, audit logs)
- Isolated data (context, decisions are NOT shared across tenants)
- Independent rule configuration
- Separate approval chains

```
Tenant {
  tenant_id: string              // UUID or slug (e.g., "hotel-123", "supplier-456")
  tenant_type: "buyer" | "supplier" | "internal"
  organization_name: string      // Metadata non-logical (display only)

  // Isolation markers
  rules_namespace: string        // Rules are tenant-scoped
  audit_log_partition: string    // Decisions logged separately

  created_at: timestamp
  status: "ACTIVE" | "SUSPENDED" | "ARCHIVED"
}
```

**PRINCIPLE**: A user of Tenant A CANNOT see, query, or influence decisions of Tenant B.

---

## organization_name as Metadata Non-Logical (CLARIFIED)

```typescript
Tenant {
  tenant_id: string              // ← Used in ALL logic (filtering, partitioning)
  organization_name: string      // ← Metadata ONLY (for display/audit)
  tenant_type: "buyer" | "supplier" | "internal"

  status: "ACTIVE" | "SUSPENDED" | "ARCHIVED"
}
```

**CRITICAL DISTINCTION:**

```
LOGICAL (used in decision evaluation & data isolation):
  ✅ tenant_id
  ✅ status (ACTIVE/SUSPENDED/ARCHIVED)

NON-LOGICAL (metadata only):
  ❌ organization_name
  ❌ tenant_type
  ❌ created_at
  ❌ contact_email
```

**WHY?**
- organization_name can change without affecting logic
- Rule evaluation NEVER references organization_name
- Audit queries filter by tenant_id, NOT organization_name
- If organization_name is used in rule logic → DESIGN MISTAKE

**Code Guard Rail:**
```typescript
// WRONG: Do NOT do this
async function evaluateRule(rule: Rule, context: object, tenant: Tenant): Decision {
  if (tenant.organization_name === "critical-customer") {  // ❌ NO
    return { outcome: "ALLOWED" };
  }
}

// CORRECT: Use tenant_id or pass org attributes as context
async function evaluateRule(rule: Rule, context: object, tenant_id: string): Decision {
  // Only use tenant_id for isolation
  const rules = await getRulesByType(tenant_id, decision_type);
  // Rule evaluation uses context only, not tenant metadata
}
```

---

## Tenant Context (MANDATORY in every decision)

Every decision request MUST include tenant context:

```typescript
DecisionRequest {
  tenant_id: string              // MANDATORY. Which tenant is requesting?
  decision_type: string
  context: object

  // Optional but recommended
  source_system: string          // Which app/module called this (e.g., "accounting", "pms")
  request_id: string             // For tracing
}
```

**VALIDATION**:
```
IF tenant_id is missing OR null OR empty
THEN request REJECTED
     error: "tenant_id required"

IF tenant_id format invalid (not UUID/slug)
THEN request REJECTED
     error: "Invalid tenant_id format"

IF tenant_id doesn't exist in Infra
THEN request REJECTED
     error: "Tenant not found or inactive"
```

---

## Tenant Isolation Boundaries

### BOUNDARY 1: Rules are Tenant-Scoped

```
Rule storage:
  tenant_id="hotel-123":
    - accounting.journal_approval (v1.2)
    - pms.room_reassignment (v1.0)
    - ...

  tenant_id="supplier-456":
    - accounting.journal_approval (v1.0)  ← Different version!
    - procurement.po_approval (v1.5)

GUARANTEE:
  Tenant A's rule changes do NOT affect Tenant B.
  Each tenant can update rules independently.
  Version divergence is OK.
```

**GUARD RAIL: Tenant Rule Isolation**
```typescript
async function getRulesByType(tenant_id: string, decision_type: string): Rule[] {
  // STEP 1: Validate tenant exists
  const tenant = await tenantService.get(tenant_id);
  if (!tenant || tenant.status !== "ACTIVE") {
    throw TenantNotFoundError(tenant_id);
  }

  // STEP 2: Query rules for THIS tenant only
  const rules = await rulesDb.query({
    tenant_id: tenant_id,  // ← MANDATORY filter
    decision_type: decision_type
  });

  // STEP 3: Return (or empty if no rules)
  return rules || [];
}
```

---

### BOUNDARY 2: Audit Logs are Tenant-Scoped

```
Audit log partitioning:
  /audit/tenant-123/decisions/...
  /audit/tenant-456/decisions/...

GUARANTEE:
  A user of Tenant A querying audit logs ONLY sees Tenant A decisions.
  Cannot query Tenant B decisions (even with direct database access).

IMPLEMENTATION:
  Audit logs physically separated by tenant partition key.
```

**GUARD RAIL: Audit Query Isolation**
```typescript
async function queryDecisions(tenant_id: string, filters: object): Decision[] {
  // STEP 1: Validate requesting user's tenant
  const user_tenant = await getUserTenant(current_user_id);

  // STEP 2: Verify requested tenant matches user's tenant
  if (tenant_id !== user_tenant.id) {
    throw UnauthorizedError("Cannot query other tenant's decisions");
  }

  // STEP 3: Query only THIS tenant's decisions
  return await auditDb.query({
    tenant_id: tenant_id,  // ← MANDATORY, already validated
    ...filters
  });
}
```

---

### BOUNDARY 3: Workflows are Tenant-Scoped

```
Approval workflows:
  tenant_id="hotel-123":
    - workflow-abc (CFO approval for GL)
    - workflow-def (manager approval for room reassignment)

  tenant_id="supplier-456":
    - workflow-xyz (procurement team approval)

GUARANTEE:
  Approval chain of Tenant A uses Tenant A's approvers.
  When Tenant B approves something, it does NOT trigger Tenant A's workflow.
```

---

### BOUNDARY 4: Context is Tenant-Isolated (Strict)

```
Decision context MUST only reference entities within same tenant:

VALID context:
  {
    tenant_id: "hotel-123",
    room_id: "room-101",        ← Must belong to hotel-123
    current_status: "OCCUPIED"
  }

INVALID context:
  {
    tenant_id: "hotel-123",
    room_id: "room-999",        ← Belongs to supplier-456 ❌
    ...
  }

INVALID context:
  {
    tenant_id: "hotel-123",
    supplier_id: "supplier-456", ← Cross-tenant reference ❌
    ...
  }
```

---

## Entity Ownership Validation Delegated to Application Adapter (CRITICAL)

**PRINCIPLE**: Infra does NOT resolve entity ownership. That is APPLICATION responsibility.

```
Question: "Does room-101 belong to hotel-123?"

Answer: Infra DOES NOT answer this.
        Application (via adapter) answers this.
```

**Why?**
- Entity ownership rules vary per application (PMS, Inventory, Accounting, etc.)
- Infra is domain-agnostic → cannot know "is this room?"
- Performance: Infra should NOT query application database for ownership validation
- Trust boundary: Application provides context; Infra trusts it

**Flow:**

```
APPLICATION ADAPTER (e.g., Accounting Module):
  ├─ User requests: "Approve journal entry X"
  ├─ Application resolves: "Journal entry belongs to tenant-123"
  ├─ Application resolves: "Journal amount is 15000"
  ├─ Application builds context:
  │   {
  │     journal_entry_amount: 15000,
  │     journal_entry_type: "correction",
  │     requester_role: "staff"
  │   }
  └─ Application calls Infra:
      infra.decide({
        tenant_id: "hotel-123",  ← App asserts ownership
        decision_type: "accounting.journal_approval",
        context: {...}
      })

INFRA:
  ├─ Receives request
  ├─ Does NOT validate "is journal-X really in tenant-123?"
  ├─ Trusts tenant_id from application
  ├─ Evaluates rules
  └─ Returns decision

IF Application provides wrong tenant_id:
  → Infra returns decision for wrong tenant
  → Application is responsible for bug/security issue
  → Infra logs decision accurately (audit trail shows misuse)
```

**Code Pattern (Application Adapter):**

```typescript
// Application Module (e.g., Accounting Service)
async function approveJournalEntry(journal_id: string, user_id: string) {
  // STEP 1: Load journal entry (within application scope)
  const journal = await journalDb.get(journal_id);
  if (!journal) throw NotFoundError();

  // STEP 2: Verify ownership (application responsibility)
  const tenant_id = await getCurrentUserTenant(user_id);
  if (journal.tenant_id !== tenant_id) {
    throw UnauthorizedError("Journal not found");
  }

  // STEP 3: Build context (application knows what's relevant)
  const context = {
    journal_entry_amount: journal.amount,
    journal_entry_type: journal.type,
    requester_role: (await getUserRole(user_id)).role
  };

  // STEP 4: Call Infra (delegate decision to Infra)
  const decision = await infra.decide({
    tenant_id: tenant_id,  // ← App asserts ownership
    decision_type: "accounting.journal_approval",
    context: context
  });

  // STEP 5: Execute based on Infra decision
  if (decision.outcome === "ALLOWED") {
    await journalDb.update(journal_id, { status: "APPROVED" });
  } else if (decision.outcome === "DENIED") {
    throw ForbiddenError("Not allowed to approve");
  } else if (decision.outcome === "REQUIRE_APPROVAL") {
    await createApprovalWorkflow(journal_id, decision.workflow_id);
  }
}
```

**What Infra DOES NOT Do:**
```
❌ Query journal database to verify ownership
❌ Validate "is journal-X really in tenant-123?"
❌ Load entity details from application database
❌ Resolve which approver owns which entity
❌ Make assumptions about entity relationships
```

**What Infra DOES Do:**
```
✅ Trust tenant_id from application
✅ Evaluate rules against context
✅ Return decision
✅ Log decision with tenant_id (for audit)
✅ If misuse happens, audit trail shows it
```

**Guard Rail: Application Adapter Contract**

```typescript
interface ApplicationAdapter {
  /**
   * Validate entity belongs to tenant BEFORE calling Infra.
   * Infra will NOT validate this.
   *
   * Example:
   *   const room = await db.room.get(room_id);
   *   assert(room.tenant_id === tenant_id); // ← App validates
   *
   *   infra.decide({
   *     tenant_id: tenant_id,  // ← App asserts ownership
   *     context: { room_id, ... }
   *   });
   */
  buildContextWithOwnershipValidation(
    entity_id: string,
    tenant_id: string
  ): object;

  /**
   * Extract relevant context from entity.
   * Infra does NOT know what's "relevant" for your domain.
   */
  sanitizeEntityToContext(entity: any): object;

  /**
   * After Infra decision, execute in your domain.
   * Infra does NOT execute.
   */
  executeDecision(decision: Decision, entity_id: string): Promise<void>;
}
```

**Documentation for Application Developers:**

```
IMPORTANT: Entity Ownership Validation

Infra trusts that tenant_id in your request is correct.
YOU MUST validate entity ownership in YOUR application
BEFORE calling Infra.

Example (PMS - Room Reassignment):
  1. User requests: "Reassign room 101 to guest ABC"
  2. YOUR APP validates:
     - room_id "room-101" exists
     - room belongs to current user's tenant
  3. YOUR APP calls Infra:
     infra.decide({
       tenant_id: getCurrentTenant(),  // From user session
       decision_type: "pms.room_reassignment",
       context: { room_id: "room-101", ... }
     })
  4. Infra evaluates rules
  5. YOUR APP executes (creates new reservation, updates folio, etc.)

If you skip step 2, you may leak data across tenants.
That is YOUR responsibility, not Infra's.
```

---

## Context Propagation Flow (SDK → Core → Storage)

**STEP 1: SDK Receives Decision Request**
```
SDK client (e.g., accounting app):

  const decision = await infra.decide({
    tenant_id: getCurrentTenant(),           // From session/context
    decision_type: "accounting.journal_approval",
    context: {
      journal_entry_amount: 15000,
      journal_entry_type: "correction",
      requester_role: "staff"
    }
  });
```

**STEP 2: SDK Adds Metadata & Sends to Core**
```typescript
DecisionRequest {
  tenant_id: "hotel-123"                     // From app
  decision_type: "accounting.journal_approval"
  context: {
    journal_entry_amount: 15000,
    journal_entry_type: "correction",
    requester_role: "staff"
  },

  // SDK-added metadata
  sdk_version: "1.2.0",
  sdk_language: "python",
  request_id: "req-abc123",
  timestamp_sent: 2025-12-27T10:30:00Z
}
```

**STEP 3: Core Validates Tenant & Context**
```typescript
async function validateRequest(req: DecisionRequest): void {
  // Validation 1: tenant_id exists and active
  const tenant = await tenantService.get(req.tenant_id);
  if (!tenant) throw TenantNotFoundError();

  // Validation 2: context is not empty
  if (!req.context || Object.keys(req.context).isEmpty()) {
    throw EmptyContextError();
  }

  // Validation 3: no sensitive data in context
  await validateContextSanitization(req.context);
}
```

**STEP 4: Core Evaluates Rules (Tenant-Scoped)**
```typescript
async function evaluateDecision(req: DecisionRequest): Decision {
  // Rule query is automatically tenant-scoped
  const rules = await getRulesByType(req.tenant_id, req.decision_type);

  // Rule evaluation (first-match-wins, single rule)
  for (const rule of rules) {
    if (rule.condition.evaluate(req.context)) {
      return {
        decision_id: uuid(),
        tenant_id: req.tenant_id,
        rule_matched: rule.name,
        outcome: rule.action
      };
    }
  }

  // No rule matched → fail-closed
  return {
    decision_id: uuid(),
    tenant_id: req.tenant_id,
    rule_matched: null,
    outcome: "DENIED"
  };
}
```

**STEP 5: Core Stores Decision (Tenant-Partitioned)**
```typescript
async function storeDecision(decision: Decision): void {
  // Store in tenant-partitioned audit log
  await auditDb.insert({
    partition_key: decision.tenant_id,  // ← Partition by tenant
    decision_id: decision.decision_id,
    decision_type: decision.decision_type,
    outcome: decision.outcome,
    rule_matched: decision.rule_matched,
    context_hash: hash(sanitize(decision.context)),  // Sanitized context
    timestamp: now()
  });
}
```

**STEP 6: Core Returns Decision to SDK**
```typescript
DecisionResponse {
  decision_id: "dec-xyz789",
  outcome: "REQUIRE_APPROVAL",
  rule_matched: "correction_amount_15000_cfo",
  workflow_id: "wf-123",
  timestamp: 2025-12-27T10:30:00.150Z,
  execution_time_ms: 42
}
```

**STEP 7: SDK Executes Based on Outcome**
```
IF outcome = "ALLOWED":
  → Proceed with operation (journal entry posts)

IF outcome = "DENIED":
  → Reject operation (show user "not allowed")

IF outcome = "REQUIRE_APPROVAL":
  → Create approval workflow (store workflow_id in app)
  → Wait for approval notification from Infra
```

---

## Cross-Tenant Scenarios (CRITICAL)

### Scenario 1: Supplier → Buyer Event (Procurement)

```
Context:
  Supplier Tenant (tenant_id="supplier-456") creates PO approval decision
  Buyer Tenant (tenant_id="hotel-123") receives PO via event

Question: Can Supplier's decision affect Buyer's decision?

Answer: NO. Completely separate.

Flow:
  SUPPLIER SIDE:
    decision_type: "procurement.po_approval"
    tenant_id: "supplier-456"
    context: { vendor_id: "...", po_amount: 50000, ... }
    → rule evaluation in supplier's rule namespace
    → outcome: ALLOWED (based on supplier's rules)
    → stored in supplier's audit log

  BUYER SIDE:
    event received: "PO.Received.v1" from supplier-456
    decision_type: "procurement.po_receipt_allowed"
    tenant_id: "hotel-123"
    context: { supplier_id: "supplier-456", po_amount: 50000, ... }
    → rule evaluation in BUYER's rule namespace (different rules!)
    → outcome: REQUIRE_APPROVAL (based on BUYER's rules)
    → stored in BUYER's audit log

CRITICAL: Supplier's ALLOWED does NOT automatically mean Buyer's ALLOWED.
Each tenant evaluates independently.
```

---

### Scenario 2: Multi-Tenant Approval Chain (Same Organization)

```
Context:
  Hotel (tenant-123) with Accounting, PMS, Inventory modules
  All modules are within SAME tenant

Question: Can approval from PMS trigger Accounting rule?

Answer: YES, but through explicit approval delegation, not automatic.

Flow:
  PMS Module decides: "room_reassignment requires manager approval"
  → Creates workflow in tenant-123
  → Manager approves in PMS

  Accounting Module decides: "journal_entry requires CFO approval"
  → Separate workflow in tenant-123
  → CFO approves in Accounting

THESE ARE INDEPENDENT.
PMS manager ≠ CFO. Different approval chains, same tenant.

IF Accounting wants to know "has PMS approval been given?":
  → Query Infra decision history for PMS approval decision
  → Check if approved
  → NOT automatic, explicit query needed
```

---

### Scenario 3: Invalid Cross-Tenant Context (SECURITY)

```
ATTACK SCENARIO:
  Attacker (tenant="attacker-999") tries to request:
    decision_type: "accounting.journal_approval"
    tenant_id: "hotel-123"   ← Different tenant!
    context: { ... }

GUARD RAIL:
  IF request_user_tenant ≠ requested_tenant_id
  THEN request REJECTED
       logged as SECURITY_VIOLATION

IMPLEMENTATION:
  async function checkTenantAuthorization(
    user: User,
    requested_tenant_id: string
  ): void {
    const user_tenant = await getUserTenant(user.id);

    if (user_tenant.id !== requested_tenant_id) {
      throw UnauthorizedError(
        `User belongs to ${user_tenant.id}, ` +
        `cannot request decision for ${requested_tenant_id}`
      );
    }
  }
```

---

## Tenant Isolation Guard Rails (LOCKED)

**GR-TEN-1: Every decision MUST have tenant_id**
```
IF decision.tenant_id is null/missing/empty
THEN decision REJECTED
     logged as SECURITY_EVENT
```

**GR-TEN-2: Rules are queried with tenant_id filter**
```
IF getRules() called WITHOUT tenant_id
THEN error thrown, no rules returned
```

**GR-TEN-3: Context entities validation delegated to application**
```
IF application provides wrong tenant_id for entity
THEN application is responsible for bug/security issue
Infra logs decision with provided tenant_id (audit trail shows misuse)
```

**GR-TEN-4: Audit logs are tenant-partitioned**
```
IF audit query without tenant_id filter
THEN error thrown, no logs returned
```

**GR-TEN-5: Workflow approval is tenant-scoped**
```
IF approval request from user of different tenant
THEN approval REJECTED
     logged as SECURITY_EVENT
```

**GR-TEN-6: Tenant context propagation mandatory**
```
IF SDK doesn't send tenant_id
THEN request REJECTED
     error: "tenant_id required in all requests"
```

---

## Tenant Lifecycle

**Tenant Creation:**
```
POST /infra/tenants
{
  tenant_id: "hotel-123",
  organization_name: "Sunrise Hotel",
  tenant_type: "buyer"
}

Response:
  Tenant created with status="ACTIVE"
  Empty rule namespace (no rules yet)
  Audit log partition created
```

**Tenant Suspension:**
```
PUT /infra/tenants/{tenant_id}/status
{
  status: "SUSPENDED"
}

Effect:
  - New decision requests REJECTED
  - Existing decisions NOT deleted (immutable)
  - Audit logs still queryable (read-only)
  - Rules not evaluated
```

**Tenant Archival:**
```
PUT /infra/tenants/{tenant_id}/status
{
  status: "ARCHIVED"
}

Effect:
  - All operations REJECTED
  - Data retained for compliance
  - Cannot be reactivated
```

---

## Checklist: Tenancy Model LOCKED

- ✅ Every decision includes tenant_id (mandatory)
- ✅ Rules are tenant-scoped (no cross-tenant rule sharing)
- ✅ Audit logs are tenant-partitioned (physical separation)
- ✅ organization_name is metadata, NOT logical
- ✅ Entity ownership validation delegated to application
- ✅ Workflows are tenant-scoped (approvers in same tenant)
- ✅ Cross-tenant scenarios are independent (no automatic propagation)
- ✅ 6 Guard Rails explicitly defined
- ✅ Tenant context propagation flow (SDK → Core → Storage)
- ✅ Fail-closed behavior on tenant mismatch
- ✅ Security violations logged explicitly
- ✅ Trust but audit approach (application responsible for context)
