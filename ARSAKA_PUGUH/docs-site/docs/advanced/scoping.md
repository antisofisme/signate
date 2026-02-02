---
sidebar_position: 2
---

# Resource Scoping

Understand how resources are scoped in ATLAS PUGUH.

## Scoping Model

PUGUH uses a two-level scoping model:

```
Tenant
└── Project
    └── Resources (Rules, Decisions, Workflows)
```

## Scope Types

### Tenant-Scoped (Shared)

Resources available across all projects:

```typescript
// Create tenant-level rule
const rule = await client.createRule({
  name: 'Company-Wide Policy',
  scope: 'tenant',
  // No projectId
});
```

Use cases:
- Organization-wide policies
- Global approval thresholds
- Compliance rules

### Project-Scoped (Isolated)

Resources only available within a specific project:

```typescript
// Create project-level rule
const rule = await client.createRule({
  name: 'Production Rule',
  scope: 'project',
  projectId: 'project-uuid',
});
```

Use cases:
- Environment-specific rules
- Team-isolated resources
- Test configurations

## Resource Scoping Rules

| Resource | Scope Options | Notes |
|----------|---------------|-------|
| **Rules** | Tenant or Project | Project rules override tenant |
| **Decisions** | Project only | Always project-scoped |
| **Workflows** | Project only | Templates can be tenant-level |
| **Audit Logs** | Both | Filterable by project |

## Rule Evaluation Order

When a decision is requested:

1. **Project Rules First**: Evaluate project-specific rules
2. **Tenant Rules Second**: Evaluate shared rules
3. **Priority Ordering**: Higher priority wins within each level
4. **First Match**: Stop at first matching rule

### Example

```
Request: expense_approval in Production project

Evaluation Order:
1. [P100] Production: Emergency Override (project) → No match
2. [P50]  Production: Strict Limit (project) → No match
3. [P100] Company: CFO Approval (tenant) → MATCH → Stop
4. [P50]  Company: Manager Approval (tenant) → Skipped
5. [P10]  Company: Default Allow (tenant) → Skipped
```

## Scope Inheritance

### Rules
- Project rules can override tenant rules
- Use priority to control override behavior
- Explicit overrides preferred over implicit

### Workflows
- Workflow templates can be tenant-level
- Workflow instances are always project-scoped
- Cross-project workflows not supported

### Users
- User permissions inherited from tenant role
- No project-level user permissions (yet)
- Project access controlled by tenant membership

## Configuration Patterns

### Pattern 1: Override by Priority

Tenant rule with low priority, project rule with high priority:

```typescript
// Tenant rule (base policy)
await client.createRule({
  name: 'Default Manager Approval',
  priority: 50,
  scope: 'tenant',
  conditions: { field: 'amount', operator: '>', value: 1000 },
  actions: { type: 'REQUIRE_APPROVAL' },
});

// Project rule (override for production)
await client.createRule({
  name: 'Production: Stricter Limit',
  priority: 100,
  scope: 'project',
  projectId: 'production',
  conditions: { field: 'amount', operator: '>', value: 500 },
  actions: { type: 'REQUIRE_APPROVAL' },
});
```

Result: Production uses $500 limit, others use $1000.

### Pattern 2: Additive Rules

Multiple rules that add conditions:

```typescript
// Tenant: Always require approval for equipment
await client.createRule({
  name: 'Equipment Always Approval',
  priority: 200,
  scope: 'tenant',
  conditions: { field: 'category', operator: '=', value: 'equipment' },
  actions: { type: 'REQUIRE_APPROVAL' },
});

// Project: Also require for high amounts
await client.createRule({
  name: 'High Amount Approval',
  priority: 100,
  scope: 'project',
  projectId: 'production',
  conditions: { field: 'amount', operator: '>', value: 10000 },
  actions: { type: 'REQUIRE_APPROVAL' },
});
```

Both rules can trigger, tenant rule has higher priority.

### Pattern 3: Project Exemption

Exempt a project from tenant rules:

```typescript
// Tenant: Require approval over $5000
await client.createRule({
  name: 'Standard Approval',
  priority: 50,
  scope: 'tenant',
  conditions: { field: 'amount', operator: '>', value: 5000 },
  actions: { type: 'REQUIRE_APPROVAL' },
});

// Development project: Auto-approve everything
await client.createRule({
  name: 'Dev: Auto Approve',
  priority: 1000, // Very high priority
  scope: 'project',
  projectId: 'development',
  conditions: { field: 'true', operator: '=', value: true }, // Always match
  actions: { type: 'ALLOW' },
});
```

Development project bypasses normal rules.

## Best Practices

### 1. Define Clear Scope Boundaries

Document what belongs at tenant vs project level:

| Resource Type | Scope | Reason |
|---------------|-------|--------|
| Compliance rules | Tenant | Company-wide |
| Threshold rules | Project | Environment-specific |
| Emergency bypass | Tenant | Universal access |
| Test rules | Project | Only for testing |

### 2. Use Consistent Priority Ranges

```
1-99:    Low priority defaults
100-199: Standard rules
200-299: Important policies
300-399: Critical controls
400+:    Emergency overrides
```

### 3. Document Override Behavior

Add comments explaining rule interactions:

```typescript
await client.createRule({
  name: 'Production Override',
  description: 'Overrides tenant rule "Standard Approval" for stricter control',
  // ...
});
```

### 4. Test Scope Interactions

Create test scenarios that verify:
- Project rules override correctly
- Tenant rules apply when no project match
- Priority ordering works as expected

## Querying by Scope

### List Tenant Rules

```typescript
const tenantRules = await client.listRules({
  scope: 'tenant',
});
```

### List Project Rules

```typescript
const projectRules = await client.listRules({
  scope: 'project',
  projectId: 'project-uuid',
});
```

### List All Rules (Both Scopes)

```typescript
const allRules = await client.listRules({
  projectId: 'project-uuid',
  includeShared: true, // Include tenant rules
});
```

## Debugging Scope Issues

### Why Isn't My Rule Matching?

1. **Check Scope**: Is it the right scope for this project?
2. **Check Priority**: Is another rule matching first?
3. **Check Project ID**: Is the rule in the right project?
4. **Check Evaluation**: Use rule testing to see what's matching

### Viewing Effective Rules

```typescript
const effective = await client.getEffectiveRules({
  projectId: 'project-uuid',
  decisionType: 'expense_approval',
});

// Shows rules in evaluation order
effective.forEach((rule, index) => {
  console.log(`${index + 1}. [${rule.scope}] ${rule.name} (p${rule.priority})`);
});
```

## Related

- [Multi-Tenant Architecture](/docs/advanced/multi-tenant)
- [Best Practices](/docs/advanced/best-practices)
- [Rules Overview](/docs/user-guides/decisions/rules)
