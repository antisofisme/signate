# Enterprise Hospitality Platform Vision

> Visi platform enterprise untuk industri hospitality yang terintegrasi penuh.
>
> **Created**: 2025-12-05
> **Status**: Planning

---

## Executive Summary

Platform enterprise yang menghubungkan **semua stakeholder** dalam ekosistem hospitality:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENTERPRISE HOSPITALITY PLATFORM                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │   GUESTS    │   │  EMPLOYEES  │   │  SUPPLIERS  │   │   OWNERS    │     │
│  │   (Tamu)    │   │ (Karyawan)  │   │ (Pemasok)   │   │  (Pemilik)  │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│         │                 │                 │                 │             │
│         ▼                 ▼                 ▼                 ▼             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │  Guest App  │   │ Employee    │   │  Supplier   │   │  Owner      │     │
│  │  (Mobile)   │   │ Portal      │   │  Portal     │   │  Dashboard  │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│         │                 │                 │                 │             │
│         └────────────┬────┴────────────┬────┴────────────┬────┘             │
│                      │                 │                 │                  │
│                      ▼                 ▼                 ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SHARED BACKEND (FastAPI)                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  Auth   │ │  User   │ │  Org    │ │  RBAC   │ │  Audit  │       │   │
│  │  │ Service │ │ Service │ │ Service │ │ Service │ │ Service │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SHARED DATABASE                              │   │
│  │                    (PostgreSQL + Redis + S3)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Applications Overview

### A. Customer-Facing Applications

#### 1. Guest App (Aplikasi Tamu)
**Target User**: Tamu hotel, pelanggan F&B, member loyalty

```
┌─────────────────────────────────────────┐
│            GUEST APP                     │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  Booking &  │  │   Loyalty   │      │
│  │  Reservasi  │  │  & Points   │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │   Online    │  │   Digital   │      │
│  │  Check-in   │  │  Room Key   │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │    F&B      │  │   Service   │      │
│  │   Order     │  │   Request   │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │   Invoice   │  │   Feedback  │      │
│  │  & Payment  │  │   & Review  │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
- **Booking & Reservation**: Book room, lihat availability, manage reservations
- **Loyalty Program**: View points, tier status, redeem rewards, member benefits
- **Online Check-in/out**: Pre-arrival check-in, express checkout
- **Digital Room Key**: Mobile key untuk buka pintu kamar
- **F&B Ordering**: Order food dari restaurant/room service via app
- **Service Request**: Request amenities, housekeeping, maintenance
- **Invoice & Payment**: View bill, make payment, split bill
- **Feedback & Review**: Rate stay, submit feedback, NPS survey

**Loyalty/Leveling System:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    GUEST LOYALTY TIERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BRONZE (0-999 pts)     SILVER (1K-4,999)    GOLD (5K-14,999)  │
│  ┌─────────────┐        ┌─────────────┐      ┌─────────────┐   │
│  │ Basic       │        │ 5% Discount │      │ 10% Discount│   │
│  │ Member      │   →    │ Early       │  →   │ Room        │   │
│  │ Benefits    │        │ Check-in    │      │ Upgrade     │   │
│  └─────────────┘        └─────────────┘      └─────────────┘   │
│                                                                 │
│  PLATINUM (15K-49,999)         DIAMOND (50K+)                  │
│  ┌─────────────┐               ┌─────────────┐                 │
│  │ 15% Discount│               │ 20% Discount│                 │
│  │ Lounge      │       →       │ Suite       │                 │
│  │ Access      │               │ Upgrade     │                 │
│  │ Late C/O    │               │ Personal    │                 │
│  └─────────────┘               │ Concierge   │                 │
│                                └─────────────┘                 │
│                                                                 │
│  Points Earning:                                               │
│  • Room: 10 pts/USD spent                                      │
│  • F&B: 5 pts/USD spent                                        │
│  • Spa: 5 pts/USD spent                                        │
│  • Bonus: Birthday 2x, Anniversary 3x                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 2. Supplier Portal (Portal Supplier)
**Target User**: Vendor, supplier, distributor

```
┌─────────────────────────────────────────┐
│          SUPPLIER PORTAL                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  Product    │  │   Price     │      │
│  │  Catalog    │  │   List      │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  Purchase   │  │  Delivery   │      │
│  │  Orders     │  │  Schedule   │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  Invoice &  │  │  Payment    │      │
│  │  Billing    │  │  History    │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  Their Own  │  │   Reports   │      │
│  │  Employees  │  │ & Analytics │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
- **Product Catalog**: Manage products, update specs, upload images
- **Price List**: Set prices, bulk discounts, contract prices
- **Purchase Orders**: Receive POs, confirm, update status
- **Delivery Schedule**: Set delivery dates, track shipments
- **Invoice & Billing**: Submit invoices, track payment status
- **Payment History**: View payment history, download statements
- **Supplier's Employees**: Manage their own staff who handle our account
- **Reports**: Sales reports, order history, performance metrics

