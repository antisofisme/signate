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

### 1.6 Hybrid Authentication (Identity Providers)

Platform mendukung **multiple authentication methods** yang dapat dikonfigurasi per organization.

#### 1.6.1 Supported Identity Providers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUPPORTED IDENTITY PROVIDERS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1 (MVP) ✅                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Provider        │ Type          │ Use Case                         │   │
│  ├─────────────────┼───────────────┼──────────────────────────────────┤   │
│  │ Google OAuth    │ Social/Work   │ Quick login, Google Workspace    │   │
│  │ Email+Password  │ Traditional   │ Fallback, no Google users        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PHASE 2 (Future) 📋                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Apple Sign-in   │ Social        │ iOS users                        │   │
│  │ Microsoft OAuth │ Work          │ Corporate/Microsoft 365 users    │   │
│  │ SAML 2.0 SSO    │ Enterprise    │ Hotel chains with Okta/Azure AD  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.6.2 Organization Auth Configuration

```yaml
# Per-organization auth settings
organization_auth_config:
  org_id: 123
  org_code: "grandindo"

  # Enabled login methods
  login_methods:
    google_oauth: true       # Allow Google login
    email_password: true     # Allow traditional login
    apple_signin: false      # Future
    microsoft_oauth: false   # Future
    saml_sso: false          # Enterprise future

  # Google OAuth settings
  google_oauth_config:
    allow_any_google: false  # false = must link first via invitation
    allowed_domains: []      # Empty = any domain, or ["company.com"] for Google Workspace

  # Password policy (if email_password enabled)
  password_policy:
    min_length: 8
    require_uppercase: true
    require_number: true
    require_symbol: false
    expire_days: 0           # 0 = never expire

  # MFA settings
  mfa_config:
    required_for_roles: ["owner", "admin", "manager", "accountant"]
    methods: ["totp", "sms"]
```

#### 1.6.3 Google OAuth Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOOGLE OAUTH LOGIN FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User clicks "Sign in with Google"                                      │
│                     │                                                       │
│                     ▼                                                       │
│  2. Redirect to Google OAuth consent screen                                │
│     - Scopes: openid, email, profile                                       │
│                     │                                                       │
│                     ▼                                                       │
│  3. User grants permission, Google returns id_token                        │
│                     │                                                       │
│                     ▼                                                       │
│  4. Backend validates id_token with Google                                 │
│     - Verify signature                                                     │
│     - Check expiry                                                         │
│     - Extract: google_id, email, name                                      │
│                     │                                                       │
│                     ▼                                                       │
│  5. Lookup user by google_id + org_code                                    │
│     ┌─────────────────────────────────────────┐                            │
│     │ Found?                                   │                            │
│     │ ├─ YES → Issue JWT (login success)      │                            │
│     │ └─ NO  → Check org config               │                            │
│     │         ├─ allow_any_google: true       │                            │
│     │         │   → Auto-create user? (risky) │                            │
│     │         └─ allow_any_google: false      │                            │
│     │             → "Account not linked"      │                            │
│     └─────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.7 User Invitation & Account Linking

User onboarding menggunakan **invitation-based flow** dimana admin mengirim undangan dan user memilih cara login.

#### 1.7.1 Invitation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INVITATION FLOW                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Admin Creates User                                                │
│  ───────────────────────────────────────────────────────────────────────── │
│  Admin Dashboard → Users → Add New User                                    │
│                                                                             │
│  ┌─────────────────────────────────────────┐                               │
│  │ Name:       [John Doe            ]      │                               │
│  │ Work Email: [john@company.com    ]      │ ← For invitation              │
│  │ Role:       [Front Office Staff  ▼]     │                               │
│  │ Department: [Front Office        ▼]     │                               │
│  │                                         │                               │
│  │ [✓] Send invitation email              │                               │
│  │                                         │                               │
│  │ [Create User]                           │                               │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
│  STEP 2: System Sends Email                                                │
│  ───────────────────────────────────────────────────────────────────────── │
│  To: john@company.com                                                      │
│  Subject: You're invited to {Organization Name}                            │
│                                                                             │
│  Content:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Hi John,                                                            │   │
│  │                                                                      │   │
│  │ You've been invited to join Grand Indo Hotel system.               │   │
│  │ Click the button below to set up your account.                     │   │
│  │                                                                      │   │
│  │ [Set Up My Account]                                                 │   │
│  │                                                                      │   │
│  │ Link expires: {7 days from now}                                    │   │
│  │                                                                      │   │
│  │ If you didn't expect this, ignore this email.                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STEP 3: User Clicks Link → Account Setup                                  │
│  ───────────────────────────────────────────────────────────────────────── │
│  URL: https://{org}.app.com/setup?token={invitation_token}                 │
│                                                                             │
│  ┌─────────────────────────────────────────┐                               │
│  │                                         │                               │
│  │  Welcome, John!                         │                               │
│  │  Complete your account setup            │                               │
│  │                                         │                               │
│  │  Choose how you want to sign in:       │                               │
│  │                                         │                               │
│  │  ┌─────────────────────────────────┐   │                               │
│  │  │ 🔵 Link Google Account          │   │ ← Recommended                 │
│  │  │    Fast & secure login          │   │                               │
│  │  └─────────────────────────────────┘   │                               │
│  │                                         │                               │
│  │  ─────────── OR ───────────            │                               │
│  │                                         │                               │
│  │  ┌─────────────────────────────────┐   │                               │
│  │  │ 🔑 Create Password              │   │ ← Traditional                 │
│  │  └─────────────────────────────────┘   │                               │
│  │                                         │                               │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
│  STEP 4a: Google Linking                                                   │
│  ───────────────────────────────────────────────────────────────────────── │
│  1. User clicks "Link Google Account"                                      │
│  2. Google OAuth popup → select account                                    │
│  3. System receives google_id_token                                        │
│  4. System stores: google_id, google_email, google_linked_at              │
│  5. Account activated → redirect to dashboard                              │
│                                                                             │
│  STEP 4b: Password Setup                                                   │
│  ───────────────────────────────────────────────────────────────────────── │
│  1. User clicks "Create Password"                                          │
│  2. Enter password + confirm password                                      │
│  3. System validates password policy                                       │
│  4. System stores: password_hash                                           │
│  5. Account activated → redirect to dashboard                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.7.2 User Database Schema

