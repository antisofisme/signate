# INFRA-LAY2-006: Billing & Payment API Contracts

**VERSION**: Layer 2 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines the API contracts for Billing and Payment endpoints:
- Subscription management
- Plan information
- Checkout and payment
- Invoice management
- Usage tracking
- Midtrans webhook handling

---

## Base URL

```
Production: https://api.atlaspuguh.com/api/v1
Staging:    https://api.staging.atlaspuguh.com/api/v1
Local:      http://localhost:8000/api/v1
```

---

## Authentication

Most endpoints require JWT authentication with tenant context:

```
Authorization: Bearer <access_token>
```

Webhook endpoints (no auth, signature verification instead):
- `POST /webhooks/midtrans`

---

## 1. Plans

### GET /billing/plans

Get available subscription plans.

**Headers:**
```
Authorization: Bearer <access_token>  (optional)
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "plan_id": "free",
        "name": "Free",
        "description": "For personal projects and testing",
        "price": {
          "amount": 0,
          "currency": "IDR",
          "interval": "month",
          "formatted": "Rp 0"
        },
        "limits": {
          "projects": 1,
          "decisions_per_month": 1000,
          "team_members": 3,
          "rules": 10,
          "audit_retention_days": 30
        },
        "features": {
          "api_access": false,
          "sso": false,
          "priority_support": false,
          "sla_guarantee": false
        },
        "trial_days": 0,
        "is_current": true,
        "is_recommended": false
      },
      {
        "plan_id": "starter",
        "name": "Starter",
        "description": "For small teams getting started",
        "price": {
          "amount": 29000000,
          "currency": "IDR",
          "interval": "month",
          "formatted": "Rp 290.000"
        },
        "limits": {
          "projects": 5,
          "decisions_per_month": 10000,
          "team_members": 10,
          "rules": 50,
          "audit_retention_days": 90
        },
        "features": {
          "api_access": true,
          "sso": false,
          "priority_support": false,
          "sla_guarantee": false
        },
        "trial_days": 14,
        "is_current": false,
        "is_recommended": false
      },
      {
        "plan_id": "pro",
        "name": "Pro",
        "description": "For growing teams with advanced needs",
        "price": {
          "amount": 99000000,
          "currency": "IDR",
          "interval": "month",
          "formatted": "Rp 990.000"
        },
        "limits": {
          "projects": null,
          "decisions_per_month": 100000,
          "team_members": 50,
          "rules": null,
          "audit_retention_days": 365
        },
        "features": {
          "api_access": true,
          "sso": false,
          "priority_support": true,
          "sla_guarantee": true
        },
        "trial_days": 14,
        "is_current": false,
        "is_recommended": true
      },
      {
        "plan_id": "enterprise",
        "name": "Enterprise",
        "description": "For large organizations with custom requirements",
        "price": {
          "amount": null,
          "currency": "IDR",
          "interval": "year",
          "formatted": "Contact Sales"
        },
        "limits": {
          "projects": null,
          "decisions_per_month": null,
          "team_members": null,
          "rules": null,
          "audit_retention_days": 730
        },
        "features": {
          "api_access": true,
          "sso": true,
          "priority_support": true,
          "dedicated_support": true,
          "sla_guarantee": true,
          "custom_branding": true
        },
        "trial_days": 0,
        "is_current": false,
        "is_recommended": false,
        "contact_sales": true
      }
    ]
  }
}
```

**Notes:**
- `null` in limits means unlimited
- `is_current` is true if user is authenticated and on that plan
- `is_recommended` highlights the best value plan

---

## 2. Subscription

### GET /billing/subscription

Get current subscription details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "subscription_id": "sub_123456",
      "plan_id": "starter",
      "plan_name": "Starter",
      "status": "active",
      "current_period": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-02-01T00:00:00Z"
      },
      "trial": {
        "is_trialing": false,
        "trial_end": null
      },
      "cancellation": {
        "cancel_at_period_end": false,
        "cancelled_at": null,
        "cancellation_reason": null
      },
      "payment_provider": "midtrans",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "plan": {
      "plan_id": "starter",
      "name": "Starter",
      "price": {
        "amount": 29000000,
        "currency": "IDR",
        "interval": "month"
      },
      "limits": {
        "projects": 5,
        "decisions_per_month": 10000,
        "team_members": 10,
        "rules": 50
      }
    },
    "usage": {
      "decisions_this_month": 2500,
      "decisions_limit": 10000,
      "decisions_percentage": 25,
      "projects_count": 2,
      "projects_limit": 5,
      "projects_percentage": 40,
      "team_members_count": 3,
      "team_members_limit": 10,
      "team_members_percentage": 30,
      "usage_reset_at": "2024-02-01T00:00:00Z"
    },
    "billing": {
      "next_billing_date": "2024-02-01T00:00:00Z",
      "next_billing_amount": 29000000,
      "currency": "IDR"
    }
  }
}
```

**Subscription Status Values:**
- `trialing`: In trial period
- `active`: Paid and active
- `past_due`: Payment failed, grace period
- `cancelled`: Subscription cancelled
- `paused`: Subscription paused

---

## 3. Checkout

### POST /billing/checkout

Create a checkout session for plan upgrade.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "plan_id": "pro",
  "billing_interval": "month"
}
```

