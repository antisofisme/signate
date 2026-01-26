# Migration Guide: Leaving PUGUH

> **Easy to leave**: Your application, your data, your choice.

---

## Overview

We build PUGUH to earn your trust, not trap you. This guide explains exactly how to migrate away from PUGUH if you choose to do so.

**Estimated migration time**: 1-2 weeks for typical enterprise

---

## What You Keep

When you leave PUGUH, you take everything:

| Asset | Format | How to Export |
|-------|--------|---------------|
| Authorization rules | OpenFGA, JSON | Dashboard or API |
| Decision audit history | JSON, CSV | API bulk export |
| Workflow definitions | JSON, YAML | Dashboard or API |
| Role assignments | JSON | API export |
| Configuration | JSON | Settings export |

---

## Step 1: Export Your Data

### Export Rules (Authorization Model)

```bash
# Export as OpenFGA format (recommended for migration)
curl -X GET "https://api.puguh.io/v1/export/rules?format=openfga" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > rules-openfga.json

# Export as JSON (full detail)
curl -X GET "https://api.puguh.io/v1/export/rules?format=json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > rules-full.json
```

**OpenFGA format example:**

```json
{
  "schema_version": "1.1",
  "type_definitions": [
    {
      "type": "user"
    },
    {
      "type": "document",
      "relations": {
        "reader": {"this": {}},
        "writer": {"this": {}},
        "owner": {"this": {}}
      }
    }
  ]
}
```

### Export Decision Audit

```bash
# Export all decisions (can be large)
curl -X GET "https://api.puguh.io/v1/export/decisions?start=2024-01-01&end=2025-12-31" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > decisions-audit.json

# Export by date range for smaller files
curl -X GET "https://api.puguh.io/v1/export/decisions?start=2025-01-01&end=2025-01-31" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > decisions-2025-01.json
```

### Export Workflows

```bash
curl -X GET "https://api.puguh.io/v1/export/workflows" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > workflows.json
```

### Export Role Assignments

```bash
curl -X GET "https://api.puguh.io/v1/export/roles" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > role-assignments.json
```

---

## Step 2: Choose Your Target

### Option A: OpenFGA (Recommended)

OpenFGA is the open-source authorization system PUGUH is compatible with.

```bash
# Install OpenFGA
docker pull openfga/openfga
docker run -p 8080:8080 openfga/openfga run

# Import your rules
openfga-cli store create --name your-app
openfga-cli store import --file rules-openfga.json
```

**Pros:**
- Direct import of PUGUH rules
- Active open-source community
- Similar API surface

**Cons:**
- Self-hosted (you manage infrastructure)
- No built-in workflow automation

### Option B: Auth0 FGA

Auth0's managed FGA service (Zanzibar-based).

```bash
# Install CLI
npm install -g @auth0/fga-cli

# Import model
fga model write --file rules-openfga.json
```

**Pros:**
- Managed service (like PUGUH)
- Direct rule import

**Cons:**
- Different pricing model
- Fewer workflow features

### Option C: Ory Keto

Another Zanzibar implementation.

```bash
# Requires transformation of rules to Ory format
# Use our conversion tool:
puguh export --format ory-keto > rules-keto.json
```

**Pros:**
- Part of Ory ecosystem
- Open source

**Cons:**
- Different rule format (conversion needed)
- Self-hosted

### Option D: Build Your Own

If your needs are simple, you can implement authorization directly.

```python
# Simple RBAC implementation
class SimpleAuth:
    def __init__(self, rules: dict):
        self.rules = rules

    def check(self, actor: str, action: str, resource: str) -> bool:
        # Simple first-match evaluation
        for rule in self.rules:
            if self._matches(rule, actor, action, resource):
                return rule['decision'] == 'ALLOWED'
        return False  # Fail-closed
```

**Pros:**
- Full control
- No external dependency

**Cons:**
- No audit trail (you build it)
- No workflow automation
- Maintenance burden

---

## Step 3: Update Your Code

### Remove PUGUH SDK

#### Python

```python
# Before (PUGUH)
from puguh import Infra
infra = Infra(api_key="...", tenant_id="...")

result = infra.check(
    actor="user:alice",
    action="read",
    resource="document:123"
)

# After (OpenFGA)
from openfga_sdk import OpenFgaClient
client = OpenFgaClient(api_url="...")

result = client.check(
    user="user:alice",
    relation="reader",
    object="document:123"
)
```

#### TypeScript

```typescript
// Before (PUGUH)
import { Infra } from '@puguh/sdk';
const infra = new Infra({ apiKey: '...', tenantId: '...' });

const result = await infra.check({
  actor: 'user:alice',
  action: 'read',
  resource: 'document:123'
});

// After (OpenFGA)
import { OpenFgaClient } from '@openfga/sdk';
const client = new OpenFgaClient({ apiUrl: '...' });

const result = await client.check({
  user: 'user:alice',
  relation: 'reader',
  object: 'document:123'
});
```