```sql
-- Users table with Google linking support
CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    -- Basic info
    employee_code VARCHAR(50),                -- Optional employee ID
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,              -- Work email (for invitations)
    phone VARCHAR(50),

    -- Department & Role
    department_id INTEGER REFERENCES departments(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),

    -- Password authentication (optional)
    password_hash VARCHAR(255),               -- NULL if using Google only
    password_changed_at TIMESTAMPTZ,

    -- Google OAuth linking
    google_id VARCHAR(255) UNIQUE,            -- Google's unique user ID
    google_email VARCHAR(255),                -- Google email (can differ from work email)
    google_linked_at TIMESTAMPTZ,

    -- Future: Other providers
    apple_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,

    -- Invitation tracking
    invitation_token VARCHAR(100),
    invitation_token_hash VARCHAR(64),        -- SHA256 for lookup
    invitation_sent_at TIMESTAMPTZ,
    invitation_expires_at TIMESTAMPTZ,
    invitation_accepted_at TIMESTAMPTZ,
    invited_by INTEGER REFERENCES users(id),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'invited',
    -- invited: awaiting setup
    -- active: can login
    -- inactive: disabled by admin
    -- locked: too many failed attempts

    -- Audit
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_user_org_email UNIQUE (organization_id, email),
    CONSTRAINT chk_user_status CHECK (status IN ('invited', 'active', 'inactive', 'locked'))
);

-- Indexes
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_google ON users(google_id) WHERE google_id IS NOT NULL;
CREATE INDEX idx_users_invitation ON users(invitation_token_hash) WHERE invitation_token_hash IS NOT NULL;
CREATE INDEX idx_users_status ON users(organization_id, status);

-- Auth audit log
CREATE TABLE user_auth_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    -- login_success, login_failed, logout, password_changed,
    -- google_linked, google_unlinked, mfa_enabled, mfa_disabled,
    -- invitation_sent, invitation_accepted, account_locked, account_unlocked

    performed_by INTEGER REFERENCES users(id),  -- NULL if self, user_id if admin
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    metadata JSONB,                             -- Additional event data
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- TimescaleDB hypertable
SELECT create_hypertable('user_auth_events', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

CREATE INDEX idx_auth_events_user ON user_auth_events(user_id, created_at DESC);
CREATE INDEX idx_auth_events_type ON user_auth_events(event_type, created_at DESC);
```

#### 1.7.3 Admin Management of Linked Accounts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADMIN: USER MANAGEMENT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Users List View                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Name          │ Work Email        │ Auth Method      │ Status │ ⚙️ │   │
│  ├───────────────┼───────────────────┼──────────────────┼────────┼────┤   │
│  │ John Doe      │ john@company.com  │ 🔵 Google        │ Active │ ⚙️ │   │
│  │               │                   │ john@gmail.com   │        │    │   │
│  ├───────────────┼───────────────────┼──────────────────┼────────┼────┤   │
│  │ Mary Jane     │ mary@company.com  │ 🔵 Google + 🔑   │ Active │ ⚙️ │   │
│  │               │                   │ mary@yahoo.com   │        │    │   │
│  ├───────────────┼───────────────────┼──────────────────┼────────┼────┤   │
│  │ Bob Smith     │ bob@company.com   │ ⏳ Pending       │Invited │ ⚙️ │   │
│  ├───────────────┼───────────────────┼──────────────────┼────────┼────┤   │
│  │ Alice Wong    │ alice@company.com │ 🔑 Password only │ Active │ ⚙️ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Legend:                                                                    │
│  🔵 Google      = Google account linked                                    │
│  🔑 Password    = Password set                                             │
│  🔵 + 🔑        = Both methods available                                   │
│  ⏳ Pending     = Invitation sent, not yet setup                           │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  User Detail: John Doe                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Authentication Methods                                             │   │
│  │  ────────────────────────────────────────────────────────────────   │   │
│  │                                                                      │   │
│  │  Google Account                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │ Status:    ✅ Linked                                         │   │   │
│  │  │ Email:     johndoe.personal@gmail.com                        │   │   │
│  │  │ Linked on: 2024-01-15 10:30 WIB                              │   │   │
│  │  │                                                               │   │   │
│  │  │ [🔓 Unlink Google Account]                                   │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  Password                                                           │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │ Status:    ❌ Not set                                        │   │   │
│  │  │                                                               │   │   │
│  │  │ [📧 Send Password Setup Link]                                │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  ────────────────────────────────────────────────────────────────   │   │
│  │                                                                      │   │
│  │  Admin Actions                                                      │   │
│  │  [📧 Resend Invitation]                                            │   │
│  │  [🔄 Reset All Auth] ← Unlink all, force re-setup                  │   │
│  │  [🚫 Deactivate User]                                              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.7.4 API Endpoints

