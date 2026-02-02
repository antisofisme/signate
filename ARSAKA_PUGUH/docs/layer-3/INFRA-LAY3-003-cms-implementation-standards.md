# INFRA-LAY3-003: CMS Implementation Standards

**VERSION**: Layer 3 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-28

---

## Overview

This document defines **implementation standards** for Infra CMS (Content Management System).

- **Scope**: Rule CRUD, rule activation, audit querying, rule versioning, archival management
- **Constraint**: CMS is NOT in critical decision path; all rule changes asynchronous
- **Source of Truth**: INFRA-DEC-003 (Rule & Workflow Abstraction), INFRA-LAY2-003 (Data Persistence)

**Key Principle**: CMS is **operational tool**, not decision engine. It manages rule configuration, not outcomes. Rule changes do NOT affect in-flight decisions (immutable).

---

## 1. Rule CRUD Standards

### 1.1 Create Rule

```
OPERATION: Create new rule for specific decision_type.

Request Schema:
{
  decision_type: string,              // e.g., "accounting.journal_approval"
  rule_name: string,                  // e.g., "high_amount_rule"
  description: string,                // for audit trail
  conditions: object,                 // condition definition
  action: {
    outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL",
    approval_config: object            // if outcome = REQUIRE_APPROVAL
  },
  extension_hooks: object[]           // async, non-blocking
}

Validation (CMS Side, before persistence):

VALIDATION 1: decision_type format
  - Pattern: ^[a-z0-9_]+\.[a-z0-9_]+\.[a-z0-9_]+$
  - Verify decision_type exists in Core (or allow any format)
  - Error: 400 "INVALID_DECISION_TYPE"

VALIDATION 2: rule_name format
  - Pattern: ^[a-z0-9_]{3,64}$
  - Must be unique within decision_type (no duplicates)
  - Error: 400 "INVALID_RULE_NAME" or 409 "DUPLICATE_RULE_NAME"

VALIDATION 3: condition structure
  - Must be object with valid condition format
  - Nesting depth max 3 (per INFRA-DEC-003)
  - Supported operators: ==, !=, <, <=, >, >=, AND, OR, NOT
  - Context fields referenced must be scalar types
  - Error: 400 "INVALID_CONDITION_FORMAT"

VALIDATION 4: action.outcome
  - Must be one of: ALLOWED, DENIED, REQUIRE_APPROVAL
  - Error: 400 "INVALID_ACTION_OUTCOME"

VALIDATION 5: approval_config (if outcome=REQUIRE_APPROVAL)
  - Must include approver_role (role identifier)
  - Pattern: ^[A-Z][A-Z0-9_]*$
  - Error: 400 "INVALID_APPROVAL_CONFIG"

VALIDATION 6: extension_hooks
  - Must be array (or empty)
  - Each hook must have: hook_type (string), hook_url (HTTPS), timeout (seconds)
  - Error: 400 "INVALID_EXTENSION_HOOKS"

Persistence:

INSERT INTO rules (
  rule_id, decision_type, rule_name, description, conditions, action,
  extension_hooks, tenant_id, version, status, created_by_user_id, created_at
)
VALUES (
  uuid(), ?, ?, ?, ?, ?, ?, ?, '1.0', 'DRAFT', ?, now()
)

Result:
  - New rule created with status = DRAFT (not active yet)
  - Rule ID returned to caller
  - Audit log: rule_created event

Response:
{
  "rule_id": uuid,
  "decision_type": string,
  "rule_name": string,
  "status": "DRAFT",
  "version": "1.0",
  "created_at": timestamp
}
```

### 1.2 Update Rule

