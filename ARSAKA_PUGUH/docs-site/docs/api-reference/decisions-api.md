---
sidebar_position: 3
---

# Decisions API

API reference for requesting and querying decisions.

## Overview

The Decisions API allows you to:
- Request decisions from the rule engine
- Query decision history
- View decision details

## Request Decision

The primary endpoint for getting a decision.

```http
POST /api/v1/decisions
Content-Type: application/json
```

### Request Body

```json
{
  "type": "expense_approval",
  "context": {
    "amount": 15000,
    "category": "equipment",
    "department": "engineering",
    "requester": {
      "email": "john@example.com",
      "role": "manager",
      "manager": "jane@example.com"
    }
  },
  "options": {
    "dry_run": false,
    "include_evaluation": true
  }
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Decision type (e.g., "expense_approval") |
| `context` | object | Yes | Data to evaluate against rules |
| `options.dry_run` | boolean | No | If true, don't persist the decision |
| `options.include_evaluation` | boolean | No | Include rule evaluation details |
| `idempotency_key` | string | No | Prevent duplicate decisions |

### Response

```json
{
  "success": true,
  "data": {
    "decision_id": "dec-uuid",
    "type": "expense_approval",
    "outcome": "REQUIRE_APPROVAL",
    "matched_rule": {
      "id": "rule-uuid",
      "name": "High Value Approval",
      "version": 3
    },
    "action": {
      "type": "REQUIRE_APPROVAL",
      "workflow_id": "wf-uuid",
      "priority": "high"
    },
    "evaluation": {
      "rules_evaluated": 5,
      "rules_matched": 1,
      "duration_ms": 8,
      "conditions": [
        {
          "rule": "High Value Approval",
          "field": "amount",
          "result": true,
          "actual": 15000,
          "threshold": 5000
        }
      ]
    },
    "timestamp": "2025-01-20T10:30:00.123Z"
  }
}
```

### Outcome Values

| Outcome | Description |
|---------|-------------|
| `ALLOWED` | Decision approved, no workflow |
| `DENIED` | Decision rejected |
| `REQUIRE_APPROVAL` | Workflow created |
| `FLAGGED` | Flagged for review |
| `NO_MATCH` | No rules matched |

## List Decisions

Query decision history.

```http
GET /api/v1/decisions
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by decision type |
| `outcome` | string | Filter by outcome |
| `start_date` | datetime | Start of date range |
| `end_date` | datetime | End of date range |
| `rule_id` | uuid | Filter by rule |
| `limit` | int | Max results (default 20) |
| `offset` | int | Pagination offset |

### Response

```json
{
  "success": true,
  "data": [
    {
      "decision_id": "dec-uuid",
      "type": "expense_approval",
      "outcome": "ALLOWED",
      "matched_rule": "Default Allow",
      "timestamp": "2025-01-20T09:00:00Z"
    },
    {
      "decision_id": "dec-uuid-2",
      "type": "expense_approval",
      "outcome": "REQUIRE_APPROVAL",
      "matched_rule": "High Value Approval",
      "workflow_id": "wf-uuid",
      "timestamp": "2025-01-20T10:30:00Z"
    }
  ],
  "meta": {
    "total": 1543,
    "limit": 20,
    "offset": 0
  }
}
```

## Get Decision

Get details of a specific decision.

```http
GET /api/v1/decisions/{id}
```

### Response

```json
{
  "success": true,
  "data": {
    "decision_id": "dec-uuid",
    "type": "expense_approval",
    "outcome": "REQUIRE_APPROVAL",
    "context": {
      "amount": 15000,
      "category": "equipment",
      "department": "engineering"
    },
    "matched_rule": {
      "id": "rule-uuid",
      "name": "High Value Approval",
      "version": 3
    },
    "action": {
      "type": "REQUIRE_APPROVAL",
      "workflow_id": "wf-uuid"
    },
    "workflow": {
      "id": "wf-uuid",
      "status": "PENDING",
      "current_stage": "Manager Review"
    },
    "evaluation": {
      "rules_evaluated": 5,
      "rules_matched": 1,
      "duration_ms": 8,
      "trace": [
        { "rule": "Executive Bypass", "matched": false },
        { "rule": "High Value Approval", "matched": true },
        { "rule": "Default Allow", "skipped": true }
      ]
    },
    "timestamp": "2025-01-20T10:30:00.123Z",
    "tenant_id": "tenant-uuid",
    "project_id": "project-uuid"
  }
}
```

## Decision Analytics

Get aggregated decision statistics.

```http
GET /api/v1/decisions/analytics
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | "day", "week", "month" |
| `type` | string | Filter by decision type |
| `group_by` | string | "outcome", "rule", "type" |

### Response

```json
{
  "success": true,
  "data": {
    "period": "week",
    "total_decisions": 5432,
    "by_outcome": {
      "ALLOWED": 4200,
      "DENIED": 150,
      "REQUIRE_APPROVAL": 1082
    },
    "by_day": [
      { "date": "2025-01-14", "count": 756 },
      { "date": "2025-01-15", "count": 812 },
      { "date": "2025-01-16", "count": 795 }
    ],
    "avg_latency_ms": 12,
    "top_rules": [
      { "rule": "Default Allow", "count": 3800 },
      { "rule": "High Value Approval", "count": 1082 }
    ]
  }
}
```

## Bulk Decisions

Process multiple decisions in one request.

```http
POST /api/v1/decisions/bulk
Content-Type: application/json
```

### Request Body

```json
{
  "decisions": [
    {
      "type": "expense_approval",
      "context": { "amount": 500 },
      "reference_id": "exp-001"
    },
    {
      "type": "expense_approval",
      "context": { "amount": 7500 },
      "reference_id": "exp-002"
    }
  ],
  "options": {
    "stop_on_error": false
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "processed": 2,
    "results": [
      {
        "reference_id": "exp-001",
        "decision_id": "dec-uuid-1",
        "outcome": "ALLOWED"
      },
      {
        "reference_id": "exp-002",
        "decision_id": "dec-uuid-2",
        "outcome": "REQUIRE_APPROVAL"
      }
    ]
  }
}
```

## Idempotency

Use idempotency keys to prevent duplicate decisions.

```http
POST /api/v1/decisions
Idempotency-Key: unique-request-id-123
Content-Type: application/json
```

If the same key is used within 24 hours, the original decision is returned.

## Webhooks

Configure webhooks to receive decision notifications.

### Webhook Payload

```json
{
  "event": "decision.created",
  "timestamp": "2025-01-20T10:30:00.123Z",
  "data": {
    "decision_id": "dec-uuid",
    "type": "expense_approval",
    "outcome": "REQUIRE_APPROVAL",
    "context": {...}
  }
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `decision.created` | New decision made |
| `decision.workflow_completed` | Associated workflow done |

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid decision type",
    "details": {
      "type": "Unknown decision type: invalid_type"
    }
  }
}
```

### 429 Rate Limited

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Decision rate limit exceeded",
    "retry_after": 60
  }
}
```

### 503 Service Unavailable

```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Rule engine temporarily unavailable"
  }
}
```

## Related

- [Rules API](/docs/api-reference/rules-api)
- [SDK Usage](/docs/api-reference/sdk-usage)
- [Authentication](/docs/api-reference/authentication)