```yaml
# ============================================
# USER INVITATION & AUTH LINKING APIs
# ============================================

# Admin: Create user with invitation
POST /api/v1/admin/users
Authorization: Bearer {admin_token}
Body:
  name: "John Doe"
  email: "john@company.com"
  role_id: 5
  department_id: 2
  send_invitation: true
Response:
  id: 123
  status: "invited"
  invitation_sent_at: "2024-01-15T10:00:00Z"
  invitation_expires_at: "2024-01-22T10:00:00Z"

# Admin: Resend invitation
POST /api/v1/admin/users/{id}/resend-invitation
Authorization: Bearer {admin_token}
Response:
  success: true
  invitation_expires_at: "2024-01-22T10:00:00Z"

# Admin: Unlink Google account
DELETE /api/v1/admin/users/{id}/auth/google
Authorization: Bearer {admin_token}
Response:
  success: true
  message: "Google account unlinked"
  # User must re-link or set password to login

# Admin: Force password reset
POST /api/v1/admin/users/{id}/auth/force-password-reset
Authorization: Bearer {admin_token}
Response:
  success: true
  reset_link_sent: true

# Admin: Reset all auth (nuclear option)
POST /api/v1/admin/users/{id}/auth/reset-all
Authorization: Bearer {admin_token}
Response:
  success: true
  # Unlinks Google, clears password, sends new invitation

# ─────────────────────────────────────────────────────────────

# Public: Validate invitation token
GET /api/v1/auth/invitation/{token}
Response:
  valid: true
  user_name: "John Doe"
  organization_name: "Grand Indo Hotel"
  organization_logo: "https://cdn.../logo.png"
  expires_at: "2024-01-22T10:00:00Z"
  available_methods: ["google", "password"]

# Public: Complete setup with Google
POST /api/v1/auth/invitation/{token}/link-google
Body:
  google_id_token: "eyJhbGciOiJSUzI1NiIs..."
Response:
  success: true
  access_token: "eyJ..."
  refresh_token: "..."
  user: { id, name, email, role, ... }

# Public: Complete setup with password
POST /api/v1/auth/invitation/{token}/set-password
Body:
  password: "SecureP@ssw0rd!"
  confirm_password: "SecureP@ssw0rd!"
Response:
  success: true
  access_token: "eyJ..."
  refresh_token: "..."
  user: { id, name, email, role, ... }

# ─────────────────────────────────────────────────────────────

# Public: Login with Google
POST /api/v1/auth/login/google
Body:
  google_id_token: "eyJhbGciOiJSUzI1NiIs..."
  org_code: "grandindo"  # From subdomain
Response:
  success: true
  access_token: "eyJ..."
  refresh_token: "..."
  user: { id, name, email, role, organization, ... }

# Public: Login with password
POST /api/v1/auth/login
Body:
  email: "john@company.com"
  password: "..."
  org_code: "grandindo"
Response:
  success: true
  access_token: "eyJ..."
  refresh_token: "..."
  user: { id, name, email, role, organization, ... }
```

---

### 1.8 Guest Authentication (Public Users)

Untuk aplikasi public-facing (pms.ibe, pos.online, pms.guest_app), auth berbeda dari staff.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GUEST AUTHENTICATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POS.ONLINE (Self-Order / Online Menu)                                     │
│  ───────────────────────────────────────────────────────────────────────── │
│  Auth: NONE REQUIRED ✓                                                     │
│                                                                             │
│  • Anonymous session (session_id in cookie)                                │
│  • Optional: Phone number for order updates                                │
│  • Order linked to: table_number + session_id                              │
│  • No account needed                                                       │
│                                                                             │
│  Flow:                                                                      │
│  Scan QR → Browse menu → Add to cart → Checkout                            │
│          (no login required)                                                │
│                                                                             │
│  Payment options (configured per organization):                            │
│  • Pay now (QRIS, e-wallet) → Order auto-sent to kitchen                  │
│  • Pay later (room charge, cashier) → Staff confirms → Order sent         │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  PMS.IBE (Booking Engine)                                                  │
│  ───────────────────────────────────────────────────────────────────────── │
│  Auth: EMAIL REQUIRED ✓ (for confirmation)                                 │
│                                                                             │
│  Options:                                                                   │
│  1. Guest checkout (no account)                                            │
│     • Enter: name, email, phone                                            │
│     • Confirmation sent to email                                           │
│     • Booking code for lookup                                              │
│                                                                             │
│  2. Quick checkout with Google                                             │
│     • Click "Continue with Google"                                         │
│     • Auto-fill name & email from Google                                   │
│     • Faster checkout                                                       │
│                                                                             │
│  3. Create account (optional)                                              │
│     • Email + password                                                     │
│     • Can manage bookings later                                            │
│     • View booking history                                                 │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  PMS.GUEST_APP (Guest Mobile App)                                          │
│  ───────────────────────────────────────────────────────────────────────── │
│  Auth: BOOKING VERIFICATION ✓                                              │
│                                                                             │
│  Options:                                                                   │
│  1. Booking code + Last name                                               │
│     • Enter: BOOK-12345 + "Doe"                                            │
│     • Verify against reservation                                           │
│     • Session valid during stay                                            │
│                                                                             │
│  2. QR code from confirmation email                                        │
│     • Scan QR → auto-login                                                 │
│     • Links to specific reservation                                        │
│                                                                             │
│  3. Google (if booked with Google)                                         │
│     • Match Google email with booking email                                │
│     • Auto-find reservations                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.8.1 Guest Database Schema

