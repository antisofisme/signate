# Security & Authentication Requirements

> **Date**: 2025-12-07
> **Status**: Draft
> **Compliance**: OWASP Top 10, SOC 2 Type II ready

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SECURITY ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  AUTHENTICATION LAYER                                           │   │
│  │  - Platform Auth (owner_users) → Platform JWT                   │   │
│  │  - Community Auth (users) → Community JWT                       │   │
│  │  - Separate token issuers, separate validation                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  AUTHORIZATION LAYER                                            │   │
│  │  - Platform: Role-based (5 owner roles)                         │   │
│  │  - Community: RBAC per organization                             │   │
│  │  - App-level: Feature flags per tier                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  DATA PROTECTION LAYER                                          │   │
│  │  - Multi-tenant isolation                                       │   │
│  │  - Encryption at rest & in transit                              │   │
│  │  - Field-level encryption for sensitive data                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Authentication

### 1.1 Authentication Flows

#### 1.1.1 Platform Authentication (Owner System)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PLATFORM AUTH FLOW                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Login    │───►│ Validate │───►│ Generate │───►│ Return   │
│ Request  │    │ Creds    │    │ Tokens   │    │ Response │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ email    │   │ Check    │   │ Platform │   │ access_  │
│ password │   │ owner_   │   │ JWT with │   │ token    │
│          │   │ users    │   │ owner    │   │ refresh_ │
│          │   │ table    │   │ claims   │   │ token    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘

Platform JWT Claims:
{
  "iss": "platform.domain.com",
  "sub": "owner:123",
  "type": "platform",
  "role": "super_admin",
  "permissions": ["manage_tenants", "manage_billing", ...],
  "exp": 1702000000,
  "iat": 1702000000
}
```

#### 1.1.2 Community Authentication

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMMUNITY AUTH FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Login    │───►│ Validate │───►│ Load Org │───►│ Generate │
│ Request  │    │ Creds    │    │ Context  │    │ Tokens   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ email    │   │ Check    │   │ Get user │   │ Community│
│ password │   │ users    │   │ org      │   │ JWT with │
│ org_id?  │   │ table    │   │ assign-  │   │ org      │
│          │   │          │   │ ments    │   │ context  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘

Community JWT Claims:
{
  "iss": "community.domain.com",
  "sub": "user:456",
  "type": "community",
  "tenant_id": 1,
  "organization_id": 2,
  "organization_code": "HGI-BALI",
  "role": "admin",
  "permissions": ["manage_users", "view_reports", ...],
  "app_access": ["pms", "pos", "accounting"],
  "exp": 1702000000,
  "iat": 1702000000
}
```

#### 1.1.3 Organization Context Switch

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORG CONTEXT SWITCH FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

Current Token                    Switch Request              New Token
┌──────────────┐                ┌──────────────┐            ┌──────────────┐
│ org_id: 1    │  ─────────►   │ org_id: 2    │  ────────► │ org_id: 2    │
│ role: admin  │                │ (requested)  │            │ role: manager│
│ apps: [...]  │                └──────────────┘            │ apps: [...]  │
└──────────────┘                      │                     └──────────────┘
                                      ▼
                              ┌──────────────┐
                              │ Validate:    │
                              │ - User has   │
                              │   assignment │
                              │ - Org active │
                              │ - Same tenant│
                              └──────────────┘

Rules:
- Users can only switch to orgs within same tenant hierarchy
- New token issued with new org context
- Old token remains valid until expiry
- Session can be invalidated server-side
```

### 1.2 Token Specification

#### 1.2.1 Access Token

| Property | Value |
|----------|-------|
| Algorithm | RS256 (RSA + SHA256) |
| Expiry | 1 hour (3600 seconds) |
| Format | JWT (RFC 7519) |
| Refresh | Via refresh token |

**Structure:**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id-2025-01"
  },
  "payload": {
    "iss": "https://auth.domain.com",
    "sub": "user:123",
    "aud": ["api.domain.com"],
    "exp": 1702003600,
    "iat": 1702000000,
    "jti": "unique-token-id",
    "type": "access",
    "tenant_id": 1,
    "organization_id": 2,
    "role": "admin",
    "permissions": ["perm1", "perm2"]
  }
}
```

