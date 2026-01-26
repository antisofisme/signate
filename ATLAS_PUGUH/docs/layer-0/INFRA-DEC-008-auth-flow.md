# INFRA-DEC-008: Authentication Flow

**VERSION**: Layer 0 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines authentication flows for ATLAS_PUGUH SaaS platform:
- Email/Password registration and login
- OAuth authentication (Google, GitHub)
- Email verification
- Password reset
- Token management (JWT)
- Account linking

---

## Authentication Providers

### Supported Providers

| Provider | Type | Features |
|----------|------|----------|
| **Local** | Email/Password | Registration, login, password reset |
| **Google** | OAuth 2.0 | SSO, auto email verification |
| **GitHub** | OAuth 2.0 | SSO, auto email verification |

### Provider Configuration

```typescript
AuthConfig {
  // Local auth
  local: {
    enabled: true
    password_min_length: 8
    require_uppercase: true
    require_number: true
    require_special: false
  }

  // Google OAuth
  google: {
    enabled: true
    client_id: string      // From Google Cloud Console
    client_secret: string  // From Google Cloud Console
    scopes: ["email", "profile"]
  }

  // GitHub OAuth
  github: {
    enabled: true
    client_id: string      // From GitHub Developer Settings
    client_secret: string  // From GitHub Developer Settings
    scopes: ["user:email", "read:user"]
  }
}
```

---

## 1. Registration Flow (Local)

### Sequence Diagram

```
User                Frontend              Backend              Email Service
 │                    │                     │                      │
 │ Fill form          │                     │                      │
 │─────────────────► │                     │                      │
 │                    │ POST /auth/register │                      │
 │                    │────────────────────►│                      │
 │                    │                     │ Create user          │
 │                    │                     │ (pending_verification)
 │                    │                     │                      │
 │                    │                     │ Send verification    │
 │                    │                     │─────────────────────►│
 │                    │                     │                      │
 │                    │   201 Created       │                      │
 │                    │◄────────────────────│                      │
 │ Show "check email" │                     │                      │
 │◄─────────────────  │                     │                      │
 │                    │                     │                      │
 │ Click email link   │                     │                      │
 │─────────────────────────────────────────►│                      │
 │                    │                     │ Verify token         │
 │                    │                     │ Update status=active │
 │                    │                     │ Create tenant/project│
 │                    │                     │ Issue JWT            │
 │◄─────────────────────────────────────────│                      │
 │ Redirect to        │                     │                      │
 │ dashboard          │                     │                      │
```

### API Contract

**POST /auth/register**

```typescript
// Request
{
  email: string           // Valid email
  password: string        // Min 8 chars, 1 uppercase, 1 number
  display_name: string    // 2-100 chars
}

// Success Response (201)
{
  success: true
  data: {
    user_id: string
    email: string
    status: "pending_verification"
    message: "Please check your email to verify your account"
  }
}

// Error Response (400)
{
  success: false
  error: {
    code: "VALIDATION_ERROR"
    message: "Password must be at least 8 characters"
    field: "password"
  }
}

// Error Response (409)
{
  success: false
  error: {
    code: "EMAIL_EXISTS"
    message: "An account with this email already exists"
  }
}
```

### Email Verification Token

```typescript
VerificationToken {
  token: string           // Random 64-char hex
  user_id: UUID
  type: "email_verification"
  expires_at: timestamp   // 24 hours from creation
  created_at: timestamp
}
```

**GET /auth/verify-email?token={token}**

```typescript
// Success Response (200)
{
  success: true
  data: {
    user_id: string
    email: string
    status: "active"
    access_token: string   // JWT
    refresh_token: string
    tenant: {
      tenant_id: string
      name: string
      slug: string
    }
    project: {
      project_id: string
      name: string
      slug: string
    }
    redirect_url: "/app/{tenant-slug}/{project-slug}/dashboard"
  }
}

// Error Response (400)
{
  success: false
  error: {
    code: "INVALID_TOKEN"
    message: "Verification link is invalid or expired"
  }
}
```

### Validation Rules

