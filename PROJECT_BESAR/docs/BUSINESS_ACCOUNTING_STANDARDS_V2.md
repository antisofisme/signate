# Business & Accounting Standards V2

> Lanjutan dari BUSINESS_ACCOUNTING_STANDARDS.md
>
> **Last Updated**: 2025-12-07
> **Status**: ✅ Completed

---

## Table of Contents

10. [Integration with Other Modules](#10-integration-with-other-modules) ✅
11. [Audit Trail & Compliance](#11-audit-trail--compliance) ✅
12. [Fixed Assets](#12-fixed-assets) ✅
13. [Inventory Costing](#13-inventory-costing) ✅
14. [Budgeting](#14-budgeting) ✅
15. [Consolidation](#15-consolidation) ✅

---

## 10. Integration with Other Modules

> **Status**: ✅ Approved (2025-12-07)

### 10.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Journal Balance Check | ✅ (Debit = Credit) | ❌ |
| Integration Mode | ✅ (Real-time) | ❌ |
| Auto-Post Behavior | ❌ | ✅ (per journal type) |
| GL Mapping | ❌ | ✅ (per transaction type) |
| Source Document Link | ✅ (mandatory) | ❌ |

### 10.2 Integration Architecture

**Real-time Integration Flow:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    PMS      │     │  Accounting │     │   General   │
│  POS, etc   │ ──► │   Service   │ ──► │   Ledger    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   Transaction         Validate            Journal
   Created             & Map GL            Entry
```

**Event-Driven Pattern:**

```python
# Source module publishes event
event = TransactionEvent(
    source="pms",
    type="room_charge",
    transaction_id=12345,
    data={
        "room_number": "101",
        "guest_name": "John Smith",
        "amount": 1500000,
        "tax_amount": 180000,
        "department": "RM"
    }
)

# Accounting service subscribes and creates journal
journal = JournalEntry(
    source_type="pms",
    source_id=12345,
    entries=[
        {"account": "1103-001", "debit": 1680000},  # AR - Guest
        {"account": "4101-001-RM", "credit": 1500000},  # Room Revenue
        {"account": "2103-001", "credit": 180000}  # PPN Keluaran
    ]
)
```

### 10.3 Module Integration Points

#### 10.3.1 PMS → Accounting

| PMS Transaction | Journal Type | Debit | Credit |
|-----------------|--------------|-------|--------|
| Room Charge | SJ | AR - Guest Ledger | Room Revenue + Tax |
| F&B Charge (room) | SJ | AR - Guest Ledger | F&B Revenue + Tax |
| Guest Payment | CR | Cash/Bank | AR - Guest Ledger |
| City Ledger Transfer | GJ | AR - City Ledger | AR - Guest Ledger |
| Deposit Received | CR | Cash/Bank | Guest Deposit (Liability) |
| Deposit Applied | GJ | Guest Deposit | AR - Guest Ledger |

#### 10.3.2 POS → Accounting

| POS Transaction | Journal Type | Debit | Credit |
|-----------------|--------------|-------|--------|
| Cash Sale | SJ | Cash | Revenue + Tax |
| Card Sale | SJ | AR - Card | Revenue + Tax |
| Room Charge | SJ | AR - Guest Ledger | Revenue + Tax |
| Void | SJ (Reverse) | Revenue + Tax | Cash/AR |
| Settlement | CR | Bank | AR - Card |

#### 10.3.3 Inventory → Accounting

| Inventory Transaction | Journal Type | Debit | Credit |
|-----------------------|--------------|-------|--------|
| Purchase Receipt | PJ | Inventory | AP |
| Issue to Department | IV | COGS/Expense | Inventory |
| Adjustment (Shrinkage) | IV | Inventory Loss | Inventory |
| Transfer Between Locations | IV | Inv - Dest | Inv - Source |

#### 10.3.4 Payroll → Accounting

| Payroll Transaction | Journal Type | Debit | Credit |
|--------------------|--------------|-------|--------|
| Salary Expense | PY | Salary Expense (by dept) | PPh 21 Payable + Bank |
| BPJS Expense | PY | BPJS Expense | BPJS Payable |
| Bonus/THR | PY | Bonus Expense | PPh 21 Payable + Bank |

### 10.4 GL Mapping Configuration (Soft)

**Configurable per Transaction Type:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ GL Mapping - PMS Transactions                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Transaction Type: Room Charge                           │
│ ──────────────────────────────────────────────────────  │
│                                                         │
│ Debit Account:                                          │
│ [1103-001 - AR Guest Ledger ▼]                          │
│                                                         │
│ Credit Accounts:                                        │
│ ├── Revenue: [4101-001-RM - Room Revenue ▼]             │
│ └── Tax: [2103-001 - PPN Keluaran ▼]                    │
│                                                         │
│ Department Mapping:                                     │
│ ● Use source department code                            │
│ ○ Fixed department: [________]                          │
│                                                         │
│ [Save Mapping]                                          │
└─────────────────────────────────────────────────────────┘
```

### 10.5 Auto-Post Configuration (Soft)

**Configurable per Journal Type:**

```json
{
  "rule_code": "INTEGRATION_AUTO_POST",
  "rule_type": "mapping",
  "default_value": {
    "SJ": {"auto_post": true, "require_approval": false},
    "PJ": {"auto_post": false, "require_approval": true},
    "CR": {"auto_post": true, "require_approval": false},
    "CD": {"auto_post": false, "require_approval": true},
    "PY": {"auto_post": false, "require_approval": true},
    "IV": {"auto_post": true, "require_approval": false}
  }
}
```

**Config Panel:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Integration Auto-Post Settings                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Journal Type          │ Auto-Post │ Require Approval    │
│ ──────────────────────┼───────────┼──────────────────── │
│ SJ - Sales Journal    │ [✓]       │ [ ]                 │
│ PJ - Purchase Journal │ [ ]       │ [✓]                 │
│ CR - Cash Receipt     │ [✓]       │ [ ]                 │
│ CD - Cash Disbursement│ [ ]       │ [✓]                 │
│ PY - Payroll Journal  │ [ ]       │ [✓]                 │
│ IV - Inventory Journal│ [✓]       │ [ ]                 │
│                                                         │
│ [Save Settings]                                         │
└─────────────────────────────────────────────────────────┘
```

### 10.6 Error Handling

**Failed Integration Journal:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Integration Errors                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 3 transactions failed to create journal                 │
│                                                         │
│ [!] PMS-12345  Room Charge  05-Dec 10:30               │
│     Error: GL Account 4101-999 not found                │
│     [Retry] [Map Account] [Skip]                        │
│                                                         │
│ [!] POS-5678   Cash Sale    05-Dec 11:45               │
│     Error: Department code 'XX' not configured          │
│     [Retry] [Configure Dept] [Skip]                     │
│                                                         │
│ [!] INV-9999   Stock Issue  05-Dec 14:00               │
│     Error: Insufficient inventory balance               │
│     [Retry] [Adjust Inventory] [Skip]                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 10.7 Database Schema

```sql
-- Integration Mappings
CREATE TABLE integration_mappings (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    source_module VARCHAR(20) NOT NULL,     -- 'pms', 'pos', 'inventory', 'payroll'
    transaction_type VARCHAR(50) NOT NULL,  -- 'room_charge', 'cash_sale', etc.

    -- GL Mapping
    debit_account_id INTEGER REFERENCES coa_accounts(id),
    credit_account_id INTEGER REFERENCES coa_accounts(id),
    tax_account_id INTEGER REFERENCES coa_accounts(id),

    -- Department handling
    use_source_department BOOLEAN DEFAULT TRUE,
    fixed_department_id INTEGER REFERENCES departments(id),

    -- Journal settings
    journal_type VARCHAR(10) NOT NULL,
    auto_post BOOLEAN DEFAULT FALSE,
    require_approval BOOLEAN DEFAULT FALSE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(organization_id, source_module, transaction_type)
);

-- Integration Queue (for failed/pending journals)
CREATE TABLE integration_queue (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    source_module VARCHAR(20) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_data JSONB NOT NULL,

    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'processing', 'completed', 'failed', 'skipped'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(source_module, source_id)
);

CREATE INDEX idx_integration_queue_status ON integration_queue(organization_id, status);
```

---

## 11. Audit Trail & Compliance

> **Status**: ✅ Approved (2025-12-07)

### 11.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Audit Trail Enabled | ✅ (always on) | ❌ |
| Log Level | ❌ | ✅ (all tables by default) |
| Retention Period | ❌ | ✅ (configurable) |
| Posted Journal Immutability | ✅ | ❌ |
| User Action Logging | ✅ | ❌ |

### 11.2 Audit Trail Scope

**Everything is Logged:**

| Category | Tables | What's Logged |
|----------|--------|---------------|
| **Transactions** | journals, invoices, payments | All CRUD + status changes |
| **Master Data** | customers, vendors, accounts | All CRUD |
| **Configuration** | business_rules, mappings | All changes |
| **Security** | users, roles, permissions | All changes + login/logout |
| **System** | period closing, year-end | All actions |

### 11.3 Audit Log Structure

**For Every Change:**

```json
{
  "id": 123456,
  "timestamp": "2025-12-07T10:30:45.123Z",
  "organization_id": 1,

  "table_name": "ar_invoices",
  "record_id": 5678,
  "action": "UPDATE",

  "old_values": {
    "status": "draft",
    "total_amount": 10000000
  },
  "new_values": {
    "status": "open",
    "total_amount": 11000000
  },
  "changed_fields": ["status", "total_amount"],

  "user_id": 42,
  "user_name": "john.doe",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",

  "context": {
    "module": "ar",
    "action": "approve_invoice",
    "reason": "Customer confirmed order"
  }
}
```

### 11.4 Transaction Immutability (Hard)

**Posted Journals Cannot Be Changed:**

```
Journal JNL-2025-12-00001 (POSTED)
├── Status: POSTED ✅
├── Posted at: 2025-12-05 14:30
├── Posted by: Finance Manager
│
└── Actions Available:
    ├── [View] ✅
    ├── [Print] ✅
    ├── [Edit] ❌ BLOCKED
    ├── [Delete] ❌ BLOCKED
    └── [Void] ✅ (creates reversing entry)
```

**Void Process:**
1. User requests void with reason
2. Approval required (if configured)
3. System creates reversing entry
4. Original marked as VOIDED
5. Both linked for audit trail

### 11.5 User Action Logging

**All User Actions Tracked:**

| Action Type | Example |
|-------------|---------|
| Authentication | Login, Logout, Failed login |
| Data View | View invoice, Export report |
| Data Change | Create, Update, Delete |
| Approval | Approve, Reject |
| System Action | Period close, Year-end |
| Config Change | Update business rule |

**Login History:**

```
┌─────────────────────────────────────────────────────────┐
│ 👤 User Activity - john.doe@company.com                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Recent Logins:                                          │
│ ├── 07-Dec 08:30  ✅ Success  192.168.1.100  Chrome     │
│ ├── 06-Dec 17:45  ✅ Success  192.168.1.100  Chrome     │
│ ├── 06-Dec 08:25  ❌ Failed   203.0.113.50   Unknown    │
│ └── 05-Dec 09:00  ✅ Success  192.168.1.100  Chrome     │
│                                                         │
│ Recent Actions:                                         │
│ ├── 07-Dec 10:30  Approved Invoice INV-2025-001         │
│ ├── 07-Dec 10:15  Created Payment PAY-2025-050          │
│ ├── 07-Dec 09:45  Updated Customer CUST-001             │
│ └── 07-Dec 09:30  Exported AR Aging Report              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 11.6 Compliance Features

**SOX/Financial Controls:**

| Control | Implementation |
|---------|----------------|
| Segregation of Duties | Role-based, no user can approve own transactions |
| Approval Workflows | Configurable by amount/type |
| Period Controls | Lock periods after closing |
| Access Controls | Permission-based, audit logged |
| Data Retention | Configurable, minimum 5 years |

**Regulatory Compliance:**

| Regulation | Features |
|------------|----------|
| **Tax (DJP)** | E-Faktur integration, tax reporting |
| **PSAK** | Standard financial reports |
| **OJK** | If applicable, regulatory reports |

### 11.7 Audit Trail Viewer

```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Audit Trail Viewer                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Filters:                                                │
│ Date: [01-Dec-2025] to [07-Dec-2025]                    │
│ Table: [All Tables ▼]                                   │
│ User: [All Users ▼]                                     │
│ Action: [All Actions ▼]                                 │
│                                                         │
│ Results: 1,234 records                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Time       │ User    │ Table    │ Action │ Record  │ │
│ ├────────────┼─────────┼──────────┼────────┼─────────┤ │
│ │ 10:30:45   │ john    │ ar_inv   │ UPDATE │ INV-001 │ │
│ │ 10:28:12   │ mary    │ ap_pay   │ CREATE │ PAY-050 │ │
│ │ 10:25:00   │ admin   │ bus_rule │ UPDATE │ TAX_PPN │ │
│ │ 10:20:33   │ john    │ customer │ UPDATE │ CUST-01 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Export CSV] [Export PDF]                               │
└─────────────────────────────────────────────────────────┘
```

### 11.8 Data Retention (Soft)

**Configurable Retention:**

```json
{
  "rule_code": "AUDIT_RETENTION_POLICY",
  "rule_type": "mapping",
  "default_value": {
    "transaction_logs": {"years": 7, "archive_after": 2},
    "access_logs": {"years": 5, "archive_after": 1},
    "config_logs": {"years": 10, "archive_after": 5},
    "security_logs": {"years": 7, "archive_after": 2}
  }
}
```

### 11.9 Database Schema

```sql
-- Comprehensive Audit Log
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Who
    organization_id INTEGER REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),
    user_name VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),

    -- What
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(20) NOT NULL,            -- 'INSERT', 'UPDATE', 'DELETE', 'VIEW', 'EXPORT'

    -- Changes
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- Context
    module VARCHAR(50),
    action_name VARCHAR(100),
    reason TEXT,
    metadata JSONB
);

-- Partitioned by month for performance
-- CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs
--     FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE INDEX idx_audit_logs_org_time ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);

-- User Sessions
CREATE TABLE user_sessions (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expired_at TIMESTAMP WITH TIME ZONE,

    is_active BOOLEAN DEFAULT TRUE
);

-- Login History
CREATE TABLE login_history (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    user_id INTEGER REFERENCES users(id),
    username VARCHAR(100) NOT NULL,

    login_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,

    status VARCHAR(20) NOT NULL,            -- 'success', 'failed', 'locked'
    failure_reason VARCHAR(100),

    session_id VARCHAR(100)
);

CREATE INDEX idx_login_history_user ON login_history(user_id, login_at DESC);
CREATE INDEX idx_login_history_ip ON login_history(ip_address, login_at DESC);
```

---

## 12. Fixed Assets

> **Status**: ✅ Approved (2025-12-07)

### 12.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Double-entry for FA transactions | ✅ | ❌ |
| Depreciation calculation accuracy | ✅ | ❌ |
| Disposal approval workflow | ✅ | ❌ |
| Depreciation method | ❌ | ✅ (per asset) |
| Asset categories | ✅ (fixed fiskal) | ❌ |
| Revaluation policy | ❌ | ✅ (frequency) |
| Useful life | ❌ | ✅ (per asset/category) |

### 12.2 Depreciation Methods (Soft)

**All Methods Available - User Selects per Asset:**

| Method | Formula | Use Case |
|--------|---------|----------|
| **Straight Line (SL)** | (Cost - Salvage) / Useful Life | Most common, equal annual depreciation |
| **Declining Balance (DB)** | Book Value × Rate | Assets depreciate faster early |
| **Sum of Years Digits (SYD)** | (Remaining Life / SYD) × Depreciable Amount | Accelerated depreciation |
| **Units of Production (UOP)** | (Cost - Salvage) × (Units Used / Total Units) | Based on actual usage |

**Configuration per Asset:**

```
┌─────────────────────────────────────────────────────────┐
│ 🏭 Asset Registration                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Asset Code: FA-2025-00123                               │
│ Name: Toyota Avanza - B 1234 XYZ                        │
│                                                         │
│ Category: [Kendaraan ▼]                                 │
│ Acquisition Date: [15-Jan-2025]                         │
│ Acquisition Cost: [Rp 250,000,000]                      │
│                                                         │
│ ─────── Depreciation Settings ───────                   │
│                                                         │
│ Method: [Declining Balance ▼]                           │
│   ○ Straight Line                                       │
│   ● Declining Balance                                   │
│   ○ Sum of Years Digits                                 │
│   ○ Units of Production                                 │
│                                                         │
│ Useful Life: [8] years (from fiscal category)           │
│ Salvage Value: [Rp 25,000,000] (10%)                    │
│ DB Rate: [25%] (calculated from useful life)            │
│                                                         │
│ [Calculate Preview] [Save Asset]                        │
└─────────────────────────────────────────────────────────┘
```

### 12.3 Asset Categories (Hard - Fiskal)

**Fixed Categories per PMK No. 96/PMK.03/2009:**

| Group | Category | Useful Life (Tax) | Useful Life (Book) | Rate (SL) | Rate (DB) |
|-------|----------|-------------------|--------------------|-----------| ----------|
| **I** | Bukan Bangunan - Kelompok 1 | 4 years | Configurable | 25% | 50% |
| **II** | Bukan Bangunan - Kelompok 2 | 8 years | Configurable | 12.5% | 25% |
| **III** | Bukan Bangunan - Kelompok 3 | 16 years | Configurable | 6.25% | 12.5% |
| **IV** | Bukan Bangunan - Kelompok 4 | 20 years | Configurable | 5% | 10% |
| **V** | Bangunan Permanen | 20 years | Configurable | 5% | - |
| **VI** | Bangunan Tidak Permanen | 10 years | Configurable | 10% | - |

**Sub-Categories (for Hotel Industry):**

```
Kelompok 1 (4 tahun):
├── Komputer & Peripherals
├── Peralatan Komunikasi
├── Peralatan Dapur Kecil
└── Peralatan Kantor

Kelompok 2 (8 tahun):
├── Kendaraan (Mobil, Motor)
├── Furniture & Fixtures
├── Peralatan Dapur Besar
├── Laundry Equipment
└── AC & Refrigeration

Kelompok 3 (16 tahun):
├── Heavy Equipment
├── Lift & Escalator
└── Sistem CCTV & Security

Kelompok 4 (20 tahun):
├── Generator & Power Systems
├── Water Treatment Plant
└── Swimming Pool Equipment

Bangunan (20/10 tahun):
├── Main Building
├── Annexes
├── Parking Structure
└── Temporary Structures
```

### 12.4 Asset Lifecycle & Disposal (Full Workflow)

**Asset Lifecycle Flow:**

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Acquire  │───►│  Active  │───►│ Dispose  │───►│ Disposed │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
  Register      Depreciate      Full Workflow    Archive
  & Capitalize  Monthly         with Approval    & Journal
```

**Disposal Workflow (Full Lifecycle):**

```
┌─────────────────────────────────────────────────────────┐
│ 📋 Asset Disposal Workflow                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: PROPOSE                                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Asset: FA-2025-00123 - Toyota Avanza            │    │
│  │ Book Value: Rp 150,000,000                      │    │
│  │                                                 │    │
│  │ Disposal Type: [Sale ▼]                         │    │
│  │   ○ Sale (sold to third party)                  │    │
│  │   ○ Trade-In (exchange for new asset)           │    │
│  │   ○ Scrap (no value, write-off)                 │    │
│  │   ○ Donation                                    │    │
│  │   ○ Loss (theft, disaster)                      │    │
│  │                                                 │    │
│  │ Proposed Sale Price: [Rp 120,000,000]           │    │
│  │ Reason: [Vehicle replacement program 2025]      │    │
│  │                                                 │    │
│  │ Attachments:                                    │    │
│  │ [+ Vehicle Condition Report]                    │    │
│  │ [+ Price Quotation from Dealer]                 │    │
│  │                                                 │    │
│  │ [Submit for Approval]                           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Step 2: APPROVE                                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🔔 Pending Approval (2)                         │    │
│  │                                                 │    │
│  │ ▸ FA-2025-00123 - Sale Rp 120,000,000          │    │
│  │   Proposed by: John (05-Dec 10:30)              │    │
│  │   Book Value: Rp 150,000,000                    │    │
│  │   Loss on Disposal: Rp 30,000,000               │    │
│  │                                                 │    │
│  │   [Approve] [Reject] [Request Revision]         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Step 3: EXECUTE                                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ✅ Approved - Ready to Execute                  │    │
│  │                                                 │    │
│  │ Actual Sale Date: [07-Dec-2025]                 │    │
│  │ Actual Sale Price: [Rp 120,000,000]             │    │
│  │ Buyer: [PT ABC Motor]                           │    │
│  │ Invoice No: [INV-ABC-2025-123]                  │    │
│  │                                                 │    │
│  │ [Execute Disposal]                              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Step 4: POST                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 📒 Journal Entry Created                        │    │
│  │                                                 │    │
│  │ JNL-2025-12-00050 (FA Disposal)                 │    │
│  │                                                 │    │
│  │ Account              │ Debit         │ Credit   │    │
│  │ ─────────────────────┼───────────────┼───────── │    │
│  │ Cash/Bank            │ 120,000,000   │          │    │
│  │ Accum Depr - Vehicle │ 100,000,000   │          │    │
│  │ Loss on Disposal     │  30,000,000   │          │    │
│  │ Fixed Asset - Vehicle│               │250,000,000│   │
│  │                      │ 250,000,000   │250,000,000│   │
│  │                                                 │    │
│  │ Status: POSTED ✅                               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 12.5 Revaluation (PSAK 16 Compliant)

**Mandatory Periodic Revaluation:**

| Setting | Hard Rule | Soft Rule |
|---------|-----------|-----------|
| Revaluation allowed | ✅ (PSAK 16) | ❌ |
| Revaluation frequency | ❌ | ✅ (1/3/5 years) |
| Surplus handling | ✅ (to OCI) | ❌ |
| Deficit handling | ✅ (to P&L or OCI) | ❌ |
| Appraiser requirement | ❌ | ✅ (external/internal) |

**Revaluation Process:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Asset Revaluation                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Revaluation Date: [31-Dec-2025]                         │
│ Category: [Bangunan Permanen]                           │
│                                                         │
│ Assets to Revalue:                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Asset         │ Book Value    │ Fair Value   │ Diff │ │
│ ├───────────────┼───────────────┼──────────────┼──────┤ │
│ │ Main Building │ 50,000,000,000│55,000,000,000│+10%  │ │
│ │ Parking       │  5,000,000,000│ 4,500,000,000│-10%  │ │
│ │ Pool Area     │  2,000,000,000│ 2,500,000,000│+25%  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Appraiser: [KJPP ABC & Partners]                        │
│ Report No: [APR-2025-12-001]                            │
│ Report Date: [15-Dec-2025]                              │
│                                                         │
│ [Upload Appraisal Report]                               │
│                                                         │
│ Summary:                                                │
│ ├── Total Revaluation Surplus: Rp 5,500,000,000         │
│ ├── Total Revaluation Deficit: Rp   500,000,000         │
│ └── Net Surplus (to OCI): Rp 5,000,000,000              │
│                                                         │
│ [Process Revaluation]                                   │
└─────────────────────────────────────────────────────────┘
```

**Revaluation Journal:**

```
JNL-2025-12-00100 (Revaluation Surplus)

Account                          │ Debit           │ Credit
─────────────────────────────────┼─────────────────┼────────────────
Fixed Asset - Building           │ 5,500,000,000   │
Accumulated Depr - Building      │                 │ 500,000,000
Revaluation Surplus (OCI)        │                 │ 5,000,000,000
                                 │ 5,500,000,000   │ 5,500,000,000
```

### 12.6 Monthly Depreciation Run

**Automated Monthly Process:**

```
┌─────────────────────────────────────────────────────────┐
│ 📅 Monthly Depreciation Run                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Period: December 2025                                   │
│ Run Date: [31-Dec-2025]                                 │
│                                                         │
│ Assets Summary:                                         │
│ ├── Total Active Assets: 450                            │
│ ├── Total Asset Value: Rp 150,000,000,000               │
│ ├── This Month Depreciation: Rp 1,250,000,000           │
│ └── Accumulated Depreciation: Rp 45,000,000,000         │
│                                                         │
│ By Category:                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Category       │ Assets │ This Month    │ YTD       │ │
│ ├────────────────┼────────┼───────────────┼───────────┤ │
│ │ Bangunan       │ 5      │ 500,000,000   │ 6B        │ │
│ │ Kendaraan      │ 25     │ 150,000,000   │ 1.8B      │ │
│ │ Peralatan      │ 200    │ 400,000,000   │ 4.8B      │ │
│ │ Furniture      │ 220    │ 200,000,000   │ 2.4B      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Preview Journal] [Run Depreciation]                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 12.7 Database Schema

```sql
-- Asset Categories (Fixed - Fiscal)
CREATE TABLE asset_categories (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    code VARCHAR(10) NOT NULL UNIQUE,           -- 'K1', 'K2', 'K3', 'K4', 'BP', 'BTP'
    name VARCHAR(100) NOT NULL,                 -- 'Kelompok 1', 'Bangunan Permanen'

    fiscal_life_years INTEGER NOT NULL,         -- 4, 8, 16, 20
    sl_rate DECIMAL(5,2) NOT NULL,              -- 25, 12.5, 6.25, 5
    db_rate DECIMAL(5,2),                       -- 50, 25, 12.5, 10 (NULL for buildings)

    is_building BOOLEAN DEFAULT FALSE,

    -- GL Accounts
    asset_account_id INTEGER REFERENCES coa_accounts(id),
    depreciation_account_id INTEGER REFERENCES coa_accounts(id),
    accumulated_depr_account_id INTEGER REFERENCES coa_accounts(id),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Asset Sub-Categories
CREATE TABLE asset_subcategories (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    category_id INTEGER NOT NULL REFERENCES asset_categories(id),

    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Override book life (soft rule)
    default_book_life_years INTEGER,
    default_salvage_percentage DECIMAL(5,2) DEFAULT 10,

    UNIQUE(category_id, code)
);

-- Fixed Assets Register
CREATE TABLE fixed_assets (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Identification
    asset_code VARCHAR(30) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    serial_number VARCHAR(100),

    -- Classification
    category_id INTEGER NOT NULL REFERENCES asset_categories(id),
    subcategory_id INTEGER REFERENCES asset_subcategories(id),
    department_id INTEGER REFERENCES departments(id),
    location VARCHAR(200),

    -- Acquisition
    acquisition_date DATE NOT NULL,
    acquisition_cost DECIMAL(18,2) NOT NULL,
    acquisition_type VARCHAR(20) NOT NULL,      -- 'purchase', 'donation', 'transfer', 'construction'
    supplier_id INTEGER REFERENCES vendors(id),
    po_number VARCHAR(50),
    invoice_number VARCHAR(50),

    -- Depreciation Settings
    depreciation_method VARCHAR(10) NOT NULL,   -- 'SL', 'DB', 'SYD', 'UOP'
    useful_life_years INTEGER NOT NULL,
    useful_life_units INTEGER,                  -- For Units of Production
    salvage_value DECIMAL(18,2) DEFAULT 0,
    depreciation_start_date DATE NOT NULL,

    -- Current Values
    current_book_value DECIMAL(18,2) NOT NULL,
    accumulated_depreciation DECIMAL(18,2) DEFAULT 0,
    last_depreciation_date DATE,

    -- Revaluation
    is_revalued BOOLEAN DEFAULT FALSE,
    revalued_amount DECIMAL(18,2),
    last_revaluation_date DATE,
    revaluation_surplus DECIMAL(18,2) DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'active',        -- 'active', 'disposed', 'fully_depreciated', 'under_maintenance'
    disposed_date DATE,
    disposal_type VARCHAR(20),                  -- 'sale', 'trade_in', 'scrap', 'donation', 'loss'
    disposal_amount DECIMAL(18,2),
    disposal_journal_id INTEGER REFERENCES journal_entries(id),

    -- Audit
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by_id INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(organization_id, asset_code)
);

-- Depreciation History
CREATE TABLE depreciation_history (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    asset_id INTEGER NOT NULL REFERENCES fixed_assets(id) ON DELETE CASCADE,

    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,

    depreciation_amount DECIMAL(18,2) NOT NULL,
    accumulated_total DECIMAL(18,2) NOT NULL,
    book_value_after DECIMAL(18,2) NOT NULL,

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(asset_id, period_year, period_month)
);

-- Asset Disposal Workflow
CREATE TABLE asset_disposals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES fixed_assets(id),

    -- Proposal
    disposal_type VARCHAR(20) NOT NULL,
    proposed_amount DECIMAL(18,2),
    reason TEXT NOT NULL,

    -- Values at proposal time
    book_value_at_proposal DECIMAL(18,2) NOT NULL,
    accumulated_depr_at_proposal DECIMAL(18,2) NOT NULL,

    -- Workflow Status
    status VARCHAR(20) DEFAULT 'proposed',      -- 'proposed', 'approved', 'rejected', 'executed', 'posted'

    proposed_by_id INTEGER REFERENCES users(id),
    proposed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,

    -- Execution
    actual_disposal_date DATE,
    actual_amount DECIMAL(18,2),
    buyer_name VARCHAR(200),
    buyer_invoice VARCHAR(50),

    executed_by_id INTEGER REFERENCES users(id),
    executed_at TIMESTAMP WITH TIME ZONE,

    -- Journal
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    gain_loss_amount DECIMAL(18,2),

    -- Documentation
    attachments JSONB                           -- [{filename, url, type}]
);

-- Asset Revaluations
CREATE TABLE asset_revaluations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    revaluation_date DATE NOT NULL,
    category_id INTEGER REFERENCES asset_categories(id),  -- NULL = all categories

    appraiser_type VARCHAR(20) NOT NULL,        -- 'external', 'internal'
    appraiser_name VARCHAR(200),
    report_number VARCHAR(50),
    report_date DATE,

    -- Summary
    total_assets INTEGER,
    total_surplus DECIMAL(18,2),
    total_deficit DECIMAL(18,2),
    net_adjustment DECIMAL(18,2),

    status VARCHAR(20) DEFAULT 'draft',         -- 'draft', 'approved', 'posted'

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Revaluation Details
CREATE TABLE revaluation_details (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    revaluation_id INTEGER NOT NULL REFERENCES asset_revaluations(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES fixed_assets(id),

    book_value_before DECIMAL(18,2) NOT NULL,
    fair_value DECIMAL(18,2) NOT NULL,
    adjustment_amount DECIMAL(18,2) NOT NULL,

    is_surplus BOOLEAN NOT NULL
);

-- Indexes
CREATE INDEX idx_fixed_assets_org ON fixed_assets(organization_id);
CREATE INDEX idx_fixed_assets_status ON fixed_assets(organization_id, status);
CREATE INDEX idx_fixed_assets_category ON fixed_assets(category_id);
CREATE INDEX idx_depreciation_period ON depreciation_history(period_year, period_month);
CREATE INDEX idx_asset_disposals_status ON asset_disposals(organization_id, status);
```

### 12.8 Business Rules Configuration

**Soft Rules for Fixed Assets:**

```json
{
  "rule_code": "FA_DEPRECIATION_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "default_method": "SL",
    "allow_method_change": false,
    "auto_run_monthly": true,
    "run_day": 28,
    "require_approval_above": 100000000
  }
},
{
  "rule_code": "FA_REVALUATION_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "frequency_years": 3,
    "require_external_appraiser": true,
    "min_appraiser_certification": "KJPP",
    "auto_adjust_depreciation": true
  }
},
{
  "rule_code": "FA_DISPOSAL_APPROVAL",
  "rule_type": "threshold",
  "default_value": {
    "under_10m": {"approval_level": 1},
    "10m_to_100m": {"approval_level": 2},
    "above_100m": {"approval_level": 3}
  }
}
```

---

## 13. Inventory Costing

> **Status**: ✅ Approved (2025-12-07)

### 13.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Inventory valuation accuracy | ✅ | ❌ |
| COGS calculation | ✅ | ❌ |
| Stock balance integrity | ✅ (no negative) | ❌ |
| Costing method | ❌ | ✅ (per item) |
| Valuation type | ❌ | ✅ (perpetual/periodic) |
| Warehouse structure | ❌ | ✅ (configurable) |
| Count frequency | ❌ | ✅ (annual/cycle) |

### 13.2 Costing Methods (Soft)

**All Methods Available - Configurable per Item:**

| Method | Formula | Use Case |
|--------|---------|----------|
| **FIFO** | First In, First Out | Perishables, F&B ingredients |
| **LIFO** | Last In, First Out | Inflation hedge (rarely used) |
| **Weighted Average** | Total Cost / Total Qty | General supplies, consumables |
| **Specific Identification** | Actual cost per unit | High-value items, serialized |

**Method Selection per Item:**

```
┌─────────────────────────────────────────────────────────┐
│ 📦 Item Master - Costing Settings                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Item Code: INV-001                                      │
│ Name: Beef Tenderloin (per kg)                          │
│ Category: [Food - Meat ▼]                               │
│                                                         │
│ ─────── Costing Settings ───────                        │
│                                                         │
│ Costing Method: [FIFO ▼]                                │
│   ● FIFO (recommended for perishables)                  │
│   ○ LIFO                                                │
│   ○ Weighted Average                                    │
│   ○ Specific Identification                             │
│                                                         │
│ Valuation Type: [Perpetual ▼]                           │
│   ● Perpetual (update setiap transaksi)                 │
│   ○ Periodic (update akhir periode)                     │
│                                                         │
│ Current Cost: Rp 250,000 /kg                            │
│ Last Purchase: Rp 255,000 /kg (05-Dec-2025)             │
│                                                         │
│ [Save Settings]                                         │
└─────────────────────────────────────────────────────────┘
```

### 13.3 Valuation Types (Hybrid)

**Perpetual vs Periodic:**

| Aspect | Perpetual | Periodic |
|--------|-----------|----------|
| **Cost Update** | Every transaction | End of period |
| **Real-time Accuracy** | ✅ High | ❌ Low |
| **Processing Load** | Higher | Lower |
| **Best For** | Fast-moving, perishables | Slow-moving, bulk items |
| **COGS Calculation** | Immediate | Period-end |

**Hybrid Configuration:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Inventory Valuation Settings                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Default Valuation by Category:                          │
│                                                         │
│ Category              │ Valuation    │ Costing Method   │
│ ──────────────────────┼──────────────┼───────────────── │
│ Food - Perishables    │ Perpetual    │ FIFO             │
│ Food - Dry Goods      │ Perpetual    │ Weighted Avg     │
│ Beverages - Alcohol   │ Perpetual    │ FIFO             │
│ Beverages - Non-Alc   │ Perpetual    │ Weighted Avg     │
│ Cleaning Supplies     │ Periodic     │ Weighted Avg     │
│ Guest Amenities       │ Periodic     │ Weighted Avg     │
│ Engineering Spares    │ Periodic     │ Specific ID      │
│ Operating Equipment   │ Periodic     │ Weighted Avg     │
│                                                         │
│ [Save Defaults]                                         │
└─────────────────────────────────────────────────────────┘
```

### 13.4 Warehouse & Location Structure

**Three-Level Hierarchy:**

```
Organization
└── Warehouse (Level 1)
    └── Zone/Area (Level 2)
        └── Bin/Rack (Level 3)

Example:
Hotel Grand Indonesia
├── Main Store (WH-001)
│   ├── Dry Store
│   │   ├── A-01-01 (Rack A, Row 1, Shelf 1)
│   │   ├── A-01-02
│   │   └── ...
│   ├── Cold Room
│   │   ├── C-01-01
│   │   └── ...
│   └── Freezer
│       └── F-01-01
│
├── F&B Store (WH-002)
│   ├── Kitchen Store
│   ├── Bar Store
│   └── Pastry Store
│
├── Housekeeping Store (WH-003)
│   ├── Linen Room
│   ├── Amenities
│   └── Chemicals
│
└── Engineering Store (WH-004)
    ├── Electrical
    ├── Mechanical
    └── Civil
```

**Location Master:**

```
┌─────────────────────────────────────────────────────────┐
│ 🏭 Warehouse & Location Setup                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ▸ WH-001 - Main Store                                   │
│   │  Address: Basement 1                                │
│   │  Manager: John Doe                                  │
│   │                                                     │
│   ├── ▸ ZONE-DRY - Dry Store                            │
│   │   ├── A-01-01  │ Capacity: 50 │ Current: 35        │
│   │   ├── A-01-02  │ Capacity: 50 │ Current: 42        │
│   │   └── [+ Add Bin]                                   │
│   │                                                     │
│   ├── ▸ ZONE-COLD - Cold Room                           │
│   │   │  Temperature: 2-4°C                             │
│   │   ├── C-01-01  │ Capacity: 30 │ Current: 28        │
│   │   └── [+ Add Bin]                                   │
│   │                                                     │
│   └── [+ Add Zone]                                      │
│                                                         │
│ [+ Add Warehouse]                                       │
└─────────────────────────────────────────────────────────┘
```

### 13.5 Inter-Warehouse Transfer

**Transfer Workflow:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Stock Transfer Request                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Transfer No: TRF-2025-12-00045                          │
│ Date: [07-Dec-2025]                                     │
│                                                         │
│ From: [WH-001 - Main Store ▼]                           │
│ To:   [WH-002 - F&B Store ▼]                            │
│                                                         │
│ Items:                                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Item           │ From Bin │ Qty   │ To Bin │ Cost   │ │
│ ├────────────────┼──────────┼───────┼────────┼────────┤ │
│ │ Beef Tenderloin│ C-01-01  │ 10 kg │ K-01-01│2,500,000│ │
│ │ Olive Oil      │ A-01-05  │ 5 ltr │ K-02-03│ 750,000│ │
│ │ Salt           │ A-02-01  │ 20 kg │ K-03-01│ 100,000│ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Total Transfer Value: Rp 3,350,000                      │
│                                                         │
│ Status: [Draft] → [Requested] → [In Transit] → [Received]│
│                                                         │
│ [Submit Request]                                        │
└─────────────────────────────────────────────────────────┘
```

**Transfer Journal (No P&L Impact):**

```
JNL-2025-12-TRF-045 (Inventory Transfer)

Account                          │ Debit       │ Credit
─────────────────────────────────┼─────────────┼────────────
Inventory - F&B Store            │ 3,350,000   │
Inventory - Main Store           │             │ 3,350,000
                                 │ 3,350,000   │ 3,350,000
```

### 13.6 Physical Count / Stock Opname

**Two Counting Methods Available:**

#### 13.6.1 Annual Full Count

```
┌─────────────────────────────────────────────────────────┐
│ 📋 Annual Stock Count - Year End 2025                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Count Date: [31-Dec-2025]                               │
│ Warehouse: [All Warehouses ▼]                           │
│ Status: Planning                                        │
│                                                         │
│ Schedule:                                               │
│ ├── 30-Dec: Freeze all transactions                     │
│ ├── 31-Dec: Physical count (all teams)                  │
│ ├── 01-Jan: Variance review                             │
│ └── 02-Jan: Adjustment posting                          │
│                                                         │
│ Teams:                                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Warehouse       │ Counter 1   │ Counter 2  │ Auditor│ │
│ ├─────────────────┼─────────────┼────────────┼────────┤ │
│ │ Main Store      │ John        │ Mary       │ Ahmad  │ │
│ │ F&B Store       │ Peter       │ Lisa       │ Budi   │ │
│ │ Housekeeping    │ Susan       │ David      │ Ahmad  │ │
│ │ Engineering     │ Michael     │ Sarah      │ Budi   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Generate Count Sheets] [Start Count]                   │
└─────────────────────────────────────────────────────────┘
```

#### 13.6.2 Cycle Counting

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Cycle Count Schedule                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ABC Classification:                                     │
│                                                         │
│ Class │ % of Items │ % of Value │ Count Frequency       │
│ ──────┼────────────┼────────────┼────────────────────── │
│ A     │ 20%        │ 80%        │ Monthly               │
│ B     │ 30%        │ 15%        │ Quarterly             │
│ C     │ 50%        │ 5%         │ Semi-annually         │
│                                                         │
│ This Week's Counts:                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Date    │ Warehouse  │ Items  │ Status     │ Assign │ │
│ ├─────────┼────────────┼────────┼────────────┼────────┤ │
│ │ Mon 09  │ Main Store │ A-items│ Scheduled  │ John   │ │
│ │ Wed 11  │ F&B Store  │ A-items│ Scheduled  │ Peter  │ │
│ │ Fri 13  │ Main Store │ B-items│ Scheduled  │ Mary   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Generate Schedule] [Auto-Assign Counters]              │
└─────────────────────────────────────────────────────────┘
```

### 13.7 Variance & Adjustment

**Count Result & Variance:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Stock Count Variance Report                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Count: CYC-2025-12-001 (Cycle Count - A Items)          │
│ Date: 09-Dec-2025                                       │
│ Warehouse: Main Store                                   │
│                                                         │
│ Summary:                                                │
│ ├── Items Counted: 45                                   │
│ ├── Items with Variance: 8                              │
│ ├── Total Shortage Value: Rp 2,500,000                  │
│ └── Total Overage Value: Rp 350,000                     │
│                                                         │
│ Variances:                                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Item           │ System │ Actual │ Var  │ Value     │ │
│ ├────────────────┼────────┼────────┼──────┼───────────┤ │
│ │ Beef Tenderloin│ 25 kg  │ 23 kg  │ -2   │ -500,000  │ │
│ │ Salmon Fillet  │ 15 kg  │ 12 kg  │ -3   │ -900,000  │ │
│ │ Olive Oil      │ 20 ltr │ 18 ltr │ -2   │ -300,000  │ │
│ │ Rice           │ 100 kg │ 105 kg │ +5   │ +75,000   │ │
│ │ Sugar          │ 50 kg  │ 52 kg  │ +2   │ +30,000   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Variance Reasons (required for adjustment):             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Item           │ Reason              │ Approved By  │ │
│ ├────────────────┼─────────────────────┼──────────────┤ │
│ │ Beef Tenderloin│ Spoilage - expired  │ [Select ▼]   │ │
│ │ Salmon Fillet  │ Theft suspected     │ [Select ▼]   │ │
│ │ Olive Oil      │ Measurement error   │ [Select ▼]   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Request Approval] [Post Adjustment]                    │
└─────────────────────────────────────────────────────────┘
```

**Adjustment Journal:**

```
JNL-2025-12-ADJ-001 (Inventory Adjustment)

Account                          │ Debit       │ Credit
─────────────────────────────────┼─────────────┼────────────
Inventory Shrinkage Expense      │ 1,700,000   │
Inventory Spoilage Expense       │ 500,000     │
Inventory Measurement Adj        │ 300,000     │
Inventory - Main Store           │             │ 2,500,000
                                 │ 2,500,000   │ 2,500,000

-- Overage (separate entry)
Inventory - Main Store           │ 105,000     │
Inventory Overage (Other Income) │             │ 105,000
```

### 13.8 COGS Calculation

**Perpetual Method (Real-time):**

```python
# FIFO Example - Issue 5 kg Beef Tenderloin
inventory_layers = [
    {"batch": "PO-001", "qty": 10, "cost": 240000},  # First in
    {"batch": "PO-002", "qty": 15, "cost": 250000},  # Second
    {"batch": "PO-003", "qty": 8, "cost": 255000},   # Third (most recent)
]

issue_qty = 5  # kg
cogs = 0

# FIFO: Take from oldest first
for layer in inventory_layers:
    if issue_qty <= 0:
        break
    take = min(layer["qty"], issue_qty)
    cogs += take * layer["cost"]
    layer["qty"] -= take
    issue_qty -= take

# Result: COGS = 5 × 240,000 = Rp 1,200,000
```

**Weighted Average Example:**

```python
# Weighted Average - Issue 5 kg
total_qty = 33  # 10 + 15 + 8
total_cost = 10*240000 + 15*250000 + 8*255000  # = 8,190,000
avg_cost = total_cost / total_qty  # = 248,182 per kg

cogs = 5 * 248182  # = Rp 1,240,909
```

### 13.9 Database Schema

```sql
-- Warehouses
CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,

    manager_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, code)
);

-- Warehouse Zones
CREATE TABLE warehouse_zones (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,

    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(20),              -- 'dry', 'cold', 'freezer', 'chemical'
    temperature_range VARCHAR(20),       -- '2-4°C', '-18°C', etc

    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(warehouse_id, code)
);

-- Bin/Rack Locations
CREATE TABLE warehouse_bins (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    zone_id INTEGER NOT NULL REFERENCES warehouse_zones(id) ON DELETE CASCADE,

    code VARCHAR(30) NOT NULL,           -- 'A-01-01'
    description VARCHAR(100),

    capacity_qty DECIMAL(12,3),
    capacity_uom VARCHAR(10),

    current_qty DECIMAL(12,3) DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(zone_id, code)
);

-- Item Categories
CREATE TABLE item_categories (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    parent_id INTEGER REFERENCES item_categories(id),

    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,

    -- Default costing for items in this category
    default_costing_method VARCHAR(20) DEFAULT 'weighted_average',
    default_valuation_type VARCHAR(20) DEFAULT 'perpetual',

    -- GL Accounts
    inventory_account_id INTEGER REFERENCES coa_accounts(id),
    cogs_account_id INTEGER REFERENCES coa_accounts(id),
    variance_account_id INTEGER REFERENCES coa_accounts(id),

    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(organization_id, code)
);

-- Item Master
CREATE TABLE items (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    code VARCHAR(30) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    category_id INTEGER REFERENCES item_categories(id),

    -- Units
    base_uom VARCHAR(10) NOT NULL,       -- 'kg', 'ltr', 'pcs'
    purchase_uom VARCHAR(10),
    issue_uom VARCHAR(10),

    -- Costing
    costing_method VARCHAR(20) NOT NULL, -- 'fifo', 'lifo', 'weighted_average', 'specific'
    valuation_type VARCHAR(20) NOT NULL, -- 'perpetual', 'periodic'

    current_cost DECIMAL(18,4),
    last_purchase_cost DECIMAL(18,4),
    standard_cost DECIMAL(18,4),

    -- Stock Control
    reorder_point DECIMAL(12,3),
    reorder_qty DECIMAL(12,3),
    min_stock DECIMAL(12,3),
    max_stock DECIMAL(12,3),

    -- Classification
    abc_class VARCHAR(1),                -- 'A', 'B', 'C'
    is_perishable BOOLEAN DEFAULT FALSE,
    shelf_life_days INTEGER,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(organization_id, code)
);

-- Stock On Hand (by Location)
CREATE TABLE stock_on_hand (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    bin_id INTEGER REFERENCES warehouse_bins(id),

    quantity DECIMAL(12,3) NOT NULL DEFAULT 0,
    reserved_qty DECIMAL(12,3) DEFAULT 0,
    available_qty DECIMAL(12,3) GENERATED ALWAYS AS (quantity - reserved_qty) STORED,

    -- For Weighted Average
    total_cost DECIMAL(18,2) DEFAULT 0,

    last_count_date DATE,
    last_count_qty DECIMAL(12,3),

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(item_id, warehouse_id, bin_id)
);

-- Stock Layers (for FIFO/LIFO)
CREATE TABLE stock_layers (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    bin_id INTEGER REFERENCES warehouse_bins(id),

    batch_number VARCHAR(50),
    lot_number VARCHAR(50),
    expiry_date DATE,

    receipt_date DATE NOT NULL,
    receipt_reference VARCHAR(50),       -- PO number, etc

    original_qty DECIMAL(12,3) NOT NULL,
    remaining_qty DECIMAL(12,3) NOT NULL,
    unit_cost DECIMAL(18,4) NOT NULL,

    is_depleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stock_layers_item ON stock_layers(item_id, warehouse_id) WHERE NOT is_depleted;
CREATE INDEX idx_stock_layers_expiry ON stock_layers(expiry_date) WHERE NOT is_depleted;

-- Stock Transactions
CREATE TABLE stock_transactions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    transaction_type VARCHAR(20) NOT NULL, -- 'receive', 'issue', 'transfer', 'adjustment', 'count'
    transaction_date DATE NOT NULL,
    reference_number VARCHAR(50) NOT NULL,

    item_id INTEGER NOT NULL REFERENCES items(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    bin_id INTEGER REFERENCES warehouse_bins(id),

    -- For transfers
    to_warehouse_id INTEGER REFERENCES warehouses(id),
    to_bin_id INTEGER REFERENCES warehouse_bins(id),

    quantity DECIMAL(12,3) NOT NULL,
    unit_cost DECIMAL(18,4) NOT NULL,
    total_cost DECIMAL(18,2) NOT NULL,

    -- Layer tracking (for FIFO/LIFO)
    layer_id INTEGER REFERENCES stock_layers(id),

    -- Source document
    source_type VARCHAR(20),             -- 'po', 'requisition', 'production', 'count'
    source_id INTEGER,

    notes TEXT,

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stock_trans_item ON stock_transactions(item_id, transaction_date);
CREATE INDEX idx_stock_trans_ref ON stock_transactions(reference_number);

-- Stock Transfers
CREATE TABLE stock_transfers (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    transfer_number VARCHAR(30) NOT NULL,
    transfer_date DATE NOT NULL,

    from_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    to_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),

    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'requested', 'approved', 'in_transit', 'received', 'cancelled'

    total_items INTEGER,
    total_value DECIMAL(18,2),

    requested_by_id INTEGER REFERENCES users(id),
    requested_at TIMESTAMP WITH TIME ZONE,

    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    shipped_by_id INTEGER REFERENCES users(id),
    shipped_at TIMESTAMP WITH TIME ZONE,

    received_by_id INTEGER REFERENCES users(id),
    received_at TIMESTAMP WITH TIME ZONE,

    notes TEXT,

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    UNIQUE(organization_id, transfer_number)
);

-- Stock Counts
CREATE TABLE stock_counts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    count_number VARCHAR(30) NOT NULL,
    count_type VARCHAR(20) NOT NULL,     -- 'annual', 'cycle', 'spot'
    count_date DATE NOT NULL,

    warehouse_id INTEGER REFERENCES warehouses(id),  -- NULL = all warehouses

    status VARCHAR(20) DEFAULT 'planning', -- 'planning', 'counting', 'reviewing', 'approved', 'posted'

    total_items INTEGER,
    items_with_variance INTEGER,
    total_shortage_value DECIMAL(18,2),
    total_overage_value DECIMAL(18,2),

    freeze_transactions BOOLEAN DEFAULT TRUE,

    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    journal_entry_id INTEGER REFERENCES journal_entries(id),

    UNIQUE(organization_id, count_number)
);

-- Stock Count Details
CREATE TABLE stock_count_details (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    count_id INTEGER NOT NULL REFERENCES stock_counts(id) ON DELETE CASCADE,

    item_id INTEGER NOT NULL REFERENCES items(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    bin_id INTEGER REFERENCES warehouse_bins(id),

    system_qty DECIMAL(12,3) NOT NULL,
    counted_qty DECIMAL(12,3),
    variance_qty DECIMAL(12,3),

    unit_cost DECIMAL(18,4) NOT NULL,
    variance_value DECIMAL(18,2),

    variance_reason VARCHAR(50),         -- 'spoilage', 'theft', 'damage', 'measurement_error', 'unknown'
    notes TEXT,

    counted_by_id INTEGER REFERENCES users(id),
    counted_at TIMESTAMP WITH TIME ZONE,

    verified_by_id INTEGER REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE
);

-- Cycle Count Schedule
CREATE TABLE cycle_count_schedule (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    abc_class VARCHAR(1) NOT NULL,       -- 'A', 'B', 'C'
    frequency VARCHAR(20) NOT NULL,      -- 'weekly', 'monthly', 'quarterly', 'semi_annual'

    last_count_date DATE,
    next_count_date DATE,

    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes
CREATE INDEX idx_items_org ON items(organization_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_stock_on_hand_item ON stock_on_hand(item_id);
CREATE INDEX idx_stock_counts_status ON stock_counts(organization_id, status);
```

### 13.10 Business Rules Configuration

**Soft Rules for Inventory:**

```json
{
  "rule_code": "INV_COSTING_DEFAULTS",
  "rule_type": "mapping",
  "default_value": {
    "default_costing_method": "weighted_average",
    "default_valuation_type": "perpetual",
    "allow_negative_stock": false,
    "auto_reorder": false
  }
},
{
  "rule_code": "INV_COUNT_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "annual_count_month": 12,
    "freeze_days_before": 1,
    "require_dual_count": true,
    "variance_approval_threshold": 1000000,
    "cycle_count_enabled": true,
    "abc_frequencies": {
      "A": "monthly",
      "B": "quarterly",
      "C": "semi_annual"
    }
  }
},
{
  "rule_code": "INV_VARIANCE_REASONS",
  "rule_type": "list",
  "default_value": [
    {"code": "spoilage", "name": "Spoilage/Expired", "gl_account": "6201-001"},
    {"code": "theft", "name": "Theft/Pilferage", "gl_account": "6201-002"},
    {"code": "damage", "name": "Damage", "gl_account": "6201-003"},
    {"code": "measurement", "name": "Measurement Error", "gl_account": "6201-004"},
    {"code": "unknown", "name": "Unknown", "gl_account": "6201-005"}
  ]
}

---

## 14. Budgeting

> **Status**: ✅ Approved (2025-12-07)

### 14.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Budget period alignment | ✅ (fiscal year) | ❌ |
| Variance calculation accuracy | ✅ | ❌ |
| Budget granularity | ❌ | ✅ (account/dept/month) |
| Budget versions/scenarios | ❌ | ✅ (unlimited) |
| Entry methods | ❌ | ✅ (manual/import/formula) |
| Approval workflow | ❌ | ✅ (configurable) |

### 14.2 Budget Structure (Full Detail)

**Three-Dimensional Budget:**

```
Budget = Account × Department × Period

Example:
┌────────────────────────────────────────────────────────────────┐
│ Budget 2026 - Rooms Division                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Account: 4101-001 - Room Revenue                               │
│ Department: RM - Rooms                                         │
│                                                                │
│ Monthly Breakdown:                                             │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Month   │ Budget      │ Occupancy │ ADR      │ RevPAR   │   │
│ ├─────────┼─────────────┼───────────┼──────────┼──────────┤   │
│ │ Jan     │ 2,500,000,000│ 65%      │ 850,000  │ 552,500  │   │
│ │ Feb     │ 2,300,000,000│ 63%      │ 850,000  │ 535,500  │   │
│ │ Mar     │ 2,800,000,000│ 70%      │ 880,000  │ 616,000  │   │
│ │ Apr     │ 3,000,000,000│ 75%      │ 880,000  │ 660,000  │   │
│ │ May     │ 2,700,000,000│ 68%      │ 875,000  │ 595,000  │   │
│ │ Jun     │ 3,200,000,000│ 80%      │ 900,000  │ 720,000  │   │
│ │ Jul     │ 3,500,000,000│ 85%      │ 920,000  │ 782,000  │   │
│ │ Aug     │ 3,300,000,000│ 82%      │ 900,000  │ 738,000  │   │
│ │ Sep     │ 2,900,000,000│ 72%      │ 890,000  │ 640,800  │   │
│ │ Oct     │ 2,600,000,000│ 66%      │ 870,000  │ 574,200  │   │
│ │ Nov     │ 2,400,000,000│ 62%      │ 855,000  │ 530,100  │   │
│ │ Dec     │ 3,800,000,000│ 90%      │ 950,000  │ 855,000  │   │
│ ├─────────┼─────────────┼───────────┼──────────┼──────────┤   │
│ │ TOTAL   │35,000,000,000│ 73%      │ 885,000  │ 649,925  │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 14.3 Budget Scenarios (Multiple Versions)

**Available Scenarios:**

| Scenario | Purpose | Usage |
|----------|---------|-------|
| **Original** | Initial approved budget | Baseline for comparison |
| **Revised** | Mid-year adjustments | After significant changes |
| **Best Case** | Optimistic projection | Upper bound planning |
| **Worst Case** | Conservative projection | Risk management |
| **Forecast** | Rolling forecast | Updated monthly |

**Scenario Management:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Budget Scenarios - FY 2026                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Scenario     │ Status    │ Created   │ Approved    │ │
│ ├──────────────┼───────────┼───────────┼─────────────┤ │
│ │ Original     │ ✅ Active │ 15-Nov-25 │ 01-Dec-25   │ │
│ │ Best Case    │ ✅ Active │ 15-Nov-25 │ 01-Dec-25   │ │
│ │ Worst Case   │ ✅ Active │ 15-Nov-25 │ 01-Dec-25   │ │
│ │ Revised Q1   │ 📝 Draft  │ 01-Apr-26 │ Pending     │ │
│ │ Forecast     │ 🔄 Rolling│ Auto      │ Auto        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Compare: [Original ▼] vs [Revised Q1 ▼]                 │
│                                                         │
│ [+ New Scenario] [Copy Scenario] [Delete Draft]         │
└─────────────────────────────────────────────────────────┘
```

### 14.4 Budget Entry Methods

#### 14.4.1 Manual Entry

```
┌─────────────────────────────────────────────────────────┐
│ ✏️ Budget Entry - Manual                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Scenario: [Original ▼]                                  │
│ Department: [RM - Rooms ▼]                              │
│ Account: [4101-001 - Room Revenue ▼]                    │
│                                                         │
│ Entry Mode:                                             │
│ ● Monthly detail                                        │
│ ○ Annual (spread evenly)                                │
│ ○ Seasonal pattern                                      │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Month │ Amount         │ Notes                      │ │
│ ├───────┼────────────────┼────────────────────────────┤ │
│ │ Jan   │ [2,500,000,000]│ [Low season             ]  │ │
│ │ Feb   │ [2,300,000,000]│ [                       ]  │ │
│ │ Mar   │ [2,800,000,000]│ [Spring break           ]  │ │
│ │ ...   │                │                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Save Draft] [Submit for Approval]                      │
└─────────────────────────────────────────────────────────┘
```

#### 14.4.2 Excel Import

```
┌─────────────────────────────────────────────────────────┐
│ 📥 Budget Import - Excel                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Scenario: [Original ▼]                                  │
│                                                         │
│ Step 1: Download Template                               │
│ [Download Template] (includes account & dept codes)     │
│                                                         │
│ Step 2: Upload Filled Template                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  📄 Drag & drop Excel file here                     │ │
│ │     or [Browse...]                                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Step 3: Validation Results                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✅ 450 rows validated successfully                  │ │
│ │ ⚠️ 3 warnings (missing optional fields)            │ │
│ │ ❌ 2 errors (invalid account codes)                 │ │
│ │                                                     │ │
│ │ [View Details] [Download Error Report]              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Import Valid Rows] [Cancel]                            │
└─────────────────────────────────────────────────────────┘
```

**Excel Template Format:**

| Account | Department | Jan | Feb | Mar | ... | Dec | Annual |
|---------|------------|-----|-----|-----|-----|-----|--------|
| 4101-001 | RM | 2,500,000,000 | 2,300,000,000 | 2,800,000,000 | ... | 3,800,000,000 | 35,000,000,000 |
| 5101-001 | RM | 200,000,000 | 190,000,000 | 220,000,000 | ... | 300,000,000 | 2,800,000,000 |

#### 14.4.3 Formula-Based Entry

```
┌─────────────────────────────────────────────────────────┐
│ 🧮 Budget Entry - Formula                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Scenario: [Revised Q1 ▼]                                │
│ Base: [Original ▼]                                      │
│                                                         │
│ Formula Builder:                                        │
│                                                         │
│ Revenue Accounts (4xxx):                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Formula: [PREVIOUS_YEAR * 1.05              ▼]      │ │
│ │                                                     │ │
│ │ Available formulas:                                 │ │
│ │ • PREVIOUS_YEAR * factor                            │ │
│ │ • PREVIOUS_BUDGET * factor                          │ │
│ │ • PREVIOUS_YEAR + fixed_amount                      │ │
│ │ • YTD_ACTUAL * (12 / current_month)                 │ │
│ │ • Custom formula...                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Expense Accounts (5xxx-6xxx):                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Formula: [PREVIOUS_BUDGET * 1.03            ▼]      │ │
│ │ (3% increase for inflation)                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Preview Results:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Account     │ Original    │ Calculated  │ Change   │ │
│ ├─────────────┼─────────────┼─────────────┼──────────┤ │
│ │ Room Rev    │ 35,000M     │ 36,750M     │ +5.0%    │ │
│ │ F&B Rev     │ 12,000M     │ 12,600M     │ +5.0%    │ │
│ │ Salary Exp  │ 8,000M      │ 8,240M      │ +3.0%    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Apply Formulas] [Adjust Individual Items]              │
└─────────────────────────────────────────────────────────┘
```

### 14.5 Budget Approval Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 📋 Budget Approval Workflow                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Budget: FY 2026 - Original                              │
│                                                         │
│ Workflow Steps:                                         │
│                                                         │
│ ① Department Submission                                 │
│    └── Each HOD submits their department budget         │
│        Status: ✅ 12/12 departments submitted           │
│                                                         │
│ ② Department Review                                     │
│    └── Finance reviews each department                  │
│        Status: ✅ All reviewed                          │
│                                                         │
│ ③ Consolidation                                         │
│    └── Finance consolidates into master budget          │
│        Status: ✅ Consolidated                          │
│                                                         │
│ ④ Management Review                                     │
│    └── GM/DOF reviews consolidated budget               │
│        Status: ✅ Approved by DOF                       │
│                                                         │
│ ⑤ Final Approval                                        │
│    └── Owner/Board approval                             │
│        Status: 🔄 Pending (sent 28-Nov)                 │
│                                                         │
│ [View Timeline] [Send Reminder] [Escalate]              │
└─────────────────────────────────────────────────────────┘
```

### 14.6 Variance Analysis (Full)

**Dashboard View:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Budget vs Actual Analysis - December 2025            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Scenario: [Original ▼]  Period: [Dec 2025 ▼]            │
│                                                         │
│ ┌─────────── Summary ───────────┐                       │
│ │                               │                       │
│ │  MTD Variance    YTD Variance │                       │
│ │  ▲ +5.2%         ▲ +3.8%      │                       │
│ │  (Favorable)     (Favorable)  │                       │
│ │                               │                       │
│ └───────────────────────────────┘                       │
│                                                         │
│ Revenue:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Department │ Budget    │ Actual    │ Var %  │ Trend │ │
│ ├────────────┼───────────┼───────────┼────────┼───────┤ │
│ │ Rooms      │ 3,800M    │ 4,100M    │ +7.9%  │ ▲▲▲   │ │
│ │ F&B        │ 1,200M    │ 1,150M    │ -4.2%  │ ▼     │ │
│ │ Spa        │ 300M      │ 320M      │ +6.7%  │ ▲▲    │ │
│ │ Other      │ 200M      │ 210M      │ +5.0%  │ ▲     │ │
│ ├────────────┼───────────┼───────────┼────────┼───────┤ │
│ │ TOTAL REV  │ 5,500M    │ 5,780M    │ +5.1%  │ ▲▲    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Click row to drill-down]                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Drill-Down View:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Drill-Down: Rooms Revenue - December 2025            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [◀ Back to Summary]                                     │
│                                                         │
│ Rooms Revenue: Budget 3,800M vs Actual 4,100M (+7.9%)   │
│                                                         │
│ By Revenue Type:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Type          │ Budget   │ Actual   │ Variance     │ │
│ ├───────────────┼──────────┼──────────┼──────────────┤ │
│ │ Room Rental   │ 3,200M   │ 3,500M   │ +300M (+9.4%)│ │
│ │ Minibar       │ 150M     │ 140M     │ -10M (-6.7%) │ │
│ │ Laundry       │ 100M     │ 110M     │ +10M (+10%)  │ │
│ │ Others        │ 350M     │ 350M     │ 0 (0%)       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Key Metrics:                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Metric     │ Budget  │ Actual  │ Variance          │ │
│ ├────────────┼─────────┼─────────┼───────────────────┤ │
│ │ Occupancy  │ 90%     │ 93%     │ +3 pts            │ │
│ │ ADR        │ 950,000 │ 980,000 │ +30,000 (+3.2%)   │ │
│ │ RevPAR     │ 855,000 │ 911,400 │ +56,400 (+6.6%)   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [View Transactions] [Export to Excel]                   │
└─────────────────────────────────────────────────────────┘
```

**Trend Analysis:**

```
┌─────────────────────────────────────────────────────────┐
│ 📈 Trend Analysis - Rooms Revenue 2025                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│     Budget ─── Actual ─── Forecast ...                  │
│                                                         │
│ 4.5M ┤                                          ╭──●    │
│      │                                    ╭────╯        │
│ 4.0M ┤                              ╭────╯    ●         │
│      │                        ╭────╯    ●               │
│ 3.5M ┤                  ╭────╯    ●                     │
│      │            ╭────╯    ●                           │
│ 3.0M ┤      ╭────╯    ●                                 │
│      │╭────╯    ●                                       │
│ 2.5M ┼●                                                 │
│      └────┬────┬────┬────┬────┬────┬────┬────┬────┬──── │
│          Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep... │
│                                                         │
│ YTD Performance:                                        │
│ • Budget: 32,500M                                       │
│ • Actual: 33,750M                                       │
│ • Variance: +1,250M (+3.8%)                             │
│ • Forecast Full Year: 36,800M (+5.1% vs budget)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 14.7 Rolling Forecast