**Validation:**
- `plan_id`: Required, must be valid plan (not "free")
- `billing_interval`: Required, "month" or "year"

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "checkout": {
      "checkout_id": "INV-2024-00001",
      "snap_token": "xxxxx-xxxxx-xxxxx",
      "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/xxxxx",
      "expires_at": "2024-01-27T12:00:00Z"
    },
    "invoice": {
      "invoice_id": "inv_123456",
      "invoice_number": "INV-2024-00001",
      "amount": 99000000,
      "currency": "IDR",
      "status": "pending"
    },
    "plan": {
      "plan_id": "pro",
      "name": "Pro",
      "price": 99000000
    }
  }
}
```

**Error Response (400 Bad Request - Already on Plan):*
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_ON_PLAN",
    "message": "You are already subscribed to the Pro plan"
  }
}
```

**Error Response (400 Bad Request - Downgrade):*
```json
{
  "success": false,
  "error": {
    "code": "USE_DOWNGRADE_ENDPOINT",
    "message": "To downgrade, use POST /billing/downgrade instead",
    "redirect": "/billing/downgrade"
  }
}
```

---

## 4. Downgrade

### POST /billing/downgrade

Downgrade to a lower plan (takes effect at period end).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "plan_id": "starter"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "subscription_id": "sub_123456",
      "current_plan_id": "pro",
      "scheduled_plan_id": "starter",
      "scheduled_change_at": "2024-02-01T00:00:00Z"
    },
    "message": "Your plan will change to Starter on February 1, 2024. You'll continue to enjoy Pro features until then."
  }
}
```

**Error Response (400 Bad Request - Data Loss Warning):*
```json
{
  "success": false,
  "error": {
    "code": "DOWNGRADE_DATA_LOSS",
    "message": "Downgrading would exceed new plan limits",
    "details": {
      "projects": {
        "current": 8,
        "new_limit": 5,
        "action_required": "Delete 3 projects before downgrading"
      },
      "team_members": {
        "current": 15,
        "new_limit": 10,
        "action_required": "Remove 5 team members before downgrading"
      }
    },
    "confirm_url": "/billing/downgrade?confirm=true"
  }
}
```

---

## 5. Cancel Subscription

### POST /billing/cancel

Cancel subscription (continues until period end).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "reason": "Too expensive",
  "feedback": "Would use again if pricing was lower"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "subscription_id": "sub_123456",
      "status": "active",
      "cancel_at_period_end": true,
      "current_period_end": "2024-02-01T00:00:00Z"
    },
    "message": "Your subscription has been cancelled. You'll have access until February 1, 2024, then your account will revert to the Free plan."
  }
}
```

### POST /billing/reactivate