```
OPERATION: Modify rule definition (DRAFT status only).

Request Schema:
{
  rule_id: uuid,
  rule_name: string,                  // optional
  description: string,                // optional
  conditions: object,                 // optional
  action: object,                     // optional
  extension_hooks: object[]           // optional
}

Validation:

CONSTRAINT 1: Rule must be DRAFT status
  - Query: SELECT status FROM rules WHERE rule_id = ?
  - If status != 'DRAFT': Error 409 "CANNOT_UPDATE_ACTIVE_RULE"
  - Rationale: Active rules must be versioned, not modified in-place

CONSTRAINT 2: Tenant isolation
  - Verify rule.tenant_id matches current_tenant_id
  - Error: 403 "FORBIDDEN"

Validation rules (same as Create):
  - Validate rule_name format (if provided)
  - Validate condition structure (if provided)
  - Validate action (if provided)
  - Validate extension_hooks (if provided)

Persistence (DRAFT update):

UPDATE rules SET
  rule_name = ?,
  description = ?,
  conditions = ?,
  action = ?,
  extension_hooks = ?,
  updated_at = now()
WHERE rule_id = ? AND status = 'DRAFT' AND tenant_id = ?

Result:
  - Rule updated in-place (DRAFT only)
  - No version increment (still version 1.0)
  - Audit log: rule_updated event

Activation Flow (if not DRAFT):
  - ACTIVE rule cannot be modified directly
  - Must create new version (see 1.3)
  - Deactivate old version
  - Activate new version
```

### 1.3 Rule Versioning

```
OPERATION: Create new version when modifying ACTIVE rule.

Scenario:
  - Rule "high_amount_rule" version 1.0 is ACTIVE
  - Need to change condition from 10000 to 15000
  - Cannot modify in-place (ACTIVE)

Process:

STEP 1: Query current rule
  SELECT * FROM rules
  WHERE rule_name = ? AND decision_type = ? AND tenant_id = ?
  ORDER BY version DESC LIMIT 1

STEP 2: Verify current status is ACTIVE
  - If status = 'ACTIVE': proceed to step 3
  - If status = 'DRAFT': use Update operation (1.2), no versioning

STEP 3: Create new version (copy and modify)
  INSERT INTO rules (
    rule_id, decision_type, rule_name, description, conditions, action,
    extension_hooks, tenant_id, version, status, created_by_user_id, created_at
  )
  VALUES (
    uuid(),
    current.decision_type,
    current.rule_name,
    current.description,
    new_conditions,  // from request
    current.action,  // or override from request
    current.extension_hooks,  // or override from request
    current.tenant_id,
    increment_version(current.version),  // 1.0 → 1.1, 1.1 → 1.2, etc.
    'DRAFT',
    ?,
    now()
  )

STEP 4: New version created (DRAFT)
  - Old version (1.0) remains ACTIVE
  - New version (1.1) is DRAFT
  - Both versions exist simultaneously

STEP 5: Test new version
  - CMS admin can test rule 1.1 (DRAFT) without affecting 1.0 (ACTIVE)
  - Use test endpoint (see 1.7)

STEP 6: Activate new version (see 1.4)
  - Once tested, activate 1.1
  - Deactivate 1.0
  - Switch happens atomically
```

### 1.4 Activate Rule

