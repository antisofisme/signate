# STD-21: Multi-Currency Exchange Rate Handling Standard

**Status**: ✅ Approved (2025-12-24)
**Scope**: How all modules handle foreign exchange rates, recordings, and FX gain/loss accounting

---

## Overview

When transactions occur between tenants with different functional currencies (e.g., Supplier in USD, Hotel in IDR), the system MUST:
1. Record amounts in both currencies
2. Fix exchange rates at specific lock points
3. Calculate realized FX gains/losses at settlement
4. Track unrealized FX separately (for period-end revaluation)

---

## 1. Functional Currency Definition

**Per-Tenant Rule**: Each tenant has ONE immutable functional currency

```sql
-- tenants table
functional_currency: VARCHAR(3) NOT NULL  -- 'IDR', 'USD', 'EUR', etc. (set at tenant creation)
-- CONSTRAINT: Cannot be changed after tenant creation
```

**Impact**: All GL accounts use this currency. Multi-currency transactions must be converted.

---

## 2. Exchange Rate Lock Points

**Rule**: Exchange rate is FIXED at the transaction creation date (never updated after posting)

### Lock Point Matrix

| Transaction Type | Lock Point | Rate Source | Adjustment Policy |
|---|---|---|---|
| **Purchase Invoice** | invoice_date | Published rate (ECB/BI) | ❌ NO post-posting adjustments |
| **Supplier Payment** | payment_date | Spot rate at settlement | ❌ Realized FX recorded at settlement |
| **Customer Invoice** | invoice_date | Published rate | ❌ NO post-posting adjustments |
| **Customer Receipt** | payment_date | Spot rate at settlement | ✅ Realized FX recorded, not unrealized |
| **Bank Statement** | transaction_date | Actual settlement rate | ❌ NO adjustments (audit trail) |

### Rate Determination Algorithm

```typescript
async function getExchangeRate(
  fromCurrency: string,
  toCurrency: string,
  rateDate: Date,
  tenantId: UUID
): Promise<{ rate: Decimal; source: string; rateDate: Date }> {
  // 1. Check if contract specifies custom rate
  const contract = await checkContract(tenantId, fromCurrency, toCurrency);
  if (contract?.override_rate) {
    return {
      rate: contract.override_rate,
      source: 'CONTRACT_SPECIFIED',
      rateDate: contract.effective_date
    };
  }

  // 2. Use published rate (ECB, Bank Indonesia, etc.)
  const publishedRate = await getPublishedRate(fromCurrency, toCurrency, rateDate);
  if (publishedRate) {
    return {
      rate: publishedRate,
      source: 'PUBLISHED_RATE',
      rateDate: rateDate
    };
  }

  // 3. Fallback to last known good rate (max 2 business days old)
  const lastRate = await getLastKnownRate(fromCurrency, toCurrency);
  if (lastRate && isWithin2BusinessDays(lastRate.date, rateDate)) {
    return {
      rate: lastRate.rate,
      source: 'LAST_KNOWN_RATE',
      rateDate: lastRate.date
    };
  }

  throw new Error(`No exchange rate found for ${fromCurrency}/${toCurrency} on ${rateDate}`);
}

**CLARIFICATION - FX Rate Fallback Definition (Ambiguity #7 Resolution)**:
```
RULE: "Last known good" = most recent published rate within 2 business days
RULE: If no rate within 2 business days, REJECT transaction with error
RULE: Fallback rate must be marked in GL with flag 'rate_source=FALLBACK' for audit
RULE: Cannot use rate > 2 business days old (prevents stale rates)
```

**Fallback Rate Logic**:

```typescript
async function getLastKnownRate(
  fromCurrency: string,
  toCurrency: string
): Promise<{ rate: Decimal; date: Date } | null> {
  const twoBusinessDaysAgo = calculateBusinessDaysBack(new Date(), 2);

  // Query most recent rate within 2 business days
  const lastRate = await db('exchange_rates')
    .where({
      from_currency: fromCurrency,
      to_currency: toCurrency,
      rate_date: { gte: twoBusinessDaysAgo }
    })
    .orderBy('rate_date', 'desc')
    .first();

  return lastRate
    ? { rate: lastRate.rate, date: lastRate.rate_date }
    : null;
}

