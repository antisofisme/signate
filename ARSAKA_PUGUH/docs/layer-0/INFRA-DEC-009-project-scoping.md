# INFRA-DEC-009: Project Scoping Model

**VERSION**: Layer 0 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines how Rules, Decisions, Workflows, and Events are scoped within the Tenant/Project hierarchy. The system uses a **Hybrid Scope Model** that allows:
- **Tenant-level rules**: Shared across all projects
- **Project-level rules**: Isolated to specific projects
- **Project-required resources**: Decisions, Workflows, Events always scoped to project

---

## Scope Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     TENANT BOUNDARY                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              TENANT-LEVEL RESOURCES                         │ │
│  │  (project_id = NULL, shared across all projects)            │ │
│  │                                                              │ │
│  │  Rules:                                                      │ │
│  │    - accounting.journal_approval (tenant-wide)               │ │
│  │    - security.access_control (tenant-wide)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  PROJECT: Prod  │  │ PROJECT: Stage  │  │  PROJECT: Dev   │ │
│  │                 │  │                 │  │                 │ │
│  │  Rules:         │  │  Rules:         │  │  Rules:         │ │
│  │  (project-level)│  │  (project-level)│  │  (project-level)│ │
│  │                 │  │                 │  │                 │ │
│  │  Decisions:     │  │  Decisions:     │  │  Decisions:     │ │
│  │  (required)     │  │  (required)     │  │  (required)     │ │
│  │                 │  │                 │  │                 │ │
│  │  Workflows:     │  │  Workflows:     │  │  Workflows:     │ │
│  │  (required)     │  │  (required)     │  │  (required)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Rules Scoping (Hybrid Model)

### Scope Types

| Scope | project_id | Visibility | Use Case |
|-------|------------|------------|----------|
| **Tenant-level** | NULL | All projects in tenant | Global policies, security rules |
| **Project-level** | UUID | Only that project | Environment-specific rules |

### Rule Structure

```typescript
Rule {
  rule_id: UUID
  tenant_id: UUID           // REQUIRED - tenant isolation
  project_id: UUID | null   // NULL = tenant-level, UUID = project-level

  decision_type: string     // e.g., "accounting.journal_approval"
  name: string              // Human-readable name
  version: string           // Semantic version

  condition: object         // Rule condition (first-match-wins)
  action: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"

  priority: number          // Lower = higher priority (within same scope)
  status: "active" | "draft" | "deprecated"

  created_at: timestamp
  updated_at: timestamp
}
```

### Database Schema

```sql
ALTER TABLE rules ADD COLUMN project_id UUID REFERENCES projects(project_id);

-- Rules index for efficient lookup
CREATE INDEX idx_rules_scope ON rules(tenant_id, project_id, decision_type, status);

-- Unique constraint: same decision_type can have different rules at tenant vs project level
-- No uniqueness constraint on (tenant_id, decision_type) alone
```

### Rule Evaluation Algorithm

When evaluating a decision for a specific project:

```
INPUT:
  - tenant_id: UUID
  - project_id: UUID
  - decision_type: string
  - context: object

ALGORITHM:
  1. Load PROJECT-LEVEL rules:
     SELECT * FROM rules
     WHERE tenant_id = :tenant_id
       AND project_id = :project_id
       AND decision_type = :decision_type
       AND status = 'active'
     ORDER BY priority ASC

  2. Load TENANT-LEVEL rules:
     SELECT * FROM rules
     WHERE tenant_id = :tenant_id
       AND project_id IS NULL
       AND decision_type = :decision_type
       AND status = 'active'
     ORDER BY priority ASC

  3. Merge rules with PROJECT-LEVEL PRECEDENCE:
     merged_rules = []

     # Add project-level rules first
     for rule in project_rules:
       merged_rules.append(rule)

     # Add tenant-level rules that don't have project-level override
     project_rule_names = [r.name for r in project_rules]
     for rule in tenant_rules:
       if rule.name not in project_rule_names:
         merged_rules.append(rule)

     # Sort by priority
     merged_rules.sort(by: priority)

  4. Evaluate (first-match-wins):
     for rule in merged_rules:
       if rule.condition.evaluate(context):
         return Decision(
           outcome: rule.action,
           rule_matched: rule.name,
           rule_version: rule.version,
           rule_scope: "tenant" if rule.project_id is None else "project"
         )

     # No rule matched → fail-closed
     return Decision(outcome: "DENIED", rule_matched: null)
```

