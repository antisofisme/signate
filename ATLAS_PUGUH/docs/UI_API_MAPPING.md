# ATLAS_PUGUH CMS - API Call Mapping

**Phase**: 4
**Status**: IMPLEMENTATION READY
**Date**: 2026-01-24

---

## Overview

This document maps every UI screen to its API calls.

**CRITICAL RULES:**
1. ALL API calls go through SDK client
2. ALL mutations require idempotency_key
3. ALL requests require tenant + subject context
4. NO direct database access

---

## Context Requirements

Every API call MUST include:

```typescript
interface RequestContext {
  tenant_id: UUID;        // REQUIRED - no default
  subject_id: UUID;       // REQUIRED - no default
  subject_type: string;   // "user" | "service"
  trace_id: UUID;         // REQUIRED - for tracing
  idempotency_key?: string; // REQUIRED for mutations
}
```

---

## 1. IAM Domain API Mapping

### 1.1 User List (`/iam/users`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load users | GET | `/api/v1/iam/users` | ✅ Required | ❌ No |
| Search users | GET | `/api/v1/iam/users?q={query}` | ✅ Required | ❌ No |
| Filter by role | GET | `/api/v1/iam/users?role={roleId}` | ✅ Required | ❌ No |

```typescript
// SDK Call
const users = await sdk.iam.listUsers({
  context: { tenant_id, subject_id, trace_id },
  filters: { role_id, search },
  pagination: { page, limit }
});
```

### 1.2 User Detail (`/iam/users/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load user | GET | `/api/v1/iam/users/:id` | ✅ Required | ❌ No |
| Load user roles | GET | `/api/v1/iam/users/:id/roles` | ✅ Required | ❌ No |

```typescript
// SDK Call
const user = await sdk.iam.getUser({
  context: { tenant_id, subject_id, trace_id },
  user_id
});
```

### 1.3 Role List (`/iam/roles`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load roles | GET | `/api/v1/iam/roles` | ✅ Required | ❌ No |

```typescript
// SDK Call
const roles = await sdk.iam.listRoles({
  context: { tenant_id, subject_id, trace_id }
});
```

### 1.4 Role Detail (`/iam/roles/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load role | GET | `/api/v1/iam/roles/:id` | ✅ Required | ❌ No |
| Load permissions | GET | `/api/v1/iam/roles/:id/permissions` | ✅ Required | ❌ No |

### 1.5 Service Accounts (`/iam/service-accounts`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load accounts | GET | `/api/v1/iam/service-accounts` | ✅ Required | ❌ No |

### 1.6 Permission Matrix (`/iam/permissions`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load matrix | GET | `/api/v1/iam/permissions/matrix` | ✅ Required | ❌ No |

---

## 2. Tenant Domain API Mapping

### 2.1 Tenant List (`/tenant/list`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load tenants | GET | `/api/v1/tenants` | ✅ Required | ❌ No |

```typescript
// SDK Call
const tenants = await sdk.tenant.listTenants({
  context: { tenant_id, subject_id, trace_id }
});
```

**NOTE**: User can only see tenants they have access to.

### 2.2 Tenant Detail (`/tenant/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load tenant | GET | `/api/v1/tenants/:id` | ✅ Required | ❌ No |

**CRITICAL**: tenant_id in context MUST match :id parameter.
Cross-tenant access is DENIED.

### 2.3 Tenant Members (`/tenant/:id/members`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load members | GET | `/api/v1/tenants/:id/members` | ✅ Required | ❌ No |

### 2.4 Isolation Check (`/tenant/isolation-check`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Run check | GET | `/api/v1/tenants/isolation-check` | ✅ Required | ❌ No |

---

## 3. Decision Domain API Mapping

### 3.1 Rule List (`/decision/rules`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load rules | GET | `/api/v1/rules` | ✅ Required | ❌ No |
| Filter by status | GET | `/api/v1/rules?status={status}` | ✅ Required | ❌ No |
| Filter by type | GET | `/api/v1/rules?decision_type={type}` | ✅ Required | ❌ No |

```typescript
// SDK Call
const rules = await sdk.decision.listRules({
  context: { tenant_id, subject_id, trace_id },
  filters: { status, decision_type }
});
```

