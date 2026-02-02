# INFRA-DEC-010: Payment & Billing Model

**VERSION**: Layer 0 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines the payment and billing model for ARSAKA_PUGUH SaaS platform:
- Subscription plans (Free, Starter, Pro, Enterprise)
- Midtrans payment gateway integration
- Billing cycles and invoicing
- Usage metering and plan limits
- Modular architecture for easy provider swap

---

## Payment Gateway: Midtrans

### Why Midtrans

| Factor | Midtrans | Alternatives |
|--------|----------|--------------|
| Currency | IDR (native) | Stripe (USD primary) |
| Local Payment | GoPay, OVO, Dana, VA | Limited |
| Pricing | Competitive for Indonesia | Higher for cross-border |
| Integration | Good API, Snap popup | N/A |
| Compliance | Indonesia BI regulations | N/A |

### Modular Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      PAYMENT MODULE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Interface (Abstract)              Adapter (Concrete)           │
│   ┌─────────────────────┐          ┌─────────────────────┐      │
│   │  IPaymentGateway    │          │  MidtransAdapter    │      │
│   │  ─────────────────  │  ◄────── │  ─────────────────  │      │
│   │  create_checkout()  │          │  Uses Snap API      │      │
│   │  verify_webhook()   │          │  Handles callbacks  │      │
│   │  get_transaction()  │          │  IDR currency       │      │
│   │  cancel_sub()       │          │                     │      │
│   └─────────────────────┘          └─────────────────────┘      │
│            ▲                                                     │
│            │                       ┌─────────────────────┐      │
│            │ (Future: easy swap)   │  StripeAdapter      │      │
│            └────────────────────── │  (Not implemented)  │      │
│                                    └─────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Subscription Plans

### Plan Definitions

| Plan | Price (IDR) | Price (USD) | Billing | Trial |
|------|-------------|-------------|---------|-------|
| **Free** | 0 | $0 | N/A | N/A |
| **Starter** | 290,000/mo | ~$18/mo | Monthly | 14 days |
| **Pro** | 990,000/mo | ~$62/mo | Monthly | 14 days |
| **Enterprise** | Custom | Custom | Annual | Custom |

### Plan Features

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Projects | 1 | 5 | Unlimited | Unlimited |
| Decisions/month | 1,000 | 10,000 | 100,000 | Custom |
| Team members | 3 | 10 | 50 | Unlimited |
| Rules | 10 | 50 | Unlimited | Unlimited |
| Audit retention | 30 days | 90 days | 1 year | Custom |
| API access | ❌ | ✅ | ✅ | ✅ |
| SSO | ❌ | ❌ | ❌ | ✅ |
| SLA | ❌ | ❌ | 99.9% | 99.99% |
| Support | Community | Email | Priority | Dedicated |

### Plan Metadata

```typescript
SubscriptionPlan {
  plan_id: string              // "free" | "starter" | "pro" | "enterprise"
  name: string                 // "Free", "Starter", "Pro", "Enterprise"

  // Pricing
  price_cents: number          // Price in smallest currency unit (IDR)
  currency: "IDR"
  billing_interval: "month" | "year"

  // Limits
  max_projects: number | null  // null = unlimited
  max_decisions_per_month: number | null
  max_team_members: number | null
  max_rules: number | null
  audit_retention_days: number

  // Features (boolean flags)
  features: {
    api_access: boolean
    sso: boolean
    priority_support: boolean
    custom_branding: boolean
    dedicated_support: boolean
    sla_guarantee: boolean
  }

  // Trial
  trial_days: number           // 0 = no trial

  // Status
  is_active: boolean           // Can new users subscribe?
  display_order: number        // Order on pricing page
}
```

### Database Schema

```sql
CREATE TABLE subscription_plans (
  plan_id VARCHAR(20) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,

  price_cents INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
  billing_interval VARCHAR(10) NOT NULL DEFAULT 'month',

  max_projects INTEGER,          -- NULL = unlimited
  max_decisions_per_month INTEGER,
  max_team_members INTEGER,
  max_rules INTEGER,
  audit_retention_days INTEGER NOT NULL DEFAULT 30,

  features JSONB NOT NULL DEFAULT '{}',

  trial_days INTEGER NOT NULL DEFAULT 0,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  display_order INTEGER NOT NULL DEFAULT 0,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data
INSERT INTO subscription_plans (plan_id, name, price_cents, max_projects, max_decisions_per_month, max_team_members, max_rules, audit_retention_days, trial_days, features, display_order) VALUES
  ('free', 'Free', 0, 1, 1000, 3, 10, 30, 0, '{"api_access": false, "sso": false}', 1),
  ('starter', 'Starter', 29000000, 5, 10000, 10, 50, 90, 14, '{"api_access": true, "sso": false}', 2),
  ('pro', 'Pro', 99000000, NULL, 100000, 50, NULL, 365, 14, '{"api_access": true, "sso": false, "priority_support": true, "sla_guarantee": true}', 3),
  ('enterprise', 'Enterprise', 0, NULL, NULL, NULL, NULL, 730, 0, '{"api_access": true, "sso": true, "priority_support": true, "dedicated_support": true, "sla_guarantee": true, "custom_branding": true}', 4);
```