### Rule Precedence Examples

**Example 1: Project Override**

```
Tenant-level rule: "All transactions > $10K need CFO approval"
Project-level rule (Dev): "All transactions allowed for testing"

In Production project:
  → Tenant rule applies (no project override)
  → Transaction $15K → REQUIRE_APPROVAL

In Development project:
  → Project rule overrides tenant rule
  → Transaction $15K → ALLOWED
```

**Example 2: Additive Rules**

```
Tenant-level rule: "CFO approval for > $10K"
Project-level rule (Prod): "Additional: Legal approval for contracts"

In Production project:
  → Both rules apply (different decision_types)
  → $15K transaction → REQUIRE_APPROVAL (CFO)
  → Contract signing → REQUIRE_APPROVAL (Legal)
```

### Rule Management API

```typescript
// Create tenant-level rule
POST /api/v1/tenants/{tenant_id}/rules
{
  decision_type: "accounting.journal_approval",
  name: "high_value_cfo_approval",
  condition: { amount_cents: { gt: 1000000 } },
  action: "REQUIRE_APPROVAL",
  priority: 100
}

// Create project-level rule
POST /api/v1/tenants/{tenant_id}/projects/{project_id}/rules
{
  decision_type: "accounting.journal_approval",
  name: "dev_always_allow",
  condition: { always: true },
  action: "ALLOWED",
  priority: 1
}

// List rules with scope filter
GET /api/v1/tenants/{tenant_id}/rules?scope=tenant
GET /api/v1/tenants/{tenant_id}/projects/{project_id}/rules?include_tenant=true
```

---

## 2. Decisions Scoping (Project-Required)

### Principle

**Decisions MUST always be scoped to a project.** There is no such thing as a "tenant-level decision" - every decision is made in the context of a specific project.

### Decision Structure

```typescript
Decision {
  decision_id: UUID
  tenant_id: UUID           // REQUIRED - tenant isolation
  project_id: UUID          // REQUIRED - project scope

  decision_type: string
  context_hash: string      // Hash of sanitized context

  outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
  rule_matched: string | null
  rule_version: string | null
  rule_scope: "tenant" | "project"   // Which scope provided the matched rule

  approval_workflow_id: UUID | null

  // Immutable after creation
  created_at: timestamp
  created_by_user_id: UUID
}
```

### Database Schema

```sql
-- Add project_id column (NOT NULL, required)
ALTER TABLE decisions ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);

-- Update index for efficient lookup
CREATE INDEX idx_decisions_scope ON decisions(tenant_id, project_id, decision_type, created_at);
```

### Decision Creation Flow

```
1. SDK receives decision request with tenant_id + project_id
2. Core validates:
   - tenant_id valid and active
   - project_id valid and belongs to tenant
   - User has access to project (via tenant membership)
3. Core evaluates rules (using hybrid model above)
4. Core creates decision with project_id
5. Core emits event (with project_id for filtering)
6. SDK returns decision
```

### Guard Rails

```
GR-DEC-SCOPE-1: Project Required
  IF decision request missing project_id
  THEN request REJECTED
       error: "project_id is required for decisions"

GR-DEC-SCOPE-2: Project Validation
  IF project_id does not belong to tenant_id
  THEN request REJECTED
       error: 404 (not found, no tenant leak)

GR-DEC-SCOPE-3: Immutability
  IF attempt to modify decision.project_id
  THEN request REJECTED
       error: "Decisions are immutable"
```

---

## 3. Workflows Scoping (Project-Required)

### Principle

**Workflows MUST always be scoped to the same project as their parent decision.** A workflow cannot span multiple projects.

### Workflow Structure

```typescript
Workflow {
  workflow_id: UUID
  decision_id: UUID         // FK to parent decision
  tenant_id: UUID           // REQUIRED - denormalized for queries
  project_id: UUID          // REQUIRED - denormalized for queries

  state: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "ESCALATED" | "DELEGATED"

  approver_role: string
  approved_by_user_id: UUID | null
  comment: string | null

  created_at: timestamp
  updated_at: timestamp
}
```

