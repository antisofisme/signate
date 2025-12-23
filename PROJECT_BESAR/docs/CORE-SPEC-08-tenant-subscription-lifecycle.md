# SPEC-08: Tenant & Subscription Lifecycle

This document specifies the **business process and state machine** for tenant and subscription lifecycle in PROJECT_BESAR. It defines how tenants are created, activated, managed, modified, suspended, and terminated.

**Prerequisite:** SPEC-07 (Use Cases) — understand what actors do before understanding how system orchestrates it.

---

## Key Principles

1. **Tenant is Subscription-Dependent**
   - No active tenant without an active subscription
   - Subscription determines which modules/apps are enabled
   - Tenant cannot exist in suspended state indefinitely

2. **Owner Role = Subscription Result**
   - First user to successfully pay for subscription becomes automatic Owner
   - Owner role cannot be assigned before subscription is paid
   - Subscription payment is gate to tenant activation

3. **No Data Loss on Suspend**
   - Suspension blocks access but preserves all data
   - Suspended tenant can be reactivated within grace period
   - Data deletion requires explicit owner request

4. **All Changes Audited**
   - Every state change recorded in audit log
   - Timestamp, reason, and actor recorded
   - Enables forensics and compliance

5. **Event-Driven Architecture**
   - Each state change generates event (TenantActivated, SubscriptionExpired, etc.)
   - Events trigger downstream processes (notifications, billing, provisioning)
   - No synchronous blocking calls between services

---

## Tenant States

```
┌─────────────┐
│   DRAFT     │  Tenant created but not yet activated
└──────┬──────┘
       │ (Payment received)
       ▼
┌─────────────┐
│   ACTIVE    │  Tenant operational, subscription valid
└──────┬──────┘
       │ (Payment failed / Trial expired / Owner suspended)
       ▼
┌─────────────┐
│  SUSPENDED  │  Access blocked, data preserved
└──────┬──────┘
       │ (Payment received / Reactivation approved)
       ▼
    ACTIVE
       │ (Owner requests deletion / Subscription cancelled)
       ▼
┌─────────────┐
│  DELETED    │  Data archived/purged per retention policy
└─────────────┘
```

---

## Subscription States

```
┌─────────────┐
│   DRAFT     │  Tenant created, payment not initiated
└──────┬──────┘
       │ (Payment initiated)
       ▼
┌─────────────────┐
│ AWAITING_PAYMENT│  Payment processing
└──────┬──────────┘
       │ (Payment succeeded)
       ▼
┌─────────────┐
│   ACTIVE    │  Subscription valid, tenant can operate
└──────┬──────┘
       │ (Trial expiration approaching / Manual upgrade)
       ▼
┌─────────────────┐
│ AWAITING_RENEWAL│  Renewal payment needed
└──────┬──────────┘
       │ (Renewal payment received)
       ▼
    ACTIVE
       │ (Renewal payment failed)
       ▼
┌──────────────┐
│ GRACE_PERIOD │  Payment overdue, grace period active
└──────┬───────┘
       │ (Payment received)
       ▼
    ACTIVE
       │ (Grace period expired)
       ▼
┌─────────────┐
│ EXPIRED     │  Subscription ended
└─────────────┘
```

---

## Main Flow: Create Tenant & Subscribe

### Phase 1: User Registration

**Trigger**: New user accesses platform

**Steps**:
1. User fills registration form (email, password, name, company)
2. System validates email format and uniqueness
3. System creates **global Identity** record
4. System sends verification email
5. User clicks verification link
6. System marks identity as verified

**Output**: Identity created (no role, no tenant)

**Error Handling**:
- Email already registered → direct to login
- Email verification fails → resend link option
- Email verification timeout (24h) → require re-registration

---

### Phase 2: Select Application & Package

**Trigger**: Verified user accesses platform dashboard

**Steps**:
1. System displays available applications/modules (PMS, Accounting, Inventory, etc.)
2. System displays pricing packages for each module
3. User selects modules and package tier
4. System calculates total monthly/yearly cost
5. User reviews and confirms selection

**Pricing Options**:
- Basic (essential features only)
- Professional (standard features)
- Enterprise (advanced features + support)
- Custom (bundled modules)

**Output**: Selected modules and pricing stored in draft subscription

**Example**:
```
Selection:
  - PMS (Professional tier): $99/month
  - Accounting (Professional tier): $49/month
  - Inventory (Basic tier): $29/month
Total: $177/month = $2,124/year
```

---

### Phase 3: Create Tenant & Subscription (Draft)

**Trigger**: User confirms package selection

