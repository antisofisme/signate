# PMS Hotel Reference Documentation

> Reference documentation dari database PMS Hotel (Firebird) untuk pengembangan sistem baru.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [PMS_DATABASE_ANALYSIS.md](./PMS_DATABASE_ANALYSIS.md) | Business flow, entity relationships, module overview |
| [PMS_DATABASE_SCHEMA.md](./PMS_DATABASE_SCHEMA.md) | Complete table structures from SQL export |

---

## Source Files

| File | Size | Content |
|------|------|---------|
| `powerfo.gdb` | 1.4GB | Front Office database (Firebird) |
| `powerbo.gdb` | 914MB | Back Office database (Firebird) |
| `powerfo.sql` | 1.9MB | Front Office schema (341 tables, 551 procedures) |
| `powerbo.sql` | 1.5MB | Back Office schema (318 tables, 367 procedures) |

---

## Database Statistics

### Front Office (powerfo)
- **Tables**: 341
- **Domains**: 126
- **Indexes**: 239
- **Stored Procedures**: 551
- **Triggers**: 672

### Back Office (powerbo)
- **Tables**: 318
- **Domains**: 66
- **Indexes**: 263
- **Stored Procedures**: 367
- **Triggers**: 562

---

## Core Modules

### Front Office
| Module | Key Tables | Description |
|--------|------------|-------------|
| **Guest/Folio** | FOGUEST, FOGROUP, FOJUR | Guest registration, billing |
| **Room** | FOROOM, FOSYSROOMTYPE | Room inventory |
| **Rate** | FOSYSRATE, FOSYSPACKAGE | Pricing |
| **AR/Payment** | ARCASH0, ARVCH, AR_CARD | Payments, city ledger |
| **Housekeeping** | HKROOM, HKASSIGN | Room cleaning |
| **POS** | MB_*, PBX_* | Outlets, phone |
| **Banquet** | BQ_* | Events & meetings |

### Back Office
| Module | Key Tables | Description |
|--------|------------|-------------|
| **General Ledger** | GL_*, GLJUR | Chart of accounts |
| **Accounts Payable** | AP_*, APJUR | Vendor payments |
| **Inventory** | INV_*, INVJUR | Stock management |
| **Fixed Assets** | FA_* | Asset tracking |
| **Bank Book** | BB_*, BBJUR | Cash management |

---

## Key Entity Relationships

```
SYSCUSTOMER (Company/Agent)
    │
    ├──► FOGUEST (Reservation/Guest)
    │       │
    │       ├──► FOROOM (Room Assignment)
    │       │
    │       ├──► FOJUR (Transactions)
    │       │       │
    │       │       └──► Category charges
    │       │
    │       └──► FOSYSRATE (Rate Applied)
    │
    └──► ARVCH (City Ledger Invoice)
            │
            └──► ARCASH0 (Payment Receipt)
```

---

## How to Use This Reference

### For New Feature Development

1. **Find the module** in PMS_DATABASE_ANALYSIS.md
2. **Look up table structure** in PMS_DATABASE_SCHEMA.md
3. **Understand the flow** from business process diagrams
4. **Map to new architecture** using our naming conventions

### For Understanding Business Logic

1. Check **stored procedures** in powerfo.sql/powerbo.sql
2. Look at **triggers** for automatic calculations
3. Review **exceptions** for business rules validation

### Example: Building Reservation Module

```
Reference Tables:
├── FOGUEST (main reservation)
├── FOGROUP (group booking)
├── FOGROUP_RATE (group rates)
├── FO_CUST_ALLOTMENT (room blocks)
├── FOSYSROOMTYPE (room types)
├── FOSYSRATE (rate codes)
└── SYSCUSTOMER (companies)

Key Procedures:
├── FO_CHECKIN_* (check-in logic)
├── FO_CHECKOUT_* (check-out logic)
└── FO_RATE_* (rate calculation)
```

---

## Naming Convention Mapping

| Old (Firebird) | New (PostgreSQL) | Notes |
|----------------|------------------|-------|
| FOGUEST | reservations / guests | Split into 2 tables |
| FOROOM | rooms | Keep similar |
| FOSYSROOMTYPE | room_types | Normalize prefix |
| FOSYSRATE | rate_codes | Normalize prefix |
| FOJUR | folio_transactions | Descriptive name |
| SYSCUSTOMER | companies | More specific |
| ARCASH0 | ar_payments | Descriptive |
| ARVCH | ar_invoices | Descriptive |

---

## Connection Info (If Needed)

```
Database: Firebird 2.x/3.x
Username: SYSDBA
Password: masterkey
Character Set: WIN1251 (Cyrillic - may need conversion)
```

### Tools for Viewing

- **DBeaver** (free, cross-platform)
- **IBExpert** (Windows, Firebird-specific)
- **FlameRobin** (free, Firebird-specific)

---

*Last updated: 2025-12-05*