```
GR-REG-1: Email Validation
  - Valid email format (RFC 5322)
  - Email normalized to lowercase
  - Disposable email domains blocked (optional)

GR-REG-2: Password Validation
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 number
  - Not in common password list

GR-REG-3: Display Name Validation
  - 2-100 characters
  - No HTML/script injection
  - Profanity filter (optional)

GR-REG-4: Rate Limiting
  - Max 5 registration attempts per IP per hour
  - Max 3 verification emails per email per hour
```

---

## 2. Login Flow (Local)

### Sequence Diagram

```
User                Frontend              Backend
 │                    │                     │
 │ Enter credentials  │                     │
 │─────────────────► │                     │
 │                    │ POST /auth/login    │
 │                    │────────────────────►│
 │                    │                     │ Validate password
 │                    │                     │ Check status
 │                    │                     │ Load tenants
 │                    │                     │ Issue JWT
 │                    │   200 OK            │
 │                    │◄────────────────────│
 │                    │                     │
 │ (If N tenants)     │                     │
 │ Show tenant selector                     │
 │                    │                     │
 │ Select tenant      │                     │
 │─────────────────► │                     │
 │                    │ POST /auth/select-context
 │                    │────────────────────►│
 │                    │                     │ Update JWT context
 │                    │   200 OK            │
 │                    │◄────────────────────│
 │ Redirect to        │                     │
 │ dashboard          │                     │
```

### API Contract

**POST /auth/login**

```typescript
// Request
{
  email: string
  password: string
  remember_me?: boolean   // Extend refresh token to 30 days
}

// Success Response (200) - Single tenant
{
  success: true
  data: {
    user: {
      user_id: string
      email: string
      display_name: string
    }
    access_token: string
    refresh_token: string
    active_tenant: {
      tenant_id: string
      name: string
      slug: string
      role: string
    }
    active_project: {
      project_id: string
      name: string
      slug: string
    }
    redirect_url: "/app/{tenant-slug}/{project-slug}/dashboard"
  }
}

// Success Response (200) - Multiple tenants
{
  success: true
  data: {
    user: {
      user_id: string
      email: string
      display_name: string
    }
    access_token: string      // Limited token, no active context
    refresh_token: string
    tenants: [
      {
        tenant_id: string
        name: string
        slug: string
        role: string
        projects: [...]
      }
    ]
    requires_context_selection: true
    redirect_url: "/app/select-tenant"
  }
}

// Error Response (401)
{
  success: false
  error: {
    code: "INVALID_CREDENTIALS"
    message: "Invalid email or password"
  }
}

// Error Response (403)
{
  success: false
  error: {
    code: "ACCOUNT_NOT_VERIFIED"
    message: "Please verify your email before logging in"
  }
}

// Error Response (403)
{
  success: false
  error: {
    code: "ACCOUNT_SUSPENDED"
    message: "Your account has been suspended"
  }
}
```

**POST /auth/select-context**

```typescript
// Request
{
  tenant_id: string
  project_id?: string   // Optional, defaults to default project
}

// Success Response (200)
{
  success: true
  data: {
    access_token: string    // New token with context
    active_tenant: {...}
    active_project: {...}
    redirect_url: "/app/{tenant-slug}/{project-slug}/dashboard"
  }
}
```

### Validation Rules

```
GR-LOGIN-1: Credential Validation
  - Email case-insensitive
  - Timing-safe password comparison (prevent timing attacks)
  - Same error message for wrong email or password

GR-LOGIN-2: Account Status
  - "pending_verification" → redirect to verify
  - "suspended" → deny with message
  - "active" → proceed

GR-LOGIN-3: Rate Limiting
  - Max 5 failed attempts per email per 15 minutes
  - Account locked after 10 failed attempts per hour
  - IP-based rate limiting: 20 attempts per IP per hour

GR-LOGIN-4: Last Login Update
  - Update last_login_at on successful login
  - Log login event to audit
```

---

## 3. OAuth Flow (Google/GitHub)

### Sequence Diagram