#### 1.2.2 Refresh Token

| Property | Value |
|----------|-------|
| Algorithm | RS256 |
| Expiry | 30 days |
| Storage | HttpOnly cookie + DB |
| Rotation | On use |
| Revocation | Supported |

**Refresh Token Rotation:**
```
1. Client sends refresh_token
2. Server validates token
3. Server checks token in DB (not revoked)
4. Server generates new access_token + new refresh_token
5. Server revokes old refresh_token in DB
6. Server returns new token pair
```

### 1.3 Password Requirements

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Maximum length | 128 characters |
| Complexity | At least 3 of: uppercase, lowercase, number, symbol |
| History | Cannot reuse last 5 passwords |
| Expiry | Optional, configurable (90 days default if enabled) |
| Lockout | 5 failed attempts → 15 min lockout |

**Hashing:**
```python
# Bcrypt with cost factor 12
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

### 1.4 Multi-Factor Authentication (MFA)

#### 1.4.1 Supported Methods

| Method | Implementation | Required For |
|--------|---------------|--------------|
| TOTP | RFC 6238 (Google Authenticator, Authy) | Owner team (mandatory) |
| SMS OTP | 6-digit code, 5 min expiry | Optional for users |
| Email OTP | 6-digit code, 15 min expiry | Password reset |
| Recovery Codes | 8 codes, one-time use | Account recovery |

#### 1.4.2 TOTP Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Password │───►│ MFA      │───►│ Verify   │───►│ Issue    │
│ Valid    │    │ Required │    │ TOTP     │    │ Token    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
  Success       Return         6-digit         Full
  + MFA flag    challenge      code from       access
                token          authenticator   token
```

### 1.5 Session Management

#### 1.5.1 Session Storage

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    refresh_token_hash VARCHAR(64) NOT NULL,  -- SHA256 hash
    device_info JSONB,  -- user_agent, ip, device_type
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(100)
);

CREATE INDEX idx_sessions_user_active ON sessions(user_id, is_active);
CREATE INDEX idx_sessions_token ON sessions(refresh_token_hash);
```

#### 1.5.2 Session Limits

| Scope | Limit | Action on Exceed |
|-------|-------|------------------|
| Per user | 10 active sessions | Revoke oldest |
| Per device type | 3 per type | Warn user |
| Concurrent logins | Allowed | Track all |

#### 1.5.3 Session Revocation

```python
# Revoke single session
await session_repo.revoke(session_id, reason="user_logout")

# Revoke all user sessions (password change)
await session_repo.revoke_all_for_user(user_id, reason="password_changed")

# Revoke all org sessions (user removed)
await session_repo.revoke_all_for_user_org(user_id, org_id, reason="access_revoked")
```

---

## Part 2: Authorization

### 2.1 RBAC Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       RBAC HIERARCHY                                    │
└─────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │ Permission  │
                         │ (atomic)    │
                         └──────┬──────┘
                                │ many
                                ▼
                         ┌─────────────┐
                         │    Role     │
                         │ (grouped)   │
                         └──────┬──────┘
                                │ many
                                ▼
                    ┌───────────────────────┐
                    │  User-Org Assignment  │
                    │  (contextual)         │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │    User     │         │Organization │
             └─────────────┘         └─────────────┘
```

### 2.2 Platform Roles (Owner System)

| Role | Description | Permissions |
|------|-------------|-------------|
| `super_admin` | Full system access | `*` |
| `admin` | Tenant & subscription management | `tenants.*`, `subscriptions.*`, `apps.read`, `users.read` |
| `finance` | Billing & payment only | `invoices.*`, `payments.*`, `tenants.read`, `subscriptions.read` |
| `support` | Read-only + limited actions | `*.read`, `tenants.support_actions` |
| `viewer` | Read-only access | `*.read` |

### 2.3 Community Roles (Per Organization)

| Role | Description | Typical Permissions |
|------|-------------|---------------------|
| `owner` | Organization owner | `*` (all permissions) |
| `admin` | Full admin access | `users.*`, `roles.*`, `settings.*`, `apps.*` |
| `manager` | Operational management | `apps.*`, `reports.*`, `users.read` |
| `operator` | Day-to-day operations | `apps.use`, `reports.read` |
| `viewer` | Read-only | `*.read` |

