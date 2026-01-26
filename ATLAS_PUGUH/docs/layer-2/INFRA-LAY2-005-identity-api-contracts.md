# INFRA-LAY2-005: Identity & Auth API Contracts

**VERSION**: Layer 2 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines the API contracts for Identity and Authentication endpoints:
- User registration and login
- OAuth authentication (Google, GitHub)
- Token management (refresh, logout)
- Email verification and password reset
- User profile management
- Tenant context selection

---

## Base URL

```
Production: https://api.atlaspuguh.com/api/v1
Staging:    https://api.staging.atlaspuguh.com/api/v1
Local:      http://localhost:8000/api/v1
```

---

## Authentication

Most endpoints require JWT authentication via Bearer token:

```
Authorization: Bearer <access_token>
```

Public endpoints (no auth required):
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/verify-email`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `GET /auth/google`
- `GET /auth/google/callback`
- `GET /auth/github`
- `GET /auth/github/callback`
- `POST /auth/refresh`

---

## 1. Registration

### POST /auth/register

Register a new user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "display_name": "John Doe"
}
```

**Validation:**
- `email`: Required, valid email format, max 255 chars
- `password`: Required, min 8 chars, 1 uppercase, 1 number
- `display_name`: Required, 2-100 chars

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "John Doe",
    "status": "pending_verification",
    "message": "Please check your email to verify your account"
  }
}
```

**Error Responses:**

*400 Bad Request (Validation Error):*
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password must be at least 8 characters",
    "field": "password",
    "details": {
      "min_length": 8,
      "current_length": 5
    }
  }
}
```

*409 Conflict (Email Exists):*
```json
{
  "success": false,
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "An account with this email already exists"
  }
}
```

*429 Too Many Requests:*
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many registration attempts. Please try again later.",
    "retry_after": 3600
  }
}
```

---

## 2. Email Verification

### GET /auth/verify-email

Verify user's email address using token from email link.

**Query Parameters:**
- `token` (required): Verification token from email

**Request:**
```
GET /auth/verify-email?token=abc123def456...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "display_name": "John Doe",
      "status": "active"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
    "expires_in": 900,
    "tenant": {
      "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
      "name": "John's Workspace",
      "slug": "johns-workspace"
    },
    "project": {
      "project_id": "772f0622-g41d-63f6-c938-668877662222",
      "name": "Default",
      "slug": "default"
    },
    "redirect_url": "/app/johns-workspace/default/dashboard"
  }
}
```

**Error Response (400 Bad Request):*
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Verification link is invalid or expired"
  }
}
```

### POST /auth/resend-verification

Resend verification email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "If an account exists with this email, a verification email has been sent"
  }
}
```

---

## 3. Login

### POST /auth/login

Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "remember_me": false
}
```

**Success Response - Single Tenant (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "display_name": "John Doe",
      "avatar_url": null
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
    "expires_in": 900,
    "active_tenant": {
      "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
      "name": "John's Workspace",
      "slug": "johns-workspace",
      "role": "owner"
    },
    "active_project": {
      "project_id": "772f0622-g41d-63f6-c938-668877662222",
      "name": "Default",
      "slug": "default",
      "is_default": true
    },
    "redirect_url": "/app/johns-workspace/default/dashboard"
  }
}
```

**Success Response - Multiple Tenants (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "display_name": "John Doe",
      "avatar_url": null
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
    "expires_in": 900,
    "tenants": [
      {
        "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
        "name": "John's Workspace",
        "slug": "johns-workspace",
        "role": "owner",
        "projects": [
          {
            "project_id": "772f0622-g41d-63f6-c938-668877662222",
            "name": "Default",
            "slug": "default",
            "is_default": true
          }
        ]
      },
      {
        "tenant_id": "882g0622-h52e-74g7-d049-779988773333",
        "name": "Acme Corp",
        "slug": "acme-corp",
        "role": "member",
        "projects": [
          {
            "project_id": "993h1733-i63f-85h8-e150-880099884444",
            "name": "Production",
            "slug": "production",
            "is_default": true
          },
          {
            "project_id": "aa4i2844-j74g-96i9-f261-991100995555",
            "name": "Staging",
            "slug": "staging",
            "is_default": false
          }
        ]
      }
    ],
    "requires_context_selection": true,
    "redirect_url": "/app/select-tenant"
  }
}
```

