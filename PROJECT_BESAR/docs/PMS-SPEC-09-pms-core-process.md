# SPEC-09: PMS Core Process & Workflow

This document specifies the **core operational workflow** of the PMS (Property Management System) module in PROJECT_BESAR. It defines the business process for guest reservations, check-in/check-out, in-house operations, and daily closing (night audit).

**Prerequisite:** SPEC-07 (Use Cases) — understand Staff and Guest roles before understanding PMS workflow.

---

## Key Principles

1. **Folio is Center of Billing**
   - Every guest stay = one folio (bill)
   - All charges accumulate in folio
   - Folio opened at check-in, closed at check-out

2. **Check-in Opens, Check-out Closes**
   - No transactions without open folio
   - Check-in is gate to folio creation
   - Check-out is final settlement

3. **Night Audit Locks the Day**
   - End-of-day process finalizes all transactions
   - No backdating charges after night audit
   - Immutable record for accounting

4. **Accounting Integration**
   - PMS generates events (reservations, charges, payments)
   - Accounting system consumes events asynchronously
   - Double-entry ledger entries created from PMS events

5. **Audit Trail Required**
   - Every state change logged
   - User who initiated change recorded
   - Timestamp, reason, and amount captured

---

## Reservation States

```
┌──────────────┐
│  CREATED     │  Reservation just created (online/offline)
└──────┬───────┘
       │ (Guest arrives and checks in)
       ▼
┌──────────────┐
│  CHECKED-IN  │  Guest is in hotel, folio is open
└──────┬───────┘
       │ (Guest departs, folio closed and paid)
       ▼
┌──────────────┐
│  CHECKED-OUT │  Stay completed, folio settled
└──────┬───────┘
       │ (Manual cancellation or override)
       ▼
┌──────────────┐
│  CANCELLED   │  Reservation void
└──────────────┘

Alternative paths from CREATED:
       │ (Guest doesn't arrive by deadline)
       ▼
┌──────────────┐
│  NO-SHOW     │  Guest didn't check in, no-show policy applied
└──────────────┘
```

---

## Folio States

```
┌──────────────┐
│   CLOSED     │  Folio doesn't exist yet
└──────┬───────┘
       │ (Check-in happens)
       ▼
┌──────────────┐
│   OPEN       │  Folio created, charges accumulating
└──────┬───────┘
       │ (Check-out or settlement)
       ▼
┌──────────────┐
│  SETTLED     │  Payment received, folio closed
└──────────────┘
```

---

## Main Flow: Complete Stay Cycle

### Step 1: Reservation

**Trigger**: Guest makes booking (online portal, phone, OTA, walk-in)

**Actors**: Guest (or Staff on behalf of guest), System

**Steps**:
1. Guest selects:
   - Check-in date and time
   - Check-out date and time
   - Room type preference (single, double, suite, etc.)
   - Number of guests
   - Special requests (high floor, quiet room, etc.)

2. System verifies:
   - Date range is valid (check-out > check-in)
   - Rooms available for requested dates
   - Guest identity (if registered member or corporate)

3. System calculates:
   - Room rate per night (based on rate plan, season, demand)
   - Total room charges
   - Taxes and fees
   - Total estimated amount

4. System displays confirmation:
   - Reservation number
   - Guest name
   - Room assignment (if assigned, or "to be assigned")
   - Check-in time (e.g., 3 PM)
   - Check-out time (e.g., 11 AM)
   - Total amount

5. System creates **Reservation** record:
   ```
   Reservation {
     id: 'res-12345',
     guest_id: 'guest-789',
     room_id: null (assigned at check-in),
     room_type: 'double',
     check_in_date: '2025-12-25',
     check_in_time: '15:00',
     check_out_date: '2025-12-27',
     check_out_time: '11:00',
     num_nights: 2,
     num_guests: 2,
     status: 'CREATED',
     rate_code: 'STANDARD',
     estimated_charges: 200.00,
     created_at: '2025-12-21T10:00:00Z',
     created_by: 'guest' or 'staff-123'
   }
   ```

6. System sends confirmation:
   - Email with reservation details
   - Cancellation policy reminder
   - Check-in instructions

**Output**: Reservation in CREATED state

**Channel Manager Integration** (For OTA Bookings):

