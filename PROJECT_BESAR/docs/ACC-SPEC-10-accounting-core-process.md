# SPEC-10: Accounting Core Process & Workflow

This document specifies the **core operational workflow** of the Accounting module in PROJECT_BESAR. It defines the business process for invoice generation, payment recording, journal posting, reconciliation, and period closing (financial statement preparation).

**Related Specs:**
- SPEC-09 (PMS Core Process) — Example of how PMS generates invoices for accounting to consume
- POS Core Process — Example of how POS generates sales for accounting to consume
- Inventory Integration — Example of how Inventory generates COGS for accounting to consume
- **Key Point**: Accounting processes invoices from ANY operational module (PMS, POS, Inventory, Procurement, etc.). Accounting module is NOT dependent on PMS specifically.

---

## Key Principles

1. **Immutable Ledger**
   - Journal entries never modified after posting
   - Corrections use reversals, not edits
   - Audit trail traces all changes

2. **Double-Entry Bookkeeping**
   - Every transaction has debit and credit
   - Ledger always balances (debits = credits)
   - No single-entry postings allowed

3. **Append-Only Core Data**
   - Invoices, payments, journal entries append-only
   - No deletion after posting
   - Enables audit trail and forensics

4. **Event-Driven Integration**
   - Operational modules (PMS, POS) emit events
   - Accounting system consumes events asynchronously
   - Journal entries created from events, not manual entry

5. **Period Lock**
   - Closing period prevents changes to closed data
   - No backdate posting after period closed
   - Ensures financial statement integrity

6. **Accounting is Single Source of Truth**
   - Ledger is authoritative record
   - UI is view/entry mechanism, not editor
   - All changes go through ledger service

---

## Invoice States

```
┌──────────────┐
│   DRAFT      │  Invoice created but not yet confirmed
└──────┬───────┘
       │ (Staff confirms or auto-posting from event)
       ▼
┌──────────────┐
│   OPEN       │  Invoice posted to ledger, awaiting payment
└──────┬───────┘
       │ (Payment received in full)
       ▼
┌──────────────┐
│   PAID       │  Fully paid, folio closed
└──────┬───────┘
       │ (Refund issued or correction made)
       ▼
┌──────────────┐
│   REVERSED   │  Corrected via reversal entry
└──────────────┘

Alternative path from OPEN:
       │ (Partial payment received)
       ▼
┌──────────────────┐
│ PARTIALLY_PAID   │  Some payment received, balance outstanding
└──────┬───────────┘
       │ (Final payment received)
       ▼
    PAID
```

---

## Journal Entry States

```
┌──────────────┐
│   DRAFT      │  Entry prepared but not yet validated
└──────┬───────┘
       │ (Validation passed)
       ▼
┌──────────────┐
│   POSTED     │  Entry in ledger, immutable
└──────┬───────┘
       │ (Reversal journal created to correct)
       ▼
┌──────────────┐
│  REVERSED    │  Original entry marked reversed, reversal entry posted
└──────────────┘
```

---

## Accounting Period States

```
┌──────────────┐
│   OPEN       │  Period receiving transactions, can post entries
└──────┬───────┘
       │ (Period close process starts)
       ▼
┌──────────────┐
│  CLOSING     │  Period close in progress, limited modifications
└──────┬───────┘
       │ (Close process completes, verified)
       ▼
┌──────────────┐
│   CLOSED     │  Period locked, no new transactions
└──────────────┘
```

---

## Main Flow: Complete Accounting Cycle

### Step 1: Invoice Generation

**Trigger**: Operational module (PMS, POS, etc.) completes transaction and publishes event

**Actors**: Source System (PMS/POS), Accounting System, Guest/Customer

**Steps**:

#### 1.1: Source System Emits Event
PMS generates guest folio, publishes event:
```json
{
  "event_type": "guest.checked_out",
  "event_id": "evt-12345",
  "tenant_id": "org-123",
  "folio_id": "folio-456",
  "guest_id": "guest-789",
  "timestamp": "2025-12-27T11:00:00Z",
  "data": {
    "room_charge": 200.00,
    "ancillary_charges": 86.00,
    "subtotal": 286.00,
    "tax": 28.60,
    "grand_total": 314.60,
    "payment_method": "CREDIT_CARD",
    "amount_paid": 314.60
  }
}
```

#### 1.2: Accounting System Consumes Event
1. Accounting service receives event
2. Validates event signature (HMAC)
3. Checks for duplicates (idempotency key = event_id + accounting-service)
4. Extracts invoice data from event

