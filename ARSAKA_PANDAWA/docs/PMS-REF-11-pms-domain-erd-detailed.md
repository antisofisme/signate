# REF-11: PMS Domain ERD (Detailed)

This document defines the **detailed entity relationship design for the PMS (Property Management System) domain**. PMS is the operational heart of hotel management, but it is **NOT a financial system**—all financial impacts flow to Accounting through invoices and events.

**Critical Principle**: *PMS generates operational facts (reservations, stays, charges). Accounting consumes these facts and converts them to financial records. PMS never writes to GL or creates financial balances.*

---

## PMS Principles (Locked - Non-Negotiable)

### Principle 1: PMS = Operational Truth, Not Financial Truth
```
PMS records what happened operationally (guest checked in).
Accounting records what it means financially (post AR invoice).
```

### Principle 2: No Balances in PMS
```
PMS does NOT store account balances.
No "Total Owed" field that's the source of truth.
Financial state lives in Accounting only.
```

### Principle 3: All Money = Invoice to Accounting
```
Every charge in PMS → becomes line item in Invoice.
Invoice sent to Accounting → posts GL.
No direct GL posting from PMS.
```

### Principle 4: Night Audit = Control Process, Not GL Posting
```
Night Audit validates daily totals.
Publishes NightAuditClosed event.
Accounting consumes event and posts GL.
```

### Principle 5: Guests Never Access Accounting
```
Guests see their folio (operational charges).
Guests do NOT see GL, invoices, or financial records.
Separation of operational and financial views.
```

---

## Domain 1: Property Master Data

### Property (Hotel/Property)

**Purpose**: Define the hotel property and its settings

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique property identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel owns property |
| `name` | VARCHAR | NOT NULL | Property name |
| `timezone` | VARCHAR | NOT NULL | Time zone (Asia/Jakarta, etc.) |
| `currency` | VARCHAR | NOT NULL | Property currency (IDR, USD) |
| `address` | TEXT | | Physical address |
| `phone` | VARCHAR | | Contact number |
| `email` | VARCHAR | | Contact email |
| `checkin_time` | TIME | | Default check-in time (3 PM) |
| `checkout_time` | TIME | | Default check-out time (11 AM) |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- One tenant can have multiple properties (e.g., hotel group)
- timezone and currency affect all operational data

---

### RoomType (Room Classification)

**Purpose**: Define room categories (Standard, Deluxe, Suite, etc.)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique room type identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `code` | VARCHAR | NOT NULL, UNIQUE (tenant_id) | "STD", "DEL", "STE" |
| `name` | VARCHAR | NOT NULL | "Standard Room", "Deluxe Suite" |
| `capacity` | INT | NOT NULL | Max occupancy (2, 4, 6) |
| `base_rate` | DECIMAL(10,2) | NOT NULL | Default nightly rate |
| `description` | TEXT | | Room amenities, size, etc. |
| `is_active` | BOOLEAN | NOT NULL | Currently available |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**:
- (tenant_id, code) - One code per tenant

---

### Room (Physical Room)

**Purpose**: Individual room inventory

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique room identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `room_type_id` | UUID | FK→RoomType, NOT NULL | Room category |
| `room_number` | VARCHAR | NOT NULL | "101", "502", etc. |
| `floor` | INT | | Floor number |
| `status` | ENUM | NOT NULL | 'available', 'occupied', 'cleaning', 'maintenance', 'blocked' |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last status change |

**Unique Constraint**:
- (tenant_id, room_number) - One number per hotel

**Status Meanings & Transitions**:
| Status | Meaning | Can Sell? | How to Exit |
|--------|---------|-----------|------------|
| `available` | Room is clean, ready to sell | ✅ Yes | Guest checks in → occupied |
| `occupied` | Guest is in room | ❌ No | Guest checks out → cleaning |
| `cleaning` | Housekeeping is cleaning room | ❌ No | Cleaning complete → available |
| `maintenance` | Room being repaired/maintained | ❌ No | Repairs done → available |
| `blocked` | Room blocked by manager (OOO, renovation) | ❌ No | Manager unblocks → available |

