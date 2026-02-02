# Why PUGUH?

> **PUGUH**: Enterprise Authorization Engine with Workflow Automation

---

## The Problem: Authorization Chaos

Every enterprise application needs authorization:

```
"Can Alice approve this purchase order?"
"Is Bob allowed to view salary data?"
"Who can deploy to production on weekends?"
"Why was that access denied last week?"
"Are we compliant with our own policies?"
```

**Without centralized authorization:**

| Problem | Consequence |
|---------|-------------|
| Scattered rules | Authorization logic duplicated across services |
| No audit trail | "Who approved this?" - Nobody knows |
| Inconsistent enforcement | Same rule, different results |
| Policy drift | Rules change without documentation |
| Compliance gaps | Can't prove who had access when |

---

## The PUGUH Solution

PUGUH is an **authorization engine** that centralizes all access decisions with full audit trail and workflow automation.

### Core Capabilities

| Capability | What It Does |
|------------|--------------|
| **Centralized Rules** | All authorization rules in one place |
| **Decision Audit** | Every ALLOWED/DENIED logged with context |
| **Workflow Automation** | Approval chains, escalations, timeouts |
| **Real-time Evaluation** | Sub-millisecond decision latency |
| **Multi-tenant** | Complete data isolation per tenant |

### The Three Decisions

Every authorization request gets one of three outcomes:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ALLOWED   │    │   DENIED    │    │  REQUIRE    │
│             │    │             │    │  APPROVAL   │
│  Proceed    │    │  Stop       │    │  Start      │
│  immediately│    │  immediately│    │  workflow   │
└─────────────┘    └─────────────┘    └─────────────┘
```

No ambiguity. No "maybe." No undefined behavior.

---

## Integration Model: SDK + Engine

PUGUH has two parts:

### 1. SDK (In Your Code)

```python
from puguh import Infra

infra = Infra(api_key="...")

# Check authorization
result = infra.check(
    actor="user:alice",
    action="approve",
    resource="purchase:PO-123"
)

if result.decision == "ALLOWED":
    # Proceed
elif result.decision == "DENIED":
    # Stop, show reason
elif result.decision == "REQUIRE_APPROVAL":
    # Start workflow, wait for approval
    approval = infra.request_approval(result.workflow_id)
```

### 2. Engine (Hosted Service)

The engine handles:
- Rule evaluation
- Decision logging
- Workflow orchestration
- Tenant isolation
- Audit storage

Your application only sees the SDK. The engine is invisible.

---

## Easy to Leave

We believe in earning your trust, not trapping you.

### Standard Interfaces

PUGUH uses **OpenFGA-compatible** authorization model:

```yaml
# Your rules are portable
type user
type document
  relations
    define reader: [user]
    define writer: [user]
    define owner: [user]
```

If you leave PUGUH, your authorization model works with:
- OpenFGA (open source)
- Auth0 FGA
- Ory Keto
- Any Zanzibar-based system

### Thin SDK

The PUGUH SDK is intentionally minimal:

```python
# Only 4 core methods
infra.check()           # Check authorization
infra.request_approval() # Start workflow
infra.grant()           # Grant permission (admin)
infra.revoke()          # Revoke permission (admin)
```

Replacing it requires ~50 lines of wrapper code per service.

### Full Data Export

```bash
# Export all rules
GET /api/v1/export/rules?format=openfga

# Export all decisions (audit)
GET /api/v1/export/decisions?start=2025-01-01&end=2025-12-31

# Export all workflows
GET /api/v1/export/workflows?format=json
```

You keep:
- Authorization model (portable)
- All decision history
- Workflow definitions
- Audit trail

### What Happens If You Leave

| Aspect | Impact |
|--------|--------|
| Your application | Keeps running (swap SDK for another) |
| Your rules | Portable to OpenFGA-compatible systems |
| Your audit data | Exported, yours to keep |
| Migration effort | ~1-2 weeks for typical enterprise |

---

## Hard to Want to Leave

### 1. Decision Intelligence

After 6 months of PUGUH:

```
"Why was Alice denied access to that report?"
→ Decision ID: dec-2025-01-24-12345
  Denied by rule: "reports.salary requires HR role"
  Alice's roles: [engineering, project-lead]
  Missing: HR role
  Suggested action: Request HR role or ask manager to approve

"Who can access production database?"
→ 15 users with direct access
→ 23 users via role inheritance
→ 3 service accounts
→ Last access audit: 2025-01-20
```

Without PUGUH, this information lives in:
- Code comments (maybe)
- Slack threads (lost)
- People's heads (they left)

### 2. Workflow Automation

```yaml
# Expense approval workflow
workflow: expense_approval
triggers:
  - action: approve
    resource: expense:*
    condition: "amount > 1000"

steps:
  - approver: direct_manager
    timeout: 24h
    escalate_to: department_head

  - approver: finance_team
    timeout: 48h
    condition: "amount > 5000"

on_timeout: deny_with_notification
on_approve: log_and_proceed
on_deny: log_and_notify_requester
```

Building this yourself:
- Custom workflow engine: 2-3 months
- Approval routing: 2-4 weeks
- Timeout handling: 1-2 weeks
- Audit integration: 2-4 weeks

### 3. Compliance Automation

```
Auditor: "Show me all access to PII data in Q4"

PUGUH response (instant):
{
  "period": "2025-10-01 to 2025-12-31",
  "pii_access_events": 1,247,
  "unique_users": 45,
  "top_accessors": [...],
  "denied_attempts": 89,
  "approval_workflows_completed": 23
}
```

Without PUGUH:
- Search application logs (scattered)
- Correlate across systems (manual)
- Build report (days of work)
- Hope nothing was missed

### 4. Cross-System Authorization

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CRM       │    │   Billing   │    │   Support   │
│   System    │    │   System    │    │   System    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                    ┌─────┴─────┐
                    │   PUGUH   │  ← Single authorization
                    │   Engine  │    for all systems
                    └───────────┘
```

One policy change → All systems updated instantly.

---

## Who Uses PUGUH?

### Engineering Teams
- Centralized authorization logic
- No more scattered permission checks
- Consistent enforcement

### Security Teams
- Complete audit trail
- Policy compliance verification
- Access reviews

### Compliance Teams
- Audit-ready reports
- Historical access data
- Policy documentation

### Operations Teams
- Workflow automation
- Escalation handling
- Access provisioning

---

## Getting Started

### 1. Install SDK

```bash
# Python
pip install puguh-sdk

# TypeScript
npm install @puguh/sdk
```

### 2. Initialize

```python
from puguh import Infra

infra = Infra(
    api_key="your-api-key",
    tenant_id="your-tenant"
)
```

### 3. First Check

```python
result = infra.check(
    actor="user:alice",
    action="read",
    resource="document:budget-2025"
)

print(result.decision)  # ALLOWED, DENIED, or REQUIRE_APPROVAL
```

No complex setup. No infrastructure to manage. Just authorization.

---

## Summary

| Aspect | PUGUH Approach |
|--------|----------------|
| **Integration** | Thin SDK, standard interfaces |
| **Lock-in** | None - OpenFGA compatible |
| **Value** | Decision audit, workflow automation, compliance |
| **Migration** | Export everything, ~2 weeks effort |
| **Pricing** | Per decision, predictable |

**Easy to leave. Hard to want to leave.**