#### 1.3: Create Invoice Record
System creates **Invoice** record:
```
Invoice {
  id: 'inv-001',
  invoice_date: '2025-12-27',
  due_date: '2026-01-10',
  tenant_id: 'org-123',
  customer_id: 'guest-789',
  source_folio_id: 'folio-456',
  source_event_id: 'evt-12345',
  billing_period: '2025-12-25 to 2025-12-27',

  line_items: [
    {
      description: 'Room 101 - 2 nights',
      account_code: '4100',  // Room Revenue
      amount: 200.00,
      quantity: 2,
      unit_price: 100.00
    },
    {
      description: 'Restaurant & Minibar',
      account_code: '4200',  // Ancillary Revenue
      amount: 86.00
    }
  ],

  subtotal: 286.00,
  tax: 28.60,
  tax_account_code: '2300',  // Tax Payable
  total: 314.60,

  payment_method: 'CREDIT_CARD',
  status: 'DRAFT',
  created_at: '2025-12-27T11:05:00Z',
  created_by: 'system'
}
```

#### 1.4: Validate Invoice
System validates:
- ✅ All line items have valid account codes
- ✅ Quantities and amounts are reasonable
- ✅ Totals reconcile (subtotal + tax = total)
- ✅ Customer/tenant relationship valid
- ✅ Period is still OPEN (not closed)

#### 1.5: Post Invoice to Ledger
If validation passes:
1. Invoice status → OPEN
2. Generates event: `InvoicePosted`

If validation fails:
1. Invoice status → REJECTED
2. Alert sent to accounting staff
3. Manual review required

**Output**: Invoice posted to ledger, ready for payment recording

---

### Step 2: Payment Recording

**Trigger**: Payment received from guest or payment gateway notification

**Actors**: Payment Gateway, Accounting System, Staff (optional for cash), Customer

**Scenarios**:

#### 2A: Full Payment (Single Transaction)

**Example**: Guest paid $314.60 with credit card at check-out

**Steps**:
1. Payment Gateway sends confirmation:
   ```json
   {
     "event_type": "payment.received",
     "payment_id": "pay-98765",
     "invoice_id": "inv-001",
     "tenant_id": "org-123",
     "amount": 314.60,
     "payment_method": "CREDIT_CARD",
     "transaction_id": "stripe-xyz789",
     "timestamp": "2025-12-27T11:02:00Z"
   }
   ```

2. Accounting system records **Payment**:
   ```
   Payment {
     id: 'pay-98765',
     invoice_id: 'inv-001',
     payment_date: '2025-12-27',
     amount: 314.60,
     payment_method: 'CREDIT_CARD',
     reference: 'stripe-xyz789',
     status: 'COMPLETED',
     recorded_at: '2025-12-27T11:03:00Z'
   }
   ```

3. System updates Invoice:
   - Invoice status: PAID
   - Paid amount: 314.60
   - Balance due: 0.00

4. System generates event: `InvoicePaid`

**Output**: Invoice marked as PAID, payment recorded

#### 2B: Partial Payment

**Example**: Guest pays $200 now, balance due later

**Steps**:
1. Staff records partial payment (cash or manual entry):
   ```
   Payment {
     invoice_id: 'inv-001',
     amount: 200.00,
     payment_date: '2025-12-27',
     status: 'COMPLETED'
   }
   ```

2. System updates Invoice:
   - Invoice status: PARTIALLY_PAID
   - Paid amount: 200.00
   - Balance due: 114.60

3. Invoice remains open, awaiting additional payment

4. System generates event: `InvoicePartiallyPaid`

**Follow-up**:
- System sends reminder to customer (due date approaching)
- If payment still outstanding after due date:
  - Mark as OVERDUE
  - Send collection notice

#### 2C: Cash Payment (Manual Entry)

**Example**: Guest pays $314.60 in cash

**Steps**:
1. Staff receives cash and records in receipt book
2. Staff enters payment in Accounting system:
   - Invoice ID: inv-001
   - Amount: $314.60
   - Payment method: CASH
   - Reference: receipt number

3. System records payment (same as credit card)

4. Cash is aggregated with other cash payments for daily bank deposit

---

### Step 3: Journal Posting

**Trigger**: Invoice posted (OPEN status) and/or Payment received

**Actors**: Accounting System (automated), Ledger

**Key Concept**: Double-entry bookkeeping
- Every transaction = debit one account, credit another account
- Debits must = Credits (balanced)
- Posted to General Ledger (immutable)

#### 3.1: Post Invoice as AR (Accounts Receivable)