**Supplier Employee Management:**
```
┌─────────────────────────────────────────────────────────────────┐
│              SUPPLIER'S OWN EMPLOYEE ACCESS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Supplier Company: PT Sumber Makmur                            │
│  ├── Admin (Full Access)                                       │
│  │   └── Can manage all, invite employees                      │
│  │                                                             │
│  ├── Sales Rep (Sales Access)                                  │
│  │   └── Can view orders, update catalog, respond to RFQ       │
│  │                                                             │
│  ├── Finance (Finance Access)                                  │
│  │   └── Can submit invoices, view payments                    │
│  │                                                             │
│  └── Delivery (Logistics Access)                               │
│      └── Can update delivery status, confirm receipt           │
│                                                                 │
│  Benefit:                                                      │
│  • Supplier tidak perlu buat sistem sendiri                    │
│  • Data terintegrasi langsung dengan hotel                     │
│  • Real-time order tracking                                    │
│  • Paperless transactions                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### B. Internal Operations Applications

#### 3. PMS (Property Management System)
**Target User**: Front Office, Reservations, Cashier

**Modules:**
- Room Management
- Reservations
- Guest Check-in/Check-out
- Billing & Folio
- Night Audit
- Guest Profiles
- Rate Management

---

#### 4. HRM (Human Resource Management)
**Target User**: HR, Department Heads, Employees

```
┌─────────────────────────────────────────┐
│              HRM SYSTEM                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        EMPLOYEE DATABASE         │   │
│  ├─────────────────────────────────┤   │
│  │ • Personal Info                 │   │
│  │ • Employment History            │   │
│  │ • Documents (KTP, NPWP, etc)    │   │
│  │ • Emergency Contacts            │   │
│  │ • Skills & Certifications       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │          ATTENDANCE              │   │
│  ├─────────────────────────────────┤   │
│  │ • Clock In/Out (Mobile/Web)     │   │
│  │ • Shift Scheduling              │   │
│  │ • Overtime Tracking             │   │
│  │ • Leave Management              │   │
│  │ • Attendance Reports            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │           PAYROLL                │   │
│  ├─────────────────────────────────┤   │
│  │ • Salary Structure              │   │
│  │ • Allowances & Deductions       │   │
│  │ • Tax Calculation (PPh 21)      │   │
│  │ • BPJS Ketenagakerjaan          │   │
│  │ • BPJS Kesehatan                │   │
│  │ • THR & Bonus                   │   │
│  │ • Payslip Generation            │   │
│  │ • Bank Transfer Integration     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       PERFORMANCE & KPI          │   │
│  ├─────────────────────────────────┤   │
│  │ • Goal Setting (OKR)            │   │
│  │ • Performance Reviews           │   │
│  │ • 360 Feedback                  │   │
│  │ • Training Records              │   │
│  │ • Career Development            │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Employee Leveling System:**
```
┌─────────────────────────────────────────────────────────────────┐
│                 EMPLOYEE GRADE & LEVEL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Grade 1-3: Staff Level                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Trainee      → 2. Junior Staff  → 3. Senior Staff   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Grade 4-6: Supervisory Level                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 4. Supervisor   → 5. Asst. Manager → 6. Manager        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Grade 7-9: Executive Level                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 7. Sr. Manager  → 8. Director      → 9. VP/C-Level     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Each grade has:                                               │
│  • Salary range (min-mid-max)                                  │
│  • Benefits package                                            │
│  • Authority level                                             │
│  • Approval limits                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 5. SCM (Supply Chain Management) / Procurement
**Target User**: Purchasing, Receiving, Warehouse

```
┌─────────────────────────────────────────┐
│         PROCUREMENT SYSTEM               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      PURCHASE REQUISITION        │   │
│  ├─────────────────────────────────┤   │
│  │ • Department Request (PR)       │   │
│  │ • Budget Check                  │   │
│  │ • Approval Workflow             │   │
│  │ • Convert to PO                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        PURCHASE ORDER            │   │
│  ├─────────────────────────────────┤   │
│  │ • Vendor Selection              │   │
│  │ • Price Comparison              │   │
│  │ • PO Generation                 │   │
│  │ • Send to Supplier              │   │
│  │ • Track Delivery                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │           RECEIVING              │   │
│  ├─────────────────────────────────┤   │
│  │ • Goods Receipt Note (GRN)      │   │
│  │ • Quality Check                 │   │
│  │ • Variance Report               │   │
│  │ • Auto-update Inventory         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       VENDOR MANAGEMENT          │   │
│  ├─────────────────────────────────┤   │
│  │ • Vendor Database               │   │
│  │ • Performance Rating            │   │
│  │ • Contract Management           │   │
│  │ • Price History                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Procurement Workflow:**
```
┌─────────────────────────────────────────────────────────────────┐
│                  PROCUREMENT WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Department              Purchasing           Supplier          │
│      │                       │                    │             │
│      │  1. Create PR         │                    │             │
│      │──────────────────────▶│                    │             │
│      │                       │                    │             │
│      │  2. Approve/Reject    │                    │             │
│      │◀──────────────────────│                    │             │
│      │                       │                    │             │
│      │                       │  3. Create PO      │             │
│      │                       │───────────────────▶│             │
│      │                       │                    │             │
│      │                       │  4. Confirm PO     │             │
│      │                       │◀───────────────────│             │
│      │                       │                    │             │
│      │                       │  5. Delivery       │             │
│      │                       │◀───────────────────│             │
│      │                       │                    │             │
│      │  6. GRN               │  6. Invoice        │             │
│      │◀──────────────────────│◀───────────────────│             │
│      │                       │                    │             │
│      │                       │  7. Payment        │             │
│      │                       │───────────────────▶│             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 6. POS (Point of Sale)
**Target User**: F&B Outlets, Retail, Spa

```
┌─────────────────────────────────────────┐
│            POS SYSTEM                    │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │ Restaurant  │  │    Bar &    │      │
│  │    POS      │  │   Lounge    │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │    Room     │  │  Minibar    │      │
│  │  Service    │  │   Posting   │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │    Spa &    │  │   Retail    │      │
│  │  Wellness   │  │    Shop     │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  Features:                              │
│  • Menu Management                      │
│  • Table Management                     │
│  • Kitchen Display System (KDS)         │
│  • Split Bill                           │
│  • Post to Room Folio                   │
│  • Multiple Payment Methods             │
│  • Inventory Deduction                  │
│  • Sales Reports                        │
│                                         │
└─────────────────────────────────────────┘
```

---

#### 7. Online Menu & Ordering
**Target User**: Guests, Walk-in Customers

```
┌─────────────────────────────────────────┐
│         ONLINE MENU SYSTEM               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        QR CODE MENU              │   │
│  ├─────────────────────────────────┤   │
│  │ • Scan QR at table              │   │
│  │ • Browse digital menu           │   │
│  │ • View photos & descriptions    │   │
│  │ • Filter by dietary (vegan,     │   │
│  │   halal, gluten-free)           │   │
│  │ • Multi-language                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        SELF-ORDERING             │   │
│  ├─────────────────────────────────┤   │
│  │ • Add items to cart             │   │
│  │ • Customize (spicy level, etc)  │   │
│  │ • Special requests              │   │
│  │ • Submit order                  │   │
│  │ • Track order status            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         PAYMENT                  │   │
│  ├─────────────────────────────────┤   │
│  │ • Pay at table (cashless)       │   │
│  │ • Post to room folio            │   │
│  │ • Split bill                    │   │
│  │ • Use loyalty points            │   │
│  │ • Digital receipt               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Integration:                           │
│  • → POS (order sent)                  │
│  • → KDS (kitchen display)             │
│  • → Inventory (stock deduction)       │
│  • → PMS (room charge)                 │
│  • → Loyalty (points earned)           │
│                                         │
└─────────────────────────────────────────┘
```

---

#### 8. Inventory Management
**Target User**: Warehouse, Cost Control, Outlets

```
┌─────────────────────────────────────────┐
│        INVENTORY MANAGEMENT              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │          STOCK CONTROL           │   │
│  ├─────────────────────────────────┤   │
│  │ • Item Master Database          │   │
│  │ • Multiple Warehouses           │   │
│  │ • Stock Levels (Min/Max/Reorder)│   │
│  │ • Batch/Lot Tracking            │   │
│  │ • Expiry Date Tracking          │   │
│  │ • Serial Number Tracking        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       STOCK MOVEMENTS            │   │
│  ├─────────────────────────────────┤   │
│  │ • Goods Receipt (from PO)       │   │
│  │ • Stock Transfer (antar gudang) │   │
│  │ • Stock Issue (to department)   │   │
│  │ • Stock Return                  │   │
│  │ • Stock Adjustment              │   │
│  │ • Stock Opname (Physical Count) │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │          COSTING                 │   │
│  ├─────────────────────────────────┤   │
│  │ • FIFO / LIFO / Average Cost    │   │
│  │ • Recipe Costing (F&B)          │   │
│  │ • Cost of Goods Sold (COGS)     │   │
│  │ • Variance Analysis             │   │
│  │ • Cost Reports                  │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

