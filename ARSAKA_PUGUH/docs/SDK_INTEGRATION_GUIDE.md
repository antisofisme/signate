# PUGUH SDK Integration Guide

## Overview

PUGUH SDK memungkinkan app creators untuk mengintegrasikan infrastruktur PUGUH (auth, tenant, billing) ke aplikasi mereka tanpa harus build dari scratch.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR APPLICATION                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        PUGUH SDK                                 │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │   Auth       │  │   Tenant     │  │   Billing    │           │    │
│  │  │   Client     │  │   Client     │  │   Client     │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  │                                                                  │    │
│  │  Features:                                                       │    │
│  │  - Login/Register users                                          │    │
│  │  - Validate JWT tokens                                           │    │
│  │  - Manage organizations                                          │    │
│  │  - Manage members & roles                                        │    │
│  │  - Handle subscriptions                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              │ API Calls                                 │
│                              ▼                                           │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PUGUH PLATFORM                                   │
│                                                                          │
│  Auth API (/api/v1/auth)                                                │
│  Tenant API (/api/v1/tenants)                                           │
│  Project API (/api/v1/projects)                                         │
│  Billing API (/api/v1/billing)                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Python SDK

```bash
pip install puguh-sdk
# or
poetry add puguh-sdk
```

### TypeScript/JavaScript SDK

```bash
npm install @puguh/sdk
# or
bun add @puguh/sdk
```

---

## Quick Start

### 1. Initialize SDK

```python
# Python
from puguh_sdk import PuguhClient

client = PuguhClient(
    base_url="https://api.puguh.io",
    # For user context (frontend apps)
    access_token="user_jwt_token",
    # OR for service context (backend services)
    api_key="pk_live_xxxxxxxxxxxx",
)
```

```typescript
// TypeScript
import { PuguhClient } from '@puguh/sdk';

const client = new PuguhClient({
  baseUrl: 'https://api.puguh.io',
  // For user context
  accessToken: 'user_jwt_token',
  // OR for service context
  apiKey: 'pk_live_xxxxxxxxxxxx',
});
```

### 2. Authenticate Users

```python
# Register new user
user = await client.auth.register(
    email="user@example.com",
    password="secure_password",
    display_name="John Doe"
)

# Login existing user
tokens = await client.auth.login(
    email="user@example.com",
    password="secure_password"
)
print(tokens.access_token)
print(tokens.refresh_token)

# Validate token (for your backend)
user_info = await client.auth.validate_token(tokens.access_token)
print(user_info.user_id)
print(user_info.email)
print(user_info.tenant_id)
```

### 3. Manage Tenants (Organizations)

```python
# Create organization
tenant = await client.tenants.create(
    name="My Company",
    billing_email="billing@mycompany.com"
)

# List user's organizations
tenants = await client.tenants.list()

# Invite member
invitation = await client.tenants.invite_member(
    tenant_id=tenant.tenant_id,
    email="colleague@example.com",
    role="admin"  # owner, admin, member, viewer
)

# Accept invitation (by invited user)
await client.tenants.accept_invitation(
    tenant_id=tenant.tenant_id,
    invitation_id=invitation.invitation_id
)
```

### 4. Manage Projects

```python
# Create project
project = await client.projects.create(
    tenant_id=tenant.tenant_id,
    name="Project Alpha",
    description="Main project"
)

# Add member to project
await client.projects.add_member(
    project_id=project.project_id,
    user_id="user_uuid",
    role="developer"  # owner, admin, developer, viewer
)
```

---

## Authentication Methods

### 1. User Token Authentication (Frontend Apps)

For frontend applications where users login interactively.

```python
# User logs in via your app
tokens = await client.auth.login(email, password)

# Initialize client with user token
client = PuguhClient(
    base_url="https://api.puguh.io",
    access_token=tokens.access_token
)

# All API calls are scoped to this user
tenants = await client.tenants.list()  # Returns only user's tenants
```

### 2. Service Account Authentication (Backend Services)

For backend services that need to operate on behalf of users or perform administrative tasks.

```python
# Initialize with API key (obtained from PUGUH dashboard)
client = PuguhClient(
    base_url="https://api.puguh.io",
    api_key="pk_live_xxxxxxxxxxxx"  # Service account key
)

# Operate on specific tenant
client.set_tenant_context(tenant_id="tenant_uuid")

# Or impersonate user (admin only)
client.set_user_context(user_id="user_uuid")
```

### 3. OAuth Integration