When invoice posted (OPEN status):
```
Journal Entry {
  entry_id: 'je-001',
  entry_date: '2025-12-27',
  period: '2025-12',
  description: 'Guest checkout - Room charges and taxes',
  status: 'POSTED',
  posted_at: '2025-12-27T11:05:00Z',

  lines: [
    {
      account_code: '1200',   // Accounts Receivable
      debit: 314.60,
      credit: 0,
      description: 'Invoice inv-001 from guest-789'
    },
    {
      account_code: '4100',   // Room Revenue
      debit: 0,
      credit: 200.00,
      description: 'Room revenue 2 nights'
    },
    {
      account_code: '4200',   // Ancillary Revenue
      debit: 0,
      credit: 86.00,
      description: 'Restaurant and minibar'
    },
    {
      account_code: '2300',   // Tax Payable
      debit: 0,
      credit: 28.60,
      description: 'Sales tax collected'
    }
  ],

  total_debits: 314.60,
  total_credits: 314.60,
  balanced: true
}
```

**Validation**:
- ✅ Total debits = Total credits (314.60 = 314.60)
- ✅ Entry balances
- ✅ All accounts valid
- ✅ Period is OPEN

#### 3.2: Post Payment as Cash Receipt

When payment received:
```
Journal Entry {
  entry_id: 'je-002',
  entry_date: '2025-12-27',
  period: '2025-12',
  description: 'Payment received - Invoice inv-001',
  status: 'POSTED',
  posted_at: '2025-12-27T11:05:00Z',

  lines: [
    {
      account_code: '1000',   // Cash / Bank
      debit: 314.60,
      credit: 0,
      description: 'Payment from guest-789, card stripe-xyz789'
    },
    {
      account_code: '1200',   // Accounts Receivable
      debit: 0,
      credit: 314.60,
      description: 'Payment for invoice inv-001'
    }
  ],

  total_debits: 314.60,
  total_credits: 314.60,
  balanced: true
}
```

#### 3.3: Tax Accrual (if using accrual accounting)

For tax, an additional entry may be created:
```
Journal Entry {
  entry_id: 'je-003',
  description: 'Tax accrual - Invoice inv-001',

  lines: [
    {
      account_code: '5100',   // Tax Expense (or can defer)
      debit: 28.60,
      credit: 0
    },
    {
      account_code: '2300',   // Tax Payable
      debit: 0,
      credit: 28.60
    }
  ]
}
```

(Note: Tax treatment depends on policy—accrual vs. cash basis)

---

### Step 4: Reconciliation

**Trigger**: Daily or periodic (weekly/monthly)

**Actors**: Accounting System (automated), Accounting Staff (exception handling)

**Steps**:

#### 4.1: Three-Way Match
System verifies:
1. **Invoice** ↔ **Payment** ↔ **Journal Entry**
   - Amount in invoice = amount paid = amount in journal
   - Dates are consistent
   - Source references match (folio ID, payment gateway reference)

#### 4.2: Accounts Reconciliation
For each general ledger account:
1. Sum all journal entry lines for account (period)
2. Get beginning balance (from previous period)
3. Calculate ending balance = beginning + debits - credits
4. Compare with subledger balance (AR, AP, cash)
5. Investigate discrepancies

**Example**:
```
Account 1200 (Accounts Receivable):
  Beginning balance (2025-11-30): $1,500.00
  Period debits (invoices):        +$314.60
  Period credits (payments):        -$200.00
  Ending balance (2025-12-31):     $1,614.60

  Subledger verification:
    - Invoice inv-001: $314.60 (partial payment, balance: $114.60)
    - Previous AR:     $1,500.00
    ✅ Matches!
```

#### 4.3: Bank Reconciliation
If period includes bank statement date:
1. Get bank statement (account activity from bank)
2. Match cleared checks/deposits to journal entries
3. Identify outstanding items (not yet cleared)
4. Verify bank balance = accounting record

#### 4.4: Flag Exceptions
If discrepancy found:
- Flag entry for manual review
- Send alert to accounting staff
- Document exception with reason
- Prevent period close until resolved

**Common Exceptions**:
- Invoice posted but payment never received (overdue)
- Payment received for invoice not yet posted (customer prepayment)
- Amount mismatch (customer paid different amount)
- Duplicate entry (same invoice/payment posted twice)

---

### Step 5: Period Closing

**Trigger**: Accounting staff initiates close (e.g., end of month)

**Actors**: Accounting Staff, Accounting System, Owner/Manager (approval)

**Prerequisites**:
- All invoices for period posted
- All payments for period recorded
- Reconciliation complete (no exceptions)
- Period status is OPEN

**Steps**:

