# API Contracts: Platform & Community

> **Date**: 2025-12-07
> **Status**: Draft
> **Base URL**:
> - Platform API: `https://platform.domain.com/api/v1`
> - Community API: `https://community.domain.com/api/v1`

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PLATFORM API (Owner System - Internal)                         │   │
│  │  - Tenant management (CRUD + actions)                           │   │
│  │  - App catalog management                                       │   │
│  │  - Subscription & billing                                       │   │
│  │  - Owner team management                                        │   │
│  │  - Dashboard & analytics                                        │   │
│  │  Auth: Owner JWT (owner_users)                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  COMMUNITY API (Shared - Public)                                │   │
│  │  - User registration & auth                                     │   │
│  │  - Organization management                                      │   │
│  │  - Role & permission                                            │   │
│  │  - Profile management                                           │   │
│  │  Auth: Community JWT (users)                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Standards Applied

| Standard | Pattern | Reference |
|----------|---------|-----------|
| Action Endpoints | `POST /resource/{id}/{action}` | Decision #87 |
| Pagination | `?page=1&page_size=20` | Dev Standards |
| Filtering | `?status=active&search=keyword` | Dev Standards |
| Sorting | `?sort_by=created_at&sort_order=desc` | Dev Standards |
| Response Format | `{ success, data, meta }` | Dev Standards 6.3 |
| Error Format | `{ success: false, error: { code, message, details } }` | Dev Standards 6.3 |
| Date Format | ISO 8601 (`2025-12-07T10:30:00Z`) | Dev Standards |

---

## Response Format

> **Reference**: DEVELOPMENT_STANDARDS.md Section 6.3

### Success Response (Single Entity)
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Success Response (List with Pagination)
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [ ... ],
    "request_id": "req-abc-123"
  }
}
```

> **Note**: Semua response di dokumen ini mengikuti format di atas. Untuk brevity, beberapa contoh mungkin tidak menampilkan field `success` secara eksplisit.

---

## Part 1: Platform API (Owner System)

### 1.1 Authentication

#### POST /auth/login
Login untuk owner team.

**Request:**
```json
{
  "email": "admin@owner.com",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "admin@owner.com",
      "name": "Admin User",
      "role": "super_admin"
    }
  }
}
```

#### POST /auth/refresh
Refresh access token.

#### POST /auth/logout
Invalidate tokens.

---

### 1.2 Tenants

#### GET /tenants
List all tenants dengan pagination & filtering.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| page | int | Page number (default: 1) |
| page_size | int | Items per page (default: 20, max: 100) |
| status | string | Filter by status (pending, trial, active, suspended, closed) |
| search | string | Search by name, code, email |
| sort_by | string | Sort field (created_at, name, status) |
| sort_order | string | asc / desc |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "code": "HTL-001",
      "name": "PT. Hotel Group Indonesia",
      "email": "admin@hotelgroup.com",
      "status": "active",
      "billing_cycle": "monthly",
      "trial_ends_at": null,
      "organization_count": 5,
      "active_subscriptions": 3,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

#### GET /tenants/{id}
Get tenant detail.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "code": "HTL-001",
    "name": "PT. Hotel Group Indonesia",
    "legal_name": "PT. Hotel Group Indonesia Tbk",
    "tax_id": "01.234.567.8-901.000",
    "email": "admin@hotelgroup.com",
    "phone": "+62-21-12345678",
    "website": "https://hotelgroup.com",
    "address": "Jl. Sudirman No. 1",
    "city": "Jakarta",
    "province": "DKI Jakarta",
    "country": "Indonesia",
    "postal_code": "10110",
    "status": "active",
    "trial_days": 14,
    "trial_started_at": "2025-01-01T00:00:00Z",
    "trial_ends_at": "2025-01-15T00:00:00Z",
    "billing_cycle": "monthly",
    "billing_email": "billing@hotelgroup.com",
    "payment_terms_days": 30,
    "is_invoice_consolidated": true,
    "base_fee": "500000.0000",
    "notes": "Premium customer",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-06-01T00:00:00Z",
    "organizations": [
      {
        "id": 1,
        "code": "HGI-HQ",
        "name": "Hotel Group HQ",
        "level": "holding",
        "is_active": true
      }
    ],
    "subscriptions": [
      {
        "id": 1,
        "app_code": "PMS",
        "tier": "enterprise",
        "status": "active",
        "monthly_fee": "2000000.0000"
      }
    ]
  }
}
```

