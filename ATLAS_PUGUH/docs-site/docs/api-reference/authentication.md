---
sidebar_position: 1
---

# API Authentication

Learn how to authenticate with the ATLAS PUGUH API.

## Authentication Methods

PUGUH supports two authentication methods:

1. **API Keys**: For server-to-server integrations
2. **JWT Tokens**: For user-context operations

## API Keys

### Obtaining an API Key

1. Go to your profile settings
2. Click **"API Keys"**
3. Click **"Create New Key"**
4. Copy the key (shown only once!)

Or create a service account for production use.

### Using API Keys

Include the key in the `Authorization` header:

```bash
curl -X GET https://api-puguh.atlashub.com/api/v1/rules \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer {api_key}` |
| `X-Tenant-ID` | Yes | Your tenant UUID |
| `X-Project-ID` | Sometimes | Required for project-scoped operations |
| `Content-Type` | For POST/PUT | Usually `application/json` |

## JWT Tokens

### Obtaining a Token

Login to get a JWT token:

```bash
curl -X POST https://api-puguh.atlashub.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
  }
}
```

### Using JWT Tokens

```bash
curl -X GET https://api-puguh.atlashub.com/api/v1/rules \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Refreshing Tokens

Before expiration, refresh your token:

```bash
curl -X POST https://api-puguh.atlashub.com/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
  }'
```

## SDK Authentication

### JavaScript/TypeScript

```typescript
import { PuguhClient } from '@atlashub/puguh-sdk';

// Using API Key
const client = new PuguhClient({
  apiKey: process.env.PUGUH_API_KEY,
  tenantId: process.env.PUGUH_TENANT_ID,
});

// Using JWT
const client = new PuguhClient({
  accessToken: userToken,
  onTokenExpired: async () => {
    const newToken = await refreshToken();
    return newToken;
  },
});
```

### Python

```python
from puguh import PuguhClient

# Using API Key
client = PuguhClient(
    api_key=os.environ['PUGUH_API_KEY'],
    tenant_id=os.environ['PUGUH_TENANT_ID']
)

# Using JWT
client = PuguhClient(
    access_token=user_token,
    on_token_expired=refresh_token_callback
)
```

## Security Best Practices

### API Key Security

1. **Never commit keys to source control**
   ```bash
   # .gitignore
   .env
   *.key
   ```

2. **Use environment variables**
   ```bash
   export PUGUH_API_KEY=your_key_here
   ```

3. **Rotate keys regularly**
   - Rotate production keys quarterly
   - Rotate immediately if compromised

4. **Use separate keys per environment**
   - Development key
   - Staging key
   - Production key

### Token Security

1. **Store securely**
   - Use secure cookies (HttpOnly, Secure, SameSite)
   - Don't store in localStorage for sensitive apps

2. **Short expiration**
   - Access tokens: 1 hour recommended
   - Refresh tokens: 7-30 days

3. **Revoke on logout**
   ```bash
   curl -X POST https://api-puguh.atlashub.com/api/v1/auth/logout \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Error Responses

### 401 Unauthorized

Missing or invalid credentials:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

### 403 Forbidden

Valid credentials but lacking permission:

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Missing permission: decision.rules.create"
  }
}
```

### Token Expired

Access token has expired:

```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Access token has expired"
  }
}
```

Handle by refreshing the token and retrying.

## Rate Limiting

API calls are rate limited:

| Plan | Requests/minute |
|------|-----------------|
| Free | 60 |
| Starter | 300 |
| Pro | 1000 |
| Enterprise | Custom |

Rate limit headers:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1640000000
```

### 429 Too Many Requests

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

## Testing Authentication

### Verify Token

Check if your token is valid:

```bash
curl -X GET https://api-puguh.atlashub.com/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "tenants": [
      {
        "tenant_id": "uuid",
        "name": "My Org",
        "role": "admin"
      }
    ]
  }
}
```

### Test API Key

```bash
curl -X GET https://api-puguh.atlashub.com/api/v1/health \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

## OAuth Integration (Enterprise)

For SSO integration:

### Authorization URL

```
https://api-puguh.atlashub.com/oauth/authorize
  ?client_id=YOUR_CLIENT_ID
  &redirect_uri=YOUR_REDIRECT_URI
  &response_type=code
  &scope=read:user read:resources
  &state=RANDOM_STATE
```

### Exchange Code for Token

```bash
curl -X POST https://api-puguh.atlashub.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

## Related

- [Rules API](/docs/api-reference/rules-api)
- [Decisions API](/docs/api-reference/decisions-api)
- [SDK Usage](/docs/api-reference/sdk-usage)
