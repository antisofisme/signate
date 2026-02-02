# SPEC-10: Accounting Core Process & Workflow

This document specifies the **core operational workflow** of the Accounting module in ARSAKA_PANDAWA. It defines the business process for invoice generation, payment recording, journal posting, reconciliation, and period closing (financial statement preparation).

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

**CLARIFICATION - GL Posting Failure Recovery (Ambiguity #1 Resolution)**:
```
RULE: If GL post fails, store in failed_processing queue and retry with exponential backoff
RULE: After 24 hours of failed retries, escalate to Finance Director
RULE: Manual recovery process available with full audit trail
```

**GL Posting Retry Logic**:

```typescript
async function processGLPostingEvent(event: AccountingEvent) {
  const maxRetries = 100; // Up to 24 hours with exponential backoff
  let retryCount = 0;

  try {
    // Attempt GL posting
    await postJournalEntry(event.data);

  } catch (error) {
    // GL posting failed
    logger.error(`GL posting failed for event ${event.event_id}: ${error.message}`);

    // Store in failed_processing queue
    const failedJob = await createFailedProcessingRecord({
      event_id: event.event_id,
      event_type: event.event_type,
      error_message: error.message,
      error_stack: error.stack,
      status: 'FAILED',
      retry_count: 0,
      next_retry_at: calculateNextRetry(0), // 1 second
      created_at: new Date()
    });

    // Schedule retry
    await scheduleRetry(failedJob.id);

    throw error; // Propagate error for logging
  }
}

function calculateNextRetry(retryCount: number): Date {
  // Exponential backoff: 1s, 2s, 4s, 8s, ..., max 24 hours
  const delays = [
    1,      // 0: 1 second
    2,      // 1: 2 seconds
    4,      // 2: 4 seconds
    8,      // 3: 8 seconds
    16,     // 4: 16 seconds
    32,     // 5: 32 seconds
    60,     // 6: 1 minute
    120,    // 7: 2 minutes
    300,    // 8: 5 minutes
    600,    // 9: 10 minutes
    1800,   // 10: 30 minutes
    3600,   // 11+: 1 hour (max)
  ];

  const delaySeconds = delays[Math.min(retryCount, delays.length - 1)];
  return new Date(Date.now() + delaySeconds * 1000);
}

// Background job: Retry failed GL postings
async function retryFailedGLPostings() {
  const failedJobs = await getFailedJobs({
    status: 'FAILED',
    next_retry_at: { lte: new Date() }
  });

  for (const job of failedJobs) {
    try {
      // Retry GL posting
      await postJournalEntry(JSON.parse(job.event_data));

      // Success!
      await updateFailedJob(job.id, {
        status: 'RECOVERED',
        recovered_at: new Date(),
        retry_count: job.retry_count + 1
      });

      logger.info(
        `GL posting recovered for event ${job.event_id} ` +
        `after ${job.retry_count + 1} retries`
      );

    } catch (error) {
      const newRetryCount = job.retry_count + 1;

      if (newRetryCount >= 100 || Date.now() - job.created_at.getTime() > 24 * 3600 * 1000) {
        // Max retries exceeded OR 24 hours passed
        await updateFailedJob(job.id, {
          status: 'ESCALATED',
          retry_count: newRetryCount,
          escalated_at: new Date()
        });

        await escalateToFinanceDirector({
          event_id: job.event_id,
          event_type: job.event_type,
          error_message: error.message,
          retry_count: newRetryCount,
          time_elapsed: `${Math.round((Date.now() - job.created_at.getTime()) / 3600000)} hours`,
          action_required: 'Manual review and recovery required'
        });

        logger.error(
          `GL posting failed after ${newRetryCount} retries (24h). ` +
          `Event ${job.event_id} escalated to Finance Director.`
        );

      } else {
        // Schedule next retry
        await updateFailedJob(job.id, {
          retry_count: newRetryCount,
          next_retry_at: calculateNextRetry(newRetryCount),
          last_error: error.message
        });
      }
    }
  }
}
```

**Dead-Letter Queue Design**:

```sql
CREATE TABLE failed_gl_processing (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,

  event_id VARCHAR(255) NOT NULL UNIQUE,
  event_type VARCHAR(100) NOT NULL,
  event_data JSONB NOT NULL,

  error_message TEXT,
  error_stack TEXT,

  status VARCHAR(20) NOT NULL, -- 'FAILED', 'RECOVERED', 'ESCALATED', 'MANUALLY_RESOLVED'
  retry_count INT DEFAULT 0,
  next_retry_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW(),
  recovered_at TIMESTAMP,
  escalated_at TIMESTAMP,
  resolved_at TIMESTAMP,
  resolved_by UUID REFERENCES users(id),

  INDEX idx_failed_retry (status, next_retry_at),
  INDEX idx_failed_tenant (tenant_id, created_at DESC)
);
```

**Manual Recovery Steps**:

When Finance Director receives escalation:

1. **Review Failed Event**:
   ```sql
   SELECT * FROM failed_gl_processing
   WHERE status = 'ESCALATED'
   ORDER BY created_at DESC;
   ```

2. **Diagnose Root Cause**:
   - Check error message: "Account code 4100 does not exist"
   - Check event data: Verify GL accounts, amounts, dates

3. **Fix Root Cause**:
   - Create missing GL account OR
   - Correct event data (if source system sent wrong data)

4. **Manual Retry**:
   ```typescript
   async function manualRetryGLPosting(failedJobId: string, userId: string) {
     const job = await getFailedJob(failedJobId);

     // Finance Director fixes issue (e.g., creates missing account)
     // Then manually retries

     try {
       await postJournalEntry(JSON.parse(job.event_data));

       await updateFailedJob(job.id, {
         status: 'MANUALLY_RESOLVED',
         resolved_at: new Date(),
         resolved_by: userId
       });

       await auditLog({
         action: 'MANUAL_GL_RECOVERY',
         entity_type: 'FailedGLProcessing',
         entity_id: job.id,
         performed_by: userId,
         details: `Manually resolved after ${job.retry_count} failed retries`
       });

       return { success: true };

     } catch (error) {
       throw new Error(`Manual retry failed: ${error.message}`);
     }
   }
   ```

**Escalation Notification**:

```typescript
async function escalateToFinanceDirector(details: EscalationDetails) {
  const notification = {
    recipient: 'finance_director@company.com',
    subject: `[URGENT] GL Posting Failure - Manual Review Required`,
    body: `
Event ID: ${details.event_id}
Event Type: ${details.event_type}
Error: ${details.error_message}
Retry Attempts: ${details.retry_count}
Time Elapsed: ${details.time_elapsed}

Action Required: ${details.action_required}

View Details: /accounting/failed-processing/${details.event_id}
    `
  };

  await sendEmail(notification);
  await sendSlackAlert('#finance-alerts', notification);
}
```

**Dashboard View**:

```
Finance Director Dashboard:
┌──────────────────────────────────────────────────────────┐
│ Failed GL Processing Queue                               │
│                                                           │
│ Status: 3 ESCALATED items require attention              │
│                                                           │
│ Event ID       Type           Error              Retries │
│ ─────────────────────────────────────────────────────────│
│ evt-001   Invoice.Posted   Account 4100 missing   100   │
│ evt-002   Payment.Received  Validation failed      85   │
│ evt-003   Refund.Issued     Balance mismatch       92   │
│                                                           │
│ [Review & Retry]  [Export to CSV]                        │
└──────────────────────────────────────────────────────────┘
```

**Audit Trail Requirements**:
- All retry attempts logged with timestamp, retry_count, error
- Escalations logged with Finance Director notification timestamp
- Manual resolutions logged with user_id, resolution_timestamp, reason

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

**CLARIFICATION - Correction Approval Expiry (Ambiguity #6 Resolution)**:
```
RULE: If approval expires (auto-reject after 7 days), reversal+corrected GL entries are auto-rolled back
RULE: Staff must resubmit correction request from beginning
RULE: Original error GL entry remains in place (never deleted)
```

**Approval Expiry Workflow**:

**Scenario**: Correction request not approved within 7 days

```typescript
// Background job: Check for expired approval requests
async function checkExpiredCorrectionRequests() {
  const expiredRequests = await getCorrectionRequests({
    status: 'PENDING_APPROVAL',
    created_at: { lt: new Date(Date.now() - 7 * 24 * 3600 * 1000) } // 7 days ago
  });

  for (const request of expiredRequests) {
    try {
      // Step 1: Auto-reject expired request
      await updateCorrectionRequest(request.id, {
        status: 'AUTO_REJECTED',
        rejected_reason: 'Approval timeout (7 days)',
        rejected_at: new Date()
      });

      // Step 2: Rollback any GL entries created during correction attempt
      if (request.reversal_entry_id || request.corrected_entry_id) {
        await rollbackCorrectionEntries({
          reversal_entry_id: request.reversal_entry_id,
          corrected_entry_id: request.corrected_entry_id,
          reason: 'Approval expired'
        });

        logger.warn(
          `Rolled back GL entries for expired correction ${request.id}. ` +
          `Reversal: ${request.reversal_entry_id}, Corrected: ${request.corrected_entry_id}`
        );
      }

      // Step 3: Notify staff
      await sendNotification({
        recipient: request.created_by,
        subject: 'Correction Request Expired',
        body: `
Your correction request ${request.id} was auto-rejected due to timeout.
Reason: No approval received within 7 days.

Original GL entry ${request.original_entry_id} remains unchanged.

To proceed, please resubmit correction request.
        `
      });

      // Step 4: Audit log
      await auditLog({
        action: 'CORRECTION_EXPIRED_AUTO_ROLLBACK',
        entity_type: 'CorrectionRequest',
        entity_id: request.id,
        original_entry_id: request.original_entry_id,
        outcome: 'Reversal and corrected entries rolled back',
        timestamp: new Date()
      });

    } catch (error) {
      logger.error(`Failed to process expired correction ${request.id}: ${error.message}`);
    }
  }
}

async function rollbackCorrectionEntries(entries: RollbackEntries) {
  const trx = await db.transaction();

  try {
    // Rollback reversal entry if exists
    if (entries.reversal_entry_id) {
      await trx('journal_entries')
        .where({ id: entries.reversal_entry_id })
        .update({
          status: 'CANCELLED',
          cancelled_reason: entries.reason,
          cancelled_at: new Date()
        });
    }

    // Rollback corrected entry if exists
    if (entries.corrected_entry_id) {
      await trx('journal_entries')
        .where({ id: entries.corrected_entry_id })
        .update({
          status: 'CANCELLED',
          cancelled_reason: entries.reason,
          cancelled_at: new Date()
        });
    }

    await trx.commit();

  } catch (error) {
    await trx.rollback();
    throw error;
  }
}
```

**Consequences of Auto-Reject**:

1. **Original GL Entry Preserved**:
   - Original error entry (je-001) remains with status = POSTED
   - Financial data unchanged (prevents orphaned entries)
   - Entry visible in GL with original amounts

2. **Reversal Entry Cancelled** (if created):
   - Reversal entry (je-002) status → CANCELLED
   - Not counted in trial balance
   - Marked as "cancelled due to approval expiry"

3. **Corrected Entry Cancelled** (if created):
   - Corrected entry (je-003) status → CANCELLED
   - Not counted in trial balance

4. **Staff Can Resubmit**:
   - Create new correction request
   - Start approval process from beginning
   - Fresh 7-day approval window

**Prevents Orphaned GL Entries**:

```
Scenario WITHOUT auto-rollback:
- je-001: Original error (POSTED)
- je-002: Reversal (POSTED) - no approval
- Result: je-001 reversed but je-003 never posted → orphaned reversal

Scenario WITH auto-rollback (correct):
- je-001: Original error (POSTED)
- je-002: Reversal (CANCELLED) - approval expired
- Result: je-001 remains as-is, no orphaned entries
```

**CLARIFICATION - Session Expiry During GL Transaction (Ambiguity #3 Resolution)**:
```
RULE: Session expiry does NOT cancel database transactions
RULE: Transactions complete (commit or rollback) independent of session state
RULE: User must login again to see result after session expires
```

**Session Expiry Handling**:

```typescript
async function postJournalEntryWithSession(
  userId: string,
  sessionToken: string,
  journalEntry: JournalEntry
) {
  // Step 1: Validate session BEFORE transaction
  const session = await validateSession(sessionToken);
  if (!session || session.expired) {
    throw new SessionExpiredError('Session expired. Please login again.');
  }

  // Step 2: Start database transaction (independent of session)
  const trx = await db.transaction();

  try {
    // GL posting (runs to completion regardless of session state)
    await trx('journal_entries').insert(journalEntry);
    await trx('journal_lines').insert(journalEntry.lines);
    await trx.commit();

    // After commit, check if session still valid
    const sessionStillValid = await checkSessionValid(sessionToken);
    if (!sessionStillValid) {
      await auditLog({
        action: 'GL_POST_SESSION_EXPIRED_DURING_TRANSACTION',
        user_id: userId,
        journal_entry_id: journalEntry.id,
        outcome: 'Transaction completed, session expired',
        note: 'User must login to see result'
      });
    }

    return { success: true, session_valid: sessionStillValid };

  } catch (error) {
    await trx.rollback();
    throw error;
  }
}
```

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

## Financial Integrity Guardrails

**CRITICAL GUARDRAIL: GL Posting Failure Recovery - Full Escalation Policy (Financial Gap #1)**

**RULE**: GL posting failures MUST follow strict escalation sequence: auto-retry (1-24 hours) → Finance Director notification → manual recovery options.

**Problem**: Without clear escalation policy, GL posting failures could be missed or escalated too early, causing incomplete financial records or unnecessary manual intervention.

**Implementation Requirement**:

**Phase 1: Automatic Recovery (0-24 hours)**
```typescript
// Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 1m, 2m, 4m, 8m, 16m, 32m, 1h
// Total attempts: 13 retries over ~24 hours
const RETRY_SCHEDULE = [
  1,      // 1 second
  2, 4, 8, 16, 32,        // 32 seconds cumulative
  60, 120, 240, 480, 960, 1920, 3600  // Up to 1 hour each, max 24 hours cumulative
];

async function postGLEntryWithAutoRecovery(event: AccountingEvent) {
  try {
    // Attempt to post immediately
    await postJournalEntry(event);
  } catch (error) {
    // Store failure record for retry
    const failedRecord = await createFailedProcessingRecord({
      event_id: event.event_id,
      event_type: event.event_type,
      error_message: error.message,
      error_stack: error.stack,
      status: 'FAILED',
      retry_count: 0,
      next_retry_at: calculateNextRetry(0),
      escalation_sent_at: null,  // Not yet escalated
      last_attempted_at: new Date()
    });

    // Schedule automatic retry
    await scheduleRetry(failedRecord.id);
  }
}

async function retryFailedGLPosting(jobId: string) {
  const job = await getFailedProcessingRecord(jobId);

  if (job.retry_count >= 24) {
    // Max retries exceeded - escalate to Finance Director
    await escalateToFinanceDirector(job);
    return;
  }

  try {
    const event = await reconstructEventFromFailedRecord(job);
    await postJournalEntry(event);

    // Success - mark as recovered
    await updateFailedProcessingRecord(jobId, { status: 'RECOVERED' });
  } catch (error) {
    // Update retry count and schedule next attempt
    const nextRetryCount = job.retry_count + 1;
    const nextRetryTime = calculateNextRetry(nextRetryCount);

    if (nextRetryCount > 24) {
      // Escalate after 24 hours of retries
      await escalateToFinanceDirector({
        ...job,
        retry_count: nextRetryCount,
        error_message: error.message
      });
    }

    await updateFailedProcessingRecord(jobId, {
      retry_count: nextRetryCount,
      next_retry_at: nextRetryTime,
      last_attempted_at: new Date()
    });
  }
}
```

**Phase 2: Escalation to Finance Director (24+ hours)**
```typescript
async function escalateToFinanceDirector(failedRecord: FailedProcessingRecord) {
  // STEP 1: Update escalation status
  await updateFailedProcessingRecord(failedRecord.id, {
    status: 'ESCALATED',
    escalation_sent_at: new Date(),
    escalation_acknowledged: false
  });

  // STEP 2: Send urgent notification
  const notification = {
    to: 'finance_director@company.com',
    cc: ['accounting_manager@company.com'],
    subject: `🚨 URGENT: GL Posting Failure - 24+ Hours Without Recovery`,
    priority: 'high',
    body: `
EVENT ID: ${failedRecord.event_id}
EVENT TYPE: ${failedRecord.event_type}
FAILURE TIME: ${failedRecord.created_at}
RETRY ATTEMPTS: ${failedRecord.retry_count}

ERROR: ${failedRecord.error_message}

ACTION REQUIRED:
1. Review failed posting details
2. Investigate root cause
3. Choose recovery option:
   a) Manual GL entry adjustment
   b) Event replay after issue fixed
   c) Accounting reversal & restatement

LINK: /accounting/failed-gl-posting/${failedRecord.id}

SLA: Acknowledge within 2 hours. Resolve within 8 business hours.
    `
  };

  await sendEmail(notification);
  await sendSlackAlert('#finance-critical', notification);
}
```

**Phase 3: Manual Recovery Options**
```typescript
interface ManualRecoveryOptions {
  // Option 1: Retry the failed GL posting
  retryNow: async (jobId: string) => Promise<void>,

  // Option 2: Manual GL entry adjustment
  manualAdjustment: async (jobId: string, manualEntryData: JournalEntry) => Promise<void>,

  // Option 3: Acknowledge and defer (if resolved externally)
  acknowledgeAndResolve: async (jobId: string, resolutionNotes: string) => Promise<void>,

  // Option 4: Escalate to CFO (for high-value or systemic issues)
  escalateToCFO: async (jobId: string, reason: string) => Promise<void>
}
```

**Audit Trail Requirements**:
- ✅ EVERY retry attempt logged: timestamp, retry_count, error_message, next_retry_time
- ✅ EVERY escalation logged: escalation_time, recipient, notification_method
- ✅ EVERY manual action logged: action_type, performed_by, timestamp, justification
- ✅ EVERY resolution logged: resolution_type, details, who_resolved, timestamp
- ✅ Link all logs to audit_trail_id for full event traceability

---

**CRITICAL GUARDRAIL: FX Rate Immutability - Multi-Layer Enforcement (Financial Gap #2)**

**RULE**: FX rates MUST be immutable after GL posting. Database trigger is PRIMARY enforcement; application validation is SECONDARY defense-in-depth.

**Problem**: If FX rates can be modified after posting, historical GL entries would become invalid, financial statements could be restated arbitrarily, and audit trail would be corrupted.

**Implementation Requirement**:

**Layer 1: Database Trigger (PRIMARY ENFORCEMENT)**
```sql
-- Primary enforcement: Database trigger prevents any FX rate updates after posting
CREATE TRIGGER prevent_fx_rate_updates_after_posting
BEFORE UPDATE ON fx_transactions
FOR EACH ROW
WHEN (OLD.posted_at IS NOT NULL)  -- Only applies to POSTED transactions
BEGIN
  -- Check if rate fields are being changed
  IF (NEW.rate_at_creation != OLD.rate_at_creation
      OR NEW.rate_at_settlement != OLD.rate_at_settlement
      OR NEW.spread_applied != OLD.spread_applied) THEN
    RAISE EXCEPTION 'FX_RATE_IMMUTABLE_AFTER_POSTING'
      USING MESSAGE = 'FX rates are immutable after GL posting. ' +
                      'Posted at: ' || OLD.posted_at ||
                      '. To correct FX errors, create reversal entry.';
  END IF;

  -- Only allow updates to non-rate fields (status, audit fields)
  IF (NEW.status != OLD.status  -- Allow status changes
      OR NEW.reconciled_at != OLD.reconciled_at
      OR NEW.reconciled_by != OLD.reconciled_by) THEN
    -- Allow non-rate field updates
    RETURN NEW;
  END IF;

  RETURN NEW;
END;

CREATE INDEX idx_fx_posted_at ON fx_transactions(posted_at)
  WHERE posted_at IS NOT NULL;  -- Index only posted transactions for performance
```

**Layer 2: Application Validation (SECONDARY DEFENSE)**
```typescript
async function updateFXTransaction(
  txnId: string,
  updates: Partial<FXTransaction>,
  userId: string
): Promise<FXTransaction> {
  // STEP 1: Load current transaction
  const current = await fxService.getTransaction(txnId);

  // STEP 2: Check if transaction is posted
  if (current.posted_at !== null) {
    // STEP 3: If posted, reject ANY rate field updates
    const rateFields = ['rate_at_creation', 'rate_at_settlement', 'spread_applied'];
    const attemptedRateUpdate = rateFields.some(
      field => updates[field] !== undefined && updates[field] !== current[field]
    );

    if (attemptedRateUpdate) {
      throw new Error(
        `FX rate immutability violation. Transaction ${txnId} was posted on ` +
        `${current.posted_at.toISOString()}. FX rates cannot be modified after posting. ` +
        `To correct FX errors, create a reversal entry (new FX transaction with opposite direction).`
      );
    }

    // Log attempt for audit trail (even if rejected)
    await auditService.log({
      action: 'FX_UPDATE_REJECTED',
      reason: 'RATE_IMMUTABILITY_VIOLATION',
      transaction_id: txnId,
      attempted_changes: updates,
      user_id: userId,
      timestamp: new Date()
    });
  }

  // STEP 4: Allow updates to non-rate fields
  const allowedFields = ['status', 'reconciled_at', 'reconciled_by', 'notes'];
  const safeUpdates = Object.keys(updates).reduce((acc, key) => {
    if (allowedFields.includes(key)) {
      acc[key] = updates[key];
    }
    return acc;
  }, {});

  return await fxService.update(txnId, safeUpdates);
}
```

**Layer 3: Testing & Verification**
```typescript
// Unit test: Verify database trigger enforces immutability
test('FX rate immutability - database trigger prevents update', async () => {
  const txn = await createPostedFXTransaction({
    rate_at_creation: 16500,
    posted_at: new Date()
  });

  // Attempt to update FX rate (should fail at database level)
  const promise = db.raw(`
    UPDATE fx_transactions
    SET rate_at_creation = 16600
    WHERE id = $1
  `, [txn.id]);

  await expect(promise).rejects.toThrow('FX_RATE_IMMUTABLE_AFTER_POSTING');
});

// Unit test: Verify application rejects FX rate updates
test('FX rate immutability - application validation rejects update', async () => {
  const txn = await createPostedFXTransaction({ rate_at_creation: 16500 });

  const promise = fxService.updateTransaction(txn.id, {
    rate_at_creation: 16600
  }, userId);

  await expect(promise).rejects.toThrow('FX rate immutability violation');
});
```

---

**CRITICAL GUARDRAIL: FX Adjustment Audit Trail - Mandatory for All Changes (Financial Gap #3)**

**RULE**: EVERY FX adjustment (including reconciliation, accrual, settlement) MUST generate detailed audit trail entry with before/after values.

**Problem**: Without mandatory audit trails, FX adjustments could be made without accountability, making it impossible to trace FX-related GL errors back to the decision maker.

**Implementation Requirement**:
```typescript
async function recordFXAdjustment(
  adjustment: FXAdjustment,
  context: {
    user_id: string,
    reason: string,
    authorization_level: 'ACCOUNTING_STAFF' | 'ACCOUNTING_MANAGER' | 'CFO',
    approval_reference?: string  // For high-value adjustments
  }
): Promise<FXAdjustmentRecord> {
  // STEP 1: Validate authorization level vs adjustment amount
  if (adjustment.amount > 10000 && context.authorization_level === 'ACCOUNTING_STAFF') {
    throw new Error(`Adjustment amount > $10,000 requires ACCOUNTING_MANAGER or CFO approval`);
  }

  // STEP 2: Create adjustment record with full audit trail
  const record = await fxAdjustmentService.create({
    // Identification
    id: generateId('fxadj'),
    tenant_id: adjustment.tenant_id,
    fx_transaction_id: adjustment.fx_transaction_id,

    // Adjustment details
    adjustment_type: adjustment.type,  // 'RECONCILIATION', 'ACCRUAL', 'SETTLEMENT', 'CORRECTION'
    amount: adjustment.amount,
    currency: adjustment.currency,
    rate_before: adjustment.rate_before,
    rate_after: adjustment.rate_after,
    gl_impact_debit_account: adjustment.debit_account,
    gl_impact_credit_account: adjustment.credit_account,

    // Business context
    reason: context.reason,  // e.g., "Q4 year-end accrual", "Bank statement reconciliation"
    approval_reference: context.approval_reference,  // PO reference, approval document

    // Authorization trail
    authorized_by: context.user_id,
    authorization_level: context.authorization_level,
    authorized_at: new Date(),

    // GL Integration
    gl_entry_id: null,  // Will be populated after GL posting
    gl_posting_status: 'PENDING',

    // Timestamps
    created_at: new Date(),
    created_by: context.user_id,
    posted_at: null,  // Only set after GL posting succeeds
    posted_by: null
  });

  // STEP 3: Log detailed audit entry
  await auditService.log({
    action: 'FX_ADJUSTMENT_CREATED',
    entity_type: 'FXAdjustment',
    entity_id: record.id,
    changes: {
      before: null,
      after: {
        adjustment_type: record.adjustment_type,
        amount: record.amount,
        rate_before: record.rate_before,
        rate_after: record.rate_after,
        reason: record.reason
      }
    },
    performed_by: context.user_id,
    authorization_level: context.authorization_level,
    timestamp: new Date(),
    request_id: generateRequestId()
  });

  return record;
}

// Post FX adjustment to GL
async function postFXAdjustmentToGL(adjustmentId: string) {
  const adjustment = await fxAdjustmentService.get(adjustmentId);

  // Create GL entry for FX adjustment
  const glEntry = {
    lines: [
      {
        account_code: adjustment.gl_impact_debit_account,
        debit: Math.abs(adjustment.amount),
        description: `FX ${adjustment.adjustment_type}: ${adjustment.reason}`
      },
      {
        account_code: adjustment.gl_impact_credit_account,
        credit: Math.abs(adjustment.amount),
        description: `FX ${adjustment.adjustment_type}: ${adjustment.reason}`
      }
    ],
    source_adjustment_id: adjustmentId
  };

  try {
    const je = await glService.postJournalEntry(glEntry);

    // Update adjustment record with GL reference
    await fxAdjustmentService.update(adjustmentId, {
      gl_entry_id: je.id,
      gl_posting_status: 'POSTED',
      posted_at: new Date(),
      posted_by: getCurrentUser().id
    });

    // Log GL posting success
    await auditService.log({
      action: 'FX_ADJUSTMENT_POSTED_TO_GL',
      entity_type: 'FXAdjustment',
      entity_id: adjustmentId,
      reference_id: je.id,
      timestamp: new Date()
    });
  } catch (error) {
    // Log GL posting failure
    await auditService.log({
      action: 'FX_ADJUSTMENT_GL_POSTING_FAILED',
      entity_type: 'FXAdjustment',
      entity_id: adjustmentId,
      error: error.message,
      timestamp: new Date()
    });

    throw error;
  }
}
```

---

**CRITICAL GUARDRAIL: Reconciliation Failure SLA - Escalation & Resolution Timeline (Financial Gap #4)**

**RULE**: Reconciliation failures MUST be resolved within SLA based on severity. Unresolved reconciliation blocks period close and financial reporting.

**Problem**: Without SLA definition, reconciliation failures could languish unresolved, delaying period close and hiding financial discrepancies.

**Implementation Requirement**:

**Severity Classification**:
```
┌────────────────┬──────────────────┬──────────────────┬─────────────────────┐
│ Severity       │ Discrepancy Type │ Amount Threshold │ SLA Resolution      │
├────────────────┼──────────────────┼──────────────────┼─────────────────────┤
│ CRITICAL       │ Bank mismatch     │ Any amount       │ 2 hours             │
│ CRITICAL       │ GL unbalanced     │ Any amount       │ 4 hours             │
│ HIGH           │ AR/AP mismatch    │ > $10,000        │ 8 hours / 1 bus day │
│ MEDIUM         │ AR/AP mismatch    │ $1,000 - $10,000 │ 1 business day      │
│ LOW            │ Rounding/timing   │ < $1,000         │ 3 business days     │
└────────────────┴──────────────────┴──────────────────┴─────────────────────┘
```

**Escalation Workflow**:
```typescript
async function handleReconciliationFailure(
  failure: ReconciliationFailure,
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
) {
  const SLA_MAP = {
    'CRITICAL': { hours: 2, escalationEmail: 'cfo@company.com' },
    'HIGH': { hours: 8, escalationEmail: 'accounting_manager@company.com' },
    'MEDIUM': { hours: 24, escalationEmail: 'accounting_manager@company.com' },
    'LOW': { hours: 72, escalationEmail: 'accounting_staff@company.com' }
  };

  const sla = SLA_MAP[severity];
  const dueDate = new Date(Date.now() + sla.hours * 60 * 60 * 1000);

  // Create reconciliation issue record
  const issue = await reconciliationIssueService.create({
    id: generateId('reconcile-issue'),
    period_id: failure.period_id,
    failure_type: failure.type,
    discrepancy_amount: failure.amount,
    severity,
    sla_due_date: dueDate,
    assigned_to: sla.escalationEmail,
    created_at: new Date(),
    status: 'OPEN'
  });

  // Prevent period close
  await periodService.blockClose(failure.period_id, {
    reason: `Reconciliation failure: ${failure.description}`,
    blocking_issue_id: issue.id
  });

  // Send initial notification
  await sendNotification(sla.escalationEmail, {
    subject: `${severity} Reconciliation Issue - ${failure.description}`,
    dueDate,
    issueLink: `/accounting/reconciliation-issues/${issue.id}`
  });

  // Schedule escalation reminders
  await scheduleEscalation(issue.id, {
    at: new Date(dueDate.getTime() - 30 * 60 * 1000),  // 30 min before SLA
    escalateTo: 'accounting_manager@company.com',
    message: 'Reconciliation issue approaching SLA deadline'
  });
}

// Verify and resolve reconciliation
async function resolveReconciliationIssue(
  issueId: string,
  resolution: {
    resolution_type: 'MANUAL_ADJUSTMENT' | 'REVERSAL' | 'TIMING_DIFFERENCE' | 'DATA_ERROR',
    adjustment_entries?: JournalEntry[],
    notes: string,
    resolved_by: string
  }
) {
  const issue = await reconciliationIssueService.get(issueId);

  // Verify SLA compliance
  if (new Date() > issue.sla_due_date) {
    // Log SLA violation
    await auditService.log({
      action: 'RECONCILIATION_SLA_VIOLATION',
      entity_id: issueId,
      resolved_at: new Date(),
      due_at: issue.sla_due_date,
      hours_overdue: (new Date().getTime() - issue.sla_due_date.getTime()) / (60 * 60 * 1000)
    });
  }

  // Post adjustment entries if provided
  if (resolution.adjustment_entries && resolution.adjustment_entries.length > 0) {
    for (const entry of resolution.adjustment_entries) {
      await glService.postJournalEntry({
        ...entry,
        description: `Reconciliation adjustment: ${resolution.notes}`,
        source_reconciliation_issue_id: issueId
      });
    }
  }

  // Mark issue resolved
  await reconciliationIssueService.update(issueId, {
    status: 'RESOLVED',
    resolution_type: resolution.resolution_type,
    resolution_notes: resolution.notes,
    resolved_by: resolution.resolved_by,
    resolved_at: new Date()
  });

  // Allow period close to proceed
  await periodService.unblockClose(issue.period_id, issueId);

  // Log resolution
  await auditService.log({
    action: 'RECONCILIATION_ISSUE_RESOLVED',
    entity_id: issueId,
    resolution_type: resolution.resolution_type,
    resolved_by: resolution.resolved_by,
    timestamp: new Date()
  });
}
```

---

## Critical Failure Scenario Guardrails

**CRITICAL GUARDRAIL: Database Transaction Failure Halfway Through GL Posting (Missing Guardrail #1)**

**RULE**: If a database transaction fails halfway through GL posting, ALL changes MUST be rolled back atomically. Partial GL entries MUST NOT exist in the ledger.

**Problem**: If a multi-statement transaction (e.g., UPDATE journal_entry, INSERT journal_line, UPDATE account_balance) fails midway, some statements could succeed while others fail, creating an inconsistent GL state where debits ≠ credits.

**Implementation Requirement**:

**Pattern: Atomic GL Posting Transaction**
```typescript
async function postJournalEntryAtomically(
  entry: JournalEntry
): Promise<JournalEntry> {
  // Use database transaction for atomicity
  return await db.transaction(async (trx) => {
    try {
      // STEP 1: Verify GL structure is balanced
      const debits = entry.lines
        .filter(l => l.debit)
        .reduce((sum, l) => sum + l.debit, 0);
      const credits = entry.lines
        .filter(l => l.credit)
        .reduce((sum, l) => sum + l.credit, 0);

      if (Math.abs(debits - credits) > 0.01) {
        throw new Error(`Journal entry unbalanced. Debits: ${debits}, Credits: ${credits}`);
      }

      // STEP 2: Lock all affected GL accounts (prevents concurrent updates)
      const accountIds = [...new Set(entry.lines.map(l => l.account_id))];
      await trx('gl_accounts')
        .whereIn('id', accountIds)
        .forUpdate()  // SELECT...FOR UPDATE (pessimistic lock)
        .select('id', 'balance');  // Just lock, don't modify yet

      // STEP 3: Create journal entry record
      const je = await trx('journal_entries').insert({
        id: entry.id,
        tenant_id: entry.tenant_id,
        period_id: entry.period_id,
        entry_date: entry.entry_date,
        description: entry.description,
        status: 'DRAFT',  // Start as DRAFT, post after lines inserted
        created_at: new Date()
      }).returning('*');

      // STEP 4: Insert all journal lines (each line is a single operation)
      const lines = await Promise.all(
        entry.lines.map(line =>
          trx('journal_lines').insert({
            id: generateId('jl'),
            journal_entry_id: je.id,
            account_id: line.account_id,
            tenant_id: entry.tenant_id,
            debit_amount: line.debit || null,
            credit_amount: line.credit || null,
            description: line.description,
            created_at: new Date()
          }).returning('*')
        )
      );

      // STEP 5: Update GL account balances (only if all lines inserted successfully)
      for (const line of lines) {
        const impact = (line.debit_amount || 0) - (line.credit_amount || 0);
        await trx('gl_accounts')
          .where('id', line.account_id)
          .increment('balance', impact);
      }

      // STEP 6: Mark entry as POSTED (atomic with above updates)
      await trx('journal_entries')
        .where('id', je.id)
        .update({
          status: 'POSTED',
          posted_at: new Date(),
          posted_by: getCurrentUserId()
        });

      // STEP 7: Return posted entry
      return {
        ...je,
        lines,
        status: 'POSTED',
        posted_at: new Date()
      };

    } catch (error) {
      // Transaction automatically rolled back on error
      throw new Error(`GL posting failed. All changes rolled back. Error: ${error.message}`);
    }
  });
}
```

**Atomicity Enforcement**:
- ✅ Use database-level transactions (ACID compliance)
- ✅ Lock all affected accounts before modifying (pessimistic locking)
- ✅ Single logical unit: validate → lock → insert → update → mark posted
- ✅ Automatic rollback on ANY error (database guarantee)
- ✅ No partial GL states allowed (no orphaned lines or unbalanced accounts)
- ✅ Test: Simulate mid-transaction failure; verify complete rollback

---

**CRITICAL GUARDRAIL: Payment Gateway Timeout During Check-Out (Missing Guardrail #2)**

**RULE**: Payment gateway timeouts MUST NOT result in loss of guest charges or incomplete payments. Use compensation pattern for recovery.

**Problem**: If payment processor times out after authorizing but before settling, guest could be charged twice, or folio could have incomplete GL posting, leaving accounts payable hanging.

**Implementation Requirement**:

**Three-Phase Payment Processing**:
```typescript
enum PaymentPhase {
  PENDING = 'PENDING',      // Payment initiated, awaiting processor response
  AUTHORIZED = 'AUTHORIZED', // Processor confirmed authorization, not yet settled
  SETTLED = 'SETTLED',      // Payment successfully settled, GL posted
  FAILED = 'FAILED',        // Payment failed or timed out
  COMPENSATING = 'COMPENSATING'  // Attempting to cancel authorization
}

async function processPaymentWithTimeoutRecovery(
  folio: Folio,
  payment: PaymentRequest,
  timeoutMs: number = 30000  // 30 second timeout
): Promise<PaymentResult> {
  let paymentRecord = {
    id: generateId('pay'),
    folio_id: folio.id,
    tenant_id: folio.tenant_id,
    amount: payment.amount,
    phase: PaymentPhase.PENDING,
    initiated_at: new Date(),
    authorization_code: null,
    settlement_reference: null,
    last_error: null
  };

  try {
    // PHASE 1: Authorization (with timeout)
    paymentRecord = await authorizePaymentWithTimeout(
      payment,
      timeoutMs
    );

    if (paymentRecord.phase === PaymentPhase.AUTHORIZED) {
      // PHASE 2: Settlement
      try {
        paymentRecord = await settleAuthorizedPayment(paymentRecord);

        if (paymentRecord.phase === PaymentPhase.SETTLED) {
          // PHASE 3: GL Posting
          await postPaymentToGL(paymentRecord);
          paymentRecord.phase = PaymentPhase.SETTLED;
          return { success: true, payment: paymentRecord };
        }
      } catch (settlementError) {
        // Settlement failed after authorization
        // Compensate: Void the authorization
        await compensateAuthorization(paymentRecord);
        paymentRecord.phase = PaymentPhase.FAILED;
        paymentRecord.last_error = settlementError.message;
      }
    }
  } catch (error) {
    if (error.code === 'TIMEOUT') {
      // Handle timeout-specific logic
      paymentRecord.phase = PaymentPhase.PENDING;
      paymentRecord.last_error = `Payment timeout after ${timeoutMs}ms`;

      // Schedule async recovery
      await schedulePaymentRecoveryRetry({
        payment_id: paymentRecord.id,
        folio_id: folio.id,
        initial_attempt_at: paymentRecord.initiated_at,
        retry_attempts: 0,
        next_retry_at: new Date(Date.now() + 60000) // Retry in 1 minute
      });

      // Return partial result - folio NOT closed yet
      return { success: false, payment: paymentRecord, retryable: true };
    }

    paymentRecord.phase = PaymentPhase.FAILED;
    paymentRecord.last_error = error.message;
  }

  // Persist payment record (for audit & recovery)
  await savePaymentRecord(paymentRecord);

  return { success: false, payment: paymentRecord };
}

// Async recovery of timed-out payments
async function retryTimedOutPayment(recoveryJob: PaymentRecoveryJob) {
  const maxRetries = 5;
  const payment = await getPaymentRecord(recoveryJob.payment_id);

  if (recoveryJob.retry_attempts >= maxRetries) {
    // Escalate to management
    await escalatePaymentFailureToFront(recoveryJob);
    return;
  }

  try {
    // STEP 1: Check payment processor for authorization status
    const processorStatus = await getPaymentProcessorStatus(
      payment.authorization_code
    );

    if (processorStatus === 'AUTHORIZED') {
      // Authorization succeeded - retry settlement
      const settled = await settleAuthorizedPayment(payment);
      if (settled.phase === PaymentPhase.SETTLED) {
        // Success - post to GL
        await postPaymentToGL(settled);
        return;
      }
    } else if (processorStatus === 'DECLINED') {
      // Authorization already declined
      await markPaymentFailed(payment);
      await sendGuestNotification(payment.folio_id, 'Payment was declined');
      return;
    }

    // Still pending or unknown - retry
    await schedulePaymentRecoveryRetry({
      ...recoveryJob,
      retry_attempts: recoveryJob.retry_attempts + 1,
      next_retry_at: new Date(Date.now() + 60000 * (recoveryJob.retry_attempts + 1))
    });

  } catch (error) {
    // Retry failed
    await schedulePaymentRecoveryRetry({
      ...recoveryJob,
      retry_attempts: recoveryJob.retry_attempts + 1,
      next_retry_at: new Date(Date.now() + 300000)  // Retry in 5 minutes
    });
  }
}
```

**SLA for Payment Recovery**:
- ✅ Timeout detected → immediate async retry scheduled
- ✅ Retry every 1 minute for up to 5 attempts (5-minute window)
- ✅ If still pending after 5 minutes → escalate to Front Desk Manager
- ✅ Manager can: (1) retry manually, (2) check payment processor, (3) cancel charge
- ✅ All actions logged with audit trail
- ✅ Guest never charged multiple times (idempotent payment processing)

---

**CRITICAL GUARDRAIL: Journal Entry Posted But Event Publish Fails (Missing Guardrail #3)**

**RULE**: If GL posting succeeds but event publishing fails, a compensation job MUST republish the event asynchronously. Events MUST eventually reach subscribers.

**Problem**: If journal entry is posted to GL but the event broadcast fails, downstream systems (PMS, Inventory) won't know about GL changes, creating inconsistency between GL and operational systems.

**Implementation Requirement**:

**Compensating Transaction Pattern**:
```typescript
async function postGLAndPublishEventWithCompensation(
  event: AccountingEvent,
  glEntry: JournalEntry
): Promise<{ success: boolean, details: any }> {
  let glPosted = false;
  let eventPublished = false;

  try {
    // STEP 1: Post GL entry (primary action)
    const posted = await postJournalEntryAtomically(glEntry);
    glPosted = true;

    // STEP 2: Publish event to subscribers
    const published = await eventBus.publish(event);
    eventPublished = true;

    return { success: true, details: { glPosted, eventPublished } };

  } catch (error) {
    if (glPosted && !eventPublished) {
      // GL succeeded, event failed - compensate
      console.error('GL posted but event publish failed. Creating compensation job.');

      // Create compensation record for async retry
      const compensationJob = await createEventPublishingCompensationJob({
        id: generateId('comp-evt-pub'),
        event_id: event.event_id,
        event_type: event.event_type,
        event_payload: event,
        journal_entry_id: glEntry.id,
        status: 'PENDING',
        retry_count: 0,
        next_retry_at: new Date(Date.now() + 5000),  // Retry in 5 seconds
        created_at: new Date(),
        failed_reason: error.message
      });

      // Schedule compensation job
      await scheduleCompensationJob(compensationJob);

      return {
        success: false,
        details: {
          glPosted: true,
          eventPublished: false,
          compensationJobId: compensationJob.id,
          message: 'GL posted successfully. Event publish failed. Async retry scheduled.'
        }
      };
    }

    throw error;
  }
}

// Async compensation job to retry event publishing
async function compensateEventPublishing(jobId: string) {
  const job = await getCompensationJob(jobId);
  const maxRetries = 24; // 24 hours of exponential backoff

  if (job.retry_count >= maxRetries) {
    // Escalate to event delivery team
    await escalateEventDeliveryFailure(job);
    return;
  }

  try {
    // Republish the event
    await eventBus.publish(job.event_payload);

    // Success - mark job resolved
    await markCompensationJobResolved(jobId, {
      resolved_at: new Date(),
      resolved_by: 'COMPENSATION_JOB',
      note: `Event republished successfully after ${job.retry_count} retries`
    });

  } catch (error) {
    // Retry failed - schedule next attempt
    const nextRetryCount = job.retry_count + 1;
    const backoffMs = calculateExponentialBackoff(nextRetryCount);

    await updateCompensationJob(jobId, {
      retry_count: nextRetryCount,
      next_retry_at: new Date(Date.now() + backoffMs),
      last_error: error.message,
      last_attempt_at: new Date()
    });
  }
}

// Escalation for persistent event delivery failures
async function escalateEventDeliveryFailure(job: CompensationJob) {
  // Mark job as escalated
  await updateCompensationJob(job.id, {
    status: 'ESCALATED',
    escalated_at: new Date()
  });

  // Send alert to event delivery team
  await sendAlert({
    to: 'event-delivery-team@company.com',
    subject: 'CRITICAL: Event Delivery Failure - 24+ Hours Without Success',
    body: `
Event ID: ${job.event_id}
Journal Entry ID: ${job.journal_entry_id}
Retry Attempts: ${job.retry_count}
Last Error: ${job.last_error}

GL POST: ✅ Successful (data is in ledger)
EVENT PUBLISH: ❌ Failed (downstream systems unaware)

ACTION REQUIRED:
1. Investigate event publishing infrastructure
2. Check if subscribers are receiving other events
3. Manually republish event or mark as acknowledged
4. Update compensation job status

Link: /accounting/compensation-jobs/${job.id}
    `
  });
}
```

**Enforcement**:
- ✅ EVERY GL posting followed by event publishing in same logical transaction
- ✅ Compensation job created IMMEDIATELY if event publish fails
- ✅ Async retry every 30s-1h (exponential backoff) for up to 24 hours
- ✅ Escalation after 24 hours to event delivery team
- ✅ Test: Simulate event publish failure; verify compensation job retries successfully

---

## Multi-Tenant Guardrails

**CRITICAL GUARDRAIL: GL Query Tenant Isolation in JOINs (Multi-Tenant Gap #1)**

**RULE**: All GL queries MUST filter tenant_id at EVERY table join, not just the primary table.

**Problem**: When queries LEFT JOIN from accounts → journal_lines → journal_entries, filtering only je.tenant_id = $1 can miss tenant isolation if journal_lines lacks a tenant_id filter. This creates data leak risk.

**Implementation Requirement**:
```sql
-- CORRECT: Explicit tenant_id filters on ALL tables in joins
SELECT
  a.account_code,
  a.account_name,
  SUM(jl.debit_amount) AS total_debit,
  SUM(jl.credit_amount) AS total_credit
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id
  AND jl.tenant_id = $1  -- MANDATORY: tenant_id filter on joined table
LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
  AND je.tenant_id = $1  -- MANDATORY: tenant_id filter on joined table
WHERE a.tenant_id = $1  -- MANDATORY: tenant_id filter on primary table
  AND a.is_header = FALSE
  AND je.posted_at IS NOT NULL
  AND je.is_deleted = FALSE  -- MANDATORY: exclude soft-deleted entries
GROUP BY a.id, a.account_code, a.account_name
ORDER BY a.account_code;
```

**Enforcement**:
- ✅ Database schema: journal_lines table MUST have tenant_id column (indexed)
- ✅ Code review: Every GL query MUST have tenant_id filters on ALL joined tables
- ✅ Test: Unit test must verify cross-tenant data isolation (query with tenant-A credentials cannot see tenant-B accounts)
- ✅ Database trigger: Prevent INSERT into journal_lines without tenant_id
- ✅ ORM mappings: journal_lines.tenant_id MUST be automatically set from current request context

---

**CRITICAL GUARDRAIL: Soft-Delete Exclusion in GL Calculations (Multi-Tenant Gap #4)**

**RULE**: All GL calculations (trial balance, financial statements, account balances) MUST exclude soft-deleted records.

**Problem**: If a journal entry or journal line is soft-deleted (is_deleted=true) but not hard-deleted, GL calculations will be incorrect. Reversals MUST NOT be treated as soft-deletions; they are explicit reversal entries.

**Implementation Requirement**:
```sql
-- MANDATORY: ALL GL calculation queries must include is_deleted filter

-- Trial Balance Query
SELECT a.account_code, SUM(jl.debit_amount) AS total_debit
FROM accounts a
LEFT JOIN journal_lines jl ON a.id = jl.account_id AND jl.tenant_id = $1
LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id AND je.tenant_id = $1
WHERE a.tenant_id = $1
  AND je.posted_at IS NOT NULL
  AND je.is_deleted = FALSE      -- MANDATORY: Exclude soft-deleted entries
  AND jl.is_deleted = FALSE      -- MANDATORY: Exclude soft-deleted lines
  AND a.is_deleted = FALSE       -- MANDATORY: Exclude soft-deleted accounts
GROUP BY a.id, a.account_code;

-- Account Balance Query
SELECT SUM(COALESCE(debit, 0) - COALESCE(credit, 0)) AS balance
FROM journal_lines
WHERE account_id = $1
  AND tenant_id = $2
  AND is_deleted = FALSE         -- MANDATORY: exclude soft-deleted
  AND journal_entry_id IN (
    SELECT id FROM journal_entries
    WHERE posted_at IS NOT NULL
    AND is_deleted = FALSE       -- MANDATORY: exclude soft-deleted entries
  );
```

**Enforcement**:
- ✅ Schema: All GL-related tables (journal_entries, journal_lines, accounts) MUST have is_deleted column
- ✅ Audit Trail: When is_deleted = true, MUST log: who deleted, when, reason
- ✅ Code review: Zero tolerance — any GL query without is_deleted filter is CODE RED
- ✅ Test: Unit test must verify that soft-deleted entries don't affect GL balance
- ✅ Reversal vs Deletion: is_deleted used ONLY for administrative deletions (mistakes); reversals create explicit reversal entries

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