#### 9. Asset Management
**Target User**: Engineering, Finance, IT

```
┌─────────────────────────────────────────┐
│         ASSET MANAGEMENT                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        ASSET REGISTER            │   │
│  ├─────────────────────────────────┤   │
│  │ • Asset Master Database         │   │
│  │ • Categories (FF&E, IT, Vehicle)│   │
│  │ • Location Tracking             │   │
│  │ • Custodian Assignment          │   │
│  │ • QR Code/Barcode Labels        │   │
│  │ • Photos & Documents            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        DEPRECIATION              │   │
│  ├─────────────────────────────────┤   │
│  │ • Acquisition Cost              │   │
│  │ • Useful Life                   │   │
│  │ • Depreciation Method           │   │
│  │   (Straight-line, DB, SYD)      │   │
│  │ • Monthly Depreciation Run      │   │
│  │ • Book Value Tracking           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │     MAINTENANCE SCHEDULE         │   │
│  ├─────────────────────────────────┤   │
│  │ • Preventive Maintenance        │   │
│  │ • Service History               │   │
│  │ • Warranty Tracking             │   │
│  │ • Maintenance Costs             │   │
│  │ • Work Orders                   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        ASSET LIFECYCLE           │   │
│  ├─────────────────────────────────┤   │
│  │ • Acquisition                   │   │
│  │ • Transfer                      │   │
│  │ • Revaluation                   │   │
│  │ • Disposal/Write-off            │   │
│  │ • Audit Trail                   │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

#### 10. Digital Signage (CMS)
**Target User**: Marketing, Front Office

**Already Built** - See current `cms-vite` and `player-vite`

Features:
- Content Management (images, videos)
- Playlist Builder
- Device Management
- Scheduling
- Real-time Updates

---

#### 11. Accounting / Finance
**Target User**: Finance, Accounting

```
┌─────────────────────────────────────────┐
│         ACCOUNTING SYSTEM                │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       GENERAL LEDGER             │   │
│  ├─────────────────────────────────┤   │
│  │ • Chart of Accounts             │   │
│  │ • Journal Entries               │   │
│  │ • Trial Balance                 │   │
│  │ • Financial Statements          │   │
│  │ • Multi-currency                │   │
│  │ • Multi-company consolidation   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      ACCOUNTS RECEIVABLE         │   │
│  ├─────────────────────────────────┤   │
│  │ • City Ledger                   │   │
│  │ • Invoice Generation            │   │
│  │ • Payment Receipt               │   │
│  │ • Aging Report                  │   │
│  │ • Collection Tracking           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       ACCOUNTS PAYABLE           │   │
│  ├─────────────────────────────────┤   │
│  │ • Vendor Invoices               │   │
│  │ • Payment Scheduling            │   │
│  │ • Payment Processing            │   │
│  │ • Aging Report                  │   │
│  │ • Bank Reconciliation           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         BUDGETING                │   │
│  ├─────────────────────────────────┤   │
│  │ • Annual Budget                 │   │
│  │ • Department Budgets            │   │
│  │ • Budget vs Actual              │   │
│  │ • Variance Analysis             │   │
│  │ • Forecasting                   │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

