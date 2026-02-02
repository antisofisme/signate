---
sidebar_position: 1
---

# Rules Overview

Learn about rules in ATLAS PUGUH's decision engine.

## What are Rules?

Rules are the core building blocks of PUGUH's decision engine. They define:

- **When** something should happen (conditions)
- **What** should happen (actions)
- **Priority** when multiple rules match

## Rule Components

### Conditions

Conditions determine if a rule applies to a given context:

```json
{
  "all": [
    { "field": "amount", "operator": "greater_than", "value": 1000 },
    { "field": "category", "operator": "equals", "value": "equipment" }
  ]
}
```

### Actions

Actions define what happens when conditions match:

| Action | Description |
|--------|-------------|
| `ALLOW` | Approve immediately |
| `DENY` | Reject immediately |
| `REQUIRE_APPROVAL` | Route to workflow |
| `FLAG` | Flag for review |
| `CUSTOM` | Custom action handler |

### Priority

When multiple rules match, higher priority rules win:
- Priority 100 > Priority 50
- Equal priorities evaluated in order of creation

## Rule Lifecycle

```
┌─────────┐    Submit    ┌─────────────────┐
│  DRAFT  │ ──────────►  │ PENDING_REVIEW  │
└─────────┘              └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │ Approved   │ Rejected   │
                    ▼            │            ▼
              ┌──────────┐      │       ┌──────────┐
              │  ACTIVE  │      │       │ REJECTED │
              └──────────┘      │       └──────────┘
                    │           │
                    ▼           │
              ┌──────────────┐  │
              │ DEPRECATED   │  │
              └──────────────┘  │
                    │           │
                    ▼           │
              ┌──────────────┐  │
              │  ARCHIVED    │◄─┘
              └──────────────┘
```

### Draft

- Rule is being created or edited
- Not evaluated in decisions
- Can be modified freely

### Pending Review

- Submitted for activation
- Awaiting admin approval
- Cannot be edited while pending

### Active

- Live and evaluating decisions
- Changes require new version
- Can be deprecated

### Deprecated

- Still evaluating but being phased out
- Warning shown in dashboard
- Should migrate to replacement

### Archived

- No longer evaluated
- Kept for audit purposes
- Cannot be reactivated

## Viewing Rules

Navigate to **Decision > Rules** to see all rules.

### Rule List Columns

| Column | Description |
|--------|-------------|
| Name | Rule identifier |
| Decision Type | What kind of decision |
| Status | Current lifecycle state |
| Priority | Evaluation order |
| Version | Current version number |
| Updated | Last modification date |

### Filtering Rules

- **By Status**: Draft, Active, etc.
- **By Decision Type**: Filter by category
- **By Project**: Tenant-wide or project-specific
- **Search**: Find by name or description

## Rule Details

Click a rule to view its details:

### Overview Tab
- Name, description, status
- Decision type and priority
- Created/updated timestamps

### Conditions Tab
- Visual condition tree
- Condition logic explanation
- Test with sample data

### Actions Tab
- Action configuration
- Workflow routing (if applicable)
- Custom action parameters

### History Tab
- All versions with changes
- Who made each change
- Restore previous versions

## Rule Scoping

Rules can be scoped at two levels:

### Tenant-Level Rules
- Apply to all projects in tenant
- Company-wide policies
- Higher precedence option

### Project-Level Rules
- Only apply within one project
- Environment-specific logic
- Can override tenant rules

:::tip
Use tenant-level rules for organization-wide policies and project-level rules for environment-specific overrides.
:::

## Decision Types

Rules are organized by decision type:

```
Decision Type: "expense_approval"
└── Rule: "High value requires approval" (priority 100)
└── Rule: "Executive exemption" (priority 200)
└── Rule: "Default allow under $500" (priority 10)
```

Create decision types at **Decision > Types**.

## Best Practices

### Naming
- Use descriptive names: "High Value Equipment Approval"
- Include the primary condition: "Over $5000 Requires CFO"
- Avoid generic names: "Rule 1", "Test Rule"

### Organization
- Group related rules by decision type
- Use consistent priority ranges
- Document the purpose

### Testing
- Always test rules before activation
- Use edge cases in tests
- Verify priority ordering

### Maintenance
- Review rules quarterly
- Archive unused rules
- Keep descriptions updated

## Common Patterns

### Threshold-Based Approval

```json
{
  "name": "Manager approval for high amounts",
  "conditions": {
    "field": "amount",
    "operator": "greater_than",
    "value": 5000
  },
  "action": {
    "type": "REQUIRE_APPROVAL",
    "workflow": "manager-approval"
  },
  "priority": 100
}
```

### Role-Based Exception

```json
{
  "name": "Executive bypass",
  "conditions": {
    "field": "requester.role",
    "operator": "equals",
    "value": "executive"
  },
  "action": {
    "type": "ALLOW"
  },
  "priority": 200
}
```

### Multi-Condition Logic

```json
{
  "name": "Urgent equipment in engineering",
  "conditions": {
    "all": [
      { "field": "is_urgent", "operator": "equals", "value": true },
      { "field": "category", "operator": "equals", "value": "equipment" },
      { "field": "department", "operator": "equals", "value": "engineering" }
    ]
  },
  "action": {
    "type": "FLAG",
    "reason": "Urgent equipment request needs quick review"
  },
  "priority": 150
}
```

## Related

- [Rule Builder](/docs/user-guides/decisions/rule-builder)
- [Testing Rules](/docs/user-guides/decisions/testing)
- [Versioning](/docs/user-guides/decisions/versioning)
