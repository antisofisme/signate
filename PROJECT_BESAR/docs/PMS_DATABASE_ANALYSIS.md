# PMS Hotel Database Analysis

> **Source**: `powerfo.gdb` (Front Office) & `powerbo.gdb` (Back Office)
> **Database Type**: Firebird
> **Analysis Date**: 2025-12-05
> **Purpose**: Reference untuk pengembangan PMS Hotel baru

---

## Overview

Database PMS Hotel ini terbagi menjadi 2 file:

| Database | Size | Focus | Unique Identifiers |
|----------|------|-------|-------------------|
| `powerfo.gdb` | 1.4GB | Front Office Operations | ~18,380 |
| `powerbo.gdb` | 914MB | Back Office / Accounting | ~8,215 |
| **Shared** | - | Common entities | ~3,186 |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PMS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  powerfo.gdb (FRONT OFFICE)        powerbo.gdb (BACK OFFICE)    │
│  ═══════════════════════════       ════════════════════════     │
│  • Reservations (FO_CUST_*)        • General Ledger (GL_)       │
│  • Room Management (FO_ROOM*)      • Accounts Payable (AP_)     │
│  • Guest Management (FO_GUEST*)    • Fixed Assets (FA_)         │
│  • Check-in/Check-out              • Inventory (INV_)           │
│  • Folio & Billing (FO_FOLIO*)     • Bank Book (BB_)            │
│  • Accounts Receivable (AR_)       • Purchasing                 │
│  • Housekeeping (HK_)              • HR/Payroll                 │
│  • Point of Sale (POS_)                                         │
│  • Tenant Management (TN_)                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table Naming Conventions

| Prefix | Module | Description |
|--------|--------|-------------|
| `FO_` | Front Office | Core hotel operations |
| `AR_` | Accounts Receivable | Guest billing, city ledger, aging |
| `AP_` | Accounts Payable | Vendor payments, purchasing |
| `GL_` | General Ledger | Chart of accounts, journal entries |
| `INV_` | Inventory | Stock management, purchasing |
| `FA_` | Fixed Assets | Asset depreciation, tracking |
| `HK_` | Housekeeping | Room cleaning, assignments |
| `POS_` | Point of Sale | Restaurant, outlets |
| `TN_` | Tenant | Long-stay/apartment management |
| `BB_` | Bank Book | Cash management, reconciliation |
| `BQ_` | Banquet | Event & meeting management |

### Common Suffixes

| Suffix | Meaning |
|--------|---------|
| `_BI` | Before Insert (trigger/log) |
| `_BU` | Before Update (trigger/log) |
| `_AI` | After Insert (trigger/log) |
| `_AU` | After Update (trigger/log) |
| `_IDX_` | Index |
| `_FK_` | Foreign Key |
| `_RPT_` | Report |
| `_HIST_` | History |
| `_LOG` | Audit Log |
| `_JUR` | Journal Entry |

---

## Core Modules Detail

### 1. ROOM MANAGEMENT

**Key Tables:**
- `FO_ROOM` - Room master data
- `FO_ROOMTYPE` - Room type definitions
- `FO_ROOM_STATUS` - Current room status
- `FO_ROOMRATE` - Room rates
- `FO_FLOORPLAN` - Floor layout
- `FO_FLOOR_BLOCK` - Floor blocking

**Key Fields Identified:**
```
ROOM, ROOMNO, ROOMNUMBER, ROOM_NUMBER
ROOMTYPE, RTYPE, ROOM_TYPE
ROOMSTATUS, ROOM_STATUS, ROOM_STAT
ROOMRATE, RATE_ROOM
FLOOR, FLOORPLAN, FLOOR_BLOCK
BED, EXTRA_BED, BED_TYPE
```

**Room Status Values (likely):**
- Vacant Clean (VC)
- Vacant Dirty (VD)
- Occupied Clean (OC)
- Occupied Dirty (OD)
- Out of Order (OOO)
- Out of Service (OOS)