---

## 2. Subscriptions

### Subscription Entity

```typescript
Subscription {
  subscription_id: UUID
  tenant_id: UUID              // One subscription per tenant

  // Plan
  plan_id: string              // FK to subscription_plans
  status: "trialing" | "active" | "past_due" | "cancelled" | "paused"

  // Payment provider
  payment_provider: "midtrans" | "stripe" | "manual"
  provider_subscription_id: string | null  // Midtrans doesn't have recurring, use order_id

  // Billing period
  current_period_start: timestamp
  current_period_end: timestamp

  // Trial
  trial_end_at: timestamp | null

  // Cancellation
  cancel_at_period_end: boolean  // Will cancel at period end
  cancelled_at: timestamp | null
  cancellation_reason: string | null

  // Usage (denormalized for quick checks)
  decisions_this_month: number
  usage_reset_at: timestamp

  created_at: timestamp
  updated_at: timestamp
}
```

### Database Schema

```sql
CREATE TABLE subscriptions (
  subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(tenant_id) ON DELETE CASCADE,

  plan_id VARCHAR(20) NOT NULL REFERENCES subscription_plans(plan_id),
  status VARCHAR(20) NOT NULL DEFAULT 'active',

  payment_provider VARCHAR(20) NOT NULL DEFAULT 'manual',
  provider_subscription_id VARCHAR(255),

  current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  current_period_end TIMESTAMPTZ NOT NULL,

  trial_end_at TIMESTAMPTZ,

  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,

  decisions_this_month INTEGER NOT NULL DEFAULT 0,
  usage_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT check_status CHECK (
    status IN ('trialing', 'active', 'past_due', 'cancelled', 'paused')
  )
);

CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);
```

---

## 3. Invoices

### Invoice Entity

```typescript
Invoice {
  invoice_id: UUID
  tenant_id: UUID
  subscription_id: UUID

  // Invoice details
  invoice_number: string       // INV-2024-00001
  amount_cents: number
  currency: "IDR"

  // Line items
  line_items: [{
    description: string        // "Pro Plan - January 2024"
    quantity: number           // 1
    unit_price_cents: number   // 99000000
    amount_cents: number       // 99000000
  }]

  // Tax (if applicable)
  tax_rate: number             // 0.11 for 11% PPN
  tax_amount_cents: number
  total_cents: number

  // Status
  status: "draft" | "pending" | "paid" | "failed" | "cancelled" | "refunded"

  // Payment
  payment_provider: "midtrans" | "stripe" | "manual"
  provider_invoice_id: string | null
  provider_payment_id: string | null

  // Dates
  invoice_date: timestamp
  due_date: timestamp
  paid_at: timestamp | null

  created_at: timestamp
  updated_at: timestamp
}
```

### Database Schema

```sql
CREATE TABLE invoices (
  invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
  subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id),

  invoice_number VARCHAR(50) NOT NULL UNIQUE,
  amount_cents INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'IDR',

  line_items JSONB NOT NULL DEFAULT '[]',

  tax_rate DECIMAL(5,4) NOT NULL DEFAULT 0,
  tax_amount_cents INTEGER NOT NULL DEFAULT 0,
  total_cents INTEGER NOT NULL,

  status VARCHAR(20) NOT NULL DEFAULT 'draft',

  payment_provider VARCHAR(20) NOT NULL DEFAULT 'midtrans',
  provider_invoice_id VARCHAR(255),
  provider_payment_id VARCHAR(255),

  invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
  due_date DATE NOT NULL,
  paid_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT check_invoice_status CHECK (
    status IN ('draft', 'pending', 'paid', 'failed', 'cancelled', 'refunded')
  )
);

CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
```

---

## 4. Payment Methods

### Payment Method Entity

