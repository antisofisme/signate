# Accounting Reconciliation, Controls & Audit Trail

> **Business Standard #3**: Reconciliation Rules, Entry Lifecycle, Corrections & Audit Controls
>
> **Last Updated**: 2025-12-13
> **Status**: ✅ Standard Approved
> **Related**: BIZ-01 (Core Accounting), BIZ-02 (Advanced), STD-16 (Smart Suggestions)

---

## Overview

This standard governs how entries are created, modified, corrected, and reconciled. It ensures data integrity through controlled edit windows, clear audit trails, transparent correction linkage, and reconciliation rules.

**Key Principles**:
- ✅ Prevention: Design forms to prevent wrong data entry (STD-15)
- ✅ Transparency: Full audit trail, never hide changes
- ✅ Control: Edit windows, approval gates, period locks
- ✅ Reconciliation: Auto-match with human review, clear rules
- ✅ Correction: Reversal + new entry for post-24h changes

---

## 1. Entry Lifecycle & States

### 1.1 Entry States

```
┌──────────┐
│  DRAFT   │  Entry created but not posted
│ (Editable)│ • All fields can be changed
└────┬─────┘ • No GL impact
     │ [SAVE]
     ↓
┌──────────┐
│ POSTED   │  Entry posted to GL
│(Editable)│ • GL entries created
└────┬─────┘ • Can edit if <24h & conditions met
     │ • Other restrictions: period lock, reconciled
     │ [EDIT] or [REVERSE & REPOST]
     ↓
┌──────────┐
│ LOCKED   │  Entry locked (cannot edit)
│(Read-only)│ • Period closed (year-end, audit)
└────┬─────┘ • Entry reconciled to bank/AP/AR
     │ • Can only view, not modify
     │ [VIEW HISTORY]
     ↓
┌──────────┐
│ ARCHIVED │  Entry archived (historical)
│(Read-only)│ • Moved to archive storage
└──────────┘ • Still auditable
```

### 1.2 State Transition Rules

```
DRAFT → POSTED:
  Prerequisites:
    ✓ All required fields filled
    ✓ Validation passed (STD-02)
    ✓ Form constraints satisfied (STD-15)
    ✓ Approval obtained (if required)
  Action: Create GL entries, update accounts

POSTED ↔ POSTED (EDIT):
  Conditions:
    ✓ Entry is <24 hours old
    ✓ Period is not locked
    ✓ Entry not reconciled
    ✓ Approval obtained (context-based)
  Action: Record change, update GL, maintain audit trail

POSTED → REVERSAL + REPOST:
  When:
    • Entry is >24 hours old
    • Entry reconciled
    • Period locked
    • High-risk field changed
  Action: Create reversal entry + new corrected entry

POSTED → LOCKED:
  When:
    • Period close triggered
    • Entry reconciled to bank/AR/AP
    • Manual lock by manager
  Action: Prevent any edits

LOCKED → POSTED (UNFREEZE):
  Only by: Director+ permission
  Use: Only if manual lock or period reopened
  Action: Restore editability
```

---

## 2. Edit Window & Approval Rules

### 2.1 Edit Window Decision Tree

```
User clicks EDIT on transaction

┌─ CHECK: Same day?
│  YES → Check other conditions
│  NO  → FORCE REVERSAL + REPOST (skip to 2.3)
│
├─ CHECK: Period locked?
│  YES → NOT ALLOWED (locked)
│  NO  → Continue
│
├─ CHECK: Reconciled?
│  YES → FORCE REVERSAL + REPOST
│  NO  → Continue
│
├─ CHECK: Field being edited?
│  Low-risk (memo, description)  → AUTO APPROVE
│  Medium-risk (amount, date)    → MANAGER APPROVE
│  High-risk (COA, type)         → FORCE REVERSAL
│
├─ CHECK: User permission
│  Creator editing own entry <Rp 5M → AUTO APPROVE
│  Creator editing >Rp 5M           → MANAGER APPROVE
│  Other user editing               → MANAGER + CONTEXT
│
└─ DECISION: Allow edit or force reversal
```