```
User                Frontend              Backend              OAuth Provider
 │                    │                     │                      │
 │ Click "Sign in     │                     │                      │
 │   with Google"     │                     │                      │
 │─────────────────► │                     │                      │
 │                    │ GET /auth/google    │                      │
 │                    │────────────────────►│                      │
 │                    │                     │ Generate state       │
 │                    │   302 Redirect      │                      │
 │                    │◄────────────────────│                      │
 │                    │                     │                      │
 │◄───────────────────┤ Redirect to Google  │                      │
 │                    │                     │                      │
 │ Login at Google    │                     │                      │
 │────────────────────────────────────────────────────────────────►│
 │                    │                     │                      │
 │ Consent & Redirect │                     │                      │
 │◄────────────────────────────────────────────────────────────────│
 │                    │                     │                      │
 │ Redirect to        │                     │                      │
 │ callback           │ GET /auth/google/   │                      │
 │───────────────────►│ callback?code=...   │                      │
 │                    │────────────────────►│                      │
 │                    │                     │ Exchange code        │
 │                    │                     │─────────────────────►│
 │                    │                     │ Get user info        │
 │                    │                     │◄─────────────────────│
 │                    │                     │                      │
 │                    │                     │ Find/create user     │
 │                    │                     │ Issue JWT            │
 │                    │   302 Redirect      │                      │
 │                    │◄────────────────────│                      │
 │ Redirect to        │                     │                      │
 │ dashboard          │                     │                      │
 │◄───────────────────│                     │                      │
```

### API Contracts

**GET /auth/google**

```typescript
// Redirects to Google OAuth consent screen
// Query params:
{
  redirect_uri?: string   // Post-auth redirect (default: /app)
}

// Redirect URL example:
// https://accounts.google.com/o/oauth2/v2/auth
//   ?client_id={GOOGLE_CLIENT_ID}
//   &redirect_uri={BACKEND_URL}/auth/google/callback
//   &response_type=code
//   &scope=email+profile
//   &state={encrypted_state}
```

**GET /auth/google/callback**

```typescript
// Query params from Google:
{
  code: string            // Authorization code
  state: string           // CSRF state
}

// On success: Redirect to frontend with token
// /app?token={access_token}&refresh={refresh_token}

// On error: Redirect to frontend with error
// /login?error=oauth_failed&message=...
```

### OAuth User Handling

```
Scenario 1: New User (OAuth email not in database)
  1. Create user (status = active, email already verified by OAuth)
  2. Set auth_provider = "google" or "github"
  3. Store oauth_provider_id
  4. Auto-create tenant + default project
  5. Issue JWT, redirect to dashboard

Scenario 2: Existing User (Same OAuth provider)
  1. Find user by (auth_provider, oauth_provider_id)
  2. Update last_login_at
  3. Issue JWT, redirect to dashboard

Scenario 3: Existing User (Email exists, local account)
  1. Find user by email
  2. Prompt to link accounts:
     - "An account with this email exists. Enter password to link."
  3. On password confirmation:
     - Add oauth_provider_id to user
     - Update auth_provider to "local+google" (or similar)
  4. Issue JWT, redirect to dashboard

Scenario 4: Existing User (Email exists, different OAuth)
  1. Find user by email
  2. If auth_provider is different OAuth:
     - Add new oauth_provider_id
     - Allow login with either OAuth
```

### Validation Rules

```
GR-OAUTH-1: State Validation
  - State parameter required (CSRF protection)
  - State encrypted and signed
  - State expires in 10 minutes

GR-OAUTH-2: Email Verification
  - Trust OAuth provider's email verification
  - Skip email verification step for OAuth users

GR-OAUTH-3: Account Linking
  - Require password to link OAuth to existing local account
  - Allow linking multiple OAuth providers to one account
  - Each OAuth provider ID can only be linked to one user

GR-OAUTH-4: Profile Sync
  - Optionally update display_name/avatar from OAuth on each login
  - Never overwrite if user has customized
```

---

## 4. Password Reset Flow

### Sequence Diagram

```
User                Frontend              Backend              Email Service
 │                    │                     │                      │
 │ Click "Forgot      │                     │                      │
 │   Password"        │                     │                      │
 │─────────────────► │                     │                      │
 │                    │ POST /auth/         │                      │
 │                    │ forgot-password     │                      │
 │                    │────────────────────►│                      │
 │                    │                     │ Generate reset token │
 │                    │                     │────────────────────►│ Send email
 │                    │   200 OK            │                      │
 │                    │◄────────────────────│                      │
 │ "Check your email" │                     │                      │
 │◄─────────────────  │                     │                      │
 │                    │                     │                      │
 │ Click reset link   │                     │                      │
 │─────────────────► │                     │                      │
 │                    │ GET /reset-password │                      │
 │                    │ ?token={token}      │                      │
 │ Enter new password │                     │                      │
 │─────────────────► │                     │                      │
 │                    │ POST /auth/         │                      │
 │                    │ reset-password      │                      │
 │                    │────────────────────►│                      │
 │                    │                     │ Validate token       │
 │                    │                     │ Update password      │
 │                    │                     │ Invalidate sessions  │
 │                    │   200 OK            │                      │
 │                    │◄────────────────────│                      │
 │ Redirect to login  │                     │                      │
 │◄─────────────────  │                     │                      │
```