### 2.4 Permission Structure

```
Permission Format: {resource}.{action}

Resources:
- users
- roles
- organizations
- settings
- reports
- [app_specific]: pms, pos, accounting, etc.

Actions:
- create
- read
- update
- delete
- manage (all CRUD)
- use (app-specific)
- export
- approve

Examples:
- users.create
- users.read
- users.manage (= create + read + update + delete)
- pms.use
- reports.export
- invoices.approve
```

### 2.5 Permission Check Flow

```python
# Middleware/Decorator approach
@require_permission("users.create")
async def create_user(request: Request, dto: CreateUserDTO):
    # Only reaches here if permission check passes
    pass

# Manual check in use case
class CreateUserUseCase:
    async def execute(self, actor: Actor, dto: CreateUserDTO):
        if not actor.has_permission("users.create"):
            raise PermissionDeniedError("Cannot create users")

        # Additional checks
        if dto.role == "admin" and not actor.has_permission("users.assign_admin"):
            raise PermissionDeniedError("Cannot assign admin role")
```

### 2.6 Feature Access Control

```python
# Tier-based feature access
class FeatureGuard:
    async def check_feature(self, org_id: int, feature_code: str) -> bool:
        subscription = await self.sub_repo.get_active_for_org(org_id)
        if not subscription:
            return False

        tier_features = await self.tier_repo.get_features(subscription.tier_id)
        feature = tier_features.get(feature_code)

        if not feature or not feature.is_enabled:
            return False

        # Check limits
        if feature.limit_value:
            current_usage = await self.usage_repo.get_current(org_id, feature_code)
            if current_usage >= feature.limit_value:
                return False

        return True

# Usage in route
@router.post("/reservations")
async def create_reservation(
    request: Request,
    dto: CreateReservationDTO,
    feature_guard: FeatureGuard = Depends()
):
    if not await feature_guard.check_feature(request.org_id, "RESERVATION"):
        raise FeatureNotAvailableError("Reservation feature not available in your tier")
```

---

## Part 3: Data Protection

### 3.1 Multi-Tenant Isolation

#### 3.1.1 Database Level

```sql
-- Row-Level Security (RLS) Example
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON transactions
    USING (tenant_id = current_setting('app.current_tenant_id')::INTEGER);

-- Application sets context before query
SET app.current_tenant_id = '123';
SELECT * FROM transactions;  -- Only returns tenant 123 data
```

#### 3.1.2 Application Level

```python
# Middleware to enforce tenant context
class TenantContextMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract from JWT
        tenant_id = request.state.token.get("tenant_id")

        # Set in request state
        request.state.tenant_id = tenant_id

        # Set in database session
        await request.state.db.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )

        return await call_next(request)

# Repository always filters by tenant
class BaseRepository:
    def _apply_tenant_filter(self, query):
        return query.filter(self.model.tenant_id == self.tenant_id)
```

### 3.2 Encryption

#### 3.2.1 Data at Rest

| Data Type | Encryption | Method |
|-----------|------------|--------|
| Database | Enabled | PostgreSQL TDE or Volume encryption |
| File Storage | Enabled | Server-side encryption (SSE-S3 equivalent) |
| Backups | Enabled | AES-256 |
| Logs | Masked | PII removed/masked before storage |

#### 3.2.2 Data in Transit

| Protocol | Version | Configuration |
|----------|---------|---------------|
| TLS | 1.3 (minimum 1.2) | Strong cipher suites only |
| HTTPS | Enforced | HSTS enabled |
| Internal | mTLS | Service-to-service |

#### 3.2.3 Field-Level Encryption

```python
# Sensitive fields encrypted at application level
from cryptography.fernet import Fernet

class EncryptedField:
    """Encrypt sensitive data before storage"""

    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage in model
class Tenant(Base):
    tax_id = Column(String(200))  # Stored encrypted

    @property
    def decrypted_tax_id(self) -> str:
        return encryption_service.decrypt(self.tax_id)

    @decrypted_tax_id.setter
    def decrypted_tax_id(self, value: str):
        self.tax_id = encryption_service.encrypt(value)

# Encrypted fields list
ENCRYPTED_FIELDS = [
    "tenants.tax_id",
    "tenants.billing_email",
    "users.phone",
    "payments.card_last_four",
]
```

