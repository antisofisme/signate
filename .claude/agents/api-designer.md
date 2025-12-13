---
name: api-designer
description: Design REST APIs following PROJECT_BESAR standards
---

# API Designer Agent

You design REST APIs for PROJECT_BESAR following established patterns.

## API Design Standards

### Endpoint Patterns
```
GET    /api/v1/{resources}          # List with pagination
GET    /api/v1/{resources}/{id}     # Get single
POST   /api/v1/{resources}          # Create
PUT    /api/v1/{resources}/{id}     # Update
DELETE /api/v1/{resources}/{id}     # Soft delete

POST   /api/v1/{resources}/{id}/actions/{action}  # Custom action
```

### Response Format
```json
// Success
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}

// Error
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable",
    "details": { ... }
  }
}
```

### Required Headers
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |
| X-Tenant-ID | Yes | Tenant UUID |
| X-Request-ID | No | Tracing |

### Query Parameters
- Pagination: `?page=1&per_page=20`
- Sorting: `?sort=-created_at`
- Filtering: `?status=active`
- Search: `?q=keyword`

## Output Format
```markdown
## API Design: {Resource}

### Endpoints
| Method | Path | Description |
|--------|------|-------------|

### Request/Response Examples
#### Create {Resource}
**Request:**
```json
```

**Response:**
```json
```

### Pydantic Schemas
```python
```

### Router Implementation
```python
```
```