### API Contracts

**POST /auth/forgot-password**

```typescript
// Request
{
  email: string
}

// Success Response (200) - Always same response (prevent email enumeration)
{
  success: true
  data: {
    message: "If an account exists, a password reset email has been sent"
  }
}
```

**POST /auth/reset-password**

```typescript
// Request
{
  token: string
  new_password: string
}

// Success Response (200)
{
  success: true
  data: {
    message: "Password reset successful. Please log in."
  }
}

// Error Response (400)
{
  success: false
  error: {
    code: "INVALID_TOKEN"
    message: "Reset link is invalid or expired"
  }
}
```

### Password Reset Token

```typescript
ResetToken {
  token: string           // Random 64-char hex
  user_id: UUID
  type: "password_reset"
  expires_at: timestamp   // 1 hour from creation
  used_at: timestamp      // Set when used (one-time)
  created_at: timestamp
}
```

### Validation Rules

```
GR-RESET-1: Token Expiration
  - Reset tokens expire in 1 hour
  - Token can only be used once

GR-RESET-2: Rate Limiting
  - Max 3 reset requests per email per hour
  - Max 10 reset requests per IP per hour

GR-RESET-3: Password Requirements
  - Same as registration requirements
  - Cannot reuse last 5 passwords (optional)

GR-RESET-4: Session Invalidation
  - Invalidate all existing sessions on password reset
  - Require re-login on all devices
```

---

## 5. Token Management

### Token Types

| Token | Purpose | Expiration | Storage |
|-------|---------|------------|---------|
| Access Token | API authentication | 15 minutes | Memory/localStorage |
| Refresh Token | Get new access token | 7 days (30 if remember_me) | httpOnly cookie |
| Verification Token | Email verification | 24 hours | Database |
| Reset Token | Password reset | 1 hour | Database |

### JWT Structure

```typescript
// Access Token
{
  // Header
  alg: "RS256"       // Or HS256 for simpler setup
  typ: "JWT"

  // Payload
  sub: string        // user_id
  email: string
  display_name: string

  tenants: [{
    tenant_id: string
    slug: string
    role: string
    projects: [{
      project_id: string
      slug: string
      is_default: boolean
    }]
  }]

  active_tenant_id: string | null
  active_project_id: string | null

  iat: number        // Issued at
  exp: number        // Expiration
}

// Refresh Token
{
  sub: string        // user_id
  jti: string        // Token ID (for revocation)
  iat: number
  exp: number
}
```

### Token Refresh Flow

**POST /auth/refresh**

```typescript
// Request (refresh token in httpOnly cookie)
// No body needed

// Success Response (200)
{
  success: true
  data: {
    access_token: string
    expires_in: 900    // 15 minutes
  }
}

// Error Response (401)
{
  success: false
  error: {
    code: "INVALID_REFRESH_TOKEN"
    message: "Please log in again"
  }
}
```

### Token Revocation

**POST /auth/logout**

```typescript
// Request
// No body needed

// Success Response (200)
{
  success: true
  data: {
    message: "Logged out successfully"
  }
}

// Actions:
// 1. Add refresh token jti to blacklist
// 2. Clear httpOnly cookie
// 3. Return 200
```

### Token Validation Rules

```
GR-TOKEN-1: Signature Validation
  - Verify JWT signature on every request
  - Reject expired tokens
  - Reject tokens with invalid structure

GR-TOKEN-2: Context Validation
  - If active_tenant_id set, verify user has membership
  - If active_project_id set, verify project belongs to tenant

GR-TOKEN-3: Refresh Token Security
  - Store refresh tokens in httpOnly cookie
  - Implement refresh token rotation
  - Blacklist used refresh tokens

GR-TOKEN-4: Token Blacklist
  - Maintain blacklist for revoked tokens
  - Clean up expired entries periodically
  - Use Redis for high-performance lookups
```