```sql
-- Guests table (for booking engine & guest app)
CREATE TABLE guests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    -- Basic info
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Optional account
    password_hash VARCHAR(255),        -- NULL if guest checkout
    google_id VARCHAR(255),

    -- Verification
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,

    -- Status
    is_registered BOOLEAN DEFAULT FALSE,  -- true if created account

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_booking_at TIMESTAMPTZ,

    CONSTRAINT uq_guest_org_email UNIQUE (organization_id, email)
);

CREATE INDEX idx_guests_email ON guests(organization_id, email);
CREATE INDEX idx_guests_google ON guests(google_id) WHERE google_id IS NOT NULL;
```

---

### 1.9 Subdomain & Multi-Tenant Routing

Platform menggunakan **subdomain-based multi-tenancy** dengan single codebase.

#### 1.9.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUBDOMAIN ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SINGLE CODEBASE - DYNAMIC TENANT DETECTION                                │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│       grandindo.app.com  ──┐                                               │
│       aston.app.com      ──┼──►  [ Single React App ]  ──►  [ Single API ]│
│       hyatt.app.com      ──┘           │                                   │
│                                        │                                   │
│                                        ▼                                   │
│                              ┌─────────────────┐                           │
│                              │ Detect subdomain│                           │
│                              │ Load org config │                           │
│                              │ Apply branding  │                           │
│                              └─────────────────┘                           │
│                                                                             │
│  Benefits:                                                                  │
│  • Single deployment = easier maintenance                                  │
│  • Single codebase = consistent features                                   │
│  • Dynamic branding = white-label ready                                    │
│  • Cost efficient = no per-tenant infrastructure                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.9.2 URL Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    URL STRUCTURE                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAFF APPS (Internal)                                                     │
│  ───────────────────────────────────────────────────────────────────────── │
│  https://{org_code}.app.com/                    → Dashboard                │
│  https://{org_code}.app.com/pms                 → PMS module               │
│  https://{org_code}.app.com/pos                 → POS module               │
│  https://{org_code}.app.com/accounting          → Accounting               │
│  https://{org_code}.app.com/hrm                 → HRM                      │
│  https://{org_code}.app.com/inventory           → Inventory                │
│                                                                             │
│  PUBLIC APPS (Guest-facing)                                                │
│  ───────────────────────────────────────────────────────────────────────── │
│  https://{org_code}.app.com/book                → Booking engine (IBE)     │
│  https://{org_code}.app.com/menu                → Online menu (pos.online) │
│  https://{org_code}.app.com/guest               → Guest app                │
│                                                                             │
│  PLATFORM (SaaS Admin)                                                     │
│  ───────────────────────────────────────────────────────────────────────── │
│  https://platform.app.com/                      → Platform admin           │
│                                                                             │
│  Examples:                                                                  │
│  https://grandindo.app.com/pms/reservations     → Grand Indo's PMS         │
│  https://aston.app.com/pos/orders               → Aston's POS              │
│  https://grandindo.app.com/book                 → Grand Indo booking       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.9.3 Frontend Tenant Detection

```typescript
// src/hooks/useTenant.ts
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface OrgConfig {
  org_id: number;
  org_code: string;
  name: string;
  logo_url: string;
  favicon_url: string;
  primary_color: string;
  secondary_color: string;
  login_methods: ('google' | 'password')[];
  features: string[];
  timezone: string;
  locale: string;
}

export function useTenant() {
  const [orgCode, setOrgCode] = useState<string | null>(null);

  useEffect(() => {
    const hostname = window.location.hostname;

    if (hostname.includes('.app.com')) {
      // Production: grandindo.app.com → "grandindo"
      const subdomain = hostname.split('.')[0];
      setOrgCode(subdomain);
    } else if (hostname === 'localhost') {
      // Development: use query param
      const params = new URLSearchParams(window.location.search);
      setOrgCode(params.get('org') || 'demo');
    }
  }, []);

  const { data: config, isLoading, error } = useQuery({
    queryKey: ['org-config', orgCode],
    queryFn: () => fetchOrgConfig(orgCode!),
    enabled: !!orgCode,
    staleTime: 5 * 60 * 1000, // Cache 5 minutes
  });

  return { orgCode, config, isLoading, error };
}

async function fetchOrgConfig(orgCode: string): Promise<OrgConfig> {
  const response = await fetch(`/api/v1/public/org-config?code=${orgCode}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Organization not found');
    }
    throw new Error('Failed to load organization');
  }
  return response.json();
}
```

#### 1.9.4 Dynamic Branding

```typescript
// src/providers/TenantProvider.tsx
import { createContext, useContext, useEffect, ReactNode } from 'react';
import { useTenant, OrgConfig } from '../hooks/useTenant';

const TenantContext = createContext<OrgConfig | null>(null);

