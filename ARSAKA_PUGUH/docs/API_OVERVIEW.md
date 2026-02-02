# ARSAKA_PUGUH API Overview

Complete API documentation for the ARSAKA_PUGUH SaaS platform.

## Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://api.puguh.arsaka.io` |
| Staging | `https://api-puguh-staging.arsaka.io` |
| Development | `http://localhost:8001` |

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "...",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### Refreshing a Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

---

## API Modules

### 1. Authentication (`/api/v1/auth`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | POST | No | Register new user |
| `/login` | POST | No | Login with email/password |
| `/logout` | POST | Yes | Invalidate session |
| `/refresh` | POST | No | Refresh access token |
| `/verify-email` | POST | No | Verify email address |
| `/forgot-password` | POST | No | Request password reset |
| `/reset-password` | POST | No | Reset password |
| `/me` | GET | Yes | Get current user |
| `/google` | GET | No | Initiate Google OAuth |
| `/google/callback` | GET | No | Google OAuth callback |
| `/github` | GET | No | Initiate GitHub OAuth |
| `/github/callback` | GET | No | GitHub OAuth callback |

### 2. Tenants (`/api/v1/tenants`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | Yes | List user's tenants |
| `/` | POST | Yes | Create new tenant |
| `/{tenant_id}` | GET | Yes | Get tenant details |
| `/{tenant_id}` | PATCH | Yes | Update tenant |
| `/{tenant_id}` | DELETE | Yes | Delete tenant |
| `/{tenant_id}/members` | GET | Yes | List tenant members |
| `/{tenant_id}/members` | POST | Yes | Add member |
| `/{tenant_id}/members/{user_id}` | PATCH | Yes | Update member role |
| `/{tenant_id}/members/{user_id}` | DELETE | Yes | Remove member |
| `/{tenant_id}/invite` | POST | Yes | Send invitation |

### 3. Projects (`/api/v1/projects`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | Yes | List projects |
| `/` | POST | Yes | Create project |
| `/{project_id}` | GET | Yes | Get project |
| `/by-slug/{slug}` | GET | Yes | Get project by slug |
| `/{project_id}` | PATCH | Yes | Update project |
| `/{project_id}` | DELETE | Yes | Delete project |
| `/{project_id}/members` | GET | Yes | List project members |
| `/{project_id}/members` | POST | Yes | Add member |
| `/{project_id}/members/{user_id}` | PATCH | Yes | Update member role |
| `/{project_id}/members/{user_id}` | DELETE | Yes | Remove member |

### 4. Billing (`/api/v1/billing`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/plans` | GET | No | List subscription plans |
| `/subscription` | GET | Yes | Get current subscription |
| `/checkout` | POST | Yes | Create checkout session |
| `/cancel` | POST | Yes | Cancel subscription |
| `/invoices` | GET | Yes | List invoices |
| `/invoices/{id}` | GET | Yes | Get invoice details |
| `/usage` | GET | Yes | Get usage metrics |

### 5. Webhooks (`/webhooks`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/midtrans` | POST | Signature | Midtrans payment callback |

---

## Common Parameters

### Pagination

```
?limit=100    # Max items per page (default: 100, max: 1000)
?offset=0     # Skip N items (default: 0)
```

### Tenant Context

Most endpoints require tenant context:

```
?tenant_id=550e8400-e29b-41d4-a716-446655440000
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "total": 100,
    "limit": 10,
    "offset": 0
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Auth endpoints | 10 | 1 minute |
| API endpoints | 100 | 1 minute |
| Webhook endpoints | 1000 | 1 minute |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706300000
```

---

## SDKs & Libraries

### JavaScript/TypeScript

```typescript
import { ArsakaPuguhClient } from '@arsaka/puguh-sdk'

const client = new ArsakaPuguhClient({
  baseUrl: 'https://api.puguh.arsaka.io',
  accessToken: 'your-token',
})

// List projects
const projects = await client.projects.list({ tenantId: '...' })
```

### Python

```python
from atlaspuguh import Client

client = Client(
    base_url="https://api.puguh.arsaka.io",
    access_token="your-token",
)

# List projects
projects = client.projects.list(tenant_id="...")
```

---

## Interactive Documentation

- **Swagger UI**: `/api/docs`
- **ReDoc**: `/api/redoc`
- **OpenAPI Spec**: `/api/openapi.json`

---

*API Version: 1.0.0*
*Last updated: January 2026*
