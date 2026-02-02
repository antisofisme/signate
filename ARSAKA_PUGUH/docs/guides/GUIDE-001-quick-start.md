# Quick Start Guide

> **Your first authorization check in 5 minutes.**

---

## Prerequisites

- Python 3.9+ or Node.js 18+
- PUGUH API key (get one at dashboard)
- 5 minutes

---

## Step 1: Install SDK

### Python

```bash
pip install puguh-sdk
```

### TypeScript

```bash
npm install @puguh/sdk
# or
bun add @puguh/sdk
```

---

## Step 2: Initialize Client

### Python

```python
from puguh import Infra

infra = Infra(
    api_key="your-api-key",
    tenant_id="your-tenant-id"
)
```

### TypeScript

```typescript
import { Infra } from '@puguh/sdk';

const infra = new Infra({
  apiKey: 'your-api-key',
  tenantId: 'your-tenant-id'
});
```

---

## Step 3: First Authorization Check

### The Basics

```python
# Check if alice can read budget document
result = infra.check(
    actor="user:alice",
    action="read",
    resource="document:budget-2025"
)

print(result.decision)  # ALLOWED, DENIED, or REQUIRE_APPROVAL
```

### Understanding the Response

```python
# Full response structure
{
    "decision": "ALLOWED",       # or DENIED, REQUIRE_APPROVAL
    "decision_id": "dec-123",    # For audit trail
    "evaluated_at": "2025-01-24T10:00:00Z",
    "matched_rule": "rule-456",  # Which rule matched
    "context": {
        "actor_roles": ["employee", "finance-team"],
        "resource_owner": "finance-dept"
    }
}
```

---

## Step 4: Handle Different Decisions

```python
result = infra.check(
    actor="user:alice",
    action="approve",
    resource="expense:EXP-789"
)

if result.decision == "ALLOWED":
    # Proceed with the action
    approve_expense("EXP-789")

elif result.decision == "DENIED":
    # Show error to user
    raise PermissionError(f"Access denied: {result.reason}")

elif result.decision == "REQUIRE_APPROVAL":
    # Start approval workflow
    workflow = infra.request_approval(
        decision_id=result.decision_id,
        requester="user:alice",
        context={"expense_id": "EXP-789", "amount": 5000}
    )
    # Notify user that approval is pending
    notify_user_approval_pending(workflow.id)
```

---

## Step 5: Define Your First Rule

### Using the Dashboard

1. Go to **Rules** → **Create Rule**
2. Fill in:
   - **Actor**: `user:*` (all users)
   - **Action**: `read`
   - **Resource**: `document:public-*`
   - **Decision**: `ALLOWED`
3. Click **Save**

### Using the API

```python
# Create a rule via API
infra.admin.create_rule(
    actor="user:*",
    action="read",
    resource="document:public-*",
    decision="ALLOWED",
    description="All users can read public documents"
)
```

---

## Common Patterns

### Role-Based Access

```python
# Define role-based rules
infra.admin.create_rule(
    actor="role:finance-manager",
    action="approve",
    resource="expense:*",
    decision="ALLOWED"
)

infra.admin.create_rule(
    actor="role:employee",
    action="create",
    resource="expense:*",
    decision="ALLOWED"
)

# Assign role to user
infra.admin.grant_role(
    user="user:bob",
    role="finance-manager"
)
```

### Attribute-Based Access

```python
# Rule with conditions
infra.admin.create_rule(
    actor="user:*",
    action="approve",
    resource="expense:*",
    decision="REQUIRE_APPROVAL",
    condition="resource.amount > 1000"
)
```

### Approval Workflow

```python
# Create approval workflow
infra.admin.create_workflow(
    name="expense-approval",
    trigger={
        "action": "approve",
        "resource": "expense:*",
        "condition": "resource.amount > 5000"
    },
    steps=[
        {
            "approver": "user:direct-manager",
            "timeout": "24h"
        },
        {
            "approver": "role:finance-head",
            "timeout": "48h"
        }
    ]
)
```

---

## Integration Example

### FastAPI