export function TenantProvider({ children }: { children: ReactNode }) {
  const { config, isLoading, error } = useTenant();

  useEffect(() => {
    if (config) {
      // Apply CSS variables
      const root = document.documentElement;
      root.style.setProperty('--color-primary', config.primary_color);
      root.style.setProperty('--color-secondary', config.secondary_color);

      // Set favicon
      const favicon = document.querySelector("link[rel='icon']") as HTMLLinkElement;
      if (favicon && config.favicon_url) {
        favicon.href = config.favicon_url;
      }

      // Set page title
      document.title = config.name;
    }
  }, [config]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (error) {
    return <OrgNotFoundScreen message={error.message} />;
  }

  return (
    <TenantContext.Provider value={config}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenantConfig() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenantConfig must be used within TenantProvider');
  }
  return context;
}
```

#### 1.9.5 Traefik Configuration

```yaml
# docker-compose.yml - Traefik with wildcard subdomain
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@domain.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  frontend:
    image: app-frontend:latest
    labels:
      # Catch ALL subdomains *.app.com
      - "traefik.http.routers.frontend.rule=HostRegexp(`{subdomain:[a-z0-9-]+}.app.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls=true"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      # Wildcard certificate
      - "traefik.http.routers.frontend.tls.domains[0].main=app.com"
      - "traefik.http.routers.frontend.tls.domains[0].sans=*.app.com"

  backend:
    image: app-backend:latest
    labels:
      - "traefik.http.routers.api.rule=HostRegexp(`{subdomain:[a-z0-9-]+}.app.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls=true"

volumes:
  letsencrypt:
```

#### 1.9.6 Backend Tenant Middleware

```python
# middleware/tenant.py
from fastapi import Request, HTTPException
from typing import Optional

async def get_tenant_from_request(request: Request) -> dict:
    """Extract tenant/organization from subdomain."""

    host = request.headers.get("host", "")

    # Extract subdomain: grandindo.app.com → grandindo
    if ".app.com" in host:
        org_code = host.split(".")[0]
    else:
        # Development: check header or query param
        org_code = request.headers.get("X-Org-Code") or \
                   request.query_params.get("org_code")

    if not org_code:
        raise HTTPException(status_code=400, detail="Organization not specified")

    # Lookup organization
    org = await organization_repo.get_by_code(org_code)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.status != "active":
        raise HTTPException(status_code=403, detail="Organization is not active")

    return {
        "org_id": org.id,
        "org_code": org.code,
        "tenant_id": org.tenant_id,
        "timezone": org.timezone,
        "locale": org.locale,
    }

# Dependency for protected routes
async def require_tenant(request: Request):
    tenant = await get_tenant_from_request(request)
    request.state.tenant = tenant
    return tenant
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
| `admin` | Tenant & subscription management | `platform.tenants.*`, `platform.subscriptions.*`, `platform.apps.read`, `core.users.read` |
| `finance` | Billing & payment only | `platform.invoices.*`, `platform.payments.*`, `platform.tenants.read`, `platform.subscriptions.read` |
| `support` | Read-only + limited actions | `*.*.read`, `platform.tenants.support` |
| `viewer` | Read-only access | `*.*.read` |

### 2.3 Community Roles (Per Organization)

| Role | Description | Typical Permissions |
|------|-------------|---------------------|
| `owner` | Organization owner | `*` (all permissions) |
| `admin` | Full admin access | `core.users.*`, `core.roles.*`, `core.settings.*`, `pms.*`, `pos.*`, `accounting.*` |
| `manager` | Operational management | `pms.*`, `pos.*`, `core.reports.*`, `core.users.read` |
| `operator` | Day-to-day operations | `pms.reservations.*`, `pos.orders.*`, `core.reports.read` |
| `viewer` | Read-only | `*.*.read` |

### 2.4 Permission Structure

```
Permission Format: {app}.{module}.{action}

Apps (Level 1):
- platform     # Platform-level (tenant management)
- core         # Core services (users, roles, settings)
- pms          # Property Management System
- pos          # Point of Sale
- accounting   # Accounting & Finance
- hrm          # Human Resource Management
- inventory    # Inventory Management

Modules (Level 2):
- users, roles, settings, reports       # Core modules
- reservations, rooms, guests, folios   # PMS modules
- orders, payments, tables              # POS modules
- journals, invoices, accounts          # Accounting modules

Actions (Level 3):
- create
- read
- update
- delete
- manage (= create + read + update + delete)
- approve
- export
- void

Examples:
- core.users.create
- core.users.read
- core.users.manage (= all CRUD)
- core.roles.manage
- pms.reservations.create
- pms.rooms.manage
- pms.folios.void
- pos.orders.create
- accounting.journals.approve
- accounting.reports.export
- platform.tenants.manage
```

### 2.5 Permission Check Flow

```python
# Middleware/Decorator approach
@require_permission("core.users.create")
async def create_user(request: Request, dto: CreateUserDTO):
    # Only reaches here if permission check passes
    pass

# Manual check in use case
class CreateUserUseCase:
    async def execute(self, actor: Actor, dto: CreateUserDTO):
        if not actor.has_permission("core.users.create"):
            raise PermissionDeniedError("Cannot create users")

        # Additional checks
        if dto.role == "admin" and not actor.has_permission("core.users.assign_admin"):
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
  "action": "core.users.update",
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

## Part 8: Frontend Security

### 8.1 Content Security Policy (CSP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTENT SECURITY POLICY                              │
└─────────────────────────────────────────────────────────────────────────┘

HTTP Header:
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.domain.com;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data: https: blob:;
  connect-src 'self' https://api.domain.com wss://ws.domain.com;
  frame-ancestors 'none';
  form-action 'self';
  base-uri 'self';
  upgrade-insecure-requests;
```

#### 8.1.1 CSP Implementation

```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Next.js requires
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https: blob:",
      "font-src 'self' data:",
      "connect-src 'self' https://api.* wss://*",
      "frame-ancestors 'none'",
      "form-action 'self'",
    ].join('; ')
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(self), payment=()'
  }
];
```

### 8.2 XSS Prevention

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    XSS PREVENTION LAYERS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Layer 1: Input Validation                                              │
│  ├── Sanitize on input (forms, URL params)                             │
│  ├── Whitelist allowed characters                                       │
│  └── Reject/escape dangerous patterns                                   │
│                                                                         │
│  Layer 2: Output Encoding                                               │
│  ├── React auto-escapes by default                                     │
│  ├── NEVER use dangerouslySetInnerHTML                                 │
│  └── Use DOMPurify for rich text                                       │
│                                                                         │
│  Layer 3: CSP                                                           │
│  ├── Block inline scripts                                              │
│  └── Whitelist script sources                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 8.2.1 Sanitization Utilities

```typescript
// lib/security/sanitize.ts
import DOMPurify from 'isomorphic-dompurify';

// HTML sanitization untuk rich text
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOW_DATA_ATTR: false,
  });
}

// Input sanitization - remove dangerous characters
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim();
}

// URL sanitization
export function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
      return '#';
    }
    return url;
  } catch {
    return '#';
  }
}

// SQL-like pattern detection (untuk search inputs)
export function detectSqlInjection(input: string): boolean {
  const patterns = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)/i,
    /(--)|(\/\*)|(\*\/)/,
    /(;|\||&)/,
  ];
  return patterns.some(p => p.test(input));
}
```

### 8.3 CSRF Protection

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CSRF PROTECTION                                      │
└─────────────────────────────────────────────────────────────────────────┘

Strategy: Double Submit Cookie + SameSite

1. Backend sets CSRF token in cookie (HttpOnly=false, SameSite=Strict)
2. Frontend reads cookie, sends in header
3. Backend validates header matches cookie

Implementation:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────►│   Cookie    │────►│   Server    │
│             │     │ csrf_token  │     │             │
│ Header:     │     │             │     │ Compare     │
│ X-CSRF-Token│     │             │     │ cookie ==   │
│             │     │             │     │ header      │
└─────────────┘     └─────────────┘     └─────────────┘
```

#### 8.3.1 CSRF Implementation

```typescript
// Frontend: API client
import Cookies from 'js-cookie';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Include cookies
});