**Automatic Forecast Update:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Rolling Forecast - Updated Monthly                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Current Period: December 2025                           │
│ Forecast Method: [Actual + Remaining Budget ▼]          │
│                                                         │
│ Forecast Calculation:                                   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Component           │ Amount                        │ │
│ ├─────────────────────┼───────────────────────────────┤ │
│ │ YTD Actual (Jan-Nov)│ 32,500,000,000                │ │
│ │ Dec Forecast        │ 4,100,000,000 (trending)      │ │
│ │ Full Year Forecast  │ 36,600,000,000                │ │
│ │ vs Original Budget  │ +1,600,000,000 (+4.6%)        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Alternative Methods:                                    │
│ ○ Actual + Remaining Budget (current)                   │
│ ○ Run-rate (YTD × 12 / months elapsed)                  │
│ ○ Seasonal adjustment                                   │
│ ○ Custom formula                                        │
│                                                         │
│ [Update Forecast] [Compare Methods]                     │
└─────────────────────────────────────────────────────────┘
```

### 14.8 Database Schema

```sql
-- Budget Scenarios
CREATE TABLE budget_scenarios (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    fiscal_year INTEGER NOT NULL,
    scenario_code VARCHAR(20) NOT NULL,      -- 'ORIGINAL', 'REVISED_Q1', 'BEST_CASE', etc
    scenario_name VARCHAR(100) NOT NULL,

    scenario_type VARCHAR(20) NOT NULL,      -- 'original', 'revised', 'best_case', 'worst_case', 'forecast'
    base_scenario_id INTEGER REFERENCES budget_scenarios(id),  -- For revisions

    status VARCHAR(20) DEFAULT 'draft',      -- 'draft', 'submitted', 'approved', 'active', 'archived'

    is_active BOOLEAN DEFAULT FALSE,         -- Only one active per year
    is_rolling_forecast BOOLEAN DEFAULT FALSE,

    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    notes TEXT,

    UNIQUE(organization_id, fiscal_year, scenario_code)
);