### Database Schema

```sql
-- Add project_id column (NOT NULL, required)
ALTER TABLE workflows ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);

-- Update index
CREATE INDEX idx_workflows_scope ON workflows(tenant_id, project_id, state, created_at);
```

### Workflow Context Consistency

```
GR-WF-SCOPE-1: Parent Decision Consistency
  IF workflow created for decision
  THEN workflow.project_id MUST equal decision.project_id

GR-WF-SCOPE-2: No Cross-Project Workflows
  Workflows CANNOT span multiple projects
  Each workflow belongs to exactly one project

GR-WF-SCOPE-3: Approval Context
  Approver must have access to project (via tenant membership)
  Approval action must include project context
```

---

## 4. Events Scoping (Project-Required)

### Principle

**Events MUST always include project context for proper filtering and audit trails.**

### Event Structure

```typescript
Event {
  event_id: UUID
  tenant_id: UUID           // REQUIRED - partition key
  project_id: UUID          // REQUIRED - for filtering

  event_type: string        // e.g., "decision.created", "workflow.approved"
  aggregate_type: string    // "decision" | "workflow"
  aggregate_id: UUID        // Reference to decision_id or workflow_id

  payload: object           // Event-specific data

  created_at: timestamp     // Immutable
}
```

### Database Schema

```sql
-- Add project_id column (NOT NULL, required)
ALTER TABLE event_log ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);

-- Update index for efficient filtering
CREATE INDEX idx_events_scope ON event_log(tenant_id, project_id, event_type, created_at);
```

### Event Subscription Filtering

```typescript
// Subscribe to events for specific project
EventBus.subscribe({
  tenant_id: "tenant-123",
  project_id: "project-456",
  event_types: ["decision.*", "workflow.*"]
})

// Subscribe to all events in tenant (admin)
EventBus.subscribe({
  tenant_id: "tenant-123",
  project_id: null,  // Wildcard - all projects
  event_types: ["*"]
})
```

---

## 5. API Request Context

### SDK Context Requirements

All SDK requests MUST include both tenant and project context:

```typescript
SDKContext {
  tenant_id: string         // Required
  project_id: string        // Required
  user_id: string           // From JWT
  trace_id: string          // For debugging
  idempotency_key?: string  // For deduplication
}

// Decision request example
infra.decide({
  tenant_id: "tenant-123",
  project_id: "project-456",
  decision_type: "accounting.journal_approval",
  context: {
    amount_cents: 1500000,
    journal_type: "correction"
  }
});
```

### Frontend Context Management

```typescript
// authStore.ts
interface AuthState {
  user: User | null
  active_tenant_id: string | null
  active_project_id: string | null

  // Derived
  current_context: SDKContext | null
}

// Usage in components
const { current_context } = useAuthStore()

// All API calls include context
const decision = await sdk.decide({
  ...current_context,
  decision_type: "...",
  context: { ... }
})
```

### URL Routing

```
/app/{tenant-slug}/{project-slug}/dashboard
/app/{tenant-slug}/{project-slug}/decisions
/app/{tenant-slug}/{project-slug}/rules
/app/{tenant-slug}/{project-slug}/workflows
/app/{tenant-slug}/{project-slug}/audit
```

---

## 6. Audit Log Queries

### Query Patterns

```typescript
// Query decisions in specific project
GET /api/v1/tenants/{tenant_id}/projects/{project_id}/decisions
  ?start_date=2024-01-01
  &end_date=2024-01-31
  &outcome=REQUIRE_APPROVAL

// Query decisions across all projects (admin)
GET /api/v1/tenants/{tenant_id}/decisions
  ?start_date=2024-01-01
  &end_date=2024-01-31

// Query rules with scope
GET /api/v1/tenants/{tenant_id}/rules
  ?scope=all        // tenant + all projects
  ?scope=tenant     // tenant-level only

GET /api/v1/tenants/{tenant_id}/projects/{project_id}/rules
  ?include_tenant=true   // Include tenant-level rules
```

### Dashboard Metrics

