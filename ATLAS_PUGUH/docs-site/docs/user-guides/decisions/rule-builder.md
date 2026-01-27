---
sidebar_position: 2
---

# Rule Builder

Use the visual rule builder to create conditions without writing code.

## Opening the Rule Builder

1. Navigate to **Decision > Rules**
2. Click **"New Rule"** or edit an existing rule
3. The rule builder opens automatically

## Builder Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  Rule Name: [___________________________________]               │
│  Description: [___________________________________]             │
│  Decision Type: [Dropdown ▼]    Priority: [___]                │
├─────────────────────────────────────────────────────────────────┤
│  CONDITIONS                                               [+ADD]│
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ○ ALL of the following (AND)                             │  │
│  │   ┌────────────────────────────────────────────────────┐ │  │
│  │   │ Field: [amount ▼]  Operator: [> ▼]  Value: [5000] │ │  │
│  │   └────────────────────────────────────────────────────┘ │  │
│  │   ┌────────────────────────────────────────────────────┐ │  │
│  │   │ Field: [category ▼] Operator: [= ▼] Value: [equip]│ │  │
│  │   └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ACTIONS                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Action Type: [REQUIRE_APPROVAL ▼]                        │  │
│  │ Workflow: [manager-approval ▼]                           │  │
│  │ Priority: [High ▼]                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        [TEST RULE]  [SAVE DRAFT]  [SUBMIT]      │
└─────────────────────────────────────────────────────────────────┘
```

## Building Conditions

### Adding a Condition

1. Click **"+ Add Condition"**
2. Select the field from dropdown
3. Choose an operator
4. Enter the value

### Condition Fields

Fields are derived from your decision context schema:

| Field Type | Examples |
|------------|----------|
| Number | `amount`, `quantity`, `score` |
| String | `category`, `department`, `status` |
| Boolean | `is_urgent`, `is_approved`, `has_manager` |
| Date | `created_at`, `due_date` |
| Nested | `requester.role`, `item.category` |

### Operators

#### Comparison Operators

| Operator | Symbol | Works With |
|----------|--------|------------|
| Equals | `=` | All types |
| Not equals | `!=` | All types |
| Greater than | `>` | Numbers, Dates |
| Less than | `<` | Numbers, Dates |
| Greater or equal | `>=` | Numbers, Dates |
| Less or equal | `<=` | Numbers, Dates |

#### String Operators

| Operator | Example |
|----------|---------|
| Contains | `email contains "@company.com"` |
| Starts with | `code starts_with "EXP-"` |
| Ends with | `name ends_with "Inc"` |
| Matches regex | `phone matches "^\+1"` |

#### List Operators

| Operator | Example |
|----------|---------|
| In | `department in ["sales", "marketing"]` |
| Not in | `status not_in ["cancelled", "rejected"]` |
| Contains any | `tags contains_any ["urgent", "priority"]` |
| Contains all | `roles contains_all ["admin", "reviewer"]` |

#### Null Operators

| Operator | Example |
|----------|---------|
| Is null | `manager is_null` |
| Is not null | `approval_date is_not_null` |

### Logical Operators

#### ALL (AND)

All conditions must be true:

```
ALL of:
├── amount > 1000
├── department = "engineering"
└── is_approved = false

Result: True only if ALL three are true
```

#### ANY (OR)

At least one condition must be true:

```
ANY of:
├── is_urgent = true
├── priority = "critical"
└── escalated = true

Result: True if ANY one is true
```

#### NOT

Negates a condition:

```
NOT:
└── status = "exempt"

Result: True if status is NOT "exempt"
```

### Nested Conditions

Combine logical operators for complex rules:

```
ALL of:
├── amount > 5000
└── ANY of:
    ├── department = "sales"
    ├── is_executive = true
    └── has_pre_approval = true
```

This means: Amount over $5000 AND (sales department OR executive OR pre-approved)

## Configuring Actions

### Action Types

#### ALLOW
Immediately approve the decision.

```
Action: ALLOW
No additional configuration needed
```

#### DENY
Immediately reject the decision.

```
Action: DENY
Reason: "Amount exceeds policy limit"
```

#### REQUIRE_APPROVAL
Route to a workflow for human approval.

```
Action: REQUIRE_APPROVAL
Workflow: manager-approval
Priority: high
Notify: requester.manager
```

#### FLAG
Flag for review but don't block.

```
Action: FLAG
Reason: "Unusual pattern detected"
Tags: ["review", "compliance"]
```

#### CUSTOM
Execute custom logic via webhook.

```
Action: CUSTOM
Webhook: https://api.example.com/custom-handler
Headers: { "X-API-Key": "..." }
Payload: { "rule_id": "...", "context": {...} }
```

### Action Configuration

Click on the action to configure details:

| Field | Description |
|-------|-------------|
| **Workflow** | Which workflow to use (REQUIRE_APPROVAL) |
| **Priority** | Workflow priority (low/medium/high) |
| **Notify** | Who to notify |
| **Reason** | Explanation shown to user |
| **Tags** | Labels for filtering |
| **Metadata** | Custom data passed through |

## Testing Your Rule

Before activating, test with sample data:

### Using the Test Panel

1. Click **"Test Rule"** button
2. Enter sample JSON data:

```json
{
  "amount": 7500,
  "category": "equipment",
  "department": "engineering",
  "requester": {
    "email": "john@example.com",
    "role": "manager"
  }
}
```

3. Click **"Run Test"**
4. See the result:
   - Which conditions matched/failed
   - Final action that would be taken
   - Any warnings or notes

### Test Scenarios

Save test scenarios for regression testing:

1. Create tests for expected matches
2. Create tests for expected non-matches
3. Test edge cases (boundaries, nulls)
4. Run all tests when making changes

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save draft |
| `Ctrl+Enter` | Run test |
| `Ctrl+/` | Toggle comment |
| `Tab` | Next field |
| `Escape` | Close modal |

## Tips & Tricks

### Use Descriptive Names
Bad: "Rule 1"
Good: "High Value Equipment Requires CFO Approval"

### Start Simple
Build incrementally - start with one condition, test, add more.

### Check Priority
Verify your rule won't be overridden by a higher-priority rule.

### Document Reasoning
Use the description field to explain WHY, not just WHAT.

### Version Carefully
Each save creates a new version - make meaningful changes.

## Common Mistakes

### Wrong Operator
Using `=` for partial match instead of `contains`.

### Missing Negation
Forgetting to check for null values.

### Priority Conflicts
Two rules with same priority causing unpredictable behavior.

### Over-Engineering
Creating complex rules when simple ones would work.

## Related

- [Rules Overview](/docs/user-guides/decisions/rules)
- [Testing Rules](/docs/user-guides/decisions/testing)
- [Versioning](/docs/user-guides/decisions/versioning)
