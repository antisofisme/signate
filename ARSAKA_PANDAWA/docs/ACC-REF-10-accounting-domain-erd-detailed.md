# REF-10: Accounting Domain ERD (Detailed)

This document provides the **detailed entity relationship design for the Accounting domain**. Accounting is the "financial spine" of ARSAKA_PANDAWA—all other operational domains (PMS, POS, Inventory, Procurement, HR) must integrate with and conform to this accounting model.

**Critical**: This is the authoritative source for all accounting entity design. Changes to this model require cross-module coordination.

---

## Accounting Principles (Locked - Non-Negotiable)

### Principle 1: Double-Entry Accounting
```
Every transaction results in balanced journal entry.
Total debits = Total credits (always).
No single-sided entries allowed.
```

### Principle 2: Append-Only Ledger
```
Posted journal entries NEVER updated.
Account balances NOT stored (calculated from entries).
Corrections issued as new reversing entries.
Complete audit trail of all changes preserved.
```

### Principle 3: Period Locking
```
Accounting periods must be formally closed.
Cannot post to closed periods.
Locked periods are immutable (read-only).
```

### Principle 4: All Corrections via Journal
```
NO direct balance adjustments.
NO updates to posted entries.
ALL corrections: create reversing journal entry.
```

### Principle 5: Event-Driven, Not CRUD
```
Accounting doesn't create data directly.
Responds to events from operational systems.
Example: Guest.CheckedOut event → creates Invoice → posts GL.
```

---

## Domain 1: Master Data

### ChartOfAccount (GL Account Structure)

**Purpose**: Define all general ledger accounts and hierarchy

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique account identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant owns account |
| `code` | VARCHAR | NOT NULL, UNIQUE (tenant_id) | Account number (1000, 2000, etc.) |
| `name` | VARCHAR | NOT NULL | Account name (Cash, AR, Revenue, etc.) |
| `type` | ENUM | NOT NULL | 'asset', 'liability', 'equity', 'revenue', 'expense' |
| `parent_account_id` | UUID | FK→ChartOfAccount | For hierarchical GL structure |
| `is_header` | BOOLEAN | NOT NULL | True if summary account (no transactions) |
| `is_active` | BOOLEAN | NOT NULL | False for soft-deleted accounts |
| `description` | TEXT | | What this account tracks |
| `normal_balance` | ENUM | NOT NULL | 'debit' or 'credit' (which side increases balance) |
| `created_at` | TIMESTAMP | NOT NULL | When account added |
| `created_by` | UUID | FK→User | Who created it |

**Unique Constraints**:
- (tenant_id, code) - One account code per tenant

**Hierarchical Structure**:
```
1000 Assets
├─ 1100 Current Assets
│  ├─ 1110 Cash
│  ├─ 1120 Bank Account
│  └─ 1130 Accounts Receivable
├─ 1200 Fixed Assets
│  ├─ 1210 Building
│  └─ 1220 Equipment
└─ 1300 Other Assets

4000 Revenue
├─ 4100 Room Revenue
├─ 4200 Food & Beverage Revenue
└─ 4300 Other Revenue

5000 Expenses
├─ 5100 Salaries
├─ 5200 Utilities
└─ 5300 Supplies
```

**Notes**:
- Immutable once created (only soft delete)
- parent_account_id NULL for top-level accounts
- is_header = true for summary accounts (no postings allowed)
- normal_balance determines debit/credit interpretation

---

### AccountingPeriod (Fiscal Period Management)