#### 12. Department-Specific Apps

```
┌─────────────────────────────────────────────────────────────────┐
│              DEPARTMENT-SPECIFIC FEATURES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   HOUSEKEEPING  │  │   ENGINEERING   │  │    SECURITY     │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤ │
│  │ • Room Status   │  │ • Work Orders   │  │ • Incident      │ │
│  │ • Task Assign   │  │ • PM Schedule   │  │   Reports       │ │
│  │ • Lost & Found  │  │ • Equipment     │  │ • CCTV Log      │ │
│  │ • Minibar       │  │   Tracking      │  │ • Key Control   │ │
│  │ • Laundry       │  │ • Energy Mgmt   │  │ • Patrol Log    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │    SALES &      │  │   BANQUET &     │  │      SPA &      │ │
│  │   MARKETING     │  │   EVENTS        │  │    WELLNESS     │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤ │
│  │ • Lead Mgmt     │  │ • Event Booking │  │ • Appointment   │ │
│  │ • Corporate     │  │ • Function      │  │   Booking       │ │
│  │   Accounts      │  │   Sheets        │  │ • Therapist     │ │
│  │ • Campaign      │  │ • Catering      │  │   Schedule      │ │
│  │   Tracking      │  │   Orders        │  │ • Treatment     │ │
│  │ • Revenue       │  │ • BEO           │  │   Menu          │ │
│  │   Targets       │  │   (Banquet      │  │ • Package       │ │
│  │                 │  │   Event Order)  │  │   Builder       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Concept

### Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CORE ENTITIES                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      ORGANIZATION (Multi-Tenant)                      │  │
│  │  • Hotels, Restaurants, Suppliers - all are "organizations"          │  │
│  │  • Each org has its own users, data isolation via RLS                │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  │                                          │
│          ┌───────────────────────┼───────────────────────┐                 │
│          ▼                       ▼                       ▼                 │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐          │
│  │    USERS      │      │  DEPARTMENTS  │      │   LOCATIONS   │          │
│  │ (All People)  │      │               │      │  (Properties) │          │
│  ├───────────────┤      ├───────────────┤      ├───────────────┤          │
│  │ • Employees   │      │ • Front Office│      │ • Main Hotel  │          │
│  │ • Guests      │      │ • F&B         │      │ • Branch      │          │
│  │ • Suppliers   │      │ • HK          │      │ • Restaurant  │          │
│  │ • Contacts    │      │ • Engineering │      │ • Outlet      │          │
│  └───────────────┘      │ • Finance     │      └───────────────┘          │
│                         │ • HR          │                                   │
│                         │ • Sales       │                                   │
│                         └───────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER TYPES & RELATIONSHIPS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User Type: EMPLOYEE                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  users ──┬── employees (employment details)                         │   │
│  │          ├── employee_salaries (payroll)                            │   │
│  │          ├── employee_attendance (clock in/out)                     │   │
│  │          ├── employee_leaves (cuti)                                 │   │
│  │          └── employee_documents (KTP, NPWP)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  User Type: GUEST                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  users ──┬── guests (guest profile)                                 │   │
│  │          ├── guest_preferences (JSONB)                              │   │
│  │          ├── loyalty_members (points, tier)                         │   │
│  │          └── reservations (booking history)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  User Type: SUPPLIER_CONTACT                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  users ──┬── supplier_contacts (contact person)                     │   │
│  │          └── suppliers (company) ──┬── products                     │   │
│  │                                     ├── purchase_orders             │   │
│  │                                     └── invoices                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### User Table (Unified)

```sql
-- Single users table for ALL user types
CREATE TABLE users (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    -- Common fields
    email VARCHAR(200) UNIQUE,
    phone VARCHAR(20),
    username VARCHAR(50),
    password_hash VARCHAR(255),

    -- Profile
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),

    -- Type discriminator
    user_type VARCHAR(20) NOT NULL,  -- 'employee', 'guest', 'supplier_contact', 'system'

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_user_type CHECK (user_type IN ('employee', 'guest', 'supplier_contact', 'system'))
);