-- Budget Lines (the actual budget data)
CREATE TABLE budget_lines (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    scenario_id INTEGER NOT NULL REFERENCES budget_scenarios(id) ON DELETE CASCADE,

    account_id INTEGER NOT NULL REFERENCES coa_accounts(id),
    department_id INTEGER REFERENCES departments(id),

    -- Monthly amounts
    period_01 DECIMAL(18,2) DEFAULT 0,
    period_02 DECIMAL(18,2) DEFAULT 0,
    period_03 DECIMAL(18,2) DEFAULT 0,
    period_04 DECIMAL(18,2) DEFAULT 0,
    period_05 DECIMAL(18,2) DEFAULT 0,
    period_06 DECIMAL(18,2) DEFAULT 0,
    period_07 DECIMAL(18,2) DEFAULT 0,
    period_08 DECIMAL(18,2) DEFAULT 0,
    period_09 DECIMAL(18,2) DEFAULT 0,
    period_10 DECIMAL(18,2) DEFAULT 0,
    period_11 DECIMAL(18,2) DEFAULT 0,
    period_12 DECIMAL(18,2) DEFAULT 0,
    period_13 DECIMAL(18,2) DEFAULT 0,       -- Adjustment period

    annual_total DECIMAL(18,2) GENERATED ALWAYS AS (
        period_01 + period_02 + period_03 + period_04 +
        period_05 + period_06 + period_07 + period_08 +
        period_09 + period_10 + period_11 + period_12 +
        period_13
    ) STORED,

    -- Formula tracking
    formula_used VARCHAR(100),
    formula_base VARCHAR(50),                -- 'PREVIOUS_YEAR', 'PREVIOUS_BUDGET', etc
    formula_factor DECIMAL(8,4),

    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(scenario_id, account_id, department_id)
);