**Steps**:
1. System creates **Tenant** record (draft status)
   - tenant_id (UUID)
   - created_at (timestamp)
   - created_by (user_id)
   - status: DRAFT
   - name: derived from user company/org input
   - region: selected by user (affects pricing, data residency)

2. System creates **Subscription** record (draft status)
   - subscription_id (UUID)
   - tenant_id (reference)
   - modules: [PMS, Accounting, Inventory]
   - billing_period: monthly or yearly
   - price_total: calculated
   - status: DRAFT
   - valid_from: null (set after payment)
   - valid_until: null

3. System creates **TenantApp** records (one per selected module)
   - tenant_id, app_code (e.g., 'PMS')
   - status: DRAFT (will be ACTIVE after payment)
   - subscribed_at: null

**Output**: Tenant and Subscription in DRAFT state

**Database entries**:
```
Tenant {
  id: 'org-12345',
  status: 'DRAFT',
  created_at: '2025-12-21T10:00:00Z'
}

Subscription {
  id: 'sub-67890',
  tenant_id: 'org-12345',
  status: 'DRAFT',
  modules: ['PMS', 'Accounting', 'Inventory']
}

TenantApp {
  tenant_id: 'org-12345',
  app_code: 'PMS',
  status: 'DRAFT'
}
```

---

### Phase 4: Payment Processing

**Trigger**: User proceeds to payment

**Steps**:
1. System updates Subscription status to **AWAITING_PAYMENT**
2. System redirects user to Payment Gateway (Stripe, PayPal, etc.)
3. User enters payment details
4. Payment Gateway processes payment
5. Payment Gateway returns result to system (webhook)

**Decision Gateway: Payment Successful?**

**Path A: Payment FAILED**
- Subscription status → FAILED
- Tenant status → stays DRAFT
- User can retry payment or select different package
- Tenant remains in DRAFT (no data loss)
- Draft data expires after 30 days

**Path B: Payment SUCCEEDED**
- Payment Gateway confirms transaction
- System receives payment confirmation
- Continue to Phase 5 (Activation)

---

### Phase 5: Tenant Activation

**Trigger**: Payment confirmed

**Steps**:
1. System updates **Subscription** status → ACTIVE
   - valid_from: now
   - valid_until: now + 1 month (or 1 year for annual)

2. System updates **Tenant** status → ACTIVE

3. System creates **Membership** (Owner role)
   - user_id: the user who registered
   - tenant_id: the new tenant
   - role: OWNER
   - created_at: now

4. System activates all **TenantApp** records
   - status: ACTIVE for all selected modules
   - subscribed_at: now

5. System generates event: `TenantActivated`
   ```json
   {
     "event_type": "tenant.activated",
     "tenant_id": "org-12345",
     "subscription_id": "sub-67890",
     "modules": ["PMS", "Accounting", "Inventory"],
     "billing_period": "monthly",
     "valid_until": "2026-01-21T10:00:00Z",
     "timestamp": "2025-12-21T10:05:00Z"
   }
   ```

6. System sends confirmation email to Owner

**Output**: Tenant ACTIVE, Owner role created, modules enabled

---

### Phase 6: Initial Configuration

**Trigger**: Owner first login after activation

**Steps**:
1. Owner logs into tenant dashboard
2. System detects first login and shows onboarding flow
3. Owner fills basic tenant info:
   - Legal company name
   - Address, phone, email
   - Industry/business type
   - Currency and timezone
   - Operational hours

4. Owner configures initial module settings:
   - **PMS**: Room types, rates, check-in time
   - **Accounting**: Chart of accounts, tax settings
   - **Inventory**: Stock locations, units of measure

5. Owner (optional) invites staff:
   - Defines roles (Admin, Staff)
   - Shares invitation links
   - Staff accepts and joins

6. System marks onboarding as complete

**Output**: Tenant configured and ready for operations

---

## Alternate Flows

### Flow A: Trial Subscription

**Scenario**: User selects free trial instead of paid subscription

**Variation on Phase 3-5**:
1. System creates Tenant and Subscription (same as above)
2. For trial, subscription status → ACTIVE (without payment)
3. valid_until: now + 14 days (trial period)
4. No payment processed

**Trigger: Trial Expiration**:
1. System detects valid_until < now
2. System updates Subscription status → AWAITING_RENEWAL
3. System sends email to Owner: "Your trial expires in 3 days"
4. Owner chooses to upgrade (pay) or trial ends

**Decision: Upgrade?**
- YES → Payment flow (same as Phase 4), tenant stays active after payment
- NO → Subscription status → EXPIRED, Tenant status → SUSPENDED

---

### Flow B: Modify Subscription (Add/Remove Modules)

