---
sidebar_position: 2
---

# Workflow Triggers

Learn about the different ways workflows can be triggered.

## Trigger Types

Workflows can be started by:

1. **Rule Match**: When a rule returns `REQUIRE_APPROVAL`
2. **Manual**: User explicitly starts a workflow
3. **Schedule**: Time-based triggers
4. **Webhook**: External system calls API
5. **Event**: Triggered by system events

## Rule Match Trigger

The most common trigger - when a decision rule evaluates to `REQUIRE_APPROVAL`.

### How It Works

```
Decision Request → Rule Evaluation → REQUIRE_APPROVAL → Workflow Created
```

### Configuration

In your rule action:
```json
{
  "type": "REQUIRE_APPROVAL",
  "workflow_template": "purchase-approval",
  "priority": "high",
  "context": {
    "forward_all": true
  }
}
```

### Context Passing

The workflow receives context from the decision:
```json
{
  "decision_id": "uuid",
  "decision_type": "expense_approval",
  "rule_id": "high-value-rule",
  "context": {
    "amount": 15000,
    "category": "equipment",
    "requester": {
      "email": "john@company.com",
      "manager": "jane@company.com"
    }
  }
}
```

## Manual Trigger

Users can manually start workflows.

### When to Use

- Ad-hoc approvals not covered by rules
- One-off requests
- Testing workflows

### Starting Manually

1. Go to **Workflow > Create**
2. Select workflow template
3. Fill in required context
4. Click **"Start Workflow"**

### API

```bash
curl -X POST https://api-puguh.atlashub.com/api/v1/workflows \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "purchase-approval",
    "context": {
      "amount": 5000,
      "description": "New laptop"
    }
  }'
```

## Schedule Trigger

Start workflows on a schedule.

### Use Cases

- Monthly expense reviews
- Quarterly access recertification
- Periodic compliance checks

### Configuration

```json
{
  "trigger": {
    "type": "schedule",
    "cron": "0 9 1 * *",
    "timezone": "Asia/Jakarta"
  },
  "workflow_template": "monthly-review"
}
```

### Cron Examples

| Schedule | Cron Expression |
|----------|-----------------|
| Daily at 9 AM | `0 9 * * *` |
| Weekly Monday | `0 9 * * 1` |
| Monthly 1st | `0 9 1 * *` |
| Quarterly | `0 9 1 1,4,7,10 *` |

## Webhook Trigger

External systems can trigger workflows via API.

### Webhook URL

```
POST https://api-puguh.atlashub.com/api/v1/webhooks/workflow
```

### Request Format

```json
{
  "webhook_secret": "your-webhook-secret",
  "template_id": "purchase-approval",
  "context": {
    "source": "erp-system",
    "amount": 25000,
    "po_number": "PO-12345"
  }
}
```

### Setting Up Webhooks

1. Go to **Tenant > Settings > Webhooks**
2. Click **"Create Webhook"**
3. Configure:
   - Name and description
   - Secret key (for verification)
   - Allowed templates
4. Copy the webhook URL

### Verifying Webhooks

PUGUH verifies webhook requests using HMAC:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Event Trigger

Triggered by internal system events.

### Available Events

| Event | Description |
|-------|-------------|
| `user.created` | New user registered |
| `user.role_changed` | User role updated |
| `rule.activated` | Rule went live |
| `decision.denied` | Decision was denied |

### Configuration

```json
{
  "trigger": {
    "type": "event",
    "events": ["user.role_changed"],
    "conditions": {
      "new_role": "admin"
    }
  },
  "workflow_template": "admin-access-review"
}
```

## Trigger Conditions

Add conditions to triggers:

### Filter by Context

Only trigger if conditions match:
```json
{
  "trigger": {
    "type": "rule_match",
    "conditions": {
      "context.department": "finance"
    }
  }
}
```

### Multiple Conditions

```json
{
  "conditions": {
    "all": [
      { "field": "context.amount", "operator": ">", "value": 10000 },
      { "field": "context.is_urgent", "operator": "=", "value": true }
    ]
  }
}
```

## Trigger Priority

When multiple templates could match:

```json
{
  "priority": 100,
  "trigger": {...}
}
```

Higher priority templates are selected first.

## Trigger History

View trigger history:

1. Go to **Workflow > Triggers**
2. See recent trigger events
3. Filter by:
   - Trigger type
   - Success/failure
   - Date range

## Debugging Triggers

### Trigger Not Firing?

1. **Check rule action**: Is it `REQUIRE_APPROVAL`?
2. **Verify template**: Does the template exist and is active?
3. **Check conditions**: Do trigger conditions match?
4. **Review logs**: Check audit trail for errors

### Unexpected Triggers?

1. **Check priority**: Higher priority rule/template winning?
2. **Verify conditions**: Conditions too broad?
3. **Review context**: What data is being passed?

## Best Practices

### 1. Be Specific
Use trigger conditions to avoid unwanted workflows.

### 2. Test First
Test triggers with sample data before production.

### 3. Monitor Volume
Watch for trigger storms during peak times.

### 4. Document Dependencies
Note which systems/rules trigger which workflows.

### 5. Handle Failures
Configure retry and fallback for webhook triggers.

## Related

- [Creating Workflows](/docs/user-guides/workflows/creating)
- [Monitoring Workflows](/docs/user-guides/workflows/monitoring)
- [Rules](/docs/user-guides/decisions/rules)
