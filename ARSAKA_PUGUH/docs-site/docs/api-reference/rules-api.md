---
sidebar_position: 2
---

# Rules API

Complete API reference for managing rules.

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/rules` | List all rules |
| `GET` | `/api/v1/rules/{id}` | Get rule details |
| `POST` | `/api/v1/rules` | Create a rule |
| `PATCH` | `/api/v1/rules/{id}` | Update a rule |
| `DELETE` | `/api/v1/rules/{id}` | Delete a rule |
| `POST` | `/api/v1/rules/{id}/test` | Test a rule |
| `POST` | `/api/v1/rules/{id}/activate` | Activate a rule |

## List Rules

```http
GET /api/v1/rules
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `decision_type` | string | Filter by type |
| `project_id` | uuid | Filter by project |
| `limit` | int | Max results (default 20) |
| `offset` | int | Pagination offset |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "High Value Approval",
      "description": "Requires approval for high amounts",
      "decision_type": "expense_approval",
      "status": "active",
      "priority": 100,
      "version": 3,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z"
    }
  ],
  "meta": {
    "total": 45,
    "limit": 20,
    "offset": 0
  }
}
```

## Get Rule

```http
GET /api/v1/rules/{id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "High Value Approval",
    "description": "Requires approval for amounts over $5000",
    "decision_type": "expense_approval",
    "status": "active",
    "priority": 100,
    "version": 3,
    "scope": "project",
    "project_id": "uuid",
    "conditions": {
      "all": [
        {
          "field": "amount",
          "operator": "greater_than",
          "value": 5000
        }
      ]
    },
    "actions": {
      "type": "REQUIRE_APPROVAL",
      "config": {
        "workflow_id": "manager-approval",
        "priority": "high"
      }
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z",
    "created_by": "user-uuid"
  }
}
```

## Create Rule

```http
POST /api/v1/rules
Content-Type: application/json
```

### Request Body

```json
{
  "name": "High Value Approval",
  "description": "Requires approval for amounts over $5000",
  "decision_type": "expense_approval",
  "priority": 100,
  "scope": "project",
  "project_id": "uuid",
  "conditions": {
    "all": [
      {
        "field": "amount",
        "operator": "greater_than",
        "value": 5000
      }
    ]
  },
  "actions": {
    "type": "REQUIRE_APPROVAL",
    "config": {
      "workflow_id": "manager-approval"
    }
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "new-rule-uuid",
    "name": "High Value Approval",
    "status": "draft",
    "version": 1,
    "created_at": "2025-01-20T10:00:00Z"
  }
}
```

## Update Rule

```http
PATCH /api/v1/rules/{id}
Content-Type: application/json
```

### Request Body

```json
{
  "description": "Updated description",
  "priority": 150,
  "conditions": {
    "all": [
      {
        "field": "amount",
        "operator": "greater_than",
        "value": 10000
      }
    ]
  }
}
```

Creates a new version of the rule.

### Response

```json
{
  "success": true,
  "data": {
    "id": "rule-uuid",
    "version": 4,
    "status": "draft",
    "updated_at": "2025-01-20T10:00:00Z"
  }
}
```

## Delete Rule

```http
DELETE /api/v1/rules/{id}
```

Soft-deletes the rule (sets status to archived).

### Response

```json
{
  "success": true,
  "data": {
    "id": "rule-uuid",
    "status": "archived",
    "deleted_at": "2025-01-20T10:00:00Z"
  }
}
```

## Test Rule

```http
POST /api/v1/rules/{id}/test
Content-Type: application/json
```

### Request Body

```json
{
  "context": {
    "amount": 7500,
    "category": "equipment",
    "department": "engineering"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "matches": true,
    "action": {
      "type": "REQUIRE_APPROVAL",
      "config": {
        "workflow_id": "manager-approval"
      }
    },
    "evaluation": {
      "conditions": [
        {
          "field": "amount",
          "operator": "greater_than",
          "value": 5000,
          "actual": 7500,
          "result": true
        }
      ],
      "duration_ms": 2
    }
  }
}
```

## Activate Rule

```http
POST /api/v1/rules/{id}/activate
Content-Type: application/json
```

### Request Body

```json
{
  "description": "Activating after testing"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "rule-uuid",
    "status": "active",
    "activated_at": "2025-01-20T10:00:00Z",
    "activated_by": "user-uuid"
  }
}
```

## Get Rule Versions

```http
GET /api/v1/rules/{id}/versions
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "version": 3,
      "status": "active",
      "description": "Increased threshold",
      "created_at": "2025-01-15T00:00:00Z",
      "created_by": "user-uuid"
    },
    {
      "version": 2,
      "status": "superseded",
      "description": "Added department condition",
      "created_at": "2025-01-10T00:00:00Z",
      "created_by": "user-uuid"
    },
    {
      "version": 1,
      "status": "superseded",
      "description": "Initial version",
      "created_at": "2025-01-01T00:00:00Z",
      "created_by": "user-uuid"
    }
  ]
}
```

## Condition Operators

| Operator | Description | Value Types |
|----------|-------------|-------------|
| `equals` | Exact match | any |
| `not_equals` | Not equal | any |
| `greater_than` | Greater than | number, date |
| `less_than` | Less than | number, date |
| `greater_than_or_equals` | >= | number, date |
| `less_than_or_equals` | <= | number, date |
| `contains` | String contains | string |
| `starts_with` | String starts with | string |
| `ends_with` | String ends with | string |
| `in` | Value in list | any |
| `not_in` | Value not in list | any |
| `is_null` | Value is null | any |
| `is_not_null` | Value is not null | any |

## Action Types

| Type | Description |
|------|-------------|
| `ALLOW` | Immediately allow |
| `DENY` | Immediately deny |
| `REQUIRE_APPROVAL` | Route to workflow |
| `FLAG` | Flag for review |
| `CUSTOM` | Custom webhook |

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid rule configuration",
    "details": {
      "conditions": "Invalid operator 'contains' for number field"
    }
  }
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Rule not found"
  }
}
```

### 409 Conflict

```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Rule is already active"
  }
}
```

## Related

- [Decisions API](/docs/api-reference/decisions-api)
- [SDK Usage](/docs/api-reference/sdk-usage)
- [Authentication](/docs/api-reference/authentication)