```typescript
PaymentMethod {
  payment_method_id: UUID
  tenant_id: UUID

  // Provider
  payment_provider: "midtrans"
  provider_method_id: string | null

  // Type
  type: "card" | "bank_transfer" | "gopay" | "ovo" | "dana" | "shopeepay"

  // Details (masked)
  details: {
    // Card
    brand?: string             // "visa", "mastercard"
    last_four?: string         // "4242"
    exp_month?: number
    exp_year?: number

    // Bank transfer
    bank?: string              // "bca", "bni", "mandiri"

    // E-wallet
    phone_masked?: string      // "0812****5678"
  }

  is_default: boolean

  created_at: timestamp
  updated_at: timestamp
}
```

### Database Schema

```sql
CREATE TABLE payment_methods (
  payment_method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

  payment_provider VARCHAR(20) NOT NULL DEFAULT 'midtrans',
  provider_method_id VARCHAR(255),

  type VARCHAR(30) NOT NULL,
  details JSONB NOT NULL DEFAULT '{}',

  is_default BOOLEAN NOT NULL DEFAULT FALSE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT check_payment_type CHECK (
    type IN ('card', 'bank_transfer', 'gopay', 'ovo', 'dana', 'shopeepay')
  )
);

CREATE INDEX idx_payment_methods_tenant ON payment_methods(tenant_id);

-- Only one default per tenant
CREATE UNIQUE INDEX idx_payment_methods_default ON payment_methods(tenant_id)
  WHERE is_default = TRUE;
```

---

## 5. Midtrans Integration

### Midtrans API Overview

Midtrans provides several payment APIs:
- **Snap**: Hosted payment popup (recommended)
- **Core API**: Direct API integration
- **Recurring**: Subscription billing (limited features)

For ARSAKA_PUGUH, we use **Snap** for simplicity and security.

### Payment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CHECKOUT FLOW                                │
└─────────────────────────────────────────────────────────────────────┘

1. User clicks "Upgrade to Pro"
         │
         ▼
2. Frontend calls: POST /api/v1/billing/checkout
   {
     plan_id: "pro",
     billing_interval: "month"
   }
         │
         ▼
3. Backend creates Midtrans Snap transaction:
   POST https://app.sandbox.midtrans.com/snap/v1/transactions
   {
     "transaction_details": {
       "order_id": "INV-2024-00001",
       "gross_amount": 99000000
     },
     "customer_details": {
       "email": "user@example.com",
       "first_name": "John"
     },
     "item_details": [{
       "id": "pro-monthly",
       "price": 99000000,
       "quantity": 1,
       "name": "Pro Plan - Monthly"
     }]
   }
         │
         ▼
4. Backend returns Snap token to frontend:
   {
     "success": true,
     "data": {
       "snap_token": "xxx-xxx-xxx",
       "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/xxx"
     }
   }
         │
         ▼
5. Frontend opens Snap popup:
   snap.pay(snapToken, {
     onSuccess: (result) => { ... },
     onPending: (result) => { ... },
     onError: (result) => { ... },
     onClose: () => { ... }
   })
         │
         ▼
6. User completes payment (Card/GoPay/Bank Transfer)
         │
         ▼
7. Midtrans sends webhook:
   POST /webhooks/midtrans
   {
     "transaction_status": "settlement",
     "order_id": "INV-2024-00001",
     "gross_amount": "99000000.00",
     "payment_type": "credit_card",
     ...
   }
         │
         ▼
8. Backend verifies signature and updates subscription:
   - Invoice status → "paid"
   - Subscription status → "active"
   - Subscription period → extended
         │
         ▼
9. Frontend receives success callback → refresh page
```

### Midtrans Webhook Handling

```typescript
// Webhook payload from Midtrans
MidtransWebhook {
  transaction_status: "capture" | "settlement" | "pending" | "deny" | "cancel" | "expire" | "refund"
  order_id: string           // Our invoice number
  transaction_id: string     // Midtrans transaction ID
  gross_amount: string       // Amount in string format
  payment_type: string       // "credit_card", "gopay", "bank_transfer", etc.
  signature_key: string      // For verification
  fraud_status?: string      // "accept" | "challenge" | "deny"
}