**Error Responses:**

*401 Unauthorized:*
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

*403 Forbidden (Not Verified):*
```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_NOT_VERIFIED",
    "message": "Please verify your email before logging in",
    "can_resend": true
  }
}
```

*403 Forbidden (Suspended):*
```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_SUSPENDED",
    "message": "Your account has been suspended. Please contact support."
  }
}
```

*423 Locked (Too Many Attempts):*
```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_LOCKED",
    "message": "Account temporarily locked due to too many failed attempts",
    "unlock_at": "2024-01-26T12:00:00Z"
  }
}
```

---

## 4. Context Selection

### POST /auth/select-context

Select active tenant and project context.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
  "project_id": "772f0622-g41d-63f6-c938-668877662222"
}
```

**Notes:**
- `project_id` is optional; defaults to tenant's default project

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900,
    "active_tenant": {
      "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
      "name": "John's Workspace",
      "slug": "johns-workspace",
      "role": "owner"
    },
    "active_project": {
      "project_id": "772f0622-g41d-63f6-c938-668877662222",
      "name": "Default",
      "slug": "default"
    },
    "redirect_url": "/app/johns-workspace/default/dashboard"
  }
}
```

**Error Response (404 Not Found):*
```json
{
  "success": false,
  "error": {
    "code": "TENANT_NOT_FOUND",
    "message": "Tenant not found or you don't have access"
  }
}
```

---

## 5. OAuth Authentication

### GET /auth/google

Initiate Google OAuth flow.

**Query Parameters:**
- `redirect_uri` (optional): Post-auth redirect URL

**Request:**
```
GET /auth/google?redirect_uri=/app
```

**Response:**
```
302 Redirect to:
https://accounts.google.com/o/oauth2/v2/auth
  ?client_id={GOOGLE_CLIENT_ID}
  &redirect_uri=https://api.atlaspuguh.com/api/v1/auth/google/callback
  &response_type=code
  &scope=email+profile
  &state={encrypted_state}
```

### GET /auth/google/callback

Handle Google OAuth callback.

**Query Parameters:**
- `code` (required): Authorization code from Google
- `state` (required): CSRF state token

**Success Response:**
```
302 Redirect to:
{FRONTEND_URL}/auth/callback?token={access_token}&refresh={refresh_token}
```

**Error Response:**
```
302 Redirect to:
{FRONTEND_URL}/login?error=oauth_failed&message=...
```

### GET /auth/github

Initiate GitHub OAuth flow. Same pattern as Google.

### GET /auth/github/callback

Handle GitHub OAuth callback. Same pattern as Google.

---

## 6. Token Management

### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
Refresh token is sent via httpOnly cookie (automatic).

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900
  }
}
```

**Error Response (401 Unauthorized):*
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Please log in again"
  }
}
```

### POST /auth/logout

Logout and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:** No body needed.

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

**Side Effects:**
- Refresh token blacklisted
- httpOnly cookie cleared

---

## 7. Password Reset

### POST /auth/forgot-password

Request password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "If an account exists with this email, a password reset link has been sent"
  }
}
```

**Note:** Same response regardless of whether email exists (security).

### POST /auth/reset-password

Reset password using token.

**Request:**
```json
{
  "token": "abc123def456...",
  "new_password": "NewSecurePass456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Password reset successful. Please log in with your new password."
  }
}
```

**Error Response (400 Bad Request):*
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Reset link is invalid or expired"
  }
}
```

---

## 8. User Profile