If reservation came from Channel Manager (OTA, travel agent, booking.com):

```
1. PMS imports reservation from Channel Manager:
   - channel = 'ota' (not 'direct', 'phone', 'walk-in')
   - reference_number = OTA reference ID (booking.com ID, Expedia ref, etc.)
   - OTA guest name and details imported

2. PMS publishes event: PMS.Reservation.Created.v1
   {
     reservation_id: 'res-12345',
     channel: 'ota',
     reference_number: 'BDC-123456789',  // Booking.com reference
     channel_manager: 'booking.com',     // Which OTA system
     ...
   }

3. Channel Manager consumer (if subscribed):
   - Receives event
   - Updates OTA status to "confirmed in PMS"
   - Prevents double-booking
   - (Optional) sends notification to guest

4. During stay:
   - PMS publishes: PMS.Guest.CheckedIn.v1
   - Channel Manager receives and updates OTA status
   - Prevents cancellation during active stay

5. At check-out:
   - PMS publishes: PMS.Guest.CheckedOut.v1
   - Folio closed and invoice created
   - Channel Manager receives, marks booking complete
   - Channel Manager ready for guest review/rating
```

**Important**: PMS is source of truth for reservation. Channel Manager syncs FROM PMS, not the reverse.

---

**No-Show Detection**:
- If check-in date arrives and guest doesn't check in by deadline (e.g., 6 PM)
- System marks reservation as NO-SHOW
- No-show policy applied (charge percentage or full night, per policy)
- Event: `ReservationNoShow`

---

### Step 2: Check-in

**Trigger**: Guest arrives at hotel and presents to front desk

**Actors**: Guest, Staff (Front Desk), System

**Prerequisites**:
- Valid reservation exists for guest
- Reservation check-in date is today
- Guest has authenticated (ID verification)

**Steps**:
1. Staff searches for reservation by:
   - Reservation number, OR
   - Guest name + check-in date, OR
   - Guest email/phone

2. System displays reservation details:
   - Guest name, contact info
   - Room type
   - Duration (2 nights)
   - Estimated charges
   - Special requests

3. Staff verifies guest identity:
   - Check ID/passport matches name
   - Verify contact information
   - Note any discrepancies

4. Staff assigns room:
   - System suggests available rooms of requested type
   - Staff can override (if guest requests different room)
   - System holds room (prevents double-assignment)

5. System **creates Folio**:
   ```
   Folio {
     id: 'folio-456',
     guest_id: 'guest-789',
     reservation_id: 'res-12345',
     tenant_id: 'org-123',
     room_id: 'room-101',
     check_in_time: '2025-12-25T15:30:00Z',
     check_out_time: null,
     status: 'OPEN',
     balance_due: 0.00,
     created_at: '2025-12-25T15:30:00Z',
     created_by: 'staff-456'
   }
   ```

6. System updates **Reservation** status:
   - status: CHECKED-IN
   - room_id: assigned room
   - checked_in_at: timestamp

7. System posts initial room charge to folio:
   ```
   FolioCharge {
     id: 'charge-001',
     folio_id: 'folio-456',
     type: 'ROOM_CHARGE',
     description: 'Room 101 - 2 nights @ $100/night',
     amount: 200.00,
     posted_at: timestamp,
     status: 'POSTED'
   }
   ```

8. Staff provides:
   - Room key/access card
   - Welcome folder with hotel info
   - WiFi credentials
   - Emergency contact info

9. System sends event: `GuestCheckedIn`
   ```json
   {
     "event_type": "guest.checked_in",
     "folio_id": "folio-456",
     "guest_id": "guest-789",
     "room_id": "room-101",
     "num_nights": 2,
     "timestamp": "2025-12-25T15:30:00Z"
   }
   ```

**Output**: Folio OPEN, room charges posted

**Error Cases**:
- Reservation not found → offer to create ad-hoc booking
- Room not available → offer alternative room or date
- Guest ID doesn't match → require manager override

---

### Step 3: In-House Stay

**Duration**: From check-in to check-out

**Actors**: Guest, Staff (various departments), System

**What Happens**:

#### 3A: Room Charges (Automatic)
- First night charge posted at check-in
- Subsequent nights posted nightly (via night audit)
- No action needed from staff unless override required