#### 5.1: Pre-Close Verification
System checks:
```
✅ All invoices posted
✅ All payments recorded
✅ Reconciliation complete
✅ No exceptions remain
✅ Accounts balance (total debits = total credits)
✅ No unposted entries in period
✅ All taxes accounted for
```

If all pass → proceed to closing
If any fail → halt and alert staff to resolve

#### 5.2: Generate Trial Balance

System generates trial balance by summing all posted journal entries for the period.

**Entry Flow Recap**:
1. Invoice posted: DR AR 314.60, CR Room Revenue 200, CR Ancillary 86, CR Tax Payable 28.60
2. Payment posted: DR Cash 314.60, CR AR 314.60

**Correct Trial Balance - 2025-12** (after both entries):
```
Account Code | Description              | Debit     | Credit    | Balance
1000         | Cash                     | 314.60    |           | 314.60 D
1200         | Accounts Receivable      |           | 314.60    | 0.00
2300         | Tax Payable              |           | 28.60     | 28.60 C
4100         | Room Revenue             |           | 200.00    | 200.00 C
4200         | Ancillary Revenue        |           | 86.00     | 86.00 C
---          | TOTALS                   | 314.60    | 314.60    | ✅ BALANCED
```

**SQL Query to Generate Trial Balance**:
```sql
SELECT
  a.account_code,
  a.account_name,
  COALESCE(SUM(CASE WHEN jl.debit_amount IS NOT NULL THEN jl.debit_amount ELSE 0 END), 0) AS total_debit,
  COALESCE(SUM(CASE WHEN jl.credit_amount IS NOT NULL THEN jl.credit_amount ELSE 0 END), 0) AS total_credit,
  COALESCE(SUM(CASE WHEN jl.debit_amount IS NOT NULL THEN jl.debit_amount ELSE -jl.credit_amount END), 0) AS balance
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
WHERE je.tenant_id = $1  -- Multi-tenant isolation (MANDATORY)
  AND je.period_id = $2  -- Specific period
  AND je.posted_at IS NOT NULL  -- Only posted entries
  AND a.tenant_id = $1  -- Account belongs to tenant
  AND a.is_header = FALSE  -- Only posting accounts (leaf nodes), exclude summary accounts
GROUP BY a.id, a.account_code, a.account_name
ORDER BY a.account_code;
```

**Key Points**:
- ✅ Trial balance MUST be filtered by tenant_id (multi-tenant isolation)
- ✅ Trial balance MUST be filtered by period_id
- ✅ Only POSTED entries included (posted_at IS NOT NULL)
- ✅ Only POSTING accounts included (is_header = FALSE) - excludes summary accounts
- ✅ Debits and credits must equal (if not, GL integrity issue)
- ❌ Draft/unposted entries excluded
- ❌ Header/summary accounts excluded

#### 5.3: Generate Financial Statements

> **Status**: ✅ Approved (2025-12-07)

System generates three primary financial statements from trial balance:

**A. Income Statement (P&L)**

Purpose: Show profitability for the period

```sql
-- Income Statement Query
SELECT
  'Revenue' AS section,
  account_name,
  SUM(credit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'REVENUE')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

UNION ALL

SELECT
  'Cost of Goods Sold' AS section,
  account_name,
  SUM(debit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'COGS')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

UNION ALL

SELECT
  'Operating Expenses' AS section,
  account_name,
  SUM(debit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'EXPENSE')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

ORDER BY section, account_name;

-- Post-process to calculate:
-- Gross Profit = Revenue - COGS
-- Operating Income = Gross Profit - Operating Expenses
-- Net Income = Operating Income ± Other Income/Expense
```

**B. Balance Sheet (Statement of Financial Position)**

Purpose: Show asset, liability, and equity positions at period-end

```sql
-- Balance Sheet Query
SELECT
  'Assets' AS section,
  account_name,
  SUM(debit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'ASSET')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

UNION ALL

SELECT
  'Liabilities' AS section,
  account_name,
  SUM(credit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'LIABILITY')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

UNION ALL

SELECT
  'Equity' AS section,
  account_name,
  SUM(credit_balance) AS amount
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
WHERE a.category_id IN (SELECT id FROM account_categories WHERE code = 'EQUITY')
  AND jl.period_id = $1
  AND a.tenant_id = $2
  AND a.is_header = FALSE
GROUP BY a.id, a.account_name

ORDER BY section, account_name;

-- Post-process to verify: Assets = Liabilities + Equity
```

**C. Cash Flow Statement (Optional - Phase 2)**

Purpose: Show cash movement (operating, investing, financing)