-- Budget Workflow (approval tracking)
CREATE TABLE budget_approvals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    scenario_id INTEGER NOT NULL REFERENCES budget_scenarios(id) ON DELETE CASCADE,

    step_order INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,

    department_id INTEGER REFERENCES departments(id),  -- NULL = all

    status VARCHAR(20) DEFAULT 'pending',    -- 'pending', 'submitted', 'approved', 'rejected', 'revision_requested'

    submitted_by_id INTEGER REFERENCES users(id),
    submitted_at TIMESTAMP WITH TIME ZONE,

    reviewed_by_id INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    due_date DATE
);

-- Budget Import History
CREATE TABLE budget_imports (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    scenario_id INTEGER NOT NULL REFERENCES budget_scenarios(id),

    filename VARCHAR(255) NOT NULL,
    import_type VARCHAR(20) NOT NULL,        -- 'excel', 'csv'

    total_rows INTEGER,
    successful_rows INTEGER,
    error_rows INTEGER,
    warning_rows INTEGER,

    error_details JSONB,

    imported_by_id INTEGER REFERENCES users(id),
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Variance Analysis Cache (for performance)
CREATE TABLE budget_variance_cache (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    scenario_id INTEGER NOT NULL REFERENCES budget_scenarios(id),

    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,

    account_id INTEGER NOT NULL REFERENCES coa_accounts(id),
    department_id INTEGER REFERENCES departments(id),

    budget_amount DECIMAL(18,2),
    actual_amount DECIMAL(18,2),
    variance_amount DECIMAL(18,2),
    variance_percentage DECIMAL(8,4),

    ytd_budget DECIMAL(18,2),
    ytd_actual DECIMAL(18,2),
    ytd_variance_amount DECIMAL(18,2),
    ytd_variance_percentage DECIMAL(8,4),

    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(scenario_id, period_year, period_month, account_id, department_id)
);

-- Budget KPIs (for non-financial metrics)
CREATE TABLE budget_kpis (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    scenario_id INTEGER NOT NULL REFERENCES budget_scenarios(id) ON DELETE CASCADE,

    kpi_code VARCHAR(30) NOT NULL,           -- 'OCCUPANCY', 'ADR', 'REVPAR', etc
    kpi_name VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(id),

    period_01 DECIMAL(12,4),
    period_02 DECIMAL(12,4),
    period_03 DECIMAL(12,4),
    period_04 DECIMAL(12,4),
    period_05 DECIMAL(12,4),
    period_06 DECIMAL(12,4),
    period_07 DECIMAL(12,4),
    period_08 DECIMAL(12,4),
    period_09 DECIMAL(12,4),
    period_10 DECIMAL(12,4),
    period_11 DECIMAL(12,4),
    period_12 DECIMAL(12,4),

    unit VARCHAR(20),                        -- '%', 'IDR', 'nights', etc

    UNIQUE(scenario_id, kpi_code, department_id)
);

-- Indexes
CREATE INDEX idx_budget_scenarios_org ON budget_scenarios(organization_id, fiscal_year);
CREATE INDEX idx_budget_lines_scenario ON budget_lines(scenario_id);
CREATE INDEX idx_budget_lines_account ON budget_lines(account_id);
CREATE INDEX idx_budget_variance_cache_period ON budget_variance_cache(scenario_id, period_year, period_month);
```

### 14.9 Business Rules Configuration

**Soft Rules for Budgeting:**

```json
{
  "rule_code": "BUDGET_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "fiscal_year_start_month": 1,
    "budget_submission_deadline_days": 30,
    "allow_over_budget_transactions": true,
    "warn_threshold_percentage": 90,
    "block_threshold_percentage": null
  }
},
{
  "rule_code": "BUDGET_APPROVAL_WORKFLOW",
  "rule_type": "list",
  "default_value": [
    {"step": 1, "name": "Department Submission", "role": "department_head"},
    {"step": 2, "name": "Finance Review", "role": "finance_manager"},
    {"step": 3, "name": "Consolidation", "role": "finance_director"},
    {"step": 4, "name": "Management Approval", "role": "general_manager"},
    {"step": 5, "name": "Final Approval", "role": "owner"}
  ]
},
{
  "rule_code": "BUDGET_FORMULA_TEMPLATES",
  "rule_type": "list",
  "default_value": [
    {"code": "PREV_YEAR_PLUS", "name": "Previous Year + %", "formula": "PREVIOUS_YEAR * (1 + factor)"},
    {"code": "PREV_BUDGET_PLUS", "name": "Previous Budget + %", "formula": "PREVIOUS_BUDGET * (1 + factor)"},
    {"code": "ZERO_BASE", "name": "Zero-Based", "formula": "0"},
    {"code": "RUN_RATE", "name": "Run Rate", "formula": "YTD_ACTUAL * (12 / ELAPSED_MONTHS)"},
    {"code": "SEASONAL", "name": "Seasonal Pattern", "formula": "PREVIOUS_YEAR_MONTH * (1 + factor)"}
  ]
},
{
  "rule_code": "FORECAST_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "auto_update": true,
    "update_day": 5,
    "method": "actual_plus_remaining",
    "lock_completed_months": true
  }
}