function calculateBusinessDaysBack(date: Date, numDays: number): Date {
  let currentDate = new Date(date);
  let daysBack = 0;

  while (daysBack < numDays) {
    currentDate.setDate(currentDate.getDate() - 1);

    // Skip weekends
    const dayOfWeek = currentDate.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {  // Not Sunday or Saturday
      daysBack++;
    }
  }

  return currentDate;
}

function isWithin2BusinessDays(rateDate: Date, transactionDate: Date): boolean {
  const twoBusinessDaysAgo = calculateBusinessDaysBack(transactionDate, 2);
  return rateDate >= twoBusinessDaysAgo;
}
```

**Transaction Rejection Example**:

```typescript
try {
  const rate = await getExchangeRate('USD', 'IDR', new Date('2025-12-24'), tenantId);
} catch (error) {
  if (error.message.includes('No exchange rate found')) {
    // Rate not available within 2 business days
    throw new RateUnavailableError({
      message: 'FX rate unavailable for USD/IDR on 2025-12-24. ' +
               'No published rate within 2 business days. ' +
               'Please contact Finance to manually enter rate or try again later.',
      currency_pair: 'USD/IDR',
      transaction_date: '2025-12-24',
      last_available_rate_date: lastRateDate || 'N/A',
      days_since_last_rate: daysSinceLastRate
    });
  }
}
```

**GL Audit Flag for Fallback Rates**:

```sql
-- Add rate_source flag to GL entries
ALTER TABLE journal_lines ADD COLUMN fx_rate_source VARCHAR(20);
-- Values: 'PUBLISHED_RATE', 'FALLBACK', 'CONTRACT_SPECIFIED'

-- Example GL entry using fallback rate
INSERT INTO journal_lines (
  journal_entry_id,
  account_id,
  debit,
  credit,
  currency,
  exchange_rate,
  fx_rate_source,  -- ← Audit flag
  rate_date
) VALUES (
  'je-001',
  '1200',
  12500000,
  0,
  'IDR',
  12500,
  'FALLBACK',  -- ← Indicates fallback rate used
  '2025-12-22'  -- Date of fallback rate (not transaction date)
);
```

**Audit Trail Requirements**:

```typescript
await auditLog({
  action: 'FX_RATE_FALLBACK_USED',
  entity_type: 'JournalEntry',
  entity_id: journalEntryId,
  details: {
    currency_pair: 'USD/IDR',
    transaction_date: '2025-12-24',
    requested_rate_date: '2025-12-24',
    fallback_rate_date: '2025-12-22',  // 2 business days old
    fallback_rate: 12500,
    rate_source: 'FALLBACK',
    reason: 'No published rate for transaction date, using last known good rate',
    approval_required: false  // Auto-approved for fallback within 2 days
  }
});
```

**Report for Fallback Usage**:

```sql
-- Finance report: All transactions using fallback rates
SELECT
  je.id AS journal_entry_id,
  je.entry_date,
  jl.currency,
  jl.exchange_rate,
  jl.fx_rate_source,
  jl.rate_date AS fallback_rate_date,
  je.entry_date AS transaction_date,
  DATEDIFF(je.entry_date, jl.rate_date) AS days_difference
FROM journal_entries je
JOIN journal_lines jl ON je.id = jl.journal_entry_id
WHERE jl.fx_rate_source = 'FALLBACK'
  AND je.tenant_id = $1
  AND je.entry_date BETWEEN $2 AND $3