### 3.2 Create Rule Draft (`/decision/rules/new`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Create draft | POST | `/api/v1/rules` | ✅ Required | ✅ **REQUIRED** |

```typescript
// SDK Call - MUTATION
const rule = await sdk.decision.createRuleDraft({
  context: {
    tenant_id,
    subject_id,
    trace_id,
    idempotency_key: generateIdempotencyKey() // REQUIRED
  },
  rule_name: "...",
  decision_type: "...",
  conditions: {...},
  action: {...}
});
```

**UI MUST show confirmation:**
```
This will:
✓ Create a rule in DRAFT status
✓ Generate an audit record
✓ NOT affect live decisions until activated
```

### 3.3 Rule Detail (`/decision/rules/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load rule | GET | `/api/v1/rules/:id` | ✅ Required | ❌ No |

### 3.4 Rule Versions (`/decision/rules/:id/versions`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load versions | GET | `/api/v1/rules/:id/versions` | ✅ Required | ❌ No |

### 3.5 Activate Rule (`/decision/rules/:id/activate`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Request activation | POST | `/api/v1/rules/:id/activate` | ✅ Required | ✅ **REQUIRED** |

```typescript
// SDK Call - MUTATION (creates workflow)
const workflow = await sdk.decision.requestRuleActivation({
  context: {
    tenant_id,
    subject_id,
    trace_id,
    idempotency_key: generateIdempotencyKey()
  },
  rule_id
});
```

**UI MUST show confirmation:**
```
This will:
✓ Create a decision record
✓ Create an approval workflow
✓ Notify approvers
✓ Rule will NOT be active until approved
```

### 3.6 Decision History (`/decision/history`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load decisions | GET | `/api/v1/decisions` | ✅ Required | ❌ No |
| Filter by type | GET | `/api/v1/decisions?type={type}` | ✅ Required | ❌ No |
| Filter by outcome | GET | `/api/v1/decisions?outcome={outcome}` | ✅ Required | ❌ No |

### 3.7 Decision Detail (`/decision/history/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load decision | GET | `/api/v1/decisions/:id` | ✅ Required | ❌ No |
| Load events | GET | `/api/v1/decisions/:id/events` | ✅ Required | ❌ No |

**NOTE**: Decision detail is READ-ONLY. No edit actions available.

---

## 4. Workflow Domain API Mapping

### 4.1 My Pending (`/workflow/pending`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load my queue | GET | `/api/v1/workflows?assignee=me&status=pending` | ✅ Required | ❌ No |

```typescript
// SDK Call
const workflows = await sdk.workflow.listPending({
  context: { tenant_id, subject_id, trace_id }
});
```

### 4.2 Workflow Detail (`/workflow/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load workflow | GET | `/api/v1/workflows/:id` | ✅ Required | ❌ No |
| Load transitions | GET | `/api/v1/workflows/:id/transitions` | ✅ Required | ❌ No |
| Load decision | GET | `/api/v1/workflows/:id/decision` | ✅ Required | ❌ No |

### 4.3 Approve Workflow (`/workflow/:id/approve`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Approve | POST | `/api/v1/workflows/:id/approve` | ✅ Required | ✅ **REQUIRED** |

```typescript
// SDK Call - MUTATION
const result = await sdk.workflow.approve({
  context: {
    tenant_id,
    subject_id,
    trace_id,
    idempotency_key: generateIdempotencyKey()
  },
  workflow_id,
  comment: "..." // optional
});
```

**UI MUST show confirmation:**
```
This will:
✓ Approve the pending workflow
✓ Update the parent decision outcome
✓ Create transition record
✓ Emit workflow.approved event
✓ This action CANNOT be undone
```

### 4.4 Reject Workflow (`/workflow/:id/reject`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Reject | POST | `/api/v1/workflows/:id/reject` | ✅ Required | ✅ **REQUIRED** |

```typescript
// SDK Call - MUTATION
const result = await sdk.workflow.reject({
  context: {
    tenant_id,
    subject_id,
    trace_id,
    idempotency_key: generateIdempotencyKey()
  },
  workflow_id,
  reason: "..." // REQUIRED
});
```