#### 3B: Ancillary Charges (Manual)
Guest uses additional services, staff posts charges:

**Example 1: Restaurant Charge**
1. Guest orders breakfast/lunch/dinner
2. Restaurant staff charges to room (folio number)
3. System receives charge from restaurant module
4. System adds charge to folio

**Example 2: Minibar or WiFi Upgrade**
1. Housekeeping scans minibar items
2. System calculates charge
3. System posts to folio

**Example 3: Service Charge (laundry, spa, etc.)**
1. Guest requests service
2. Staff posts service to folio
3. System records charge

**Folio Entry Example**:
```
FolioCharge {
  id: 'charge-002',
  folio_id: 'folio-456',
  type: 'RESTAURANT',
  description: 'Breakfast - December 26',
  amount: 45.00,
  posted_at: '2025-12-26T08:00:00Z',
  posted_by: 'staff-789',
  status: 'POSTED'
}
```

#### 3C: Folio Balance Update
System calculates running balance:
```
Running Balance:
  Room charges: $200.00
  Restaurant: $45.00
  Minibar: $15.00
  ---
  Current Total: $260.00
```

#### 3D: In-House Balance Check (Optional)
- Staff can check guest's folio balance anytime
- Used for:
  - Pre-check-out notification if balance high
  - Dispute resolution if guest questions charge
  - Safety check (identify unusual activity)

#### 3E: Charge Corrections (If Needed)
If error detected (duplicate charge, wrong amount):
1. Staff identifies error
2. Staff creates reversal entry (negative charge)
3. Staff creates corrected charge
4. Both entries logged with reason and timestamp
5. Manager approval required if > threshold amount

**Example**:
```
FolioCharge {
  id: 'charge-003',
  folio_id: 'folio-456',
  type: 'REVERSAL',
  description: 'Reversal of restaurant charge (duplicate)',
  amount: -45.00,
  reason: 'Duplicate entry',
  reversed_charge_id: 'charge-002',
  posted_at: '2025-12-26T08:15:00Z',
  posted_by: 'staff-789',
  approved_by: 'manager-101'
}
```

#### 3F: No Backdating Without Approval
Rule: Staff cannot post charge for date > 3 days past without manager approval
- Prevents accidental old charges
- Maintains audit trail
- Requires explicit reason

---

### Step 4: Check-out

**Trigger**: Guest indicates departure (or departure date/time arrives)

**Actors**: Guest, Staff (Front Desk), System

**Prerequisites**:
- Guest folio is OPEN
- Guest has settled payment or authorized billing method

**Steps**:

#### 4.1: Initiate Check-out
1. Guest approaches front desk or calls
2. Staff searches folio by guest name or room number
3. System displays folio with all charges

#### 4.2: Final Charges (If Any)
1. Staff applies final charges:
   - Last minute restaurant/minibar
   - Damage charges (if applicable)
   - Special services used

2. System updates folio total

#### 4.3: Calculate Final Bill
System calculates:
```
Room charges:              $200.00
Restaurant/Minibar:        $60.00
Services:                  $0.00
Subtotal:                 $260.00
Tax (10%):                $26.00
---
Grand Total:             $286.00

Payments Applied:
  Credit card:           -$286.00
---
Balance Due:              $0.00
```

#### 4.4: Present Bill to Guest
1. Staff shows itemized folio
2. Guest reviews charges
3. Guest questions any charges (if applicable)
4. Staff resolves disputes

#### 4.5: Process Payment
**Option A: Prepaid Reservation**
- Charges already charged to card during check-in
- System shows "no balance due"
- Check-out is straightforward

**Option B: Post-Paid (Pay on Departure)**
1. Guest provides payment method
2. System charges amount to:
   - Credit card, OR
   - Debit card, OR
   - Cash, OR
   - Direct billing (corporate)

3. System processes payment:
   - If credit card: authorize and charge
   - If cash: staff collects and records
   - If corporate: invoice sent to corporate

4. Payment status: `COMPLETED`

#### 4.6: Close Folio
1. System updates Folio status: SETTLED
2. System updates Reservation status: CHECKED-OUT
3. System records:
   - Actual check-out time
   - Payment method
   - Amount paid
   - Balance