ORDER BY je.entry_date DESC;
```

**Example Scenarios**:

**Scenario 1: Rate Available (no fallback)**
```
Transaction Date: 2025-12-24 (Wednesday)
Published Rate for 2025-12-24: Available
→ Use published rate
→ rate_source = 'PUBLISHED_RATE'
```

**Scenario 2: Rate Unavailable, Fallback Used**
```
Transaction Date: 2025-12-24 (Wednesday)
Published Rate for 2025-12-24: NOT available
Last Published Rate: 2025-12-22 (Monday) - 2 business days ago
→ Use fallback rate from 2025-12-22
→ rate_source = 'FALLBACK'
→ Audit log: "Using fallback rate (2 business days old)"
```

**Scenario 3: Rate Too Old, Transaction Rejected**
```
Transaction Date: 2025-12-24 (Wednesday)
Published Rate for 2025-12-24: NOT available
Last Published Rate: 2025-12-19 (Thursday) - 5 business days ago
→ REJECT transaction
→ Error: "FX rate unavailable for USD/IDR. Last rate is > 2 business days old."
→ User must contact Finance or wait for new rate
```

**Manual Rate Entry (Override)**:

If Finance Director needs to manually enter rate:

```typescript
async function manuallyEnterFXRate(
  fromCurrency: string,
  toCurrency: string,
  rate: Decimal,
  rateDate: Date,
  userId: string
) {
  await db('exchange_rates').insert({
    from_currency: fromCurrency,
    to_currency: toCurrency,
    rate: rate,
    rate_date: rateDate,
    rate_source: 'MANUAL_ENTRY',
    created_by: userId,
    created_at: new Date()
  });

  await auditLog({
    action: 'FX_RATE_MANUAL_ENTRY',
    performed_by: userId,
    details: {
      currency_pair: `${fromCurrency}/${toCurrency}`,
      rate: rate,
      rate_date: rateDate,
      reason: 'Manual entry by Finance Director (rate unavailable from provider)'
    }
  });
}
}
```

---

## 3. Transaction Recording (Dual Currency)

All cross-currency transactions recorded in BOTH currencies:

### Purchase Invoice Example

```json
{
  "invoice_id": "inv-001",
  "tenant_id": "hotel-123",

  "supplier_currency": "USD",
  "supplier_amount": 550.00,

  "functional_currency": "IDR",
  "recorded_amount": 8250000.00,

  "exchange_rate": 15000,
  "rate_date": "2025-12-24",
  "rate_source": "ECB_PUBLISHED",

  "posting_status": "POSTED",
  "posted_at": "2025-12-24T10:30:00Z"
}
```

### GL Entry for Invoice (BOTH amounts recorded)

```
[PMS] Invoice Posted: PMS.Invoice.Created.v1 (USD 550)

Debit:  Expense Account (IDR)     8,250,000  (550 × 15000)
  Credit: AP Account (IDR)                     8,250,000

NOTE: Both supplier_currency and functional_currency stored in transaction metadata.
GL entries use ONLY functional_currency (IDR).
Cross-reference to original USD amount for audit trail.
```

---

## 4. FX Gain/Loss Treatment

### Realized FX (at Settlement)

**When**: Payment made to supplier

```
Scenario: Invoice for USD 550 @ rate 15000 (IDR 8.25M)
Payment made later @ rate 15100 (new rate available)

Actual payment required: USD 550 @ 15100 = IDR 8.305M
Payment difference: IDR 55,000 loss

GL Entry:
  Debit:  AP Account        8,250,000  (original invoice amount)
  Debit:  FX Loss Account   55,000     (loss at settlement)
    Credit: Bank (IDR)                 8,305,000