-- Employee-specific data (if user_type = 'employee')
CREATE TABLE employees (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    employee_code VARCHAR(20) UNIQUE NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    position_id INTEGER REFERENCES positions(id),
    grade_id INTEGER REFERENCES employee_grades(id),
    manager_id INTEGER REFERENCES employees(id),

    hire_date DATE NOT NULL,
    contract_type VARCHAR(20),  -- permanent, contract, probation
    contract_end_date DATE,

    -- Payroll
    base_salary NUMERIC(15,2),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    tax_id VARCHAR(50),  -- NPWP

    -- Status
    employment_status VARCHAR(20) DEFAULT 'active',
    termination_date DATE,
    termination_reason TEXT,

    CONSTRAINT chk_employment_status CHECK (employment_status IN ('active', 'on_leave', 'suspended', 'terminated'))
);

-- Guest-specific data (if user_type = 'guest')
CREATE TABLE guests (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- Identity
    nationality VARCHAR(50),
    id_type VARCHAR(20),  -- passport, ktp, sim
    id_number VARCHAR(50),
    id_expiry DATE,

    -- Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}',

    -- Communication
    preferred_language VARCHAR(10) DEFAULT 'en',
    communication_preference VARCHAR(20) DEFAULT 'email',
    marketing_consent BOOLEAN DEFAULT FALSE,

    -- Stats
    total_stays INTEGER DEFAULT 0,
    total_revenue NUMERIC(15,2) DEFAULT 0,
    last_stay_date DATE,

    -- Loyalty
    loyalty_member_id INTEGER REFERENCES loyalty_members(id)
);