// Signature verification
function verifyMidtransSignature(payload: MidtransWebhook): boolean {
  const serverKey = process.env.MIDTRANS_SERVER_KEY;
  const data = payload.order_id + payload.status_code + payload.gross_amount + serverKey;
  const expectedSignature = crypto.createHash('sha512').update(data).digest('hex');
  return payload.signature_key === expectedSignature;
}
```

### Transaction Status Mapping

| Midtrans Status | Invoice Status | Subscription Action |
|-----------------|----------------|---------------------|
| `pending` | `pending` | No change |
| `capture` | `pending` | No change (card auth) |
| `settlement` | `paid` | Activate/extend period |
| `deny` | `failed` | Mark as past_due |
| `cancel` | `cancelled` | No change |
| `expire` | `failed` | Mark as past_due |
| `refund` | `refunded` | Cancel subscription |

### Environment Configuration

```env
# Midtrans Sandbox (Development)
MIDTRANS_SERVER_KEY=SB-Mid-server-xxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
MIDTRANS_MERCHANT_ID=G123456789
MIDTRANS_IS_PRODUCTION=false
MIDTRANS_SNAP_URL=https://app.sandbox.midtrans.com/snap/v1/transactions
MIDTRANS_CORE_URL=https://api.sandbox.midtrans.com/v2

# Midtrans Production
# MIDTRANS_SERVER_KEY=Mid-server-xxx
# MIDTRANS_CLIENT_KEY=Mid-client-xxx
# MIDTRANS_IS_PRODUCTION=true
# MIDTRANS_SNAP_URL=https://app.midtrans.com/snap/v1/transactions
# MIDTRANS_CORE_URL=https://api.midtrans.com/v2
```

---

## 6. Billing Operations

### Subscription Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUBSCRIPTION LIFECYCLE                        │
└─────────────────────────────────────────────────────────────────┘

                    ┌───────────┐
                    │  CREATE   │ (new tenant → free plan)
                    └─────┬─────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │                                │
         ▼                                │
   ┌──────────┐                    ┌──────┴─────┐
   │ TRIALING │──(trial ends)────► │   ACTIVE   │◄────────────┐
   └──────────┘                    └──────┬─────┘             │
         │                                │                    │
         │                                │                    │
         │ (no payment)                   │ (payment fails)    │ (payment succeeds)
         │                                ▼                    │
         │                         ┌───────────┐              │
         └────────────────────────►│ PAST_DUE  │──────────────┘
                                   └─────┬─────┘
                                         │
                                         │ (after grace period)
                                         ▼
                                   ┌───────────┐
                                   │ CANCELLED │
                                   └───────────┘
```

### Subscription Operations

```typescript
// Upgrade plan
async function upgradePlan(tenant_id: string, new_plan_id: string): Promise<Checkout> {
  // 1. Validate new plan exists and is higher tier
  // 2. Calculate prorated amount (optional)
  // 3. Create Midtrans checkout
  // 4. Return checkout URL/token
}

// Downgrade plan
async function downgradePlan(tenant_id: string, new_plan_id: string): Promise<void> {
  // 1. Validate new plan exists and is lower tier
  // 2. Mark subscription to change at period end
  // 3. New plan takes effect next billing cycle
}

// Cancel subscription
async function cancelSubscription(tenant_id: string, reason: string): Promise<void> {
  // 1. Mark cancel_at_period_end = true
  // 2. Record cancellation reason
  // 3. Subscription remains active until period end
  // 4. Then reverts to free plan
}

// Reactivate subscription
async function reactivateSubscription(tenant_id: string): Promise<void> {
  // 1. If cancel_at_period_end = true, set to false
  // 2. If already cancelled, create new checkout
}
```

### Usage Metering

```typescript
// Increment decision count
async function incrementDecisionCount(tenant_id: string): Promise<void> {
  await db.query(`
    UPDATE subscriptions
    SET decisions_this_month = decisions_this_month + 1,
        updated_at = NOW()
    WHERE tenant_id = $1
  `, [tenant_id]);
}

// Check if limit exceeded
async function checkDecisionLimit(tenant_id: string): Promise<boolean> {
  const result = await db.query(`
    SELECT s.decisions_this_month, p.max_decisions_per_month
    FROM subscriptions s
    JOIN subscription_plans p ON s.plan_id = p.plan_id
    WHERE s.tenant_id = $1
  `, [tenant_id]);

  const { decisions_this_month, max_decisions_per_month } = result.rows[0];

  if (max_decisions_per_month === null) return false; // Unlimited
  return decisions_this_month >= max_decisions_per_month;
}

// Reset monthly usage (cron job)
async function resetMonthlyUsage(): Promise<void> {
  await db.query(`
    UPDATE subscriptions
    SET decisions_this_month = 0,
        usage_reset_at = NOW(),
        updated_at = NOW()
    WHERE usage_reset_at < NOW() - INTERVAL '1 month'
  `);
}
```

---

## 7. Plan Limit Enforcement

### Enforcement Points