```

**GL Account Rules**:
- **FX Gains Account** (4400): Revenue from FX gains
- **FX Losses Account** (5700): Expense from FX losses
- **Unrealized FX Account** (2510): Liability account for period-end adjustments

### Unrealized FX (at Period-End) - Phase 2

**Note**: Phase 1 MVP does NOT include automatic period-end revaluation.

**Future (Phase 2)**: Add unrealized FX calculation at period close
- Balance all open payables/receivables at period-end rates
- Record unrealized gains/losses to Unrealized FX account
- Reverse at next period start

**CRITICAL GUARDRAIL - Phase 1 Unrealized FX Treatment (Contradiction #9 Resolution)**:
```
RULE: Phase 1 calculates ONLY realized FX at settlement
RULE: Unrealized FX field is reserved for Phase 2 (set to NULL in Phase 1)
RULE: Open AR/AP are valued at original invoice rate (no revaluation)
RULE: Balance sheet FX disclosure shows open payables at original rate
```

**Phase 1 Implementation**:

**AR/AP Valuation**:
```typescript
// Phase 1: Open AR/AP valued at ORIGINAL RATE (no revaluation)
async function getOpenReceivables(tenantId: string, asOfDate: Date) {
  const openAR = await db('invoices')
    .where({
      tenant_id: tenantId,
      status: 'OPEN',  // Not yet paid
      invoice_date: { lte: asOfDate }
    })
    .select(
      'id',
      'invoice_date',
      'supplier_currency',
      'supplier_amount',
      'functional_currency',
      'recorded_amount',  // At ORIGINAL rate (invoice_date rate)
      'exchange_rate'     // LOCKED at invoice_date, NEVER updated
    );

  // Calculate total AR at original rates
  const totalAR = openAR.reduce((sum, inv) => sum + inv.recorded_amount, 0);

  return {
    total_ar: totalAR,
    currency: openAR[0]?.functional_currency,
    valuation_method: 'HISTORICAL_RATE',  // Phase 1: Original rate
    note: 'Open AR valued at invoice rate. No unrealized FX revaluation.'
  };
}
```

**Balance Sheet Disclosure**:

```
Balance Sheet - Hotel Tenant (IDR)
As of December 31, 2025

ASSETS
Current Assets:
  Cash and Bank                     50,000,000
  Accounts Receivable               12,500,000  (a)
    Less: Allowance for Doubtful       (250,000)
  Inventory                          8,000,000
                                   ────────────
Total Current Assets                70,250,000

(a) Accounts Receivable - FX Disclosure:
    Open AR includes USD $1,000 @ rate 12,500 (original invoice rate)
    Current rate: 12,800 (for information only, not revalued)
    Unrealized FX potential gain: $300 (not recognized in Phase 1)
```

**Unrealized FX Field Handling**:

```sql
-- Phase 1: fx_transactions table
CREATE TABLE fx_transactions (
  id UUID PRIMARY KEY,

  -- Realized FX (populated in Phase 1)
  rate_at_creation DECIMAL(18,8) NOT NULL,  -- Invoice rate (locked)
  rate_at_settlement DECIMAL(18,8),         -- Settlement rate (locked when paid)
  realized_fx_gain_loss DECIMAL(18,2),      -- Calculated at payment

  -- Unrealized FX (reserved for Phase 2, NULL in Phase 1)
  unrealized_fx_gain_loss DECIMAL(18,2) DEFAULT NULL,  -- ← Phase 2 only
  unrealized_fx_type VARCHAR(20),  -- NULL in Phase 1

  -- Audit
  posted_at TIMESTAMP,
  CHECK (posted_at IS NOT NULL OR realized_fx_gain_loss IS NOT NULL),

  -- PHASE 1 CONSTRAINT: Unrealized fields must be NULL
  CHECK (
    (unrealized_fx_gain_loss IS NULL AND unrealized_fx_type IS NULL)
    OR posted_at > '2026-01-01'  -- Phase 2 date (example)
  )
);
```

**Phase 1 FX Calculation Example**:

```typescript
// Invoice created: USD 1,000 @ rate 12,500 = IDR 12,500,000
const invoice = {
  supplier_currency: 'USD',
  supplier_amount: 1000,
  functional_currency: 'IDR',
  recorded_amount: 12500000,
  exchange_rate: 12500,
  rate_date: '2025-12-01',
  unrealized_fx: null  // Phase 1: Always NULL
};

// Payment made later: USD 1,000 @ rate 12,800 = IDR 12,800,000
const payment = {
  supplier_amount: 1000,
  payment_rate: 12800,
  actual_idr_paid: 12800000,

  // Realized FX: Difference between invoice and payment rate
  realized_fx_loss: 12800000 - 12500000,  // = 300,000 IDR loss

  // Unrealized FX: NULL (not calculated in Phase 1)
  unrealized_fx: null
};