**UI MUST show confirmation:**
```
This will:
✓ Reject the pending workflow
✓ Update the parent decision to DENIED
✓ Create transition record
✓ Emit workflow.rejected event
✓ This action CANNOT be undone
```

### 4.5 Delegate Workflow (`/workflow/:id/delegate`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Delegate | POST | `/api/v1/workflows/:id/delegate` | ✅ Required | ✅ **REQUIRED** |

```typescript
// SDK Call - MUTATION
const result = await sdk.workflow.delegate({
  context: {
    tenant_id,
    subject_id,
    trace_id,
    idempotency_key: generateIdempotencyKey()
  },
  workflow_id,
  delegate_to_user_id,
  reason: "..." // REQUIRED
});
```

### 4.6 Escalate Workflow (`/workflow/:id/escalate`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Escalate | POST | `/api/v1/workflows/:id/escalate` | ✅ Required | ✅ **REQUIRED** |

---

## 5. Control Domain API Mapping

### 5.1 Audit Trail (`/control/audit`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load audit | GET | `/api/v1/audit` | ✅ Required | ❌ No |
| Filter by resource | GET | `/api/v1/audit?resource_type={type}` | ✅ Required | ❌ No |
| Filter by action | GET | `/api/v1/audit?action={action}` | ✅ Required | ❌ No |

```typescript
// SDK Call - READ ONLY
const audit = await sdk.control.listAudit({
  context: { tenant_id, subject_id, trace_id },
  filters: { resource_type, date_range }
});
```

**NOTE**: Audit domain is 100% READ-ONLY. No mutations allowed.

### 5.2 Audit Detail (`/control/audit/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load record | GET | `/api/v1/audit/:id` | ✅ Required | ❌ No |

### 5.3 Event Timeline (`/control/events`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load events | GET | `/api/v1/events` | ✅ Required | ❌ No |
| Filter by type | GET | `/api/v1/events?event_type={type}` | ✅ Required | ❌ No |
| Filter by aggregate | GET | `/api/v1/events?aggregate_id={id}` | ✅ Required | ❌ No |

### 5.4 Event Detail (`/control/events/:id`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load event | GET | `/api/v1/events/:id` | ✅ Required | ❌ No |

### 5.5 DLQ View (`/control/dlq`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load DLQ | GET | `/api/v1/events/dlq` | ✅ Required | ❌ No |

**NOTE**: DLQ view is READ-ONLY. No replay or reprocess from UI.

### 5.6 Metrics Dashboard (`/control/metrics`)

| Action | Method | Endpoint | Context | Idempotency |
|--------|--------|----------|---------|-------------|
| Load metrics | GET | `/api/v1/metrics` | ✅ Required | ❌ No |
| Load decision stats | GET | `/api/v1/metrics/decisions` | ✅ Required | ❌ No |
| Load workflow stats | GET | `/api/v1/metrics/workflows` | ✅ Required | ❌ No |

---

## Summary: Mutation Endpoints

| Domain | Endpoint | Action | Idempotency |
|--------|----------|--------|-------------|
| Decision | POST `/api/v1/rules` | Create rule draft | ✅ REQUIRED |
| Decision | POST `/api/v1/rules/:id/activate` | Request activation | ✅ REQUIRED |
| Workflow | POST `/api/v1/workflows/:id/approve` | Approve | ✅ REQUIRED |
| Workflow | POST `/api/v1/workflows/:id/reject` | Reject | ✅ REQUIRED |
| Workflow | POST `/api/v1/workflows/:id/delegate` | Delegate | ✅ REQUIRED |
| Workflow | POST `/api/v1/workflows/:id/escalate` | Escalate | ✅ REQUIRED |

**Total mutations: 6**
**All other endpoints: READ-ONLY**

---

## Error Handling

### Standard Error Response

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TENANT_REQUIRED` | 400 | Missing tenant context |
| `SUBJECT_REQUIRED` | 400 | Missing subject context |
| `IDEMPOTENCY_REQUIRED` | 400 | Missing idempotency key |
| `CROSS_TENANT_DENIED` | 403 | Cross-tenant access attempt |
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | Not authorized for action |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Idempotency conflict |
