---
sidebar_position: 1
---

# Creating Workflows

Learn how to create and configure approval workflows.

## What are Workflows?

Workflows are automated approval processes that route decisions to the right people for review and action. When a rule triggers `REQUIRE_APPROVAL`, a workflow is created.

## Workflow Components

### Stages
Steps in the approval process:
- Manager approval
- Finance review
- Final sign-off

### Participants
Who can take action:
- Specific users
- Role-based (any admin)
- Dynamic (requester's manager)

### Transitions
How workflows move between stages:
- Approved → next stage
- Rejected → end
- Delegated → reassigned
- Escalated → higher authority

## Creating a Workflow Template

### Step 1: Navigate

1. Go to **Workflow > Templates**
2. Click **"Create Template"**

### Step 2: Basic Info

```
Name: Purchase Approval Flow
Description: Multi-level approval for purchases
Trigger: When rules return REQUIRE_APPROVAL
```

### Step 3: Define Stages

Add stages in order of execution:

```
Stage 1: Manager Review
├── Participants: requester.manager
├── Timeout: 24 hours
└── On Timeout: Escalate

Stage 2: Finance Approval (if amount > 10000)
├── Participants: role:finance-admin
├── Timeout: 48 hours
└── On Timeout: Auto-reject

Stage 3: Executive Sign-off (if amount > 50000)
├── Participants: user:cfo@company.com
├── Timeout: 72 hours
└── On Timeout: Escalate to CEO
```

### Step 4: Configure Notifications

```yaml
notifications:
  on_created:
    - to: participants
      template: workflow-created
  on_pending:
    - to: next_approver
      template: approval-needed
  on_approved:
    - to: requester
      template: request-approved
  on_rejected:
    - to: requester
      template: request-rejected
```

### Step 5: Save Template

Click **"Save Template"** to create.

## Workflow Template JSON

Complete template structure:

```json
{
  "name": "Purchase Approval Flow",
  "description": "Multi-level approval for purchases",
  "stages": [
    {
      "name": "Manager Review",
      "order": 1,
      "participants": {
        "type": "dynamic",
        "expression": "context.requester.manager"
      },
      "timeout": {
        "duration": "24h",
        "action": "escalate"
      },
      "conditions": null
    },
    {
      "name": "Finance Approval",
      "order": 2,
      "participants": {
        "type": "role",
        "role": "finance-admin"
      },
      "timeout": {
        "duration": "48h",
        "action": "reject"
      },
      "conditions": {
        "field": "context.amount",
        "operator": "greater_than",
        "value": 10000
      }
    }
  ],
  "notifications": {
    "on_created": ["participants"],
    "on_approved": ["requester"],
    "on_rejected": ["requester"]
  }
}
```

## Participant Types

### Static User
Specific user by email:
```json
{
  "type": "user",
  "email": "cfo@company.com"
}
```

### Role-Based
Any user with a specific role:
```json
{
  "type": "role",
  "role": "finance-admin"
}
```

### Dynamic
Computed from context:
```json
{
  "type": "dynamic",
  "expression": "context.requester.manager"
}
```

### Group
Multiple users (any can approve):
```json
{
  "type": "group",
  "users": ["alice@co.com", "bob@co.com", "carol@co.com"],
  "require": "any"
}
```

### Sequential
Multiple users (all must approve):
```json
{
  "type": "group",
  "users": ["alice@co.com", "bob@co.com"],
  "require": "all"
}
```

## Stage Conditions

Make stages conditional:

### Skip If
Skip stage if condition is true:
```json
{
  "skip_if": {
    "field": "context.is_pre_approved",
    "operator": "equals",
    "value": true
  }
}
```

### Only If
Only run stage if condition is true:
```json
{
  "only_if": {
    "field": "context.amount",
    "operator": "greater_than",
    "value": 50000
  }
}
```

## Timeout Actions

What happens when a stage times out:

| Action | Description |
|--------|-------------|
| `escalate` | Move to escalation flow |
| `reject` | Auto-reject the workflow |
| `remind` | Send reminder, extend timeout |
| `skip` | Skip to next stage |
| `custom` | Call webhook |

## Linking to Rules

Connect workflows to rules:

### In Rule Builder
1. Set action to `REQUIRE_APPROVAL`
2. Select workflow template
3. Save rule

### In Workflow Template
1. Add trigger conditions
2. Specify which decision types use this workflow

## Testing Workflows

### Dry Run
Test without creating real workflow:
1. Open workflow template
2. Click **"Test"**
3. Enter sample context
4. See simulated execution

### Preview Stages
See which stages would activate:
```json
{
  "context": {
    "amount": 75000,
    "requester": { "manager": "jane@co.com" }
  }
}
```

Result:
```
Stage 1: Manager Review ✓ (jane@co.com)
Stage 2: Finance Approval ✓ (amount > 10000)
Stage 3: Executive Sign-off ✓ (amount > 50000)
```

## Best Practices

### 1. Keep It Simple
Start with fewer stages, add complexity as needed.

### 2. Set Reasonable Timeouts
Not too short (people need time) or too long (delays decisions).

### 3. Use Clear Names
"Manager Review" not "Stage 1".

### 4. Document Conditions
Explain why each stage exists.

### 5. Test Thoroughly
Test all paths through the workflow.

### 6. Monitor Performance
Track approval times and bottlenecks.

## Common Patterns

### Two-Level Approval
```
1. Direct Manager → 2. Department Head
```

### Threshold-Based
```
< $1000: Auto-approve
$1000-$10000: Manager only
> $10000: Manager + Finance
```

### Parallel Approval
```
Both Legal AND Finance must approve
```

### Hierarchical Escalation
```
Manager → Director → VP → CEO
```

## Related

- [Workflow Triggers](/docs/user-guides/workflows/triggers)
- [Monitoring Workflows](/docs/user-guides/workflows/monitoring)
- [Rules](/docs/user-guides/decisions/rules)
