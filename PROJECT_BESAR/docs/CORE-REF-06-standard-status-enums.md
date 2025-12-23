# REF-06: Standard Status Enums Reference

**Status**: ✅ Approved (2025-12-24)
**Purpose**: Authoritative definitions of all standard status enums used throughout PROJECT_BESAR

---

## Overview

All domain entities use standard status enums defined below. This ensures:
- Consistency across modules
- Simplified status comparisons and queries
- Unified UI display (no case conversion needed)
- Single source of truth for valid statuses

**Format**: ALL enum values in UPPERCASE (database standard)

---

## 1. Reservation Statuses (PMS)

**Entity**: Reservation
**Valid Transitions**: PENDING → CONFIRMED → CHECKED_IN → CHECKED_OUT or CANCELLED

```typescript
enum ReservationStatus {
  PENDING = "PENDING",            // Created, awaiting confirmation
  CONFIRMED = "CONFIRMED",        // Guest confirmed arrival
  CHECKED_IN = "CHECKED_IN",      // Guest in property
  CHECKED_OUT = "CHECKED_OUT",    // Guest departed, folio closed
  CANCELLED = "CANCELLED",        // Reservation cancelled (no show)
  NO_SHOW = "NO_SHOW",           // Guest didn't arrive by deadline
  DISPUTED = "DISPUTED",          // Under dispute (charge/payment issue)
}
```

---

## 2. Invoice Statuses (Accounting)

**Entity**: Invoice
**Valid Transitions**: DRAFT → FINALIZED → POSTED → PAID or OVERDUE

```typescript
enum InvoiceStatus {
  DRAFT = "DRAFT",                // Created, not finalized
  FINALIZED = "FINALIZED",        // Ready to post (amount locked)
  POSTED = "POSTED",              // Posted to GL, immutable
  PARTIALLY_PAID = "PARTIALLY_PAID",
  PAID = "PAID",                  // Fully settled
  OVERDUE = "OVERDUE",            // Past due date
  CANCELLED = "CANCELLED",        // Voided (soft delete)
  REVERSED = "REVERSED",          // Reversal posted
}
```

---

## 3. Purchase Order Statuses (Procurement)

**Entity**: PurchaseOrder
**Valid Transitions**: DRAFT → ISSUED → ACCEPTED → COMPLETED or REJECTED

```typescript
enum PurchaseOrderStatus {
  DRAFT = "DRAFT",                // Created, not sent
  ISSUED = "ISSUED",              // Sent to supplier
  ACCEPTED = "ACCEPTED",          // Supplier confirmed
  RECEIVED = "RECEIVED",          // Goods received
  COMPLETED = "COMPLETED",        // Invoice matched and paid
  REJECTED = "REJECTED",          // Supplier rejected
  CANCELLED = "CANCELLED",        // Buyer cancelled
}
```

---

## 4. Payment Statuses (AR/AP)

**Entity**: Payment
**Valid Transitions**: PENDING → PROCESSED → CLEARED or FAILED

```typescript
enum PaymentStatus {
  PENDING = "PENDING",            // Initiated, not yet processed
  PROCESSED = "PROCESSED",        // Bank accepted
  CLEARED = "CLEARED",            // Settlement complete
  FAILED = "FAILED",              // Payment declined
  REVERSED = "REVERSED",          // Reversal processed
  DISPUTED = "DISPUTED",          // Under dispute
}
```

---

## 5. Journal Entry Statuses (GL)

**Entity**: JournalEntry
**Valid Transitions**: DRAFT → POSTED or REVERSED (only POSTED is immutable)

```typescript
enum JournalEntryStatus {
  DRAFT = "DRAFT",                // Prepared, not validated
  POSTED = "POSTED",              // Posted to GL (immutable)
  REVERSED = "REVERSED",          // Reversal entry posted
  VOIDED = "VOIDED",              // Cancelled before posting
}
```

---

## 6. Workflow Approval Statuses

**Entity**: WorkflowInstance
**Valid Transitions**: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED → ARCHIVED

```typescript
enum ApprovalStatus {
  DRAFT = "DRAFT",                // Not submitted yet
  PENDING_APPROVAL = "PENDING_APPROVAL",    // Awaiting decision
  APPROVED = "APPROVED",          // Approved by authority
  REJECTED = "REJECTED",          // Rejected by authority
  PENDING_INFO = "PENDING_INFO",  // Requesting more info
  ARCHIVED = "ARCHIVED",          // Auto-expired or superseded
}
```

---

## 7. Room Statuses (PMS)

**Entity**: Room
**Valid Transitions**: AVAILABLE → OCCUPIED/CLEANING/MAINTENANCE/BLOCKED → AVAILABLE

```typescript
enum RoomStatus {
  AVAILABLE = "AVAILABLE",        // Ready for guests
  OCCUPIED = "OCCUPIED",          // Guest in room
  CLEANING = "CLEANING",          // Housekeeping cleaning
  MAINTENANCE = "MAINTENANCE",    // Under repair
  BLOCKED = "BLOCKED",            // Manager blocked (OOO, reno)
  OUT_OF_SERVICE = "OUT_OF_SERVICE",  // Permanently unavailable
}
```