#### POST /tenants
Create new tenant.

**Request:**
```json
{
  "code": "HTL-002",
  "name": "PT. Beach Resort",
  "email": "admin@beachresort.com",
  "phone": "+62-361-123456",
  "address": "Jl. Pantai Kuta",
  "city": "Bali",
  "province": "Bali",
  "billing_cycle": "yearly",
  "trial_days": 30,
  "notes": "Referred by HTL-001"
}
```

**Response (201):**
```json
{
  "data": {
    "id": 2,
    "code": "HTL-002",
    "name": "PT. Beach Resort",
    "status": "pending",
    "created_at": "2025-12-07T10:00:00Z"
  }
}
```

#### PUT /tenants/{id}
Update tenant info.

#### DELETE /tenants/{id}
Soft delete tenant (set is_deleted = true).

---

### 1.3 Tenant Actions

#### POST /tenants/{id}/activate
Activate tenant (pending/trial → active).

**Request:**
```json
{
  "reason": "Payment received"
}
```

**Response (200):**
```json
{
  "data": {
    "id": 1,
    "status": "active",
    "activated_at": "2025-12-07T10:00:00Z"
  },
  "message": "Tenant activated successfully"
}
```

#### POST /tenants/{id}/start-trial
Start trial period.

**Request:**
```json
{
  "trial_days": 14
}
```

#### POST /tenants/{id}/suspend
Suspend tenant.

**Request:**
```json
{
  "reason": "Payment overdue 60 days",
  "notify_users": true
}
```

#### POST /tenants/{id}/reactivate
Reactivate suspended tenant.

#### POST /tenants/{id}/close
Close tenant account (final).

**Request:**
```json
{
  "reason": "Customer request",
  "export_data": true
}
```

---

### 1.4 Tenant Organizations

#### GET /tenants/{tenant_id}/organizations
List organizations within tenant.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "code": "HGI-HQ",
      "name": "Hotel Group HQ",
      "level": "holding",
      "parent_id": null,
      "is_active": true,
      "user_count": 5,
      "children": [
        {
          "id": 2,
          "code": "HGI-BALI",
          "name": "Bali Regional",
          "level": "regional"
        }
      ]
    }
  ]
}
```

#### POST /tenants/{tenant_id}/organizations
Create organization within tenant.

**Request:**
```json
{
  "code": "HGI-LOMBOK",
  "name": "Lombok Regional",
  "level": "regional",
  "parent_id": 1,
  "address": "Jl. Senggigi",
  "city": "Lombok"
}
```

#### PUT /tenants/{tenant_id}/organizations/{org_id}
Update organization.

#### DELETE /tenants/{tenant_id}/organizations/{org_id}
Soft delete organization.

---

### 1.5 Apps (Product Catalog)

#### GET /apps
List all available apps.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "code": "PMS",
      "name": "Property Management System",
      "description": "Hotel operations management",
      "icon_url": "/icons/pms.svg",
      "is_active": true,
      "tiers": [
        {
          "id": 1,
          "tier": "basic",
          "monthly_price": "500000.0000",
          "yearly_price": "5000000.0000",
          "max_users": 5,
          "max_properties": 1
        },
        {
          "id": 2,
          "tier": "pro",
          "monthly_price": "1500000.0000",
          "yearly_price": "15000000.0000",
          "max_users": 20,
          "max_properties": 5
        },
        {
          "id": 3,
          "tier": "enterprise",
          "monthly_price": "5000000.0000",
          "yearly_price": "50000000.0000",
          "max_users": null,
          "max_properties": null
        }
      ]
    }
  ]
}
```

#### GET /apps/{id}
Get app detail with tier features.