---

### 2. RESERVATION / BOOKING

**Key Tables:**
- `FO_CUST_ALLOTMENT` - Room allotments/blocks
- `FO_CUST_ALLOTMENT_DRILL` - Allotment details
- `FO_RPT_RESERVATION_DAILY` - Daily reservation report
- `FO_STAT_ALLOTMENT` - Allotment statistics

**Key Fields:**
```
RESERVATION, RSV, BOOK, BOOKING
ALLOTMENT, ALLOTED, ALLOTMENT_COUNT
ARRIVAL, DATECI, CHECKIN
DEPARTURE, DATECO, CHECKOUT
NIGHT, ROOMNIGHT, ACTUAL_NIGHT
PAX, ADULT, CHILD
```

**Reservation Status (likely):**
- Tentative
- Confirmed
- Guaranteed
- Waitlist
- Cancelled
- No-Show

---

### 3. GUEST MANAGEMENT

**Key Tables:**
- `FO_GUEST` - Guest in-house
- `FO_CUST_*` - Customer/Company master
- `AR_CUSTOMER` - AR customer accounts
- `FO_CUST_CONTACT` - Contact persons
- `FO_CUST_RATE` - Contracted rates
- `FO_CUST_ROOM_NIGHT` - Room night history

**Guest Types:**
```
GUEST - Individual guest
CUST/CUSTOMER - Company/Corporate
MEMBER - Loyalty member
VIP - VIP guest (VIP1-VIP5 levels)
AGENT - Travel agent
SOURCE - Booking source
SEGMENT - Market segment
```

**Key Fields:**
```
GUESTNAME, GUEST_NAME
PAX, ADULT_PAX, CHILD_PAX
MEMBER, MEMBERTYPE, MEMBERSHIP
VIP, VIP_LEVEL
NATION, NATIONALITY, COUNTRY
COMPANY, COMPANYNAME
```

---

### 4. FOLIO & BILLING

**Key Tables:**
- `FO_FOLIO` - Guest folio master
- `FO_FOLIOSTATUS` - Folio status
- `FO_JUR_*` - Folio journal entries
- `FO_RATE_FOLIO` - Rate applied to folio
- `FO_RPT_FOLIO` - Folio reports

**Folio Types:**
```
FOLIO - Main guest folio
MASTER_FOLIO - Group master
SPLIT_FOLIO - Split billing
CITY_LEDGER - Transfer to AR
```

**Key Fields:**
```
FOLIO, FOLIO_NO, FOLIONUMBER
FOLIOSTATUS, FOLIO_STATUS
CHARGE, POST, POSTING
DEBIT, CREDIT, BALANCE
JOURNAL, JOURNAL_LINE
```

**Transaction Types:**
```
ROOM_CHARGE - Room rate posting
PACKAGE - Package inclusions
OUTLET - F&B, Spa, etc.
PHONE - Telephone charges
MINIBAR - Minibar consumption
LAUNDRY - Laundry service
TAX - Tax charges
SERVICE - Service charge
DISCOUNT - Discounts
ADJUSTMENT - Corrections
PAYMENT - Payments received
TRANSFER - Transfer to other folio
```

---

### 5. RATE & PACKAGE MANAGEMENT

**Key Tables:**
- `FO_RATECODE` - Rate code master
- `FO_CUST_RATE` - Customer contracted rates
- `FO_RATE_CHART` - Rate chart/calendar
- `FO_RATE_CHART_YIELD` - Yield management
- `FO_RATE_GUEST` - Applied guest rates
- `FO_JUR_PACKAGE_ALLOWANCE` - Package allowances

**Key Fields:**
```
RATE, RATECODE, RATE_CODE
RATE_AMOUNT, ROOMRATE
PACKAGE, PKG, PACKAGE_CODE
TARIF, TARIFF, PRICE
DISCOUNT, RATE_DISCOUNT
COMMISSION
```

