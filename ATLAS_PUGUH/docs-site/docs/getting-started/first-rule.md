---
sidebar_position: 4
---

# Create Your First Rule

**Rules** are the heart of ATLAS PUGUH. They define the logic that governs your decisions, specifying conditions and actions.

## Understanding Rules

A rule consists of:

- **Conditions**: When should this rule apply? (e.g., `amount > 1000`)
- **Actions**: What happens when conditions are met? (e.g., `require_approval`)
- **Priority**: When multiple rules match, which one takes precedence?

## Creating a Rule

### Step 1: Navigate to Rules

1. Go to **Decision > Rules** in the sidebar
2. Click **"New Rule"** button

### Step 2: Basic Information

Fill in the rule metadata:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Descriptive rule name | "High Value Purchase Approval" |
| **Description** | What this rule does | "Requires manager approval for purchases over $5,000" |
| **Decision Type** | What kind of decision | "expense_approval" |
| **Priority** | Higher = evaluated first | 100 |
| **Scope** | Tenant-wide or project only | Project |

### Step 3: Define Conditions

Use our condition builder to specify when the rule applies:

```
IF amount > 5000
AND category = "equipment"
AND requester.department != "executive"
```

**Condition Builder UI:**

1. Click **"Add Condition"**
2. Select the field: `amount`
3. Choose operator: `greater than`
4. Enter value: `5000`
5. Add more conditions with AND/OR logic

### Step 4: Define Actions

Specify what happens when conditions match:

| Action Type | Description |
|-------------|-------------|
| `ALLOW` | Approve immediately |
| `DENY` | Reject immediately |
| `REQUIRE_APPROVAL` | Route to workflow |
| `FLAG` | Flag for review |
| `CUSTOM` | Execute custom logic |

For our example, select **REQUIRE_APPROVAL** and configure:

```json
{
  "workflow_id": "manager-approval",
  "priority": "high",
  "reason": "High value purchase requires manager approval"
}
```

### Step 5: Save and Test

1. Click **"Save Draft"** - the rule is saved but not active
2. Click **"Test Rule"** to verify with sample data:

```json
{
  "amount": 7500,
  "category": "equipment",
  "requester": {
    "email": "john@example.com",
    "department": "engineering"
  }
}
```

3. Review the test result - it should show `REQUIRE_APPROVAL`

### Step 6: Activate the Rule

Once tested:

1. Click **"Request Activation"**
2. An admin will review and approve the rule
3. Once approved, the rule goes live

## Rule Example: Complete JSON

Here's the complete rule as JSON:

```json
{
  "name": "High Value Purchase Approval",
  "description": "Requires manager approval for purchases over $5,000",
  "decision_type": "expense_approval",
  "priority": 100,
  "status": "active",
  "conditions": {
    "all": [
      {
        "field": "amount",
        "operator": "greater_than",
        "value": 5000
      },
      {
        "field": "category",
        "operator": "equals",
        "value": "equipment"
      },
      {
        "field": "requester.department",
        "operator": "not_equals",
        "value": "executive"
      }
    ]
  },
  "actions": {
    "type": "REQUIRE_APPROVAL",
    "config": {
      "workflow_id": "manager-approval",
      "priority": "high"
    }
  }
}
```

## Condition Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `status = "pending"` |
| `not_equals` | Not equal | `status != "approved"` |
| `greater_than` | Numeric > | `amount > 1000` |
| `less_than` | Numeric < | `amount < 100` |
| `greater_than_or_equals` | Numeric >= | `amount >= 1000` |
| `less_than_or_equals` | Numeric <= | `amount <= 100` |
| `contains` | String contains | `email contains "@company"` |
| `starts_with` | String prefix | `code starts_with "EXP-"` |
| `ends_with` | String suffix | `email ends_with ".com"` |
| `in` | Value in list | `department in ["eng", "product"]` |
| `not_in` | Value not in list | `status not_in ["rejected", "cancelled"]` |
| `is_null` | Value is null | `manager_id is_null` |
| `is_not_null` | Value exists | `approval_date is_not_null` |

## Logical Operators

Combine conditions with:

```json
{
  "all": [...],  // AND - all conditions must be true
  "any": [...],  // OR - at least one must be true
  "not": {...}   // NOT - negate a condition
}
```

**Complex Example:**

```json
{
  "all": [
    { "field": "amount", "operator": "greater_than", "value": 1000 },
    {
      "any": [
        { "field": "department", "operator": "equals", "value": "sales" },
        { "field": "is_urgent", "operator": "equals", "value": true }
      ]
    }
  ]
}
```

This matches: `amount > 1000 AND (department = "sales" OR is_urgent = true)`

## Rule Lifecycle

```
DRAFT → PENDING_REVIEW → ACTIVE
                      ↘ REJECTED

ACTIVE → DEPRECATED → ARCHIVED
```

| Status | Description |
|--------|-------------|
| `DRAFT` | Being edited, not evaluated |
| `PENDING_REVIEW` | Submitted for approval |
| `ACTIVE` | Live and evaluating decisions |
| `REJECTED` | Review failed, needs revision |
| `DEPRECATED` | Being phased out |
| `ARCHIVED` | No longer in use |

## Best Practices

1. **Start Simple**: Begin with basic conditions, add complexity as needed
2. **Use Priorities**: Higher priority rules override lower ones
3. **Test Thoroughly**: Always test with edge cases before activating
4. **Document Well**: Clear descriptions help future maintainers
5. **Version Control**: Use rule versions for major changes

## Next Steps

With your first rule created:

- [Learn the Rule Builder](/docs/user-guides/decisions/rule-builder) for advanced features
- [Set up Testing](/docs/user-guides/decisions/testing) for comprehensive validation
- [Understand Versioning](/docs/user-guides/decisions/versioning) for change management