**Response (200):**
```json
{
  "data": {
    "id": 1,
    "code": "PMS",
    "name": "Property Management System",
    "description": "Complete hotel operations management",
    "icon_url": "/icons/pms.svg",
    "is_active": true,
    "tiers": [
      {
        "id": 1,
        "tier": "basic",
        "monthly_price": "500000.0000",
        "yearly_price": "5000000.0000",
        "max_users": 5,
        "max_properties": 1,
        "features": [
          {
            "feature_code": "RESERVATION",
            "feature_name": "Reservation Management",
            "is_enabled": true,
            "limit_value": 100,
            "limit_unit": "bookings/month"
          },
          {
            "feature_code": "HOUSEKEEPING",
            "feature_name": "Housekeeping",
            "is_enabled": true,
            "limit_value": null,
            "limit_unit": null
          },
          {
            "feature_code": "REPORTS_ADVANCED",
            "feature_name": "Advanced Reports",
            "is_enabled": false,
            "limit_value": null,
            "limit_unit": null
          }
        ]
      }
    ]
  }
}
```

#### POST /apps
Create new app (admin only).

#### PUT /apps/{id}
Update app info.

#### POST /apps/{id}/tiers
Add tier to app.

#### PUT /apps/{id}/tiers/{tier_id}
Update tier.

#### POST /apps/{id}/tiers/{tier_id}/features
Add/update features for tier.

---

### 1.6 Subscriptions

#### GET /subscriptions
List all subscriptions.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| tenant_id | int | Filter by tenant |
| app_id | int | Filter by app |
| status | string | active, trial, expired, cancelled |

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "tenant": {
        "id": 1,
        "code": "HTL-001",
        "name": "PT. Hotel Group"
      },
      "organization": {
        "id": 2,
        "code": "HGI-BALI",
        "name": "Bali Regional"
      },
      "app": {
        "id": 1,
        "code": "PMS",
        "name": "Property Management System"
      },
      "tier": "enterprise",
      "status": "active",
      "started_at": "2025-01-01T00:00:00Z",
      "expires_at": "2026-01-01T00:00:00Z",
      "monthly_fee": "5000000.0000",
      "per_user_fee": "100000.0000",
      "current_users": 15,
      "auto_renew": true
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 45,
    "total_pages": 3
  }
}
```

#### GET /subscriptions/{id}
Get subscription detail.

#### POST /subscriptions
Create subscription for tenant organization.

**Request:**
```json
{
  "tenant_id": 1,
  "organization_id": 2,
  "app_id": 1,
  "tier_id": 3,
  "billing_cycle": "yearly",
  "auto_renew": true,
  "notes": "Upgrade from Pro tier"
}
```

#### PUT /subscriptions/{id}
Update subscription.

---

### 1.7 Subscription Actions

#### POST /subscriptions/{id}/upgrade
Upgrade subscription tier.

**Request:**
```json
{
  "new_tier_id": 3,
  "effective_date": "2025-12-07",
  "prorate": true
}
```

#### POST /subscriptions/{id}/downgrade
Downgrade subscription tier.

#### POST /subscriptions/{id}/cancel
Cancel subscription.

**Request:**
```json
{
  "reason": "Customer request",
  "effective_date": "2025-12-31",
  "retain_data_days": 90
}
```

#### POST /subscriptions/{id}/renew
Renew subscription.

---

### 1.8 Invoices

#### GET /invoices
List all invoices.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| tenant_id | int | Filter by tenant |
| status | string | draft, sent, paid, overdue, cancelled |
| date_from | date | Invoice date from |
| date_to | date | Invoice date to |

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "invoice_number": "INV-2025-001234",
      "tenant": {
        "id": 1,
        "name": "PT. Hotel Group"
      },
      "organization": {
        "id": 2,
        "name": "Bali Regional"
      },
      "invoice_date": "2025-12-01",
      "due_date": "2025-12-31",
      "subtotal": "7000000.0000",
      "tax_amount": "770000.0000",
      "total_amount": "7770000.0000",
      "paid_amount": "0.0000",
      "status": "sent",
      "items_count": 3
    }
  ]
}
```

#### GET /invoices/{id}
Get invoice detail with line items.