**Typical Flow**: available → occupied → cleaning → available

**Examples**:
- `cleaning`: Between checkout (11am) and next check-in (4pm). Housekeeping cleans, marks available when done.
- `maintenance`: AC broken, toilet repair, etc. Until fixed → available
- `blocked`: Owner blocks for personal use, seasonal closure, or major renovation

---

## Domain 2: Reservation

### Reservation (Booking)

**Purpose**: Guest booking (may not become actual stay)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique reservation identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `guest_id` | UUID | FK→Guest, NOT NULL | Who booked |
| `status` | ENUM | NOT NULL | 'reserved', 'cancelled', 'no_show', 'checked_in', 'checked_out' |
| `checkin_date` | DATE | NOT NULL | Expected check-in date |
| `checkout_date` | DATE | NOT NULL | Expected check-out date |
| `room_count` | INT | NOT NULL | Number of rooms |
| `guest_count` | INT | NOT NULL | Total guests |
| `channel` | ENUM | NOT NULL | 'direct', 'ota', 'agent', 'corporate' |
| `reference_number` | VARCHAR | | OTA reference (Booking.com ID, etc.) |
| `special_requests` | TEXT | | Guest notes (high floor, late checkout, etc.) |
| `created_at` | TIMESTAMP | NOT NULL | Booking date |
| `created_by` | UUID | FK→User | Who made booking |

**Relationships**:
```
Reservation 1--1 Stay (when checked in)
Reservation 1--* Stay (if multi-room)
```

**Status Workflow**:
```
RESERVED
  ├─ → CHECKED_IN (guest arrives)
  ├─ → CANCELLED (guest cancels)
  └─ → NO_SHOW (guest doesn't arrive)

CHECKED_IN
  └─ → CHECKED_OUT (guest departs)

CHECKED_OUT
  └─ Complete (folio finalized)

CANCELLED / NO_SHOW
  └─ Complete (no stay occurred)
```

---

## Domain 3: Stay

### Stay (Actual Guest Occupancy)

**Purpose**: Record of actual guest stay (linked to Reservation)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique stay identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `reservation_id` | UUID | FK→Reservation, NOT NULL | Which booking |
| `room_id` | UUID | FK→Room, NOT NULL | Which room assigned |
| `checkin_at` | TIMESTAMP | NOT NULL | Actual check-in time |
| `checkout_at` | TIMESTAMP | | Actual check-out time |
| `nights_stayed` | INT | | Calculated from checkout - checkin |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Relationships**:
```
Stay 1--1 Folio (when checked in)
```

**Notes**:
- Multiple Stays can exist if guest books multiple nights across different rooms
- checkout_at NULL until guest checks out

---

## Domain 4: Guest & Folio

### Guest (Customer/Visitor)

**Purpose**: Guest profile (may or may not have User account)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique guest identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `user_id` | UUID | FK→User | If registered (nullable) |
| `name` | VARCHAR | NOT NULL | Guest full name |
| `email` | VARCHAR | | Email address |
| `phone` | VARCHAR | | Phone number |
| `id_type` | ENUM | | 'passport', 'ktp', 'driver_license' |
| `id_number` | VARCHAR | | ID document number (encrypted) |
| `nationality` | VARCHAR | | Country of origin |
| `address` | TEXT | | Home address |
| `created_at` | TIMESTAMP | NOT NULL | Guest first visit |

**Notes**:
- user_id is nullable (guest without account)
- id_number is encrypted (PII protection, see SEC-02)
- Guests can repeat visits (accumulated history)

---

### Folio (Guest Billing Record)