---

## 15. Consolidation

> **Status**: ✅ Approved (2025-12-07)

### 15.1 Hard vs Soft Rules Summary

| Rule Type | Hard (Embedded) | Soft (Configurable) |
|-----------|-----------------|---------------------|
| Consolidation accuracy | ✅ | ❌ |
| Elimination matching | ✅ (must balance) | ❌ |
| Entity hierarchy structure | ❌ | ✅ (multi-level) |
| Consolidation features | ❌ | ✅ (eliminations, MI, forex) |
| Intercompany detection | ❌ | ✅ (semi-auto) |
| Consolidation frequency | ❌ | ✅ (on-demand/monthly/annual) |

### 15.2 Configurable Consolidation Scope

**Each feature can be enabled/disabled per consolidation group:**

| Feature | Description | Default |
|---------|-------------|---------|
| **Eliminations** | Remove intercompany transactions | ✅ On |
| **Minority Interest** | Calculate non-controlling interest | ⬚ Off |
| **Forex Translation** | Translate foreign currency subsidiaries | ⬚ Off |

**Configuration Panel:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Consolidation Group Settings                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Group Name: [PT Hospitality Group]                      │
│ Parent Entity: [PT Hospitality Holding]                 │
│                                                         │
│ Consolidation Features:                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [✓] Intercompany Eliminations                       │ │
│ │     Automatically eliminate IC transactions         │ │
│ │                                                     │ │
│ │ [✓] Minority Interest                               │ │
│ │     Calculate NCI for <100% owned subsidiaries      │ │
│ │                                                     │ │
│ │ [✓] Foreign Currency Translation                    │ │
│ │     Translate USD/SGD subsidiaries to IDR           │ │
│ │     Method: [Current Rate ▼]                        │ │
│ │     ○ Current Rate (all at closing rate)            │ │
│ │     ● Temporal (monetary vs non-monetary)           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Save Settings]                                         │
└─────────────────────────────────────────────────────────┘
```

### 15.3 Multi-Level Entity Hierarchy

**Three-Level Structure:**

```
Holding Company (Level 0)
└── Sub-Holding (Level 1)
    └── Operating Entity (Level 2)
        └── Branch/Unit (Level 3 - optional)