```
OPERATION: Activate DRAFT rule or activate new version.

Request Schema:
{
  rule_id: uuid,
  approval_comment: string            // for audit trail
}

Validation:

CONSTRAINT 1: Rule must be DRAFT status
  - SELECT status FROM rules WHERE rule_id = ?
  - If status = 'ACTIVE': Error 409 "ALREADY_ACTIVE"

CONSTRAINT 2: Tenant isolation
  - Verify rule.tenant_id matches current_tenant_id
  - Error: 403 "FORBIDDEN"

CONSTRAINT 3: Rule is valid (syntax, conditions, action)
  - Check for parse errors, unsupported operators, etc.
  - If invalid: Error 400 "INVALID_RULE"

Activation Process:

STEP 1: If previous version ACTIVE, mark as DEPRECATED
  SELECT * FROM rules
  WHERE rule_name = ? AND decision_type = ? AND status = 'ACTIVE'

  If found:
    UPDATE rules SET status = 'DEPRECATED' WHERE rule_id = ?

STEP 2: Mark new version as ACTIVE
  UPDATE rules SET status = 'ACTIVE' WHERE rule_id = ? AND status = 'DRAFT'

STEP 3: Invalidate rule cache (Core)
  - Set cache TTL = 0 for this rule_set
  - Core reloads from database on next decision
  - Propagation: < 2 seconds

STEP 4: Audit log
  INSERT INTO operations_audit (...) VALUES (
    operation_type='ACTIVATE',
    resource_type='rule',
    resource_id=?,
    actor_user_id=?,
    reason='approval_comment',
    timestamp=now()
  )

Result:
  - Old version (if any): DEPRECATED
  - New version: ACTIVE
  - New decisions use new rule immediately
  - Old decisions unaffected (immutable)

Response:
{
  "rule_id": uuid,
  "version": "1.1",
  "status": "ACTIVE",
  "previous_version": "1.0",
  "previous_version_status": "DEPRECATED",
  "activated_at": timestamp
}
```

### 1.5 Deactivate Rule

```
OPERATION: Deactivate ACTIVE rule (mark as ARCHIVED/DEPRECATED).

Request Schema:
{
  rule_id: uuid,
  reason: string                      // for audit trail (required)
}

Validation:

CONSTRAINT 1: Rule must be ACTIVE status
  - If status != 'ACTIVE': Error 409 "ALREADY_INACTIVE"

CONSTRAINT 2: Tenant isolation
  - Verify rule.tenant_id matches current_tenant_id
  - Error: 403 "FORBIDDEN"

CONSTRAINT 3: Reason must be provided
  - Rationale: Audit trail importance
  - Error: 400 "REASON_REQUIRED"

Deactivation Process:

STEP 1: Check if decision_type has other ACTIVE rules
  SELECT COUNT(*) FROM rules
  WHERE decision_type = ? AND status = 'ACTIVE'

STEP 2: If only 1 ACTIVE rule: warn (but allow deactivation)
  - Warning: "No other active rules for this decision_type (fail-closed)"
  - Decision with no rules → outcome DENIED

STEP 3: Mark as DEPRECATED
  UPDATE rules SET
    status = 'DEPRECATED',
    deactivated_at = now(),
    deactivation_reason = ?
  WHERE rule_id = ? AND status = 'ACTIVE'

STEP 4: Invalidate rule cache
  - Core reloads rule_set on next decision

STEP 5: Audit log
  INSERT INTO operations_audit (...) VALUES (
    operation_type='DEACTIVATE',
    reason=?,
    timestamp=now()
  )

Result:
  - Rule marked as DEPRECATED
  - No longer used by Core
  - Data not deleted (audit trail preserved)

Response:
{
  "rule_id": uuid,
  "status": "DEPRECATED",
  "deactivated_at": timestamp,
  "reason": string
}
```

### 1.6 Query Rules

```
OPERATION: List rules (by decision_type, tenant, status).

Query Parameters:
{
  decision_type: string,              // filter by decision_type
  status: "DRAFT" | "ACTIVE" | "DEPRECATED",  // filter by status
  rule_name: string,                  // search rule name (optional)
  limit: number,                      // 1-1000 (default 100)
  offset: number                      // for pagination
}

Query:
  SELECT * FROM rules
  WHERE tenant_id = current_tenant_id
    AND (decision_type = ? OR decision_type IS NULL)
    AND (status = ? OR status IS NULL)
    AND (rule_name LIKE ? OR rule_name IS NULL)
  ORDER BY decision_type, rule_name, version DESC
  LIMIT ? OFFSET ?

Response:
{
  "rules": [
    {
      "rule_id": uuid,
      "decision_type": string,
      "rule_name": string,
      "version": string,
      "status": "DRAFT" | "ACTIVE" | "DEPRECATED",
      "created_at": timestamp,
      "activated_at": timestamp | null,
      "created_by_user_id": uuid,
      "description": string
    },
    ...
  ],
  "total_count": number,
  "limit": number,
  "offset": number
}
```