**Trigger**: Owner clicks "Upgrade/Modify Subscription"

**Scenario 1: Add Module**
1. Owner selects additional module (e.g., add "POS" to existing PMS + Accounting)
2. System calculates price difference (prorated for current billing period)
3. System displays amount due immediately
4. Owner confirms
5. System charges payment gateway (delta amount)
6. If payment succeeds:
   - New TenantApp record created with status ACTIVE
   - Event generated: `ModuleAdded`
7. If payment fails:
   - Subscription unchanged, User notified
   - Can retry

**Scenario 2: Remove Module**
1. Owner selects module to remove
2. System calculates credit (prorated refund)
3. System shows refund amount
4. Owner confirms removal
5. TenantApp status updated → DEACTIVATED
6. Event generated: `ModuleRemoved`
7. Refund processed to original payment method

**Scenario 3: Downgrade Tier**
1. Owner selects lower tier (e.g., Professional → Basic)
2. System calculates credit
3. Owner confirms
4. Credit applied to future invoices or refunded
5. Subscription updated with new tier/price
6. Event generated: `SubscriptionDowngraded`

---

### Flow C: Renewal (Billing Period Expires)

**Trigger**: Subscription valid_until date reached

**30 days before expiration**:
1. System sends reminder email to Owner
2. Billing email address receives invoice preview

**3 days before expiration**:
1. System sends final reminder
2. Optional: Owner can upgrade/downgrade before renewal

**On expiration date**:
1. System attempts automatic renewal charge (stored payment method)
2. Subscription status → AWAITING_RENEWAL

**Decision: Renewal Successful?**

**Path A: Payment SUCCEEDED**
- Subscription status → ACTIVE
- valid_until: now + 1 month
- Event: `SubscriptionRenewed`

**Path B: Payment FAILED**
- Subscription status → GRACE_PERIOD
- Tenant status → stays ACTIVE (but with warning)
- Owner receives payment failure notice
- Retry scheduled for 3 days later

**If Grace Period Expires** (payment not received):
- Subscription status → EXPIRED
- Tenant status → SUSPENDED
- Modules disabled
- Event: `SubscriptionExpired`

---

### Flow D: Payment Failure & Recovery

**Trigger**: Automatic payment fails (expired card, insufficient funds, etc.)

**Immediate**:
1. System marks Subscription status → GRACE_PERIOD
2. Tenant stays ACTIVE (users can still operate)
3. Email sent to Owner: "Payment failed, update payment method"
4. Email sent to billing contact

**Retry Schedule**:
- 1st retry: 2 days later
- 2nd retry: 5 days later
- 3rd retry: 10 days later

**If Payment Succeeds on Retry**:
- Subscription status → ACTIVE
- valid_until extended by 1 period
- Event: `PaymentRecovered`

**If All Retries Fail** (after 10 days):
- Subscription status → EXPIRED
- Tenant status → SUSPENDED
- Modules disabled (staff cannot access)
- Event: `TenantSuspended`

---

### Flow E: Owner Requests Suspension

**Trigger**: Owner clicks "Suspend Tenant" in settings

**Scenario**: Owner wants to temporarily stop operations

**Steps**:
1. System shows confirmation dialog: "Data will be preserved, cannot access for 30 days"
2. Owner confirms reason (vacation, renovation, etc.)
3. System updates Tenant status → SUSPENDED
4. Subscription still ACTIVE (billing continues)
5. All modules disabled
6. Event: `TenantSuspendedByOwner`

**Reactivation**:
1. Owner clicks "Reactivate Tenant"
2. System updates Tenant status → ACTIVE
3. Modules re-enabled immediately
4. Event: `TenantReactivated`

---

### Flow F: Owner Requests Deletion

**Trigger**: Owner clicks "Delete Tenant" in settings

**Prerequisites**:
- Subscription not in grace period
- No outstanding invoices (or balance cleared)

**Steps**:
1. System shows warning: "This is permanent. Data will be deleted after 30-day grace period"
2. Owner enters password to confirm
3. System sets Tenant status → PENDING_DELETION
4. Subscription status → CANCELLED
5. Modules immediately disabled
6. Grace period: 30 days (owner can restore)
7. Event: `TenantDeletionRequested`

**During Grace Period**:
- Owner can click "Restore" to cancel deletion
- Tenant status → ACTIVE, modules re-enabled

**After Grace Period**:
1. System marks Tenant status → DELETED
2. Data deleted per retention policy:
   - Transactional data: hard delete
   - Financial ledger: archived to cold storage (7-year retention for audit)
   - PII (guest data): secure purge (GDPR compliance)