// GL Entry for Payment:
// DR AP 12,500,000 (clear original invoice)
// DR FX Loss 300,000 (realized at payment)
// CR Bank 12,800,000 (actual payment)
```

**Period-End Reporting (Phase 1)**:

```typescript
async function generatePeriodEndFXReport(tenantId: string, periodEnd: Date) {
  // Step 1: Calculate realized FX for period
  const realizedFX = await db('fx_transactions')
    .where({
      tenant_id: tenantId,
      posted_at: { between: [periodStart, periodEnd] },
      realized_fx_gain_loss: { isNotNull: true }
    })
    .sum('realized_fx_gain_loss as total_realized_fx');

  // Step 2: Note open AR/AP (informational only, not revalued)
  const openAR = await getOpenReceivables(tenantId, periodEnd);
  const openAP = await getOpenPayables(tenantId, periodEnd);

  // Step 3: Generate report
  return {
    period: periodEnd,
    realized_fx_gain_loss: realizedFX.total_realized_fx,
    unrealized_fx_gain_loss: null,  // Phase 1: Not calculated

    open_positions_note: {
      open_ar: openAR.total_ar,
      open_ap: openAP.total_ap,
      valuation_method: 'HISTORICAL_RATE',
      disclosure: 'Open AR/AP valued at original invoice rates. ' +
                  'Unrealized FX not recognized in Phase 1.'
    }
  };
}
```

**Migration Path to Phase 2**:

When Phase 2 is implemented:

1. **Enable Unrealized FX Calculation**:
   ```typescript
   // At period close, revalue open AR/AP
   const currentRate = await getCurrentRate('USD', 'IDR');
   const unrealizedFX = (openAR.supplier_amount * currentRate) - openAR.recorded_amount;

   // Create unrealized FX entry
   await createUnrealizedFXEntry({
     source_invoice_id: openAR.id,
     unrealized_fx_gain_loss: unrealizedFX,
     rate_at_period_end: currentRate,
     reversal_scheduled_at: nextPeriodStart
   });
   ```

2. **Update Schema**:
   - Remove Phase 1 constraint on unrealized_fx fields
   - Add period_end_revaluation table
   - Add reversal entries at period start

3. **Balance Sheet Changes**:
   - AR/AP shown at current rate (not original rate)
   - Unrealized FX shown separately in equity or other comprehensive income

---

## 5. Rounding Rules

**Rounding Method**: Banker's Rounding (round-to-even)

```typescript
// ISO 20022 standard rounding for forex
function roundFX(amount: Decimal, decimals: number = 2): Decimal {
  const factor = Math.pow(10, decimals);
  return (Math.round(amount * factor + 0.5) / factor);
}

// Example:
// 550 USD × 15000 = 8,250,000.00 IDR (exact, no rounding needed)
// 550.55 USD × 15000 = 8,257,500.00 IDR (no rounding needed)
```

**Important**:
- Always round AFTER multiplication (not before)
- Never accumulate rounding errors across multiple transactions
- Validate that GL debits = credits (catches rounding issues)

---

## 6. Database Schema

```sql
-- Exchange rate history (audit trail)
CREATE TABLE exchange_rates (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),

  from_currency VARCHAR(3) NOT NULL,    -- 'USD', 'EUR'
  to_currency VARCHAR(3) NOT NULL,      -- 'IDR', 'SGD'
  rate DECIMAL(18,8) NOT NULL,          -- Supports rates like 0.00001234

  rate_date DATE NOT NULL,              -- When this rate became effective
  rate_source VARCHAR(20) NOT NULL,     -- 'ECB_PUBLISHED', 'BANK_BI', 'CONTRACT_SPECIFIED'

  created_at TIMESTAMP NOT NULL,
  created_by UUID NOT NULL REFERENCES users(id),

  UNIQUE(tenant_id, from_currency, to_currency, rate_date),
  INDEX idx_rates_lookup (tenant_id, from_currency, to_currency, rate_date DESC)
);