---

## 2. Audit Querying Standards

### 2.1 Rule Change Audit Trail

```
OPERATION: Query who changed what rule and when.

Query:
  SELECT * FROM operations_audit
  WHERE tenant_id = current_tenant_id
    AND resource_type = 'rule'
    AND timestamp BETWEEN ? AND ?
  ORDER BY timestamp DESC

Result Columns:
  - audit_id (unique forever)
  - operation_type (CREATE, UPDATE, ACTIVATE, DEACTIVATE)
  - resource_id (rule_id)
  - actor_user_id (who made change)
  - actor_role (user's role)
  - reason (approval_comment, deactivation_reason, etc.)
  - timestamp (when)

Example:
  [
    {audit_id: "aud-001", operation_type: "ACTIVATE", rule_id: "r-123",
     actor_user_id: "user-cms-admin", timestamp: "2025-12-27T14:00:00Z"},
    {audit_id: "aud-002", operation_type: "DEACTIVATE", rule_id: "r-123",
     actor_user_id: "user-cms-admin", timestamp: "2025-12-27T14:05:00Z"}
  ]

Explainability:
  - When was rule X activated?
  - Who made the change?
  - What was the reason?
  - Which version?
  - All questions answerable from audit trail
```

### 2.2 Decision Audit Trail (Core Side)

```
OPERATION: Query decisions made by specific rule.

Query (from CMS):
  SELECT * FROM decisions
  WHERE tenant_id = current_tenant_id
    AND rule_matched = ?
    AND created_at BETWEEN ? AND ?

Result:
  - decision_id
  - outcome (ALLOWED, DENIED, REQUIRE_APPROVAL)
  - context_snapshot
  - created_at
  - latency_ms

Purpose:
  - Verify rule is behaving as expected
  - Identify rule side effects (e.g., too many DENY outcomes)
  - Audit trail for compliance (rule change → decision impact)

Example Query:
  SELECT COUNT(*), outcome
  FROM decisions
  WHERE rule_matched = 'high_amount_rule'
    AND created_at > now() - interval 24 hours
  GROUP BY outcome

  Result:
    outcome=ALLOWED: 950 decisions
    outcome=DENIED: 45 decisions
    outcome=REQUIRE_APPROVAL: 5 decisions
```

---

## 3. Rule Testing Standards

### 3.1 Test Rule (DRAFT)

```
OPERATION: Test DRAFT rule without activating.

Request Schema:
{
  rule_id: uuid,
  test_context: object              // context to test against rule
}

Validation:

CONSTRAINT 1: Rule must be DRAFT or ACTIVE
  - Can test DRAFT (before activation)
  - Can test ACTIVE (for preview, no side effects)

CONSTRAINT 2: test_context format
  - Must be valid context (see INFRA-LAY3-001)
  - Must not contain PII

CONSTRAINT 3: Tenant isolation
  - Verify rule.tenant_id matches current_tenant_id

Execution:

STEP 1: Load rule definition
  SELECT conditions, action FROM rules WHERE rule_id = ?

STEP 2: Evaluate condition against test_context
  - Use same evaluation engine as Core
  - No database persistence
  - No side effects

STEP 3: Return result
  {
    "rule_id": uuid,
    "test_context": object,
    "condition_match": true | false,
    "outcome": "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL" | null,
    "approval_role": string | null,
    "execution_time_ms": number
  }

Example:
  Test Request:
  {
    "rule_id": "r-high-amount",
    "test_context": {
      "amount": 15000,
      "department": "accounting"
    }
  }

  Response:
  {
    "condition_match": true,
    "outcome": "DENY",
    "execution_time_ms": 2
  }
```

### 3.2 Compare Rule Versions