Example:
PT Hospitality Group (Holding)
├── PT Hotel Management (Sub-Holding)
│   ├── PT Grand Hotel Jakarta (Operating - 100%)
│   ├── PT Grand Hotel Bali (Operating - 100%)
│   └── PT Grand Hotel Surabaya (Operating - 80%)
│       └── Minority: Local Partner (20%)
│
├── PT F&B Management (Sub-Holding)
│   ├── PT Resto Chain (Operating - 100%)
│   └── PT Catering Services (Operating - 70%)
│       └── Minority: Strategic Partner (30%)
│
└── PT Property Holding (Sub-Holding - 60%)
    ├── PT Mall Jakarta (Operating - 100%)
    └── Minority: Foreign Investor (40%)
```

**Entity Master:**

```
┌─────────────────────────────────────────────────────────┐
│ 🏢 Entity Hierarchy Setup                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ▾ PT Hospitality Group [Holding]                        │
│   │  Ownership: 100% (Ultimate Parent)                  │
│   │  Currency: IDR                                      │
│   │                                                     │
│   ├── ▾ PT Hotel Management [Sub-Holding]               │
│   │   │  Ownership: 100%                                │
│   │   │  Currency: IDR                                  │
│   │   │                                                 │
│   │   ├── PT Grand Hotel Jakarta [Operating]            │
│   │   │   Ownership: 100% │ Currency: IDR               │
│   │   │                                                 │
│   │   ├── PT Grand Hotel Bali [Operating]               │
│   │   │   Ownership: 100% │ Currency: IDR               │
│   │   │                                                 │
│   │   └── PT Grand Hotel Surabaya [Operating]           │
│   │       Ownership: 80% │ NCI: 20% │ Currency: IDR     │
│   │                                                     │
│   ├── ▾ PT F&B Management [Sub-Holding]                 │
│   │   │  Ownership: 100%                                │
│   │   │  ...                                            │
│   │                                                     │
│   └── ▾ PT Property Holding [Sub-Holding]               │
│       │  Ownership: 60% │ NCI: 40%                      │
│       │  ...                                            │
│                                                         │
│ [+ Add Entity] [Edit Hierarchy] [View Chart]            │
└─────────────────────────────────────────────────────────┘
```

### 15.4 Intercompany Transaction Detection (Semi-Auto)

**Detection Process:**

```
Step 1: System Detects Potential IC Transactions
────────────────────────────────────────────────