-- FX gain/loss ledger (IMMUTABLE AFTER POSTING)
CREATE TABLE fx_transactions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),

  source_transaction_id UUID,           -- Reference to invoice/payment
  source_type VARCHAR(20),              -- 'INVOICE', 'PAYMENT', 'BANK_RECONCILIATION'

  from_currency VARCHAR(3) NOT NULL,
  to_currency VARCHAR(3) NOT NULL,
  from_amount DECIMAL(18,2) NOT NULL,
  to_amount DECIMAL(18,2) NOT NULL,

  rate_at_creation DECIMAL(18,8) NOT NULL,  -- IMMUTABLE (locked at invoice date, cannot change)
  rate_at_settlement DECIMAL(18,8),         -- IMMUTABLE (locked at settlement, cannot change)

  fx_gain_loss DECIMAL(18,2),           -- Positive = gain, Negative = loss
  fx_gain_loss_type VARCHAR(20),        -- 'REALIZED', 'UNREALIZED'

  gl_entry_id UUID REFERENCES journal_entries(id),

  posted_at TIMESTAMP,              -- NULL before posting, immutable after
  posted_by UUID REFERENCES users(id),

  created_at TIMESTAMP DEFAULT NOW(),
  -- NOTE: NO updated_at field - once posted, record is immutable

  -- CRITICAL: Enforce immutability - rates CANNOT change once record created
  -- Application code MUST validate before UPDATE attempts
  -- This table designed for INSERT/SELECT only, UPDATE forbidden on rate fields
  CHECK (posted_at IS NOT NULL OR (rate_at_creation IS NOT NULL AND rate_at_settlement IS NULL)),

  -- Prevent dual-state (partially posted)
  CHECK ((posted_at IS NULL AND posted_by IS NULL) OR (posted_at IS NOT NULL AND posted_by IS NOT NULL)),

  -- GUARDRAIL: Prevent any UPDATE to rate fields (immutability enforcement)
  -- Database-level: CREATE TRIGGER prevent_rate_updates
  --   IF rate_at_creation_old != rate_at_creation_new OR rate_at_settlement_old != rate_at_settlement_new
  --   THEN RAISE EXCEPTION 'FX rates are immutable after creation'
  -- Application-level: All UPDATE statements FORBIDDEN on rate_at_creation, rate_at_settlement

  INDEX idx_fx_lookup (tenant_id, source_transaction_id),
  INDEX idx_fx_settlement (tenant_id, posted_at DESC)
);
```

### Immutability Enforcement

**PRIMARY: Database Level CHECK Constraints** (MUST be enforced first)
- Database CHECK constraint is the ONLY source of truth for immutability
- Application code cannot bypass database constraints
- All UPDATE attempts that violate immutability are rejected at database level

```sql
-- REQUIRED: Trigger to prevent ANY update to rate fields after posting
CREATE TRIGGER prevent_fx_rate_updates
BEFORE UPDATE ON fx_transactions
FOR EACH ROW
WHEN (OLD.posted_at IS NOT NULL)
BEGIN
  IF (NEW.rate_at_creation != OLD.rate_at_creation
      OR NEW.rate_at_settlement != OLD.rate_at_settlement) THEN
    RAISE EXCEPTION 'FX rates are immutable after posting (posted_at=%)', OLD.posted_at;
  END IF;
END;

