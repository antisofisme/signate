# ARCH-09: Modularization Principles & Module Architecture

This document establishes the **architectural principles for module design, module boundaries, and module composition** in PROJECT_BESAR. It defines how modules can be technically standalone but strategically bundled as products.

**Mandatory Reading**: Must be read before ERD design and implementation.

---

## Core Principle: Architecture ≠ Product Packaging

### Architecture (Technical)
- Answers: "Can this module function independently?"
- Defined by: dependencies, data flow, integration points
- Example: PMS *can technically* work without Accounting

### Product Packaging (Business)
- Answers: "Should this module be sold separately?"
- Defined by: business value, customer needs, legal requirements
- Example: PMS *should NOT be sold without* Accounting (product decision)

**Key Insight**:
```
A module can be:
  ✅ Architecturally independent (can work alone)
  ❌ Commercially independent (must bundle with others)

EXAMPLE:
  PMS is architecturally independent
  BUT must bundle with Accounting for commercial release
```

---

## Golden Rules (Locked - Non-Negotiable)

### Rule 1: Accounting is the Core Financial Engine
- All financial transactions converge to Accounting module
- Accounting can exist and function without any operational module (PMS, POS, HR)
- Accounting is the single source of truth for ledger
- **No module bypasses Accounting for financial records**

### Rule 2: PMS is the Operational Engine (But Bundled)
- PMS can technically operate standalone (create reservations, folios, charges)
- BUT must bundle with Accounting for product release
- Reason: Without Accounting, no closing, no ledger, no financial statements
- This is **product policy, not technical limitation**

### Rule 3: All Modules Communicate via Events & Adapters
- No module writes directly to another module's database
- No module calls another module's ledger endpoint directly
- All integration flows through:
  - Events (asynchronous)
  - Adapters (translation layer)
- Prevents tight coupling and enables independent scaling

### Rule 4: Standalone ≠ Always Enabled
- Module can be architecturally standalone
- BUT subscription/feature gates determine if enabled for tenant
- Even if code exists, disabled modules don't create transactions
- UI hides disabled module features (feature gating)

---

## Module Classification

### Category A: Core Modules (Can be Standalone & Sold Independently)

**Accounting**
- Can accept manual invoice input
- Can accept imported data from external systems
- Can function without any operational module (PMS, POS, HR)
- Capable of closure and reporting
- **Can be sold as standalone product**

**HR / Payroll** (Future)
- Can accept manual payroll data
- Can import employee records
- Can calculate and post payroll entries
- Independent from PMS/POS

**Inventory** (Future - Basic)
- Can track stock manually
- Can accept physical counts
- Can do basic stock movements
- Can work independently (or integrated with POS/PMS)

**Characteristics**:
- Can input data manually OR via import
- Don't strictly depend on operational data
- Can generate financial ledger entries independently
- Can produce standalone reports

---

### Category B: Operational Modules (Standalone Technical, Bundled Commercial)

**PMS (Property Management System)**
- Generates operational transactions (reservations, check-ins, charges)
- Does NOT have its own ledger (no chart of accounts, no period close)
- Publishes events to Accounting via adapter
- Technically can work without Accounting (can record operations)
- Commercially MUST bundle with Accounting

**POS (Point of Sale)**
- Generates sales transactions
- Does NOT have ledger, period closing, or financial statements
- Publishes events to Accounting via adapter
- Same bundling requirement as PMS

**Booking Engine** (Future)
- Generates reservation events
- Feeds into PMS or standalone bookings
- Events published to Accounting

**Characteristics**:
- Generate transactional events
- No ledger of their own
- Must integrate with Accounting via adapter
- Architecturally standalone but commercially bundled
- Cannot produce auditable financial statements independently

---

### Category C: Supporting Modules (Dependent, Enable Other Modules)

**CRM / Guest Management**
- Tracks guest profiles and interactions
- Consumes events from PMS, POS, Booking
- Does NOT generate financial transactions
- Enhances operational insights
- Depends on operational modules for data

**Loyalty Program**
- Tracks member points and rewards
- Consumes events from POS/PMS
- May publish "point earned" and "point redeemed" events
- Supporting feature, not core operation

**Reporting & Analytics**
- Consumes events from all modules
- Generates insights and dashboards
- Does NOT create transactions
- Reads from ledger but doesn't modify