---

## 6. Account Linking

### Link OAuth to Existing Account

**POST /auth/link-oauth**

```typescript
// Request
{
  provider: "google" | "github"
}

// Response: Redirect URL
{
  success: true
  data: {
    redirect_url: "https://accounts.google.com/..."
  }
}
```

**GET /auth/link-oauth/{provider}/callback**

```typescript
// Requires authenticated user
// Links OAuth provider to current user

// Success: Redirect to /settings with success message
// Error: Redirect to /settings with error message
```

### Unlink OAuth Provider

**DELETE /auth/unlink-oauth/{provider}**

```typescript
// Request
// No body needed

// Success Response (200)
{
  success: true
  data: {
    message: "Provider unlinked successfully"
  }
}

// Error Response (400)
{
  success: false
  error: {
    code: "CANNOT_UNLINK"
    message: "Cannot unlink the only authentication method"
  }
}
```

### Validation Rules

```
GR-LINK-1: At Least One Auth Method
  - Cannot unlink OAuth if it's the only auth method
  - Must have password OR at least one OAuth

GR-LINK-2: Unique Provider ID
  - Each OAuth provider ID can only be linked to one user
  - Error if provider ID already linked to different user

GR-LINK-3: Account Confirmation
  - Linking to existing email requires password confirmation
  - Or email confirmation to prove ownership
```

---

## 7. Security Considerations

### Password Hashing

```python
# Use bcrypt with cost factor 12
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    ).decode('utf-8')

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hash.encode('utf-8')
    )
```

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/register | 5 | 1 hour / IP |
| POST /auth/login | 5 | 15 min / email |
| POST /auth/forgot-password | 3 | 1 hour / email |
| POST /auth/refresh | 30 | 1 min / user |
| GET /auth/verify-email | 10 | 1 hour / IP |

### CORS Configuration

```python
CORS_CONFIG = {
    "allow_origins": [
        "https://app.atlaspuguh.com",
        "http://localhost:5173",  # Dev only
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type"],
}
```

### Cookie Security

```python
COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,          # HTTPS only in production
    "samesite": "lax",
    "domain": ".atlaspuguh.com",
    "path": "/",
}
```

---

## 8. Environment Variables

```env
# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://api.atlaspuguh.com/auth/google/callback

# GitHub OAuth
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GITHUB_REDIRECT_URI=https://api.atlaspuguh.com/auth/github/callback

# Email (for verification/reset)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=xxx
EMAIL_FROM=noreply@atlaspuguh.com

# URLs
FRONTEND_URL=https://app.atlaspuguh.com
BACKEND_URL=https://api.atlaspuguh.com
```

---

## 9. Database Schema (Auth Tokens)

```sql
CREATE TABLE auth_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

  token_hash VARCHAR(255) NOT NULL,  -- SHA256 hash of token
  token_type VARCHAR(30) NOT NULL,   -- email_verification, password_reset, refresh

  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT check_token_type CHECK (
    token_type IN ('email_verification', 'password_reset', 'refresh')
  )
);

CREATE INDEX idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_type ON auth_tokens(token_type, expires_at);
CREATE INDEX idx_auth_tokens_hash ON auth_tokens(token_hash);

-- Token blacklist (for revoked JWTs)
CREATE TABLE token_blacklist (
  jti VARCHAR(100) PRIMARY KEY,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blacklist_expires ON token_blacklist(expires_at);
```

---

## 10. Checklist: Auth Flow DRAFT

- ✅ Registration flow defined (email/password)
- ✅ Login flow defined (single/multi tenant)
- ✅ OAuth flow defined (Google, GitHub)
- ✅ Email verification flow defined
- ✅ Password reset flow defined
- ✅ Token management defined (JWT)
- ✅ Account linking defined
- ✅ Security considerations documented
- ✅ Rate limiting defined
- ✅ API contracts defined
- ✅ Database schema defined
- ✅ Environment variables listed

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-007: Identity Model (for User entity)
- INFRA-LAY2-005: Identity API Contracts (for detailed specs)