3. Subscriptions archived (for accounting)
4. Event: `TenantPermanentlyDeleted`

---

## Event-Driven State Changes

All state changes generate events published to event bus:

### Core Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `tenant.created` | Tenant draft created | tenant_id, created_by |
| `tenant.activated` | Payment received, tenant activated | tenant_id, modules, valid_until |
| `subscription.renewed` | Renewal payment received | subscription_id, new_valid_until |
| `subscription.expired` | valid_until reached, payment failed | subscription_id, tenant_id |
| `tenant.suspended` | Payment failed after grace period | tenant_id, reason |
| `tenant.reactivated` | Payment received during suspension | tenant_id |
| `module.added` | Owner adds module | tenant_id, module_code |
| `module.removed` | Owner removes module | tenant_id, module_code |
| `tenant.deletion_requested` | Owner initiates deletion | tenant_id, grace_period_until |
| `tenant.permanently_deleted` | Grace period expired | tenant_id |

**Example Event**:
```json
{
  "event_id": "evt-uuid-98765",
  "event_type": "subscription.renewed",
  "version": 1,
  "timestamp": "2025-12-21T10:00:00Z",
  "tenant_id": "org-12345",
  "subscription_id": "sub-67890",
  "data": {
    "previous_valid_until": "2026-01-21T10:00:00Z",
    "new_valid_until": "2026-02-21T10:00:00Z",
    "amount_charged": 177.00,
    "currency": "USD",
    "billing_period": "monthly"
  },
  "signature": "hmac-sha256-hash"
}
```

**Event Consumers**:
- Billing service: update invoice records
- Notification service: send renewal confirmation email
- Logging service: audit trail
- Analytics: track renewal rate metrics

---

## Important Invariants

### No Tenant Without Subscription
```
INVARIANT: Tenant.status = ACTIVE → Subscription.status = ACTIVE
```
- If subscription expires, tenant must be suspended or deleted
- Tenant cannot operate without valid subscription

### Owner = Subscription Payer
```
INVARIANT: If Membership.role = OWNER in Tenant T
           → Subscription for T was paid by User (identity)
```
- Owner role is never assigned before subscription payment
- Owner must exist (tenant needs owner)
- Owner cannot be changed without explicit approval

### No Data Loss on Suspend
```
INVARIANT: Tenant.status = SUSPENDED → all data preserved
```
- Suspension only blocks access
- Data accessible after reactivation within grace period
- No automatic deletion during suspension

### Audit Trail for All Changes
```
INVARIANT: Every state change logged with timestamp, actor, reason
```
- Enables forensics for disputes
- Compliance with SLA/SLO
- Historical tracking

---

## Timing & Grace Periods

| Event | Grace Period | Action |
|-------|--------------|--------|
| Payment failed | 10 days (3 retries) | Retry automatic payment, then suspend |
| Trial expired | N/A | Requires immediate action (pay or let expire) |
| Suspension | Immediate | Access blocked same day |
| Deletion request | 30 days | Owner can restore anytime during period |
| Data purge | 30 days after deletion | Hard delete PII, archive financial |

---

## Compliance & Data Handling

### GDPR Compliance
- Owner can request data export anytime
- Owner can request deletion (soft delete → 30-day grace → hard delete)
- Audit trail of all data access
- Right to erasure honored within 30 days

### Financial Record Retention
- Subscription records archived indefinitely (for audit)
- Ledger entries kept 7 years (regulatory requirement)
- Supporting documents (invoices) kept 7 years
- PII deleted after retention period

### SLA Compliance
- Suspension happens same day (automated)
- Reactivation within 1 minute of payment (automated)
- Support response to deletion request within 24 hours

---

## Related Documents

- **SPEC-07**: Use Cases — what actors do (Owner creates tenant, upgrades subscription, etc.)
- **SPEC-09**: API Boundaries — API endpoints for subscription management
- **BPMN #02**: Detailed swim lanes for tenant/subscription flows
- **ERD #14**: Core entity relationships (Tenant, Subscription, Membership, TenantApp)
- **EVENT MODEL**: Event schema and publishing mechanism

---

## Implementation Checklist

- [ ] State machine implemented with transitions validated
- [ ] All events published to event bus on state change
- [ ] Payment gateway integration tested (success and failure cases)
- [ ] Automatic renewal job scheduled and tested
- [ ] Grace period timers implemented and tested
- [ ] Deletion workflow with 30-day restore tested
- [ ] Email notifications sent at key points
- [ ] Audit logging captures all state changes
- [ ] GDPR compliance verified (data export, deletion)
- [ ] SLA timings met (suspension < 1 day, reactivation < 1 min)