**Characteristics**:
- Non-transactional
- Consume data from other modules
- Cannot function without operational or core modules
- Cannot be sold independently

---

## Module Dependency Map

```
SOLD INDEPENDENTLY:
┌─────────────────┐
│  Accounting     │  (can work alone)
└─────────────────┘

SOLD TOGETHER:
┌──────────┐        ┌──────────────────┐
│   PMS    │───────→│   Accounting     │  (via Adapter)
└──────────┘        └──────────────────┘

┌──────────┐        ┌──────────────────┐
│   POS    │───────→│   Accounting     │  (via Adapter)
└──────────┘        └──────────────────┘

SUPPORTING (Optional):
┌────────────────┐
│  CRM / Loyalty │──→ Consumes from PMS/POS
└────────────────┘

┌────────────────┐
│   Reporting    │──→ Consumes from all
└────────────────┘
```

---

## PMS: Technical Independence vs. Commercial Bundling

### Technical Architecture (Standalone)

PMS independently provides:
- Reservation creation and management
- Folio (billing record) creation and maintenance
- Room status tracking
- Check-in/check-out workflow
- Charge posting to folio
- Guest interaction history

**Example**: Hotel could theoretically use just PMS to:
- Track reservations
- Record room charges
- Manage operations
- NOT close periods or produce financial statements

---

### Commercial Requirement (Bundled)

PMS **must bundle with Accounting** because:

1. **No Ledger in PMS**
   - PMS records operational data (reservations, charges)
   - But does NOT maintain financial ledger
   - Cannot close periods
   - Cannot produce financial statements

2. **Regulatory Requirement**
   - Hotels need auditable financial records
   - Accounting provides immutable ledger
   - Period closing provides cut-off for financial reporting

3. **Business Logic Requirement**
   - Guest folio is operational
   - But financial recognition (revenue) happens in Accounting
   - Accounting module creates GL entries from PMS events

4. **No Customer Would Accept**
   - "Track my operations but can't close the books?"
   - No financial visibility
   - Cannot file taxes or audit trail

**Decision**: Architecturally possible to sell PMS alone, but **product policy forbids it**.

---

## Adapter Pattern (Required for All Operational Modules)

### Problem
Operational modules generate transactions (PMS, POS) but don't know chart of accounts, tax rules, or cost centers. Accounting needs standardized data format.

### Solution: Adapter Layer

Each operational module has a **[Module]-Accounting Adapter** that:
- Maps operational events to financial data
- Translates domain concepts to GL account codes
- Applies tax rules and cost center allocation
- Validates financial completeness

### PMS-Accounting Adapter (Example)

**Function**: Converts PMS events (guest checkout) to Accounting events (invoice + journal entries)

**Mapping**:
```
PMS Event: guest.checked_out
{
  folio_id: "folio-456",
  guest_id: "guest-789",
  room_id: "room-101",
  charges: {
    room_charge: 200.00,
    ancillary: 86.00,
    tax: 28.60,
    total: 314.60
  }
}

↓ (via Adapter)

Accounting Events:
1. invoice.created
   {
     invoice_id: "inv-001",
     customer_id: "guest-789",
     line_items: [
       { account_code: "4100", description: "Room Revenue", amount: 200 },
       { account_code: "4200", description: "Ancillary Revenue", amount: 86 },
       { account_code: "2300", description: "Tax Payable", amount: 28.60 }
     ]
   }

2. journal_entry.posted
   {
     lines: [
       { account: "1200", debit: 314.60 },     // AR
       { account: "4100", credit: 200.00 },    // Revenue
       { account: "4200", credit: 86.00 },     // Revenue
       { account: "2300", credit: 28.60 }      // Tax
     ]
   }
```

**Adapter Responsibilities**:
- ✅ Map PMS room types to GL revenue accounts
- ✅ Map ancillary services to GL accounts
- ✅ Apply tax rates (per jurisdiction)
- ✅ Allocate to cost centers (if multi-property)
- ✅ Validate: all required fields present
- ✅ Validate: amounts reconcile
- ✅ Validate: tax calculation correct

**Adapter Anti-Patterns** (DO NOT):
- ❌ Bypass adapter and write ledger directly
- ❌ Store business logic in adapter (adapter is translation, not logic)
- ❌ Create adapter without Accounting involvement
- ❌ Adapter modifies amounts (validation only)