-- Loyalty Program
CREATE TABLE loyalty_members (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    member_number VARCHAR(20) UNIQUE NOT NULL,
    tier_id INTEGER REFERENCES loyalty_tiers(id),

    points_balance INTEGER DEFAULT 0,
    points_earned_total INTEGER DEFAULT 0,
    points_redeemed_total INTEGER DEFAULT 0,

    tier_qualified_date DATE,
    tier_expiry_date DATE,

    enrollment_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE loyalty_tiers (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(50) NOT NULL,  -- Bronze, Silver, Gold, Platinum, Diamond
    min_points INTEGER NOT NULL,
    benefits JSONB NOT NULL,
    discount_percentage NUMERIC(5,2) DEFAULT 0,
    priority_level INTEGER DEFAULT 0
);

-- Supplier organization & contacts
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    legal_name VARCHAR(200),
    tax_id VARCHAR(50),

    -- Contact
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(200),
    website VARCHAR(200),

    -- Payment terms
    payment_terms INTEGER DEFAULT 30,  -- days
    credit_limit NUMERIC(15,2),

    -- Rating
    rating NUMERIC(3,2),  -- 1.00 - 5.00
    is_approved BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Supplier's own employees (they can add their staff)
CREATE TABLE supplier_contacts (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),

    role VARCHAR(50),  -- admin, sales, finance, logistics
    is_primary BOOLEAN DEFAULT FALSE,
    can_receive_po BOOLEAN DEFAULT TRUE,
    can_submit_invoice BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     APPLICATION INTEGRATION MAP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Guest App ◄─────► PMS                                                      │
│     │               │                                                       │
│     │               ├──► Reservation                                        │
│     │               ├──► Check-in/out                                       │
│     │               └──► Room Charge                                        │
│     │                                                                       │
│     ├─────────────► Online Menu ◄─────► POS                                │
│     │                    │               │                                  │
│     │                    │               ├──► Kitchen (KDS)                 │
│     │                    │               └──► Inventory (stock deduction)   │
│     │                    │                                                  │
│     └─────────────► Loyalty Program                                        │
│                          │                                                  │
│                          └──► Points earning/redemption                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Supplier Portal ◄────► Procurement                                        │
│        │                    │                                               │
│        │                    ├──► Purchase Orders                           │
│        │                    └──► Goods Receipt                             │
│        │                                                                    │
│        └────────────────► Inventory                                        │
│                               │                                             │
│                               └──► Stock Levels                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HRM ◄──────────────────► Payroll                                          │
│   │                          │                                              │
│   ├──► Attendance            └──► Bank Integration                         │
│   ├──► Leave Management                                                    │
│   └──► Performance                                                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  All Modules ──────────────► Accounting (GL Integration)                   │
│                                  │                                          │
│                                  ├──► Revenue posting                      │
│                                  ├──► Expense posting                      │
│                                  └──► Financial Reports                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Asset Management ◄────────► Engineering (Maintenance)                     │
│        │                          │                                         │
│        └──► Depreciation          └──► Work Orders                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Development Roadmap

### Phase 1: Foundation (Month 1-4)
**Core Infrastructure:**
- [x] Backend (FastAPI) - Done
- [x] Frontend (React + Vite) - Done
- [x] Database (PostgreSQL) - Done
- [x] Authentication & RBAC - Done
- [x] Digital Signage (CMS) - Done
- [ ] Multi-tenant architecture enhancement

### Phase 2: PMS Core (Month 5-8)
**Hotel Operations:**
- [ ] Room Management
- [ ] Reservations
- [ ] Check-in/Check-out
- [ ] Billing & Folio
- [ ] Night Audit
- [ ] Rate Management

### Phase 3: F&B & POS (Month 9-12)
**Food & Beverage:**
- [ ] POS System
- [ ] Online Menu (QR Order)
- [ ] Kitchen Display System
- [ ] Table Management
- [ ] Room Service

### Phase 4: Supply Chain (Month 13-16)
**Procurement & Inventory:**
- [ ] Supplier Management
- [ ] Purchase Requisition
- [ ] Purchase Orders
- [ ] Goods Receiving
- [ ] Inventory Management
- [ ] Supplier Portal

### Phase 5: HRM & Payroll (Month 17-20)
**Human Resources:**
- [ ] Employee Database
- [ ] Attendance Management
- [ ] Leave Management
- [ ] Payroll Processing
- [ ] Performance Management

### Phase 6: Guest Experience (Month 21-24)
**Customer Facing:**
- [ ] Guest App (Mobile/Web)
- [ ] Loyalty Program
- [ ] Online Check-in
- [ ] Self-Service Portal
- [ ] Feedback System

### Phase 7: Finance & Advanced (Month 25+)
**Financial & Analytics:**
- [ ] General Ledger
- [ ] Accounts Receivable
- [ ] Accounts Payable
- [ ] Asset Management
- [ ] Advanced Analytics
- [ ] AI/ML Features

---

## Summary

**Total Applications: 12+**

| # | Application | Target Users | Priority |
|---|-------------|--------------|----------|
| 1 | PMS | Front Office, Reservations | P1 |
| 2 | Digital Signage (CMS) | Marketing | Done |
| 3 | POS | F&B Outlets | P2 |
| 4 | Online Menu | Guests | P2 |
| 5 | Inventory | Warehouse, Cost Control | P3 |
| 6 | Procurement | Purchasing | P3 |
| 7 | Supplier Portal | Suppliers | P3 |
| 8 | HRM | HR Department | P4 |
| 9 | Payroll | Finance, HR | P4 |
| 10 | Guest App | Guests, Members | P5 |
| 11 | Accounting | Finance | P5 |
| 12 | Asset Management | Engineering, Finance | P5 |

**Unified Backend**: Single FastAPI backend serving all applications
**Unified Database**: Single PostgreSQL database with multi-tenancy
**Unified Auth**: Single sign-on across all applications

---

*This document captures the complete platform vision. Update as scope evolves.*