apiClient.interceptors.request.use((config) => {
  const csrfToken = Cookies.get('csrf_token');
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});
```

```python
# Backend: FastAPI middleware
from fastapi import Request, HTTPException
from fastapi.responses import Response

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

async def csrf_middleware(request: Request, call_next):
    if request.method not in SAFE_METHODS:
        cookie_token = request.cookies.get(CSRF_COOKIE)
        header_token = request.headers.get(CSRF_HEADER)

        if not cookie_token or cookie_token != header_token:
            raise HTTPException(403, "CSRF validation failed")

    response = await call_next(request)

    # Set/refresh CSRF cookie on GET requests
    if request.method == "GET":
        token = generate_csrf_token()
        response.set_cookie(
            CSRF_COOKIE,
            token,
            httponly=False,  # JS needs to read
            samesite="strict",
            secure=True,
            max_age=3600
        )

    return response
```

### 8.4 Secure Storage

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLIENT-SIDE STORAGE RULES                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ ALLOWED in localStorage:                                            │
│  ├── UI preferences (theme, language)                                  │
│  ├── Non-sensitive cache (product list)                                │
│  └── Feature flags                                                      │
│                                                                         │
│  ❌ NEVER store in localStorage:                                        │
│  ├── Access tokens (use httpOnly cookie)                               │
│  ├── Refresh tokens                                                     │
│  ├── PII (name, email, phone)                                          │
│  ├── Payment information                                                │
│  └── Session identifiers                                                │
│                                                                         │
│  🔐 Token Storage Strategy:                                             │
│  ├── Access token: Memory only (React state/context)                   │
│  ├── Refresh token: httpOnly secure cookie                             │
│  └── Auto-refresh via silent /auth/refresh endpoint                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 9: Dependency Security

### 9.1 Dependency Scanning

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY SECURITY PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │ Commit  │───►│ CI Scan │───►│ Report  │───►│ Block/  │             │
│  │         │    │         │    │         │    │ Allow   │             │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘             │
│                      │                             │                    │
│                      ▼                             ▼                    │
│               ┌─────────────┐              ┌─────────────┐             │
│               │ npm audit   │              │ Critical/   │             │
│               │ pip-audit   │              │ High: Block │             │
│               │ trivy       │              │ Med: Warn   │             │
│               │ snyk        │              │ Low: Log    │             │
│               └─────────────┘              └─────────────┘             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 CI/CD Security Pipeline

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6 AM

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Python dependencies
      - name: Python Audit
        run: |
          pip install pip-audit safety
          pip-audit --strict --desc on
          safety check --full-report

      # Node dependencies
      - name: NPM Audit
        working-directory: ./frontend
        run: |
          npm audit --audit-level=high
          npx better-npm-audit audit

      # Container scan
      - name: Trivy Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      # SAST
      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          extra_args: --only-verified
```

### 9.3 Dependency Update Policy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY UPDATE POLICY                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Severity    │ Response Time   │ Action                                 │
│  ───────────────────────────────────────────────────────────────────── │
│  Critical    │ 24 hours        │ Immediate patch, hotfix deploy        │
│  High        │ 7 days          │ Next sprint, expedited review         │
│  Medium      │ 30 days         │ Regular sprint planning               │
│  Low         │ 90 days         │ Quarterly maintenance                 │
│                                                                         │
│  Automated Tools:                                                       │
│  ├── Dependabot (GitHub) - auto PRs                                    │
│  ├── Renovate - grouped updates                                        │
│  └── Snyk - continuous monitoring                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.4 Approved Dependencies Registry