### 2.2 Direct Edit Approval (Same-Day Only)

**Conditions for DIRECT EDIT**:

```
All must be true:
  ✓ Entry created today (same calendar day)
  ✓ Period is open (not locked)
  ✓ Entry not reconciled to bank/AR/AP
  ✓ Not already edited 3+ times today
  ✓ Field being edited is not HIGH-RISK
```

**Field Risk Classification**:

```
LOW RISK (auto-approve, same-day):
  • Description, memo, notes
  • Internal reference, tags
  • Customer notes (non-financial)
  → Auto-approve (no manager needed)

MEDIUM RISK (manager approval, same-day):
  • Amount adjustment (±5% tolerance)
  • Date change (±3 days)
  • Customer/vendor selection
  → Require manager approval
     If amount > Rp 5M → require director
     If amount > Rp 50M → require CFO

HIGH RISK (force reversal, no same-day edit):
  • COA/account change
  • Entry type change (invoice → journal)
  • Tax treatment change
  • Reconciliation status change
  → MUST use Reversal + New Entry
     Even if same-day
```

**Auto-Approval Criteria**:

```
Auto-approve if ALL true:
  ✓ User = creator
  ✓ Field = LOW RISK
  ✓ Amount < Rp 5M (or no amount involved)
  ✓ Edit count today < 3
  ✓ Same day

Otherwise → Require manager approval
```

### 2.3 Reversal + New Entry (>24h or High-Risk)

**When to Use**:

```
❌ Cannot use DIRECT EDIT if:
  • Entry is >24 hours old
  • Period is locked
  • Entry is reconciled
  • Field being changed is HIGH-RISK
  • User permission insufficient

✅ MUST use REVERSAL + NEW ENTRY instead
```

**Process**:

```
Step 1: Create Reversal Entry
  Entry: REVERSAL-INV-001
  Purpose: Negate original entry
  GL:
    Debit original_account -amount
    Credit original_counter_account -amount
  Links to: INV-001 (original_entry_id)

Step 2: Create Corrected Entry
  Entry: INV-001-V2
  Purpose: Correct entry with new values
  GL:
    Debit new_account +amount
    Credit new_counter_account +amount
  Links to: INV-001 (original_entry_id), REVERSAL-INV-001

Step 3: Request Approval
  Approval level depends on:
    • Amount of correction
    • Who is correcting (creator vs other)
    • Type of correction
  Example:
    If amount > Rp 5M → Manager approval
    If >24h & amount > Rp 10M → Manager + Director
    If period locked → Director approval

Step 4: Execute
  Create GL entries for both reversal and correction
  Link them together
  Record audit trail

Step 5: Audit Trail
  Original entry remains visible
  Change history shows: Reversal date, corrector, approver, reason
  GL shows both reversal and correction with links
```

**UI Display**:

```
User clicks VIEW TRANSACTION on INV-001

Current State:
  Amount: Rp 10,000,000
  COA: 4103 (Corrected)
  Status: POSTED

Change History:
  Version 1: 2025-12-13 09:00 (ORIGINAL)
    Amount: Rp 10M, COA: 4101
    Created by: manager123

  Correction #1: 2025-12-13 11:05 (DIRECT EDIT, SAME-DAY)
    COA: 4101 → 4102
    Edited by: manager123
    Approval: AUTO (low-risk field)

  Correction #2: 2025-12-14 14:10 (REVERSAL + REPOST)
    COA: 4102 → 4103
    Reason: "Corrected revenue classification per CFO review"
    Edited by: manager123
    Approval: DIRECTOR (director456, 2025-12-14 14:30)

GL Impact:
  Line 1: Debit 4101 -Rp 10M (Reversal of correction #1)
  Line 2: Debit 4102 +Rp 10M (Correction #1)
  Line 3: Debit 4102 -Rp 10M (Reversal of correction #2)
  Line 4: Debit 4103 +Rp 10M (Correction #2)
  All linked to INV-001
```