4. System creates event: `GuestCheckedOut`
   ```json
   {
     "event_type": "guest.checked_out",
     "folio_id": "folio-456",
     "guest_id": "guest-789",
     "room_id": "room-101",
     "total_charges": 286.00,
     "amount_paid": 286.00,
     "payment_method": "CREDIT_CARD",
     "check_out_time": "2025-12-27T11:00:00Z",
     "timestamp": "2025-12-27T11:05:00Z"
   }
   ```

#### 4.7: Post Check-out
1. Staff updates room status (dirty, needs cleaning)
2. Housekeeping receives room for turnover
3. System sends:
   - Receipt to guest (email or print)
   - Thank you message
   - Feedback/review request

**Output**: Folio SETTLED, reservation CHECKED-OUT, room returned to inventory

---

### Step 5: Night Audit (End-of-Day Closing)

**Trigger**: Scheduled job at end of business day (e.g., 2 AM)

**Actors**: System (automated), Accounting system

**Prerequisites**:
- All guests have checked out (or extended into next day)
- No pending charges or corrections

**Process**:

#### 5.1: Verify All Check-outs
System verifies:
- All reservations for day are accounted for:
  - ✅ Checked-out (folio settled)
  - ⚠️ Extended (will checkout tomorrow)
  - ❌ No-show (not checked in)
  - ❌ Cancelled

#### 5.2: Identify Unclosed Folios
System flags any folio still OPEN:
- Guest still in hotel (no check-out initiated)
- Folio was never closed (system error)

Actions:
- Email alert to manager
- Halt night audit until resolved
- Manual intervention required

#### 5.3: Close Remaining Night Charges
For guests staying multiple nights:
1. Room charge for tomorrow night posted to folio
2. Folio balance updated
3. Guest charged next morning (if payment method is card)

#### 5.4: Calculate Daily Totals
System calculates:
```
Daily Report (2025-12-26):

Rooms Occupied:        45 rooms
Rooms Available:       50 rooms
Occupancy Rate:        90%

Room Revenue:        $4,500.00
Ancillary Revenue:     $850.00
Total Revenue:       $5,350.00

Tax Collected:         $535.00

Folios Settled:        43
Folios Pending:         2 (extended guests)

Payment Breakdown:
  Credit Card:      $4,200.00
  Cash:             $800.00
  Corporate Bill:    $350.00
```

#### 5.5: Lock Day (Immutable)
1. System marks business day as "CLOSED" in database
2. No further changes allowed to closed day
3. Exception: Manager override with explicit approval (rare)

#### 5.6: Post Accounting Entries
System publishes events to Accounting:
```json
{
  "event_type": "daily_closing_completed",
  "business_day": "2025-12-26",
  "tenant_id": "org-123",
  "room_revenue": 4500.00,
  "ancillary_revenue": 850.00,
  "taxes_collected": 535.00,
  "folios_settled": 43,
  "timestamp": "2025-12-27T02:00:00Z"
}
```

Accounting system:
- Creates General Ledger entries (debit Cash, credit Room Revenue)
- Updates revenue recognition schedule
- Updates tax liability

#### 5.7: Generate Reports
System generates:
- Daily Revenue Report
- Occupancy Report
- Payment Methods Report
- Outstanding Balances Report (guests still owing)

**Output**: Business day closed, accounting entries created, reports available to management

---

## Alternative Flows

### Flow A: No-Show

**Trigger**: Reservation check-in date arrives but guest doesn't check in

**Steps**:
1. System detects:
   - Reservation exists for today
   - Check-in deadline passed (e.g., 6 PM)
   - No check-in recorded

2. System marks Reservation status: NO-SHOW

3. System applies no-show policy:
   - Policy A: Charge 50% of room rate
   - Policy B: Charge full room rate
   - Policy C: Charge per cancellation policy
   - (Policy selected based on rate plan used)

4. System posts no-show charge to temporary folio
5. System attempts to charge payment method on file
6. System sends notification to guest

**GL Account Mapping for No-Show Revenue:**