**Response (200):**
```json
{
  "data": {
    "id": 1,
    "invoice_number": "INV-2025-001234",
    "tenant": {
      "id": 1,
      "code": "HTL-001",
      "name": "PT. Hotel Group",
      "tax_id": "01.234.567.8-901.000"
    },
    "organization": {
      "id": 2,
      "code": "HGI-BALI",
      "name": "Bali Regional"
    },
    "invoice_date": "2025-12-01",
    "due_date": "2025-12-31",
    "period_start": "2025-12-01",
    "period_end": "2025-12-31",
    "subtotal": "7000000.0000",
    "tax_rate": "11.00",
    "tax_amount": "770000.0000",
    "total_amount": "7770000.0000",
    "paid_amount": "0.0000",
    "balance_due": "7770000.0000",
    "status": "sent",
    "notes": "Monthly subscription - December 2025",
    "items": [
      {
        "id": 1,
        "description": "PMS Enterprise - Monthly Fee",
        "subscription_id": 1,
        "quantity": "1.0000",
        "unit_price": "5000000.0000",
        "amount": "5000000.0000"
      },
      {
        "id": 2,
        "description": "PMS Enterprise - Additional Users (15 users)",
        "subscription_id": 1,
        "quantity": "15.0000",
        "unit_price": "100000.0000",
        "amount": "1500000.0000"
      },
      {
        "id": 3,
        "description": "Base Platform Fee",
        "subscription_id": null,
        "quantity": "1.0000",
        "unit_price": "500000.0000",
        "amount": "500000.0000"
      }
    ],
    "payments": []
  }
}
```

#### POST /invoices
Create manual invoice.

#### POST /invoices/generate
Generate invoices for billing period.

**Request:**
```json
{
  "period_start": "2025-12-01",
  "period_end": "2025-12-31",
  "tenant_ids": [1, 2, 3],
  "send_immediately": false
}
```

**Response (200):**
```json
{
  "data": {
    "generated_count": 15,
    "total_amount": "125000000.0000",
    "invoices": [
      {"id": 101, "tenant_id": 1, "amount": "7770000.0000"},
      {"id": 102, "tenant_id": 2, "amount": "3330000.0000"}
    ]
  },
  "message": "15 invoices generated successfully"
}
```

---

### 1.9 Invoice Actions

#### POST /invoices/{id}/send
Send invoice to tenant.

**Request:**
```json
{
  "email_to": ["billing@tenant.com"],
  "email_cc": ["finance@tenant.com"],
  "message": "Please find attached invoice"
}
```

#### POST /invoices/{id}/cancel
Cancel invoice.

#### POST /invoices/{id}/remind
Send payment reminder.

---

### 1.10 Payments

#### GET /payments
List all payments.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "payment_number": "PAY-2025-001234",
      "tenant": {
        "id": 1,
        "name": "PT. Hotel Group"
      },
      "invoice": {
        "id": 1,
        "invoice_number": "INV-2025-001234"
      },
      "amount": "7770000.0000",
      "payment_method": "bank_transfer",
      "payment_date": "2025-12-15",
      "reference_number": "TRF-123456",
      "status": "confirmed"
    }
  ]
}
```

#### GET /payments/{id}
Get payment detail.

#### POST /payments
Record payment.

**Request:**
```json
{
  "invoice_id": 1,
  "amount": "7770000.0000",
  "payment_method": "bank_transfer",
  "payment_date": "2025-12-15",
  "reference_number": "TRF-123456",
  "notes": "Transfer dari BCA"
}
```

#### POST /payments/{id}/confirm
Confirm payment (if pending verification).

#### POST /payments/{id}/refund
Process refund.

---

### 1.11 Owner Users (Internal Team)

#### GET /users
List owner team members.

#### GET /users/{id}
Get user detail.

#### POST /users
Create owner team member.

**Request:**
```json
{
  "email": "support@owner.com",
  "name": "Support User",
  "role": "support",
  "phone": "+62-812-3456789"
}
```

#### PUT /users/{id}
Update user.

#### DELETE /users/{id}
Deactivate user.

#### POST /users/{id}/reset-password
Reset user password.

---

### 1.12 Dashboard & Analytics

#### GET /dashboard/summary
Get dashboard summary.

**Response (200):**
```json
{
  "data": {
    "tenants": {
      "total": 150,
      "active": 120,
      "trial": 15,
      "suspended": 10,
      "pending": 5
    },
    "subscriptions": {
      "total": 450,
      "active": 400,
      "expiring_soon": 25
    },
    "revenue": {
      "current_month": "1250000000.0000",
      "previous_month": "1180000000.0000",
      "growth_percent": "5.93"
    },
    "invoices": {
      "pending_payment": 45,
      "overdue": 12,
      "total_outstanding": "350000000.0000"
    }
  }
}
```

#### GET /dashboard/revenue
Get revenue analytics.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| period | string | daily, weekly, monthly, yearly |
| date_from | date | Start date |
| date_to | date | End date |
| group_by | string | app, tier, tenant |

#### GET /dashboard/subscriptions
Get subscription analytics.

---

## Part 2: Community API (Shared)

### 2.1 Authentication

#### POST /auth/register
Register new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "phone": "+62-812-3456789"
}
```