**Purpose**: Define accounting periods (months, quarters, years) and their status

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique period identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `period` | VARCHAR | NOT NULL, UNIQUE (tenant_id) | "2025-01", "2025-Q1", "2025" |
| `period_type` | ENUM | NOT NULL | 'monthly', 'quarterly', 'annual' |
| `period_start` | DATE | NOT NULL | First day of period |
| `period_end` | DATE | NOT NULL | Last day of period |
| `status` | ENUM | NOT NULL | 'open', 'locked', 'closed' |
| `locked_at` | TIMESTAMP | | When period locked (can't post new entries) |
| `locked_by` | UUID | FK→User | Who locked it |
| `closed_at` | TIMESTAMP | | When period officially closed (archival) |
| `closed_by` | UUID | FK→User | Who closed it |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**:
- (tenant_id, period) - One period record per period

**Status Transitions**:
```
OPEN → LOCKED → CLOSED
 │       └─ Can reopen if no dependent data
 └─ Can add/modify entries

LOCKED
 ├─ Can view entries
 ├─ Cannot post new entries
 └─ Can reopen to OPEN (if needed)

CLOSED
 ├─ Read-only archive
 ├─ Cannot reopen
 └─ Requires CFO approval to modify
```

**Notes**:
- period field human-readable (e.g., "2025-01" for January 2025)
- Cannot post to locked or closed periods
- Locking prevents new data entry but allows viewing
- Closing is irreversible (requires executive approval to modify)

---

## Domain 2: Source Documents (Bukti Transaksi)

Invoices and payments are the "proof" of transactions.

### Invoice (Billing Document)

**Purpose**: Record of what is owed (AR) or what is payable (AP)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique invoice identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Issuer (for AR) or buyer (for AP) |
| `counterparty_tenant_id` | UUID | FK→Tenant | For inter-tenant invoices (buyer/supplier) |
| `contract_id` | UUID | FK→BusinessContract | If from business contract |
| `invoice_number` | VARCHAR | NOT NULL | "INV-2025-001", "INV-LAU-001" |
| `type` | ENUM | NOT NULL | 'AR' (Accounts Receivable), 'AP' (Accounts Payable) |
| `status` | ENUM | NOT NULL | 'draft', 'approved', 'posted', 'paid', 'voided', 'reversed' |
| `amount` | DECIMAL(18,2) | NOT NULL, >0 | Total invoice amount |
| `currency` | VARCHAR | NOT NULL, DEFAULT 'IDR' | "IDR", "USD", etc. |
| `description` | TEXT | | What invoice is for |
| `issued_at` | TIMESTAMP | NOT NULL | When invoice was created/issued |
| `due_at` | DATE | NOT NULL | Payment due date |
| `paid_at` | TIMESTAMP | | When fully paid |
| `posted_at` | TIMESTAMP | | When GL entry posted |
| `approval_required` | BOOLEAN | NOT NULL | Whether amount exceeds approval threshold |
| `approved_by` | UUID | FK→User | Who approved it |
| `approved_at` | TIMESTAMP | | When approved |
| `voided_at` | TIMESTAMP | | If voided, when |
| `reversed_at` | TIMESTAMP | | If reversed, when |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `created_by` | UUID | FK→User | Who created |

**Unique Constraint**:
- (tenant_id, invoice_number) - One number per tenant

**Relationships**:
```
Invoice 1--* Payment
Invoice 1--* InvoiceTax
Invoice 1--* JournalEntry (when posted)
```

**Status Workflow for AR Invoice**:
```
DRAFT
  ├─ Can edit
  └─ → APPROVED (if approval not required)
     or → APPROVAL_PENDING (if amount high)

APPROVAL_PENDING
  ├─ Awaiting approver decision
  ├─ → APPROVED (after approval)
  └─ → REJECTED (denied)

APPROVED
  ├─ Ready to post to GL
  └─ → POSTED (journal entry created)

POSTED
  ├─ GL entry recorded
  ├─ Awaiting payment
  ├─ → PAID (payment received)
  └─ → REVERSED (if error, creates reversing entry)

PAID
  └─ Complete (no further action)

REVERSED
  └─ Complete (error correction)

VOIDED
  └─ Cancelled (not used)
```

**Notes**:
- AR: tenant_id = seller, counterparty_tenant_id = buyer (nullable for internal guests)
- AP: tenant_id = buyer, counterparty_tenant_id = supplier
- counterparty_tenant_id ONLY set for inter-tenant invoices
- approval_required determined by threshold rule (e.g., >$5K)

---

### Payment (Payment Allocation)

**Purpose**: Record of payment applied to invoice

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique payment record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant recorded payment |
| `invoice_id` | UUID | FK→Invoice, NOT NULL | Which invoice being paid |
| `payment_number` | VARCHAR | NOT NULL | "PAY-2025-001" |
| `amount` | DECIMAL(18,2) | NOT NULL, >0 | Payment amount |
| `currency` | VARCHAR | NOT NULL | Currency of payment |
| `method` | ENUM | NOT NULL | 'cash', 'check', 'transfer', 'card', 'gateway' |
| `reference` | VARCHAR | | Bank reference, check number, transaction ID |
| `status` | ENUM | NOT NULL | 'recorded', 'cleared', 'reversed' |
| `paid_at` | TIMESTAMP | NOT NULL | When payment was made/received |
| `cleared_at` | TIMESTAMP | | When bank confirmed payment |
| `reconciled_at` | TIMESTAMP | | When matched to bank statement |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `created_by` | UUID | FK→User | Who recorded payment |

**Constraint**: amount ≤ invoice.outstanding_amount (prevent overpayment)

**Notes**:
- Multiple payments can apply to one invoice
- Partial payments allowed
- status tracks reconciliation (recorded → cleared → reconciled)
- reference links to external payment system

---

## Domain 3: Journal Engine

The core of double-entry accounting: balanced entries posted to GL.

### JournalEntry (Transaction Header)

**Purpose**: Header for a double-entry transaction (one entry = 2+ lines)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique journal entry identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `period_id` | UUID | FK→AccountingPeriod, NOT NULL | Which period |
| `entry_date` | DATE | NOT NULL | Effective date of transaction |
| `source_type` | ENUM | NOT NULL | 'invoice', 'payment', 'adjustment', 'correction' |
| `source_id` | VARCHAR | | Polymorphic FK (invoice_id, payment_id, adjustment_id) |
| `description` | VARCHAR | NOT NULL | What this entry is for ("Room revenue checkout", etc.) |
| `status` | ENUM | NOT NULL | 'draft', 'posted', 'reversed' |
| `is_reversal` | BOOLEAN | NOT NULL, DEFAULT FALSE | True if this reverses prior entry |
| `reverses_entry_id` | UUID | FK→JournalEntry | If reversal, which entry is reversed |
| `posted_at` | TIMESTAMP | NOT NULL | When posted to GL |
| `posted_by` | UUID | FK→User | Who posted |
| `created_at` | TIMESTAMP | NOT NULL | Entry creation |

**Constraints**:
- Cannot post to LOCKED or CLOSED period
- period_id must match entry_date (date in period)
- is_reversal = TRUE implies reverses_entry_id NOT NULL

**Relationships**:
```
JournalEntry 1--* JournalLine
AccountingPeriod 1--* JournalEntry
```

**Notes**:
- Immutable once posted (no updates allowed)
- All entries must be balanced (total debit = total credit)
- source_id links back to originating document (invoice, payment, etc.)

---

### JournalLine (Transaction Detail)

**Purpose**: Individual debit/credit line within a journal entry

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique line identifier |
| `journal_entry_id` | UUID | FK→JournalEntry, NOT NULL | Which entry this belongs to |
| `account_id` | UUID | FK→ChartOfAccount, NOT NULL | Which GL account |
| `debit_amount` | DECIMAL(18,2) | ≥0 | Debit side (one of debit/credit only) |
| `credit_amount` | DECIMAL(18,2) | ≥0 | Credit side (one of debit/credit only) |
| `description` | VARCHAR | | Line description (optional) |
| `created_at` | TIMESTAMP | NOT NULL | Line creation |

**Constraints**:
- EXACTLY ONE of debit_amount or credit_amount is non-zero (not both, not neither)
- Account must be in same tenant as JournalEntry
- account_id must not be a header account (is_header = false)

**Double-Entry Example**:
```
JournalEntry: "Guest checkout"
  JournalLine 1: DR 1130 (AR) $1,500,000
  JournalLine 2: CR 4100 (Room Revenue) $1,500,000
Total Debit = Total Credit = $1,500,000 ✓
```

**Notes**:
- Immutable (no updates to posted lines)
- Always in same tenant as JournalEntry
- Account balance calculated by: SUM(credit) - SUM(debit) for the account

---

## Domain 4: Adjustments & Corrections

Making corrections to accounting records.

### Adjustment (Correction/Accrual)

**Purpose**: Post accruals, accrued expenses, or manual corrections

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique adjustment record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `reason` | VARCHAR | NOT NULL | Why adjustment needed ("Month-end accrual", "Correction of error", etc.) |
| `status` | ENUM | NOT NULL | 'draft', 'approved', 'posted' |
| `approved_by` | UUID | FK→User | Who approved it |
| `approved_at` | TIMESTAMP | | When approved |
| `posted_at` | TIMESTAMP | | When GL entry posted |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Relationships**:
```
Adjustment 1--* AdjustmentLine
Adjustment 1--1 JournalEntry (when posted)
```

**Notes**:
- Adjustments are NOT reversals; they create new GL entries
- Common adjustments: depreciation, accrued expenses, bad debt provision
- Must be approved before posting

---

### AdjustmentLine (Adjustment Detail)

**Purpose**: Individual lines within an adjustment

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique line identifier |
| `adjustment_id` | UUID | FK→Adjustment, NOT NULL | Which adjustment |
| `account_id` | UUID | FK→ChartOfAccount, NOT NULL | Which GL account |
| `debit_amount` | DECIMAL(18,2) | ≥0 | Debit side |
| `credit_amount` | DECIMAL(18,2) | ≥0 | Credit side |
| `description` | VARCHAR | | Line description |

**Constraint**: EXACTLY ONE of debit_amount or credit_amount is non-zero

---

## Domain 5: AR / AP Detail (Subledger)

Detailed tracking of receivables and payables.

### AccountsReceivable (AR Subledger)

**Purpose**: Track what customers owe (updated as invoices/payments processed)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique AR record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Seller tenant |
| `invoice_id` | UUID | FK→Invoice, NOT NULL | Which invoice |
| `customer_tenant_id` | UUID | FK→Tenant | If inter-tenant (buyer tenant) |
| `original_amount` | DECIMAL(18,2) | NOT NULL | Invoice amount |
| `outstanding_amount` | DECIMAL(18,2) | NOT NULL | Remaining to collect |
| `status` | ENUM | NOT NULL | 'open', 'partial', 'paid', 'disputed' |
| `days_overdue` | INT | | Calculated: days since due date |
| `aging_bucket` | VARCHAR | | Calculated: '0-30', '31-60', '61-90', '90+' |
| `last_payment_at` | TIMESTAMP | | When last payment received |

**Triggers**:
- Updated when invoice finalized
- Updated when payment recorded
- days_overdue, aging_bucket recalculated daily

**Notes**:
- Read-only view (updated by triggers, not direct updates)
- Used for aging reports, collection management

---

### AccountsPayable (AP Subledger)

**Purpose**: Track what supplier must be paid

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique AP record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Buyer tenant |
| `invoice_id` | UUID | FK→Invoice, NOT NULL | Which invoice |
| `supplier_tenant_id` | UUID | FK→Tenant, NOT NULL | Supplier tenant |
| `original_amount` | DECIMAL(18,2) | NOT NULL | Invoice amount |
| `outstanding_amount` | DECIMAL(18,2) | NOT NULL | Remaining to pay |
| `status` | ENUM | NOT NULL | 'open', 'partial', 'paid', 'disputed' |
| `days_overdue` | INT | | Calculated: days since due date |
| `aging_bucket` | VARCHAR | | Calculated: '0-30', '31-60', '61-90', '90+' |
| `last_payment_at` | TIMESTAMP | | When last payment made |

**Notes**:
- Updated by triggers (not direct updates)
- Used for cash planning, supplier management

---

## Domain 6: Tax & Withholding (Optional)

For tax compliance and reporting.

### Tax (Tax Configuration)

**Purpose**: Define tax types and rates

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique tax record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `name` | VARCHAR | NOT NULL | Tax name ("VAT", "PPN", "PPh", etc.) |
| `rate` | DECIMAL(5,2) | NOT NULL | Tax rate (0-100) |
| `tax_type` | ENUM | | 'income', 'sales', 'withholding' |
| `is_active` | BOOLEAN | NOT NULL | Currently applicable |
| `created_at` | TIMESTAMP | NOT NULL | When configured |

**Relationships**:
```
Tax 1--* InvoiceTax
```

---

### InvoiceTax (Tax on Invoice)

**Purpose**: Tax amounts applied to specific invoices

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique record |
| `invoice_id` | UUID | FK→Invoice, NOT NULL | Which invoice |
| `tax_id` | UUID | FK→Tax, NOT NULL | Which tax type |
| `tax_amount` | DECIMAL(18,2) | NOT NULL | Calculated tax amount |
| `tax_rate` | DECIMAL(5,2) | NOT NULL | Rate at time of invoice |

**Calculation**:
```
tax_amount = invoice_amount * (tax_rate / 100)
```

---

## Domain 7: Approval & Audit Links

Integration with approval workflows and audit trail.

### ApprovalRequest Link

**Purpose**: Link to approval workflows for high-value invoices

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique approval request |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `entity_type` | ENUM | NOT NULL | 'invoice', 'journal', 'adjustment' |
| `entity_id` | UUID | NOT NULL | Which entity (invoice_id, etc.) |
| `amount` | DECIMAL(18,2) | | Amount being approved |
| `required_role` | ENUM | NOT NULL | 'admin', 'owner' (minimum role) |
| `status` | ENUM | NOT NULL | 'pending', 'approved', 'rejected' |
| `requested_by` | UUID | FK→User | Who requested approval |
| `approved_by` | UUID | FK→User | Who approved |
| `requested_at` | TIMESTAMP | NOT NULL | When requested |
| `decided_at` | TIMESTAMP | | When decision made |

**Threshold Rules** (Examples):
```
Amount < $5,000        → Auto-approved
$5,000 - $50,000       → Admin approval required
$50,000 - $500,000     → Owner approval required
> $500,000             → CFO + Owner approval required
```

---

### AuditLog Link

**Purpose**: Link to immutable audit trail (see REF-08)

All accounting transactions logged:
```
action: 'post', 'approve', 'reverse'
entity_type: 'invoice', 'journal', 'payment'
entity_id: UUID
actor: user or system
created_at: timestamp
```

---

## Domain 8: Boundary Rules (Strict)

### ❌ Hard Rules (Cannot Be Broken)

| Rule | Why | Consequence |
|------|-----|-------------|
| **PMS/POS cannot directly create JournalLine** | Prevents accounting bypass | GL inconsistency, audit trail gaps |
| **Balance not stored (only calculated)** | Maintain append-only property | Recalculates from entries |
| **Cannot edit journal after posting** | Audit trail immutability | Reversals only for corrections |
| **Cannot post to closed period** | Period control enforcement | Error raised, transaction rejected |
| **Cannot post unbalanced entry** | Double-entry requirement | Validation error |
| **Debit and Credit both zero** | Meaningless transaction | Validation error |

### ✅ Allowed Operations

| Operation | How |
|-----------|-----|
| **Fix posted entry** | Create reversing journal entry (new, not edit) |
| **Add to locked period** | Reopen period (requires approval), add entry, relock |
| **Adjust invoice** | Create adjustment record (new entry) |
| **Reopen closed period** | Requires CFO approval + audit review |

---

## Domain 9: Integration Points (Other Domains)

How operational domains feed into Accounting.

### From PMS

**PMS generates**:
- Guest checkout → Invoice (AR for guest folio)
- Room charge posting → updates Invoice amount
- Night audit → triggers GL posting via Invoice.Finalized event

**Flow**:
```
PMS.Guest.CheckedOut
  ↓ (event)
Accounting.Adapter consumes
  ↓
Creates Invoice (AR)
  ↓
Invoice.Finalized (event)
  ↓
GL.Adapter posts JournalEntry (DR AR, CR Revenue)
```

---

### From POS

**POS generates**:
- Sale transaction → Invoice (AR for customer)
- Cash payment → Payment record

**Flow**:
```
POS.SaleCompleted
  ↓
Accounting.Adapter creates Invoice
  ↓
Payment immediately recorded (cash)
  ↓
GL posts (DR Cash, CR Revenue)
```

---

### From Inventory

**Inventory generates**:
- Stock usage (COGS) → Adjustment
- Stock movement → COGS recognition

**Flow**:
```
Inventory.StockUsed
  ↓
Accounting.Adapter creates Adjustment
  ↓
GL posts (DR COGS, CR Inventory)
```

---

### From Procurement (Supplier)

**Supplier generates**:
- Purchase order issued → (tracked, not GL yet)
- Supplier invoice → Invoice (AP)
- Payment → Payment record

**Flow**:
```
Supplier.InvoiceIssued (event)
  ↓
Accounting.Adapter creates Invoice (AP)
  ↓
Approval workflow if >threshold
  ↓
GL posts (DR Expense, CR AP)
  ↓
Payment recorded later
  ↓
GL posts (DR AP, CR Cash)
```

---

## Data Isolation & Tenant Rules

### All Accounting Data Tenant-Scoped

```sql
-- All queries must include tenant_id:

SELECT * FROM journal_entries
WHERE tenant_id = $1  -- MANDATORY
  AND period_id = $2;

-- NO queries without tenant context:
SELECT * FROM journal_entries;  -- WRONG
```

### Cross-Tenant Invoices

Only allowed via BusinessContract:

```sql
-- Inter-tenant invoice (AR for supplier, AP for buyer)
INSERT INTO invoices (
  tenant_id,                    -- Supplier's perspective
  counterparty_tenant_id,       -- Buyer's perspective
  contract_id,                  -- Must reference contract
  type,                         -- AR (supplier is issuer)
  ...
)
```

---

## Compliance Checklist

When designing accounting features:

- [ ] All GL accounts in ChartOfAccount
- [ ] Period validation before posting (must be OPEN)
- [ ] Journal entry balanced (debit = credit)
- [ ] No direct balance modifications
- [ ] Corrections via reversals only
- [ ] Approval workflow triggered for thresholds
- [ ] Audit log records all changes
- [ ] Tenant isolation enforced
- [ ] Inter-tenant invoices have contract
- [ ] Period locked after month-end
- [ ] AR/AP aging calculated daily
- [ ] Tests verify double-entry integrity

---

## Related Documents

- **REF-08**: Entity Relationship Model (Core) — Foundation model
- **REF-09**: Report Map — Accounting reports dependent on these entities
- **ARCH-12**: Read Model & CQRS Pattern — How read models consume accounting events
- **SPEC-10**: Accounting Core Process & Workflow — Business process for GL posting
- **SEC-03**: Authorization, Approval & Audit — Approval workflows and audit trail
- **STD-19**: Event Contract Standard — Events that trigger accounting transactions