---

## 8. Subscription Statuses (Billing)

**Entity**: Subscription
**Valid Transitions**: TRIAL → ACTIVE → SUSPENDED/CANCELLED

```typescript
enum SubscriptionStatus {
  TRIAL = "TRIAL",                // Free trial period
  ACTIVE = "ACTIVE",              // Paid, in use
  SUSPENDED = "SUSPENDED",        // Suspended due to non-payment
  CANCELLED = "CANCELLED",        // Ended by customer/admin
  EXPIRED = "EXPIRED",            // Trial expired
}
```

---

## 9. Supplier/Vendor Statuses

**Entity**: Supplier
**Valid Transitions**: ACTIVE → BLOCKED → ACTIVE or ARCHIVED

```typescript
enum SupplierStatus {
  ACTIVE = "ACTIVE",              // Can transact
  BLOCKED = "BLOCKED",            // Temporarily suspended
  ARCHIVED = "ARCHIVED",          // Inactive, historical only
  PENDING_APPROVAL = "PENDING_APPROVAL",   // Awaiting onboarding approval
}
```

---

## 10. Document Statuses (Generic)

**Entity**: Document, Report, etc.
**Valid Transitions**: DRAFT → FINAL → ARCHIVED

```typescript
enum DocumentStatus {
  DRAFT = "DRAFT",                // In progress
  FINAL = "FINAL",                // Locked and immutable
  ARCHIVED = "ARCHIVED",          // Historical, read-only
  SUPERSEDED = "SUPERSEDED",      // Replaced by newer version
}
```

---

## Database Implementation

```sql
-- Create ENUM types for PostgreSQL
CREATE TYPE reservation_status AS ENUM (
  'PENDING', 'CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED', 'NO_SHOW', 'DISPUTED'
);

CREATE TYPE invoice_status AS ENUM (
  'DRAFT', 'FINALIZED', 'POSTED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'CANCELLED', 'REVERSED'
);

CREATE TYPE approval_status AS ENUM (
  'DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PENDING_INFO', 'ARCHIVED'
);

-- Column definition
ALTER TABLE reservations ADD COLUMN status reservation_status NOT NULL DEFAULT 'PENDING';
ALTER TABLE invoices ADD COLUMN status invoice_status NOT NULL DEFAULT 'DRAFT';
ALTER TABLE workflow_instances ADD COLUMN status approval_status NOT NULL DEFAULT 'DRAFT';

-- Indexes for status queries
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
```

---

## Usage Rules

### In Code

```typescript
// ✅ CORRECT - Use constants
if (reservation.status === ReservationStatus.CHECKED_IN) { ... }

// ❌ WRONG - Hardcoded strings
if (reservation.status === 'checked in') { ... }
if (reservation.status === 'CheckedIn') { ... }
```

### In Queries

```sql
-- ✅ CORRECT - All UPPERCASE
SELECT * FROM invoices WHERE status = 'POSTED';

-- ❌ WRONG - Mixed case
SELECT * FROM invoices WHERE status = 'Posted';
SELECT * FROM invoices WHERE status = 'posted';
```

### In Events

```json
{
  "event_type": "Reservation.StatusChanged.v1",
  "payload": {
    "reservation_id": "res-123",
    "new_status": "CHECKED_IN",    // ← UPPERCASE
    "previous_status": "CONFIRMED"  // ← UPPERCASE
  }
}
```

---

## State Machine Validation

Before saving any status change, validate against allowed transitions:

```typescript
const VALID_TRANSITIONS: Record<string, ReservationStatus[]> = {
  PENDING: [ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED],
  CONFIRMED: [ReservationStatus.CHECKED_IN, ReservationStatus.CANCELLED],
  CHECKED_IN: [ReservationStatus.CHECKED_OUT],
  CHECKED_OUT: [],  // Terminal
  CANCELLED: [],    // Terminal
};

function validateStatusTransition(
  currentStatus: ReservationStatus,
  newStatus: ReservationStatus
): boolean {
  const allowed = VALID_TRANSITIONS[currentStatus] || [];
  return allowed.includes(newStatus);
}
```

---

## Cross-Reference by Module

| Module | Primary Statuses | Reference |
|--------|------------------|-----------|
| PMS | ReservationStatus, RoomStatus | REF-11 |
| Accounting | InvoiceStatus, JournalEntryStatus | REF-10 |
| Procurement | PurchaseOrderStatus | SPEC-11 |
| Approval | ApprovalStatus | SPEC-09 |
| Billing | SubscriptionStatus | BIZ-08 |
| AR/AP | PaymentStatus, InvoiceStatus | SPEC-10 |

---

## Related Documents

- CORE-SPEC-09: Workflow Engine (approval status machine)
- ACC-REF-10: Accounting Domain ERD (invoice/journal statuses)
- PMS-REF-11: PMS Domain ERD (reservation/room statuses)
- MULTI-SPEC-11: Cross-Tenant Flow (purchase order statuses)