```
No-show charge creation triggers FolioCharge with source='system':

Debit: Guest A/R Account or Cash (if payment collected)
  Credit: Room Revenue - No-Show Account (derived from rate plan)

OR (if payment method on file fails):

Debit: No-Show Revenue Receivable (contra-revenue)
  Credit: Room Revenue - No-Show Account

Posting: Posted at Night Audit, locked for the day
```

**GL Account Codes (Recommended):**
- `1301-REV-RM` → Room Revenue (base)
- `4101-REV-RM-NS` → No-Show Revenue (if tracking separately)
- `1231-REV-AR-NS` → No-Show A/R (for uncollected no-shows)

**Event Published:**

```typescript
// When no-show policy applied
{
  event_type: "PMS.Reservation.NoShow.v1",
  correlation_id: "corr-xxx",
  data: {
    reservation_id: "res-123",
    folio_id: "folio-456",
    guest_id: "guest-789",
    scheduled_check_in: "2025-12-24",
    no_show_detected_at: "2025-12-24T18:15:00Z",

    no_show_policy: "50%_of_rate",
    room_rate_per_night: 500000,
    no_show_amount: 250000,
    currency: "IDR",

    payment_status: "collected" | "pending" | "failed",
    payment_method_used: "card_on_file" | "corporate_billing",

    gl_account_code: "4101-REV-RM-NS",
    created_by: "system"
  }
}
```

**Accounting Integration (ACC-SPEC-10 + CORE-STD-20):**

1. PMS publishes `Reservation.NoShow.v1` event at check-in deadline
2. Accounting system consumes event
3. GL journal entry created:
   - If payment collected: Debit AR/Cash, Credit Room Revenue (No-Show)
   - If payment pending: Debit A/R Receivable, Credit Room Revenue (No-Show)
4. Event published to downstream: `Accounting.Revenue.Posted.v1`

**Output**: Reservation NO-SHOW, revenue recognized (GL posted), payment collected (if available)

---

### Flow B: Early Check-out

**Trigger**: Guest departs before scheduled check-out date

**Steps**:
1. Guest checks out early (e.g., Day 1 of 3-night stay)
2. Staff initiates check-out as normal
3. System calculates charges for actual nights stayed:
   - Night 1: $100 (charged)
   - Nights 2-3: $200 (refund or credit)

4. System determines refund policy:
   - Non-refundable rate: no refund
   - Refundable rate: refund unused nights
   - Flexible rate: refund unused nights minus cancellation fee

5. If refund due:
   - System creates credit on folio (negative charge)
   - System refunds to original payment method
   - Guest receives refund confirmation

6. Folio settled with refunded amount
7. Room released for same-day resale (if possible)

**Output**: Folio settled with adjusted charges, refund processed if applicable

---

### Flow C: Extend Stay

**Trigger**: Guest requests to extend stay (additional nights)

**Steps**:
1. Guest approaches desk: "Can I stay 1 more night?"
2. Staff checks availability:
   - Next night's room availability
   - Room type matches current room (if guest wants same room)

3. System verifies:
   - Tenant subscription includes PMS module
   - No system limit on reservation length

4. If available:
   - Staff updates Reservation end date
   - System posts new night's charges
   - System processes payment for additional night
   - Updated folio sent to guest

5. If not available:
   - Offer alternative room or offer alternative dates
   - If guest declines: check-out proceeds as scheduled

**Output**: Reservation extended, additional charges posted and collected

---

### Flow D: Charge Dispute / Correction

**Trigger**: Guest questions charge on folio

**Scenarios**:

**Scenario 1: Duplicate Charge**
- Staff identifies same charge posted twice
- Staff creates reversal entry
- System shows before/after balance
- Guest approves
- Folio updated

**Scenario 2: Wrong Amount**
- Staff posted $100 instead of $50
- Staff creates reversal of $100
- Staff creates new charge for $50
- Manager approves (if > threshold)
- Folio updated

**Scenario 3: Unauthorized Charge**
- Guest claims they didn't order item
- Staff investigates (check with restaurant, housekeeping)
- If confirmed error: reversal + apology
- If confirmed guest did order: guest pays or manager decision

**Process**:
1. Staff listens to dispute
2. Staff researches charge (check source system)
3. Resolution:
   - If staff error: create reversal, recharge correct amount
   - If vendor error: coordinate with vendor
   - If guest error: educate guest, may offer courtesy