### GET /auth/me

Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "display_name": "John Doe",
      "avatar_url": "https://...",
      "auth_provider": "local",
      "linked_providers": ["google"],
      "status": "active",
      "email_verified_at": "2024-01-26T10:00:00Z",
      "created_at": "2024-01-26T09:00:00Z",
      "last_login_at": "2024-01-26T12:00:00Z"
    },
    "tenants": [
      {
        "tenant_id": "...",
        "name": "...",
        "slug": "...",
        "role": "owner",
        "projects": [...]
      }
    ],
    "active_tenant_id": "...",
    "active_project_id": "..."
  }
}
```

### PATCH /auth/me

Update current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "display_name": "John Smith",
  "avatar_url": "https://..."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "display_name": "John Smith",
      "avatar_url": "https://..."
    }
  }
}
```

### POST /auth/change-password

Change password for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Password changed successfully"
  }
}
```

**Error Response (400 Bad Request):*
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Current password is incorrect"
  }
}
```

---

## 9. Account Linking

### POST /auth/link/{provider}

Initiate OAuth linking for existing account.

**Path Parameters:**
- `provider`: "google" | "github"

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
  }
}
```

### DELETE /auth/unlink/{provider}

Unlink OAuth provider from account.

**Path Parameters:**
- `provider`: "google" | "github"

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Provider unlinked successfully",
    "remaining_providers": ["local"]
  }
}
```

**Error Response (400 Bad Request):*
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_UNLINK",
    "message": "Cannot unlink the only authentication method"
  }
}
```

---

## 10. Tenant Management

### GET /tenants

List tenants for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tenants": [
      {
        "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
        "name": "John's Workspace",
        "slug": "johns-workspace",
        "plan": "free",
        "status": "active",
        "role": "owner",
        "member_count": 1,
        "project_count": 1,
        "created_at": "2024-01-26T09:00:00Z"
      }
    ]
  }
}
```

### POST /tenants

Create a new tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "name": "Acme Corp"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "tenant": {
      "tenant_id": "882g0622-h52e-74g7-d049-779988773333",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "plan": "free",
      "status": "active"
    },
    "membership": {
      "role": "owner",
      "status": "active"
    },
    "default_project": {
      "project_id": "993h1733-i63f-85h8-e150-880099884444",
      "name": "Default",
      "slug": "default"
    }
  }
}
```

### GET /tenants/{tenant_id}

Get tenant details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tenant": {
      "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
      "name": "John's Workspace",
      "slug": "johns-workspace",
      "plan": "free",
      "status": "active",
      "created_at": "2024-01-26T09:00:00Z"
    },
    "membership": {
      "role": "owner",
      "status": "active",
      "joined_at": "2024-01-26T09:00:00Z"
    },
    "members": [
      {
        "user_id": "...",
        "email": "user@example.com",
        "display_name": "John Doe",
        "role": "owner",
        "status": "active"
      }
    ],
    "projects": [
      {
        "project_id": "...",
        "name": "Default",
        "slug": "default",
        "is_default": true
      }
    ]
  }
}
```

### PATCH /tenants/{tenant_id}

Update tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Required Role:** owner or admin

**Request:**
```json
{
  "name": "John's Company"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tenant": {
      "tenant_id": "661f9511-f30c-52e5-b827-557766551111",
      "name": "John's Company",
      "slug": "johns-workspace"
    }
  }
}
```

---

## 11. Member Management

### POST /tenants/{tenant_id}/members/invite

Invite a user to tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Required Role:** owner or admin

**Request:**
```json
{
  "email": "newmember@example.com",
  "role": "member"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "invitation": {
      "email": "newmember@example.com",
      "role": "member",
      "status": "invited",
      "invited_at": "2024-01-26T12:00:00Z",
      "expires_at": "2024-02-02T12:00:00Z"
    },
    "message": "Invitation sent to newmember@example.com"
  }
}
```

### POST /tenants/{tenant_id}/members/accept