System scans for:
• Same counterparty (vendor/customer = group entity)
• Matching amounts (within tolerance)
• Matching dates (within period)
• Matching references

Step 2: User Reviews & Confirms Matches
────────────────────────────────────────

┌─────────────────────────────────────────────────────────┐
│ 🔍 Intercompany Transaction Matching                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Period: December 2025                                   │
│ Status: 15 potential matches found                      │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Match #1 - High Confidence (99%)                    │ │
│ │                                                     │ │
│ │ SELLER: PT Grand Hotel Jakarta                      │ │
│ │ Invoice: INV-2025-1234                              │ │
│ │ Amount: Rp 50,000,000                               │ │
│ │ Date: 15-Dec-2025                                   │ │
│ │ Description: Management Fee Dec 2025               │ │
│ │                                                     │ │
│ │ BUYER: PT Hotel Management                          │ │
│ │ Bill: BILL-2025-5678                                │ │
│ │ Amount: Rp 50,000,000                               │ │
│ │ Date: 15-Dec-2025                                   │ │
│ │ Description: Mgmt Fee - Jakarta Dec                 │ │
│ │                                                     │ │
│ │ [✓ Confirm Match] [✗ Not IC] [? Review Later]       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Match #2 - Medium Confidence (75%)                  │ │
│ │                                                     │ │
│ │ SELLER: PT Catering Services                        │ │
│ │ Amount: Rp 25,500,000                               │ │
│ │                                                     │ │
│ │ BUYER: PT Grand Hotel Bali                          │ │
│ │ Amount: Rp 25,000,000 (Diff: 500,000)               │ │
│ │                                                     │ │
│ │ ⚠️ Amount mismatch - please verify                  │ │
│ │ [✓ Confirm] [✗ Not IC] [📝 Adjust Amount]           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Summary:                                                │
│ • Auto-matched: 12                                      │
│ • Needs review: 3                                       │
│ • Total IC Value: Rp 850,000,000                        │
│                                                         │
│ [Confirm All High-Confidence] [Export to Excel]         │
└─────────────────────────────────────────────────────────┘
```

### 15.5 Consolidation Process

**On-Demand Consolidation:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Run Consolidation                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Consolidation Group: [PT Hospitality Group ▼]           │
│ Period: [December 2025 ▼]                               │
│ Type: [Monthly ▼]                                       │
│   ○ On-demand (draft, not saved)                        │
│   ● Monthly (saved for reporting)                       │
│   ○ Annual (year-end, with adjustments)                 │
│                                                         │
│ Entities to Include:                                    │
│ [✓] All entities (8 entities)                           │
│     or select specific:                                 │
│     [✓] PT Hotel Management group (4)                   │
│     [✓] PT F&B Management group (2)                     │
│     [✓] PT Property Holding group (2)                   │
│                                                         │
│ Pre-Consolidation Checks:                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✅ All entities closed for Dec 2025                 │ │
│ │ ✅ IC transactions matched (98% - 2 pending)        │ │
│ │ ✅ Exchange rates available                         │ │
│ │ ⚠️ 2 IC transactions need review                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Run Pre-Check] [Start Consolidation]                   │
└─────────────────────────────────────────────────────────┘
```

**Consolidation Steps:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Consolidation Progress                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Step 1: Aggregate Trial Balances              ✅ Done   │
│         Combined 8 entities                             │
│                                                         │
│ Step 2: Currency Translation                  ✅ Done   │
│         Translated 0 foreign entities                   │
│         (All entities in IDR)                           │
│                                                         │
│ Step 3: Intercompany Eliminations             ✅ Done   │
│         Eliminated 15 IC transactions                   │
│         Total eliminated: Rp 850,000,000                │
│                                                         │
│ Step 4: Investment Eliminations               ✅ Done   │
│         Eliminated investment in subsidiaries           │
│         Equity eliminated: Rp 500,000,000,000           │
│                                                         │
│ Step 5: Minority Interest Calculation         ✅ Done   │
│         NCI calculated for 3 entities                   │
│         Total NCI: Rp 45,000,000,000                    │
│                                                         │
│ Step 6: Generate Consolidated Statements      🔄 Running│
│         ████████████░░░░ 75%                            │
│                                                         │
│ [View Log] [Cancel]                                     │
└─────────────────────────────────────────────────────────┘
```

### 15.6 Elimination Entries

**Intercompany Eliminations:**

```
┌─────────────────────────────────────────────────────────┐
│ 📒 Elimination Journal Entries                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Period: December 2025                                   │
│ Type: Intercompany Eliminations                         │
│                                                         │
│ Entry #1: IC Revenue/Expense Elimination                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Account                    │ Debit      │ Credit    │ │
│ ├────────────────────────────┼────────────┼───────────┤ │
│ │ IC Revenue (Seller)        │ 50,000,000 │           │ │
│ │ IC Expense (Buyer)         │            │ 50,000,000│ │
│ │                                                     │ │
│ │ Reference: INV-2025-1234 ↔ BILL-2025-5678           │ │
│ │ Entities: Jakarta → Hotel Management               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Entry #2: IC Receivable/Payable Elimination             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Account                    │ Debit      │ Credit    │ │
│ ├────────────────────────────┼────────────┼───────────┤ │
│ │ IC Payable (Buyer)         │ 50,000,000 │           │ │
│ │ IC Receivable (Seller)     │            │ 50,000,000│ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Total Eliminations: 30 entries                          │
│ [View All] [Export]                                     │
└─────────────────────────────────────────────────────────┘
```

**Investment Elimination & Minority Interest:**

```
Entry #3: Investment Elimination
┌─────────────────────────────────────────────────────────┐
│ Account                        │ Debit        │ Credit  │
├────────────────────────────────┼──────────────┼─────────┤
│ Share Capital - Subsidiary     │ 100,000,000,000│        │
│ Retained Earnings - Subsidiary │ 50,000,000,000 │        │
│ Investment in Subsidiary       │              │150,000,000,000│
│                                                         │
│ Entity: PT Grand Hotel Jakarta (100% owned)             │
└─────────────────────────────────────────────────────────┘

Entry #4: Minority Interest Recognition
┌─────────────────────────────────────────────────────────┐
│ Account                        │ Debit       │ Credit   │
├────────────────────────────────┼─────────────┼──────────┤
│ Share Capital - Subsidiary     │ 20,000,000,000│         │
│ Retained Earnings - Subsidiary │ 10,000,000,000│         │
│ Non-Controlling Interest       │             │30,000,000,000│
│                                                         │
│ Entity: PT Grand Hotel Surabaya (80% owned, 20% NCI)    │
│ NCI Share: 20% × (100B + 50B) = 30B                     │
└─────────────────────────────────────────────────────────┘
```

### 15.7 Consolidated Financial Statements

**Consolidated Balance Sheet:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Consolidated Balance Sheet                           │
│    PT Hospitality Group                                 │
│    As of December 31, 2025                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                        │ Consolidated │ Eliminations   │
│ ASSETS                 │              │                │
│ ───────────────────────┼──────────────┼──────────────  │
│ Current Assets         │ 150,000 M    │ (5,000 M) IC   │
│ Fixed Assets           │ 800,000 M    │                │
│ Investment in Subs     │ -            │ (500,000 M)    │
│ Other Assets           │ 50,000 M     │                │
│ ───────────────────────┼──────────────┼──────────────  │
│ TOTAL ASSETS           │ 1,000,000 M  │                │
│                                                         │
│ LIABILITIES            │              │                │
│ ───────────────────────┼──────────────┼──────────────  │
│ Current Liabilities    │ 200,000 M    │ (5,000 M) IC   │
│ Long-term Debt         │ 300,000 M    │                │
│ ───────────────────────┼──────────────┼──────────────  │
│ TOTAL LIABILITIES      │ 500,000 M    │                │
│                                                         │
│ EQUITY                 │              │                │
│ ───────────────────────┼──────────────┼──────────────  │
│ Share Capital          │ 300,000 M    │                │
│ Retained Earnings      │ 155,000 M    │                │
│ Non-Controlling Interest│ 45,000 M    │ (calculated)   │
│ ───────────────────────┼──────────────┼──────────────  │
│ TOTAL EQUITY           │ 500,000 M    │                │
│                                                         │
│ [Drill-down by Entity] [Export] [Print]                 │
└─────────────────────────────────────────────────────────┘
```

### 15.8 Database Schema