```
OPERATION: Side-by-side comparison of ACTIVE vs DRAFT versions.

Request Schema:
{
  rule_id_draft: uuid,
  rule_id_active: uuid,
  test_cases: [
    {
      "context": object,
      "expected_outcome": "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
    },
    ...
  ]
}

Execution:

STEP 1: Evaluate all test_cases against DRAFT version
STEP 2: Evaluate all test_cases against ACTIVE version
STEP 3: Compare outcomes

Response:
{
  "comparison": [
    {
      "test_case": {...},
      "draft_outcome": "ALLOWED",
      "active_outcome": "DENY",
      "matches": false,
      "diff": "Rule outcome changed"
    },
    {
      "test_case": {...},
      "draft_outcome": "DENY",
      "active_outcome": "DENY",
      "matches": true
    }
  ],
  "total_tests": 10,
  "matching": 9,
  "differing": 1
}
```

---

## 4. Rule Validation Standards

### 4.1 Syntax Validation

```
REQUIREMENT: Rule conditions MUST be syntactically valid.

Validation Rules:

RULE 1: Condition operators
  - Supported: ==, !=, <, <=, >, >=, AND, OR, NOT
  - Unsupported: regex, contains (partial), in, between
  - Error: "UNSUPPORTED_OPERATOR"

RULE 2: Operand types
  - Supported: string, number, boolean, null
  - Unsupported: array, object, function
  - Error: "UNSUPPORTED_OPERAND_TYPE"

RULE 3: Nesting depth
  - Max: 3 levels
  - Example: ((A AND B) OR (C AND D)) = depth 2 (valid)
  - Example: (((A AND B) OR C) AND D) = depth 4 (invalid)
  - Error: "NESTING_DEPTH_EXCEEDED"

RULE 4: Missing operands
  - Every operator must have left and right operands
  - (context.amount >) = invalid
  - (context.amount > 10000) = valid
  - Error: "MALFORMED_CONDITION"

RULE 5: Type mismatch
  - Numeric operators (<, <=, >, >=) on numeric operands only
  - (context.name > 10000) = invalid (string > number)
  - Error: "TYPE_MISMATCH"

Validation Process:
  - Parse condition as AST (Abstract Syntax Tree)
  - Walk tree, validate each node
  - Collect all errors
  - Return detailed error list
```

### 4.2 Context Field Validation

```
REQUIREMENT: Rule conditions MUST reference valid context fields.

Context Field Registry:

For each decision_type, CMS should maintain list of valid context fields:
  {
    "decision_type": "accounting.journal_approval",
    "valid_fields": [
      {"name": "journal_id", "type": "string"},
      {"name": "amount", "type": "number"},
      {"name": "department", "type": "string"},
      {"name": "is_correction", "type": "boolean"}
    ]
  }

Validation:

When creating/updating rule:
  1. Extract all context field references from condition
     - "context.amount" → field "amount"
     - "context.department" → field "department"

  2. Check each field in registry
     - If found: OK
     - If not found: Warning (field may not exist in runtime)

  3. Check type compatibility
     - Operator "<" used on field "amount" (number type): OK
     - Operator "<" used on field "department" (string type): Error

Note:
  - Field registry is optional (if maintained)
  - If not maintained: warnings only, no hard errors
  - Runtime type mismatch → Core logs error, outcome DENIED
```

---

## 5. Archival & Cleanup Standards

### 5.1 Rule Archival

