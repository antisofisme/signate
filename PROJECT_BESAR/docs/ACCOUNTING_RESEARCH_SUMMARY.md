# Accounting Standards Research Summary

> Kompilasi hasil research standar akuntansi internasional dan Indonesia untuk Enterprise Hospitality Platform.
>
> **Date**: 2025-12-07
> **Purpose**: Reference sebelum menentukan keputusan di BUSINESS_ACCOUNTING_STANDARDS.md

---

## Table of Contents

1. [Chart of Accounts (CoA) Standards](#1-chart-of-accounts-coa-standards)
2. [Journal Entry & Double-Entry](#2-journal-entry--double-entry)
3. [Multi-Currency Standards](#3-multi-currency-standards)
4. [Tax Standards (Indonesia)](#4-tax-standards-indonesia)
5. [Period & Closing Standards](#5-period--closing-standards)
6. [Financial Reporting Standards](#6-financial-reporting-standards)
7. [Bank & Payment Standards](#7-bank--payment-standards)
8. [Accounts Receivable Standards](#8-accounts-receivable-standards)
9. [Accounts Payable Standards](#9-accounts-payable-standards)
10. [Audit Trail & Compliance](#10-audit-trail--compliance)
11. [Industry-Specific: USALI](#11-industry-specific-usali)

---

## 1. Chart of Accounts (CoA) Standards

### 1.1 IFRS/GAAP Standard Structure

**Account Classification (5 Main Categories):**

| Code | Category | Type | Normal Balance |
|------|----------|------|----------------|
| 1xxx | Assets | Balance Sheet | Debit |
| 2xxx | Liabilities | Balance Sheet | Credit |
| 3xxx | Equity | Balance Sheet | Credit |
| 4xxx | Revenue | Income Statement | Credit |
| 5xxx-9xxx | Expenses | Income Statement | Debit |

**Sub-classification Example:**

```
1xxx - ASSETS
├── 10xx - Current Assets
│   ├── 1010 - Cash & Cash Equivalents
│   ├── 1020 - Bank Accounts
│   ├── 1030 - Accounts Receivable
│   ├── 1040 - Inventory
│   └── 1050 - Prepaid Expenses
├── 11xx - Non-Current Assets
│   ├── 1110 - Property, Plant & Equipment
│   ├── 1120 - Intangible Assets
│   └── 1130 - Long-term Investments
└── 12xx - Other Assets

2xxx - LIABILITIES
├── 20xx - Current Liabilities
│   ├── 2010 - Accounts Payable
│   ├── 2020 - Accrued Expenses
│   ├── 2030 - Tax Payable
│   └── 2040 - Short-term Debt
└── 21xx - Non-Current Liabilities
    ├── 2110 - Long-term Debt
    └── 2120 - Deferred Tax

3xxx - EQUITY
├── 3010 - Share Capital
├── 3020 - Retained Earnings
└── 3030 - Other Comprehensive Income

4xxx - REVENUE
├── 4010 - Operating Revenue
├── 4020 - Other Income
└── 4030 - Interest Income

5xxx-9xxx - EXPENSES
├── 5xxx - Cost of Sales
├── 6xxx - Operating Expenses
├── 7xxx - Administrative Expenses
├── 8xxx - Financial Expenses
└── 9xxx - Tax Expenses
```

### 1.2 Numbering Schemes

**Option A: 4-Digit System**
- Simple, mudah diingat
- Cocok untuk bisnis kecil-menengah
- Contoh: 1010, 2010, 3010, 4010

**Option B: 6-Digit System**
- Lebih detail, support sub-accounts
- Cocok untuk multi-departemen
- Contoh: 101001, 201001, 301001

**Option C: 8-Digit System (Recommended for Enterprise)**
- Maximum flexibility
- Format: XX-XX-XX-XX
  - 2 digit: Main category
  - 2 digit: Sub-category
  - 2 digit: Detail
  - 2 digit: Sub-detail/Department
- Contoh: 10-10-01-01

**Option D: Alphanumeric**
- Contoh: A1010, L2010, E3010
- Lebih readable tapi less sortable

### 1.3 Account Attributes

Setiap account harus memiliki:
- **Account Code**: Unique identifier
- **Account Name**: Descriptive name
- **Account Type**: Asset/Liability/Equity/Revenue/Expense
- **Normal Balance**: Debit/Credit
- **Is Active**: Boolean
- **Is Header**: Boolean (parent account untuk grouping)
- **Parent Account**: For hierarchical structure
- **Currency**: Default currency (optional)
- **Tax Code**: Associated tax treatment (optional)
- **Department**: For departmental accounting (optional)

---

## 2. Journal Entry & Double-Entry

### 2.1 Double-Entry Principles

**Fundamental Equation:**
```
Assets = Liabilities + Equity

Atau expanded:
Assets = Liabilities + (Capital + Revenue - Expenses - Drawings)
```

**Debit/Credit Rules:**

| Account Type | Increase | Decrease | Normal Balance |
|--------------|----------|----------|----------------|
| Assets | Debit | Credit | Debit |
| Liabilities | Credit | Debit | Credit |
| Equity | Credit | Debit | Credit |
| Revenue | Credit | Debit | Credit |
| Expenses | Debit | Credit | Debit |

**Mnemonic: DEAD CLIC**
- **D**ebit: **E**xpenses, **A**ssets, **D**rawings
- **C**redit: **L**iabilities, **I**ncome, **C**apital

### 2.2 Journal Entry Structure

```
Date: [Transaction Date]
Journal Entry #: [Unique Reference]
Reference: [Source Document]

| Account Code | Account Name | Debit | Credit |
|--------------|--------------|-------|--------|
| 1020         | Bank Account | 1,000 |        |
| 4010         | Sales Revenue|       | 1,000  |

Description: [Narrative description]
Created By: [User]
Approved By: [Approver - if required]
```

### 2.3 Journal Entry Types

| Type | Description | Auto/Manual | Reversible |
|------|-------------|-------------|------------|
| **General Journal (GJ)** | Manual entries | Manual | Yes |
| **Sales Journal (SJ)** | Customer invoices | Auto from AR | No |
| **Purchase Journal (PJ)** | Vendor invoices | Auto from AP | No |
| **Cash Receipt (CR)** | Incoming payments | Auto | No |
| **Cash Disbursement (CD)** | Outgoing payments | Auto | No |
| **Payroll Journal (PY)** | Salary processing | Auto | No |
| **Adjusting Journal (AJ)** | Period-end adjustments | Manual | Yes |
| **Closing Journal (CJ)** | Year-end closing | Auto | No |
| **Reversing Journal (RJ)** | Reverse accruals | Auto | N/A |

### 2.4 Accrual vs Cash Basis

**Accrual Basis (IFRS/PSAK Required):**
- Revenue recognized when earned (not when cash received)
- Expenses recognized when incurred (not when cash paid)
- Requires adjusting entries at period end

**Cash Basis:**
- Revenue recognized when cash received
- Expenses recognized when cash paid
- Simpler but not IFRS/PSAK compliant

**Indonesia Requirement:** PSAK mengharuskan accrual basis untuk laporan keuangan.

### 2.5 Matching Principle

- Expenses harus di-match dengan revenue yang terkait
- Contoh: COGS di-record saat revenue dari penjualan di-record
- Deferred expenses: Prepaid dibagi rata selama periode manfaat

---

## 3. Multi-Currency Standards

### 3.1 IAS 21 - Effects of Foreign Exchange

**Key Concepts:**

| Term | Definition |
|------|------------|
| **Functional Currency** | Mata uang utama operasional perusahaan |
| **Presentation Currency** | Mata uang untuk laporan keuangan |
| **Foreign Currency** | Mata uang selain functional currency |
| **Spot Rate** | Kurs pada tanggal transaksi |
| **Closing Rate** | Kurs pada tanggal laporan |
| **Average Rate** | Rata-rata kurs selama periode |

**Translation Rules:**

| Item | Rate Used |
|------|-----------|
| Monetary Assets (Cash, AR, AP) | Closing Rate |
| Non-Monetary Assets (Inventory, PPE) | Historical Rate |
| Revenue & Expenses | Transaction Date Rate or Average |
| Equity | Historical Rate |

### 3.2 Exchange Rate Management

**Rate Sources:**
- Bank Indonesia (BI) - Official rate
- Kurs Pajak (Tax rate) - For tax purposes
- Commercial bank rates

**Recording Methods:**
1. **Single-rate method**: Satu rate per hari
2. **Dual-rate method**: Buy rate & Sell rate terpisah

### 3.3 Realized vs Unrealized Gains/Losses

**Realized (Gain/Loss sudah terjadi):**
```
Contoh: Invoice $1,000 @ Rp 15,000 = Rp 15,000,000
Payment received @ Rp 15,500 = Rp 15,500,000
Realized Gain = Rp 500,000
```

**Unrealized (Gain/Loss belum terjadi - revaluasi):**
```
Contoh: AR $1,000 @ Rp 15,000 (saat invoice)
Closing rate @ Rp 15,200
Unrealized Gain = Rp 200,000 (masuk OCI atau P&L)
```

**Journal Entries:**

Realized Gain:
```
Dr. Bank Account (Rp 15,500,000)
    Cr. Accounts Receivable (Rp 15,000,000)
    Cr. Foreign Exchange Gain (Rp 500,000)
```

Unrealized Gain (Revaluation):
```
Dr. Accounts Receivable (Rp 200,000)
    Cr. Unrealized FX Gain (Rp 200,000)
```

---

## 4. Tax Standards (Indonesia)

### 4.1 PPN (Pajak Pertambahan Nilai)

**Rate:** 12% (per January 2025, naik dari 11%)

**Mekanisme:**
- **PPN Keluaran (Output VAT)**: Dipungut dari customer saat jual
- **PPN Masukan (Input VAT)**: Dibayar ke supplier saat beli
- **PPN Terutang**: PPN Keluaran - PPN Masukan

**Faktur Pajak:**
- Wajib untuk setiap transaksi > Rp 10,000,000
- Format elektronik (e-Faktur) mandatory
- Nomor seri dari DJP

**Journal Entry - Penjualan:**
```
Dr. Accounts Receivable    Rp 112,000,000
    Cr. Sales Revenue          Rp 100,000,000
    Cr. PPN Keluaran (2030)    Rp 12,000,000
```

**Journal Entry - Pembelian:**
```
Dr. Inventory              Rp 100,000,000
Dr. PPN Masukan (1060)     Rp 12,000,000
    Cr. Accounts Payable       Rp 112,000,000
```

### 4.2 PPh 21 (Pajak Penghasilan Karyawan)

**Metode TER (Tarif Efektif Rata-rata) - Berlaku 2024:**

| Kategori | Status | Penghasilan Bulanan | Tarif |
|----------|--------|---------------------|-------|
| A | TK/0 atau TK/1 | s/d 5.4 juta | 0% |
| A | TK/0 atau TK/1 | 5.4 - 5.65 juta | 0.25% |
| A | TK/0 atau TK/1 | 5.65 - 5.95 juta | 0.5% |
| ... | ... | ... | ... (progressive) |
| A | TK/0 atau TK/1 | > 1.4 milyar | 34% |

**Kategori:**
- **TER A**: TK/0, TK/1, K/0
- **TER B**: TK/2, TK/3, K/1, K/2
- **TER C**: K/3

**Journal Entry - Payroll:**
```
Dr. Salary Expense         Rp 10,000,000
    Cr. PPh 21 Payable         Rp 300,000
    Cr. Cash/Bank              Rp 9,700,000
```

### 4.3 PPh 23 (Pajak Penghasilan atas Jasa)

**Tarif:**
- **2%**: Sewa (kecuali tanah/bangunan), jasa teknik, jasa manajemen, jasa konsultan
- **15%**: Dividen, bunga, royalti (untuk WP dalam negeri)

**Journal Entry - Pembayaran Jasa:**
```
Dr. Consulting Expense     Rp 10,000,000
    Cr. PPh 23 Payable         Rp 200,000
    Cr. Accounts Payable       Rp 9,800,000
```

### 4.4 PPh 4(2) (Pajak Final)

**Tarif Sewa Tanah/Bangunan:** 10%

**Journal Entry - Terima Sewa:**
```
Dr. Bank                   Rp 9,000,000
Dr. PPh 4(2) - Prepaid     Rp 1,000,000
    Cr. Rental Income          Rp 10,000,000
```

### 4.5 Tax Reporting Periods

| Tax Type | Reporting | Due Date |
|----------|-----------|----------|
| PPN | Monthly SPT Masa | 20th of following month |
| PPh 21 | Monthly SPT Masa | 20th of following month |
| PPh 23 | Monthly SPT Masa | 20th of following month |
| PPh 4(2) | Monthly SPT Masa | 20th of following month |
| PPh Badan | Annual SPT Tahunan | 4 months after fiscal year |

---

## 5. Period & Closing Standards

### 5.1 Fiscal Year

**Options:**
- **Calendar Year**: January 1 - December 31 (default di Indonesia)
- **Custom Fiscal Year**: Mulai bulan lain (perlu approval DJP)

**Periods:**
- Monthly: 12 periods per year
- Quarterly: 4 periods per year
- Special Period 13: For adjustments

### 5.2 Period Locking

**Hierarchy:**
1. **Soft Close**: Warning saat posting ke period lama
2. **Hard Close**: Block posting ke period lama
3. **Year-End Close**: Permanent close, generate opening balances

**Best Practice:**
- Soft close setelah monthly reconciliation selesai
- Hard close setelah management review/approval
- Year-end close setelah audit selesai

### 5.3 Month-End Closing Procedures

**Checklist:**

1. **Bank Reconciliation**
   - Match bank statement dengan GL
   - Identify outstanding checks/deposits
   - Record bank charges/interest

2. **AR Reconciliation**
   - Verify AR aging
   - Identify doubtful accounts
   - Record allowance for doubtful accounts

3. **AP Reconciliation**
   - Match vendor statements
   - Verify accrued expenses
   - Process cut-off adjustments

4. **Inventory**
   - Physical count (if applicable)
   - Adjust for shrinkage/obsolescence
   - Calculate COGS

5. **Fixed Assets**
   - Calculate depreciation
   - Record additions/disposals
   - Update asset register

6. **Accruals**
   - Record accrued expenses
   - Record prepaid amortization
   - Record deferred revenue recognition

7. **Inter-company**
   - Eliminate inter-company transactions
   - Verify balances match

### 5.4 Year-End Closing

**Steps:**

1. **Complete all month-end procedures for month 12**

2. **Adjusting Entries**
   - Audit adjustments
   - Year-end accruals
   - Tax provisions

3. **Close Income Statement**
   ```
   Dr. Revenue Accounts      (Total)
       Cr. Income Summary        (Total)

   Dr. Income Summary        (Total)
       Cr. Expense Accounts      (Total)
   ```

4. **Transfer to Retained Earnings**
   ```
   Dr. Income Summary        (Net Income)
       Cr. Retained Earnings     (Net Income)
   ```

5. **Generate Opening Balances**
   - Balance sheet accounts carry forward
   - Income statement accounts reset to zero

### 5.5 Reversing Entries

**Purpose:** Simplify recording in new period for accruals

**Example:**
December 31 - Accrue salary:
```
Dr. Salary Expense    Rp 10,000,000
    Cr. Accrued Salary    Rp 10,000,000
```

January 1 - Reversing:
```
Dr. Accrued Salary    Rp 10,000,000
    Cr. Salary Expense    Rp 10,000,000
```

January 5 - Actual payment:
```
Dr. Salary Expense    Rp 10,000,000
    Cr. Cash              Rp 10,000,000
```

---

## 6. Financial Reporting Standards

### 6.1 IFRS/PSAK Required Statements

| Statement | PSAK Reference | Description |
|-----------|----------------|-------------|
| Statement of Financial Position | PSAK 201 (IAS 1) | Balance Sheet |
| Statement of Profit or Loss | PSAK 201 (IAS 1) | Income Statement |
| Statement of Changes in Equity | PSAK 201 (IAS 1) | Equity movements |
| Statement of Cash Flows | PSAK 202 (IAS 7) | Cash inflows/outflows |
| Notes to Financial Statements | PSAK 201 (IAS 1) | Disclosures |

### 6.2 Balance Sheet Structure

**IFRS Format (Liquidity Order):**

```
ASSETS
├── Current Assets
│   ├── Cash and Cash Equivalents
│   ├── Trade Receivables
│   ├── Inventories
│   ├── Prepaid Expenses
│   └── Other Current Assets
├── Non-Current Assets
│   ├── Property, Plant & Equipment
│   ├── Intangible Assets
│   ├── Right-of-Use Assets
│   └── Deferred Tax Assets
└── TOTAL ASSETS

LIABILITIES
├── Current Liabilities
│   ├── Trade Payables
│   ├── Accrued Expenses
│   ├── Current Tax Liabilities
│   ├── Short-term Borrowings
│   └── Current Portion of Long-term Debt
├── Non-Current Liabilities
│   ├── Long-term Borrowings
│   ├── Deferred Tax Liabilities
│   └── Provisions
└── TOTAL LIABILITIES

EQUITY
├── Share Capital
├── Share Premium
├── Retained Earnings
├── Other Comprehensive Income
└── TOTAL EQUITY

TOTAL LIABILITIES AND EQUITY
```

### 6.3 Income Statement Structure

**By Function (Recommended):**

```
Revenue
Less: Cost of Sales
─────────────────────
Gross Profit

Less: Operating Expenses
├── Selling Expenses
├── Administrative Expenses
└── Other Operating Expenses
─────────────────────
Operating Profit

Other Income/(Expenses)
├── Interest Income
├── Interest Expense
├── Foreign Exchange Gain/(Loss)
└── Other Non-operating Items
─────────────────────
Profit Before Tax

Less: Income Tax Expense
─────────────────────
Profit for the Period

Other Comprehensive Income
─────────────────────
Total Comprehensive Income
```

**By Nature (Alternative):**

```
Revenue
Other Income

Changes in Inventories
Raw Materials Used
Employee Benefits
Depreciation & Amortization
Other Expenses
─────────────────────
Profit Before Tax
```

### 6.4 Cash Flow Statement

**IAS 7 / PSAK 202 Methods:**

| Method | Operating Activities |
|--------|---------------------|
| Direct | Lists actual cash receipts/payments |
| Indirect | Starts with Net Income, adjusts for non-cash items |

**Structure:**

```
CASH FLOWS FROM OPERATING ACTIVITIES
├── [Direct: Receipts from customers, Payments to suppliers, etc.]
├── [Indirect: Net Income + Depreciation - Changes in Working Capital]
└── Net Cash from Operating Activities

CASH FLOWS FROM INVESTING ACTIVITIES
├── Purchase of Property & Equipment
├── Proceeds from Sale of Equipment
├── Investment in Subsidiaries
└── Net Cash from Investing Activities

CASH FLOWS FROM FINANCING ACTIVITIES
├── Proceeds from Bank Loans
├── Repayment of Loans
├── Dividends Paid
└── Net Cash from Financing Activities

NET INCREASE/(DECREASE) IN CASH
CASH AT BEGINNING OF PERIOD
CASH AT END OF PERIOD
```

### 6.5 Trial Balance

**Purpose:** Verify debits = credits before preparing statements

**Structure:**

```
| Account Code | Account Name | Debit | Credit |
|--------------|--------------|-------|--------|
| 1010 | Cash | 100,000 | |
| 1030 | Accounts Receivable | 50,000 | |
| 2010 | Accounts Payable | | 30,000 |
| 3010 | Share Capital | | 100,000 |
| 4010 | Revenue | | 80,000 |
| 5010 | Cost of Sales | 40,000 | |
| 6010 | Operating Expenses | 20,000 | |
| TOTAL | | 210,000 | 210,000 |
```

### 6.6 IFRS 18 (New Standard - Effective 2027)

**Key Changes from IAS 1:**
- New subtotals required: Operating profit, Profit before financing
- Stricter categorization of income/expenses
- Enhanced disclosure for management performance measures (MPMs)
- "Unusual items" disclosure required

---

## 7. Bank & Payment Standards

### 7.1 ISO 20022

**What:** Universal financial messaging standard replacing SWIFT MT

**Implementation:** Global adoption completed November 2025

**Key Message Types:**

| Category | ISO 20022 Code | Description |
|----------|----------------|-------------|
| Payment Initiation | pain.001 | Customer Credit Transfer Initiation |
| Payment Status | pain.002 | Payment Status Report |
| Account Statement | camt.053 | Bank to Customer Statement |
| Direct Debit | pain.008 | Direct Debit Initiation |

**Benefits:**
- Richer data (structured addresses, LEI codes)
- Better straight-through processing
- Reduced errors and manual intervention
- Supports regulatory reporting

### 7.2 Bank Account Structure

**Database Model:**

```sql
bank_accounts (
    id,
    organization_id,
    account_code,      -- Link to CoA
    bank_name,
    account_number,
    account_name,
    currency,
    swift_code,        -- For international
    branch_code,
    is_active,
    opening_balance,
    opening_date,
    current_balance    -- Cached for performance
)
```

### 7.3 Bank Reconciliation

**Process:**

1. Import bank statement (CSV, MT940, ISO 20022)
2. Auto-match with GL transactions
   - By reference number
   - By amount + date range
   - By payee name
3. Review unmatched items
4. Create adjusting entries for bank charges, interest
5. Verify reconciled balance = bank statement balance
6. Lock reconciled transactions

**Reconciliation Report:**

```
Bank Statement Balance               xxx
Add: Deposits in Transit             xxx
Less: Outstanding Checks            (xxx)
─────────────────────────────────────────
Adjusted Bank Balance                xxx

GL Balance                           xxx
Add: Bank Interest (not recorded)    xxx
Less: Bank Charges (not recorded)   (xxx)
─────────────────────────────────────────
Adjusted Book Balance                xxx

Difference (should be zero)          0
```

### 7.4 Cash Management

**Petty Cash:**
- Imprest system: Fixed float, replenish to original amount
- Journal on replenishment, not on individual disbursements
- Physical count required monthly

**Cash Flow Forecasting:**
- Project AR collections based on aging
- Project AP payments based on due dates
- Include recurring items (payroll, rent, utilities)

---

## 8. Accounts Receivable Standards

### 8.1 Guest/Customer Ledger

**Hotel-Specific AR Types:**

| Type | Description | Example |
|------|-------------|---------|
| **Guest Ledger** | In-house guests with running tab | Room charges, F&B, spa |
| **City Ledger** | Non-room charges, corporate accounts | Direct bills, travel agents |
| **Advance Deposits** | Prepayments for future stays | Reservations |

### 8.2 Invoice Structure

**Required Fields:**
- Invoice Number (unique, sequential)
- Invoice Date
- Due Date
- Customer Information
- Line Items (qty, description, unit price, tax, total)
- Payment Terms
- Tax Summary (DPP, PPN, total)
- Bank Account for Payment

**Indonesia e-Faktur Integration:**
- Generate QR code
- Submit to DJP system
- Store Faktur Pajak number

### 8.3 IFRS 9 - Expected Credit Loss (ECL)

**Provision Matrix Approach:**

| Aging Bucket | Expected Loss Rate | AR Balance | Provision |
|--------------|-------------------|------------|-----------|
| Current | 0.5% | 100,000 | 500 |
| 1-30 days | 2% | 50,000 | 1,000 |
| 31-60 days | 5% | 20,000 | 1,000 |
| 61-90 days | 15% | 10,000 | 1,500 |
| > 90 days | 50% | 5,000 | 2,500 |
| **Total** | | **185,000** | **6,500** |

**Journal Entry:**
```
Dr. Bad Debt Expense / Expected Credit Loss    6,500
    Cr. Allowance for Doubtful Accounts           6,500
```

### 8.4 Aging Report

**Standard Buckets:**
- Current (not yet due)
- 1-30 days overdue
- 31-60 days overdue
- 61-90 days overdue
- Over 90 days overdue

**Report Format:**

```
| Customer | Current | 1-30 | 31-60 | 61-90 | >90 | Total |
|----------|---------|------|-------|-------|-----|-------|
| ABC Corp | 50,000  | 20,000| 10,000| 5,000 | 2,000| 87,000|
| XYZ Ltd  | 30,000  |   -  |   -   |   -   |   - | 30,000|
| TOTAL    | 80,000  | 20,000| 10,000| 5,000 | 2,000|117,000|
```

### 8.5 Payment Application

**Rules:**
1. Apply to oldest invoice first (FIFO)
2. Or apply to specific invoice if indicated
3. Partial payments allowed
4. Over-payments create credit balance

**Journal Entry - Payment Received:**
```
Dr. Bank Account                  100,000
    Cr. Accounts Receivable           100,000
```

**With Discount:**
```
Dr. Bank Account                   98,000
Dr. Sales Discount                  2,000
    Cr. Accounts Receivable           100,000
```

---

## 9. Accounts Payable Standards

### 9.1 3-Way Matching

**Documents:**
1. **Purchase Order (PO)**: What was ordered
2. **Goods Receipt Note (GRN)**: What was received
3. **Vendor Invoice**: What vendor claims

**Matching Process:**

| Check | Tolerance | Action if Mismatch |
|-------|-----------|-------------------|
| Quantity | ± 5% | Hold invoice, notify procurement |
| Unit Price | ± 2% | Hold invoice, notify procurement |
| Total Amount | ± Rp 10,000 | Auto-adjust if within tolerance |

**Matched Invoice Journal:**
```
Dr. Inventory/Expense        100,000
Dr. PPN Masukan               12,000
    Cr. Accounts Payable         112,000
```

### 9.2 Invoice Processing Workflow

```
Receive Invoice → Match with PO/GRN → Approval Workflow → Schedule Payment → Payment → Reconciliation
```

**Approval Levels (Example):**

| Amount | Approver |
|--------|----------|
| < 10 juta | Department Head |
| 10-50 juta | Finance Manager |
| 50-100 juta | CFO |
| > 100 juta | Director |

### 9.3 Payment Terms

**Common Terms:**

| Code | Description |
|------|-------------|
| COD | Cash on Delivery |
| Net 30 | Due 30 days from invoice date |
| Net 60 | Due 60 days from invoice date |
| 2/10 Net 30 | 2% discount if paid within 10 days, otherwise net 30 |
| EOM | End of Month |
| 15 MFI | 15th of Month Following Invoice |

### 9.4 Payment Processing

**Payment Methods:**

| Method | Use Case |
|--------|----------|
| Bank Transfer | Standard vendor payments |
| Giro/Check | Traditional, requires physical handling |
| Virtual Account | Automatic reconciliation |
| Cash | Petty cash, small amounts only |

**Payment Run:**
1. Select invoices due for payment
2. Group by vendor and payment method
3. Generate payment batch
4. Approval workflow
5. Execute payments
6. Record in GL
7. Send remittance advice to vendors

**Journal Entry:**
```
Dr. Accounts Payable         112,000
    Cr. Bank Account             112,000
```

### 9.5 Aging Report (AP)

Same structure as AR aging, but from vendor perspective:
- Helps cash flow planning
- Identifies upcoming payment obligations
- Tracks vendor relationships (payment history)

---

## 10. Audit Trail & Compliance

### 10.1 SOX (Sarbanes-Oxley) Requirements

**Section 302 - Corporate Responsibility:**
- CEO/CFO must certify financial statements
- Internal controls must be documented

**Section 404 - Internal Controls:**
- Management must assess effectiveness of internal controls
- External auditor must attest to management's assessment

### 10.2 Audit Trail Requirements

**Every Transaction Must Record:**
- Who created it (user_id)
- When created (created_at)
- Who approved it (approved_by_id)
- When approved (approved_at)
- Who modified it (updated_by_id)
- When modified (updated_at)
- What changed (before/after values)

**Database Pattern:**

```sql
-- Main table
transactions (
    id,
    transaction_date,
    amount,
    -- ... other fields
    created_by_id,
    created_at,
    updated_by_id,
    updated_at,
    approved_by_id,
    approved_at,
    status -- draft, pending_approval, approved, posted, voided
)

-- Audit log table
transactions_audit (
    id,
    transaction_id,
    action, -- create, update, approve, void
    old_values JSONB,
    new_values JSONB,
    changed_by_id,
    changed_at,
    ip_address,
    user_agent
)
```

### 10.3 Data Immutability

**Principles:**
1. **No delete** - Use soft delete (is_deleted flag)
2. **No direct update of posted transactions** - Void and create new
3. **Sequential numbering** - Gaps indicate deleted/voided
4. **Hash chain** - Each transaction references hash of previous

**Voiding Pattern:**
```sql
-- Instead of DELETE
UPDATE invoices
SET is_voided = TRUE,
    voided_by_id = :user_id,
    voided_at = NOW(),
    void_reason = :reason
WHERE id = :invoice_id;

-- Create reversing entry
INSERT INTO journal_entries (
    reference_type, reference_id,
    is_reversal, original_entry_id,
    ...
)
```

### 10.4 Segregation of Duties

**Key Controls:**

| Function | Cannot Also Perform |
|----------|---------------------|
| Create PO | Approve PO, Receive Goods |
| Receive Goods | Create PO, Approve Payment |
| Create Invoice | Approve Invoice |
| Approve Invoice | Process Payment |
| Process Payment | Bank Reconciliation |

### 10.5 Indonesia-Specific Compliance

**OJK Requirements (if applicable):**
- Monthly regulatory reporting
- Specific chart of accounts format
- Capital adequacy reporting

**Tax Compliance:**
- e-Faktur for PPN
- e-Bupot for PPh 23
- e-SPT for all tax returns
- Coretax system (new consolidated platform)

### 10.6 Document Retention

**Indonesia Requirements:**

| Document Type | Retention Period |
|---------------|-----------------|
| Tax Documents | 10 years |
| General Ledger | 10 years |
| Invoices | 10 years |
| Bank Statements | 10 years |
| Payroll Records | 5 years |

---

## 11. Industry-Specific: USALI

### 11.1 Overview

**What:** Uniform System of Accounts for the Lodging Industry
**Current Edition:** 12th Edition (2024)
**Effective:** January 1, 2026
**Publisher:** HFTP (Hospitality Financial and Technology Professionals)

### 11.2 USALI Chart of Accounts Structure

**Revenue Centers (Operated Departments):**

| Code | Department | Description |
|------|------------|-------------|
| 10 | Rooms | Room revenue, cancellation fees |
| 20 | F&B | Restaurants, bars, banquets, room service |
| 30 | Other Operated | Spa, golf, parking, telephone, laundry |
| 40 | Rentals & Other | Space rental, commissions, attrition |

**Cost Centers (Undistributed Expenses):**

| Code | Department | Description |
|------|------------|-------------|
| 50 | Administrative & General | Management, accounting, HR, IT |
| 60 | Information & Telecom | Telecom, internet, systems |
| 70 | Sales & Marketing | Sales, advertising, loyalty |
| 80 | Property Operations | Utilities, repairs, maintenance |

**Non-Operating:**

| Code | Category | Description |
|------|----------|-------------|
| 90 | Management Fees | Base and incentive fees |
| 91 | Rent, Insurance, Taxes | Fixed charges |
| 92 | Interest | Debt service |
| 93 | Depreciation | Non-cash charges |

### 11.3 USALI Standard Reports

**Summary Operating Statement:**
```
REVENUE
├── Rooms Revenue
├── Food Revenue
├── Beverage Revenue
├── Other Operated Revenue
└── Rentals & Other Income
────────────────────────────
TOTAL REVENUE

DEPARTMENTAL EXPENSES
├── Rooms Expense
├── F&B Expense
└── Other Operated Expense
────────────────────────────
TOTAL DEPARTMENTAL INCOME (GOP Departmental)

UNDISTRIBUTED EXPENSES
├── Administrative & General
├── Information & Telecom
├── Sales & Marketing
├── Property Operations
├── Utilities
────────────────────────────
GROSS OPERATING PROFIT (GOP)

MANAGEMENT FEES
────────────────────────────
INCOME BEFORE NON-OPERATING

NON-OPERATING INCOME/EXPENSES
├── Rent
├── Property Tax
├── Insurance
├── Interest
├── Depreciation
────────────────────────────
NET INCOME
```

### 11.4 Key Performance Indicators (Hotel)

| KPI | Formula | Industry Benchmark |
|-----|---------|-------------------|
| **Occupancy Rate** | Rooms Sold / Available Rooms | 65-75% |
| **ADR** (Average Daily Rate) | Room Revenue / Rooms Sold | Varies by market |
| **RevPAR** | Room Revenue / Available Rooms | ADR × Occupancy |
| **TRevPAR** | Total Revenue / Available Rooms | - |
| **GOPPAR** | GOP / Available Rooms | - |
| **Labor Cost %** | Labor Cost / Total Revenue | 25-35% |
| **Food Cost %** | Food Cost / Food Revenue | 28-35% |
| **Beverage Cost %** | Bev Cost / Bev Revenue | 20-25% |

### 11.5 USALI 12th Edition Changes (2024)

**Major Updates:**
1. **Sustainability reporting** - New section for ESG metrics
2. **Technology costs** - Reclassified to Information & Telecom
3. **Labor scheduling** - New productivity metrics
4. **Revenue management** - New revenue categories for dynamic pricing
5. **Digital services** - New categories for streaming, digital amenities

---

## Summary: Key Standards to Implement

### Must Have (Phase 1):

1. **Chart of Accounts**
   - USALI-based for hotel operations
   - 8-digit numbering for flexibility
   - Multi-company/multi-currency support

2. **Double-Entry System**
   - Balanced journal entries
   - Accrual basis accounting
   - Period closing procedures

3. **Tax Compliance (Indonesia)**
   - PPN 12% calculation
   - PPh 21 (TER method)
   - PPh 23/4(2) withholding
   - e-Faktur integration ready

4. **Basic Reports**
   - Trial Balance
   - Balance Sheet
   - Income Statement
   - Cash Flow Statement

5. **Audit Trail**
   - Full transaction logging
   - No physical deletion
   - User/timestamp tracking

### Should Have (Phase 2):

1. **Multi-Currency**
   - IAS 21 compliant
   - Realized/Unrealized gain/loss
   - Monthly revaluation

2. **AR Module**
   - Guest ledger / City ledger
   - IFRS 9 ECL provisioning
   - Aging reports

3. **AP Module**
   - 3-way matching
   - Payment scheduling
   - Vendor aging

4. **Bank Reconciliation**
   - Statement import
   - Auto-matching
   - Reconciliation report

### Nice to Have (Phase 3):

1. **Budgeting & Forecasting**
2. **Consolidation (multi-entity)**
3. **IFRS 18 compliance (2027)**
4. **ISO 20022 integration**
5. **Advanced analytics dashboard**

---

*Document ini akan digunakan sebagai referensi untuk pembahasan detail di BUSINESS_ACCOUNTING_STANDARDS.md*