```
Note: Phase 1 does NOT require cash flow statement.
Deferred to Phase 2 once cash positioning becomes operational priority.

Future design: Allocate journal entries to three categories:
1. Operating Activities (changes in current assets/liabilities)
2. Investing Activities (asset purchases/sales)
3. Financing Activities (debt/equity changes)
```

**Statement Format Example (Income Statement)**

```
═══════════════════════════════════════════════════════════
                    ACME HOTEL - INCOME STATEMENT
                    Month Ended December 31, 2025
═══════════════════════════════════════════════════════════

REVENUE
  Room Revenue (RM)                    500,000.00
  Food & Beverage (FB)                 200,000.00
  Other Revenue                         50,000.00
                                      ───────────
  Total Revenue                        750,000.00

COST OF GOODS SOLD
  Food Purchases                       (80,000.00)
  Beverage Purchases                   (30,000.00)
                                      ───────────
  Total COGS                          (110,000.00)
                                      ───────────
GROSS PROFIT                           640,000.00

OPERATING EXPENSES
  Payroll (FO)                        (120,000.00)
  Housekeeping (HK)                    (80,000.00)
  Utilities                            (40,000.00)
  Marketing & Sales                    (30,000.00)
  Depreciation                         (15,000.00)
                                      ───────────
  Total Operating Expenses            (285,000.00)
                                      ───────────
OPERATING INCOME                       355,000.00

OTHER INCOME/EXPENSE
  Interest Expense                      (5,000.00)
  FX Gain                               10,000.00
                                      ───────────
  Total Other                            5,000.00
                                      ───────────
NET INCOME                             360,000.00
═══════════════════════════════════════════════════════════
```

**Key Validation Rules**

| Rule | Check | Action |
|---|---|---|
| **P&L Balance** | Revenue - COGS - Expenses = Net Income | Auto-calc, verify formula |
| **Balance Sheet** | Assets = Liabilities + Equity | Verify at period close |
| **Account Inclusion** | Only posting accounts (is_header=FALSE) | Exclude summary accounts |
| **Period Filtering** | All amounts from specified period only | Use period_id in WHERE clause |
| **Tenant Isolation** | Data must be filtered by tenant_id | MANDATORY multi-tenant rule |

#### 5.4: Accounting Staff Review
1. Accounting staff reviews trial balance
2. Reviews financial statements for reasonableness
3. Investigates any unusual balances
4. May request manager approval if large variances

#### 5.5: Lock Period
If approved:
1. Period status → CLOSED
2. Timestamp recorded
3. Approver identity recorded
4. Event: `PeriodClosed`

**Lock Effects**:
- ❌ No new journal entries for this period
- ❌ No invoice/payment posting to this period
- ✅ Can view historical data
- ✅ Can create reversing entries (if needed for correction)

#### 5.6: Post Closing
After close:
- Archive period data (to slower storage if desired)
- Generate PDF reports for filing/audit
- Send reports to stakeholders (Owner, Manager)
- Update dashboard with final results

**Output**: Period closed, financial statements generated, data locked

---

## Corrections & Reversals (With Approval Workflow)

### Approval-Required Correction Workflow

When accounting staff needs to correct a posted entry (e.g., wrong amount, wrong account), they MUST follow approval workflow:

**Scenario**: Invoice posted for $1,000 (wrong), should be $500

**Step 1: Staff Submits Correction Request**

Staff creates correction proposal (NOT a journal entry yet):

```
CorrectionRequest {
  id: "corr-req-001",
  tenant_id: "org-123",
  original_entry_id: "je-001",
  reason: "Invoice amount error: posted $1,000, should be $500",

  reversal_entry: {
    description: "Reversal of je-001 (incorrect amount)",
    lines: [
      { account: "1200", debit: 1000, credit: 0 },
      { account: "4100", debit: 0, credit: 1000 }
    ]
  },

  corrected_entry: {
    description: "Corrected invoice posting (replaces je-001)",
    lines: [
      { account: "1200", debit: 500, credit: 0 },
      { account: "4100", debit: 0, credit: 500 }
    ]
  },

  created_by: "staff-123",
  created_at: timestamp
}
```

**Step 2: Workflow Engine Triggers Approval**

Accounting system publishes:
```
Event: Approval.Submitted.v1
{
  workflow_instance_id: "wf-001",
  entity_type: "CorrectionRequest",
  entity_id: "corr-req-001",
  required_approval_level: "admin",  // Or "owner" for high amounts
  amount_affected: 500.00
}
```

**Step 3: Approver Reviews & Approves**

Admin reviews correction:
- Is the reason valid? ✅
- Are the entry amounts correct? ✅
- Does it balance? ✅
- Click "Approve"