4. Document resolution in folio notes
5. Update balance and close folio

---

## Important Invariants

### No Check-in Without Folio
```
INVARIANT: Reservation.status = CHECKED-IN → Folio exists and status = OPEN
```
- Cannot record guest in hotel without active billing record
- Folio is created atomically at check-in

### No Charges Without Open Folio
```
INVARIANT: FolioCharge → Folio.status = OPEN
```
- Cannot post charge to closed or non-existent folio
- Every charge must reference valid folio

### Check-out Closes Folio
```
INVARIANT: Reservation.status = CHECKED-OUT → Folio.status = SETTLED
```
- Folio must be closed at check-out
- No additional charges after settlement

### Night Audit Locks Day
```
INVARIANT: After NightAudit for day D → No FolioCharge for date ≤ D (without exception override)
```
- Prevents backdating charges
- Ensures data integrity for accounting

### Payment for Charges
```
INVARIANT: FolioCharge with amount > 0 → Payment exists (or guest agreed to later payment)
```
- No charge without collection
- Outstanding balance tracked and followed up

---

## Integration with Accounting

Every folio generates accounting events:

| PMS Event | Accounting Entry |
|-----------|-----------------|
| `GuestCheckedIn` (room charge posted) | Debit Accounts Receivable, Credit Room Revenue |
| `AncillaryCharge` (restaurant, minibar) | Debit Accounts Receivable, Credit Ancillary Revenue |
| `GuestCheckedOut` (payment received) | Debit Cash, Credit Accounts Receivable |
| `RefundIssued` | Debit Room Revenue (reversal), Credit Cash |
| `NightAudit` (daily closing) | Revenue recognition entries, reconciliation |

---

## Timing & Deadlines

| Event | Timing | Flexibility |
|-------|--------|-------------|
| Check-in deadline | 6 PM | No-show after this time (or with prior notice) |
| Check-out time | 11 AM | Extended checkout available (fee may apply) |
| Night audit | 2 AM | Daily, non-negotiable |
| Charge posting | Real-time | Within business day for accuracy |
| Payment due | At check-out | Pre-authorized or deferred per policy |

---

## Data Structures

### Reservation
```typescript
interface Reservation {
  id: string;                    // res-12345
  guest_id: string;
  room_type: string;             // "double", "suite", etc.
  check_in_date: Date;
  check_out_date: Date;
  check_in_time: string;         // "15:00"
  check_out_time: string;        // "11:00"
  num_nights: number;
  num_guests: number;
  status: "CREATED" | "CHECKED-IN" | "CHECKED-OUT" | "CANCELLED" | "NO-SHOW";
  rate_code: string;             // "STANDARD", "CORPORATE", etc.
  estimated_charges: number;
  room_id?: string;              // assigned at check-in
  created_at: DateTime;
  created_by: string;
}
```

### Folio
```typescript
interface Folio {
  id: string;                    // folio-456
  guest_id: string;
  reservation_id: string;
  room_id: string;
  check_in_time: DateTime;
  check_out_time?: DateTime;
  status: "OPEN" | "SETTLED";
  charges: FolioCharge[];
  balance_due: number;
  payment_method?: string;
  payment_reference?: string;
  created_at: DateTime;
  created_by: string;
}
```

### FolioCharge
```typescript
interface FolioCharge {
  id: string;                    // charge-001
  folio_id: string;
  type: "ROOM_CHARGE" | "RESTAURANT" | "MINIBAR" | "SERVICE" | "REVERSAL" | "TAX";
  description: string;
  amount: number;
  posted_at: DateTime;
  posted_by: string;
  status: "POSTED" | "REVERSAL";
  reversed_charge_id?: string;   // if type = REVERSAL
  manager_approval?: boolean;
  approved_by?: string;
  reason?: string;
}
```

---

## POS-PMS Integration Pattern

> **Status**: ✅ Approved (2025-12-07)

**Purpose**: Define the integration mechanism between POS (Point of Sale - restaurant/bar/spa charges) and PMS (folio management). This section clarifies the architectural approach for real-time charge posting.

### Decision: Event-Driven (Primary) + API Fallback

We use **event-driven architecture** as the primary pattern with **optional API fallback** for edge cases.

#### Rationale

