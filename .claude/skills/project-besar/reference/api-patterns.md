---
description: API patterns for PROJECT_BESAR
---

# API Patterns Reference

## Response Format

### Success
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

## Error Codes
| Code | HTTP | Use |
|------|------|-----|
| VALIDATION_ERROR | 400 | Input invalid |
| UNAUTHORIZED | 401 | Not authenticated |
| PERMISSION_DENIED | 403 | Not authorized |
| NOT_FOUND | 404 | Resource missing |
| CONFLICT | 409 | Duplicate/conflict |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

## Endpoint Patterns
```
GET    /api/v1/{resources}          # List
GET    /api/v1/{resources}/{id}     # Get one
POST   /api/v1/{resources}          # Create
PUT    /api/v1/{resources}/{id}     # Update
DELETE /api/v1/{resources}/{id}     # Delete

POST   /api/v1/{resources}/{id}/actions/{action}  # Custom action
```

## Required Headers
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | `Bearer {token}` |
| X-Tenant-ID | Yes | Tenant UUID |
| X-Request-ID | No | For tracing |

## Pagination
Query: `?page=1&per_page=20&sort=-created_at`

## Filtering
Query: `?status=active&type=premium`