| Limit | Enforcement Point | Action on Exceed |
|-------|-------------------|------------------|
| Projects | Project creation | Block with upgrade prompt |
| Decisions/month | Decision creation | Block with upgrade prompt |
| Team members | Member invitation | Block with upgrade prompt |
| Rules | Rule creation | Block with upgrade prompt |
| Audit retention | Background job | Auto-delete old records |

### Implementation

```typescript
// Guard rail: Check project limit
async function checkProjectLimit(tenant_id: string): Promise<void> {
  const subscription = await getSubscription(tenant_id);
  const plan = await getPlan(subscription.plan_id);

  if (plan.max_projects === null) return; // Unlimited

  const projectCount = await countProjects(tenant_id);

  if (projectCount >= plan.max_projects) {
    throw new PlanLimitError(
      "PROJECT_LIMIT_REACHED",
      `Your ${plan.name} plan allows ${plan.max_projects} projects. ` +
      `Upgrade to create more projects.`
    );
  }
}

// Guard rail: Check decision limit
async function checkDecisionLimit(tenant_id: string): Promise<void> {
  const subscription = await getSubscription(tenant_id);
  const plan = await getPlan(subscription.plan_id);

  if (plan.max_decisions_per_month === null) return; // Unlimited

  if (subscription.decisions_this_month >= plan.max_decisions_per_month) {
    throw new PlanLimitError(
      "DECISION_LIMIT_REACHED",
      `You've reached your monthly limit of ${plan.max_decisions_per_month} decisions. ` +
      `Upgrade for more capacity.`
    );
  }
}
```

---

## 8. Guard Rails

### GR-BILL-1: One Subscription Per Tenant
```
Each tenant has exactly ONE subscription
Cannot have multiple active subscriptions
Upgrade/downgrade replaces current subscription
```

### GR-BILL-2: Webhook Verification
```
ALL Midtrans webhooks MUST be signature-verified
Reject requests without valid signature
Log all webhook attempts (valid and invalid)
```

### GR-BILL-3: Idempotent Webhook Processing
```
Webhook may be sent multiple times
Use order_id + transaction_status as idempotency key
Do not double-credit or double-charge
```

### GR-BILL-4: Grace Period for Past Due
```
If payment fails:
  - Status → past_due
  - Grace period: 7 days
  - Send reminder emails (day 1, 3, 5, 7)
  - After grace period → cancel or downgrade to free
```

### GR-BILL-5: Plan Downgrade at Period End
```
Downgrade does NOT take effect immediately
Current period continues at higher plan
New plan starts at next billing cycle
```

### GR-BILL-6: Data Retention on Cancel
```
Cancelled tenants keep data for 30 days
After 30 days, data may be deleted
Enterprise tenants have custom retention
```

### GR-BILL-7: No Prorated Refunds (v1)
```
v1: No prorated refunds for downgrades
User gets remainder of current period at higher tier
Full refunds only for exceptional cases (manual)
```

---

## 9. API Endpoints

### Billing Endpoints

```typescript
// Get current subscription
GET /api/v1/billing/subscription
→ { subscription, plan, usage }

// Get available plans
GET /api/v1/billing/plans
→ { plans: Plan[] }

// Create checkout for upgrade
POST /api/v1/billing/checkout
{ plan_id: string }
→ { snap_token, redirect_url }

// Cancel subscription
POST /api/v1/billing/cancel
{ reason?: string }
→ { success: true }

// Reactivate subscription
POST /api/v1/billing/reactivate
→ { success: true }

// List invoices
GET /api/v1/billing/invoices
→ { invoices: Invoice[] }

// Get specific invoice
GET /api/v1/billing/invoices/{invoice_id}
→ { invoice }

// Midtrans webhook (public, no auth)
POST /webhooks/midtrans
{ ... midtrans payload }
→ { success: true }
```

---

## 10. Checklist: Payment & Billing DRAFT

- ✅ Subscription plans defined (Free, Starter, Pro, Enterprise)
- ✅ Plan limits defined (projects, decisions, members, rules)
- ✅ Subscription entity defined
- ✅ Invoice entity defined
- ✅ Payment method entity defined
- ✅ Midtrans integration flow defined
- ✅ Webhook handling defined
- ✅ Usage metering defined
- ✅ Plan limit enforcement defined
- ✅ Guard rails defined (7 rules)
- ✅ Database schemas defined
- ✅ API endpoints listed

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-007: Identity Model (for Tenant entity)
- INFRA-DEC-011: Modular Architecture (for payment gateway interface)
- INFRA-LAY2-006: Billing API Contracts (for detailed specs)