---

## 3. Audit Trail & Change Tracking

### 3.1 What Gets Tracked

```
For EVERY change (edit or reversal):

WHO:
  • user_id (who made change)
  • user.name, user.role
  • created_by (original entry creator)

WHAT:
  • field_name (which field changed)
  • old_value
  • new_value
  • change_type (DIRECT_EDIT, REVERSAL_REPOST)

WHEN:
  • timestamp (when change made)
  • created_at (original entry date)
  • days_since_original (how old was entry)

WHY:
  • reason (why was change made)
  • approval_status (approved/rejected/pending)
  • approval_by (who approved)
  • approval_reason (if rejected)

CONTEXT:
  • period_id (fiscal period)
  • module (accounting, POS, etc)
  • transaction_type (invoice, journal, etc)
  • amount (for compliance threshold)
```

### 3.2 Change History Data Model

```python
class TransactionChangeHistory(Base):
    __tablename__ = 'transaction_change_history'

    # Identification
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey('tenants.id'), NOT NULL, index=True)  # REQUIRED - multi-tenant isolation
    transaction_id = Column(UUID, ForeignKey('transactions.id'), index=True)
    change_number = Column(Integer)  # 1st change, 2nd change, etc

    # Original vs Current state
    original_transaction_id = Column(UUID)  # If reversal, points to original
    is_reversal = Column(Boolean, default=False)

    # What changed
    field_name = Column(String)  # 'coa_id', 'amount', 'description'
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)

    # Who & When
    changed_by = Column(UUID, ForeignKey('users.id'), index=True)
    changed_at = Column(DateTime, default=utcnow, index=True)

    # Approval
    approval_status = Column(Enum)  # AUTO_APPROVED, PENDING, APPROVED, REJECTED
    approval_level = Column(String)  # 'AUTO', 'MANAGER', 'DIRECTOR', 'CFO'
    approval_by = Column(UUID, ForeignKey('users.id'), nullable=True)
    approval_at = Column(DateTime, nullable=True)
    approval_reason = Column(String, nullable=True)

    # Why
    change_reason = Column(String)  # "Corrected COA per CFO review"
    change_type = Column(Enum)  # DIRECT_EDIT, REVERSAL_REPOST, CORRECTION

    # Context
    period_id = Column(UUID, ForeignKey('periods.id'))
    module = Column(String)  # 'accounting', 'pos', 'pms'
    transaction_amount = Column(Numeric)  # For compliance threshold

    # GL Impact
    gl_reversal_lines = Column(JSON)  # If reversal, these GL lines created
    gl_correction_lines = Column(JSON)  # Corrected GL lines

    # Constraints
    __table_args__ = (
        Index('idx_transaction_change', 'tenant_id', 'transaction_id', 'change_number'),  # UPDATED: tenant_id first for multi-tenant filtering
        Index('idx_changed_at', 'tenant_id', 'changed_at'),  # UPDATED: tenant_id for isolation
        ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
```

### 3.3 Audit Trail Query

```sql
-- View full change history for transaction (UPDATED: added tenant_id filter)
SELECT
  change_number,
  field_name,
  old_value,
  new_value,
  users.full_name as changed_by,
  changed_at,
  approval_status,
  approval_users.full_name as approved_by,
  approval_at,
  change_reason
FROM transaction_change_history
LEFT JOIN users ON transaction_change_history.changed_by = users.id
LEFT JOIN users approval_users ON transaction_change_history.approval_by = approval_users.id
WHERE transaction_change_history.tenant_id = $1  -- Multi-tenant isolation
  AND transaction_change_history.transaction_id = $2  -- Specific transaction
ORDER BY changed_at ASC;

-- Result shows full timeline of edits with who/what/when/why
```

---

## 4. Reconciliation Rules & Auto-Matching

### 4.1 Reconciliation Types