```
Event: Approval.Approved.v1
{
  workflow_instance_id: "wf-001",
  entity_type: "CorrectionRequest",
  entity_id: "corr-req-001",
  approved_by: "admin-456",
  approved_at: timestamp,
  approval_reason: "Reviewed invoice, amount should be $500"
}
```

**Step 4: System Posts Both Entries**

Upon approval, system posts BOTH entries atomically:

```sql
-- Start transaction
BEGIN;

-- Post reversal entry (je-002)
INSERT INTO journal_entries (...) VALUES (...)
  WITH entry_id = 'je-002',
  status = 'POSTED',
  posted_at = NOW(),
  reverses_entry = 'je-001',
  reason = 'Correction: incorrect amount';

-- Post corrected entry (je-003)
INSERT INTO journal_entries (...) VALUES (...)
  WITH entry_id = 'je-003',
  status = 'POSTED',
  posted_at = NOW(),
  related_to = 'je-002',
  reason = 'Corrected posting';

-- Update original entry to mark reversed
-- NOTE: This is NOT an "edit" of financial data - only a status flag change
-- The financial amounts (debit/credit) REMAIN IMMUTABLE
UPDATE journal_entries
SET is_reversed = TRUE,
    related_to = 'je-002'  -- Link to reversal entry
WHERE id = 'je-001'
AND status = 'POSTED'
AND is_reversed = FALSE;  -- Prevent double-reversal

-- Create audit log entry
INSERT INTO audit_logs (...) VALUES (...)
  WITH action = 'correction_approved',
  original_entry = 'je-001',
  reversal_entry = 'je-002',
  corrected_entry = 'je-003';

COMMIT;
```

**CRITICAL GUARDRAIL: is_reversed Field Update**
```
RULE: Only status flags can be updated on POSTED entries
RULE: Financial amounts (debit/credit) MUST remain immutable forever
RULE: is_reversed can only transition FALSE → TRUE (never back to FALSE)
```

**What CAN be updated**:
- is_reversed: FALSE → TRUE (when valid reversal entry is posted)
- related_to: NULL → reversal_entry_id (link to reversal for audit trail)

**What CANNOT be updated**:
- debit, credit (financial amounts)
- account_id (which account affected)
- description (reason for entry)
- posted_at, posted_by (posting timestamp/user)

**Step 5: Final State**

GL now shows:
- je-001: REVERSED = TRUE, related_to = 'je-002' (original error)
- je-002: POSTED, status = REVERSAL (reversal, -$1,000)
- je-003: POSTED, status = CORRECTION (corrected, +$500)

Net GL impact: $500 (correct)
Audit trail: Shows original → reversal → correction chain

### Correction Approval Rules (LOCKED)

**Rule 1: All Corrections Require Approval**
- ❌ Staff cannot post reversing entries without approval
- ✅ Approval workflow MUST complete before posting
- ✅ Audit trail captures approver decision

**Rule 2: Approval Authority by Amount**

| Amount | Required Approval |
|--------|-------------------|
| < $1,000 | Admin (supervisor) |
| $1,000 - $10,000 | Admin (manager level) |
| > $10,000 | Owner (CFO/Director) |

**Rule 3: Approval Deadline**
- Correction requests expire after 7 days (auto-reject if not approved)
- Staff can resubmit after expiry

**Rule 4: No Manual Journal Entries**
- ❌ DO NOT allow staff to post reversal entries manually
- ✅ DO require CorrectionRequest → Approval → Automatic posting
- Purpose: Prevents unauthorized corrections

---

## Alternative Flows

### Flow A: Refund

**Trigger**: Guest requests refund or early checkout with refund

**Example**: Guest paid $314.60, entitled to $100 refund

**Steps**:

#### A.1: Create Refund Entry
Staff creates refund request:
```
Refund {
  id: 'rfnd-123',
  invoice_id: 'inv-001',
  original_payment: 314.60,
  refund_amount: 100.00,
  reason: 'Early checkout, prorated refund',
  requested_by: 'staff-456',
  requested_at: '2025-12-27T11:30:00Z'
}
```

#### A.2: Post Reversing Entry
System creates reversing journal entry:
```
Journal Entry {
  entry_id: 'je-004',
  related_entry: 'je-002',  // Original payment entry
  description: 'Refund - invoice inv-001',

  lines: [
    {
      account_code: '1200',   // AR
      debit: 100.00,
      credit: 0,
      description: 'Refund reversing original payment'
    },
    {
      account_code: '1000',   // Cash
      debit: 0,
      credit: 100.00,
      description: 'Refund to guest'
    }
  ]
}
```