```sql
-- Consolidation Groups
CREATE TABLE consolidation_groups (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,

    parent_entity_id INTEGER NOT NULL REFERENCES organizations(id),

    -- Features enabled
    enable_eliminations BOOLEAN DEFAULT TRUE,
    enable_minority_interest BOOLEAN DEFAULT FALSE,
    enable_forex_translation BOOLEAN DEFAULT FALSE,

    forex_method VARCHAR(20),            -- 'current_rate', 'temporal'
    functional_currency VARCHAR(3) DEFAULT 'IDR',

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Entity Hierarchy
CREATE TABLE consolidation_entities (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_id INTEGER NOT NULL REFERENCES consolidation_groups(id) ON DELETE CASCADE,

    entity_id INTEGER NOT NULL REFERENCES organizations(id),
    parent_entity_id INTEGER REFERENCES organizations(id),

    entity_level INTEGER NOT NULL,       -- 0=holding, 1=sub-holding, 2=operating
    entity_type VARCHAR(20) NOT NULL,    -- 'holding', 'sub_holding', 'operating', 'branch'

    ownership_percentage DECIMAL(5,2) NOT NULL,  -- e.g., 80.00
    effective_ownership DECIMAL(5,2),    -- After calculating through hierarchy

    nci_percentage DECIMAL(5,2) GENERATED ALWAYS AS (100 - ownership_percentage) STORED,

    local_currency VARCHAR(3) NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    consolidation_method VARCHAR(20) DEFAULT 'full',  -- 'full', 'equity', 'proportional'

    UNIQUE(group_id, entity_id)
);

-- Intercompany Accounts (for detection)
CREATE TABLE intercompany_accounts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_id INTEGER NOT NULL REFERENCES consolidation_groups(id),

    account_type VARCHAR(20) NOT NULL,   -- 'receivable', 'payable', 'revenue', 'expense'
    account_id INTEGER NOT NULL REFERENCES coa_accounts(id),

    elimination_account_id INTEGER REFERENCES coa_accounts(id),

    UNIQUE(group_id, account_id)
);

-- Intercompany Transaction Matches
CREATE TABLE intercompany_matches (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_id INTEGER NOT NULL REFERENCES consolidation_groups(id),

    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,

    -- Seller side
    seller_entity_id INTEGER NOT NULL REFERENCES organizations(id),
    seller_document_type VARCHAR(20),    -- 'invoice', 'journal'
    seller_document_id INTEGER,
    seller_amount DECIMAL(18,2) NOT NULL,

    -- Buyer side
    buyer_entity_id INTEGER NOT NULL REFERENCES organizations(id),
    buyer_document_type VARCHAR(20),
    buyer_document_id INTEGER,
    buyer_amount DECIMAL(18,2) NOT NULL,

    -- Matching
    amount_difference DECIMAL(18,2),
    confidence_score DECIMAL(5,2),       -- 0-100

    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'confirmed', 'rejected', 'eliminated'

    matched_by_id INTEGER REFERENCES users(id),
    matched_at TIMESTAMP WITH TIME ZONE,

    notes TEXT
);

-- Consolidation Runs
CREATE TABLE consolidation_runs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_id INTEGER NOT NULL REFERENCES consolidation_groups(id),

    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,

    run_type VARCHAR(20) NOT NULL,       -- 'on_demand', 'monthly', 'annual'
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'processing', 'completed', 'approved'

    -- Summary
    entities_count INTEGER,
    total_eliminations DECIMAL(18,2),
    total_nci DECIMAL(18,2),
    forex_adjustment DECIMAL(18,2),

    -- Execution
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    run_by_id INTEGER REFERENCES users(id),
    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    error_log TEXT,

    UNIQUE(group_id, period_year, period_month, run_type)
);

-- Consolidation Elimination Entries
CREATE TABLE consolidation_eliminations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    run_id INTEGER NOT NULL REFERENCES consolidation_runs(id) ON DELETE CASCADE,

    elimination_type VARCHAR(30) NOT NULL, -- 'ic_revenue_expense', 'ic_receivable_payable', 'investment', 'minority_interest', 'forex'

    reference_id INTEGER,                -- Link to intercompany_matches or entity

    account_id INTEGER NOT NULL REFERENCES coa_accounts(id),
    entity_id INTEGER REFERENCES organizations(id),

    debit_amount DECIMAL(18,2) DEFAULT 0,
    credit_amount DECIMAL(18,2) DEFAULT 0,

    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Consolidated Trial Balance (result)
CREATE TABLE consolidated_trial_balance (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    run_id INTEGER NOT NULL REFERENCES consolidation_runs(id) ON DELETE CASCADE,

    account_id INTEGER NOT NULL REFERENCES coa_accounts(id),

    -- Amounts
    combined_amount DECIMAL(18,2),        -- Sum of all entities
    elimination_amount DECIMAL(18,2),     -- IC eliminations
    nci_amount DECIMAL(18,2),             -- Minority interest portion
    forex_amount DECIMAL(18,2),           -- Currency translation
    consolidated_amount DECIMAL(18,2),    -- Final consolidated

    UNIQUE(run_id, account_id)
);

-- Exchange Rates (for forex translation)
CREATE TABLE consolidation_exchange_rates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_id INTEGER NOT NULL REFERENCES consolidation_groups(id),

    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,

    rate_date DATE NOT NULL,
    rate_type VARCHAR(20) NOT NULL,      -- 'closing', 'average', 'historical'

    exchange_rate DECIMAL(18,8) NOT NULL,

    source VARCHAR(50),                  -- 'BI', 'manual'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(group_id, from_currency, to_currency, rate_date, rate_type)
);

-- Indexes
CREATE INDEX idx_ic_matches_period ON intercompany_matches(group_id, period_year, period_month);
CREATE INDEX idx_ic_matches_status ON intercompany_matches(group_id, status);
CREATE INDEX idx_consol_runs_period ON consolidation_runs(group_id, period_year, period_month);
CREATE INDEX idx_consol_tb_run ON consolidated_trial_balance(run_id);
```

### 15.9 Business Rules Configuration

**Soft Rules for Consolidation:**

```json
{
  "rule_code": "CONSOLIDATION_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "default_method": "full",
    "ic_matching_tolerance": 1000,
    "auto_match_confidence_threshold": 95,
    "require_period_close_before_consol": true,
    "allow_on_demand_consolidation": true
  }
},
{
  "rule_code": "CONSOLIDATION_SCHEDULE",
  "rule_type": "mapping",
  "default_value": {
    "monthly_run_day": 10,
    "annual_run_month": 1,
    "annual_run_day": 31,
    "auto_run_monthly": false,
    "notify_on_completion": true
  }
},
{
  "rule_code": "IC_ACCOUNT_MAPPING",
  "rule_type": "list",
  "default_value": [
    {"type": "receivable", "pattern": "1104-%", "elimination": "IC Elimination"},
    {"type": "payable", "pattern": "2104-%", "elimination": "IC Elimination"},
    {"type": "revenue", "pattern": "4900-%", "elimination": "IC Revenue Elim"},
    {"type": "expense", "pattern": "6900-%", "elimination": "IC Expense Elim"}
  ]
},
{
  "rule_code": "FOREX_SETTINGS",
  "rule_type": "mapping",
  "default_value": {
    "rate_source": "BI",
    "closing_rate_for": ["assets", "liabilities"],
    "average_rate_for": ["revenue", "expenses"],
    "historical_rate_for": ["equity"],
    "translation_adjustment_account": "3300-001"
  }
}

---

## Decisions Log (V2)

| # | Topic | Decision | Date |
|---|-------|----------|------|
| 58 | Integration Mode | Real-time (setiap transaksi langsung create journal) | 2025-12-07 |
| 59 | Auto-Post Behavior | Soft rule - configurable per journal type | 2025-12-07 |
| 60 | Audit Trail Level | Everything - semua tabel termasuk config changes | 2025-12-07 |
| 61 | Transaction Immutability | Hard rule - posted journals cannot be edited | 2025-12-07 |
| 62 | Data Retention | Soft rule - configurable per log type | 2025-12-07 |
| 63 | Depreciation Methods | Multiple methods available (SL, DB, SYD, UOP) - user selects per asset | 2025-12-07 |
| 64 | Asset Categories | Fixed categories sesuai standar fiskal PMK 96/2009 | 2025-12-07 |
| 65 | Asset Disposal | Full lifecycle workflow: Propose → Approve → Execute → Post | 2025-12-07 |
| 66 | Asset Revaluation | Mandatory periodic revaluation sesuai PSAK 16, frequency configurable | 2025-12-07 |
| 67 | Inventory Costing Methods | Multiple methods (FIFO, LIFO, Weighted Avg, Specific ID) - per item | 2025-12-07 |
| 68 | Inventory Valuation | Hybrid (Perpetual for fast-moving, Periodic for slow-moving) | 2025-12-07 |
| 69 | Warehouse Structure | Multi-warehouse + Bin/Rack locations (3-level hierarchy) | 2025-12-07 |
| 70 | Physical Count | Both Annual full count + Cycle counting (ABC classification) | 2025-12-07 |
| 71 | Budget Granularity | Full detail (per account + per department + per month) | 2025-12-07 |
| 72 | Budget Versions | Multiple scenarios (Original, Best Case, Worst Case, Revised, Forecast) | 2025-12-07 |
| 73 | Budget Entry Methods | Manual + Excel import + Formula-based | 2025-12-07 |
| 74 | Budget Variance Analysis | Full analysis (YTD, MTD, Trend, Forecast, Drill-down) | 2025-12-07 |
| 75 | Consolidation Scope | Configurable features (Eliminations, Minority Interest, Forex Translation) | 2025-12-07 |
| 76 | Entity Hierarchy | Multi-level (Holding → Sub-holding → Operating → Branch) | 2025-12-07 |
| 77 | Intercompany Detection | Semi-automatic (system detects, user confirms) | 2025-12-07 |
| 78 | Consolidation Frequency | On-demand + Monthly + Annual | 2025-12-07 |

### Contradictions Resolution (Standards Alignment)

| # | Topic | Decision | Date |
|---|-------|----------|------|
| 79 | NUMERIC Precision | Unified `DECIMAL(18,4)` untuk semua monetary values | 2025-12-07 |
| 80 | Data Retention | Perpetual (no auto-delete), archive ke cold storage | 2025-12-07 |
| 81 | Soft Delete Implementation | Both columns: `is_deleted` (query) + `deleted_at` (audit) + `deleted_by_id` | 2025-12-07 |
| 82 | Organization ID for Reference Data | System Organization (org_id=1) untuk global data, semua tabel tetap `org_id NOT NULL` | 2025-12-07 |
| 83 | Period Lock Enforcement | Defense in Depth: Use Case (friendly error) + Database Trigger (safety net) | 2025-12-07 |
| 84 | Atomic Multi-table Operations | UnitOfWork Pattern *(detail implementasi mungkin perlu penyesuaian)* | 2025-12-07 |
| 85 | Hard vs Soft Rules | Developer Settings / Feature Flags untuk toggle behavior *(konsep, detail dibahas nanti)* | 2025-12-07 |
| 86 | Validation Architecture | 2-layer: Pydantic (schema) + Validator Service (business rules) | 2025-12-07 |
| 87 | Action API Endpoints | Verb in URL pattern: `POST /resource/{id}/action` | 2025-12-07 |
| 88 | Caching Strategy | Hybrid: Context-aware TTL + Event-driven invalidation | 2025-12-07 |
| 89 | TimescaleDB for Accounting | Hypertable untuk append-only (balance snapshots, audit log), regular table untuk transactional | 2025-12-07 |
| 90 | Separation of Duties (SOD) | Options B/C/D dicatat *(B: Creator≠Approver, C: SOD Matrix, D: Workflow - detail dibahas nanti)* | 2025-12-07 |
| 91 | Audit Trail Granularity | Field-level audit untuk semua perubahan | 2025-12-07 |
| 92 | Cross-Module References | Shared Kernel pattern: entities umum (journal, COA, periods, users) di shared module | 2025-12-07 |
| 93 | Report Architecture | WYSIWYG pattern: Data Config (system) + Print Config (user customizable) | 2025-12-07 |
| 94 | Multi-Currency Storage | Store all three: original amount + exchange rate + base currency amount | 2025-12-07 |
| 95 | Rounding Rules | Configurable per organization, default round half up, adjustment line untuk distribusi | 2025-12-07 |
| 96 | Concurrent Edit Handling | Hybrid: Optimistic locking default, Pessimistic untuk data kritikal | 2025-12-07 |
| 97 | Batch Processing | Hybrid: Celery background job + Database batch operations | 2025-12-07 |
| 98 | Error Recovery (Batch) | Per-item Atomic: setiap transaksi all-or-nothing, batch boleh partial success | 2025-12-07 |
| 99 | Decimal Calculation Precision | 3-level: Calculation (10 decimal), Storage (4 decimal), Display (0-2 per currency) | 2025-12-07 |

### Shared Code Standards

| # | Topic | Decision | Date |
|---|-------|----------|------|
| 100 | Backend Shared Structure | 9 kategori: config, database, exceptions, contracts, entities, repositories, services, validators, utils, types, middleware | 2025-12-07 |
| 101 | Frontend Shared Structure | 7 kategori: components, hooks, utils, types, constants, api, lib | 2025-12-07 |
| 102 | Base Class Pattern | 2-level inheritance: BaseRepository → DomainBaseRepository → ConcreteRepository | 2025-12-07 |
| 103 | Interface/Contract Pattern | Interface + DTO dalam 1 file per service (self-contained contract) untuk microservice-ready | 2025-12-07 |
| 104 | Naming Convention | I-prefix (interface), Request/Info suffix (DTO), Base prefix (base class), Mixin suffix, snake_case (functions) | 2025-12-07 |
| 105 | Dependency Injection | Hybrid: Constructor DI untuk Use Cases/Services, FastAPI Depends untuk Routes wiring only | 2025-12-07 |

### Owner System & Platform Architecture

| # | Topic | Decision | Date |
|---|-------|----------|------|
| 106 | Tenant Status Lifecycle | 5 status: pending → trial → active → suspended → closed | 2025-12-07 |
| 107 | Trial Period | Configurable per tenant (default 14 days), stored in tenant record | 2025-12-07 |
| 108 | Subscription Model | Hybrid: base fee + per app + per user tier | 2025-12-07 |
| 109 | Billing Cycle | Choice per tenant: monthly atau yearly, stored in tenant record | 2025-12-07 |
| 110 | Organization Hierarchy | 3-level: Holding → Regional → Property (within tenant) | 2025-12-07 |
| 111 | Subscription Granularity | Per App per Sub-organization (bukan per tenant) | 2025-12-07 |
| 112 | Owner Team Roles | 5 roles: super_admin, admin, finance, support, viewer | 2025-12-07 |
| 113 | Data Visibility | Metadata only (tenant info, billing), bukan detail operational/transactional | 2025-12-07 |
| 114 | Feature Tiers | 3-tier per app: Basic, Pro, Enterprise - feature matrix di app_tier_features | 2025-12-07 |
| 115 | Invoice Model | Choice per tenant: per sub-org atau consolidated ke parent | 2025-12-07 |
| 116 | User Multi-Org | 1 user (community account) dapat assignment ke multiple orgs dalam tenant dengan roles berbeda | 2025-12-07 |

---

*Continues from BUSINESS_ACCOUNTING_STANDARDS.md*