```
REQUIREMENT: CMS manages rule archival (move old rules to warm/cold storage).

Archival Trigger:

CONDITION 1: Rule status = DEPRECATED
  - Rule deactivated > 90 days ago
  - No active decisions referencing this rule

CONDITION 2: ACTIVE rule without recent decisions
  - Rule ACTIVE > 1 year
  - No decisions created using this rule > 90 days
  - Indicates obsolete rule

Process:

STEP 1: Identify candidates
  SELECT * FROM rules
  WHERE status = 'DEPRECATED'
    AND deactivated_at < now() - interval 90 days
    AND tenant_id = ?

STEP 2: Verify no active references
  SELECT COUNT(*) FROM decisions
  WHERE rule_matched = ?
    AND created_at > now() - interval 90 days

STEP 3: Archive (copy to warm storage)
  - Copy rule definition to warm tier
  - Keep reference in hot tier (for audit)
  - Move actual data to object storage (S3, GCS, etc.)

STEP 4: Update metadata
  UPDATE rules SET
    archived_at = now(),
    archive_location = 'warm_storage/rules/...',
    hot_storage_available = false
  WHERE rule_id = ?

STEP 5: Verify archival
  - Hash file: SHA256(rule_definition)
  - Store hash in hot tier
  - Compare hash on retrieval (detect tampering)

Retrieval:

If CMS needs to query archived rule:
  1. Check archive_location
  2. Retrieve from warm storage
  3. Verify hash
  4. Return definition

Audit Log:
  - archival_operation_started event
  - archival_operation_completed event
  - archival_failure event (if failed)
```

### 5.2 Rule Cleanup (Permanent Deletion)

```
REQUIREMENT: CMS can permanently delete DEPRECATED rules (compliance/GDPR).

Prerequisites:

1. Rule status = DEPRECATED
2. Rule archived >= 7 years (retention period)
3. No decisions reference this rule (in any tier)
4. Legal hold released (if applicable)
5. Compliance approval (if required)

Deletion Process:

STEP 1: Notify stakeholders
  - Alert: "Deleting rule X in 30 days (compliance window)"
  - Allow objections

STEP 2: Final audit snapshot
  - Generate complete audit report
  - Include all versions, all changes, all decisions
  - Archive report to cold storage

STEP 3: Delete warm storage file
  - Retrieve file from warm tier
  - Verify hash matches (no tampering)
  - Delete file permanently

STEP 4: Mark as deleted in hot storage
  UPDATE rules SET
    status = 'DELETED',
    deleted_at = now(),
    reason = 'RETENTION_EXPIRED',
    final_audit_report = 'uri_to_cold_storage'
  WHERE rule_id = ?

STEP 5: Log deletion
  INSERT INTO operations_audit (...) VALUES (
    operation_type = 'DELETE',
    resource_type = 'rule',
    resource_id = ?,
    deletion_reason = 'RETENTION_EXPIRED',
    approver_user_id = ?,
    timestamp = now()
  )

Note:
  - Rule record remains in database (for audit history)
  - Rule definition deleted from warm/cold storage
  - Only metadata/history retained in hot storage
```

---

## 6. Guard Rails: CMS Constraints

### 6.1 Non-Negotiable Guard Rails

```
GUARDRAIL 1: Not in Critical Path
  - CMS is async (rule changes do NOT block decisions)
  - Core caches rules, cache invalidation < 2 seconds
  - Old decisions unaffected (immutable)

GUARDRAIL 2: Tenant Isolation
  - CMS admin can only manage own tenant's rules
  - Cross-tenant queries rejected (403)
  - RLS/schema enforced at data layer

GUARDRAIL 3: No Immutability Violation
  - CMS cannot update/delete decisions or workflows
  - CMS cannot update/delete events
  - CMS cannot access event_log directly
  - All reads via audit queries only

GUARDRAIL 4: Rule Versioning
  - ACTIVE rules cannot be modified in-place
  - Must create new version → test → activate
  - Old versions preserved (audit trail)

GUARDRAIL 5: Audit Logging
  - Every operation logged (CREATE, UPDATE, ACTIVATE, DEACTIVATE, DELETE)
  - Actor tracked (who made change)
  - Reason tracked (why, when)
  - Timestamps immutable

GUARDRAIL 6: Role-Based Access
  - CMS admin: full rule management
  - CMS viewer: read-only (query, test, audit)
  - Application users: cannot access CMS

GUARDRAIL 7: Validation Before Activation
  - Rule syntax validated before creation
  - Rule conditions validated (operators, nesting, types)
  - Rule logic tested before activation (test endpoint)
  - Invalid rules rejected (400)

GUARDRAIL 8: Cache Invalidation
  - Rule changes trigger cache invalidation
  - Core reloads within 2 seconds
  - Stale read window is bounded (no indefinite staleness)
```