**Purpose**: Central record of all charges and payments during stay (Core of PMS)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique folio identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `stay_id` | UUID | FK→Stay, NOT NULL | Which stay |
| `guest_id` | UUID | FK→Guest, NOT NULL | Which guest |
| `status` | ENUM | NOT NULL | 'open', 'closed' |
| `opened_at` | TIMESTAMP | NOT NULL | Check-in time |
| `closed_at` | TIMESTAMP | | Check-out time |
| `total_charges` | DECIMAL(15,2) | NOT NULL | Sum of all charges |
| `total_payments` | DECIMAL(15,2) | NOT NULL | Sum of all payments |
| `balance` | DECIMAL(15,2) | | total_charges - total_payments |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Constraints**:
- balance is **calculated**, NOT stored
- balance = total_charges - total_payments

**Relationships**:
```
Folio 1--* Charge
Folio 1--* Payment
Folio 1--1 Invoice (when closed)
```

**Notes**:
- Folio is THE central operational record for billing
- All charges post to folio
- All payments allocated to folio
- When folio closed → creates Invoice for Accounting

---

## Domain 5: Charges (Source of Revenue)

### Charge (Line Item on Folio)

**Purpose**: Individual charge against folio (room charge, F&B, service, etc.)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique charge identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `folio_id` | UUID | FK→Folio, NOT NULL | Which folio |
| `source` | ENUM | NOT NULL | 'room', 'pos', 'service', 'adjustment', 'fee' |
| `description` | VARCHAR | NOT NULL | What charge is for ("Room 3 nights", "Restaurant", etc.) |
| `amount` | DECIMAL(12,2) | NOT NULL | Charge amount |
| `tax_percent` | DECIMAL(5,2) | | Tax rate (if applicable) |
| `tax_amount` | DECIMAL(12,2) | | Calculated tax |
| `posted_at` | TIMESTAMP | NOT NULL | When charged |
| `is_posted` | BOOLEAN | NOT NULL | Has charge been finalized |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Constraints**:
- Cannot edit charge after NightAudit (is_posted = true)
- tax_amount = amount × (tax_percent / 100)

**Source Types**:
- room: Room charge (nightly rate)
- pos: Point of Sale (restaurant, bar, gifts)
- service: Hotel services (laundry, spa, etc.)
- adjustment: Manual adjustment (discount, complimentary)
- fee: Hotel fees (resort fee, parking, etc.)

**Notes**:
- Charge is operational proof of what guest owes
- Immutable once posted (NightAudit locks daily charges)
- All charges eventually become invoice line items

---

### Payment (Money Received)