**Rate Structure:**
```
BASE_RATE - Published rate
CONTRACT_RATE - Negotiated rate
PACKAGE_RATE - Inclusive packages
SEASONAL_RATE - Seasonal pricing
YIELD_RATE - Dynamic pricing
```

---

### 6. CHECK-IN / CHECK-OUT

**Key Tables:**
- `FO_ARRIVAL` - Expected arrivals
- `FO_DEPARTURE` - Expected departures
- `FO_RPT_HIST_ARRIVAL` - Arrival history
- `FO_RPT_HIST_DEPARTURE` - Departure history

**Key Fields:**
```
CHECKIN, CHECK_IN, DATECI, DATECI_ACTUAL
CHECKOUT, CHECK_OUT, DATECO, DATECO_ACTUAL
ARRIVAL, ARRIVAL_DATE, ARRIVAL_TIME
DEPARTURE, DEPARTURE_DATE
EARLY_CHECKIN, LATE_CHECKOUT
```

**Timing Fields:**
```
DATECI - Scheduled check-in date
DATECI_ACTUAL - Actual check-in datetime
DATECI_TIME - Check-in time
DATECO - Scheduled check-out date
DATECO_ACTUAL - Actual check-out datetime
```

---

### 7. PAYMENT PROCESSING

**Key Tables:**
- `AR_CASH` - Cash payments
- `AR_CARD` - Credit card payments
- `AR_CARD_BATCH` - Card settlement batches
- `AR_DEPOSIT` - Deposits/Advances
- `AR_CHECK_*` - Check payments

**Payment Methods:**
```
CASH - Cash payment
CARD/CREDIT_CARD - Credit card
DEPOSIT - Advance deposit
VOUCHER - Vouchers
CITY_LEDGER - Bill to company
TRANSFER - Bank transfer
```

**Key Fields:**
```
PAYMENT, PAYMENT_DATE, PAYMENT_AMOUNT
CASH, CASH_AMOUNT
CARD, CARD_NUMBER, CARD_TYPE
DEPOSIT, ADVANCE, PREPAYMENT
SETTLEMENT, RECONCILE
```

---

### 8. ACCOUNTS RECEIVABLE (City Ledger)

**Key Tables:**
- `AR_*` - All AR tables (155+ in FO)
- `AR_AGING` - Aging analysis
- `AR_AGING_SUMMARY` - Aging summary
- `AR_INVOICE` - AR invoices
- `AR_JOURNAL` - AR journals

**Key Concepts:**
```
CITY_LEDGER - Company credit accounts
AGING - Outstanding by age (30/60/90 days)
INVOICE - Billing documents
CREDIT_LIMIT - Customer credit limit
DEPOSIT - Customer deposits
STATEMENT - Account statements
```

**Aging Buckets:**
```
CURRENT - 0-30 days
AGING_30 - 31-60 days
AGING_60 - 61-90 days
AGING_90 - Over 90 days
```

---

### 9. HOUSEKEEPING

**Key Tables:**
- `HK_ASSIGN` - Housekeeping assignments
- `HK_ASSIGN_ROOM` - Room assignments
- `HK_ITEM` - Housekeeping items/amenities
- `HK_ITEM_ROOMTYPE` - Items per room type
- `HK_CREDITPOINT` - Performance points
- `FO_RPT_HK_WKS` - HK worksheets

**Room Status:**
```
CLEAN - Clean room
DIRTY - Dirty room
INSPECTED - Inspected
OOO - Out of Order
OOS - Out of Service
```

**Key Fields:**
```
ROOMBOY, ATTENDANT, MAID
ASSIGN, ASSIGNMENT
CLEANING, CLEAN_STATUS
INSPECTION, INSPECTED_BY
CREDITPOINT - Performance metric
```

---

### 10. POINT OF SALE (Outlets)

**Key Tables:**
- `POS_*` - POS tables
- `FO_INFO_PHONE` - Phone call charges
- `AR_CARD_OUTLET` - Outlet card transactions