Reactivate cancelled subscription before period end.

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
    "subscription": {
      "subscription_id": "sub_123456",
      "status": "active",
      "cancel_at_period_end": false
    },
    "message": "Your subscription has been reactivated. You'll continue to be billed on February 1, 2024."
  }
}
```

---

## 6. Invoices

### GET /billing/invoices

List invoices for current tenant.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, paid, failed, cancelled)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset

**Request:**
```
GET /billing/invoices?status=paid&limit=10
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "invoices": [
      {
        "invoice_id": "inv_123456",
        "invoice_number": "INV-2024-00001",
        "status": "paid",
        "amount": 99000000,
        "currency": "IDR",
        "formatted_amount": "Rp 990.000",
        "plan_name": "Pro",
        "invoice_date": "2024-01-01",
        "due_date": "2024-01-08",
        "paid_at": "2024-01-02T10:30:00Z",
        "payment_method": "credit_card",
        "pdf_url": "/billing/invoices/inv_123456/pdf"
      },
      {
        "invoice_id": "inv_123455",
        "invoice_number": "INV-2023-00012",
        "status": "paid",
        "amount": 99000000,
        "currency": "IDR",
        "formatted_amount": "Rp 990.000",
        "plan_name": "Pro",
        "invoice_date": "2023-12-01",
        "due_date": "2023-12-08",
        "paid_at": "2023-12-01T09:15:00Z",
        "payment_method": "gopay",
        "pdf_url": "/billing/invoices/inv_123455/pdf"
      }
    ],
    "pagination": {
      "total": 12,
      "limit": 10,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### GET /billing/invoices/{invoice_id}

Get invoice details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "invoice": {
      "invoice_id": "inv_123456",
      "invoice_number": "INV-2024-00001",
      "status": "paid",
      "amount": 99000000,
      "currency": "IDR",
      "formatted_amount": "Rp 990.000",
      "line_items": [
        {
          "description": "Pro Plan - January 2024",
          "quantity": 1,
          "unit_price": 99000000,
          "amount": 99000000
        }
      ],
      "subtotal": 99000000,
      "tax_rate": 0.11,
      "tax_amount": 10890000,
      "total": 109890000,
      "tenant": {
        "name": "John's Workspace",
        "slug": "johns-workspace"
      },
      "billing_details": {
        "name": "John Doe",
        "email": "john@example.com",
        "address": null
      },
      "invoice_date": "2024-01-01",
      "due_date": "2024-01-08",
      "paid_at": "2024-01-02T10:30:00Z",
      "payment": {
        "provider": "midtrans",
        "method": "credit_card",
        "card_brand": "visa",
        "card_last_four": "4242",
        "transaction_id": "txn_12345678"
      },
      "pdf_url": "/billing/invoices/inv_123456/pdf"
    }
  }
}
```

### GET /billing/invoices/{invoice_id}/pdf

Download invoice as PDF.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="INV-2024-00001.pdf"
```

---

## 7. Payment Methods

### GET /billing/payment-methods

List saved payment methods.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "payment_methods": [
      {
        "payment_method_id": "pm_123456",
        "type": "card",
        "is_default": true,
        "details": {
          "brand": "visa",
          "last_four": "4242",
          "exp_month": 12,
          "exp_year": 2025
        },
        "created_at": "2024-01-01T10:00:00Z"
      },
      {
        "payment_method_id": "pm_123457",
        "type": "gopay",
        "is_default": false,
        "details": {
          "phone_masked": "0812****5678"
        },
        "created_at": "2024-01-05T14:00:00Z"
      }
    ]
  }
}
```

### DELETE /billing/payment-methods/{payment_method_id}

Remove a saved payment method.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Payment method removed"
  }
}
```

### PATCH /billing/payment-methods/{payment_method_id}/default

Set a payment method as default.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "payment_method": {
      "payment_method_id": "pm_123457",
      "is_default": true
    },
    "message": "Default payment method updated"
  }
}
```

---

## 8. Usage

### GET /billing/usage

Get current usage statistics.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "usage": {
      "period": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-02-01T00:00:00Z",
        "days_remaining": 5
      },
      "decisions": {
        "used": 7500,
        "limit": 10000,
        "percentage": 75,
        "status": "normal",
        "forecast_end_of_month": 9000
      },
      "projects": {
        "used": 3,
        "limit": 5,
        "percentage": 60,
        "status": "normal"
      },
      "team_members": {
        "used": 8,
        "limit": 10,
        "percentage": 80,
        "status": "warning"
      },
      "rules": {
        "used": 25,
        "limit": 50,
        "percentage": 50,
        "status": "normal"
      },
      "storage": {
        "used_bytes": 52428800,
        "used_formatted": "50 MB",
        "limit_bytes": 1073741824,
        "limit_formatted": "1 GB",
        "percentage": 5,
        "status": "normal"
      }
    },
    "alerts": [
      {
        "type": "warning",
        "resource": "team_members",
        "message": "You've used 80% of your team member limit",
        "action": "Upgrade to Pro for more seats"
      }
    ],
    "history": {
      "decisions_by_day": [
        { "date": "2024-01-20", "count": 350 },
        { "date": "2024-01-21", "count": 420 },
        { "date": "2024-01-22", "count": 380 },
        { "date": "2024-01-23", "count": 510 },
        { "date": "2024-01-24", "count": 290 },
        { "date": "2024-01-25", "count": 450 },
        { "date": "2024-01-26", "count": 320 }
      ]
    }
  }
}
```

**Usage Status Values:**
- `normal`: Under 70% of limit
- `warning`: 70-90% of limit
- `critical`: Over 90% of limit
- `exceeded`: At or over 100% of limit

---

## 9. Webhooks

### POST /webhooks/midtrans

Handle Midtrans payment webhook.

**Note:** This endpoint is public (no JWT auth). Security via signature verification.

**Headers:**
```
Content-Type: application/json
```