**Response (201):**
```json
{
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_email_verified": false,
    "created_at": "2025-12-07T10:00:00Z"
  },
  "message": "Registration successful. Please verify your email."
}
```

#### POST /auth/login
Login user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "avatar_url": null,
      "organizations": [
        {
          "id": 1,
          "code": "HGI-BALI",
          "name": "Bali Regional",
          "role": "admin"
        }
      ]
    }
  }
}
```

#### POST /auth/refresh
Refresh access token.

#### POST /auth/logout
Logout and invalidate tokens.

#### POST /auth/verify-email
Verify email address.

**Request:**
```json
{
  "token": "verification_token_here"
}
```

#### POST /auth/forgot-password
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### POST /auth/reset-password
Reset password with token.

**Request:**
```json
{
  "token": "reset_token_here",
  "password": "new_secure_password"
}
```

---

### 2.2 Profile

#### GET /profile
Get current user profile.

**Response (200):**
```json
{
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+62-812-3456789",
    "avatar_url": "/avatars/1.jpg",
    "timezone": "Asia/Jakarta",
    "language": "id",
    "is_email_verified": true,
    "is_phone_verified": false,
    "created_at": "2025-01-01T00:00:00Z",
    "organizations": [
      {
        "id": 1,
        "code": "HGI-BALI",
        "name": "Bali Regional",
        "role": "admin",
        "is_default": true
      },
      {
        "id": 2,
        "code": "HGI-LOMBOK",
        "name": "Lombok Regional",
        "role": "viewer",
        "is_default": false
      }
    ]
  }
}
```

#### PUT /profile
Update profile.

**Request:**
```json
{
  "name": "John Doe Updated",
  "phone": "+62-812-9876543",
  "timezone": "Asia/Jakarta",
  "language": "en"
}
```

#### PUT /profile/avatar
Upload avatar.

**Request:** multipart/form-data with `avatar` file.

#### PUT /profile/password
Change password.

**Request:**
```json
{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

---

### 2.3 Organizations (User's View)

#### GET /organizations
List user's organizations.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "code": "HGI-BALI",
      "name": "Bali Regional",
      "level": "regional",
      "role": "admin",
      "permissions": ["manage_users", "view_reports", "manage_content"],
      "apps": [
        {
          "code": "PMS",
          "name": "Property Management System",
          "tier": "enterprise"
        },
        {
          "code": "POS",
          "name": "Point of Sale",
          "tier": "pro"
        }
      ]
    }
  ]
}
```

#### GET /organizations/{id}
Get organization detail (if user has access).

#### POST /organizations/{id}/switch
Switch active organization context.

**Response (200):**
```json
{
  "data": {
    "organization_id": 2,
    "organization_name": "Lombok Regional",
    "access_token": "eyJ..."
  },
  "message": "Switched to Lombok Regional"
}
```

---

### 2.4 Organization Members (Admin View)

#### GET /organizations/{org_id}/members
List organization members.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe"
      },
      "role": {
        "id": 1,
        "name": "admin",
        "display_name": "Administrator"
      },
      "is_active": true,
      "assigned_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /organizations/{org_id}/members
Invite/add member to organization.

**Request:**
```json
{
  "email": "newuser@example.com",
  "role_id": 2,
  "send_invitation": true
}
```

#### PUT /organizations/{org_id}/members/{user_id}
Update member role.

**Request:**
```json
{
  "role_id": 3
}
```

#### DELETE /organizations/{org_id}/members/{user_id}
Remove member from organization.

---

### 2.5 Roles & Permissions

#### GET /roles
List roles available for organization.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "code": "admin",
      "name": "Administrator",
      "description": "Full access to organization",
      "is_system": true,
      "permissions": ["*"]
    },
    {
      "id": 2,
      "code": "manager",
      "name": "Manager",
      "description": "Manage operations",
      "is_system": true,
      "permissions": ["view_*", "manage_content", "manage_devices"]
    },
    {
      "id": 3,
      "code": "viewer",
      "name": "Viewer",
      "description": "View only access",
      "is_system": true,
      "permissions": ["view_*"]
    }
  ]
}
```