**Outlet Types:**
```
RESTAURANT/RESTO - F&B outlets
SPA - Spa services
LAUNDRY - Laundry service
MINIBAR - In-room minibar
PHONE/PBX - Telephone charges
BUSINESS_CENTER - Business services
```

**Key Fields:**
```
OUTLET, OUTLET_ID, OUTLET_CODE
POS_AMOUNT, POS_QTY
CATEGORY, ITEM
REVENUE, COST
```

---

### 11. REPORTS & STATISTICS

**Key Tables:**
- `FO_RPT_*` - Front office reports
- `AR_RPT_*` - AR reports
- `FO_HIST_ZRS_DAILY` - Daily statistics
- `FO_STAT_*` - Statistics tables

**Common Reports:**
```
DAILY_REPORT - Manager's daily report
ROOM_STATISTICS - Occupancy stats
REVENUE_REPORT - Revenue analysis
GUEST_LEDGER - In-house guest balances
CITY_LEDGER - AR aging
CASHIER_REPORT - Shift reports
NIGHT_AUDIT - End of day reports
FORECAST - Future projections
```

**Key Statistics:**
```
OCCUPANCY, OCC_PERCENT
ADR - Average Daily Rate
REVPAR - Revenue per Available Room
ROOMNIGHT - Room nights sold
PAX - Guest count
REVENUE - Total revenue
```

---

## Business Flows

### 1. Reservation Flow

```
INQUIRY
    │
    ▼
AVAILABILITY CHECK ──────────────────────┐
    │                                    │
    ▼                                    ▼
BOOKING/RESERVATION              ALLOTMENT (Group)
    │                                    │
    ├── Tentative                        │
    ├── Confirmed                        │
    └── Guaranteed                       │
    │                                    │
    ▼                                    │
CONFIRMATION ◄───────────────────────────┘
    │
    ▼
PRE-ARRIVAL
    │
    ├── Deposit Collection
    ├── Room Assignment
    └── Rate Confirmation
    │
    ▼
ARRIVAL ──────────────────────────────────►  (Continue to Check-in)
```

### 2. Check-in Flow

```
ARRIVAL
    │
    ▼
REGISTRATION
    │
    ├── Guest Profile (new/existing)
    ├── ID Verification
    ├── Rate Confirmation
    └── Payment Method
    │
    ▼
ROOM ASSIGNMENT
    │
    ├── Room Selection
    ├── Room Status Check (must be CLEAN)
    └── Key Issuance
    │
    ▼
FOLIO CREATION
    │
    ├── Main Folio
    ├── Split Folio (if needed)
    └── Routing Instructions
    │
    ▼
CHECK-IN COMPLETE
    │
    └── Room Status → OCCUPIED
```

### 3. In-House Operations

```
                    ┌─────────────────┐
                    │   GUEST FOLIO   │
                    └────────┬────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
    ▼                        ▼                        ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ ROOM CHARGES │      │   OUTLETS    │      │   EXTRAS     │
│              │      │              │      │              │
│ • Daily Rate │      │ • Restaurant │      │ • Phone      │
│ • Package    │      │ • Spa        │      │ • Minibar    │
│ • Extra Bed  │      │ • Laundry    │      │ • Movies     │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  POSTING TO     │
                    │     FOLIO       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  TAX & SERVICE  │
                    │   CALCULATION   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ RUNNING BALANCE │
                    └─────────────────┘
```

### 4. Check-out Flow

```
DEPARTURE REQUEST
    │
    ▼
FOLIO REVIEW
    │
    ├── All charges posted?
    ├── Minibar check
    ├── Late checkout charges
    └── Package reconciliation
    │
    ▼
SETTLEMENT
    │
    ├── Cash Payment ────────► AR_CASH
    ├── Credit Card ─────────► AR_CARD
    ├── City Ledger ─────────► AR_CUSTOMER (Invoice)
    └── Split Payment ───────► Multiple methods
    │
    ▼
ZERO BALANCE
    │
    ▼
CHECK-OUT COMPLETE
    │
    ├── Folio Print
    ├── Room Status → DIRTY
    └── Guest History Update
    │
    ▼
HOUSEKEEPING NOTIFICATION
```