```
BANK RECONCILIATION:
  Match: Bank statement transactions ←→ GL entries
  Frequency: Daily/weekly
  Rule: Amount exact, date within ±3 days

ACCOUNTS RECEIVABLE (AR):
  Match: Customer payments ←→ Invoices
  Frequency: Daily
  Rule: Amount exact or within tolerance, match to invoice

ACCOUNTS PAYABLE (AP):
  Match: Vendor invoices ←→ POs ←→ Receiving
  Frequency: Daily
  Rule: 3-way match (PO, invoice, receipt)

GENERAL LEDGER:
  Verify: Total debits = total credits
  Frequency: Daily, especially for period close
```

### 4.2 Bank Reconciliation Rules

```
RULE 1: Amount Match
  IF bank_amount == gl_amount
    Confidence: 50 points
  ELSE IF abs(bank_amount - gl_amount) < 1000
    Confidence: 30 points
  ELSE
    Confidence: 0 points (no match)

RULE 2: Date Proximity
  IF date_diff == 0 days
    Confidence: +30 points
  ELSE IF date_diff <= 3 days
    Confidence: +20 points
  ELSE IF date_diff <= 7 days
    Confidence: +10 points
  ELSE
    Confidence: 0 points

RULE 3: Description Match (Fuzzy)
  similarity = fuzzy_string_match(bank_desc, gl_desc)
  Confidence: similarity * 10 points (0-10)

RULE 4: Account History
  IF (bank_account, gl_account) previously matched
    Confidence: +10 points
  ELSE
    Confidence: 0 points

TOTAL CONFIDENCE = sum of all rules (max 100)

Threshold:
  >= 95% → Auto-match (high confidence, pre-check)
  70-94% → Suggest match (require user confirmation)
  < 70%  → Don't match (flag for manual review)
```

### 4.3 Reconciliation Workflow (Semi-Automatic)

```
Step 1: Import & Parse
  Import bank statement (CSV, XML, API)
  Parse transactions (date, amount, description, reference)

Step 2: Calculate Matches
  For each bank transaction:
    For each GL entry:
      Calculate confidence score (using rules above)
    Sort by confidence

Step 3: Present Suggestions (STD-16)
  ┌─────────────────────────────────┐
  │ Bank Reconciliation (35 txns)   │
  ├─────────────────────────────────┤
  │ Auto-Matched (30): >95%         │ ← Pre-checked
  │ Needs Review (5): 70-95%        │ ← User checks
  │ Low Confidence (0): <70%        │
  │                                 │
  │ [CONFIRM] [CANCEL]              │
  └─────────────────────────────────┘

Step 4: User Confirms
  • Accept auto-matched
  • Review medium-confidence matches
  • Skip uncertain matches
  • Add notes on unmatched

Step 5: Approval (If Needed)
  If amount > threshold:
    Request manager review

Step 6: Post GL
  Create reconciliation entries:
    Debit 1010 (Cash)
    Credit various (based on matched entries)

  Link all matched transactions:
    bank_txn_id → gl_entry_id

Step 7: Mark as Reconciled
  GL entries status: RECONCILED
  Cannot edit without reversal + repost

Step 8: Audit Trail
  "35 bank transactions reconciled
   30 auto-matched, 5 manual confirmation
   Approved by: manager123
   Date: 2025-12-13
   Reconciliation ID: RECON-20251213-001"
```

---

## 5. AR Reconciliation (Customer Payments)

### 5.1 AR Matching Rules