```python
from fastapi import FastAPI, HTTPException, Depends
from puguh import Infra

app = FastAPI()
infra = Infra(api_key="...", tenant_id="...")

def check_permission(actor: str, action: str, resource: str):
    result = infra.check(actor=actor, action=action, resource=resource)
    if result.decision == "DENIED":
        raise HTTPException(status_code=403, detail=result.reason)
    if result.decision == "REQUIRE_APPROVAL":
        raise HTTPException(status_code=202, detail={
            "message": "Approval required",
            "workflow_id": result.workflow_id
        })
    return result

@app.get("/documents/{doc_id}")
def get_document(doc_id: str, current_user: str = Depends(get_current_user)):
    check_permission(
        actor=f"user:{current_user}",
        action="read",
        resource=f"document:{doc_id}"
    )
    return get_document_from_db(doc_id)
```

### Express.js

```typescript
import express from 'express';
import { Infra } from '@puguh/sdk';

const app = express();
const infra = new Infra({ apiKey: '...', tenantId: '...' });

const checkPermission = async (actor: string, action: string, resource: string) => {
  const result = await infra.check({ actor, action, resource });
  if (result.decision === 'DENIED') {
    throw { status: 403, message: result.reason };
  }
  if (result.decision === 'REQUIRE_APPROVAL') {
    throw { status: 202, message: 'Approval required', workflowId: result.workflowId };
  }
  return result;
};

app.get('/documents/:docId', async (req, res) => {
  const { docId } = req.params;
  const { userId } = req.user;

  await checkPermission(`user:${userId}`, 'read', `document:${docId}`);

  const doc = await getDocumentFromDb(docId);
  res.json(doc);
});
```

---

## Testing Your Integration

### Check Authorization

```bash
# Using CLI
puguh check --actor user:alice --action read --resource document:test

# Response
{
  "decision": "ALLOWED",
  "decision_id": "dec-2025-01-24-001"
}
```

### View Audit Log

```bash
# Recent decisions
puguh audit list --limit 10

# Specific decision
puguh audit get dec-2025-01-24-001
```

### Debug Rule Evaluation

```bash
# See which rules were evaluated
puguh check --actor user:alice --action read --resource document:test --debug

# Response includes:
# - All rules evaluated
# - Which rule matched
# - Why others didn't match
```

---

## Next Steps

### 1. Define Your Authorization Model

- What actors exist? (users, services, roles)
- What actions are possible? (read, write, approve, delete)
- What resources need protection? (documents, orders, configs)

### 2. Create Rules

Start with broad rules, then add specific ones:

```python
# Broad: Deny all by default (fail-closed)
# This is the default behavior, no rule needed

# Specific: Allow certain actors
infra.admin.create_rule(
    actor="role:admin",
    action="*",
    resource="*",
    decision="ALLOWED"
)
```

### 3. Set Up Workflows

For actions that need approval:

```python
infra.admin.create_workflow(
    name="sensitive-data-access",
    trigger={"resource": "data:sensitive-*"},
    steps=[{"approver": "role:security-team"}]
)
```

### 4. Monitor & Audit

- Check the dashboard for decision patterns
- Set up alerts for denied access spikes
- Review access periodically

---

## Getting Help

| Resource | URL |
|----------|-----|
| Documentation | `/docs` in your instance |
| API Reference | `/api/docs` (OpenAPI) |
| Dashboard | Your PUGUH dashboard URL |
| Support | support@example.com |

---

## Quick Reference

### SDK Methods

```python
# Core methods
infra.check(actor, action, resource)        # Check authorization
infra.request_approval(decision_id, ...)    # Start workflow
infra.get_approval_status(workflow_id)      # Check workflow status

# Admin methods (require admin API key)
infra.admin.create_rule(...)                # Create rule
infra.admin.update_rule(...)                # Update rule
infra.admin.delete_rule(...)                # Delete rule
infra.admin.grant_role(...)                 # Grant role to user
infra.admin.revoke_role(...)                # Revoke role
infra.admin.create_workflow(...)            # Create workflow
```

### Decision Types

| Decision | Meaning | Your Action |
|----------|---------|-------------|
| `ALLOWED` | Permission granted | Proceed |
| `DENIED` | Permission denied | Block, show reason |
| `REQUIRE_APPROVAL` | Needs workflow | Start approval flow |

---

**You're ready to go. Happy authorizing!**