### 3.3 PII Handling

#### 3.3.1 PII Classification

| Level | Data Types | Handling |
|-------|-----------|----------|
| High | Tax ID, Bank Account, Card Number | Encrypted, Masked in logs, Limited access |
| Medium | Email, Phone, Address | Encrypted at rest, Audit access |
| Low | Name, Organization Name | Standard protection |

#### 3.3.2 PII Masking

```python
# Masking functions
def mask_email(email: str) -> str:
    """john.doe@example.com → j***@e***.com"""
    local, domain = email.split("@")
    return f"{local[0]}***@{domain[0]}***.{domain.split('.')[-1]}"

def mask_phone(phone: str) -> str:
    """+62-812-3456789 → +62-***-***6789"""
    return phone[:-4].replace(phone[4:-4], "***-***") + phone[-4:]

def mask_tax_id(tax_id: str) -> str:
    """01.234.567.8-901.000 → **.***.***.*-***.000"""
    return tax_id[:-3].replace(tax_id[:-3], "**.***.***.*-***") + tax_id[-3:]

# Auto-masking in logs
class PIIMaskingFilter(logging.Filter):
    PATTERNS = {
        r'\b[\w.-]+@[\w.-]+\.\w+\b': mask_email,
        r'\+\d{2,3}-\d{3,4}-\d{6,8}': mask_phone,
    }

    def filter(self, record):
        for pattern, mask_fn in self.PATTERNS.items():
            record.msg = re.sub(pattern, lambda m: mask_fn(m.group()), str(record.msg))
        return True
```

### 3.4 Data Retention & Deletion

#### 3.4.1 Retention Periods

| Data Type | Retention | Archival |
|-----------|-----------|----------|
| Active tenant data | Perpetual | N/A |
| Closed tenant data | 90 days hot, then archive | 10 years cold storage |
| Audit logs | 10 years | Compressed after 1 year |
| Session logs | 90 days | Aggregated after 30 days |
| Deleted records | 30 days soft delete | Permanent delete after |

#### 3.4.2 Right to Deletion (GDPR)

```python
class DataDeletionService:
    async def process_deletion_request(self, user_id: int):
        """Process GDPR deletion request"""

        # 1. Anonymize personal data
        await self.user_repo.anonymize(user_id, {
            "name": "Deleted User",
            "email": f"deleted_{user_id}@deleted.local",
            "phone": None,
        })

        # 2. Remove from all organizations
        await self.assignment_repo.remove_all_for_user(user_id)

        # 3. Revoke all sessions
        await self.session_repo.revoke_all_for_user(user_id)

        # 4. Log deletion
        await self.audit_repo.log(
            action="user_deleted",
            entity_type="user",
            entity_id=user_id,
            reason="gdpr_request"
        )

        # 5. Schedule hard delete of orphaned data
        await self.scheduler.schedule(
            "hard_delete_user_data",
            user_id=user_id,
            run_at=datetime.now() + timedelta(days=30)
        )
```

---

## Part 4: API Security

### 4.1 Request Validation

```python
# Input validation with Pydantic
class CreateUserDTO(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+\d{2,3}-\d{3,4}-\d{6,8}$')

    @field_validator('name')
    def validate_name(cls, v):
        # Prevent XSS in name
        if re.search(r'[<>"\']', v):
            raise ValueError('Invalid characters in name')
        return v.strip()

# SQL Injection prevention - always use parameterized queries
# ✅ Good
await db.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {"id": user_id}
)

# ❌ Bad - Never do this
await db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### 4.2 Rate Limiting

```python
# Rate limiting configuration
RATE_LIMITS = {
    "auth.login": {"requests": 10, "window": 60},  # 10 per minute
    "auth.register": {"requests": 5, "window": 3600},  # 5 per hour
    "api.read": {"requests": 100, "window": 60},  # 100 per minute
    "api.write": {"requests": 30, "window": 60},  # 30 per minute
    "api.bulk": {"requests": 5, "window": 60},  # 5 per minute
}