Accept invitation (via link in email).

**Query Parameters:**
- `token`: Invitation token

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tenant": {
      "tenant_id": "...",
      "name": "...",
      "slug": "..."
    },
    "membership": {
      "role": "member",
      "status": "active"
    },
    "redirect_url": "/app/{tenant-slug}/default/dashboard"
  }
}
```

### DELETE /tenants/{tenant_id}/members/{user_id}

Remove member from tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Required Role:** owner or admin

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Member removed successfully"
  }
}
```

### PATCH /tenants/{tenant_id}/members/{user_id}

Update member role.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Required Role:** owner or admin

**Request:**
```json
{
  "role": "admin"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "membership": {
      "user_id": "...",
      "role": "admin",
      "updated_at": "2024-01-26T12:00:00Z"
    }
  }
}
```

---

## 12. Project Management

### GET /tenants/{tenant_id}/projects

List projects in tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "project_id": "772f0622-g41d-63f6-c938-668877662222",
        "name": "Default",
        "slug": "default",
        "description": null,
        "environment": "production",
        "is_default": true,
        "created_at": "2024-01-26T09:00:00Z"
      }
    ]
  }
}
```

### POST /tenants/{tenant_id}/projects

Create a new project.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Required Role:** owner or admin

**Request:**
```json
{
  "name": "Staging",
  "description": "Staging environment",
  "environment": "staging"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "project": {
      "project_id": "aa4i2844-j74g-96i9-f261-991100995555",
      "name": "Staging",
      "slug": "staging",
      "description": "Staging environment",
      "environment": "staging",
      "is_default": false,
      "created_at": "2024-01-26T12:00:00Z"
    }
  }
}
```

**Error Response (403 Forbidden - Plan Limit):*
```json
{
  "success": false,
  "error": {
    "code": "PLAN_LIMIT_REACHED",
    "message": "Your Free plan allows 1 project. Upgrade to create more.",
    "current_count": 1,
    "plan_limit": 1,
    "upgrade_url": "/billing/upgrade"
  }
}
```

---

## Error Response Format

All errors follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "field": "field_name",       // Optional: for validation errors
    "details": { ... },           // Optional: additional context
    "retry_after": 3600           // Optional: for rate limiting
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `INVALID_TOKEN` | 400 | Token expired or invalid |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token invalid |
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | Not authorized |
| `ACCOUNT_NOT_VERIFIED` | 403 | Email not verified |
| `ACCOUNT_SUSPENDED` | 403 | Account suspended |
| `ACCOUNT_LOCKED` | 423 | Too many failed attempts |
| `NOT_FOUND` | 404 | Resource not found |
| `EMAIL_EXISTS` | 409 | Email already registered |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `PLAN_LIMIT_REACHED` | 403 | Plan limit exceeded |
| `CANNOT_UNLINK` | 400 | Cannot unlink only auth method |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/register` | 5 | 1 hour / IP |
| `POST /auth/login` | 5 | 15 min / email |
| `POST /auth/forgot-password` | 3 | 1 hour / email |
| `POST /auth/resend-verification` | 3 | 1 hour / email |
| `POST /auth/refresh` | 30 | 1 min / user |
| Other authenticated endpoints | 100 | 1 min / user |

---

## Checklist: Identity API Contracts DRAFT

- ✅ Registration endpoint defined
- ✅ Email verification endpoint defined
- ✅ Login endpoint defined (single/multi tenant)
- ✅ Context selection endpoint defined
- ✅ OAuth endpoints defined (Google, GitHub)
- ✅ Token management endpoints defined
- ✅ Password reset endpoints defined
- ✅ User profile endpoints defined
- ✅ Account linking endpoints defined
- ✅ Tenant management endpoints defined
- ✅ Member management endpoints defined
- ✅ Project management endpoints defined
- ✅ Error response format defined
- ✅ Rate limits defined

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-007: Identity Model
- INFRA-DEC-008: Auth Flow