#### A.3: Process Refund
1. System processes refund to original payment method
2. Records refund transaction
3. Updates invoice balance: 314.60 - 100 = 214.60

#### A.4: Audit Trail
Both original entry and refund entry remain in ledger:
- Original: je-002 (posted)
- Refund: je-004 (posted)
- Relationship: je-004 references je-002

**Output**: Refund processed, ledger balanced, audit trail maintained

---

### Flow B: Correction (Different Period)

**Trigger**: Error discovered in prior period (already closed)

**Example**: Invoice inv-001 was posted to December (wrong month), should be November

**Steps**:

#### B.1: Identify Error
Staff discovers:
- Invoice inv-001 has invoice_date = 2025-12-27
- But should be 2025-11-27 (November)
- November period is already closed

#### B.2: Create Correction Entry
System creates correction entry in current period:
```
Journal Entry {
  entry_id: 'je-005',
  type: 'CORRECTION',
  related_entries: ['je-001'],  // Original entry in November
  description: 'Correction - reallocate inv-001 from Dec to Nov',

  lines: [
    {
      account_code: '1200',   // AR
      debit: 0,
      credit: 314.60,
      description: 'Reverse Nov revenue incorrectly posted to Dec'
    },
    {
      account_code: '4100',   // Room Revenue
      debit: 200.00,
      credit: 0,
      description: 'Restore to November (prior period)'
    },
    {
      account_code: '4200',   // Ancillary
      debit: 86.00,
      credit: 0,
      description: 'Restore to November'
    },
    {
      account_code: '2300',   // Tax Payable
      debit: 28.60,
      credit: 0,
      description: 'Restore to November'
    }
  ]
}
```

This entry:
- Reverses the incorrect December posting
- Does NOT modify the original November entry
- Creates audit trail (related_entries)
- Allows November period to be restated if needed

**Alternative**: Create correction to original entry (if period still OPEN):
- If November not yet closed: post correction in November (preferred)
- If November closed: post correction in current period with reference

#### B.3: Document Reason
```
Correction {
  id: 'corr-123',
  entry_id: 'je-005',
  original_entry_id: 'je-001',
  reason: 'Invoice date error - should be Nov, not Dec',
  discovered_by: 'staff-456',
  approved_by: 'manager-789',
  approved_at: '2025-12-27T12:00:00Z'
}
```

**Output**: Error corrected, audit trail maintained, prior period impact documented

---

### Flow C: Partial Payment with Later Adjustment

**Trigger**: Invoice with partial payment, remainder paid later or written off

**Example**: Invoice $314.60, guest pays $200, owes $114.60

**Step 1: Record Partial Payment** (as in Step 2B)
- Invoice status: PARTIALLY_PAID
- Balance due: 114.60

**Step 2: Follow-up**
- Send payment reminder at due date
- If not paid by due date + grace period: mark OVERDUE
- If customer disputes: flag for resolution

**Step 3A: Full Payment Received**
- Guest pays remaining $114.60
- System records payment
- Invoice status: PAID
- No further action

**Step 3B: Partial Write-off** (unlikely but possible)
- Management decides to write off $50 of balance
- Customer still owes $64.60

Process:
1. Create write-off entry:
   ```
   Journal Entry {
     description: 'Write-off - uncollectible receivable',
     lines: [
       {
         account: '5200',  // Bad Debt Expense
         debit: 50.00
       },
       {
         account: '1200',  // AR
         credit: 50.00
       }
     ]
   }
   ```

2. Customer still owes $64.60 (unless further negotiation)

---

## Important Invariants

### Immutable Ledger
```
INVARIANT: Journal Entry with status = POSTED → cannot be modified
```
- Original entry cannot be changed
- Only reversals allowed
- All changes audited

### Double-Entry Balance
```
INVARIANT: All Journal Entries → total_debits = total_credits
```
- Every entry must balance
- No single-entry posting allowed
- System prevents unbalanced entries

### Invoice-Payment Correspondence
```
INVARIANT: Invoice total = Sum of Payments + Balance Due
```
- Invoice amount is authoritative
- Payments must correspond to invoices
- No orphan payments without invoice

### Period Lock
```
INVARIANT: Period with status = CLOSED → no new entries for this period
```
- Closed period is immutable
- Can only view historical data
- Reversals for corrections go to current period

### Audit Trail
```
INVARIANT: Every Journal Entry → has created_by, created_at, source_event_id
```
- Traces entry to original event
- Tracks who created and when
- Enables forensics

---

## Accounting Policies & Methods