#### GET /roles/{id}
Get role detail with permissions.

#### POST /roles
Create custom role (if allowed).

**Request:**
```json
{
  "code": "content_editor",
  "name": "Content Editor",
  "description": "Can manage content only",
  "permissions": ["view_content", "manage_content"]
}
```

#### PUT /roles/{id}
Update custom role.

#### DELETE /roles/{id}
Delete custom role.

#### GET /permissions
List all available permissions.

**Response (200):**
```json
{
  "data": [
    {
      "code": "manage_users",
      "name": "Manage Users",
      "category": "users",
      "description": "Add, edit, remove users"
    },
    {
      "code": "view_reports",
      "name": "View Reports",
      "category": "reports",
      "description": "View all reports"
    }
  ]
}
```

---

### 2.6 Settings

#### GET /settings
Get user settings.

**Response (200):**
```json
{
  "data": {
    "notifications": {
      "email_on_login": true,
      "email_on_password_change": true,
      "push_notifications": true
    },
    "display": {
      "theme": "light",
      "sidebar_collapsed": false,
      "date_format": "DD/MM/YYYY",
      "time_format": "24h"
    }
  }
}
```

#### PUT /settings
Update user settings.

#### GET /organizations/{org_id}/settings
Get organization settings.

#### PUT /organizations/{org_id}/settings
Update organization settings.

---

### 2.7 Notifications

#### GET /notifications
List user notifications.

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "type": "system",
      "title": "Welcome to the platform",
      "message": "Your account has been created successfully",
      "is_read": false,
      "action_url": "/profile",
      "created_at": "2025-12-07T10:00:00Z"
    }
  ],
  "meta": {
    "unread_count": 5
  }
}
```

#### POST /notifications/{id}/read
Mark notification as read.

#### POST /notifications/read-all
Mark all notifications as read.

---

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Email is required"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ]
  }
}
```

### HTTP Status Codes

| Code | Description | When |
|------|-------------|------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST (create) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error, invalid input |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | No permission for action |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate entry, business rule violation |
| 422 | Unprocessable Entity | Business logic error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Codes

| Code | Description |
|------|-------------|
| AUTH_INVALID_CREDENTIALS | Invalid email/password |
| AUTH_TOKEN_EXPIRED | Token has expired |
| AUTH_TOKEN_INVALID | Token is invalid |
| VALIDATION_ERROR | Input validation failed |
| RESOURCE_NOT_FOUND | Requested resource not found |
| PERMISSION_DENIED | No permission for this action |
| BUSINESS_RULE_VIOLATION | Business rule check failed |
| DUPLICATE_ENTRY | Unique constraint violation |
| PERIOD_CLOSED | Cannot modify closed period |
| TENANT_SUSPENDED | Tenant account is suspended |

---

## Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 10 req/minute |
| Read (GET) | 100 req/minute |
| Write (POST/PUT/DELETE) | 30 req/minute |
| Bulk Operations | 5 req/minute |

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702000000
```

---

## Versioning

API version in URL: `/api/v1/`, `/api/v2/`

Deprecation notice in header:
```
Deprecation: Sun, 01 Jan 2026 00:00:00 GMT
Sunset: Sun, 01 Jul 2026 00:00:00 GMT
Link: </api/v2/resource>; rel="successor-version"
```

---

*Last Updated: 2025-12-07*