| Approach | Pros | Cons | Decision |
|---|---|---|---|
| **Event-Driven (Chosen)** | Real-time, loose coupling, scalable, supports multiple POS systems, audit trail built-in | Eventual consistency (acceptable for PMS), requires event infrastructure | ✅ PRIMARY |
| **API Request/Response** | Synchronous, guaranteed delivery, simple implementation | Tight coupling, blocks POS, single POS per property, harder to scale | API Fallback Only |
| **Database Sync** | Simple, direct, no infrastructure | Tight coupling, hard to audit, race conditions, tenant isolation risk | ❌ NOT RECOMMENDED |

### Primary: Event-Driven Flow

**When POS records a charge, it publishes a `POS.Charge.Created` event:**

```typescript
// POS publishes event
event POS.Charge.Created.v1 {
  correlation_id: "corr-12345",
  source: "POS",
  timestamp: "2025-12-24T14:30:00Z",

  data: {
    charge_id: "pos-charge-001",
    tenant_id: "tenant-A",
    folio_id: "folio-99",            // ← Key: identifies which folio
    amount: 250000,                   // IDR
    currency: "IDR",
    category: "restaurant",           // restaurant, bar, spa, laundry, etc.
    description: "Lunch for 2",
    posted_at: "2025-12-24T14:25:00Z"
  }
}
```

**PMS listens and applies charge:**

```typescript
// PMS consumes event
async function handlePOSChargeCreated(event: POSChargeCreated) {
  const folio = await getFolioById(event.data.folio_id, event.data.tenant_id);

  // Validation
  if (!folio || folio.status !== 'OPEN') {
    // Log error, don't fail - POS shouldn't wait
    return logAndAlert('Folio not open', event);
  }

  // Apply charge
  const charge = await createFolioCharge({
    folio_id: folio.id,
    amount: event.data.amount,
    category: event.data.category,
    posted_at: event.data.posted_at,
    source: 'POS',
    correlation_id: event.correlation_id,
    external_id: event.data.charge_id  // Idempotency key
  });

  // Publish PMS event
  await publishEvent({
    event_id: generateUUID(),
    correlation_id: event.correlation_id,  // ← Propagate
    causation_id: event.id,
    event_type: 'PMS.Charge.Posted.v1',
    data: {
      folio_id: folio.id,
      charge_id: charge.id,
      amount: charge.amount,
      category: charge.category
    }
  });
}
```

**Benefits:**
- POS doesn't wait for PMS confirmation → Fast response to user
- PMS processes async → scalable
- Event history provides audit trail
- Easy to add other systems (e.g., Spa system, Laundry)
- Correlation_id tracks full flow across systems

### Idempotency & Duplicate Prevention

**Problem:** Network delays might cause POS to retry, creating duplicate charges.

**Solution:** Use `external_id` (from POS system) as idempotency key:

```sql
CREATE UNIQUE INDEX idx_folio_charge_external_id
  ON folio_charges(folio_id, external_id)
  WHERE deleted_at IS NULL;
```

**Implementation:**

```typescript
// On event arrival
const existingCharge = await findChargeByExternalId(
  folio_id,
  event.data.charge_id
);

if (existingCharge) {
  // Already processed - ignore duplicate
  return logger.info('Duplicate charge skipped', event.data.charge_id);
}

// First time - create charge
const charge = await createFolioCharge({
  // ...
  external_id: event.data.charge_id  // Prevents duplicates
});
```

### Fallback: Direct API (Synchronous)

For edge cases where event infrastructure is unavailable or POS system requires synchronous confirmation:

```typescript
// POS calls PMS REST API directly
POST /api/v1/folios/{folio_id}/charges
{
  amount: 250000,
  category: "restaurant",
  description: "Lunch for 2",
  idempotency_key: "pos-charge-001"  // ← Client provides dedup key
}

Response:
{
  charge_id: "charge-xyz",
  folio_id: "folio-99",
  amount: 250000,
  status: "POSTED"
}
```

**When to Use:**
- POS system upgraded/replaced (needs backward compatibility)
- Initial pilot or testing phase
- Network event broker temporarily unavailable

**Constraints:**
- API call must timeout within 5 seconds
- If timeout → POS retries with idempotency_key
- PMS still publishes event after charge created