### Mapping PUGUH to OpenFGA

| PUGUH Concept | OpenFGA Equivalent |
|---------------|-------------------|
| `actor` | `user` |
| `action` | `relation` |
| `resource` | `object` |
| `check()` | `check()` |
| `grant()` | `write()` with add |
| `revoke()` | `write()` with delete |

### Handle Missing Features

PUGUH features not in OpenFGA:

#### REQUIRE_APPROVAL (Workflows)

```python
# PUGUH handled this automatically
if result.decision == "REQUIRE_APPROVAL":
    workflow = infra.request_approval(...)

# With OpenFGA, you need separate workflow system
if needs_approval(actor, action, resource):
    # Use your own workflow engine (Temporal, AWS Step Functions, etc.)
    workflow = start_approval_workflow(...)
```

#### Audit Trail

```python
# PUGUH logged automatically
# With OpenFGA, add your own logging
def check_with_audit(user, relation, object):
    result = client.check(user=user, relation=relation, object=object)

    # Log to your audit system
    audit_log.record(
        actor=user,
        action=relation,
        resource=object,
        decision="ALLOWED" if result.allowed else "DENIED",
        timestamp=datetime.now()
    )

    return result
```

---

## Step 4: Migrate Incrementally

Don't do a big-bang migration. Use feature flags.

### Dual-Write Period

```python
class AuthorizationService:
    def __init__(self, use_puguh: bool = True):
        self.use_puguh = use_puguh
        self.puguh = Infra(...) if use_puguh else None
        self.openfga = OpenFgaClient(...) if not use_puguh else None

    def check(self, actor, action, resource):
        if self.use_puguh:
            result = self.puguh.check(actor, action, resource)
            return result.decision == "ALLOWED"
        else:
            result = self.openfga.check(
                user=actor,
                relation=action,
                object=resource
            )
            return result.allowed
```

### Migration Timeline

```
Week 1: Export all data from PUGUH
        Set up target system
        Run both in parallel (read from both, compare)

Week 2: Dual-write rules (create in both systems)
        Gradually shift read traffic to new system
        Monitor for discrepancies

Week 3: 100% traffic on new system
        PUGUH in read-only mode
        Final audit export

Week 4: Decommission PUGUH connection
        Archive final exports
        Update documentation
```

---

## Step 5: Verify Migration

### Rule Parity Check

```python
# Compare decisions between systems
test_cases = [
    ("user:alice", "read", "document:123"),
    ("user:bob", "write", "document:456"),
    # ... more test cases
]

for actor, action, resource in test_cases:
    puguh_result = puguh.check(actor, action, resource)
    openfga_result = openfga.check(user=actor, relation=action, object=resource)

    assert puguh_result.decision == ("ALLOWED" if openfga_result.allowed else "DENIED"), \
        f"Mismatch for {actor} {action} {resource}"
```

### Audit Trail Continuity

```python
# Import PUGUH audit history into new system
import json

with open('decisions-audit.json') as f:
    puguh_decisions = json.load(f)

for decision in puguh_decisions:
    new_audit_system.import_historical(
        timestamp=decision['evaluated_at'],
        actor=decision['actor'],
        action=decision['action'],
        resource=decision['resource'],
        decision=decision['decision'],
        source='puguh-migration'
    )
```

---

## Checklist

### Before Migration

- [ ] Export all rules (OpenFGA format)
- [ ] Export all decision history
- [ ] Export all workflow definitions
- [ ] Export all role assignments
- [ ] Document current rule count and decision volume
- [ ] Identify all services using PUGUH SDK

### During Migration

- [ ] Set up target authorization system
- [ ] Import rules to target system
- [ ] Update SDK in all services
- [ ] Run parallel comparison tests
- [ ] Monitor for decision discrepancies

### After Migration

- [ ] Verify 100% rule parity
- [ ] Archive audit history
- [ ] Update internal documentation
- [ ] Train team on new system
- [ ] Cancel PUGUH subscription

---

## Need Help?

Even though you're leaving, we're here to help:

| Support | Contact |
|---------|---------|
| Migration questions | support@example.com |
| Data export issues | support@example.com |
| Enterprise migration | enterprise@example.com |

We want your migration to be smooth. Your success matters, even if it's elsewhere.

---

## Why We Made This Easy

We believe:

1. **Trust is earned, not forced** - Lock-in breeds resentment
2. **Your data is yours** - Full export, standard formats
3. **Competition is healthy** - If someone builds better, use it
4. **Relationships matter** - You might come back someday

**Easy to leave. Hard to want to leave.**

---

## Coming Back?

If you decide to return:

```bash
# Re-import your rules
curl -X POST "https://api.puguh.io/v1/import/rules" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @rules-openfga.json

# We'll have you back up in minutes
```

Welcome back anytime.