**Purpose**: Payments allocated to folio

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique payment record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `folio_id` | UUID | FK→Folio, NOT NULL | Which folio |
| `amount` | DECIMAL(12,2) | NOT NULL | Payment amount |
| `method` | ENUM | NOT NULL | 'cash', 'card', 'transfer', 'check', 'credit' |
| `reference` | VARCHAR | | Payment reference (card auth #, transfer #) |
| `paid_at` | TIMESTAMP | NOT NULL | When payment received |
| `posted_at` | TIMESTAMP | | When posted to folio |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Relationships**:
```
Payment N--1 Folio
```

---

## Domain 6: Invoice Integration

### PMSInvoiceLink (Bridge to Accounting)

**Purpose**: Link between PMS folio and Accounting invoice

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique link record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `folio_id` | UUID | FK→Folio, NOT NULL, UNIQUE | Which folio |
| `invoice_id` | UUID | FK→Accounting.Invoice | Which accounting invoice |
| `created_at` | TIMESTAMP | NOT NULL | Link creation |

**Unique Constraint**:
- (tenant_id, folio_id) - One invoice per folio

**Notes**:
- PMS creates folio and charges
- When folio closed, PMS requests Invoice creation
- Accounting creates Invoice, posts GL
- PMSInvoiceLink records the relationship
- PMS never modifies invoice (read-only reference)

---

## Domain 7: Night Audit

### NightAudit (Daily Reconciliation Process)

**Purpose**: Daily control process that locks charges and triggers GL posting

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique audit record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which hotel |
| `audit_date` | DATE | NOT NULL, UNIQUE (tenant_id) | Which date |
| `status` | ENUM | NOT NULL | 'open', 'closed' |
| `total_room_revenue` | DECIMAL(15,2) | | Room sales for day |
| `total_other_revenue` | DECIMAL(15,2) | | Non-room revenue |
| `total_charges` | DECIMAL(15,2) | | Total charges posted |
| `total_payments` | DECIMAL(15,2) | | Total payments received |
| `occupancy_count` | INT | | Rooms occupied |
| `occupancy_percent` | DECIMAL(5,2) | | Occupancy percentage |
| `closed_at` | TIMESTAMP | | When audit closed |
| `closed_by` | UUID | FK→User | Who closed audit |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**:
- (tenant_id, audit_date) - One audit per day

**Function**:
1. Summarize daily charges and payments
2. Validate occupancy and revenue totals
3. Lock all charges for the day (is_posted = true)
4. Publish NightAuditClosed event
5. Accounting consumes event and posts GL

**Notes**:
- Audit does NOT post GL directly
- GL posting happens in Accounting (async, event-driven)
- Audit is control checkpoint, not financial posting

---

## Domain 8: Event Emission

Events published by PMS for other modules to consume:

| Event | When | Consumers |
|-------|------|-----------|
| `PMS.Reservation.Created.v1` | New booking made | Notification, Reporting |
| `PMS.Guest.CheckedIn.v1` | Guest checks in | Folio activation, Housekeeping |
| `PMS.Charge.Posted.v1` | Charge added to folio | Audit trail, Reporting |
| `PMS.Charge.Reversed.v1` | Charge removed | Audit trail |
| `PMS.NightAudit.Closed.v1` | Daily close completed | GL posting (Accounting), Reporting |
| `PMS.Guest.CheckedOut.v1` | Guest checks out, folio closes | Invoice creation (Accounting), Notification |
| `PMS.Folio.Closed.v1` | Folio finalized | Accounting, Reporting |

---

## Domain 9: Boundary Rules (Strict)

### ❌ Hard Rules (Cannot Be Broken)

| Rule | Why | Consequence |
|------|-----|-------------|
| **PMS cannot write JournalLine** | Maintains separation of concerns | GL integrity compromised |
| **PMS cannot modify Invoice** | Only Accounting can change financial records | Data inconsistency |
| **Charges locked after NightAudit** | Prevents post-facto modifications | Audit trail gaps |
| **Guest cannot access Accounting** | Operational vs financial separation | Data security breach |
| **Folio balance not authoritative** | GL balance is only truth | Financial inconsistency |

### ✅ Allowed Operations

| Operation | How |
|-----------|-----|
| **Add charge to open folio** | Create Charge record |
| **Post payment** | Create Payment, update folio total |
| **Correct folio error** | Create reversing Charge (before audit) |
| **Extend stay** | Update Stay checkout_date |
| **Request invoice** | Publish event when folio closed |

---

## Data Isolation & Tenant Rules

All PMS data tenant-scoped:

```sql
-- All queries must include tenant_id:

SELECT * FROM folios
WHERE tenant_id = $1  -- MANDATORY
  AND opened_at >= $2;

SELECT * FROM charges
WHERE tenant_id = $1  -- MANDATORY
  AND posted_at >= $2;
```

---

## Compliance Checklist

When designing PMS features:

- [ ] All entities have tenant_id
- [ ] No direct GL posting from PMS
- [ ] Charges immutable after audit
- [ ] NightAudit publishes event
- [ ] Folio closed → Invoice requested
- [ ] Guest cannot see Invoice
- [ ] Guest cannot see GL
- [ ] All charges traceable to folio
- [ ] Payment allocated to folio
- [ ] Tenant isolation enforced
- [ ] Tests verify operational integrity

---

## Related Documents

- **REF-10**: Accounting Domain ERD (Detailed) — Accounting entities that consume PMS data
- **REF-08**: Entity Relationship Model (Core) — Foundation model
- **SPEC-09**: PMS Core Process & Workflow — Business process for PMS operations
- **STD-19**: Event Contract Standard — Events published by PMS
- **ARCH-12**: Read Model & CQRS Pattern — Read models for PMS reporting