### 6.2 Delegated Responsibilities (NOT CMS)

```
CMS does NOT implement:

❌ Decision evaluation (delegated to Core)
❌ Workflow state management (delegated to Core)
❌ User identity validation (delegated to Application Adapter)
❌ Permission checking beyond basic RBAC (delegated to auth system)
❌ Business logic (rule logic is business config, not CMS code)
❌ Event publishing (delegated to Core)
❌ Immutability enforcement (delegated to Core & data layer)
```

---

## 7. CMS Implementation Checklist

```
Before releasing CMS, verify:

RULE CRUD:
  ✓ Create rule (validation, draft status)
  ✓ Update rule (DRAFT only)
  ✓ Activate rule (status transition, cache invalidation)
  ✓ Deactivate rule (audit trail, no side effects)
  ✓ Query rules (by decision_type, status, pagination)

RULE VERSIONING:
  ✓ New version created when modifying ACTIVE rule
  ✓ Old version marked DEPRECATED (not deleted)
  ✓ Version number increments (1.0 → 1.1 → 1.2)
  ✓ Test DRAFT before activation
  ✓ Atomic activation (old ACTIVE → DEPRECATED, new DRAFT → ACTIVE)

AUDIT TRAIL:
  ✓ Rule changes logged (who, when, why)
  ✓ Operations audit immutable (append-only)
  ✓ Decision audit trail queryable
  ✓ Explainability: rule change → decision impact (analyzable)

TESTING:
  ✓ Test rule endpoint (DRAFT & ACTIVE)
  ✓ Compare versions (side-by-side outcomes)
  ✓ Validation: syntax, conditions, nesting, types
  ✓ Context field validation (warnings if undefined)

TENANT ISOLATION:
  ✓ CMS admin scoped to own tenant
  ✓ Cross-tenant queries rejected (403)
  ✓ RLS/schema enforced at data layer

ARCHIVAL & CLEANUP:
  ✓ Archival job (move DEPRECATED rules to warm storage)
  ✓ Retrieval (cold storage rehydration < 60 minutes)
  ✓ Permanent deletion (GDPR/compliance)
  ✓ Audit report generation (before deletion)

INTEGRATION:
  ✓ Cache invalidation signals to Core
  ✓ Cache propagation < 2 seconds
  ✓ Core reloads rules on invalidation
  ✓ Old decisions unaffected (immutable)

SECURITY:
  ✓ No immutability violation (no direct event_log access)
  ✓ No modification of decisions/workflows
  ✓ No access to cross-tenant data
  ✓ Role-based access control (admin vs viewer)

MONITORING:
  ✓ Rule activation events logged
  ✓ Rule deactivation events logged
  ✓ Rule update errors logged
  ✓ Metrics: active_rules_per_decision_type, rule_version_distribution
```

---

## 8. Summary: CMS as Operational Tool

✅ **Rule CRUD**: Create, update, activate, deactivate with versioning
✅ **Tenant Isolation**: Database-enforced, CMS respects boundaries
✅ **Audit Trail**: Immutable, append-only, explainable
✅ **Testing**: Syntax validation, test endpoint, compare versions
✅ **Archival**: Move old rules to warm/cold, audit trail preserved
✅ **Guard Rails**: Not in critical path, no immutability violation, fully audited

**Status**: Layer 3.3 DRAFT, ready for review.

**Next**: Data Layer Implementation Standards (INFRA-LAY3-004).