```typescript
// Per-project metrics
GET /api/v1/tenants/{tenant_id}/projects/{project_id}/metrics
{
  decisions_today: number,
  decisions_this_month: number,
  approval_rate: number,
  average_approval_time_hours: number,
  rule_hits: {
    [rule_name]: number
  }
}

// Tenant-wide metrics (aggregate)
GET /api/v1/tenants/{tenant_id}/metrics
{
  total_decisions_this_month: number,
  decisions_by_project: {
    [project_id]: number
  },
  decisions_by_outcome: {
    ALLOWED: number,
    DENIED: number,
    REQUIRE_APPROVAL: number
  }
}
```

---

## 7. Cross-Project Considerations

### Current Scope (v1)

In v1, there is **NO cross-project interaction**:
- Rules are evaluated within project context
- Decisions cannot reference other projects
- Workflows cannot span projects
- Events are isolated per project

### Future Scope (v2 - Deferred)

Potential v2 features (NOT in current scope):
- Cross-project rule references
- Cross-project workflow chains
- Shared rule libraries
- Project templates

---

## 8. Guard Rails Summary

### Rule Scoping
```
GR-RULE-SCOPE-1: tenant_id REQUIRED on all rules
GR-RULE-SCOPE-2: project_id determines scope (NULL = tenant-level)
GR-RULE-SCOPE-3: Project-level rules override tenant-level (same name)
GR-RULE-SCOPE-4: Rule priority only applies within same scope
```

### Decision Scoping
```
GR-DEC-SCOPE-1: project_id REQUIRED on all decisions
GR-DEC-SCOPE-2: project_id must belong to tenant_id
GR-DEC-SCOPE-3: Decisions are immutable (no scope change)
```

### Workflow Scoping
```
GR-WF-SCOPE-1: project_id REQUIRED, must match parent decision
GR-WF-SCOPE-2: No cross-project workflows
GR-WF-SCOPE-3: Approver must have project access
```

### Event Scoping
```
GR-EVT-SCOPE-1: project_id REQUIRED on all events
GR-EVT-SCOPE-2: Events filterable by project
GR-EVT-SCOPE-3: Events immutable after creation
```

---

## 9. Migration Strategy

### Existing Data Backfill

```sql
-- Step 1: Ensure all tenants have default project
INSERT INTO projects (project_id, tenant_id, name, slug, is_default)
SELECT
  gen_random_uuid(),
  tenant_id,
  'Default',
  'default',
  TRUE
FROM tenants t
WHERE NOT EXISTS (
  SELECT 1 FROM projects p
  WHERE p.tenant_id = t.tenant_id AND p.is_default = TRUE
);

-- Step 2: Backfill decisions
UPDATE decisions
SET project_id = (
  SELECT project_id FROM projects
  WHERE tenant_id = decisions.tenant_id AND is_default = TRUE
)
WHERE project_id IS NULL;

-- Step 3: Backfill workflows
UPDATE workflows
SET project_id = (
  SELECT d.project_id FROM decisions d
  WHERE d.decision_id = workflows.decision_id
)
WHERE project_id IS NULL;

-- Step 4: Backfill events
UPDATE event_log
SET project_id = (
  SELECT project_id FROM projects
  WHERE tenant_id = event_log.tenant_id AND is_default = TRUE
)
WHERE project_id IS NULL;

-- Step 5: Add NOT NULL constraint after backfill
ALTER TABLE decisions ALTER COLUMN project_id SET NOT NULL;
ALTER TABLE workflows ALTER COLUMN project_id SET NOT NULL;
ALTER TABLE event_log ALTER COLUMN project_id SET NOT NULL;
```

---

## 10. Checklist: Project Scoping DRAFT

- ✅ Hybrid scope model defined (tenant + project level rules)
- ✅ Rule evaluation algorithm defined (project precedence)
- ✅ Decision scoping defined (project-required)
- ✅ Workflow scoping defined (project-required)
- ✅ Event scoping defined (project-required)
- ✅ API context requirements defined
- ✅ URL routing defined
- ✅ Audit query patterns defined
- ✅ Guard rails defined (12 rules)
- ✅ Migration strategy defined

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-007: Identity Model (for Project entity)
- INFRA-DEC-002: Tenancy Model (for tenant isolation)