```yaml
# .github/dependency-policy.yml
allowed:
  licenses:
    - MIT
    - Apache-2.0
    - BSD-2-Clause
    - BSD-3-Clause
    - ISC

  # Pre-approved packages (critical dependencies)
  packages:
    python:
      - fastapi
      - sqlalchemy
      - pydantic
      - celery
      - redis

    node:
      - react
      - next
      - @tanstack/react-query
      - zustand
      - zod

banned:
  licenses:
    - GPL-3.0  # Copyleft concern
    - AGPL-3.0

  packages:
    - event-stream  # Known compromised
    - flatmap-stream
    - colors@>1.4.0  # Sabotaged versions

review_required:
  - packages with < 1000 weekly downloads
  - packages with no updates in 2+ years
  - packages with known CVEs
```

---

## Part 10: Penetration Testing

### 10.1 Penetration Testing Schedule

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PENETRATION TESTING CALENDAR                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Type              │ Frequency    │ Scope                               │
│  ─────────────────────────────────────────────────────────────────────  │
│  Automated Scan    │ Weekly       │ OWASP ZAP, Nuclei                   │
│  Internal Pentest  │ Quarterly    │ Full application                    │
│  External Pentest  │ Annually     │ Full scope + infrastructure         │
│  Bug Bounty        │ Continuous   │ Production environment              │
│                                                                         │
│  Pre-Release Testing:                                                   │
│  ├── Major release: Full pentest before launch                         │
│  ├── Minor release: Automated scan + spot check                        │
│  └── Hotfix: Targeted test on changed components                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Testing Scope

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PENETRATION TEST SCOPE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  IN SCOPE:                                                              │
│  ├── Web Applications                                                   │
│  │   ├── Platform Admin (platform.domain.com)                          │
│  │   ├── Community Apps (*.tenant.domain.com)                          │
│  │   └── Public Website (www.domain.com)                               │
│  │                                                                      │
│  ├── APIs                                                               │
│  │   ├── REST API (api.domain.com)                                     │
│  │   ├── WebSocket (ws.domain.com)                                     │
│  │   └── Webhooks (hooks.domain.com)                                   │
│  │                                                                      │
│  ├── Authentication                                                     │
│  │   ├── Login flows                                                   │
│  │   ├── Password reset                                                │
│  │   ├── MFA bypass attempts                                           │
│  │   └── Session management                                            │
│  │                                                                      │
│  └── Authorization                                                      │
│      ├── Tenant isolation                                              │
│      ├── Role escalation                                               │
│      └── IDOR vulnerabilities                                          │
│                                                                         │
│  OUT OF SCOPE:                                                          │
│  ├── Physical security                                                  │
│  ├── Social engineering on employees                                    │
│  ├── DDoS attacks                                                       │
│  └── Third-party integrations (unless agreed)                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Automated Security Testing

```yaml
# scripts/security-test.sh
#!/bin/bash

# OWASP ZAP Baseline Scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.domain.com \
  -r zap-report.html \
  -c zap-rules.conf

# Nuclei Vulnerability Scan
nuclei -u https://staging.domain.com \
  -t cves/ \
  -t vulnerabilities/ \
  -t exposed-panels/ \
  -severity critical,high \
  -o nuclei-report.txt

# SQLMap (authorized testing only)
sqlmap -u "https://staging.domain.com/api/v1/search?q=test" \
  --batch \
  --level=3 \
  --risk=2 \
  --output-dir=sqlmap-results

# SSL/TLS Check
testssl --severity HIGH \
  --htmlfile ssl-report.html \
  staging.domain.com
```

### 10.4 Vulnerability Disclosure Policy

```markdown
## Responsible Disclosure Policy

### Reporting
- Email: security@domain.com
- PGP Key: [link to public key]
- Response time: 48 hours acknowledgment

### Rules of Engagement
1. Do not access or modify other users' data
2. Do not perform denial of service attacks
3. Do not use automated scanners on production without approval
4. Stop testing if you discover sensitive data

### Rewards (Bug Bounty)
| Severity | Reward |
|----------|--------|
| Critical | $1,000 - $5,000 |
| High | $500 - $1,000 |
| Medium | $100 - $500 |
| Low | Recognition |

### Safe Harbor
We will not pursue legal action against researchers who:
- Follow this policy
- Report findings promptly
- Do not exploit vulnerabilities beyond proof-of-concept
```

---

## Part 11: Web Application Firewall (WAF)