### POS-Accounting Adapter (Similar)
- Maps POS sales to GL revenue accounts
- Applies tax per jurisdiction
- Tracks payment method breakdown
- Feeds to Accounting via events

---

## Subscription & Feature Gating

### Subscription Model

**TenantApp** entity controls which modules are active:

```
Tenant: "Hotel Bali"
  └─ TenantApp: PMS (status: ACTIVE)
  └─ TenantApp: Accounting (status: ACTIVE)
  └─ TenantApp: Reporting (status: ACTIVE)
  └─ TenantApp: CRM (status: INACTIVE)  ← Feature not subscribed

Tenant: "Restaurant Medan"
  └─ TenantApp: POS (status: ACTIVE)
  └─ TenantApp: Accounting (status: ACTIVE)
  └─ TenantApp: Loyalty (status: ACTIVE)
  └─ TenantApp: CRM (status: INACTIVE)
```

### Feature Gating Rules

**Technical Level (Database)**:
- ❌ DO NOT add feature gates at database level
- ❌ DO NOT hide tables or columns based on subscription
- ✅ DO: Application logic checks `TenantApp.status`

**Application Level (Business Logic)**:
- ✅ Check if module is subscribed before enabling functionality
- ✅ Return error if unsubscribed user tries to use module

**UI Level (User Experience)**:
- ✅ Hide module navigation if not subscribed
- ✅ Disable buttons/features if not subscribed
- ✅ Show upgrade prompts

**Example (PMS + Accounting Bundling)**:
```typescript
// User tries to access PMS
if (tenantApp.find(t => t.app_code === 'PMS').status !== 'ACTIVE') {
  throw new Error('PMS not subscribed. Must bundle with Accounting.');
}

// PMS generates checkout event
const checkoutEvent = emitCheckoutEvent(folio);

// Adapter checks if Accounting is enabled
if (tenantApp.find(t => t.app_code === 'ACCOUNTING').status === 'ACTIVE') {
  // Convert to accounting event
  const invoiceEvent = pmsAccountingAdapter.convert(checkoutEvent);
  await eventBus.publish(invoiceEvent);
} else {
  // If Accounting not enabled, PMS still tracks operations
  // But no financial records created
  // (This scenario is blocked by product policy)
}
```

---

## Real-World Scenarios

### Scenario A: Accounting Only

**Tenant subscribes**: Accounting module only

**Use case**: Tax accountant using platform to track financial records, not running hotel

**What works**:
- ✅ Create invoices manually
- ✅ Import invoices (CSV)
- ✅ Record payments
- ✅ Post journal entries
- ✅ Close periods and generate financial statements
- ✅ Run reports