### Charge Categories & GL Mapping

| POS Category | Description | GL Account | Notes |
|---|---|---|---|
| **restaurant** | Food & beverage | Revenue - F&B | Most common |
| **bar** | Alcoholic drinks | Revenue - Bar | Separate for licensing |
| **spa** | Spa/massage services | Revenue - Spa | High-margin |
| **laundry** | Guest laundry | Revenue - Laundry | Low-volume |
| **minibar** | In-room items | Revenue - Minibar | Automatic inventory deduction |
| **phone** | Phone charges | Revenue - Telecom | Metered service |
| **late_checkout** | Early departure fee | Revenue - Fees | Time-based charge |
| **room_upgrade** | Upgrade surcharge | Revenue - Room Upgrade | Negotiated price |
| **custom** | Other charges | Revenue - Misc | Manager discretion |

### Error Handling

**When folio is closed (check-out complete):**

```
POS publishes: POS.Charge.Created
PMS receives event and checks folio status
Folio.status = 'CLOSED' → Cannot add charges

Action: Log to `unmatched_charges` table for manual review
Alert: Send notification to Front Desk + POS Operator
Manual Resolution: Manager reviews in back-office, decides:
  a) Reopen folio temporarily, add charge, close again
  b) Create separate transaction (not attached to folio)
  c) Waive charge (manager discretion with approval)
```

**When folio is not found:**

```
POS publishes: POS.Charge.Created with folio_id = "folio-99"
PMS cannot find folio → Possible causes:
  - Wrong folio_id sent from POS
  - Guest checked out already
  - System clock skew (charge for tomorrow)

Action: Log to `unmatched_charges` table
Alert: Send to Front Desk manager
Max retention: 24 hours (then manual cleanup or discard)
```

### Reconciliation Query

**Daily reconciliation between POS and PMS:**

```sql
-- Charges posted to folio
SELECT
  date(fc.posted_at) AS posting_date,
  fc.category,
  COUNT(*) AS charge_count,
  SUM(fc.amount) AS total_amount
FROM folio_charges fc
WHERE fc.tenant_id = $1
  AND fc.source = 'POS'
  AND date(fc.posted_at) = $2
GROUP BY date(fc.posted_at), fc.category;

-- Compare with POS reported charges
-- If discrepancy > 1% → Investigate and reconcile
```

### Sequence Diagram

```
POS System              PMS System            Event Broker         Accounting
    │                      │                       │                   │
    │ [User orders food]   │                       │                   │
    ├─ Create charge ─────>│                       │                   │
    │                      │ Publish event ───────>│                   │
    │ [Show confirmation]  │                       │                   │
    │<─ Charge recorded ───┤                       │ Post to queue     │
    │                      │<─ Event ACK ──────────┤                   │
    │                      │ Create FolioCharge    │                   │
    │                      │ Publish: Charge.Posted ────────────────>  │
    │                      │                       │                   │
    │                      │                       │   Consume event   │
    │                      │                       │   Create JE entry │
    │                      │                       │<───────────────────
```

---

## Related Documents

- **SPEC-07**: Use Cases — what Staff and Guest can do
- **SPEC-08**: Tenant Lifecycle — platform-level process
- **SPEC-10**: Accounting Core Process — how PMS charges become accounting entries
- **BPMN #03**: Detailed swim lanes for PMS workflow
- **ERD #19**: PMS domain entities (Reservation, Folio, Room, RoomType)
- **EVENT MODEL**: Event schema for PMS events

---

## Implementation Checklist

- [ ] Reservation creation and state transitions working
- [ ] Check-in creates folio and posts room charge
- [ ] Charge posting to open folio implemented
- [ ] Check-out calculates final balance and settles folio
- [ ] Night audit processes daily closing and locks day
- [ ] No charges can be posted to closed day without exception
- [ ] Events published for all state changes
- [ ] Accounting system consumes and posts entries
- [ ] No-show policy enforced
- [ ] Early check-out refund logic implemented
- [ ] Charge dispute workflow implemented
- [ ] Payment methods integrated (card, cash, corporate)
- [ ] Reporting dashboard shows daily metrics
- [ ] Audit trail captures all changes with user and timestamp