### 11.1 WAF Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WAF ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Internet                                                               │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────┐                                                        │
│  │ Cloudflare  │  Layer 1: DDoS Protection                             │
│  │ / AWS WAF   │  - Rate limiting                                       │
│  │             │  - Bot detection                                       │
│  │             │  - Geo blocking                                        │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │ Load        │  Layer 2: SSL Termination                             │
│  │ Balancer    │  - Certificate management                             │
│  │             │  - Health checks                                       │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │ Application │  Layer 3: Application Logic                           │
│  │ Servers     │  - Input validation                                    │
│  │             │  - Business rules                                      │
│  └─────────────┘                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 WAF Rules

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WAF RULE CATEGORIES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. OWASP Core Rule Set (CRS)                                          │
│     ├── SQL Injection (SQLi)                                           │
│     ├── Cross-Site Scripting (XSS)                                     │
│     ├── Local File Inclusion (LFI)                                     │
│     ├── Remote Code Execution (RCE)                                    │
│     └── Protocol violations                                            │
│                                                                         │
│  2. Rate Limiting Rules                                                 │
│     ├── Login: 5 req/min per IP                                        │
│     ├── API: 100 req/min per user                                      │
│     ├── Search: 30 req/min per user                                    │
│     └── File upload: 10 req/min per user                               │
│                                                                         │
│  3. Bot Protection                                                      │
│     ├── Known bad bots: Block                                          │
│     ├── Headless browsers: Challenge                                   │
│     ├── Scrapers: Rate limit                                           │
│     └── Good bots (Google, Bing): Allow                                │
│                                                                         │
│  4. Geo Restrictions                                                    │
│     ├── Default: Allow all                                             │
│     ├── High-risk countries: Challenge                                 │
│     └── Sanctioned countries: Block (compliance)                       │
│                                                                         │
│  5. Custom Rules                                                        │
│     ├── Block user-agent: curl, wget (API only)                        │
│     ├── Require headers: X-Tenant-ID on /api/*                         │
│     └── Block empty referer on forms                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Cloudflare Configuration

```typescript
// Cloudflare WAF Rules (Terraform)
resource "cloudflare_ruleset" "waf_custom" {
  zone_id = var.zone_id
  name    = "Custom WAF Rules"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  // Block SQL injection patterns
  rules {
    action      = "block"
    expression  = "(http.request.uri.query contains \"UNION SELECT\") or (http.request.uri.query contains \"1=1\")"
    description = "Block SQLi patterns"
  }

  // Rate limit login
  rules {
    action = "block"
    action_parameters {
      response {
        status_code = 429
        content     = "{\"error\":\"Too many requests\"}"
        content_type = "application/json"
      }
    }
    expression  = "(http.request.uri.path eq \"/api/v1/auth/login\") and (rate(5m) > 5)"
    description = "Rate limit login attempts"
  }

  // Challenge suspicious requests
  rules {
    action      = "managed_challenge"
    expression  = "(cf.threat_score > 30) or (cf.bot_management.score < 30)"
    description = "Challenge suspicious traffic"
  }

  // Require tenant header on API
  rules {
    action      = "block"
    expression  = "(http.request.uri.path contains \"/api/v1/\") and (not http.request.headers[\"x-tenant-id\"])"
    description = "Require X-Tenant-ID header"
  }
}
```

### 11.4 AWS WAF Configuration

```yaml
# AWS WAF Rules (CloudFormation)
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: ProjectBesarWAF
      Scope: REGIONAL
      DefaultAction:
        Allow: {}
      Rules:
        # AWS Managed Rules
        - Name: AWSManagedRulesCommonRuleSet
          Priority: 1
          OverrideAction:
            None: {}
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesCommonRuleSet
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: CommonRuleSet

        - Name: AWSManagedRulesSQLiRuleSet
          Priority: 2
          OverrideAction:
            None: {}
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesSQLiRuleSet
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: SQLiRuleSet

        # Rate limiting
        - Name: RateLimitRule
          Priority: 3
          Action:
            Block: {}
          Statement:
            RateBasedStatement:
              Limit: 2000
              AggregateKeyType: IP
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: RateLimit

      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: ProjectBesarWebACL
```

---

## Part 12: Security Checklist Summary

### 12.1 Pre-Production Checklist

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRE-PRODUCTION SECURITY CHECKLIST                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  AUTHENTICATION                                                         │
│  [ ] JWT RS256 with key rotation                                       │
│  [ ] Password hashing (argon2/bcrypt)                                  │
│  [ ] MFA implementation                                                 │
│  [ ] Session timeout configured                                         │
│  [ ] Account lockout after failed attempts                             │
│                                                                         │
│  AUTHORIZATION                                                          │
│  [ ] RBAC fully implemented                                            │
│  [ ] Tenant isolation verified                                         │
│  [ ] Permission checks on all endpoints                                │
│  [ ] No horizontal privilege escalation                                │
│                                                                         │
│  DATA PROTECTION                                                        │
│  [ ] Encryption at rest (AES-256)                                      │
│  [ ] Encryption in transit (TLS 1.3)                                   │
│  [ ] PII fields encrypted                                              │
│  [ ] Backup encryption enabled                                         │
│                                                                         │
│  INPUT VALIDATION                                                       │
│  [ ] All inputs validated (Pydantic/Zod)                               │
│  [ ] SQL injection prevented                                           │
│  [ ] XSS prevented                                                      │
│  [ ] File upload validation                                            │
│                                                                         │
│  INFRASTRUCTURE                                                         │
│  [ ] WAF configured                                                    │
│  [ ] Rate limiting enabled                                             │
│  [ ] Security headers set                                              │
│  [ ] CSP configured                                                    │
│  [ ] Secrets in vault (not env files)                                  │
│                                                                         │
│  MONITORING                                                             │
│  [ ] Security logging enabled                                          │
│  [ ] Alerting configured                                               │
│  [ ] Audit trail complete                                              │
│  [ ] Incident response plan ready                                      │
│                                                                         │
│  TESTING                                                                │
│  [ ] Dependency scan passed                                            │
│  [ ] SAST scan passed                                                  │
│  [ ] Penetration test completed                                        │
│  [ ] Vulnerability remediation done                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Security Metrics

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECURITY KPIs                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Metric                    │ Target          │ Alert Threshold          │
│  ─────────────────────────────────────────────────────────────────────  │
│  Failed login rate         │ < 5%            │ > 10%                    │
│  Critical vuln count       │ 0               │ > 0                      │
│  High vuln count           │ < 5             │ > 10                     │
│  Mean time to patch (crit) │ < 24h           │ > 48h                    │
│  WAF block rate            │ < 1%            │ > 5%                     │
│  Security incidents/month  │ < 2             │ > 5                      │
│  Audit log coverage        │ 100%            │ < 95%                    │
│  Dependency freshness      │ < 30 days       │ > 90 days                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2025-12-13 (Frontend Security, Dependency Scanning, Pentest, WAF Added)*