**Request (from Midtrans):**
```json
{
  "transaction_status": "settlement",
  "transaction_id": "txn_12345678",
  "order_id": "INV-2024-00001",
  "gross_amount": "990000.00",
  "payment_type": "credit_card",
  "status_code": "200",
  "signature_key": "sha512_hash_here",
  "fraud_status": "accept",
  "transaction_time": "2024-01-26 10:30:00",
  "settlement_time": "2024-01-26 10:30:15",
  "masked_card": "424242******4242",
  "card_type": "credit"
}
```

**Transaction Status Values:**
- `pending`: Waiting for payment
- `capture`: Card authorized (not settled)
- `settlement`: Payment successful
- `deny`: Payment denied
- `cancel`: Payment cancelled
- `expire`: Payment expired
- `refund`: Payment refunded

**Success Response (200 OK):**
```json
{
  "success": true
}
```

**Note:** Always return 200 to prevent Midtrans retry storms. Log errors internally.

### Webhook Processing Logic

```
1. Receive webhook
2. Verify signature (sha512)
3. Parse transaction status
4. Find invoice by order_id
5. Update based on status:
   - settlement: invoice.status = paid, subscription.status = active
   - deny/expire: invoice.status = failed, subscription.status = past_due
   - refund: invoice.status = refunded, subscription = handle accordingly
6. Emit events for downstream processing
7. Return 200 OK
```

---

## 10. Enterprise Contact

### POST /billing/contact-sales

Submit enterprise inquiry.

**Headers:**
```
Authorization: Bearer <access_token>  (optional)
```

**Request:**
```json
{
  "company_name": "Acme Corp",
  "contact_name": "John Doe",
  "email": "john@acmecorp.com",
  "phone": "+62812345678",
  "team_size": "50-100",
  "use_case": "We need SSO integration and custom SLA for our compliance requirements",
  "current_plan": "pro"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "inquiry_id": "inq_123456",
    "message": "Thank you for your interest! Our sales team will contact you within 24 hours."
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
    "details": { ... }
  }
}
```

### Billing-Specific Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `ALREADY_ON_PLAN` | 400 | Already subscribed to this plan |
| `USE_DOWNGRADE_ENDPOINT` | 400 | Use downgrade endpoint instead |
| `DOWNGRADE_DATA_LOSS` | 400 | Downgrade would exceed limits |
| `PAYMENT_FAILED` | 402 | Payment processing failed |
| `PLAN_NOT_FOUND` | 404 | Plan doesn't exist |
| `INVOICE_NOT_FOUND` | 404 | Invoice not found |
| `SUBSCRIPTION_NOT_FOUND` | 404 | No active subscription |
| `PLAN_LIMIT_REACHED` | 403 | Plan limit exceeded |
| `ENTERPRISE_REQUIRED` | 403 | Feature requires enterprise plan |
| `WEBHOOK_INVALID_SIGNATURE` | 401 | Webhook signature verification failed |

---

## Frontend Integration (Midtrans Snap)

### Include Snap.js

```html
<!-- Sandbox -->
<script src="https://app.sandbox.midtrans.com/snap/snap.js" data-client-key="SB-xxx"></script>

<!-- Production -->
<script src="https://app.midtrans.com/snap/snap.js" data-client-key="xxx"></script>
```

### Payment Flow

```typescript
// 1. Create checkout
const response = await fetch('/api/v1/billing/checkout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ plan_id: 'pro' })
});

const { data } = await response.json();

// 2. Open Snap popup
window.snap.pay(data.checkout.snap_token, {
  onSuccess: function(result) {
    // Payment successful
    // Refresh subscription status
    window.location.href = '/billing?status=success';
  },
  onPending: function(result) {
    // Payment pending (bank transfer, etc.)
    window.location.href = '/billing?status=pending';
  },
  onError: function(result) {
    // Payment error
    console.error('Payment failed:', result);
    alert('Payment failed. Please try again.');
  },
  onClose: function() {
    // User closed popup without completing
    console.log('Payment popup closed');
  }
});
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /billing/checkout` | 10 | 1 hour / tenant |
| `POST /billing/cancel` | 5 | 1 hour / tenant |
| `POST /webhooks/midtrans` | 100 | 1 min / IP |
| Other billing endpoints | 60 | 1 min / tenant |

---

## Checklist: Billing API Contracts DRAFT

- ✅ Plans endpoint defined
- ✅ Subscription endpoint defined
- ✅ Checkout endpoint defined
- ✅ Downgrade endpoint defined
- ✅ Cancel/Reactivate endpoints defined
- ✅ Invoices endpoints defined
- ✅ Payment methods endpoints defined
- ✅ Usage endpoint defined
- ✅ Webhook endpoint defined
- ✅ Enterprise contact endpoint defined
- ✅ Error response format defined
- ✅ Frontend integration documented
- ✅ Rate limits defined

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-010: Payment & Billing Model
- INFRA-DEC-011: Modular Architecture