### Revenue Recognition
- **Method**: Accrual (revenue recognized when service provided)
- **Timing**: Room revenue at check-in, ancillary at posting
- **Alternative**: Cash basis if policy requires

### Expense Recognition
- Matched to revenue period (accrual)
- Recorded when incurred, not when paid

### Tax Handling
- Sales tax: collected and held in Tax Payable
- Tax payable remitted monthly/quarterly per jurisdiction
- Tax entries are separate journal line items

---

## Integration with Operational Systems

| Source System | Event | Accounting Action |
|---------------|-------|-------------------|
| PMS | `GuestCheckedOut` | Post Invoice (AR + Revenue) |
| PMS | Folio charge | Update Invoice line items |
| POS | Sale completed | Post Invoice (AR + Revenue) |
| Payment Gateway | `PaymentReceived` | Post Payment (Cash + AR) |
| Inventory | Stock used | (Future: COGS entries) |

---

## Timing & Deadlines

| Activity | Timing | Notes |
|----------|--------|-------|
| Invoice posting | Real-time (from event) | Automated |
| Payment recording | Real-time (webhook) or batch | Depends on payment method |
| Daily reconciliation | End of business day | Automated with alerts |
| Period close | End of month | Manual, staff-initiated |
| Financial statements | Same day as period close | Draft, ready for approval |
| Statement finalization | Within 2 business days | Approved and filed |

---

## Data Structures

### Invoice
```typescript
interface Invoice {
  id: string;                         // inv-001
  invoice_date: Date;
  due_date: Date;
  tenant_id: string;
  customer_id: string;
  source_folio_id?: string;           // From PMS
  source_event_id: string;            // Event that triggered invoice

  line_items: LineItem[];

  subtotal: number;
  tax_amount: number;
  total: number;

  paid_amount: number;
  balance_due: number;

  status: "DRAFT" | "OPEN" | "PARTIALLY_PAID" | "PAID" | "OVERDUE" | "REVERSED" | "REJECTED";

  created_at: DateTime;
  created_by: string;
}

interface LineItem {
  description: string;
  account_code: string;               // GL account
  amount: number;
  quantity?: number;
  unit_price?: number;
}
```

### Payment
```typescript
interface Payment {
  id: string;                         // pay-98765
  invoice_id: string;
  payment_date: Date;
  amount: number;
  payment_method: "CREDIT_CARD" | "CASH" | "CHECK" | "BANK_TRANSFER" | "CORPORATE";
  reference: string;                  // Stripe transaction ID, check number, etc.
  status: "PENDING" | "COMPLETED" | "FAILED" | "REVERSED";

  recorded_at: DateTime;
  recorded_by: string;
}
```

### JournalEntry
```typescript
interface JournalEntry {
  id: string;                         // je-001
  entry_date: Date;
  period: string;                     // "2025-12" (year-month)
  description: string;

  lines: JournalLine[];

  total_debits: number;
  total_credits: number;
  balanced: boolean;

  status: "DRAFT" | "POSTED" | "REVERSED";

  source_event_id?: string;           // Event that triggered entry
  related_entry_id?: string;          // If reversal

  created_at: DateTime;
  created_by: string;
  posted_at?: DateTime;
  posted_by?: string;
}

interface JournalLine {
  account_code: string;               // GL account (1000, 4100, etc.)
  description: string;
  debit?: number;
  credit?: number;
}
```

---

## Related Documents

- **SPEC-09**: PMS Core Process — source of revenue transactions
- **BIZ-01, 02, 03**: Accounting domain documents — conceptual details
- **ARCH-07**: Design Patterns — CQRS pattern for accounting (separate read/write)
- **STD-13**: Fraud & Audit — audit trail and controls
- **BPMN #04**: Detailed swim lanes for accounting workflow
- **ERD #18**: Accounting domain entities (Invoice, Payment, JournalEntry, GLAccount)

---

## Implementation Checklist

- [ ] Invoice creation from events (automated)
- [ ] Invoice validation and posting
- [ ] Payment recording (card, cash, corporate)
- [ ] Journal entry posting (double-entry verified)
- [ ] Accounts Receivable subledger maintained
- [ ] Bank account reconciliation
- [ ] Three-way match (invoice-payment-journal)
- [ ] Period close process (verification → lock)
- [ ] Trial balance and financial statements generated
- [ ] Reversals for corrections implemented
- [ ] Audit trail captures source event for every entry
- [ ] Tax tracking and reporting
- [ ] Overdue invoice detection and alerts
- [ ] Immutability enforced (no deletion after posting)
- [ ] Event-driven architecture (accounting is consumer, not source)
