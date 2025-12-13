# Business & Accounting Standards

> Standar bisnis dan akuntansi untuk **Enterprise Hospitality Platform**.
>
> **Last Updated**: 2025-12-07
> **Status**: In Progress

---

## Table of Contents

1. [Chart of Accounts (CoA)](#1-chart-of-accounts-coa) ✅
2. [Journal Entry Patterns](#2-journal-entry-patterns) ✅
3. [Multi-Currency Handling](#3-multi-currency-handling) ✅ (Phase 2)
4. [Tax Management](#4-tax-management)
5. [Period & Closing](#5-period--closing)
6. [Financial Reporting](#6-financial-reporting)
7. [Bank & Cash Management](#7-bank--cash-management)
8. [Accounts Receivable (AR)](#8-accounts-receivable-ar)
9. [Accounts Payable (AP)](#9-accounts-payable-ap)
10. [Business Rules Engine](#10-business-rules-engine) ✅

**11-16**: See [BUSINESS_ACCOUNTING_STANDARDS_V2.md](./BUSINESS_ACCOUNTING_STANDARDS_V2.md)

---

## 1. Chart of Accounts (CoA)

> **Status**: ✅ Approved (2025-12-07)

### 1.1 Hierarchical Structure (4 Levels)

CoA menggunakan struktur hierarki 4 level untuk mencegah kesalahan input:

```
Level 1: Categories     → Fixed (5 kategori IFRS)
Level 2: Subcategories  → 80% Fixed + 20% Custom
Level 3: Account Types  → 50% Fixed + 50% Custom
Level 4: Accounts       → 100% Custom per Organization
```

**Diagram:**

```
┌─────────────────────────────────────────────────────────┐
│ Level 1: CATEGORIES (Fixed - IFRS Standard)            │
├─────────────────────────────────────────────────────────┤
│ Code │ Name          │ Normal Balance                  │
│ 1    │ Assets        │ Debit                           │
│ 2    │ Liabilities   │ Credit                          │
│ 3    │ Equity        │ Credit                          │
│ 4    │ Revenue       │ Credit                          │
│ 5    │ Expenses      │ Debit                           │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ Level 2: SUBCATEGORIES (Template + Custom)             │
├─────────────────────────────────────────────────────────┤
│ 11 - Current Assets        │ 21 - Current Liabilities  │
│ 12 - Non-Current Assets    │ 22 - Non-Current Liab.    │
│ 31 - Share Capital         │ 41 - Operating Revenue    │
│ 32 - Retained Earnings     │ 51 - Cost of Sales        │
│ ...                        │ 52 - Operating Expenses   │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ Level 3: ACCOUNT TYPES (Template + Custom)             │
├─────────────────────────────────────────────────────────┤
│ 1101 - Cash                │ 2101 - Accounts Payable   │
│ 1102 - Bank                │ 2103 - Output VAT         │
│ 1103 - Accounts Receivable │ 4101 - Sales Revenue      │
│ 1104 - Inventory           │ 5201 - Salary & Wages     │
│ 1106 - Input VAT           │ ...                       │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ Level 4: ACCOUNTS (User-created per Organization)      │
├─────────────────────────────────────────────────────────┤
│ 1102-001    - Bank BCA IDR                             │
│ 1102-002    - Bank BCA USD                             │
│ 1102-003-FB - Kas Kecil F&B                            │
│ 4101-001-RM - Pendapatan Kamar                         │
│ 5201-001-FO - Gaji Front Office                        │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Account Numbering Format

**Format: `XXXX-XXX-XX`**

```
XXXX  -  XXX  -  XX
 │        │      │
 │        │      └── Department Code (optional, 2 chars)
 │        │          FO, FB, HK, RM, SP, etc.
 │        │
 │        └────────── Sequence Number (3 digits, auto-increment)
 │                    001, 002, 003... per type
 │
 └─────────────────── Account Type Code (4 digits)
                      From Level 3 (coa_types)
```

**Contoh:**

| Code | Name | Breakdown |
|------|------|-----------|
| `1102-001` | Bank BCA - IDR | Type 1102 (Bank) + Seq 001 |
| `1102-002` | Bank BCA - USD | Type 1102 (Bank) + Seq 002 |
| `1101-001-FO` | Kas Kecil Front Office | Type 1101 (Cash) + Seq 001 + Dept FO |
| `4101-001-RM` | Pendapatan Kamar | Type 4101 (Revenue) + Seq 001 + Dept Rooms |
| `5201-003-HK` | Gaji Housekeeping | Type 5201 (Salary) + Seq 003 + Dept HK |

### 1.3 Flexibility Matrix

| Level | Fixed | Custom | Can Deactivate | Soft Delete | Audit Log |
|-------|-------|--------|----------------|-------------|-----------|
| 1 - Categories | 100% | 0% | No | No | No |
| 2 - Subcategories | 80% | 20% | If not required | Yes | Yes |
| 3 - Account Types | 50% | 50% | If not required | Yes | Yes |
| 4 - Accounts | 0% | 100% | Always | Yes (if no txn) | Yes |

**Rules:**

- `is_system = TRUE` → Tidak bisa dihapus
- `is_required = TRUE` → Tidak bisa dinonaktifkan
- `is_locked = TRUE` → Tidak bisa diubah (ada transaksi)

### 1.4 Department Codes (USALI Standard)

**Revenue Centers:**

| Code | Name | Required |
|------|------|----------|
| RM | Rooms | Yes |
| FB | Food & Beverage | Yes |
| BQ | Banquet | No |
| SP | Spa | No |
| RC | Recreation | No |
| PK | Parking | No |
| LN | Laundry | No |
| TC | Telecom | No |
| OT | Other Operated | No |

**Cost Centers:**

| Code | Name | Required |
|------|------|----------|
| FO | Front Office | Yes |
| HK | Housekeeping | Yes |
| EN | Engineering | No |
| SC | Security | No |
| SL | Sales & Marketing | No |
| HR | Human Resources | No |
| FN | Finance | Yes |
| IT | Information Technology | No |
| EX | Executive | No |
| GN | General | Yes |

### 1.5 Multi-Entity Strategy

**Hierarchy:**

```
Platform (Global Templates)
    └── Management Group (Required, even for 1 PT)
            └── PT/Company (Own Database)
                    └── Apps (Schema per App)
```

**Default Strategy: `group_std`**

- Management Group menyediakan template standar
- PT copy dari group template
- PT dapat customize (tambah account, activate/deactivate)
- Consolidation ready dari awal

**CoA Template Inheritance:**

```
Platform Template (IFRS/USALI)
        │
        ▼
Management Group Template (customized)
        │
        ├──► PT A CoA (copy + customize)
        ├──► PT B CoA (copy + customize)
        └──► PT C CoA (copy + customize)
```

### 1.6 App Integration Mode

| Mode | Description | Database | CoA |
|------|-------------|----------|-----|
| `master` | App adalah master system | Own | Own |
| `integrated` | Share dengan master | Shared | Shared |
| `standalone` | Mandiri tanpa master | Own | Own |

**Contoh:**

```
PT Hotel ABC
├── PMS (master)
│   ├── Database: hotel_abc_db
│   └── CoA: Full hotel CoA
│
├── POS (integrated)
│   ├── Database: hotel_abc_db (shared)
│   └── CoA: Uses PMS CoA (FB accounts)
│
└── HRM (integrated)
    ├── Database: hotel_abc_db (shared)
    └── CoA: Uses PMS CoA (all dept payroll)
```

### 1.7 Database Tables

```sql
-- Level 1: Fixed categories
coa_categories (id, code, name, name_id, normal_balance, is_system, is_active)

-- Level 2: Template + custom subcategories
coa_subcategories (id, category_id, code, name, name_id, is_system, is_required,
                   is_active, is_deleted, deleted_at, deleted_by_id,
                   created_at, updated_at, created_by_id, updated_by_id)

-- Level 3: Template + custom types (global or per-org)
coa_types (id, subcategory_id, organization_id, code, name, name_id,
           is_system, is_required, is_active, is_deleted, ...)

-- Level 4: User accounts per organization
coa_accounts (id, organization_id, type_id, department_id,
              type_code, sequence_number, department_code, code, name,
              currency, is_bank_account, is_cash_account, is_control_account,
              is_active, is_locked, is_deleted, current_balance, ...)

-- Audit log for all changes
coa_audit_logs (id, table_name, record_id, organization_id, action,
                old_values, new_values, changed_fields, reason,
                performed_by_id, performed_at, ip_address, user_agent)

-- Department definitions
departments (id, organization_id, code, name, name_id, department_type,
             is_system, is_required, is_active, is_deleted, ...)

-- Consolidation mapping
group_account_mappings (id, management_group_id, group_account_code,
                        group_account_name, pt_organization_id,
                        pt_account_code, mapping_type, split_percentage, ...)
```

---

## 2. Journal Entry Patterns

> **Status**: ✅ Approved (2025-12-07)

### 2.1 Double-Entry Principle

Semua transaksi harus balanced (Total Debit = Total Credit).

**Debit/Credit Rules:**

| Account Type | Increase | Decrease | Normal Balance |
|--------------|----------|----------|----------------|
| Assets | DEBIT | Credit | Debit |
| Liabilities | Credit | DEBIT | Credit |
| Equity | Credit | DEBIT | Credit |
| Revenue | Credit | DEBIT | Credit |
| Expenses | DEBIT | Credit | Debit |

### 2.2 Journal Types

**Auto-Generated (dari modul lain):**

| Code | Name | Source | Auto-Post |
|------|------|--------|-----------|
| SJ | Sales Journal | POS, AR Invoice | Configurable |
| PJ | Purchase Journal | AP Invoice | Configurable |
| CR | Cash Receipt | AR Payment | Configurable |
| CD | Cash Disbursement | AP Payment | Configurable |
| PY | Payroll Journal | HRM/Payroll | Configurable |
| IV | Inventory Journal | Inventory | Configurable |
| FA | Fixed Asset | Asset Module | Configurable |
| DP | Depreciation | Asset Module | Configurable |

**Manual (dibuat user):**

| Code | Name | Use Case |
|------|------|----------|
| GJ | General Journal | Adjustments, corrections |
| AJ | Adjusting Journal | Period-end accruals |
| RJ | Reversing Journal | Reverse accruals |
| CJ | Closing Journal | Year-end closing |
| OB | Opening Balance | Initial setup, migration |

### 2.3 Journal Numbering

**Format:** `TYPE-YYYY-MM-NNNNN`

```
TYPE  -  YYYY  -  MM  -  NNNNN
 │        │       │       │
 │        │       │       └── Sequence (5 digits, reset per month)
 │        │       └────────── Month (01-12)
 │        └────────────────── Year
 └─────────────────────────── Journal Type Code
```

**Contoh:**
- `GJ-2025-12-00001` → General Journal, Dec 2025, #1
- `SJ-2025-12-00045` → Sales Journal, Dec 2025, #45
- `CR-2026-01-00001` → Cash Receipt, Jan 2026, #1 (reset)

### 2.4 Journal Status Flow

```
DRAFT → PENDING APPROVAL → APPROVED → POSTED
  │           │                          │
  ▼           ▼                          ▼
DELETED    REJECTED                   VOIDED
(soft)    (back to draft)          (reversing entry)
```

**Status Definitions:**

| Status | Description | Can Edit | Can Delete |
|--------|-------------|----------|------------|
| Draft | Belum submit | Yes | Yes (soft) |
| Pending | Menunggu approval | No | No |
| Rejected | Ditolak, kembali ke draft | Yes | Yes (soft) |
| Approved | Disetujui, siap posting | No | No |
| Posted | Sudah masuk GL | No | No (void only) |
| Voided | Dibatalkan dengan reversing | No | No |

### 2.5 Approval Workflow

**Configurable per Organization:**

```sql
journal_approval_rules (
    organization_id,
    journal_type,          -- 'GJ', 'AJ', 'ALL'
    min_amount,            -- Threshold minimum
    max_amount,            -- Threshold maximum
    approver_role_id,      -- Role yang approve
    approval_order,        -- Level (1, 2, 3)
    is_active
)
```

**Contoh Configuration:**

| Journal Type | Amount | Approver |
|--------------|--------|----------|
| ALL | < 10 juta | Finance Staff |
| ALL | 10-100 juta | Finance Manager |
| ALL | > 100 juta | Finance Director |
| GJ, AJ | Any | Always requires approval |

**Auto-Generated Journals:** Configurable per journal type (dapat langsung post atau perlu approval).

### 2.6 Reversing Entries

Untuk accrual entries yang perlu di-reverse di periode berikutnya:

```
Original (Dec 31):
Dr. Utilities Expense      5,000,000
    Cr. Accrued Expense        5,000,000

Auto-Reversing (Jan 1):
Dr. Accrued Expense        5,000,000
    Cr. Utilities Expense      5,000,000
```

**Database Fields:**
```sql
journal_entries (
    is_auto_reverse BOOLEAN DEFAULT FALSE,
    reverse_date DATE,              -- When to auto-reverse
    reversed_from_id INTEGER,       -- Link to original
    reversed_by_id INTEGER          -- Link to reversing entry
)
```

### 2.7 Voiding Posted Entries

**Rule:** Posted entries TIDAK BOLEH dihapus, hanya bisa di-VOID.

**Void Process:**
1. User request void dengan reason
2. Approval (jika required)
3. System creates reversing entry
4. Original entry marked as VOIDED
5. Both entries linked

```
Original (Posted):
Dr. Expense    100,000
    Cr. AP         100,000

Void Entry (Auto-created):
Dr. AP         100,000
    Cr. Expense    100,000
```

### 2.8 Auto-Generated Journal Templates

**Sales Invoice:**
```
Dr. Accounts Receivable     112,000,000
    Cr. Sales Revenue           100,000,000
    Cr. Output VAT               12,000,000
```

**Cash Receipt:**
```
Dr. Bank/Cash               112,000,000
    Cr. Accounts Receivable     112,000,000
```

**Purchase Invoice:**
```
Dr. Expense/Inventory       100,000,000
Dr. Input VAT                12,000,000
    Cr. Accounts Payable        112,000,000
```

**Payroll:**
```
Dr. Salary Expense (by dept) xxx
    Cr. PPh 21 Payable           xxx
    Cr. Bank                     xxx
```

---

## 3. Multi-Currency Handling

> **Status**: ✅ Approved (2025-12-07)
> **Implementation**: Phase 2 (Schema ready, fitur dikerjakan nanti)

### 3.1 Currency Concepts (IAS 21)

| Term | Definition |
|------|------------|
| **Functional Currency** | Mata uang utama operasional (configurable per PT) |
| **Presentation Currency** | Mata uang laporan keuangan (bisa sama/beda) |
| **Foreign Currency** | Mata uang selain functional |

### 3.2 Exchange Rate Types

| Type | Usage | Source |
|------|-------|--------|
| **Spot Rate** | Tanggal transaksi | Manual / Import |
| **Closing Rate** | Akhir periode (revaluasi) | Manual / Import |
| **Average Rate** | Rata-rata periode | Calculated |
| **Tax Rate (KMK)** | Transaksi pajak | Kemenkeu (weekly) |

### 3.3 Rate Source (Phase 1)

- **Manual input** dengan form
- **Template import** (Excel/CSV)
- Auto-fetch dari external API: **Later phase**

### 3.4 Transaction Recording

```
Invoice: USD 1,000 @ Rp 15,500

Dr. AR - Guest (USD)          USD 1,000 × 15,500 = Rp 15,500,000
    Cr. Room Revenue                                Rp 13,750,000
    Cr. Tax                                         Rp  1,750,000
```

Journal entry menyimpan:
- `foreign_currency`: USD
- `foreign_amount`: 1,000.00
- `exchange_rate`: 15,500
- `local_amount`: 15,500,000 (IDR)

### 3.5 Realized vs Unrealized Forex

**Realized (saat settlement):**
```
Invoice: USD 1,000 @ 15,500 = Rp 15,500,000
Payment: USD 1,000 @ 15,800 = Rp 15,800,000
Gain: Rp 300,000

Dr. Bank                  15,800,000
    Cr. AR                    15,500,000
    Cr. Forex Gain Realized      300,000
```

**Unrealized (revaluasi akhir periode):**
```
AR Book: USD 1,000 @ 15,500 = Rp 15,500,000
Closing: USD 1,000 @ 15,700 = Rp 15,700,000
Unrealized Gain: Rp 200,000

Dr. AR                       200,000
    Cr. Forex Gain Unrealized    200,000
```

**Treatment:** Configurable per organization (P&L atau OCI)

### 3.6 Revaluation

- **Frequency:** On-demand (user trigger)
- **Process:**
  1. Select period end date
  2. System gets all foreign currency monetary balances
  3. Apply closing rate
  4. Calculate differences
  5. Generate revaluation journal

### 3.7 Database Schema

```sql
-- Currencies
currencies (code, name, symbol, decimal_places, is_active)

-- Exchange Rates
exchange_rates (
    organization_id, from_currency, to_currency,
    rate_date, rate_type, rate, source,
    created_at, created_by_id
)

-- Journal with foreign currency
journal_entry_lines (
    ...,
    foreign_currency,    -- NULL = functional
    foreign_amount,
    exchange_rate,
    debit_amount,        -- Always in functional currency
    credit_amount
)

-- Revaluation history
forex_revaluations (
    organization_id, period_date, currency,
    closing_rate, total_gain, total_loss,
    journal_entry_id
)
```

---

## 4. Tax Management

> **Status**: ⚠️ Draft - Perlu Konsultasi Pakar
> **Note**: Alur real-world perlu divalidasi dengan praktisi accounting/tax

### 4.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Tax Rates | ❌ | ✅ (bisa berubah via Config) |
| Tax Calculation Method | ❌ | ✅ (Inclusive/Exclusive) |
| Rounding Rules | ❌ | ✅ (0, 1, 100 rupiah) |
| E-Faktur Numbering | ✅ (format DJP) | ❌ |
| Due Date Rules | ✅ (fixed per law) | ❌ |
| Tax Category Mapping | ❌ | ✅ (per account/item) |
| PPh 21 TER Tables | ❌ | ✅ (via template import) |
| Withholding Tax Rates | ❌ | ✅ (configurable) |
| Tax Account Mapping | ❌ | ✅ (GL mapping per tax type) |

### 4.2 Tax Types (Indonesia)

#### 4.2.1 PPN (Pajak Pertambahan Nilai)

**Soft Rules (Configurable):**

| Rule Code | Type | Default | Configurable |
|-----------|------|---------|--------------|
| `TAX_PPN_RATE` | percentage | 12% | ✅ Yes |
| `TAX_PPN_CALCULATION` | selection | exclusive | ✅ Yes (inclusive/exclusive) |
| `TAX_PPN_ROUNDING` | selection | round_down | ✅ Yes (round/round_down/round_up) |
| `TAX_PPN_THRESHOLD` | threshold | 10,000,000 | ✅ Yes (e-Faktur threshold) |
| `TAX_PPN_OUTPUT_ACCOUNT` | mapping | 2103 | ✅ Yes (GL account) |
| `TAX_PPN_INPUT_ACCOUNT` | mapping | 1106 | ✅ Yes (GL account) |

**Hard Rules (Embedded):**
- E-Faktur numbering format (dari DJP)
- Due date: 20th of following month
- Monthly SPT Masa requirement
- Tax invoice mandatory for threshold

**Calculation Formula (Soft):**
```
# Exclusive (default):
ppn_amount = base_amount × ppn_rate

# Inclusive:
base_amount = total / (1 + ppn_rate)
ppn_amount = total - base_amount
```

**Journal Templates:**

Penjualan (Output VAT):
```
Dr. Accounts Receivable     [total_amount]
    Cr. Sales Revenue           [base_amount]
    Cr. PPN Keluaran            [ppn_amount]
```

Pembelian (Input VAT):
```
Dr. Expense/Inventory       [base_amount]
Dr. PPN Masukan             [ppn_amount]
    Cr. Accounts Payable        [total_amount]
```

#### 4.2.2 PPh 21 (Payroll Tax)

**Soft Rules (Configurable):**

| Rule Code | Type | Default | Description |
|-----------|------|---------|-------------|
| `TAX_PPH21_TER_TABLE` | mapping | TER 2024 | Tarif Efektif Rata-rata table |
| `TAX_PPH21_PAYABLE_ACCOUNT` | mapping | 2104 | GL account for liability |
| `TAX_PPH21_AUTO_CALCULATE` | toggle | true | Auto-calculate on payroll |

**TER Table (Soft - dapat di-import/update):**

```json
{
  "category_A": {
    "status": ["TK/0", "TK/1", "K/0"],
    "brackets": [
      {"min": 0, "max": 5400000, "rate": 0},
      {"min": 5400000, "max": 5650000, "rate": 0.25},
      {"min": 5650000, "max": 5950000, "rate": 0.50},
      ...
    ]
  },
  "category_B": {...},
  "category_C": {...}
}
```

**Journal Template:**
```
Dr. Salary Expense          [gross_salary]
    Cr. PPh 21 Payable          [pph21_amount]
    Cr. Bank/Cash               [net_salary]
```

#### 4.2.3 PPh 23 (Service Withholding)

**Soft Rules (Configurable):**

| Rule Code | Type | Default | Description |
|-----------|------|---------|-------------|
| `TAX_PPH23_RATE_JASA` | percentage | 2% | Services rate |
| `TAX_PPH23_RATE_SEWA` | percentage | 2% | Rent (non-property) rate |
| `TAX_PPH23_RATE_DIVIDEN` | percentage | 15% | Dividend rate |
| `TAX_PPH23_PAYABLE_ACCOUNT` | mapping | 2105 | GL account |
| `TAX_PPH23_AUTO_WITHHOLD` | toggle | true | Auto-calculate on AP |

**Journal Template (Pembayaran Jasa):**
```
Dr. Consulting Expense      [gross_amount]
    Cr. PPh 23 Payable          [pph23_amount]
    Cr. Accounts Payable        [net_amount]
```

#### 4.2.4 PPh 4(2) (Final Tax)

**Soft Rules (Configurable):**

| Rule Code | Type | Default | Description |
|-----------|------|---------|-------------|
| `TAX_PPH42_RATE_SEWA_TB` | percentage | 10% | Property rent rate |
| `TAX_PPH42_PREPAID_ACCOUNT` | mapping | 1109 | Prepaid tax account |

**Journal Template (Receive Rent - dipotong penyewa):**
```
Dr. Bank                    [net_amount]
Dr. PPh 4(2) Prepaid        [pph42_amount]
    Cr. Rental Income           [gross_amount]
```

### 4.3 Tax Configuration UI

**Config Panel for Tax Page:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Tax Configuration                            [Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📋 PPN Settings                                         │
│ ├── Rate: [12%] ← Dropdown (configurable)               │
│ ├── Calculation: ○ Exclusive ● Inclusive                │
│ ├── Rounding: [Round Down ▼]                            │
│ ├── E-Faktur Threshold: [10,000,000]                    │
│ └── Output VAT Account: [2103 - PPN Keluaran ▼]         │
│                                                         │
│ 📋 PPh 23 Settings                                      │
│ ├── Default Rate (Jasa): [2%]                           │
│ ├── Auto-Withhold: [✓] On payment                       │
│ └── Payable Account: [2105 - PPh 23 Payable ▼]          │
│                                                         │
│ 📋 PPh 21 Settings                                      │
│ ├── TER Table: [TER 2024 ▼] [Import New]                │
│ ├── Auto-Calculate: [✓] On payroll run                  │
│ └── Payable Account: [2104 - PPh 21 Payable ▼]          │
│                                                         │
│ 🔗 Impact Analysis                                      │
│ ├── Affects: All Sales Invoices                         │
│ ├── Affects: All Purchase Invoices                      │
│ └── Affects: Payroll Processing                         │
│                                                         │
│ [Save Changes]                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.4 Tax Due Date Rules (Hard)

**Built-in validation - tidak bisa diubah:**

| Tax Type | Reporting Period | Due Date |
|----------|------------------|----------|
| PPN | Monthly | 20th of following month |
| PPh 21 | Monthly | 20th of following month |
| PPh 23 | Monthly | 20th of following month |
| PPh 4(2) | Monthly | 20th of following month |
| PPh Badan | Annual | 4 months after fiscal year |

**System Alerts (Hard):**
- Warning 7 days before due date
- Alert on due date
- Overdue status if not reported

### 4.5 Tax Account Mapping (Soft)

**Configurable per Transaction Type:**

| Transaction Type | Tax Type | Default Account |
|------------------|----------|-----------------|
| Sales Invoice | PPN Keluaran | 2103 |
| Purchase Invoice | PPN Masukan | 1106 |
| Payment to Vendor | PPh 23 | 2105 |
| Payroll | PPh 21 | 2104 |
| Receive Rent | PPh 4(2) | 1109 |

**Organization dapat override mapping via Config Panel.**

### 4.6 Tax Inclusive vs Exclusive (Soft)

**Exclusive (Default):**
```
Price: Rp 100,000
PPN (12%): Rp 12,000
Total: Rp 112,000
```

**Inclusive:**
```
Total: Rp 112,000
Base: Rp 100,000 (112,000 / 1.12)
PPN: Rp 12,000 (112,000 - 100,000)
```

**Config Rule:**
```json
{
  "rule_code": "TAX_PPN_CALCULATION",
  "rule_type": "selection",
  "default_value": "exclusive",
  "allowed_values": [
    {"value": "exclusive", "label": "Tax Exclusive", "label_id": "Belum Termasuk Pajak"},
    {"value": "inclusive", "label": "Tax Inclusive", "label_id": "Sudah Termasuk Pajak"}
  ]
}
```

### 4.7 Tax Rounding Rules (Soft)

| Method | Example | Result |
|--------|---------|--------|
| `round` | 12,345.67 | 12,346 |
| `round_down` | 12,345.67 | 12,345 |
| `round_up` | 12,345.67 | 12,346 |
| `round_100` | 12,345.67 | 12,300 |

**Config Rule:**
```json
{
  "rule_code": "TAX_ROUNDING",
  "rule_type": "selection",
  "default_value": "round_down",
  "allowed_values": [
    {"value": "round", "label": "Standard Rounding"},
    {"value": "round_down", "label": "Round Down (Floor)"},
    {"value": "round_up", "label": "Round Up (Ceiling)"},
    {"value": "round_100", "label": "Round to Nearest 100"}
  ]
}
```

### 4.8 Database Schema

```sql
-- Tax Types (System-defined)
CREATE TABLE tax_types (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(20) NOT NULL UNIQUE,     -- 'PPN', 'PPH21', 'PPH23', 'PPH42'
    name VARCHAR(100) NOT NULL,
    name_id VARCHAR(100),

    -- Hard rules (embedded)
    reporting_period VARCHAR(20) NOT NULL,  -- 'monthly', 'annual'
    due_day INTEGER NOT NULL,               -- 20 for monthly

    is_system BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tax Rates (Soft - configurable per organization)
CREATE TABLE tax_rates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tax_type_id INTEGER NOT NULL REFERENCES tax_types(id) ON DELETE CASCADE,

    rate DECIMAL(5,2) NOT NULL,            -- 12.00 for 12%
    effective_from DATE NOT NULL,
    effective_to DATE,                     -- NULL = still active

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    UNIQUE(organization_id, tax_type_id, effective_from)
);

-- Tax Account Mapping (Soft - configurable)
CREATE TABLE tax_account_mappings (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tax_type_id INTEGER NOT NULL REFERENCES tax_types(id) ON DELETE CASCADE,

    transaction_type VARCHAR(50) NOT NULL,  -- 'sales', 'purchase', 'payroll'
    account_id INTEGER NOT NULL REFERENCES coa_accounts(id) ON DELETE CASCADE,

    is_default BOOLEAN DEFAULT FALSE,

    UNIQUE(organization_id, tax_type_id, transaction_type)
);

-- PPh 21 TER Tables (Soft - importable)
CREATE TABLE pph21_ter_tables (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,            -- 'TER 2024'
    effective_from DATE NOT NULL,
    effective_to DATE,

    table_data JSONB NOT NULL,             -- Full TER table as JSON

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Tax Transactions (for reporting)
CREATE TABLE tax_transactions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tax_type_id INTEGER NOT NULL REFERENCES tax_types(id) ON DELETE CASCADE,

    transaction_date DATE NOT NULL,
    tax_period VARCHAR(7) NOT NULL,        -- '2025-12'

    base_amount DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) NOT NULL,

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    source_type VARCHAR(50),               -- 'invoice', 'payment', 'payroll'
    source_id INTEGER,

    -- E-Faktur (PPN only)
    faktur_number VARCHAR(50),
    faktur_status VARCHAR(20),             -- 'created', 'reported', 'approved'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tax_transactions_period ON tax_transactions(organization_id, tax_period);
CREATE INDEX idx_tax_transactions_type ON tax_transactions(tax_type_id);
```

---

## 5. Period & Closing

> **Status**: ⚠️ Draft - Perlu Konsultasi Pakar
> **Note**: Alur real-world perlu divalidasi dengan praktisi accounting

### 5.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Fiscal Year Start | ❌ | ✅ (January default, configurable) |
| Period Count | ✅ (12 + 1 adjustment) | ❌ |
| Period Immutability | ✅ (closed = no changes) | ❌ |
| Closing Sequence | ✅ (must follow order) | ❌ |
| Grace Period | ❌ | ✅ (days after period end) |
| Soft Close Warning | ❌ | ✅ (warn/block policy) |
| Closing Checklist | ❌ | ✅ (items configurable) |
| Auto-Closing | ❌ | ✅ (enable/disable) |

### 5.2 Fiscal Year Configuration (Soft)

**Soft Rules:**

| Rule Code | Type | Default | Description |
|-----------|------|---------|-------------|
| `PERIOD_FISCAL_START_MONTH` | selection | 1 (January) | Bulan awal fiscal year |
| `PERIOD_GRACE_DAYS` | threshold | 15 | Hari setelah period end untuk posting |
| `PERIOD_AUTO_CLOSE` | toggle | false | Auto-close setelah grace period |
| `PERIOD_CLOSING_APPROVAL` | toggle | true | Butuh approval untuk close |

**Period Structure (Hard):**

```
Fiscal Year: January 2025 - December 2025

Period 01: Jan 2025     Period 07: Jul 2025
Period 02: Feb 2025     Period 08: Aug 2025
Period 03: Mar 2025     Period 09: Sep 2025
Period 04: Apr 2025     Period 10: Oct 2025
Period 05: May 2025     Period 11: Nov 2025
Period 06: Jun 2025     Period 12: Dec 2025
Period 13: Adjustment (Year-end entries only)
```

### 5.3 Period Status (Hard)

**Status Flow (tidak bisa diubah):**

```
OPEN → SOFT_CLOSED → CLOSED → LOCKED
  │         │           │         │
  └────────────────────────────────┘
       Cannot revert once LOCKED
```

| Status | Can Post? | Can Edit? | Can Void? | Description |
|--------|-----------|-----------|-----------|-------------|
| `OPEN` | ✅ | ✅ | ✅ | Normal operations |
| `SOFT_CLOSED` | ⚠️ Warning | ✅ | ✅ | Grace period, warn before post |
| `CLOSED` | ❌ Block | ❌ | ⚠️ Special | After reconciliation |
| `LOCKED` | ❌ Block | ❌ | ❌ | Permanent, setelah audit |

### 5.4 Period Locking Policy (Soft)

**Configurable Behavior:**

```json
{
  "rule_code": "PERIOD_SOFT_CLOSE_ACTION",
  "rule_type": "selection",
  "default_value": "warn",
  "allowed_values": [
    {"value": "allow", "label": "Allow posting without warning"},
    {"value": "warn", "label": "Show warning, allow proceed"},
    {"value": "approval", "label": "Require approval to post"},
    {"value": "block", "label": "Block all posting"}
  ]
}
```

### 5.5 Month-End Closing Checklist (Soft)

**Configurable checklist per organization:**

```json
{
  "rule_code": "PERIOD_CLOSING_CHECKLIST",
  "rule_type": "mapping",
  "default_value": [
    {"code": "BANK_RECON", "name": "Bank Reconciliation", "is_required": true, "order": 1},
    {"code": "AR_RECON", "name": "AR Reconciliation", "is_required": true, "order": 2},
    {"code": "AP_RECON", "name": "AP Reconciliation", "is_required": true, "order": 3},
    {"code": "INV_COUNT", "name": "Inventory Count", "is_required": false, "order": 4},
    {"code": "DEPRECIATION", "name": "Depreciation Run", "is_required": true, "order": 5},
    {"code": "ACCRUALS", "name": "Accrual Entries", "is_required": true, "order": 6},
    {"code": "INTERCO", "name": "Intercompany Reconciliation", "is_required": false, "order": 7},
    {"code": "TRIAL_BAL", "name": "Trial Balance Review", "is_required": true, "order": 8}
  ]
}
```

**UI Checklist:**

```
┌─────────────────────────────────────────────────────────┐
│ 📅 Period Closing: December 2025                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ Checklist (6/8 completed)                            │
│ [✓] Bank Reconciliation        Completed by: Finance    │
│ [✓] AR Reconciliation          Completed by: AR Team    │
│ [✓] AP Reconciliation          Completed by: AP Team    │
│ [ ] Inventory Count            Optional, skipped        │
│ [✓] Depreciation Run           Auto-completed           │
│ [✓] Accrual Entries            Completed by: Manager    │
│ [ ] Intercompany Recon         Optional, skipped        │
│ [✓] Trial Balance Review       Completed by: CFO        │
│                                                         │
│ 📊 Period Summary                                       │
│ ├── Total Journals: 1,245                               │
│ ├── Total Debit: Rp 15,678,900,000                      │
│ ├── Total Credit: Rp 15,678,900,000                     │
│ └── Balance: Rp 0 ✅                                    │
│                                                         │
│ [Close Period]                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.6 Year-End Closing (Hard + Soft)

**Hard Rules (Embedded):**

1. **Closing Sequence** - harus berurutan:
   - Close semua monthly periods dulu
   - Adjustment period (13) terakhir
   - Generate closing journal entries

2. **Closing Journal** - auto-generated:
   ```
   # Step 1: Close Revenue to Income Summary
   Dr. Revenue Accounts        [Total Revenue]
       Cr. Income Summary          [Total Revenue]

   # Step 2: Close Expenses to Income Summary
   Dr. Income Summary          [Total Expenses]
       Cr. Expense Accounts        [Total Expenses]

   # Step 3: Transfer to Retained Earnings
   If Net Income (profit):
   Dr. Income Summary          [Net Income]
       Cr. Retained Earnings       [Net Income]

   If Net Loss:
   Dr. Retained Earnings       [Net Loss]
       Cr. Income Summary          [Net Loss]
   ```

3. **Opening Balances** - auto-generated:
   - Balance sheet accounts carry forward
   - Income/Expense accounts reset to zero
   - Retained Earnings updated

**Soft Rules (Configurable):**

| Rule Code | Type | Default | Description |
|-----------|------|---------|-------------|
| `YEAR_END_APPROVAL` | toggle | true | Require approval for year-end close |
| `YEAR_END_JOURNAL_TYPE` | selection | CJ | Closing journal type |
| `YEAR_END_RETAINED_ACCOUNT` | mapping | 3020 | Retained earnings account |
| `YEAR_END_INCOME_SUMMARY` | mapping | 3099 | Income summary account |

### 5.7 Period Reopening (Hard)

**Rule:** Closed period TIDAK BOLEH dibuka kembali.

**Exception:** `LOCKED` period absolutely cannot be changed. `CLOSED` period can only be voided with special approval.

**Workaround for corrections:**
- Post adjustment in current open period
- Create reversing entry in current period
- Document reference to original transaction

### 5.8 Config Panel

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Period Configuration                         [Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📋 Fiscal Year Settings                                 │
│ ├── Start Month: [January ▼]                            │
│ ├── Period Count: 12 + 1 Adjustment (fixed)             │
│ └── Current Fiscal Year: 2025                           │
│                                                         │
│ 📋 Closing Policy                                       │
│ ├── Grace Period: [15] days                             │
│ ├── Soft Close Action: [Warn and allow ▼]               │
│ ├── Require Approval: [✓] Yes                           │
│ └── Auto-Close: [ ] No                                  │
│                                                         │
│ 📋 Year-End Settings                                    │
│ ├── Retained Earnings: [3020 - Retained Earnings ▼]     │
│ ├── Income Summary: [3099 - Income Summary ▼]           │
│ └── Closing Journal Type: [CJ - Closing Journal ▼]      │
│                                                         │
│ 📋 Closing Checklist [Manage Items]                     │
│ ├── 8 items configured                                  │
│ └── 5 required, 3 optional                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.9 Database Schema

```sql
-- Fiscal Years
CREATE TABLE fiscal_years (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(50) NOT NULL,              -- 'FY 2025'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- 'open', 'closing', 'closed'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    closed_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, start_date)
);

-- Accounting Periods
CREATE TABLE accounting_periods (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    fiscal_year_id INTEGER NOT NULL REFERENCES fiscal_years(id) ON DELETE CASCADE,

    period_number INTEGER NOT NULL,         -- 1-12, 13 for adjustment
    name VARCHAR(50) NOT NULL,              -- 'January 2025', 'Adjustment 2025'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- 'open', 'soft_closed', 'closed', 'locked'

    -- Closing tracking
    soft_closed_at TIMESTAMP WITH TIME ZONE,
    soft_closed_by_id INTEGER REFERENCES users(id),
    closed_at TIMESTAMP WITH TIME ZONE,
    closed_by_id INTEGER REFERENCES users(id),
    locked_at TIMESTAMP WITH TIME ZONE,
    locked_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, fiscal_year_id, period_number)
);

-- Period Closing Checklist
CREATE TABLE period_closing_checklist (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    period_id INTEGER NOT NULL REFERENCES accounting_periods(id) ON DELETE CASCADE,

    checklist_code VARCHAR(50) NOT NULL,    -- 'BANK_RECON'
    checklist_name VARCHAR(100) NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,

    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'completed', 'skipped'
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by_id INTEGER REFERENCES users(id),
    notes TEXT,

    UNIQUE(period_id, checklist_code)
);

-- Closing Journal Mapping
CREATE TABLE closing_journal_entries (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fiscal_year_id INTEGER NOT NULL REFERENCES fiscal_years(id) ON DELETE CASCADE,

    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id),
    closing_type VARCHAR(20) NOT NULL,      -- 'revenue_close', 'expense_close', 'retained_transfer'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_periods_org_status ON accounting_periods(organization_id, status);
CREATE INDEX idx_periods_fiscal ON accounting_periods(fiscal_year_id);
```

---

## 6. Financial Reporting

> **Status**: ✅ Approved (2025-12-07)

### 6.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Report Structure | ✅ (Assets = Liab + Equity) | ❌ |
| Debit = Credit Check | ✅ | ❌ |
| Report Line Mapping | ❌ | ✅ (via Config Panel) |
| Comparative Periods | ❌ | ✅ (flexible selection) |
| Report Templates | ❌ | ✅ (PSAK/USALI/Custom) |
| Export Formats | ❌ | ✅ (PDF, Excel, CSV) |

### 6.2 Report Categories

**Dual Report System:**

| Category | Purpose | Format | Required |
|----------|---------|--------|----------|
| **Statutory (PSAK)** | Regulatory compliance, audit | PSAK/IFRS standard | Yes |
| **Operational (USALI)** | Hotel management, performance | USALI departmental | Yes (hospitality) |
| **Custom** | Organization-specific | User-defined | Optional |

### 6.3 Statutory Reports (PSAK/IFRS)

#### 6.3.1 Balance Sheet (Laporan Posisi Keuangan)

**Structure (Hard):**
```
ASSETS
├── Current Assets
│   ├── Cash & Cash Equivalents
│   ├── Accounts Receivable
│   ├── Inventory
│   └── Prepaid Expenses
└── Non-Current Assets
    ├── Property, Plant & Equipment
    ├── Intangible Assets
    └── Other Non-Current Assets

LIABILITIES
├── Current Liabilities
│   ├── Accounts Payable
│   ├── Accrued Expenses
│   ├── Tax Payable
│   └── Short-term Debt
└── Non-Current Liabilities
    ├── Long-term Debt
    └── Deferred Tax

EQUITY
├── Share Capital
├── Retained Earnings
└── Other Comprehensive Income
```

**Line Mapping (Soft - Configurable):**

```json
{
  "report_line": "current_assets.cash",
  "display_name": "Cash & Cash Equivalents",
  "display_name_id": "Kas dan Setara Kas",
  "account_filter": {
    "type_codes": ["1101", "1102"],
    "or_tags": ["cash", "cash_equivalent"]
  },
  "aggregation": "sum_balance"
}
```

#### 6.3.2 Income Statement (Laporan Laba Rugi)

**Structure (Hard):**
```
Revenue
├── Operating Revenue
└── Other Income

Cost of Sales
└── Direct Costs

Gross Profit = Revenue - Cost of Sales

Operating Expenses
├── Selling Expenses
├── Administrative Expenses
└── Other Operating Expenses

Operating Income = Gross Profit - Operating Expenses

Other Income/Expenses
├── Interest Income
├── Interest Expense
└── Foreign Exchange Gain/Loss

Income Before Tax = Operating Income + Other

Tax Expense
└── Income Tax

Net Income = Income Before Tax - Tax
```

#### 6.3.3 Cash Flow Statement

**Methods (Soft - Configurable):**

| Method | Description |
|--------|-------------|
| **Direct** | Actual cash receipts & payments |
| **Indirect** | Start from Net Income, adjust for non-cash |

**Structure (Hard):**
```
Operating Activities
├── Cash from customers
├── Cash paid to suppliers
├── Cash paid to employees
└── Other operating cash flows

Investing Activities
├── Purchase of PPE
├── Sale of PPE
└── Investment activities

Financing Activities
├── Proceeds from borrowings
├── Repayment of borrowings
├── Dividends paid
└── Capital contributions

Net Change in Cash
+ Opening Cash Balance
= Closing Cash Balance
```

### 6.4 Operational Reports (USALI)

**Departmental P&L Structure:**

```
┌─────────────────────────────────────────────────────────┐
│ DEPARTMENTAL INCOME STATEMENT - December 2025           │
├─────────────────────────────────────────────────────────┤
│                        Rooms    F&B      Spa     Total  │
│ Revenue               50,000  30,000  10,000   90,000   │
│ Cost of Sales              0  12,000   3,000   15,000   │
│ ─────────────────────────────────────────────────────── │
│ Gross Profit          50,000  18,000   7,000   75,000   │
│ Payroll & Related     15,000  10,000   4,000   29,000   │
│ Other Expenses         5,000   3,000   1,000    9,000   │
│ ─────────────────────────────────────────────────────── │
│ Departmental Profit   30,000   5,000   2,000   37,000   │
│                        60.0%   16.7%   20.0%    41.1%   │
└─────────────────────────────────────────────────────────┘
```

**USALI Statistics (Soft - Formula configurable):**

| Metric | Default Formula | Configurable |
|--------|-----------------|--------------|
| Occupancy % | `occupied_rooms / available_rooms × 100` | ✅ |
| ADR | `room_revenue / occupied_rooms` | ✅ |
| RevPAR | `room_revenue / available_rooms` | ✅ |
| TRevPAR | `total_revenue / available_rooms` | ✅ |
| GOPPAR | `gop / available_rooms` | ✅ |

### 6.5 Comparative Reports (Soft)

**Flexible Period Selection:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Report Settings                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Period: [December 2025 ▼]                               │
│                                                         │
│ Compare with:                                           │
│ [✓] Previous Month (November 2025)                      │
│ [✓] Same Month Last Year (December 2024)                │
│ [ ] Budget                                              │
│ [ ] Forecast                                            │
│ [✓] Year-to-Date                                        │
│                                                         │
│ Show variance as:                                       │
│ ○ Amount only                                           │
│ ● Amount and Percentage                                 │
│ ○ Percentage only                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Output Example:**

```
                      Dec 2025   Nov 2025   Var %    Dec 2024   Var %
Room Revenue          50,000     48,000    +4.2%    45,000    +11.1%
F&B Revenue           30,000     28,000    +7.1%    27,000    +11.1%
Total Revenue         90,000     85,000    +5.9%    80,000    +12.5%
```

### 6.6 Report Line Mapping Config (Soft)

**Config Panel:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Balance Sheet Mapping                        [Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Report Line: Cash & Cash Equivalents                    │
│ ──────────────────────────────────────────────────────  │
│                                                         │
│ Included Accounts:                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [✓] 1101-xxx - Cash accounts                        │ │
│ │ [✓] 1102-xxx - Bank accounts (< 3 months)           │ │
│ │ [ ] 1102-xxx - Time deposits (> 3 months)           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Or by Account Type:                                     │
│ [✓] 1101 - Cash    [✓] 1102 - Bank                     │
│                                                         │
│ Preview Balance: Rp 125,000,000                         │
│                                                         │
│ [Save Mapping]                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.7 Database Schema

```sql
-- Report Templates (System + Organization)
CREATE TABLE report_templates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),

    report_category VARCHAR(20) NOT NULL,   -- 'statutory', 'operational', 'custom'
    report_type VARCHAR(50) NOT NULL,       -- 'balance_sheet', 'income_statement', 'cash_flow', 'departmental_pl'

    structure JSONB NOT NULL,               -- Report line structure
    default_settings JSONB,                 -- Default comparative, format, etc.

    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id)
);

-- Report Line Mappings (Soft - per organization)
CREATE TABLE report_line_mappings (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES report_templates(id) ON DELETE CASCADE,

    line_code VARCHAR(50) NOT NULL,         -- 'current_assets.cash'
    line_name VARCHAR(200) NOT NULL,
    line_name_id VARCHAR(200),

    -- Account selection
    account_filter JSONB NOT NULL,          -- {"type_codes": ["1101"], "tags": ["cash"]}
    aggregation VARCHAR(20) DEFAULT 'sum',  -- 'sum', 'avg', 'count'

    -- Display
    display_order INTEGER DEFAULT 0,
    indent_level INTEGER DEFAULT 0,
    is_bold BOOLEAN DEFAULT FALSE,
    is_total BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, template_id, line_code)
);

-- Generated Reports (for audit trail)
CREATE TABLE generated_reports (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES report_templates(id),

    report_name VARCHAR(200) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    parameters JSONB,                       -- Comparative settings, filters
    report_data JSONB NOT NULL,             -- Actual report data snapshot

    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by_id INTEGER REFERENCES users(id),

    -- Export tracking
    export_format VARCHAR(20),              -- 'pdf', 'excel', 'csv'
    exported_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_generated_reports_org ON generated_reports(organization_id, generated_at DESC);
```

---

## 7. Bank & Cash Management

> **Status**: ✅ Approved (2025-12-07)

### 7.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Bank Account Structure | ✅ (code, name, currency, GL) | ❌ |
| Reconciliation Balance Check | ✅ (must balance) | ❌ |
| Petty Cash Type | ❌ | ✅ (imprest/fluctuating) |
| Transaction Limit | ❌ | ✅ (per kas kecil) |
| Approval Threshold | ❌ | ✅ (configurable) |
| Bank Statement Parser | ❌ | ✅ (per bank format) |

### 7.2 Bank Accounts

**Multi-Bank Support (Unlimited):**

```
┌─────────────────────────────────────────────────────────┐
│ Bank Accounts - Hotel ABC                               │
├─────────────────────────────────────────────────────────┤
│ Code      │ Name              │ Bank    │ Currency │ GL │
├───────────┼───────────────────┼─────────┼──────────┼────┤
│ BCA-IDR   │ BCA Operating     │ BCA     │ IDR      │1102│
│ BCA-USD   │ BCA USD Account   │ BCA     │ USD      │1102│
│ MDR-PAY   │ Mandiri Payroll   │ Mandiri │ IDR      │1102│
│ BNI-TAX   │ BNI Tax Payment   │ BNI     │ IDR      │1102│
│ CIMB-SAV  │ CIMB Savings      │ CIMB    │ IDR      │1102│
└─────────────────────────────────────────────────────────┘
```

**Bank Account Attributes:**

| Field | Description | Required |
|-------|-------------|----------|
| `code` | Unique identifier | Yes |
| `name` | Display name | Yes |
| `bank_name` | Nama bank | Yes |
| `account_number` | Nomor rekening | Yes |
| `currency` | IDR, USD, etc. | Yes |
| `account_type` | operating, payroll, tax, savings | Yes |
| `gl_account_id` | Mapping ke CoA | Yes |
| `statement_format` | BCA, Mandiri, BNI, etc. | For import |
| `is_active` | Status aktif | Yes |

### 7.3 Bank Reconciliation

**Dual Mode (User Pilih):**

| Mode | Description | Use Case |
|------|-------------|----------|
| **Manual** | User cocokkan transaksi satu-satu | Bank kecil, transaksi sedikit |
| **Semi-Auto** | Import file, system suggest match | Bank besar, transaksi banyak |

#### 7.3.1 Manual Reconciliation

```
┌─────────────────────────────────────────────────────────┐
│ 🏦 Bank Reconciliation - BCA Operating (December 2025)  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Bank Balance (per statement):  Rp 95,500,000            │
│ Book Balance (per GL):         Rp 100,000,000           │
│ Difference:                    Rp (4,500,000)           │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ Outstanding Checks (belum cair):                        │
│ [+] CHK-001  Supplier A    31-Dec   Rp 3,000,000        │
│ [+] CHK-002  Vendor B      30-Dec   Rp 2,000,000        │
│                            Total:   Rp 5,000,000        │
│                                                         │
│ Deposits in Transit (belum masuk bank):                 │
│ [+] DEP-099  Cash Deposit  31-Dec   Rp 1,500,000        │
│                                                         │
│ Bank Charges (belum dicatat):                           │
│ [+] Admin fee December              Rp (50,000)   [ADD] │
│                                                         │
│ Interest (belum dicatat):                               │
│ [+] Interest December               Rp 50,000     [ADD] │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ Adjusted Book Balance:         Rp 95,500,000            │
│ Bank Balance:                  Rp 95,500,000            │
│ Difference:                    Rp 0 ✅ BALANCED         │
│                                                         │
│ [Complete Reconciliation]                               │
└─────────────────────────────────────────────────────────┘
```

#### 7.3.2 Semi-Auto Reconciliation

**Step 1: Import Bank Statement**

```
┌─────────────────────────────────────────────────────────┐
│ 📥 Import Bank Statement                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Bank Account: [BCA Operating ▼]                         │
│ Statement Format: [BCA CSV ▼]                           │
│                                                         │
│ Supported Formats:                                      │
│ ├── BCA (CSV, Excel)                                    │
│ ├── Mandiri (CSV, Excel)                                │
│ ├── BNI (CSV, Excel)                                    │
│ ├── BRI (CSV)                                           │
│ ├── CIMB (Excel)                                        │
│ └── Generic (CSV with mapping)                          │
│                                                         │
│ [📁 Choose File] statement_dec2025.csv                  │
│                                                         │
│ [Import & Match]                                        │
└─────────────────────────────────────────────────────────┘
```

**Step 2: Auto-Match Results**

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Auto-Match Results                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ Matched: 145 transactions                            │
│ ⚠️ Suggested: 12 transactions (need confirmation)       │
│ ❓ Unmatched: 5 transactions                            │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ SUGGESTED MATCHES (confirm/reject):                     │
│                                                         │
│ Bank: 02-Dec  Transfer In  Rp 5,000,000                 │
│ Book: 01-Dec  AR Receipt   Rp 5,000,000  Guest ABC      │
│ [✓ Match] [✗ Reject]                                    │
│                                                         │
│ Bank: 15-Dec  Transfer Out Rp 3,500,000                 │
│ Book: 14-Dec  AP Payment   Rp 3,500,000  Supplier X     │
│ [✓ Match] [✗ Reject]                                    │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ UNMATCHED BANK TRANSACTIONS:                            │
│                                                         │
│ 28-Dec  Bank Charge    Rp (50,000)                      │
│ Action: [Create Journal Entry] [Ignore]                 │
│                                                         │
│ 31-Dec  Interest       Rp 75,000                        │
│ Action: [Create Journal Entry] [Ignore]                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Matching Logic (Soft - Configurable):**

```json
{
  "rule_code": "BANK_RECON_MATCH_RULES",
  "rule_type": "mapping",
  "default_value": {
    "match_by_amount": true,
    "match_by_date": true,
    "date_tolerance_days": 3,
    "match_by_reference": true,
    "auto_match_threshold": 100
  }
}
```

### 7.4 Petty Cash (Kas Kecil)

**Configurable Type per Kas:**

| Type | Description | Best For |
|------|-------------|----------|
| **Imprest** | Saldo tetap, replenishment | Kontrol ketat |
| **Fluctuating** | Saldo berubah | Fleksibilitas tinggi |

#### 7.4.1 Petty Cash Setup

```
┌─────────────────────────────────────────────────────────┐
│ ➕ Create Petty Cash                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Name: [Kas Kecil Front Office        ]                  │
│ Code: [PC-FO                         ]                  │
│ Department: [Front Office ▼]                            │
│ GL Account: [1101-001-FO ▼]                             │
│                                                         │
│ Type:                                                   │
│ ● Imprest (saldo tetap)                                 │
│   Fixed Amount: [Rp 5,000,000    ]                      │
│                                                         │
│ ○ Fluctuating (saldo berubah)                           │
│   Min Balance Warning: [Rp 500,000]                     │
│                                                         │
│ Controls:                                               │
│ Max per transaction: [Rp 500,000  ]                     │
│ Custodian: [John Doe ▼]                                 │
│ Approval required above: [Rp 200,000]                   │
│ Approver: [FO Manager ▼]                                │
│                                                         │
│ [Save]                                                  │
└─────────────────────────────────────────────────────────┘
```

#### 7.4.2 Petty Cash Transaction

```
┌─────────────────────────────────────────────────────────┐
│ 💵 Petty Cash - Front Office                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Type: Imprest | Fixed: Rp 5,000,000                     │
│ Current Balance: Rp 4,150,000                           │
│ Unreplenished: Rp 850,000                               │
│                                                         │
│ Recent Transactions:                                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Date    │ Description      │ Amount   │ Status     │ │
│ ├─────────┼──────────────────┼──────────┼────────────┤ │
│ │ 05-Dec  │ Parking guest    │ (50,000) │ ✅ Approved│ │
│ │ 05-Dec  │ Materai 10000x5  │ (50,000) │ ✅ Approved│ │
│ │ 06-Dec  │ Office supplies  │ (200,000)│ ✅ Approved│ │
│ │ 07-Dec  │ Courier fee      │ (150,000)│ ✅ Approved│ │
│ │ 08-Dec  │ Meeting snacks   │ (400,000)│ ⏳ Pending │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [+ New Transaction] [Request Replenishment]             │
└─────────────────────────────────────────────────────────┘
```

#### 7.4.3 Replenishment (Imprest)

```
Sebelum replenishment:
- Fixed Amount: Rp 5,000,000
- Current Cash: Rp 4,150,000
- Vouchers:     Rp   850,000 (bukti pengeluaran)
- Total:        Rp 5,000,000 ✓

Replenishment Journal:
Dr. Parking Expense        50,000
Dr. Office Supplies        50,000
Dr. Stationery            200,000
Dr. Courier Expense       150,000
Dr. Meeting Expense       400,000
    Cr. Bank                  850,000

Setelah replenishment:
- Cash: Rp 5,000,000 (kembali full)
```

### 7.5 Cash Count & Verification

**Physical Count (Soft - Configurable frequency):**

```
┌─────────────────────────────────────────────────────────┐
│ 🔢 Cash Count - PC-FO (08 Dec 2025, 17:00)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Denomination Count:                                     │
│ Rp 100,000 × [35] = Rp 3,500,000                        │
│ Rp  50,000 × [10] = Rp   500,000                        │
│ Rp  20,000 × [ 5] = Rp   100,000                        │
│ Rp  10,000 × [ 3] = Rp    30,000                        │
│ Rp   5,000 × [ 2] = Rp    10,000                        │
│ Rp   2,000 × [ 3] = Rp     6,000                        │
│ Rp   1,000 × [ 4] = Rp     4,000                        │
│ ─────────────────────────────────────────────────────── │
│ Physical Count:        Rp 4,150,000                     │
│ System Balance:        Rp 4,150,000                     │
│ Difference:            Rp 0 ✅                          │
│                                                         │
│ Counted by: [John Doe    ]                              │
│ Verified by: [Supervisor ▼]                             │
│                                                         │
│ [Submit Count]                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.6 Config Panel

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Bank & Cash Configuration                    [Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📋 Bank Reconciliation                                  │
│ ├── Default Mode: [Semi-Auto ▼]                         │
│ ├── Date Tolerance: [3] days                            │
│ ├── Auto-match confidence: [100]%                       │
│ └── Require approval: [✓] Yes                           │
│                                                         │
│ 📋 Petty Cash Defaults                                  │
│ ├── Default Type: [Imprest ▼]                           │
│ ├── Max Transaction: [Rp 500,000]                       │
│ ├── Approval Threshold: [Rp 200,000]                    │
│ └── Count Frequency: [Daily ▼]                          │
│                                                         │
│ 📋 Bank Statement Parsers                               │
│ ├── BCA: ✅ Configured                                  │
│ ├── Mandiri: ✅ Configured                              │
│ ├── BNI: ✅ Configured                                  │
│ ├── BRI: ⚠️ Not configured                              │
│ └── [+ Add Custom Parser]                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 7.7 Database Schema

```sql
-- Bank Accounts
CREATE TABLE bank_accounts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
    account_type VARCHAR(20) NOT NULL,      -- 'operating', 'payroll', 'tax', 'savings'

    gl_account_id INTEGER NOT NULL REFERENCES coa_accounts(id),
    statement_format VARCHAR(20),           -- 'bca', 'mandiri', 'bni', 'generic'

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, code)
);

-- Bank Statements (imported)
CREATE TABLE bank_statements (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,

    statement_date DATE NOT NULL,
    opening_balance DECIMAL(18,2) NOT NULL,
    closing_balance DECIMAL(18,2) NOT NULL,

    file_name VARCHAR(200),
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    imported_by_id INTEGER REFERENCES users(id),

    UNIQUE(bank_account_id, statement_date)
);

-- Bank Statement Lines
CREATE TABLE bank_statement_lines (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    statement_id INTEGER NOT NULL REFERENCES bank_statements(id) ON DELETE CASCADE,

    transaction_date DATE NOT NULL,
    value_date DATE,
    description TEXT,
    reference VARCHAR(100),
    debit_amount DECIMAL(18,2) DEFAULT 0,
    credit_amount DECIMAL(18,2) DEFAULT 0,

    -- Matching
    match_status VARCHAR(20) DEFAULT 'unmatched',  -- 'unmatched', 'suggested', 'matched'
    matched_journal_line_id INTEGER REFERENCES journal_entry_lines(id),
    matched_at TIMESTAMP WITH TIME ZONE,
    matched_by_id INTEGER REFERENCES users(id)
);

-- Bank Reconciliations
CREATE TABLE bank_reconciliations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,

    reconciliation_date DATE NOT NULL,
    bank_balance DECIMAL(18,2) NOT NULL,
    book_balance DECIMAL(18,2) NOT NULL,
    adjusted_balance DECIMAL(18,2) NOT NULL,

    status VARCHAR(20) DEFAULT 'draft',     -- 'draft', 'completed'
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by_id INTEGER REFERENCES users(id),

    UNIQUE(bank_account_id, reconciliation_date)
);

-- Petty Cash Accounts
CREATE TABLE petty_cash_accounts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    gl_account_id INTEGER NOT NULL REFERENCES coa_accounts(id),

    cash_type VARCHAR(20) NOT NULL,         -- 'imprest', 'fluctuating'
    fixed_amount DECIMAL(18,2),             -- For imprest
    min_balance_warning DECIMAL(18,2),      -- For fluctuating

    max_transaction_amount DECIMAL(18,2),
    approval_threshold DECIMAL(18,2),
    custodian_user_id INTEGER REFERENCES users(id),
    approver_user_id INTEGER REFERENCES users(id),

    current_balance DECIMAL(18,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, code)
);

-- Petty Cash Transactions
CREATE TABLE petty_cash_transactions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    petty_cash_id INTEGER NOT NULL REFERENCES petty_cash_accounts(id) ON DELETE CASCADE,

    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,  -- 'expense', 'replenishment', 'adjustment'
    description TEXT NOT NULL,
    amount DECIMAL(18,2) NOT NULL,

    expense_account_id INTEGER REFERENCES coa_accounts(id),
    receipt_number VARCHAR(50),
    receipt_image_url TEXT,

    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'approved', 'rejected'
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(id),

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id)
);

-- Cash Counts
CREATE TABLE cash_counts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    petty_cash_id INTEGER NOT NULL REFERENCES petty_cash_accounts(id) ON DELETE CASCADE,

    count_date DATE NOT NULL,
    count_time TIME NOT NULL,

    physical_amount DECIMAL(18,2) NOT NULL,
    system_balance DECIMAL(18,2) NOT NULL,
    difference DECIMAL(18,2) NOT NULL,

    denomination_detail JSONB,              -- {"100000": 35, "50000": 10, ...}

    counted_by_id INTEGER REFERENCES users(id),
    verified_by_id INTEGER REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,

    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bank_statements_account ON bank_statements(bank_account_id, statement_date);
CREATE INDEX idx_petty_cash_txn ON petty_cash_transactions(petty_cash_id, transaction_date);
```

---

## 8. Accounts Receivable (AR)

> **Status**: ✅ Approved (2025-12-07)

### 8.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| AR Balance = Invoice - Payment | ✅ | ❌ |
| Aging Buckets | ✅ (fixed 5 buckets) | ❌ |
| Credit Limit Type | ❌ | ✅ (hard/soft per customer) |
| Credit Limit Amount | ❌ | ✅ (per customer) |
| Payment Terms | ❌ | ✅ (template + custom) |
| Late Fee Calculation | ❌ | ✅ (rate configurable) |

### 8.2 Dual Ledger System (Hotel)

**Separation:**

| Ledger | Source | Real-time | Description |
|--------|--------|-----------|-------------|
| **Guest Ledger** | PMS | Yes | Tamu in-house, belum check-out |
| **City Ledger** | AR Module | No | Setelah check-out, corporate, travel agent |

```
┌─────────────────────────────────────────────────────────┐
│ GUEST LEDGER (Real-time from PMS)                       │
├─────────────────────────────────────────────────────────┤
│ Room 101 - Mr. John Smith (In-House)                    │
│ ├── Room Charge (3 nights)      Rp  3,000,000           │
│ ├── F&B Charge                  Rp    500,000           │
│ ├── Laundry                     Rp    150,000           │
│ ├── Deposit Paid               (Rp  1,000,000)          │
│ └── Current Balance             Rp  2,650,000           │
│                                                         │
│ → On Check-out:                                         │
│   - Pay Full → Close folio                              │
│   - Transfer to City Ledger → Create AR Invoice         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ CITY LEDGER (AR Module)                                 │
├─────────────────────────────────────────────────────────┤
│ Corporate Account - PT ABC                              │
│ ├── INV-2025-001  15-Nov  Rp 5,000,000  Due: 15-Dec     │
│ ├── INV-2025-015  01-Dec  Rp 3,500,000  Due: 31-Dec     │
│ └── Total Outstanding         Rp 8,500,000              │
│                                                         │
│ Travel Agent - Traveloka                                │
│ ├── INV-2025-008  20-Nov  Rp 12,000,000  Due: 20-Dec    │
│ └── Total Outstanding         Rp 12,000,000             │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Customer Master

**Customer Types:**

| Type | Description | Credit Terms |
|------|-------------|--------------|
| `walk_in` | Tamu langsung, bayar tunai | No credit |
| `corporate` | Perusahaan dengan kontrak | Credit limit |
| `travel_agent` | TA/OTA dengan perjanjian | Credit limit |
| `government` | Instansi pemerintah | Special terms |
| `group` | Group booking | Deposit + balance |

**Customer Attributes:**

```
┌─────────────────────────────────────────────────────────┐
│ 🏢 Customer: PT ABC Corporation                         │
├─────────────────────────────────────────────────────────┤
│ Code: CUST-001                                          │
│ Type: Corporate                                         │
│ Tax ID (NPWP): 01.234.567.8-901.000                     │
│                                                         │
│ Credit Settings:                                        │
│ ├── Credit Limit: Rp 50,000,000                         │
│ ├── Limit Type: ● Hard Block  ○ Soft Warning            │
│ ├── Payment Terms: [Net 30 ▼]                           │
│ └── Late Fee: [1.5]% per month                          │
│                                                         │
│ Current Status:                                         │
│ ├── Outstanding: Rp 35,000,000                          │
│ ├── Available Credit: Rp 15,000,000                     │
│ └── Overdue: Rp 5,000,000 (> 30 days)                   │
└─────────────────────────────────────────────────────────┘
```

### 8.4 Credit Limit (Soft - Configurable)

**Per Customer Configuration:**

| Setting | Options |
|---------|---------|
| **Limit Amount** | Configurable per customer |
| **Limit Type** | Hard Block / Soft Warning |
| **Warning Threshold** | Alert at X% of limit |

**Behavior:**

| Type | On Limit Exceeded |
|------|-------------------|
| **Hard Block** | Cannot create new invoice, must pay first |
| **Soft Warning** | Warning shown, but can proceed with approval |

```json
{
  "customer_id": 123,
  "credit_limit": 50000000,
  "credit_limit_type": "hard",
  "warning_threshold_pct": 80,
  "current_outstanding": 35000000,
  "available_credit": 15000000
}
```

### 8.5 Payment Terms (Soft - Template + Custom)

**Template Terms:**

| Code | Name | Days | Description |
|------|------|------|-------------|
| `COD` | Cash on Delivery | 0 | Bayar saat terima |
| `NET7` | Net 7 | 7 | 7 hari dari invoice |
| `NET14` | Net 14 | 14 | 14 hari dari invoice |
| `NET30` | Net 30 | 30 | 30 hari dari invoice |
| `NET45` | Net 45 | 45 | 45 hari dari invoice |
| `NET60` | Net 60 | 60 | 60 hari dari invoice |
| `NET90` | Net 90 | 90 | 90 hari dari invoice |
| `EOM` | End of Month | - | Akhir bulan berikutnya |

**Custom Terms:**
- Organization dapat buat payment terms sendiri
- Contoh: `NET21`, `2/10NET30` (2% discount if paid in 10 days)

### 8.6 Aging Report (Fixed Buckets)

**Standard Buckets:**

| Bucket | Range | Color Code |
|--------|-------|------------|
| Current | Not due yet | 🟢 Green |
| 1-30 | 1-30 days overdue | 🟡 Yellow |
| 31-60 | 31-60 days overdue | 🟠 Orange |
| 61-90 | 61-90 days overdue | 🔴 Red |
| >90 | Over 90 days | ⚫ Black |

**Report Example:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ AR AGING REPORT - As of December 31, 2025                               │
├─────────────────────────────────────────────────────────────────────────┤
│ Customer          │ Current   │ 1-30     │ 31-60   │ 61-90  │ >90     │
├───────────────────┼───────────┼──────────┼─────────┼────────┼─────────┤
│ PT ABC Corp       │ 3,500,000 │ 5,000,000│    -    │   -    │    -    │
│ Traveloka         │12,000,000 │     -    │    -    │   -    │    -    │
│ PT XYZ            │     -     │ 2,000,000│3,000,000│   -    │    -    │
│ Government Office │     -     │     -    │    -    │500,000 │1,000,000│
├───────────────────┼───────────┼──────────┼─────────┼────────┼─────────┤
│ TOTAL             │15,500,000 │ 7,000,000│3,000,000│500,000 │1,000,000│
│ Percentage        │   57.4%   │  25.9%   │  11.1%  │  1.9%  │   3.7%  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.7 Invoice & Payment Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Create     │     │   Sent/     │     │   Paid      │
│  Invoice    │ ──► │   Open      │ ──► │   (Closed)  │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
   Journal:            Due Date           Journal:
   Dr. AR              Tracking           Dr. Bank/Cash
   Cr. Revenue                            Cr. AR
   Cr. PPN
```

**Partial Payment:**
```
Invoice: Rp 10,000,000
Payment 1: Rp 6,000,000 → Remaining: Rp 4,000,000
Payment 2: Rp 4,000,000 → Remaining: Rp 0 (Closed)
```

### 8.8 Database Schema

```sql
-- Customers
CREATE TABLE customers (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    customer_type VARCHAR(20) NOT NULL,     -- 'walk_in', 'corporate', 'travel_agent', 'government', 'group'

    -- Tax
    tax_id VARCHAR(30),                     -- NPWP
    tax_name VARCHAR(200),                  -- Nama sesuai NPWP

    -- Contact
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),

    -- Credit
    credit_limit DECIMAL(18,2) DEFAULT 0,
    credit_limit_type VARCHAR(10) DEFAULT 'soft',  -- 'hard', 'soft'
    warning_threshold_pct INTEGER DEFAULT 80,
    payment_term_id INTEGER REFERENCES payment_terms(id),
    late_fee_pct DECIMAL(5,2) DEFAULT 0,

    -- GL Mapping
    ar_account_id INTEGER REFERENCES coa_accounts(id),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, code)
);

-- Payment Terms
CREATE TABLE payment_terms (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system template

    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    days INTEGER NOT NULL,
    description TEXT,

    -- Discount (e.g., 2/10 Net 30)
    discount_days INTEGER,
    discount_pct DECIMAL(5,2),

    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- AR Invoices
CREATE TABLE ar_invoices (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    invoice_number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,

    customer_id INTEGER NOT NULL REFERENCES customers(id),
    source_type VARCHAR(20),                -- 'pms', 'pos', 'manual'
    source_id INTEGER,                      -- Reference to source document

    subtotal DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) DEFAULT 0,
    total_amount DECIMAL(18,2) NOT NULL,
    paid_amount DECIMAL(18,2) DEFAULT 0,
    balance DECIMAL(18,2) NOT NULL,

    currency VARCHAR(3) DEFAULT 'IDR',
    exchange_rate DECIMAL(18,6) DEFAULT 1,

    status VARCHAR(20) DEFAULT 'open',      -- 'draft', 'open', 'partial', 'paid', 'void'

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, invoice_number)
);

-- AR Payments
CREATE TABLE ar_payments (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    payment_number VARCHAR(50) NOT NULL,
    payment_date DATE NOT NULL,

    customer_id INTEGER NOT NULL REFERENCES customers(id),
    payment_method VARCHAR(20) NOT NULL,    -- 'cash', 'transfer', 'card', 'check'
    bank_account_id INTEGER REFERENCES bank_accounts(id),

    total_amount DECIMAL(18,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',

    reference VARCHAR(100),
    notes TEXT,

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, payment_number)
);

-- Payment Allocations (link payment to invoices)
CREATE TABLE ar_payment_allocations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    payment_id INTEGER NOT NULL REFERENCES ar_payments(id) ON DELETE CASCADE,
    invoice_id INTEGER NOT NULL REFERENCES ar_invoices(id),

    allocated_amount DECIMAL(18,2) NOT NULL,

    UNIQUE(payment_id, invoice_id)
);

CREATE INDEX idx_ar_invoices_customer ON ar_invoices(customer_id, status);
CREATE INDEX idx_ar_invoices_due ON ar_invoices(due_date) WHERE status IN ('open', 'partial');
```

---

## 9. Accounts Payable (AP)

> **Status**: ✅ Approved (2025-12-07)

### 9.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| AP Balance = Invoice - Payment | ✅ | ❌ |
| Aging Buckets | ✅ (fixed 5 buckets) | ❌ |
| Payment Terms | ❌ | ✅ (template + custom) |
| Auto-Withholding PPh 23 | ❌ | ✅ (toggle per vendor) |
| Approval Workflow | ❌ | ✅ (by amount) |

### 9.2 Vendor Master

**Vendor Types:**

| Type | Description | Tax Treatment |
|------|-------------|---------------|
| `supplier` | Supplier barang | PPN + PPh 23 (if applicable) |
| `contractor` | Jasa konstruksi | PPN + PPh 4(2) |
| `consultant` | Jasa konsultan | PPN + PPh 23 |
| `utility` | PLN, PDAM, dll | PPN only |
| `government` | Instansi pemerintah | Special |

**Vendor Attributes:**

```
┌─────────────────────────────────────────────────────────┐
│ 🏭 Vendor: PT Supplier ABC                              │
├─────────────────────────────────────────────────────────┤
│ Code: VEND-001                                          │
│ Type: Supplier                                          │
│ Tax ID (NPWP): 01.234.567.8-901.000                     │
│ PKP: ✅ Yes (Pengusaha Kena Pajak)                      │
│                                                         │
│ Payment Settings:                                       │
│ ├── Payment Terms: [Net 30 ▼]                           │
│ ├── Bank: BCA - 1234567890                              │
│ └── Auto PPh 23: [✓] 2% on services                     │
│                                                         │
│ Current Status:                                         │
│ ├── Outstanding: Rp 25,000,000                          │
│ ├── Overdue: Rp 0                                       │
│ └── YTD Purchases: Rp 150,000,000                       │
└─────────────────────────────────────────────────────────┘
```

### 9.3 Purchase Invoice Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Receive        │     │   Approve       │     │   Pay           │
│  Invoice        │ ──► │   Invoice       │ ──► │   (Closed)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
    Journal:                Approval              Journal:
    Dr. Expense/Inv         Workflow              Dr. AP
    Dr. PPN Masukan                               Cr. PPh 23 Payable
    Cr. AP                                        Cr. Bank
```

**With PPh 23 Withholding:**
```
Invoice: Jasa Konsultan Rp 10,000,000 + PPN Rp 1,200,000

Record Invoice:
Dr. Consulting Expense     10,000,000
Dr. PPN Masukan             1,200,000
    Cr. AP                     11,200,000

Payment (with 2% PPh 23 withholding):
Dr. AP                     11,200,000
    Cr. PPh 23 Payable           200,000  (2% × 10,000,000)
    Cr. Bank                  11,000,000
```

### 9.4 Approval Workflow (Soft)

**Configurable by Amount:**

```json
{
  "rule_code": "AP_APPROVAL_WORKFLOW",
  "rule_type": "mapping",
  "default_value": [
    {"min": 0, "max": 5000000, "approvers": ["finance_staff"]},
    {"min": 5000001, "max": 25000000, "approvers": ["finance_manager"]},
    {"min": 25000001, "max": 100000000, "approvers": ["finance_manager", "finance_director"]},
    {"min": 100000001, "max": null, "approvers": ["finance_director", "cfo"]}
  ]
}
```

**UI:**
```
┌─────────────────────────────────────────────────────────┐
│ 📄 AP Invoice Approval                                  │
├─────────────────────────────────────────────────────────┤
│ Invoice: INV-VEND-2025-001                              │
│ Vendor: PT Supplier ABC                                 │
│ Amount: Rp 75,000,000                                   │
│                                                         │
│ Approval Required:                                      │
│ [✓] Finance Manager - Approved (05-Dec 10:30)           │
│ [ ] Finance Director - Pending                          │
│                                                         │
│ [Approve] [Reject] [Request Info]                       │
└─────────────────────────────────────────────────────────┘
```

### 9.5 Aging Report (Fixed Buckets)

**Same as AR:**

| Bucket | Range | Action |
|--------|-------|--------|
| Current | Not due yet | Normal |
| 1-30 | 1-30 days overdue | Review |
| 31-60 | 31-60 days overdue | Escalate |
| 61-90 | 61-90 days overdue | Urgent |
| >90 | Over 90 days | Critical |

### 9.6 Payment Processing

**Payment Methods:**

| Method | Description | Journal |
|--------|-------------|---------|
| `transfer` | Bank transfer | Dr. AP, Cr. Bank |
| `check` | Cek/Giro | Dr. AP, Cr. Bank (on clear) |
| `cash` | Tunai | Dr. AP, Cr. Cash |
| `offset` | Offset dengan AR | Dr. AP, Cr. AR |

**Batch Payment:**
```
┌─────────────────────────────────────────────────────────┐
│ 💳 Batch Payment                                        │
├─────────────────────────────────────────────────────────┤
│ Payment Date: [08-Dec-2025]                             │
│ Bank Account: [BCA Operating ▼]                         │
│                                                         │
│ Select Invoices to Pay:                                 │
│ [✓] INV-001  PT Supplier A    Rp 5,000,000   Due: 05-Dec│
│ [✓] INV-002  PT Supplier A    Rp 3,000,000   Due: 08-Dec│
│ [✓] INV-005  PT Vendor B      Rp 2,500,000   Due: 10-Dec│
│ [ ] INV-008  PT Vendor C      Rp 8,000,000   Due: 15-Dec│
│                                                         │
│ Selected: 3 invoices                                    │
│ Total Amount: Rp 10,500,000                             │
│ Less PPh 23: Rp (150,000)                               │
│ Net Payment: Rp 10,350,000                              │
│                                                         │
│ [Process Payment]                                       │
└─────────────────────────────────────────────────────────┘
```

### 9.7 Database Schema

```sql
-- Vendors
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    vendor_type VARCHAR(20) NOT NULL,       -- 'supplier', 'contractor', 'consultant', 'utility', 'government'

    -- Tax
    tax_id VARCHAR(30),                     -- NPWP
    tax_name VARCHAR(200),
    is_pkp BOOLEAN DEFAULT FALSE,           -- Pengusaha Kena Pajak

    -- Contact
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),

    -- Payment
    payment_term_id INTEGER REFERENCES payment_terms(id),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(30),
    bank_account_name VARCHAR(200),

    -- Tax Withholding
    is_pph23_withheld BOOLEAN DEFAULT FALSE,
    pph23_rate DECIMAL(5,2) DEFAULT 2.00,

    -- GL Mapping
    ap_account_id INTEGER REFERENCES coa_accounts(id),
    expense_account_id INTEGER REFERENCES coa_accounts(id),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, code)
);

-- AP Invoices
CREATE TABLE ap_invoices (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    invoice_number VARCHAR(50) NOT NULL,
    vendor_invoice_number VARCHAR(50),      -- Nomor invoice dari vendor
    invoice_date DATE NOT NULL,
    received_date DATE NOT NULL,
    due_date DATE NOT NULL,

    vendor_id INTEGER NOT NULL REFERENCES vendors(id),

    subtotal DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) DEFAULT 0,
    total_amount DECIMAL(18,2) NOT NULL,
    paid_amount DECIMAL(18,2) DEFAULT 0,
    balance DECIMAL(18,2) NOT NULL,

    -- Withholding
    pph23_amount DECIMAL(18,2) DEFAULT 0,
    pph42_amount DECIMAL(18,2) DEFAULT 0,

    currency VARCHAR(3) DEFAULT 'IDR',
    exchange_rate DECIMAL(18,6) DEFAULT 1,

    status VARCHAR(20) DEFAULT 'draft',     -- 'draft', 'pending_approval', 'approved', 'partial', 'paid', 'void'

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, invoice_number)
);

-- AP Invoice Approvals
CREATE TABLE ap_invoice_approvals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    invoice_id INTEGER NOT NULL REFERENCES ap_invoices(id) ON DELETE CASCADE,

    approver_user_id INTEGER NOT NULL REFERENCES users(id),
    approval_order INTEGER NOT NULL,

    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'approved', 'rejected'
    approved_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,

    UNIQUE(invoice_id, approver_user_id)
);

-- AP Payments
CREATE TABLE ap_payments (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    payment_number VARCHAR(50) NOT NULL,
    payment_date DATE NOT NULL,

    vendor_id INTEGER NOT NULL REFERENCES vendors(id),
    payment_method VARCHAR(20) NOT NULL,    -- 'transfer', 'check', 'cash', 'offset'
    bank_account_id INTEGER REFERENCES bank_accounts(id),

    total_amount DECIMAL(18,2) NOT NULL,
    pph23_withheld DECIMAL(18,2) DEFAULT 0,
    net_amount DECIMAL(18,2) NOT NULL,

    currency VARCHAR(3) DEFAULT 'IDR',

    reference VARCHAR(100),
    notes TEXT,

    journal_entry_id INTEGER REFERENCES journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, payment_number)
);

-- Payment Allocations
CREATE TABLE ap_payment_allocations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    payment_id INTEGER NOT NULL REFERENCES ap_payments(id) ON DELETE CASCADE,
    invoice_id INTEGER NOT NULL REFERENCES ap_invoices(id),

    allocated_amount DECIMAL(18,2) NOT NULL,

    UNIQUE(payment_id, invoice_id)
);

CREATE INDEX idx_ap_invoices_vendor ON ap_invoices(vendor_id, status);
CREATE INDEX idx_ap_invoices_due ON ap_invoices(due_date) WHERE status IN ('approved', 'partial');
```

---

## 10. Business Rules Engine

> **Status**: ✅ Approved (2025-12-07)

### 10.1 Core Concept: Hard vs Soft Rules

**Masalah**: Business logic yang bervariasi per organization TIDAK BOLEH di-hardcode di backend.

**Solusi**: Pisahkan rules menjadi 2 kategori:

| Type | Description | Where | Changeable |
|------|-------------|-------|------------|
| **Hard Rules** | Business logic fundamental, tidak pernah berubah | Embedded in code | Never |
| **Soft Rules** | Business logic yang bisa bervariasi per organization | Configurable via UI | Always |

### 10.2 Hard Rules (Embedded)

Rules yang HARUS ada di code, tidak bisa dikonfigurasi:

**Double-Entry Accounting:**
- Total Debit = Total Credit (mandatory)
- Journal tidak bisa posted jika unbalanced

**Data Integrity:**
- Required fields validation
- Foreign key constraints
- Data type enforcement

**Security:**
- Authentication & Authorization
- Audit trail logging
- Period locking enforcement

**Regulatory:**
- Invoice numbering uniqueness
- Posted journal immutability

### 10.3 Soft Rules (Configurable)

Rules yang BISA dikonfigurasi via UI per organization:

**Tax Rules:**
- Tax rates (PPN 11% → bisa berubah)
- Tax calculation method (inclusive/exclusive)
- Rounding rules

**Calculations:**
- Total rooms formula (include/exclude OOO?)
- Occupancy calculation base
- RevPAR formula variations
- Service charge percentage

**Thresholds:**
- Approval amounts
- Credit limit warnings
- Auto-post limits

**Business Logic:**
- GL mapping per transaction type
- Department allocations
- Inter-company transfer rules

**Report Mappings:**
- Which accounts map to which report lines
- Consolidation rules
- Currency conversion methods

### 10.4 Per-Page Config Panel

Setiap halaman yang memiliki Soft Rules menampilkan tombol **Config** dengan panel:

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Page Configuration                           [Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📋 Current Settings                                     │
│ ├── Total Rooms Formula: Available - OOO - OOI          │
│ ├── Occupancy Base: Total Available Rooms               │
│ ├── RevPAR Method: Room Revenue / Total Rooms           │
│ └── Service Charge: 10%                                 │
│                                                         │
│ 🔗 Impact Analysis                                      │
│ ├── Affects: Dashboard Statistics                       │
│ ├── Affects: Daily Report                               │
│ ├── Affects: Monthly Report                             │
│ └── Affects: Revenue Analysis                           │
│                                                         │
│ 📜 Change History                                       │
│ ├── 2025-12-01: Service Charge 10% → 11% (by Admin)     │
│ └── 2025-11-15: OOO excluded from total (by Finance)    │
│                                                         │
│ [Edit Settings]                                         │
└─────────────────────────────────────────────────────────┘
```

### 10.5 Rule Types

| Type | UI Component | Example |
|------|--------------|---------|
| `selection` | Dropdown/Radio | Tax calculation method: Inclusive / Exclusive |
| `formula` | Formula editor | `revenue / (available_rooms - ooo_rooms)` |
| `threshold` | Number input | Approval limit: 10,000,000 |
| `toggle` | Switch | Auto-post sales journal: Yes / No |
| `mapping` | Table editor | GL account mapping per transaction |
| `percentage` | Slider/Input | Service charge: 10% |

### 10.6 Formula Engine

**Safe Formula Evaluation** menggunakan `simpleeval`:

```python
from simpleeval import EvalWithCompoundTypes

class FormulaEvaluator:
    def __init__(self):
        self.evaluator = EvalWithCompoundTypes()
        self.evaluator.functions = {
            'sum': sum,
            'avg': lambda x: sum(x)/len(x) if x else 0,
            'min': min,
            'max': max,
            'round': round,
            'abs': abs,
            'if': lambda c, t, f: t if c else f,
            'coalesce': lambda *args: next((a for a in args if a is not None), None),
        }

    def evaluate(self, formula: str, variables: dict) -> any:
        self.evaluator.names = variables
        return self.evaluator.eval(formula)

# Usage
evaluator = FormulaEvaluator()

# Example: RevPAR calculation
result = evaluator.evaluate(
    "round(room_revenue / if(include_ooo, total_rooms, available_rooms), 2)",
    {
        "room_revenue": 150000000,
        "total_rooms": 100,
        "available_rooms": 95,  # excluding OOO
        "include_ooo": False
    }
)
# Result: 1578947.37
```

### 10.7 Impact Analysis

Menggunakan **dependency graph** untuk track rule relationships:

```python
import networkx as nx

class RuleImpactAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_rule(self, rule_code: str, impacts: list[str]):
        """Register rule and its impacts"""
        for impact in impacts:
            self.graph.add_edge(rule_code, impact)

    def get_affected(self, rule_code: str) -> list[str]:
        """Get all items affected by changing this rule"""
        return list(nx.descendants(self.graph, rule_code))

    def get_dependencies(self, target: str) -> list[str]:
        """Get all rules that affect this target"""
        return list(nx.ancestors(self.graph, target))

# Usage
analyzer = RuleImpactAnalyzer()

# Register rule impacts
analyzer.add_rule("TOTAL_ROOMS_FORMULA", [
    "dashboard.statistics",
    "report.daily",
    "report.monthly",
    "calculation.occupancy",
    "calculation.revpar"
])

analyzer.add_rule("calculation.occupancy", [
    "dashboard.kpi",
    "report.executive"
])

# Query impacts
affected = analyzer.get_affected("TOTAL_ROOMS_FORMULA")
# Returns: All affected reports and calculations
```

### 10.8 Data Dictionary (Auto-Generated)

System knows its own structure via database introspection + manual annotations:

**Auto-Generated from Schema:**
```python
class DataDictionaryGenerator:
    def introspect_table(self, table_name: str) -> dict:
        """Extract metadata from database schema"""
        return {
            "table": table_name,
            "columns": [
                {
                    "name": "room_revenue",
                    "type": "decimal",
                    "nullable": False,
                    "is_aggregatable": True,
                    "allowed_aggregations": ["sum", "avg", "min", "max"]
                },
                # ... auto-extracted from information_schema
            ]
        }
```

**Manual Annotations:**
```python
data_annotations = {
    "reservations.room_revenue": {
        "display_name": "Room Revenue",
        "display_name_id": "Pendapatan Kamar",
        "description": "Total revenue from room charges",
        "unit": "currency",
        "business_context": "USALI Rooms Department",
        "report_category": "Revenue",
        "formula_variable": "room_revenue"
    }
}
```

### 10.9 Visual Report/Formula Builder

**Concept**: Users dapat membuat report dan formula via UI tanpa SQL.

```
┌─────────────────────────────────────────────────────────┐
│ 🔧 Formula Builder                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Available Fields:                   Formula:            │
│ ┌─────────────────────┐            ┌──────────────────┐│
│ │ 📊 Revenue          │            │                  ││
│ │   └─ Room Revenue   │  ═══►      │ [Room Revenue]   ││
│ │   └─ F&B Revenue    │            │       ÷          ││
│ │ 📊 Statistics       │            │ [Available Rooms]││
│ │   └─ Total Rooms    │            │       =          ││
│ │   └─ Available ──────────►       │   [Result]       ││
│ │   └─ Occupied       │            │                  ││
│ └─────────────────────┘            └──────────────────┘│
│                                                         │
│ Operators: [+] [-] [×] [÷] [IF] [ROUND] [SUM]          │
│                                                         │
│ Preview: 150,000,000 ÷ 95 = 1,578,947.37               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Generated Query (hidden from user):**
```sql
SELECT
    ROUND(
        SUM(room_revenue) /
        NULLIF(COUNT(CASE WHEN status != 'OOO' THEN 1 END), 0),
        2
    ) as revpar
FROM daily_statistics
WHERE date BETWEEN :start_date AND :end_date
```

### 10.10 Database Schema

```sql
-- Business Rules Definitions (System + Organization)
CREATE TABLE business_rules (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),            -- Indonesian name
    description TEXT,

    -- Location
    module VARCHAR(50) NOT NULL,     -- 'accounting', 'pms', 'pos'
    page_path VARCHAR(200),          -- '/reports/daily-report'

    -- Rule definition
    rule_type VARCHAR(20) NOT NULL,  -- 'selection', 'formula', 'threshold', 'toggle', 'mapping'
    default_value JSONB NOT NULL,
    allowed_values JSONB,            -- For selection type
    validation_schema JSONB,         -- JSON Schema for validation

    -- Impact tracking
    impacts JSONB,                   -- ['dashboard.stats', 'report.daily']

    -- Metadata
    is_system BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Organization-Specific Rule Values
CREATE TABLE organization_rules (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES business_rules(id) ON DELETE CASCADE,

    value JSONB NOT NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    UNIQUE(organization_id, rule_id)
);

-- Rule Change History
CREATE TABLE rule_change_history (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES business_rules(id) ON DELETE CASCADE,

    old_value JSONB,
    new_value JSONB NOT NULL,
    change_reason TEXT,

    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Data Dictionary (Auto-generated + Annotated)
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),

    source_type VARCHAR(20) NOT NULL, -- 'table', 'view', 'calculated'
    table_name VARCHAR(100),
    module VARCHAR(50) NOT NULL,

    -- Multi-tenancy
    has_organization_id BOOLEAN DEFAULT TRUE,
    organization_column VARCHAR(50) DEFAULT 'organization_id',

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE data_source_columns (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    data_source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,

    -- Capabilities
    is_aggregatable BOOLEAN DEFAULT FALSE,
    allowed_aggregations JSONB,      -- ['sum', 'avg', 'min', 'max', 'count']
    is_filterable BOOLEAN DEFAULT TRUE,
    allowed_operators JSONB,         -- ['=', '!=', '>', '<', 'LIKE', 'IN']
    is_groupable BOOLEAN DEFAULT FALSE,
    is_sortable BOOLEAN DEFAULT TRUE,

    -- Display
    display_format VARCHAR(50),      -- 'currency', 'percentage', 'date', 'number'
    display_decimals INTEGER DEFAULT 2,

    -- References
    reference_source_id INTEGER REFERENCES data_sources(id),
    reference_column VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,

    UNIQUE(data_source_id, code)
);

-- Report Definitions (Configurable by Organization)
CREATE TABLE report_definitions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system template

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),

    report_type VARCHAR(50) NOT NULL,  -- 'balance_sheet', 'income_statement', 'custom'
    module VARCHAR(50) NOT NULL,

    parameters JSONB,                  -- Required input parameters
    layout_config JSONB,               -- Column widths, grouping, etc.

    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE report_fields (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    report_definition_id INTEGER NOT NULL REFERENCES report_definitions(id) ON DELETE CASCADE,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_id VARCHAR(200),

    -- Field source
    field_type VARCHAR(20) NOT NULL,  -- 'data', 'formula', 'config', 'static'
    source_id INTEGER REFERENCES data_sources(id),
    source_column_id INTEGER REFERENCES data_source_columns(id),
    aggregation VARCHAR(20),          -- 'sum', 'avg', 'count', etc.

    -- Formula (if field_type = 'formula')
    formula TEXT,
    formula_fields JSONB,             -- ['field1', 'field2'] - references to other fields

    -- Filtering
    filters JSONB,                    -- Pre-applied filters

    -- Display
    display_format VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT TRUE,

    UNIQUE(report_definition_id, code)
);
```

### 10.11 Tech Stack

**Backend:**
- FastAPI - API framework
- `simpleeval` - Safe formula evaluation
- `networkx` - Dependency graph for impact analysis
- Pydantic - Schema validation
- Redis - Rule caching

**Frontend:**
- Zustand - Rule state management
- TanStack Query - Rule fetching & caching
- React Hook Form - Rule editing forms
- ReactFlow - Impact graph visualization
- Monaco Editor - Formula editing (optional)

### 10.12 Usage Pattern

**Getting a rule value:**
```python
class RuleService:
    def get_rule_value(
        self,
        organization_id: int,
        rule_code: str
    ) -> any:
        """Get rule value for organization, fallback to default"""

        # Check organization override
        org_rule = self.repo.get_organization_rule(organization_id, rule_code)
        if org_rule:
            return org_rule.value

        # Fallback to system default
        rule = self.repo.get_business_rule(rule_code)
        return rule.default_value

# Usage in calculation
rule_service = RuleService(...)

# Get configurable values
include_ooo = rule_service.get_rule_value(org_id, "TOTAL_ROOMS_INCLUDE_OOO")
service_charge_pct = rule_service.get_rule_value(org_id, "SERVICE_CHARGE_PERCENTAGE")

# Use in calculation
if include_ooo:
    total_rooms = all_rooms
else:
    total_rooms = all_rooms - ooo_rooms

service_charge = subtotal * (service_charge_pct / 100)
```

**Updating a rule:**
```python
class RuleUseCase:
    def update_rule(
        self,
        organization_id: int,
        rule_code: str,
        new_value: any,
        user_id: int,
        reason: str
    ) -> None:
        # Validate against schema
        rule = self.repo.get_business_rule(rule_code)
        self._validate_value(new_value, rule.validation_schema)

        # Get current value for history
        current = self.repo.get_organization_rule(organization_id, rule_code)

        # Update or insert
        self.repo.upsert_organization_rule(
            organization_id,
            rule.id,
            new_value,
            user_id
        )

        # Log change
        self.repo.add_change_history(
            organization_id,
            rule.id,
            old_value=current.value if current else rule.default_value,
            new_value=new_value,
            reason=reason,
            user_id=user_id
        )

        # Invalidate cache
        self.cache.invalidate(f"rule:{organization_id}:{rule_code}")
```

---

## Decisions Log

| # | Topic | Decision | Date |
|---|-------|----------|------|
| 1 | CoA Structure | 4-level hierarchy (Category → Subcategory → Type → Account) | 2025-12-07 |
| 2 | CoA Categories | Fixed 5 categories (IFRS: Assets, Liabilities, Equity, Revenue, Expenses) | 2025-12-07 |
| 3 | CoA Numbering | Format `XXXX-XXX-XX` (Type-Sequence-Department) | 2025-12-07 |
| 4 | Sequence Digits | 3 digits (001-999 per type) | 2025-12-07 |
| 5 | Department Codes | USALI standard (RM, FB, FO, HK, etc.) with 2-char codes | 2025-12-07 |
| 6 | Template System | Fixed + Custom (is_system, is_required flags) | 2025-12-07 |
| 7 | Soft Delete | Yes, for all customizable levels (is_deleted flag) | 2025-12-07 |
| 8 | Audit Log | Yes, full tracking for all CoA changes | 2025-12-07 |
| 9 | Multi-Entity | Management Group required (even for single PT) | 2025-12-07 |
| 10 | Default Strategy | `group_std` (Group template + PT customization allowed) | 2025-12-07 |
| 11 | Consolidation | Yes, basic consolidation from Phase 1 | 2025-12-07 |
| 12 | App Integration | 3 modes: master, integrated, standalone | 2025-12-07 |
| 13 | Journal Numbering | Format `TYPE-YYYY-MM-NNNNN` | 2025-12-07 |
| 14 | Journal Approval | Configurable per organization | 2025-12-07 |
| 15 | Auto-Journal Approval | Configurable per journal type | 2025-12-07 |
| 16 | Sequence Reset | Per month | 2025-12-07 |
| 17 | Functional Currency | Configurable per PT | 2025-12-07 |
| 18 | Unrealized Forex | Configurable (P&L atau OCI) | 2025-12-07 |
| 19 | Exchange Rate Source | Manual + template import (Phase 1) | 2025-12-07 |
| 20 | Forex Revaluation | On-demand only | 2025-12-07 |
| 21 | Multi-Currency Impl | Phase 2 (schema ready, fitur nanti) | 2025-12-07 |
| 22 | Business Rules Engine | Hard vs Soft rules separation | 2025-12-07 |
| 23 | Hard Rules | Embedded in code (double-entry, data integrity, security) | 2025-12-07 |
| 24 | Soft Rules | Configurable via UI (tax rates, formulas, thresholds) | 2025-12-07 |
| 25 | Config Panel | Per-page config with impact analysis & change history | 2025-12-07 |
| 26 | Formula Engine | Safe evaluation using `simpleeval` library | 2025-12-07 |
| 27 | Impact Analysis | Dependency graph using `networkx` | 2025-12-07 |
| 28 | Data Dictionary | Auto-generated from schema + manual annotations | 2025-12-07 |
| 29 | Report Builder | Visual formula/report builder (no SQL for users) | 2025-12-07 |
| 30 | Tax Rates | Soft rule - configurable via Config Panel | 2025-12-07 |
| 31 | Tax Calculation | Soft rule - Inclusive/Exclusive configurable | 2025-12-07 |
| 32 | Tax Rounding | Soft rule - round/round_down/round_up/round_100 | 2025-12-07 |
| 33 | Tax Due Dates | Hard rule - embedded per law (20th monthly) | 2025-12-07 |
| 34 | E-Faktur Format | Hard rule - DJP format mandatory | 2025-12-07 |
| 35 | PPh 21 TER Table | Soft rule - importable/updatable | 2025-12-07 |
| 36 | Tax Account Mapping | Soft rule - configurable per transaction type | 2025-12-07 |
| 37 | Fiscal Year Start | Soft rule - configurable (default January) | 2025-12-07 |
| 38 | Period Structure | Hard rule - 12 months + 1 adjustment period | 2025-12-07 |
| 39 | Period Status Flow | Hard rule - OPEN → SOFT_CLOSED → CLOSED → LOCKED | 2025-12-07 |
| 40 | Period Immutability | Hard rule - closed period cannot reopen | 2025-12-07 |
| 41 | Grace Period | Soft rule - configurable days after period end | 2025-12-07 |
| 42 | Closing Checklist | Soft rule - configurable items per organization | 2025-12-07 |
| 43 | Year-End Closing | Hard rule - auto-generate closing journals | 2025-12-07 |
| 44 | Closing Accounts | Soft rule - configurable retained earnings & income summary | 2025-12-07 |
| 45 | Report Templates | Dual system: PSAK (statutory) + USALI (operational) | 2025-12-07 |
| 46 | Report Line Mapping | Soft rule - configurable via Config Panel | 2025-12-07 |
| 47 | Comparative Periods | Soft rule - flexible selection (multi-period) | 2025-12-07 |
| 48 | Bank Reconciliation | Dual mode: Manual + Semi-auto (user pilih) | 2025-12-07 |
| 49 | Bank Integration | Semi-manual - import file (no API) | 2025-12-07 |
| 50 | Multi-Bank | Unlimited bank accounts, multi-currency | 2025-12-07 |
| 51 | Petty Cash Type | Soft rule - configurable per kas (imprest/fluctuating) | 2025-12-07 |
| 52 | Petty Cash Controls | Soft rule - max transaction, approval threshold | 2025-12-07 |
| 53 | Guest vs City Ledger | Separated: Guest Ledger (PMS) + City Ledger (AR) | 2025-12-07 |
| 54 | AR/AP Aging Buckets | Fixed: Current, 1-30, 31-60, 61-90, >90 days | 2025-12-07 |
| 55 | Credit Limit | Soft rule - per customer, hard/soft + configurable amount | 2025-12-07 |
| 56 | Payment Terms | Template + custom terms | 2025-12-07 |
| 57 | AP Approval Workflow | Soft rule - configurable by amount | 2025-12-07 |

---

*Document ini akan di-update seiring pembahasan setiap section.*