# Implementation with Redis
class RateLimiter:
    async def check(self, key: str, limit: dict) -> bool:
        current = await self.redis.incr(f"ratelimit:{key}")
        if current == 1:
            await self.redis.expire(f"ratelimit:{key}", limit["window"])
        return current <= limit["requests"]

# Response headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702000060
```

### 4.3 CORS Configuration

```python
# FastAPI CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://platform.domain.com",
        "https://community.domain.com",
        "https://app.domain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,
)
```

### 4.4 Security Headers

```python
# Security headers middleware
class SecurityHeadersMiddleware:
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in self.HEADERS.items():
            response.headers[header] = value
        return response
```

### 4.5 Request Signing (Webhooks)

```python
# Webhook signature verification
import hmac
import hashlib

class WebhookSecurity:
    def sign_payload(self, payload: bytes, secret: str) -> str:
        """Generate HMAC-SHA256 signature"""
        return hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected = self.sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected)

# Webhook endpoint
@router.post("/webhooks/payment")
async def handle_payment_webhook(
    request: Request,
    x_signature: str = Header(...)
):
    payload = await request.body()

    if not webhook_security.verify_signature(
        payload, x_signature, settings.PAYMENT_WEBHOOK_SECRET
    ):
        raise HTTPException(401, "Invalid signature")

    # Process webhook
```

---

## Part 5: Audit & Compliance

### 5.1 Audit Logging

#### 5.1.1 What to Log

| Category | Events |
|----------|--------|
| Authentication | Login success/failure, logout, password change, MFA setup |
| Authorization | Permission denied, role change |
| Data Access | Read sensitive data, export data |
| Data Modification | Create, update, delete any record |
| Admin Actions | User management, settings changes |
| System Events | API errors, security alerts |

#### 5.1.2 Audit Log Structure

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Who
    actor_type VARCHAR(20) NOT NULL,  -- 'user', 'system', 'api_key'
    actor_id INTEGER,
    actor_email VARCHAR(255),

    -- What
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),

    -- Context
    tenant_id INTEGER,
    organization_id INTEGER,

    -- Details
    changes JSONB,  -- {field: {old, new}}
    metadata JSONB,  -- Additional context

    -- Request info
    ip_address INET,
    user_agent TEXT,
    request_id UUID,

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_audit_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at DESC);
```

#### 5.1.3 Audit Log Entry Example

```json
{
  "id": 12345,
  "actor_type": "user",
  "actor_id": 456,
  "actor_email": "admin@tenant.com",
  "action": "user.update",
  "resource_type": "user",
  "resource_id": "789",
  "tenant_id": 1,
  "organization_id": 2,
  "changes": {
    "role": {
      "old": "viewer",
      "new": "manager"
    }
  },
  "metadata": {
    "reason": "Promotion",
    "approved_by": 456
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-12-07T10:30:00Z"
}
```

### 5.2 Security Monitoring

#### 5.2.1 Alerts Configuration

| Alert | Condition | Severity |
|-------|-----------|----------|
| Brute Force | 10+ failed logins in 5 min | High |
| Account Takeover | Login from new device + sensitive action | High |
| Privilege Escalation | Role changed to admin | Medium |
| Data Export | Large export operation | Medium |
| API Abuse | Rate limit exceeded 3x | Medium |
| Suspicious IP | Login from blocked country | Low |

#### 5.2.2 Monitoring Implementation

```python
# Security event processor
class SecurityMonitor:
    async def process_event(self, event: SecurityEvent):
        # Check against rules
        for rule in self.rules:
            if await rule.matches(event):
                await self.create_alert(rule, event)

        # Update metrics
        await self.metrics.increment(f"security.{event.type}")

    async def check_brute_force(self, user_id: int, ip: str) -> bool:
        key = f"failed_login:{user_id}:{ip}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 300)  # 5 minutes

        if count >= 10:
            await self.create_alert(
                "brute_force",
                {"user_id": user_id, "ip": ip, "count": count}
            )
            return True
        return False
```

### 5.3 Compliance Requirements

#### 5.3.1 SOC 2 Type II Controls