### 5. Night Audit Flow

```
END OF DAY TRIGGER
    │
    ▼
┌─────────────────────────────────────────┐
│           NIGHT AUDIT PROCESS           │
├─────────────────────────────────────────┤
│                                         │
│  1. POSTING ROOM CHARGES                │
│     ├── Calculate room rates            │
│     ├── Apply packages                  │
│     ├── Calculate tax & service         │
│     └── Post to all in-house folios     │
│                                         │
│  2. VERIFICATION                        │
│     ├── Balance check                   │
│     ├── Unposted transactions           │
│     └── Credit limit warnings           │
│                                         │
│  3. GENERATE REPORTS                    │
│     ├── Manager's Report                │
│     ├── Revenue Summary                 │
│     ├── Occupancy Statistics            │
│     ├── Guest Ledger                    │
│     └── City Ledger Aging               │
│                                         │
│  4. SYSTEM DATE ROLLOVER                │
│     ├── Close business date             │
│     ├── Archive daily data              │
│     └── Advance to next day             │
│                                         │
│  5. GL INTERFACE                        │
│     └── Post to General Ledger          │
│                                         │
└─────────────────────────────────────────┘
    │
    ▼
NEW BUSINESS DAY
```

### 6. AR/City Ledger Flow

```
CHECK-OUT TO CITY LEDGER
    │
    ▼
AR ACCOUNT CREATION
    │
    ├── Customer Code
    ├── Credit Limit
    └── Payment Terms
    │
    ▼
INVOICE GENERATION
    │
    ├── Invoice Number
    ├── Due Date
    └── Folio Attachment
    │
    ▼
AGING TRACKING
    │
    ├── Current (0-30 days)
    ├── 30 Days
    ├── 60 Days
    └── 90+ Days
    │
    ▼
COLLECTION
    │
    ├── Payment Receipt
    ├── Apply to Invoice
    └── Balance Update
    │
    ▼
RECONCILIATION
```

---

## Data Relationships (ERD Simplified)