**What doesn't work**:
- ❌ No PMS (can't create reservations)
- ❌ No operational data
- ❌ Data input is manual or import-only

**Product**: Valid commercial scenario

---

### Scenario B: PMS + Accounting (Default Hotel)

**Tenant subscribes**: PMS + Accounting (bundled)

**Use case**: Standard hotel operation

**What works**:
- ✅ Create reservations
- ✅ Check-in/check-out guests
- ✅ Post charges to folios
- ✅ Auto-generate invoices from PMS events
- ✅ Auto-post journal entries
- ✅ Close periods
- ✅ Generate financial statements
- ✅ Track occupancy and revenue

**Data flow**:
```
PMS Events
  ↓
PMS-Accounting Adapter
  ↓
Accounting Events
  ↓
Invoice + Journal Posting
  ↓
Financial Statements
```

**Product**: Default / expected scenario

---

### Scenario C: PMS Without Accounting (BLOCKED)

**Tenant wants**: PMS only (no Accounting)

**Technical viability**: ✅ Technically possible

**Commercial decision**: ❌ Blocked by product policy

**Why blocked**:
- Cannot close periods
- Cannot generate financial statements
- No auditable record
- No ledger
- Customer would have no way to do accounting

**Product**: NOT offered to customers

---

### Scenario D: POS + Accounting (Restaurant)

**Tenant subscribes**: POS + Accounting

**What works**:
- ✅ Record sales transactions
- ✅ Track payments
- ✅ Auto-generate invoices
- ✅ Auto-post journal entries
- ✅ Run financial reports
- ✅ Track inventory usage

**Data flow**: Similar to PMS scenario, but events come from POS module

---

## Module Isolation & No Direct Access

### Anti-Pattern: Direct Database Access

❌ **DO NOT**:
```typescript
// BAD: PMS directly reads Accounting database
const ledgerBalance = await accountingDb.query(
  'SELECT SUM(debit - credit) FROM ledger WHERE account = ?'
);
```

✅ **DO INSTEAD**:
```typescript
// GOOD: PMS calls Accounting API (or reads read model)
const ledgerBalance = await accountingService.getAccountBalance('4100');

// OR consume event
const eventStream = await eventBus.consume('journal_entry.posted');
const balance = calculateBalance(eventStream);
```

### Anti-Pattern: Module Writes Ledger Directly

❌ **DO NOT**:
```typescript
// BAD: PMS writes directly to GL
await ledgerDb.insert({
  account: '4100',
  debit: 200,
  credit: 0,
  description: 'Room revenue'
});
```

✅ **DO INSTEAD**:
```typescript
// GOOD: PMS emits event, Adapter converts, Accounting posts
const checkoutEvent = await eventBus.publish('guest.checked_out', payload);
// Accounting adapter consumes and creates invoice
// Accounting posts journal entry
```

### Anti-Pattern: Feature Gating in Database

❌ **DO NOT**:
```sql
-- BAD: Hide tables based on subscription
CREATE SCHEMA IF NOT EXISTS pms_schema;
ALTER SCHEMA pms_schema OWNER TO (SELECT user FROM subscriptions WHERE module='PMS');
-- This is too invasive and breaks flexibility
```

✅ **DO INSTEAD**:
```typescript
// GOOD: Check subscription in application code
const hasPMS = tenantSubscription.modules.includes('PMS');
if (!hasPMS) {
  throw new Error('PMS module not subscribed');
}
```

---

## Critical Rules (Enforcement)

### Hard Rules (Automated Checks)
- [ ] All financial events must have `tenant_id`
- [ ] No module writes to another module's ledger
- [ ] All module-to-module communication via events
- [ ] All adapters produce consistent GL account codes
- [ ] All journal entries must balance (debits = credits)

### Code Review Rules
- [ ] Any new module integration must go through adapter
- [ ] Any GL access must be via Accounting service
- [ ] No cross-module database queries
- [ ] Feature gating implemented in application layer

### Deployment Rules
- [ ] Adapters versioned and backward-compatible
- [ ] Accounting changes don't break PMS
- [ ] Module can be disabled without crashing system
- [ ] Events can be replayed without side effects (idempotent)

---

## Module Roadmap Example

```
Current (MVP):
├─ Accounting (Core)
├─ PMS (+ bundled Accounting)
└─ Reporting

Year 1:
├─ Accounting (Core)
├─ PMS (+ bundled Accounting)
├─ POS (+ bundled Accounting)
├─ CRM (optional, consumes PMS/POS events)
└─ Reporting

Year 2:
├─ Accounting (standalone)
├─ PMS (bundled with Accounting)
├─ POS (bundled with Accounting)
├─ HR / Payroll (can be standalone or with Accounting)
├─ CRM (optional)
├─ Loyalty (optional)
└─ Reporting

Each new module:
1. Evaluated for architectural dependencies
2. If operational (PMS, POS): requires adapter to Accounting
3. Bundling decision made based on business value
4. Feature gates implemented before release
```

---

## Related Documents

- **ARCH-02**: Module Architecture — Internal design of individual modules
- **ARCH-06**: Repository Governance — How repositories align with modules
- **STD-19**: Event Model — How modules communicate via events
- **SPEC-10**: Accounting Core Process — Accounting module operations
- **SPEC-09**: PMS Core Process — PMS module operations
- **SPEC-08**: Tenant & Subscription Lifecycle — TenantApp subscription model

---

## Implementation Checklist

- [ ] Each operational module has documented adapter
- [ ] Adapter maps all operational events to GL accounts
- [ ] No module directly writes to ledger
- [ ] All module-to-module communication via events
- [ ] Feature gating implemented in application layer (not database)
- [ ] Subscription model enforced (PMS bundled with Accounting)
- [ ] Tests validate adapter correctness (amounts, balancing)
- [ ] Documentation specifies which modules can be standalone
- [ ] Documentation specifies which modules must bundle
- [ ] Product team aware of architecture vs. packaging distinction
- [ ] Monitoring tracks events from each module to Accounting
- [ ] Alerts if events drop (module producing events but Accounting not consuming)