```
RULE: Match Payment ←→ Invoice

Customer payments received:
  • Check deposit: Rp 10M from Guest XYZ
  • Bank ref: CHK-12345

GL entries (AR):
  • INV-001: Rp 10M (Guest XYZ, Dec 1)
  • INV-002: Rp 7M (Guest XYZ, Dec 5)

Matching Logic:
  1. Filter by customer: Only show INV-001, INV-002
  2. Sort by amount: INV-001 (Rp 10M) matches exactly
  3. Confidence: 99% (exact match to open invoice)

Result:
  Payment Rp 10M ←→ INV-001 (Rp 10M)
  Remaining: INV-002 (Rp 7M) still outstanding

UI:
  ┌─────────────────────────────────┐
  │ Payment: Rp 10M (Check #12345)  │
  ├─────────────────────────────────┤
  │ Customer: Guest XYZ             │
  │                                 │
  │ Match Suggestion:               │
  │ □ INV-001 Rp 10M [99% match]    │
  │   [✓ ACCEPT] [✗ REJECT]         │
  │                                 │
  │ Other open invoices:            │
  │ • INV-002 Rp 7M (partial?)      │
  │ • INV-003 Rp 5M (different cust)│
  │                                 │
  │ [CONFIRM] [CANCEL]              │
  └─────────────────────────────────┘
```

### 5.2 AR Aging Report

```
Customer: Guest XYZ
Total outstanding: Rp 22M

Invoice | Date       | Amount   | Days Overdue | Status
─────────────────────────────────────────────────────────
INV-001 | 2025-12-01 | Rp 10M   | 12 days      | RECONCILED
INV-002 | 2025-12-05 | Rp 7M    | 8 days       | OPEN
INV-003 | 2025-12-10 | Rp 5M    | 3 days       | OPEN

Action:
  • INV-001: Paid (reconciled)
  • INV-002: Send reminder (>7 days)
  • INV-003: Monitor (recent)

Audit:
  INV-001 reconciliation history:
    Invoice created: 2025-12-01
    Payment received: 2025-12-13
    Matched by: system (auto-reconciliation)
    Confidence: 99%
    Timeline: 12 days

  [View full history] [Print reconciliation]
```

---

## 6. Period Close Controls

### 6.1 Period Close Workflow

```
Step 1: PERIOD OPEN
  • All entries editable
  • Reconciliation in progress
  • Warnings if out-of-balance

Step 2: PERIOD PRE-CLOSE
  System checks:
    ✓ All GL transactions posted
    ✓ Bank reconciliation complete
    ✓ AR reconciliation >95% matched
    ✓ AP reconciliation complete
    ✓ No pending journal entries
    ✓ All approval workflows completed

  If any fail:
    Alert: "Cannot close: Bank reconciliation incomplete"
    Action: Complete before close

Step 3: PERIOD CLOSE
  Manager/CFO triggers close
  System:
    1. Lock all entries in period
    2. Archive old transactions
    3. Create closing journal entries
    4. Calculate trial balance
    5. Generate financial statements

  Entries are now LOCKED (read-only)
  Cannot edit (even reversal requires director approval)

Step 4: PERIOD LOCKED
  • All entries archived/locked
  • Financial statements finalized
  • Audit-ready

Step 5: PERIOD REOPEN (If Needed)
  Director only
  Reason: Correction discovered, missing entry
  Unlock selected entries
  Allow correction via reversal + repost
  Re-lock after correction
  Update financial statements
```

---

## 7. Report Clean, Audit Transparent

### 7.1 Financial Report (Clean View)

```
INCOME STATEMENT - December 2025
═══════════════════════════════════

Revenue                           Rp 100,000,000
  Room Sales           Rp 80M
  F&B Sales            Rp 20M

Expenses                          Rp 60,000,000
  Salaries             Rp 30M
  Utilities            Rp 15M
  Other                Rp 15M

─────────────────────────────────
Net Income                        Rp 40,000,000

Report shows FINAL numbers only
No reversal clutter
No change history visible
Clean financial view
```

### 7.2 Audit Trail (Transparent View)