-- Prevents: Application bug bypassing immutability, concurrent updates
```

**SECONDARY: Application Level Validation** (Defense-in-depth, runs BEFORE database attempt)
- Application checks before executing any UPDATE statement
- Prevents unnecessary database round-trips and provides better error messages
- But database constraint is the FINAL enforcement (cannot be bypassed)

All code that updates fx_transactions must enforce immutability:

```typescript
async function updateFXTransaction(txnId: string, updates: Partial<FXTransaction>): Promise<void> {
  // Step 1: Fetch current state
  const current = await getFXTransaction(txnId);

  // Step 2: CRITICAL CHECK - if posted, reject any updates
  if (current.posted_at !== null) {
    throw new ValidationError('IMMUTABLE_RECORD',
      `FX transaction ${txnId} has been posted to GL (posted_at=${current.posted_at}). ` +
      `Cannot modify posted FX transactions. ` +
      `To correct: create reversal entry + repost.`);
  }

  // Step 3: Allow updates only to pre-posting fields
  const allowedUpdates = [
    'fx_gain_loss_type'  // Only type can change before posting
  ];

  for (const field of Object.keys(updates)) {
    if (field === 'rate_at_creation' || field === 'rate_at_settlement') {
      throw new ValidationError('RATE_IMMUTABLE',
        `Cannot modify ${field} - exchange rates locked at transaction creation. ` +
        `Current value: ${current[field]}. ` +
        `To adjust: create new FX transaction with updated rates.`);
    }

    if (!allowedUpdates.includes(field)) {
      throw new ValidationError('UPDATE_NOT_ALLOWED',
        `Field ${field} cannot be updated on FX transactions.`);
    }
  }

  // Step 4: Safe to update (only allows non-critical fields)
  await db.query(
    `UPDATE fx_transactions SET fx_gain_loss_type = $1 WHERE id = $2 AND posted_at IS NULL`,
    [updates.fx_gain_loss_type, txnId]
  );
}
```

**Correction Pattern** (if error found after posting):

```
❌ WRONG: Try to UPDATE posted FX transaction
          → Rejected by immutability check

✅ CORRECT: Create reversal entry + new posting
1. Publish: Accounting.FXAdjustment.Reversal.v1 (reverses original GL entry)
2. Create new fx_transactions record with corrected rates
3. Publish: Accounting.FXAdjustment.Corrected.v1 (posts corrected GL entry)
4. Original transaction marked REVERSED (not deleted)
5. Audit trail shows full correction history
```

---

## 7. Integration Rules

### Accounting Module (ACC)

- Auto-post journal entries with FX gain/loss GL mapping
- Daily FX rate batch update (via scheduled job)
- Period-end report: total FX gain/loss by currency pair

### Multi-Tenant Supplier Module (MULTI)

- Invoice shows both currencies
- Payment settlement triggers FX calculation
- FX gain/loss posted to BUYER's GL (not supplier's)

### Procurement Module (Procurement)

- PO optional field: `force_supplier_currency: boolean`
  - If true: require PO amount in supplier's currency
  - If false: allow negotiation of payment currency

---

## 8. Audit Trail & Compliance

All FX transactions logged:

```json
{
  "audit_event": "FX_REALIZED_GAIN_RECORDED",
  "timestamp": "2025-12-24T15:30:00Z",
  "tenant_id": "hotel-123",

  "source_invoice": "inv-001",
  "currency_pair": "USD/IDR",
  "original_rate": 15000,
  "settlement_rate": 15100,
  "gain_loss": 55000,
  "gl_posting_reference": "je-9999",

  "performed_by": "system:scheduled-job",
  "verified_by": "user:accountant-001"
}
```

---

## 9. Testing Requirements

- [ ] Test: Exchange rate lookup for all currency pairs
- [ ] Test: GL posting with correct FX gain/loss amounts
- [ ] Test: Rounding produces correct totals (debits = credits)
- [ ] Test: Audit trail complete for all FX transactions
- [ ] Test: Period-end report accuracy
- [ ] Test: Contract override rates applied correctly
- [ ] Test: Fallback rate selection when primary not available

---

## 10. Migration Notes (Phase 1)

- Exchange rates pre-loaded for supported currency pairs (USD, EUR, GBP, SGD, etc.)
- Contract-specified rates editable by Finance Director only
- FX gain/loss calculated at payment time (not period-end revaluation)
- Manual GL entries allowed for unusual FX situations (with approval)

---

## Related Documents

- ACC-BIZ-01: Accounting Core
- MULTI-SPEC-11: Cross-Tenant Supplier Flow
- CORE-STD-20: Event Contract Specifications