| Control | Implementation |
|---------|---------------|
| CC1.1 - Integrity & Ethics | Code of conduct, background checks |
| CC2.1 - Board Oversight | Security policies, regular reviews |
| CC3.1 - Risk Assessment | Annual risk assessment, threat modeling |
| CC4.1 - Monitoring | Continuous monitoring, SIEM integration |
| CC5.1 - Control Activities | Access controls, change management |
| CC6.1 - Logical Access | RBAC, MFA, session management |
| CC7.1 - System Operations | Incident response, backup procedures |
| CC8.1 - Change Management | Version control, deployment approval |
| CC9.1 - Risk Mitigation | Vendor management, insurance |

#### 5.3.2 GDPR Compliance

| Requirement | Implementation |
|-------------|---------------|
| Lawful Basis | Consent tracking, legitimate interest documentation |
| Data Minimization | Only collect necessary data |
| Right to Access | Data export API |
| Right to Deletion | Deletion request workflow |
| Data Portability | Standard export formats |
| Breach Notification | Incident response plan, 72-hour notification |
| DPO | Data Protection Officer contact |

---

## Part 6: Infrastructure Security

### 6.1 Network Security

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       NETWORK ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

                        Internet
                            │
                            ▼
                    ┌───────────────┐
                    │   WAF/CDN     │  DDoS protection, caching
                    │  (Cloudflare) │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Load Balancer │  SSL termination
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   API Server  │ │   API Server  │ │   API Server  │
    │   (Container) │ │   (Container) │ │   (Container) │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │               │               │
            └───────────────┼───────────────┘
                            │ Private Network
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   PostgreSQL  │ │     Redis     │ │   RabbitMQ    │
    │   (Primary)   │ │   (Cluster)   │ │   (Cluster)   │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### 6.2 Secret Management

```python
# Environment-based secrets (development)
DATABASE_URL=os.getenv("DATABASE_URL")

# Vault integration (production)
from hvac import Client as VaultClient

class SecretManager:
    def __init__(self):
        self.vault = VaultClient(
            url=os.getenv("VAULT_ADDR"),
            token=os.getenv("VAULT_TOKEN")
        )

    def get_secret(self, path: str) -> dict:
        return self.vault.secrets.kv.v2.read_secret_version(path)["data"]["data"]

    # Usage
    db_creds = secret_manager.get_secret("database/production")
    DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@..."
```

### 6.3 Container Security

```dockerfile
# Dockerfile security best practices
FROM python:3.11-slim

# Non-root user
RUN useradd -m -u 1000 appuser

# Minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Read-only filesystem where possible
WORKDIR /app

# Copy with specific ownership
COPY --chown=appuser:appuser . .

# Run as non-root
USER appuser

# No shell for security
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## Part 7: Incident Response

### 7.1 Security Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P1 - Critical | Active breach, data exposure | Immediate (< 15 min) | Data leak, ransomware |
| P2 - High | Potential breach, vulnerability | < 1 hour | Failed intrusion, critical CVE |
| P3 - Medium | Security degradation | < 4 hours | Suspicious activity, minor CVE |
| P4 - Low | Monitoring alert | < 24 hours | Failed logins, config drift |

### 7.2 Incident Response Procedure

```
1. DETECTION
   - Automated alerts (SIEM, monitoring)
   - User reports
   - Third-party notification

2. TRIAGE
   - Assess severity
   - Identify affected systems
   - Initial containment if needed

3. CONTAINMENT
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

4. INVESTIGATION
   - Collect evidence (logs, artifacts)
   - Determine root cause
   - Identify scope of impact

5. ERADICATION
   - Remove malware/vulnerability
   - Patch systems
   - Reset credentials

6. RECOVERY
   - Restore from clean backups
   - Verify system integrity
   - Gradual service restoration

7. POST-INCIDENT
   - Incident report
   - Lessons learned
   - Update procedures
```

### 7.3 Contact Information

```
Security Team:
- Email: security@domain.com
- Phone: +62-xxx-xxx-xxxx (24/7)
- Slack: #security-incidents

Escalation:
1. On-call engineer (PagerDuty)
2. Security lead
3. CTO
4. Legal (if data breach)
```

---

*Last Updated: 2025-12-07*