```
For each line on report:
  Click [VIEW HISTORY] or [DRILL-DOWN]

Example: "Room Sales Rp 80M"

Transactions in Room Sales (COA 4101):
  • INV-001: Rp 10M (created Dec 1, edited once)
  • INV-002: Rp 15M (created Dec 5, no edits)
  • INV-003: Rp 55M (created Dec 10, no edits)

For INV-001, click [VIEW CHANGES]:
  Original: Rp 10M (created Dec 1 by manager123)
  Edit 1: COA 4101 → 4102 (Dec 1 11:00 by manager123)
          COA 4102 → 4101 (reversal) / COA 4101 → 4101 (repost)

  GL showing:
    Line 1: Debit 4101 Rp 10M (original)
    Line 2: Debit 4101 -Rp 10M (reversal of change)
    Line 3: Debit 4101 +Rp 10M (correction)
    Net: Debit 4101 Rp 10M ✓

Audit shows:
  ✓ What changed (COA corrected)
  ✓ Who changed it (manager123)
  ✓ When changed (Dec 1)
  ✓ Why changed (misclassification)
  ✓ Approval (auto-approved, same-day edit)
  ✓ Full GL trail (both reversal and correction visible)
```

---

## 8. Context-Based Entry Controls

### 8.1 Control Matrix by Module

```
Module      | Direct Edit Window | High-Risk Fields | Approval Needed
─────────────────────────────────────────────────────────────────────
Accounting  | 24h (tight)        | COA, Type        | Manager (>Rp 5M)
            |                    |                  | Director (>Rp 50M)
────────────┼────────────────────┼──────────────────┼─────────────────
AR/AP       | 24h (tight)        | COA, Customer    | Manager always
            |                    |                  | (financial impact)
────────────┼────────────────────┼──────────────────┼─────────────────
POS         | 24h (tight)        | Amount, Item     | Manager (>Rp 1M)
            |                    |                  | (daily sales)
────────────┼────────────────────┼──────────────────┼─────────────────
Inventory   | 24h (medium)       | Quantity, Cost   | Manager (>Rp 5M)
            |                    |                  | (cost impact)
────────────┼────────────────────┼──────────────────┼─────────────────
HRM/Payroll | 24h (medium)       | Amount, Tax      | HR Manager always
            |                    |                  | (employee impact)
```

---

## 9. Implementation Checklist

- [ ] **Define entry states**: DRAFT → POSTED → LOCKED → ARCHIVED
- [ ] **Create edit window logic**: Same-day check, period lock, reconciliation check
- [ ] **Field risk classification**: Low/medium/high risk with approval rules
- [ ] **Approval workflow**: Auto-approve vs manager vs director vs CFO
- [ ] **Change tracking**: Record old→new for all changes
- [ ] **Reversal + repost**: Process for >24h or high-risk changes
- [ ] **Reconciliation rules**: Confidence scoring, auto-matching
- [ ] **Period close**: Lock entries, prevent edits, require approval to reopen
- [ ] **Audit queries**: Show full change history with who/what/when/why
- [ ] **Report views**: Clean report + drill-down to audit trail
- [ ] **Testing**: Test edit windows, approval workflows, reconciliation logic

---

## 10. Key Principles Summary

```
✅ Entry Lifecycle: DRAFT → POSTED → (EDIT/REVERSAL) → LOCKED → ARCHIVED

✅ Same-Day Edit: Only if <24h AND not reconciled AND conditions met
   → Auto-approve for low-risk, manager approval for medium/high risk

❌ >24h Edit: Force reversal + new entry
   → Preserves period integrity
   → Clear audit trail
   → Compliant with standards

✅ Audit Trail: Track all changes (who, what, when, why, approval)
   → User can drill-down anytime
   → Easy to investigate

✅ Report Clean, Audit Transparent:
   → Financial reports show final values only
   → Full history available via "View History"
   → GL shows both reversals AND corrections (linked)

✅ Reconciliation: Semi-automatic with user confirmation
   → System suggests matches (STD-16)
   → User reviews and confirms
   → GL posted only after approval

✅ Context Matters:
   → Edit window depends on time, reconciliation, period status
   → Approval thresholds depend on amount, module, user role
   → High-risk fields always require reversal approach
```