```
┌─────────────────┐       ┌─────────────────┐
│   FO_ROOMTYPE   │       │   FO_RATECODE   │
│                 │       │                 │
│ • roomtype_id   │       │ • ratecode_id   │
│ • name          │       │ • code          │
│ • max_pax       │       │ • description   │
│ • base_rate     │       │ • amount        │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │ 1:N                     │ 1:N
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│    FO_ROOM      │       │  FO_CUST_RATE   │
│                 │       │                 │
│ • room_id       │◄──────│ • customer_id   │
│ • room_number   │       │ • ratecode_id   │
│ • roomtype_id   │       │ • valid_from    │
│ • floor         │       │ • valid_to      │
│ • status        │       │ • amount        │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │                         │
         │           ┌─────────────┘
         │           │
         ▼           ▼
┌─────────────────────────────────┐
│           FO_FOLIO              │
│                                 │
│ • folio_id                      │
│ • folio_number                  │
│ • guest_id ────────────────────►│ FO_GUEST
│ • room_id                       │
│ • customer_id ─────────────────►│ AR_CUSTOMER
│ • ratecode_id                   │
│ • checkin_date                  │
│ • checkout_date                 │
│ • status                        │
│ • balance                       │
└────────┬────────────────────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────────────────────┐
│        FO_FOLIO_TRANS           │
│      (Journal/Posting)          │
│                                 │
│ • trans_id                      │
│ • folio_id                      │
│ • trans_date                    │
│ • trans_code                    │
│ • description                   │
│ • debit                         │
│ • credit                        │
│ • outlet_id                     │
└─────────────────────────────────┘
         │
         │ Settlement
         │
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    AR_CASH      │  │    AR_CARD      │  │  AR_CUSTOMER    │
│                 │  │                 │  │  (City Ledger)  │
│ • Cash payments │  │ • Card payments │  │ • Invoices      │
│ • Receipt no    │  │ • Batch settle  │  │ • Aging         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Key Business Rules (Inferred)

### Room Management
1. Room dapat di-assign hanya jika status CLEAN/READY
2. OOO (Out of Order) tidak dihitung dalam inventory
3. OOS (Out of Service) masih dihitung inventory tapi tidak bisa dijual

### Reservation
1. Overbooking control berdasarkan roomtype
2. Allotment memiliki release date
3. No-show dapat di-charge sesuai policy

### Folio & Billing
1. Semua charge harus di-post ke folio sebelum checkout
2. Folio balance harus ZERO untuk checkout
3. City Ledger transfer memerlukan customer account

### Night Audit
1. Wajib dijalankan setiap hari
2. Room charge auto-post untuk semua in-house guest
3. System date tidak bisa rollback

### AR/City Ledger
1. Credit limit check sebelum transfer ke AR
2. Aging calculated berdasarkan invoice date
3. Payment apply ke invoice tertua (FIFO)

---

## Mapping to New Architecture

### Proposed Module Structure

```
backend-python/
├── services/
│   ├── auth/              # Existing
│   ├── organization/      # Existing (multi-tenant)
│   ├── user/              # Existing
│   │
│   ├── pms/               # NEW - PMS Core
│   │   ├── room/          # Room management
│   │   ├── roomtype/      # Room type config
│   │   ├── rate/          # Rate management
│   │   ├── guest/         # Guest profiles
│   │   ├── reservation/   # Bookings
│   │   ├── folio/         # Billing
│   │   ├── housekeeping/  # HK operations
│   │   └── night_audit/   # EOD processing
│   │
│   ├── pos/               # NEW - Point of Sale
│   │   ├── outlet/        # Outlet config
│   │   ├── menu/          # Menu items
│   │   └── transaction/   # POS transactions
│   │
│   ├── accounting/        # NEW - Back Office
│   │   ├── ar/            # Accounts Receivable
│   │   ├── ap/            # Accounts Payable
│   │   ├── gl/            # General Ledger
│   │   └── cashier/       # Cash management
│   │
│   └── reporting/         # NEW - Reports
│       ├── daily/         # Daily reports
│       ├── statistics/    # Statistics
│       └── financial/     # Financial reports
```

### Priority Implementation Order

1. **Phase 1: Room & Rate Setup**
   - Room Types
   - Room Inventory
   - Rate Codes
   - Rate Calendar

2. **Phase 2: Reservation**
   - Individual Booking
   - Group Booking
   - Allotment

3. **Phase 3: Front Desk**
   - Check-in
   - In-house Management
   - Check-out

4. **Phase 4: Billing**
   - Folio Management
   - Posting
   - Payment Processing

5. **Phase 5: Night Audit**
   - Room Charge Posting
   - Reports
   - Day Close

6. **Phase 6: AR/City Ledger**
   - Customer Accounts
   - Invoicing
   - Aging

7. **Phase 7: Back Office**
   - General Ledger
   - AP
   - Reports

---

## Notes

### Limitations of This Analysis
- Extracted from binary database using string patterns
- Actual table structures need Firebird client to verify
- Foreign key relationships are inferred
- Some field names may be column names vs table names

### To Get Complete Schema
```bash
# Install Firebird client
apt-get install firebird3.0-utils

# Connect and extract schema
isql-fb -u SYSDBA -p masterkey /path/to/database.gdb

# In isql:
SHOW TABLES;
SHOW TABLE tablename;
```

### Recommendations
1. Keep this document as reference
2. Build new tables following our naming conventions
3. Map old concepts to new architecture
4. Don't try to replicate exact structure - modernize it

---

*Document generated from database analysis on 2025-12-05*