Redirect users to PUGUH for authentication.

```python
# Generate OAuth URL
oauth_url = client.auth.get_oauth_url(
    provider="google",  # google, github
    redirect_uri="https://yourapp.com/callback",
    state="random_state_string"
)

# Handle callback
tokens = await client.auth.exchange_oauth_code(
    provider="google",
    code="oauth_code_from_callback",
    redirect_uri="https://yourapp.com/callback"
)
```

---

## Token Validation (For Your Backend)

When users make requests to YOUR backend, you need to validate their PUGUH tokens.

### Middleware Example (Python/FastAPI)

```python
from fastapi import Request, HTTPException, Depends
from puguh_sdk import PuguhClient

# Initialize SDK with service account
puguh = PuguhClient(
    base_url="https://api.puguh.io",
    api_key="pk_live_xxxxxxxxxxxx"
)

async def validate_puguh_token(request: Request):
    """Middleware to validate PUGUH tokens."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")

    token = auth_header.replace("Bearer ", "")

    try:
        # Validate token with PUGUH
        user_context = await puguh.auth.validate_token(token)

        # Attach to request state
        request.state.user_id = user_context.user_id
        request.state.tenant_id = user_context.tenant_id
        request.state.roles = user_context.roles

        return user_context
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {str(e)}")

# Use in routes
@app.get("/api/decisions")
async def list_decisions(
    user: UserContext = Depends(validate_puguh_token)
):
    # user.user_id, user.tenant_id, user.roles available
    decisions = await repository.find_by_tenant(user.tenant_id)
    return decisions
```

### Middleware Example (TypeScript/Express)

```typescript
import { PuguhClient, UserContext } from '@puguh/sdk';
import { Request, Response, NextFunction } from 'express';

const puguh = new PuguhClient({
  baseUrl: 'https://api.puguh.io',
  apiKey: 'pk_live_xxxxxxxxxxxx'
});

// Extend Request type
declare global {
  namespace Express {
    interface Request {
      userContext?: UserContext;
    }
  }
}

export async function validatePuguhToken(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing authorization header' });
  }

  const token = authHeader.replace('Bearer ', '');

  try {
    const userContext = await puguh.auth.validateToken(token);
    req.userContext = userContext;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Use in routes
app.get('/api/decisions', validatePuguhToken, async (req, res) => {
  const { tenantId } = req.userContext!;
  const decisions = await repository.findByTenant(tenantId);
  res.json(decisions);
});
```

---

## User Context (JWT Claims)

When you validate a token, you receive user context with these claims:

```typescript
interface UserContext {
  user_id: string;           // UUID
  email: string;
  display_name: string;

  tenant_id: string;         // Current tenant context
  tenant_name: string;
  tenant_plan: 'free' | 'starter' | 'pro' | 'enterprise';

  project_id?: string;       // Current project (if selected)
  project_name?: string;

  roles: string[];           // ['owner', 'mantra:admin', 'mantra:editor']

  subscriptions: {
    [product: string]: {
      plan: string;
      status: 'active' | 'trial' | 'expired';
      expires_at: string;
    }
  };

  iat: number;               // Issued at
  exp: number;               // Expires at
}
```

### Role-Based Access Control

```python
# Check roles in your app
def require_role(required_role: str):
    def decorator(func):
        async def wrapper(request, user: UserContext, *args, **kwargs):
            if required_role not in user.roles:
                raise HTTPException(403, f"Role '{required_role}' required")
            return await func(request, user, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/api/admin/settings")
@require_role("admin")
async def update_settings(user: UserContext):
    # Only admins can access
    pass
```

---

## Tenant Isolation

All data in your app should be scoped by `tenant_id`:

```python
# Repository example
class DecisionRepository:
    async def find_all(self, tenant_id: str) -> List[Decision]:
        """Always filter by tenant_id."""
        return await self.db.query(
            "SELECT * FROM decisions WHERE tenant_id = $1",
            tenant_id
        )

    async def create(self, tenant_id: str, data: CreateDecisionInput) -> Decision:
        """Always include tenant_id."""
        return await self.db.query(
            "INSERT INTO decisions (tenant_id, ...) VALUES ($1, ...) RETURNING *",
            tenant_id, ...
        )
```

---

## Subscription Checking

Check if user has access to your product:

```python
async def require_subscription(user: UserContext, product: str = "mantra"):
    """Check if user has active subscription to product."""
    sub = user.subscriptions.get(product)

    if not sub:
        raise HTTPException(402, f"Subscription to {product} required")

    if sub["status"] == "expired":
        raise HTTPException(402, f"Subscription to {product} has expired")

    return sub

# Usage
@app.get("/api/decisions")
async def list_decisions(user: UserContext = Depends(validate_puguh_token)):
    await require_subscription(user, "mantra")
    # User has active MANTRA subscription
    ...
```

---

## Error Handling

```python
from puguh_sdk.exceptions import (
    PuguhAuthError,
    PuguhTenantError,
    PuguhRateLimitError,
    PuguhValidationError,
)

try:
    user = await client.auth.login(email, password)
except PuguhAuthError as e:
    # Invalid credentials, expired token, etc.
    print(f"Auth error: {e.code} - {e.message}")
except PuguhTenantError as e:
    # Tenant not found, no access, etc.
    print(f"Tenant error: {e.code} - {e.message}")
except PuguhRateLimitError as e:
    # Too many requests
    print(f"Rate limited. Retry after: {e.retry_after}")
except PuguhValidationError as e:
    # Invalid input
    print(f"Validation error: {e.errors}")
```

---

## SDK Configuration

```python
client = PuguhClient(
    base_url="https://api.puguh.io",
    api_key="pk_live_xxxxxxxxxxxx",

    # Optional configuration
    timeout=30,                    # Request timeout (seconds)
    max_retries=3,                 # Auto-retry on failure
    retry_delay=1,                 # Initial retry delay (seconds)

    # Hooks
    on_token_refresh=lambda t: save_token(t),  # Called when token refreshed
    on_error=lambda e: log_error(e),           # Called on any error
)
```

---

## API Reference

### Auth Client

| Method | Description |
|--------|-------------|
| `register(email, password, display_name)` | Register new user |
| `login(email, password)` | Login and get tokens |
| `refresh_token(refresh_token)` | Refresh access token |
| `validate_token(access_token)` | Validate token and get user context |
| `logout(access_token)` | Invalidate token |
| `verify_email(token)` | Verify email address |
| `forgot_password(email)` | Request password reset |
| `reset_password(token, new_password)` | Reset password |
| `get_oauth_url(provider, redirect_uri, state)` | Get OAuth redirect URL |
| `exchange_oauth_code(provider, code, redirect_uri)` | Exchange OAuth code |

### Tenant Client

| Method | Description |
|--------|-------------|
| `create(name, billing_email)` | Create organization |
| `list()` | List user's organizations |
| `get(tenant_id)` | Get organization details |
| `update(tenant_id, data)` | Update organization |
| `delete(tenant_id)` | Delete organization (soft) |
| `invite_member(tenant_id, email, role)` | Invite member |
| `list_members(tenant_id)` | List members |
| `update_member_role(tenant_id, user_id, role)` | Change member role |
| `remove_member(tenant_id, user_id)` | Remove member |
| `accept_invitation(tenant_id, invitation_id)` | Accept invitation |
| `decline_invitation(tenant_id, invitation_id)` | Decline invitation |

### Project Client

| Method | Description |
|--------|-------------|
| `create(tenant_id, name, description)` | Create project |
| `list(tenant_id)` | List tenant's projects |
| `get(project_id)` | Get project details |
| `update(project_id, data)` | Update project |
| `archive(project_id)` | Archive project |
| `add_member(project_id, user_id, role)` | Add project member |
| `list_members(project_id)` | List project members |
| `remove_member(project_id, user_id)` | Remove project member |

### Billing Client

| Method | Description |
|--------|-------------|
| `get_plans()` | List available plans |
| `get_subscription(tenant_id)` | Get current subscription |
| `create_subscription(tenant_id, plan_id, product)` | Create subscription |
| `cancel_subscription(tenant_id, subscription_id)` | Cancel subscription |
| `get_invoices(tenant_id)` | List invoices |
| `get_usage(tenant_id)` | Get usage metrics |

---

## Examples

### Full Integration Example (MANTRA-like App)

See `/examples/mantra-integration/` for complete example including:
- FastAPI backend with PUGUH auth middleware
- React frontend with PUGUH SDK
- Tenant-scoped data access
- Role-based UI rendering

### Service-to-Service Example

See `/examples/service-integration/` for:
- Background worker authentication
- Admin operations
- Bulk user management

---

## Support

- Documentation: https://docs.puguh.io/sdk
- GitHub Issues: https://github.com/arsaka-puguh/sdk/issues
- Discord: https://discord.gg/arsaka-puguh
