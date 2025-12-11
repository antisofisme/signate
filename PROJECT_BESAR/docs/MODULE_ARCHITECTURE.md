# Module Architecture

> Arsitektur modular platform dengan prinsip **"Develop Once, Use Everywhere"**
>
> **Date**: 2025-12-10
> **Status**: Approved
> **Related Standards**:
> - [DEVELOPMENT_STANDARDS.md - Section 1.7](./DEVELOPMENT_STANDARDS.md) - Cross-Module Naming Convention
> - [DEVELOPMENT_STANDARDS_V12.md - Standard #43](./DEVELOPMENT_STANDARDS_V12.md) - Config Governance
> - [SHARED_CODE_STANDARDS.md - Section 9](./SHARED_CODE_STANDARDS.md) - Flexible Configuration Pattern
> - [PLATFORM_VISION.md](./PLATFORM_VISION.md) - Platform Vision & Architecture
> - [DATABASE_SCHEMA_PLATFORM.md](./DATABASE_SCHEMA_PLATFORM.md) - Database Schema

---

## Table of Contents

1. [Development Philosophy](#1-development-philosophy)
2. [Architecture Layers](#2-architecture-layers)
3. [Shared Building Blocks](#3-shared-building-blocks)
4. [Core Modules](#4-core-modules)
5. [Feature Modules](#5-feature-modules)
6. [Integration Points](#6-integration-points)
7. [Module Configuration](#7-module-configuration)
8. [Subscription Scenarios](#8-subscription-scenarios)
9. [Module Code Registry](#9-module-code-registry)

---

## 1. Development Philosophy

### 1.1 Core Principle: "Sekali Pukul, Banyak Selesai"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DEVELOPMENT PHILOSOPHY: BUILD ONCE, USE EVERYWHERE              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ❌ TRADITIONAL APPROACH (Repetitive):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  PMS Team builds:        POS Team builds:       ACC Team builds:    │   │
│  │  • Folio billing         • Receipt system       • Invoice system    │   │
│  │  • Guest payments        • Order payments       • Payment voucher   │   │
│  │  • City ledger           • Customer mgmt        • AR/AP system      │   │
│  │  • Revenue reports       • Sales reports        • Financial reports │   │
│  │                                                                      │   │
│  │  Problems:                                                           │   │
│  │  • 3x development effort for similar concepts                       │   │
│  │  • Bug fix di satu tempat, yang lain tidak ikut fix                 │   │
│  │  • Different implementation, inconsistent UX                        │   │
│  │  • Maintenance nightmare                                            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ✅ OUR APPROACH (Shared Building Blocks):                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ╔═══════════════════════════════════════════════════════════════╗  │   │
│  │  ║         SHARED BUILDING BLOCKS (Develop Once)                 ║  │   │
│  │  ╠═══════════════════════════════════════════════════════════════╣  │   │
│  │  ║  Billing Engine    │  Payment Engine   │  Entity Management   ║  │   │
│  │  ║  Task Engine       │  Document Engine  │  Notification Engine ║  │   │
│  │  ║  Workflow Engine   │  Calendar Engine  │  Reporting Engine    ║  │   │
│  │  ╚═══════════════════════════════════════════════════════════════╝  │   │
│  │                               │                                      │   │
│  │         ┌─────────────────────┼─────────────────────┐               │   │
│  │         ▼                     ▼                     ▼               │   │
│  │  ┌───────────┐         ┌───────────┐         ┌───────────┐         │   │
│  │  │    PMS    │         │    POS    │         │    ACC    │         │   │
│  │  │  Config   │         │  Config   │         │  Config   │         │   │
│  │  ├───────────┤         ├───────────┤         ├───────────┤         │   │
│  │  │ Billing:  │         │ Billing:  │         │ Billing:  │         │   │
│  │  │ "Folio"   │         │ "Receipt" │         │ "Invoice" │         │   │
│  │  │           │         │           │         │           │         │   │
│  │  │ Entity:   │         │ Entity:   │         │ Entity:   │         │   │
│  │  │ "Guest"   │         │ "Customer"│         │ "Debtor"  │         │   │
│  │  └───────────┘         └───────────┘         └───────────┘         │   │
│  │                                                                      │   │
│  │  Benefits:                                                           │   │
│  │  ✓ 1x development, Nx benefit                                       │   │
│  │  ✓ Fix bug di Billing Engine = semua module ikut fix                │   │
│  │  ✓ Consistent UX across modules                                     │   │
│  │  ✓ Config Governance menentukan behavior per module                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Principles

| Principle | Description | Reference |
|-----------|-------------|-----------|
| **DRY (Don't Repeat Yourself)** | Build shared components once, configure per module | This document |
| **Config-Driven Behavior** | Module behavior controlled by configuration, not code | [Config Governance - Standard #43](./DEVELOPMENT_STANDARDS_V12.md) |
| **Context-Aware Visibility** | Same data, different visibility per context | [Section 43.12](./DEVELOPMENT_STANDARDS_V12.md) |
| **Cross-Module Naming** | Clear naming to avoid collision | [Section 1.7](./DEVELOPMENT_STANDARDS.md) |
| **Standalone + Integrated** | Modules work alone and together | This document |

---

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 0: PLATFORM CORE                                               ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║  • Users, Organizations, Auth, RBAC                                   ║ │
│  ║  • Subscriptions, Billing, Licensing                                  ║ │
│  ║  • Shared Lookups (currencies, countries, etc)                        ║ │
│  ║                                                                        ║ │
│  ║  Reference: [PLATFORM_VISION.md], [DATABASE_SCHEMA_PLATFORM.md]       ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 1: SHARED BUILDING BLOCKS                                      ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║  Reusable engines that power all modules:                             ║ │
│  ║                                                                        ║ │
│  ║  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ║ │
│  ║  │   Billing    │ │   Payment    │ │    Entity    │ │     Task     │ ║ │
│  ║  │   Engine     │ │   Engine     │ │   Engine     │ │    Engine    │ ║ │
│  ║  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ ║ │
│  ║  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ║ │
│  ║  │   Workflow   │ │   Calendar   │ │   Document   │ │ Notification │ ║ │
│  ║  │   Engine     │ │   Engine     │ │   Engine     │ │    Engine    │ ║ │
│  ║  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ ║ │
│  ║  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ║ │
│  ║  │  Reporting   │ │  Inventory   │ │    Ledger    │ │  Membership  │ ║ │
│  ║  │   Engine     │ │   Engine     │ │   Engine     │ │    Engine    │ ║ │
│  ║  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ ║ │
│  ║                                                                        ║ │
│  ║  Reference: [SHARED_CODE_STANDARDS.md]                                ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 2: CORE MODULES (Standalone Capable)                           ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║                                                                        ║ │
│  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        ║ │
│  ║  │   PMS   │ │   POS   │ │   ACC   │ │   INV   │ │   HRM   │        ║ │
│  ║  │ Hotel   │ │  F&B    │ │ Account │ │  Stock  │ │   HR    │        ║ │
│  ║  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        ║ │
│  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        ║ │
│  ║  │   CHM   │ │  PROC   │ │   AST   │ │   CRM   │ │   PRJ   │        ║ │
│  ║  │ Channel │ │Purchase │ │ Assets  │ │Customer │ │ Project │        ║ │
│  ║  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        ║ │
│  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐                                  ║ │
│  ║  │   LDR   │ │   SPA   │ │   GYM   │                                  ║ │
│  ║  │Laundry  │ │Wellness │ │Fitness  │                                  ║ │
│  ║  └─────────┘ └─────────┘ └─────────┘                                  ║ │
│  ║                                                                        ║ │
│  ║  Reference: [Section 1.7 - Cross-Module Naming](./DEVELOPMENT_STANDARDS.md) ║
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 3: FEATURE MODULES (Requires Parent)                           ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║                                                                        ║ │
│  ║  PMS Features:     HRM Features:     ACC Features:    POS Features:  ║ │
│  ║  • pms.membership  • hrm.payroll     • acc.budget     • pos.online   ║ │
│  ║  • pms.events      • hrm.eng         • acc.tax        • pos.kitchen  ║ │
│  ║  • pms.hk          • hrm.it          • acc.audit      • pos.delivery ║ │
│  ║  • pms.concierge   • hrm.recruit     • acc.consol     • pos.reserv   ║ │
│  ║  • pms.guest_app   • hrm.membership                                   ║ │
│  ║  • pms.rms         • hrm.training                                     ║ │
│  ║  • pms.parking     • hrm.security                                     ║ │
│  ║  • pms.fleet                                                          ║ │
│  ║  • pms.security                                                       ║ │
│  ║  • pms.ibe (Booking Engine)                                           ║ │
│  ║                                                                        ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 4: INTEGRATION MODULES (Auto-enabled when both subscribed)     ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║                                                                        ║ │
│  ║  PMS+ACC │ PMS+CHM │ PMS+POS │ POS+INV │ POS+ACC │ HRM+ACC │ INV+ACC ║ │
│  ║  LDR+PMS │ LDR+ACC │ LDR+INV │ LDR+HRM │ INV+PROC│ PROC+ACC│         ║ │
│  ║  SPA+PMS │ SPA+ACC │ SPA+INV │ SPA+HRM │ GYM+PMS │ GYM+ACC │ GYM+HRM ║ │
│  ║                                                                        ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║  LAYER 5: PLATFORM MODULES (Multi-Property / Chain)                   ║ │
│  ║  ─────────────────────────────────────────────────────────────────── ║ │
│  ║                                                                        ║ │
│  ║  ┌─────────┐ ┌─────────┐                                              ║ │
│  ║  │   CRS   │ │   S&C   │                                              ║ │
│  ║  │Central  │ │ Sales & │                                              ║ │
│  ║  │Reserv.  │ │Catering │                                              ║ │
│  ║  └─────────┘ └─────────┘                                              ║ │
│  ║                                                                        ║ │
│  ║  CRS: Central Reservation System (multi-property, chain-wide)         ║ │
│  ║  S&C: Sales & Catering (hybrid CRM + Events)                          ║ │
│  ║                                                                        ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Shared Building Blocks

### 3.1 Overview

Shared Building Blocks adalah **reusable engines** yang digunakan oleh semua module. Develop sekali, configure per module via [Config Governance (Standard #43)](./DEVELOPMENT_STANDARDS_V12.md).

### 3.2 Building Blocks Detail

#### 3.2.1 Billing Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BILLING ENGINE                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Line items (charges)          │   │ • PMS → Folio                   │ │
│  │ • Taxes & service charge        │   │ • POS → Receipt/Bill            │ │
│  │ • Discounts (%, fixed, promo)   │   │ • ACC → AR Invoice, AP Invoice  │ │
│  │ • Subtotal/Total calculation    │   │ • SPA → Treatment Bill          │ │
│  │ • Split billing                 │   │ • EVT → Event Invoice           │ │
│  │ • Void/Correction               │   │ • PROC → Purchase Invoice       │ │
│  │ • Tax rounding                  │   │                                 │ │
│  │ • Multi-currency                │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Config per Module (via Config Governance):                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Config Key                        │ PMS Value    │ POS Value         │  │
│  ├───────────────────────────────────┼──────────────┼───────────────────┤  │
│  │ {module}.billing.document_name    │ "Folio"      │ "Receipt"         │  │
│  │ {module}.billing.tax_rate         │ 11           │ 10                │  │
│  │ {module}.billing.service_charge   │ 10           │ 0                 │  │
│  │ {module}.billing.number_format    │ "FO-{Y}{N}"  │ "RCP-{Y}{N}"      │  │
│  │ {module}.billing.allow_void       │ true         │ true              │  │
│  │ {module}.billing.void_requires    │ "manager"    │ "supervisor"      │  │
│  └───────────────────────────────────┴──────────────┴───────────────────┘  │
│                                                                             │
│  Database Schema:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ shared.billing_documents (                                          │   │
│  │     id, organization_id, module_code,                               │   │
│  │     document_type, document_number,                                 │   │
│  │     entity_type, entity_id,          -- Guest, Customer, Debtor     │   │
│  │     subtotal, tax_amount, service_amount, discount_amount, total,   │   │
│  │     currency_code, exchange_rate,                                   │   │
│  │     status, config_snapshot,         -- Snapshot config saat create │   │
│  │     created_at, created_by                                          │   │
│  │ )                                                                   │   │
│  │                                                                      │   │
│  │ shared.billing_line_items (                                         │   │
│  │     id, billing_document_id,                                        │   │
│  │     item_type, item_code, description,                              │   │
│  │     quantity, unit_price, discount, tax_rate,                       │   │
│  │     line_total                                                      │   │
│  │ )                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Reference: [Config Snapshot Pattern - Section 43.1.3](./DEVELOPMENT_STANDARDS_V12.md) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Payment Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PAYMENT ENGINE                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Multiple payment methods      │   │ • PMS → Folio Payment           │ │
│  │ • Split payment                 │   │ • POS → Order Payment           │ │
│  │ • Change calculation            │   │ • ACC → Receipt/Payment Voucher │ │
│  │ • Deposit/Advance payment       │   │ • SPA → Treatment Payment       │ │
│  │ • Refund processing             │   │ • EVT → Event Payment           │ │
│  │ • Settlement/Close shift        │   │                                 │ │
│  │ • EDC integration               │   │                                 │ │
│  │ • E-wallet integration          │   │                                 │ │
│  │ • QRIS support                  │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Payment Methods (Context-Aware Visibility):                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Centralized: shared.payment_methods                                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │   Cash   │ │  Card    │ │ Transfer │ │ E-Wallet │ │Room Chg  │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │       │            │            │            │            │         │   │
│  │       └────────────┴────────────┴────────────┴────────────┘         │   │
│  │                              │                                       │   │
│  │              entity_context_visibility                              │   │
│  │                              │                                       │   │
│  │       ┌──────────────────────┼──────────────────────┐               │   │
│  │       ▼                      ▼                      ▼               │   │
│  │  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       │   │
│  │  │ FO Cashier  │       │ FB Cashier  │       │ SPA Cashier │       │   │
│  │  │ ✓ All      │       │ ✓ Cash     │       │ ✓ Cash     │       │   │
│  │  │            │       │ ✓ Card     │       │ ✓ Card     │       │   │
│  │  │            │       │ ✓ E-Wallet │       │ ✓ Room Chg │       │   │
│  │  │            │       │ ✓ Room Chg │       │            │       │   │
│  │  └─────────────┘       └─────────────┘       └─────────────┘       │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Reference: [Context-Aware Visibility - Section 43.12](./DEVELOPMENT_STANDARDS_V12.md) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.3 Entity Management Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ENTITY MANAGEMENT ENGINE                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By (Config-driven name):       │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Contact information           │   │ • PMS → "Guest"                 │ │
│  │ • Address management            │   │ • POS → "Customer"              │ │
│  │ • ID/Document storage           │   │ • ACC → "Debtor", "Creditor"    │ │
│  │ • Communication preferences     │   │ • HRM → "Employee"              │ │
│  │ • History/Timeline              │   │ • PROC → "Supplier"             │ │
│  │ • Merge duplicates              │   │ • CRM → "Contact"               │ │
│  │ • Tags/Categories               │   │                                 │ │
│  │ • Custom fields                 │   │                                 │ │
│  │ • Profile picture               │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Config per Module:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Config Key                      │ PMS        │ HRM        │ ACC      │  │
│  ├─────────────────────────────────┼────────────┼────────────┼──────────┤  │
│  │ {module}.entity.display_name    │ "Guest"    │ "Employee" │ "Debtor" │  │
│  │ {module}.entity.required_fields │ [name,     │ [name,nik, │ [name,   │  │
│  │                                 │  phone]    │  position] │  npwp]   │  │
│  │ {module}.entity.id_types        │ [ktp,      │ [ktp]      │ [npwp]   │  │
│  │                                 │  passport] │            │          │  │
│  │ {module}.entity.allow_merge     │ true       │ false      │ true     │  │
│  └─────────────────────────────────┴────────────┴────────────┴──────────┘  │
│                                                                             │
│  Cross-Module Entity Linking:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Guest (PMS)  ─────────────────┐                                    │   │
│  │                                │                                     │   │
│  │  Customer (POS) ───────────────┼──► shared.entity_links             │   │
│  │                                │    (links entities across modules)  │   │
│  │  Debtor (ACC) ─────────────────┘                                    │   │
│  │                                                                      │   │
│  │  Use case: Guest checks in, dines at restaurant, gets AR invoice    │   │
│  │  → All linked as same person                                        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.4 Task Management Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TASK MANAGEMENT ENGINE                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Task creation                 │   │ • pms.hk → Room cleaning        │ │
│  │ • Assignment (auto/manual)      │   │ • hrm.eng → Work orders         │ │
│  │ • Priority & SLA                │   │ • hrm.it → IT tickets           │ │
│  │ • Status workflow (configurable)│   │ • pms.concierge → Guest requests│ │
│  │ • Checklist support             │   │ • proc → Approval tasks         │ │
│  │ • Attachments                   │   │ • prj → Project tasks           │ │
│  │ • Comments/Notes                │   │ • Generic → Any task            │ │
│  │ • Due dates & reminders         │   │                                 │ │
│  │ • Recurring tasks               │   │                                 │ │
│  │ • Time tracking                 │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Config per Module (Status Workflow Example):                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  pms.hk (Housekeeping):                                             │   │
│  │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐                 │   │
│  │  │Assigned│──►│Cleaning│──►│Inspect │──►│Complete│                 │   │
│  │  └────────┘   └────────┘   └────────┘   └────────┘                 │   │
│  │                                                                      │   │
│  │  hrm.eng (Engineering):                                             │   │
│  │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   │   │
│  │  │  Open  │──►│Assigned│──►│In Work │──►│Pending │──►│Complete│   │   │
│  │  └────────┘   └────────┘   └────────┘   │ Parts  │   └────────┘   │   │
│  │                                         └────────┘                 │   │
│  │                                                                      │   │
│  │  hrm.it (IT Support):                                               │   │
│  │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐                 │   │
│  │  │  New   │──►│In Prog │──►│Resolved│──►│ Closed │                 │   │
│  │  └────────┘   └────────┘   └────────┘   └────────┘                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Reference: [State Machine - Standard #28](./DEVELOPMENT_STANDARDS_V7.md)  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.5 Workflow/Approval Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW/APPROVAL ENGINE                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Multi-level approval          │   │ • PROC → PO Approval            │ │
│  │ • Parallel/Sequential flow      │   │ • ACC → Journal Approval        │ │
│  │ • Conditional routing           │   │ • HRM → Leave Approval          │ │
│  │ • Delegation                    │   │ • PMS → Rate Change Approval    │ │
│  │ • Escalation                    │   │ • INV → Stock Adjustment        │ │
│  │ • Timeout rules                 │   │ • Config → Config Change        │ │
│  │ • Audit trail                   │   │ • All → Document approval       │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Reference: [Config Approval Workflow - Section 43.5](./DEVELOPMENT_STANDARDS_V12.md) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.6 Calendar/Scheduling Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALENDAR/SCHEDULING ENGINE                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Resource booking              │   │ • PMS → Room reservation        │ │
│  │ • Time slot management          │   │ • SPA → Treatment booking       │ │
│  │ • Availability checking         │   │ • GYM → Class scheduling        │ │
│  │ • Recurring bookings            │   │ • pms.events → Venue booking    │ │
│  │ • Conflict detection            │   │ • HRM → Shift scheduling        │ │
│  │ • Calendar views (day/week/mo)  │   │ • hrm.eng → Maintenance sched.  │ │
│  │ • Overbooking rules             │   │ • Meeting room booking          │ │
│  │ • Block dates                   │   │ • Equipment reservation         │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.7 Document Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT ENGINE                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • PDF generation (WeasyPrint)   │   │ • All modules for reports       │ │
│  │ • HTML to PDF (Puppeteer)       │   │ • PMS → Confirmation letter     │ │
│  │ • Template management           │   │ • ACC → Financial statements    │ │
│  │ • Variable substitution         │   │ • HRM → Payslip, contracts      │ │
│  │ • Batch printing                │   │ • PROC → Purchase Order         │ │
│  │ • Email attachment              │   │ • POS → Receipt                 │ │
│  │ • Digital signature             │   │ • All → Invoices                │ │
│  │ • Barcode/QR code generation    │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Reference: [Report Generation - Standard #33](./DEVELOPMENT_STANDARDS_V8.md) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.8 Notification Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NOTIFICATION ENGINE                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Channels:                           │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Multi-channel delivery        │   │ • Email (AWS SES)               │ │
│  │ • Template management           │   │ • SMS                           │ │
│  │ • Variable substitution         │   │ • WhatsApp                      │ │
│  │ • Scheduling                    │   │ • Push notification             │ │
│  │ • Delivery tracking             │   │ • In-app notification           │ │
│  │ • Retry logic                   │   │ • Webhook                       │ │
│  │ • User preferences              │   │                                 │ │
│  │ • Do-not-disturb                │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Reference: [Notification - Standard #23](./DEVELOPMENT_STANDARDS_V5.md)   │
│             [Email Templates - Standard #35](./DEVELOPMENT_STANDARDS_V9.md)│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.9 Reporting Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  REPORTING ENGINE                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Report builder/designer       │   │ • All modules                   │ │
│  │ • Filters & parameters          │   │                                 │ │
│  │ • Drill-down capability         │   │ Report Visibility:              │ │
│  │ • Export (PDF, Excel, CSV)      │   │ (Context-Aware per Role)        │ │
│  │ • Scheduling (daily, weekly)    │   │ • Finance → All financial       │ │
│  │ • Dashboard widgets             │   │ • FO Manager → FO reports       │ │
│  │ • Cross-module reports          │   │ • FB Manager → F&B reports      │ │
│  │ • Caching results               │   │ • HR → HR reports               │ │
│  │ • Background generation         │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Reference: [Report Generation - Standard #33](./DEVELOPMENT_STANDARDS_V8.md)         │
│             [Context-Aware Visibility - Section 43.12](./DEVELOPMENT_STANDARDS_V12.md) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.10 Inventory/Stock Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INVENTORY/STOCK ENGINE                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Stock tracking                │   │ • INV → Warehouse stock         │ │
│  │ • Multi-location/warehouse      │   │ • POS → F&B ingredients         │ │
│  │ • Stock movements (in/out)      │   │ • PMS → Minibar, Amenities      │ │
│  │ • Valuation (FIFO, Average)     │   │ • SPA → Products                │ │
│  │ • Stock count/opname            │   │ • hrm.eng → Spare parts         │ │
│  │ • Min/Max levels                │   │ • All → Consumables             │ │
│  │ • Batch/Lot tracking            │   │                                 │ │
│  │ • Expiry management             │   │                                 │ │
│  │ • Auto-reorder                  │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.11 Ledger Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LEDGER ENGINE (Double-Entry Core)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Double-entry posting          │   │ • ACC → Full accounting         │ │
│  │ • Chart of Accounts             │   │ • PMS → City Ledger (simplified)│ │
│  │ • Journal entries               │   │ • POS → Cash management         │ │
│  │ • Period management             │   │ • All → Revenue tracking        │ │
│  │ • Trial balance                 │   │                                 │ │
│  │ • Sub-ledgers (AR, AP)          │   │ When PMS+ACC integrated:        │ │
│  │ • Multi-currency                │   │ • Folio → Journal (auto)        │ │
│  │ • Cost center                   │   │ • City Ledger → Full AR         │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  PMS Standalone vs PMS+ACC:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  PMS Standalone:              PMS + ACC Integrated:                 │   │
│  │  • Basic folio billing        • Full folio billing                  │   │
│  │  • Simplified city ledger     • City Ledger → Full AR               │   │
│  │  • Cash management            • Auto GL posting                     │   │
│  │  • Revenue reports            • Full financial statements           │   │
│  │                               • Cost center breakdown               │   │
│  │                               • Departmental P&L                    │   │
│  │                                                                      │   │
│  │  Sufficient for small hotel   For full financial management         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.12 Membership/Loyalty Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MEMBERSHIP/LOYALTY ENGINE                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Features:                         Used By:                            │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐ │
│  │ • Points accumulation           │   │ • pms.membership → Guest loyalty│ │
│  │ • Tier management               │   │ • hrm.membership → Employee     │ │
│  │ • Rewards catalog               │   │ • pos → Customer loyalty        │ │
│  │ • Redemption                    │   │ • CRM → Contact loyalty         │ │
│  │ • Member rates/discounts        │   │                                 │ │
│  │ • Card/QR management            │   │                                 │ │
│  │ • Points expiry                 │   │                                 │ │
│  │ • Transfer points               │   │                                 │ │
│  └─────────────────────────────────┘   └─────────────────────────────────┘ │
│                                                                             │
│  Config per Module:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  pms.membership:                  hrm.membership:                   │   │
│  │  • Tiers: Silver, Gold, Platinum  • Tiers: Regular, Senior          │   │
│  │  • Points: 1 point per 10K spent  • Benefits: Discounts, allowances │   │
│  │  • Rewards: Free nights, upgrades • Points: Based on tenure         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.13 Observability Engine (Core Infrastructure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OBSERVABILITY ENGINE (CORE INFRASTRUCTURE)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️  CORE INFRASTRUCTURE - Required for ALL deployments                     │
│                                                                             │
│  Components:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │   │
│  │  │     METRICS      │  │      LOGS        │  │     TRACING      │  │   │
│  │  │   (Prometheus)   │  │     (Loki)       │  │    (Jaeger)      │  │   │
│  │  │                  │  │                  │  │                  │  │   │
│  │  │ • App metrics    │  │ • JSON logs      │  │ • Distributed    │  │   │
│  │  │ • Business KPIs  │  │ • Per-tenant     │  │ • Request flow   │  │   │
│  │  │ • Infra metrics  │  │ • Correlation ID │  │ • Latency        │  │   │
│  │  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │   │
│  │           │                     │                     │            │   │
│  │           └─────────────────────┼─────────────────────┘            │   │
│  │                                 ▼                                  │   │
│  │                    ┌──────────────────────┐                        │   │
│  │                    │      GRAFANA         │                        │   │
│  │                    │   (Dashboards)       │                        │   │
│  │                    └──────────────────────┘                        │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────┐                        │   │
│  │  │     ERRORS       │  │    ALERTING      │                        │   │
│  │  │    (Sentry)      │  │  (AlertManager)  │                        │   │
│  │  │                  │  │                  │                        │   │
│  │  │ • Error tracking │  │ • PagerDuty      │                        │   │
│  │  │ • Stack traces   │  │ • Slack          │                        │   │
│  │  │ • Performance    │  │ • Email          │                        │   │
│  │  │ • Release track  │  │ • Webhook        │                        │   │
│  │  │ • Session replay │  │                  │                        │   │
│  │  └──────────────────┘  └──────────────────┘                        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Used By: **ALL MODULES** (automatic - no configuration needed)             │
│                                                                             │
│  Auto-Instrumentation:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Backend (FastAPI):                                                 │   │
│  │  ├── Sentry SDK auto-captures exceptions                            │   │
│  │  ├── OpenTelemetry auto-instruments HTTP, DB, Redis, Celery        │   │
│  │  ├── Prometheus metrics exported at /metrics                        │   │
│  │  └── JSON structured logging with tenant context                    │   │
│  │                                                                      │   │
│  │  Frontend (React):                                                  │   │
│  │  ├── Sentry SDK auto-captures JS errors                             │   │
│  │  ├── Performance monitoring (Core Web Vitals)                       │   │
│  │  ├── Session replay for error reproduction                          │   │
│  │  └── Source map upload for readable stack traces                    │   │
│  │                                                                      │   │
│  │  Background Jobs (Celery):                                          │   │
│  │  ├── Sentry Celery integration                                      │   │
│  │  ├── Task execution metrics                                         │   │
│  │  └── Failed task tracking                                           │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Multi-Tenant Isolation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  All observability data tagged with:                                │   │
│  │  • tenant_id (organization ID)                                      │   │
│  │  • org_code (organization code)                                     │   │
│  │  • environment (production/staging)                                 │   │
│  │                                                                      │   │
│  │  Enables:                                                           │   │
│  │  • Per-tenant dashboards in Grafana                                 │   │
│  │  • Filter errors by tenant in Sentry                                │   │
│  │  • Tenant-specific alerting rules                                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Reference: [Standard #15 - Logging & Observability](./DEVELOPMENT_STANDARDS_V2.md) │
│             [Standard #40 - Distributed Tracing](./DEVELOPMENT_STANDARDS_V11.md)   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Building Blocks Summary Table

| # | Engine | Core Responsibility | Used By Modules |
|---|--------|---------------------|-----------------|
| 1 | **Billing** | Invoices, charges, taxes, totals | PMS, POS, ACC, SPA, EVT |
| 2 | **Payment** | Payment processing, settlement | PMS, POS, ACC, SPA |
| 3 | **Entity** | Contact management | PMS, POS, ACC, HRM, CRM |
| 4 | **Task** | Task lifecycle management | PMS.HK, HRM.ENG, HRM.IT, PRJ |
| 5 | **Workflow** | Approval & routing | PROC, ACC, HRM, Config |
| 6 | **Calendar** | Booking & scheduling | PMS, SPA, EVT, HRM |
| 7 | **Document** | PDF/report generation | All modules |
| 8 | **Notification** | Multi-channel messaging | All modules |
| 9 | **Reporting** | Reports & dashboards | All modules |
| 10 | **Inventory** | Stock tracking | INV, POS, PMS, SPA |
| 11 | **Ledger** | Double-entry accounting | ACC, PMS (simplified) |
| 12 | **Membership** | Loyalty & points | PMS, HRM, POS, CRM |
| 13 | **Observability** ⭐ | Metrics, logs, tracing, errors | **All modules (Core)** |

---

## 4. Core Modules

### 4.1 Overview

Core Modules adalah **standalone-capable modules** yang dapat berjalan sendiri atau terintegrasi dengan module lain.

### 4.2 Module Capability Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MODULE CAPABILITY: STANDALONE vs INTEGRATED                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────┬─────────────────────────────┬─────────────────────────────────┐│
│  │ Module │ Standalone Capability       │ Additional When Integrated      ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ PMS    │ ✓ Reservations              │ +ACC: Auto GL posting,          ││
│  │        │ ✓ Room Management           │       Full AR, Financial Stmt   ││
│  │        │ ✓ Guest Management          │ +INV: Minibar tracking          ││
│  │        │ ✓ Folios & Billing          │ +CHM: OTA sync, rate parity     ││
│  │        │ ✓ Basic City Ledger         │ +HRM: Staff scheduling          ││
│  │        │ ✓ Cash Management           │ +POS: F&B room charge           ││
│  │        │ ✓ Revenue Reports           │ +CRM: Guest relationships       ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ ACC    │ ✓ Chart of Accounts         │ +PMS: Hotel revenue posting     ││
│  │        │ ✓ Journal Entries           │ +POS: Sales posting             ││
│  │        │ ✓ AP (Payables)             │ +INV: Stock valuation           ││
│  │        │ ✓ AR (Receivables)          │ +HRM: Payroll journal           ││
│  │        │ ✓ Bank Reconciliation       │ +PROC: PO → AP                  ││
│  │        │ ✓ Financial Statements      │                                  ││
│  │        │ ✓ Tax Reports               │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ POS    │ ✓ Orders & Items            │ +ACC: Sales → GL posting        ││
│  │        │ ✓ Table Management          │ +INV: Stock deduction           ││
│  │        │ ✓ Menu Management           │ +PMS: Room charge, guest lookup ││
│  │        │ ✓ Cash Management           │ +HRM: Staff sales tracking      ││
│  │        │ ✓ Receipts                  │ +CRM: Customer loyalty          ││
│  │        │ ✓ Basic Sales Reports       │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ INV    │ ✓ Stock Items               │ +ACC: Stock value → GL          ││
│  │        │ ✓ Warehouses                │ +POS: Auto stock deduction      ││
│  │        │ ✓ Stock Movements           │ +PROC: Receiving goods          ││
│  │        │ ✓ Stock Count               │ +PMS: Minibar, amenities        ││
│  │        │ ✓ Valuation (FIFO/Avg)      │                                  ││
│  │        │ ✓ Stock Reports             │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ HRM    │ ✓ Employee Data             │ +ACC: Payroll → GL              ││
│  │        │ ✓ Attendance                │ +PMS: Staff room allocation     ││
│  │        │ ✓ Leave Management          │ +POS: Cashier assignment        ││
│  │        │ ✓ Departments               │                                  ││
│  │        │ ✓ Shifts                    │                                  ││
│  │        │ ✓ Basic Payroll             │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ CHM    │ ✓ Channel Connections       │ +PMS: Full 2-way sync           ││
│  │        │ ✓ Rate Management           │       (Availability, Rates,     ││
│  │        │ ✓ Inventory Sync (manual)   │        Reservations)            ││
│  │        │ ✓ Manual Booking Entry      │                                  ││
│  │        │ ✓ Channel Reports           │ Without PMS: Manual inventory   ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ PROC   │ ✓ Purchase Requisition      │ +INV: Goods receiving           ││
│  │        │ ✓ Purchase Orders           │ +ACC: PO → AP invoice           ││
│  │        │ ✓ Supplier Management       │                                  ││
│  │        │ ✓ Approval Workflow         │                                  ││
│  │        │ ✓ Purchase Reports          │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ AST    │ ✓ Asset Register            │ +ACC: Depreciation → GL         ││
│  │        │ ✓ Depreciation Calculation  │ +HRM: Asset assignment to staff ││
│  │        │ ✓ Asset Location            │ +hrm.eng: Maintenance link      ││
│  │        │ ✓ Disposal Management       │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ CRM    │ ✓ Contact Management        │ +PMS: Guest history             ││
│  │        │ ✓ Interaction History       │ +POS: Purchase history          ││
│  │        │ ✓ Campaigns                 │ +ACC: Credit history            ││
│  │        │ ✓ Feedback/Survey           │                                  ││
│  │        │ ✓ NPS Tracking              │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ PRJ    │ ✓ Projects & Milestones     │ +HRM: Resource allocation       ││
│  │        │ ✓ Task Management           │ +ACC: Project costing           ││
│  │        │ ✓ Time Tracking             │                                  ││
│  │        │ ✓ Gantt Charts              │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ LDR    │ ✓ Customer Management       │ +PMS: Guest laundry → folio     ││
│  │        │ ✓ Service Catalog           │ +ACC: Revenue posting           ││
│  │        │ ✓ Order/Ticket Management   │ +INV: Supplies consumption      ││
│  │        │ ✓ Item Tracking             │ +HRM: Staff scheduling          ││
│  │        │ ✓ Route Management          │                                  ││
│  │        │ ✓ Machine Management        │                                  ││
│  │        │ ✓ Production Workflow       │                                  ││
│  │        │ ✓ Direct Billing/Invoicing  │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ SPA    │ ✓ Treatment Catalog         │ +PMS: Guest spa → folio         ││
│  │        │ ✓ Therapist Management      │ +ACC: Revenue posting           ││
│  │        │ ✓ Appointment Booking       │ +INV: Product consumption       ││
│  │        │ ✓ Room/Facility Scheduling  │ +HRM: Therapist scheduling      ││
│  │        │ ✓ Package Management        │ +CRM: Guest preferences         ││
│  │        │ ✓ Membership/Vouchers       │                                  ││
│  │        │ ✓ Direct Billing            │                                  ││
│  │        │                             │                                  ││
│  ├────────┼─────────────────────────────┼─────────────────────────────────┤│
│  │        │                             │                                  ││
│  │ GYM    │ ✓ Membership Management     │ +PMS: Guest gym → folio         ││
│  │        │ ✓ Class/Session Scheduling  │ +ACC: Revenue posting           ││
│  │        │ ✓ Trainer Management        │ +HRM: Trainer scheduling        ││
│  │        │ ✓ Equipment Tracking        │ +AST: Equipment as assets       ││
│  │        │ ✓ Access Control            │ +CRM: Member engagement         ││
│  │        │ ✓ Personal Training         │                                  ││
│  │        │ ✓ Direct Billing            │                                  ││
│  │        │                             │                                  ││
│  └────────┴─────────────────────────────┴─────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Module Details

#### 4.3.1 PMS (Property Management System)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: PMS (Property Management System)                                    │
│  Code: pms                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Hotel front office operations                                     │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Reservations (individual, group, corporate)                       │   │
│  │ • Room management (status, assignment, housekeeping integration)    │   │
│  │ • Guest management (profiles, history, preferences)                 │   │
│  │ • Rate management (room types, rate plans, packages)               │   │
│  │ • Folio management (posting charges, payments, transfers)          │   │
│  │ • Night audit (day close, reports)                                 │   │
│  │ • City ledger (simplified AR for walk-ins, credit guests)          │   │
│  │ • Cash management (cashier sessions, shift close)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: pms.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ pms.reservations          pms.rooms              pms.guests         │   │
│  │ pms.room_types            pms.rate_plans         pms.folios         │   │
│  │ pms.folio_transactions    pms.cashier_sessions   pms.night_audits   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints: /api/v1/pms/*                                              │
│  Events: pms.reservation.*, pms.folio.*, pms.guest.*                       │
│  Config Keys: pms.checkin.*, pms.checkout.*, pms.pricing.*                 │
│                                                                             │
│  Feature Modules (optional add-ons):                                        │
│  • pms.membership  - Guest loyalty                                         │
│  • pms.events      - Banquet & events                                      │
│  • pms.hk          - Housekeeping tasks                                    │
│  • pms.concierge   - Guest services                                        │
│  • pms.guest_app   - Guest mobile app                                      │
│  • pms.rms         - Revenue management                                    │
│  • pms.parking     - Valet parking                                         │
│  • pms.fleet       - Shuttle & transport                                   │
│  • pms.security    - Visitor & access control                              │
│  • pms.ibe         - Internet Booking Engine (website booking)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 ACC (Accounting)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: ACC (Accounting)                                                    │
│  Code: acc                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Full financial accounting                                         │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Chart of Accounts (multi-level, customizable)                     │   │
│  │ • Journal entries (manual & auto-posting)                           │   │
│  │ • Accounts Payable (vendor invoices, payments, aging)              │   │
│  │ • Accounts Receivable (customer invoices, receipts, aging)         │   │
│  │ • Bank reconciliation                                               │   │
│  │ • Period management (open, close, lock)                            │   │
│  │ • Financial statements (P&L, Balance Sheet, Cash Flow)             │   │
│  │ • Cost center / departmental accounting                            │   │
│  │ • Multi-currency support                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: acc.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ acc.chart_of_accounts     acc.journal_entries    acc.journal_lines  │   │
│  │ acc.ar_invoices           acc.ap_invoices        acc.payment_vouchers│  │
│  │ acc.bank_accounts         acc.bank_transactions  acc.fiscal_periods │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints: /api/v1/acc/*                                              │
│  Events: acc.journal_entry.*, acc.period.*, acc.invoice.*                  │
│  Config Keys: acc.fiscal.*, acc.journal.*, acc.ar.*, acc.ap.*              │
│                                                                             │
│  Feature Modules (optional add-ons):                                        │
│  • acc.budget    - Budget planning & control                               │
│  • acc.tax       - Tax management, e-Faktur                                │
│  • acc.audit     - Internal audit                                          │
│  • acc.consol    - Multi-company consolidation                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.3 POS (Point of Sale)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: POS (Point of Sale)                                                 │
│  Code: pos                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: F&B, Retail, Service outlets                                      │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Order management (dine-in, takeaway, delivery)                    │   │
│  │ • Table management (layout, status, merge/split)                   │   │
│  │ • Menu management (items, modifiers, combos, pricing)              │   │
│  │ • Kitchen display system integration                               │   │
│  │ • Payment processing (multi-tender, split bill)                    │   │
│  │ • Receipt printing                                                 │   │
│  │ • Cashier management (open/close shift)                            │   │
│  │ • Sales reports                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: pos.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ pos.outlets               pos.tables             pos.menu_items     │   │
│  │ pos.orders                pos.order_items        pos.order_payments │   │
│  │ pos.cashier_sessions      pos.receipts           pos.menu_categories│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Special: Menu Item Visibility per Outlet                                   │
│  (Using Context-Aware Visibility - Section 43.12)                          │
│                                                                             │
│  Feature Modules (optional add-ons):                                        │
│  • pos.online    - E-commerce, online ordering                             │
│  • pos.delivery  - Delivery management                                     │
│  • pos.kitchen   - Kitchen display system                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.4 LDR (Laundry)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: LDR (Laundry)                                                       │
│  Code: ldr                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Laundry operations - hotel guest, house, or commercial            │
│                                                                             │
│  Standalone: YES (can serve hotels, hospitals, commercial clients)          │
│  Integrated: PMS (guest laundry), ACC, INV, HRM                             │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Customer/client management (walk-in, hotel guest, corporate)     │   │
│  │ • Service catalog (wash, dry clean, press, alterations)            │   │
│  │ • Order/ticket management (pickup, process, delivery)              │   │
│  │ • Item tracking (garment count, condition notes, claims)           │   │
│  │ • Pricing tiers (regular, express, VIP)                            │   │
│  │ • Route management (pickup/delivery scheduling)                    │   │
│  │ • Machine management (washers, dryers, press)                      │   │
│  │ • Quality control checkpoints                                      │   │
│  │ • Lost & found tracking                                            │   │
│  │ • Production workflow tracking                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: ldr.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ldr.customers             ldr.orders              ldr.order_items   │   │
│  │ ldr.services              ldr.service_prices      ldr.machines      │   │
│  │ ldr.routes                ldr.route_stops         ldr.claims        │   │
│  │ ldr.production_batches    ldr.quality_checks      ldr.invoices      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints: /api/v1/ldr/*                                               │
│  Events: ldr.order.*, ldr.delivery.*, ldr.production.*                      │
│  Config Keys: ldr.pricing.*, ldr.workflow.*, ldr.sla.*                      │
│                                                                             │
│  Uses Building Blocks:                                                       │
│  • Billing Engine (invoicing)                                               │
│  • Payment Engine (collection)                                              │
│  • Task Engine (work orders)                                                │
│  • Document Engine (tickets, receipts)                                      │
│  • Notification Engine (pickup ready, delivery)                             │
│                                                                             │
│  Standalone Mode (e.g., commercial laundry):                                │
│  • Full customer management                                                 │
│  • Direct billing                                                           │
│  • Route optimization                                                       │
│  • Corporate contracts                                                      │
│                                                                             │
│  Integrated Mode (with PMS):                                                │
│  • Guest lookup from PMS                                                    │
│  • Charges post to folio                                                    │
│  • Room pickup/delivery scheduling                                          │
│  • Express service for VIP guests                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.5 SPA (Spa & Wellness)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: SPA (Spa & Wellness)                                                │
│  Code: spa                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Spa, wellness center, massage parlor operations                   │
│                                                                             │
│  Standalone: YES (day spa, wellness center, beauty salon)                   │
│  Integrated: PMS (hotel spa), ACC, INV, HRM, CRM                            │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Treatment/service catalog (massage, facial, body treatments)     │   │
│  │ • Therapist management (skills, availability, commission)          │   │
│  │ • Appointment booking (online, walk-in, by room)                   │   │
│  │ • Room/facility scheduling (treatment rooms, sauna, pool)          │   │
│  │ • Package management (bundled treatments)                          │   │
│  │ • Membership & vouchers (prepaid, gift cards)                      │   │
│  │ • Product sales (retail skincare, wellness products)               │   │
│  │ • Customer preferences (pressure, allergies, favorites)            │   │
│  │ • Waitlist management                                              │   │
│  │ • Revenue & utilization reports                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: spa.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spa.customers             spa.treatments          spa.therapists    │   │
│  │ spa.appointments          spa.rooms               spa.packages      │   │
│  │ spa.memberships           spa.vouchers            spa.products      │   │
│  │ spa.invoices              spa.commissions         spa.preferences   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints: /api/v1/spa/*                                               │
│  Events: spa.appointment.*, spa.treatment.*, spa.membership.*               │
│  Config Keys: spa.booking.*, spa.pricing.*, spa.commission.*                │
│                                                                             │
│  Uses Building Blocks:                                                       │
│  • Billing Engine (invoicing, packages)                                     │
│  • Payment Engine (collection, vouchers)                                    │
│  • Calendar Engine (appointment scheduling)                                 │
│  • Membership Engine (loyalty, prepaid)                                     │
│  • Notification Engine (reminders, confirmations)                           │
│                                                                             │
│  Standalone Mode (e.g., day spa):                                           │
│  • Full customer management                                                 │
│  • Direct billing & payments                                                │
│  • Own membership program                                                   │
│  • Retail product sales                                                     │
│                                                                             │
│  Integrated Mode (with PMS):                                                │
│  • Guest lookup from PMS                                                    │
│  • Charges post to folio                                                    │
│  • Room delivery service                                                    │
│  • VIP guest preferences sync                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.6 GYM (Fitness Center)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE: GYM (Fitness Center)                                                │
│  Code: gym                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Fitness center, gym, sports club operations                       │
│                                                                             │
│  Standalone: YES (fitness center, yoga studio, sports club)                 │
│  Integrated: PMS (hotel gym), ACC, HRM, AST, CRM                            │
│                                                                             │
│  Core Features:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Membership management (plans, renewals, freezing)                │   │
│  │ • Class/session scheduling (yoga, aerobic, spinning)               │   │
│  │ • Trainer management (specialization, availability)                │   │
│  │ • Personal training booking                                        │   │
│  │ • Equipment tracking (maintenance, availability)                   │   │
│  │ • Access control (check-in/out, capacity limits)                   │   │
│  │ • Locker management                                                │   │
│  │ • Body metrics tracking (optional)                                 │   │
│  │ • Attendance & usage reports                                        │   │
│  │ • Revenue & membership reports                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Schema: gym.*                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ gym.members               gym.memberships         gym.trainers      │   │
│  │ gym.classes               gym.class_schedules     gym.bookings      │   │
│  │ gym.equipment             gym.lockers             gym.check_ins     │   │
│  │ gym.personal_training     gym.invoices            gym.metrics       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints: /api/v1/gym/*                                               │
│  Events: gym.membership.*, gym.class.*, gym.checkin.*                       │
│  Config Keys: gym.access.*, gym.membership.*, gym.capacity.*                │
│                                                                             │
│  Uses Building Blocks:                                                       │
│  • Billing Engine (membership billing)                                      │
│  • Payment Engine (collection, auto-debit)                                  │
│  • Calendar Engine (class scheduling)                                       │
│  • Membership Engine (plans, renewals)                                      │
│  • Notification Engine (class reminders, renewals)                          │
│                                                                             │
│  Standalone Mode (e.g., fitness center):                                    │
│  • Full member management                                                   │
│  • Direct billing & auto-renewal                                            │
│  • Own membership tiers                                                     │
│  • Class packages                                                           │
│                                                                             │
│  Integrated Mode (with PMS):                                                │
│  • Guest access (complimentary or charged)                                  │
│  • Charges post to folio                                                    │
│  • Hotel guest check-in bypass                                              │
│  • VIP unlimited access                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

*(Similar detail blocks for INV, HRM, CHM, PROC, AST, CRM, PRJ)*

---

## 5. Feature Modules

### 5.1 Overview

Feature Modules adalah **sub-modules** yang memerlukan parent module untuk beroperasi.

### 5.2 Feature Module Registry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FEATURE MODULE REGISTRY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┬───────────────────────┬────────────────────────────┐   │
│  │ Parent         │ Feature Module        │ Description                │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ PMS            │ pms.membership        │ Guest loyalty & points     │   │
│  │                │ pms.events            │ Banquet & event management │   │
│  │                │ pms.hk                │ Housekeeping task mgmt     │   │
│  │                │ pms.concierge         │ Guest services & requests  │   │
│  │                │ pms.guest_app         │ Guest mobile application   │   │
│  │                │ pms.rms               │ Revenue management system  │   │
│  │                │ pms.parking           │ Valet parking & vehicle    │   │
│  │                │ pms.fleet             │ Shuttle & transport mgmt   │   │
│  │                │ pms.security          │ Visitor & access control   │   │
│  │                │ pms.ibe               │ Internet Booking Engine    │   │
│  │                │                       │                            │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ HRM            │ hrm.payroll           │ Salary processing (+ACC)   │   │
│  │                │ hrm.membership        │ Employee benefits          │   │
│  │                │ hrm.eng               │ Engineering/maintenance    │   │
│  │                │ hrm.it                │ IT support & helpdesk      │   │
│  │                │ hrm.recruit           │ Recruitment & onboarding   │   │
│  │                │ hrm.training          │ Training management        │   │
│  │                │ hrm.security          │ Security guard mgmt        │   │
│  │                │                       │                            │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ ACC            │ acc.budget            │ Budget planning & control  │   │
│  │                │ acc.tax               │ Tax management, e-Faktur   │   │
│  │                │ acc.audit             │ Internal audit management  │   │
│  │                │ acc.consol            │ Multi-company consolidation│   │
│  │                │                       │                            │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ INV            │ inv.supplier_portal   │ Supplier self-service      │   │
│  │                │                       │                            │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ POS            │ pos.online            │ E-commerce, online order   │   │
│  │                │ pos.delivery          │ Delivery management        │   │
│  │                │ pos.kitchen           │ Kitchen display system     │   │
│  │                │ pos.reservation       │ Table/restaurant booking   │   │
│  │                │                       │                            │   │
│  ├────────────────┼───────────────────────┼────────────────────────────┤   │
│  │                │                       │                            │   │
│  │ AST            │ ast.maintenance       │ Preventive maintenance     │   │
│  │                │                       │                            │   │
│  └────────────────┴───────────────────────┴────────────────────────────┘   │
│                                                                             │
│  Cross-Attach Modules (Can attach to multiple parents):                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Feature           │ Can Attach To         │ Notes                   │   │
│  ├───────────────────┼───────────────────────┼─────────────────────────┤   │
│  │ Task Management   │ PMS, HRM, PRJ         │ HK, Eng, IT, Generic    │   │
│  │ Membership        │ PMS, HRM, POS         │ Guest, Staff, Customer  │   │
│  │ Maintenance       │ HRM.ENG, AST, PMS     │ Work orders             │   │
│  └───────────────────┴───────────────────────┴─────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Platform Modules (Multi-Property / Hotel Chain)

Platform Modules adalah **special modules** untuk operasi multi-property atau hotel chain.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLATFORM MODULES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  CRS - Central Reservation System                                     │ │
│  │  ──────────────────────────────────────────────────────────────────   │ │
│  │  Code: crs                                                            │ │
│  │  Type: Platform Layer (sits above PMS instances)                      │ │
│  │                                                                        │ │
│  │  Purpose:                                                              │ │
│  │  • Multi-property reservation management                              │ │
│  │  • Central availability & rate distribution                          │ │
│  │  • Cross-property booking & transfer                                  │ │
│  │  • Chain-wide loyalty program                                         │ │
│  │  • Corporate rate management                                          │ │
│  │  • Central reporting & analytics                                      │ │
│  │                                                                        │ │
│  │  Integrates: Multiple PMS instances, CHM, CRM                         │ │
│  │                                                                        │ │
│  │  Database Schema: crs.*                                               │ │
│  │  API Endpoints: /api/v1/crs/*                                         │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  S&C - Sales & Catering                                               │ │
│  │  ──────────────────────────────────────────────────────────────────   │ │
│  │  Code: snc                                                            │ │
│  │  Type: Hybrid Module (combines CRM + pms.events)                      │ │
│  │                                                                        │ │
│  │  Purpose:                                                              │ │
│  │  • Corporate account management                                       │ │
│  │  • Group bookings & block management                                  │ │
│  │  • Contract rates & negotiated pricing                                │ │
│  │  • RFP (Request for Proposal) management                              │ │
│  │  • Sales pipeline & opportunity tracking                              │ │
│  │  • Banquet event order (BEO) management                               │ │
│  │  • Catering proposals & contracts                                     │ │
│  │                                                                        │ │
│  │  Integrates: PMS, pms.events, CRM, ACC                                │ │
│  │                                                                        │ │
│  │  Database Schema: snc.*                                               │ │
│  │  API Endpoints: /api/v1/snc/*                                         │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Architecture:                                                              │
│                                                                             │
│            ┌─────────────────────────────────────────┐                     │
│            │              CRS (Platform)             │                     │
│            │   Central Reservation & Distribution    │                     │
│            └──────────────────┬──────────────────────┘                     │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                      │
│         │                     │                     │                      │
│         ▼                     ▼                     ▼                      │
│    ┌─────────┐          ┌─────────┐          ┌─────────┐                  │
│    │  PMS    │          │  PMS    │          │  PMS    │                  │
│    │ Hotel A │          │ Hotel B │          │ Hotel C │                  │
│    └─────────┘          └─────────┘          └─────────┘                  │
│         │                     │                     │                      │
│         └─────────────────────┼─────────────────────┘                      │
│                               │                                             │
│                               ▼                                             │
│                        ┌─────────────┐                                     │
│                        │     S&C     │                                     │
│                        │ Sales &     │                                     │
│                        │ Catering    │                                     │
│                        └─────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Cross-Module Add-ons

Cross-Module Add-ons adalah **special modules** yang menganalisis atau bekerja lintas multiple modules.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CROSS-MODULE ADD-ONS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Characteristics:                                                           │
│  • Tidak bisa standalone (butuh data dari module lain)                     │
│  • Tidak punya single parent (cross-cutting)                               │
│  • Valuable sebagai subscription tambahan                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  FDA - Fraud Detection & Audit Intelligence                           │ │
│  │  ──────────────────────────────────────────────────────────────────   │ │
│  │  Code: fda                                                            │ │
│  │  Type: Cross-Module Add-on                                            │ │
│  │                                                                        │ │
│  │  Purpose:                                                              │ │
│  │  • Detect fraud, cheating, anomalies across all modules               │ │
│  │  • Three-layer detection: Rule + ML + LLM                             │ │
│  │  • Explainable alerts with recommendations                            │ │
│  │  • Super-restricted access (Auditor/Owner only)                       │ │
│  │                                                                        │ │
│  │  Requires: At least 1 analyzable module                               │ │
│  │  (PMS, POS, ACC, INV, HRM, PROC, SPA, GYM, LDR)                       │ │
│  │                                                                        │ │
│  │  Tiers:                                                                │ │
│  │  • FDA Basic: Rule-based detection                                    │ │
│  │  • FDA Pro: Rule + ML detection                                       │ │
│  │  • FDA Enterprise: Rule + ML + LLM analysis                           │ │
│  │                                                                        │ │
│  │  Reference: [Standard #44](./DEVELOPMENT_STANDARDS_V13.md)            │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Architecture:                                                              │
│                                                                             │
│                        ┌─────────────────────┐                             │
│                        │   FDA Engine        │                             │
│                        │ ┌─────┬─────┬─────┐ │                             │
│                        │ │Rule │ ML  │ LLM │ │                             │
│                        │ └─────┴─────┴─────┘ │                             │
│                        └──────────┬──────────┘                             │
│                                   │                                         │
│           ┌───────────────────────┼───────────────────────┐                │
│           │           │           │           │           │                │
│           ▼           ▼           ▼           ▼           ▼                │
│       ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐            │
│       │ PMS │     │ POS │     │ ACC │     │ INV │     │ HRM │            │
│       └─────┘     └─────┘     └─────┘     └─────┘     └─────┘            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  ICH - Internal Collaboration Hub                                     │ │
│  │  ──────────────────────────────────────────────────────────────────   │ │
│  │  Code: ich                                                            │ │
│  │  Type: Cross-Module Add-on                                            │ │
│  │                                                                        │ │
│  │  Purpose:                                                              │ │
│  │  • Internal messaging (DM, group, department channels)                │ │
│  │  • Notes & knowledge base (personal, dept, org levels)                │ │
│  │  • Flag & thread system (flag any entity, track resolution)           │ │
│  │  • Task board (from flags, manual, FDA alerts)                        │ │
│  │  • Entity sharing in chat (with permission check)                     │ │
│  │                                                                        │ │
│  │  Requires: At least 1 other module                                    │ │
│  │                                                                        │ │
│  │  Tiers:                                                                │ │
│  │  • ICH Basic: Chat + Notes only                                       │ │
│  │  • ICH Pro: + Flags + Threads + Entity sharing                        │ │
│  │  • ICH Enterprise: + Task board + FDA integration                     │ │
│  │                                                                        │ │
│  │  Reference: [Standard #45](./DEVELOPMENT_STANDARDS_V14.md)            │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Architecture:                                                              │
│                                                                             │
│              ┌───────────────────────────────────────────┐                 │
│              │             ICH Engine                     │                 │
│              │ ┌────────┬────────┬────────┬────────────┐ │                 │
│              │ │  Chat  │ Notes  │ Flags  │   Tasks    │ │                 │
│              │ └────────┴────────┴────────┴────────────┘ │                 │
│              └─────────────────────┬─────────────────────┘                 │
│                                    │                                        │
│      ┌─────────────────────────────┼─────────────────────────────┐         │
│      │         │         │         │         │         │         │         │
│      ▼         ▼         ▼         ▼         ▼         ▼         ▼         │
│  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐     │
│  │ PMS │   │ POS │   │ ACC │   │ INV │   │ HRM │   │ SPA │   │ FDA │     │
│  └─────┘   └─────┘   └─────┘   └─────┘   └─────┘   └─────┘   └─────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Points

### 6.1 Overview

Integration Points adalah **otomatis unlocked** ketika organisasi subscribe ke 2+ related modules.

### 6.2 Integration Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION POINTS MATRIX                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┬─────────────────────────────────────────────────┐  │
│  │ Integration        │ Features Unlocked                                │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PMS + ACC          │ • Folio posting → Journal entry (auto)          │  │
│  │                    │ • City Ledger → Full AR management              │  │
│  │                    │ • Guest deposit → Liability accounts            │  │
│  │                    │ • Revenue by department → Cost centers          │  │
│  │                    │ • Full financial statements                     │  │
│  │                    │ • Departmental P&L                              │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PMS + CHM          │ • 2-way sync: availability, rates, bookings     │  │
│  │                    │ • Auto room allocation from OTA                 │  │
│  │                    │ • Rate parity management                        │  │
│  │                    │ • Channel performance analytics                 │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PMS + POS          │ • Room charge (post F&B to guest folio)         │  │
│  │                    │ • Guest lookup from POS                         │  │
│  │                    │ • Combined billing                              │  │
│  │                    │ • Guest preferences in F&B                      │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PMS + INV          │ • Minibar tracking                              │  │
│  │                    │ • Amenities stock management                    │  │
│  │                    │ • Housekeeping supplies                         │  │
│  │                    │ • Auto stock deduction                          │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PMS + HRM          │ • Staff scheduling per department               │  │
│  │                    │ • Room attendant assignment                     │  │
│  │                    │ • Night audit staffing                          │  │
│  │                    │ • Staff room allocation (for employee stays)    │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ POS + ACC          │ • Sales → Journal entry (auto)                  │  │
│  │                    │ • Daily settlement posting                      │  │
│  │                    │ • Revenue recognition                           │  │
│  │                    │ • Cash over/short tracking                      │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ POS + INV          │ • Auto stock deduction on sale                  │  │
│  │                    │ • Recipe costing                                │  │
│  │                    │ • Food cost percentage                          │  │
│  │                    │ • Low stock alerts                              │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ INV + ACC          │ • Stock valuation → GL                          │  │
│  │                    │ • COGS calculation                              │  │
│  │                    │ • Inventory adjustment → Journal                │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ INV + PROC         │ • PO → Receiving → Stock update                 │  │
│  │                    │ • 3-way matching                                │  │
│  │                    │ • Auto reorder from min stock                   │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ PROC + ACC         │ • PO → AP Invoice                               │  │
│  │                    │ • 3-way matching with accounting                │  │
│  │                    │ • Vendor payment scheduling                     │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ HRM + ACC          │ • Payroll → Journal entry                       │  │
│  │                    │ • Cost allocation by department                 │  │
│  │                    │ • PPh 21 calculation & reporting                │  │
│  │                    │ • BPJS posting                                  │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ LDR + PMS          │ • Guest laundry → Folio charge                  │  │
│  │                    │ • Room pickup/delivery scheduling               │  │
│  │                    │ • Guest preferences sync                        │  │
│  │                    │ • Express laundry for VIP guests                │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ LDR + ACC          │ • Laundry revenue → Journal entry               │  │
│  │                    │ • Cost tracking by service type                 │  │
│  │                    │ • Departmental P&L                              │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ LDR + INV          │ • Detergent/supplies consumption                │  │
│  │                    │ • Auto stock deduction                          │  │
│  │                    │ • Supplies cost allocation                      │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ LDR + HRM          │ • Staff scheduling for laundry                  │  │
│  │                    │ • Workload distribution                         │  │
│  │                    │ • Productivity tracking                         │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ SPA + PMS          │ • Guest spa → Folio charge                      │  │
│  │                    │ • Guest preferences sync                        │  │
│  │                    │ • VIP priority booking                          │  │
│  │                    │ • Room delivery service                         │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ SPA + ACC          │ • Spa revenue → Journal entry                   │  │
│  │                    │ • Therapist commission posting                  │  │
│  │                    │ • Departmental P&L                              │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ SPA + INV          │ • Product consumption tracking                  │  │
│  │                    │ • Retail stock deduction                        │  │
│  │                    │ • Supplies cost allocation                      │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ SPA + HRM          │ • Therapist scheduling                          │  │
│  │                    │ • Commission calculation                        │  │
│  │                    │ • Skill-based assignment                        │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ GYM + PMS          │ • Guest gym access → Folio charge               │  │
│  │                    │ • Hotel guest check-in bypass                   │  │
│  │                    │ • VIP unlimited access                          │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ GYM + ACC          │ • Gym revenue → Journal entry                   │  │
│  │                    │ • Membership billing                            │  │
│  │                    │ • Departmental P&L                              │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ GYM + HRM          │ • Trainer scheduling                            │  │
│  │                    │ • PT commission tracking                        │  │
│  │                    │ • Class instructor assignment                   │  │
│  │                    │                                                  │  │
│  ├────────────────────┼─────────────────────────────────────────────────┤  │
│  │                    │                                                  │  │
│  │ GYM + AST          │ • Equipment as fixed assets                     │  │
│  │                    │ • Maintenance scheduling                        │  │
│  │                    │ • Depreciation tracking                         │  │
│  │                    │                                                  │  │
│  └────────────────────┴─────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Integration Event Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION EVENT FLOW: PMS + ACC                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  PMS Module                          ACC Module                       │ │
│  │  ┌─────────────┐                     ┌─────────────┐                  │ │
│  │  │   Folio     │                     │   Journal   │                  │ │
│  │  │  Payment    │                     │   Entry     │                  │ │
│  │  │  Posted     │                     │   Created   │                  │ │
│  │  └──────┬──────┘                     └──────▲──────┘                  │ │
│  │         │                                   │                          │ │
│  │         │ Event: pms.folio.payment_added    │                          │ │
│  │         │                                   │                          │ │
│  │         ▼                                   │                          │ │
│  │  ┌─────────────────────────────────────────┴──────┐                   │ │
│  │  │              INTEGRATION SERVICE               │                   │ │
│  │  │          (integration.pms_to_acc)              │                   │ │
│  │  ├────────────────────────────────────────────────┤                   │ │
│  │  │                                                │                   │ │
│  │  │  1. Listen to pms.folio.payment_added         │                   │ │
│  │  │  2. Get folio details & payment info          │                   │ │
│  │  │  3. Map to accounting entries:                │                   │ │
│  │  │     DR: Cash/Bank      CR: Revenue            │                   │ │
│  │  │     DR: Cash           CR: Tax Payable        │                   │ │
│  │  │  4. Create journal entry                      │                   │ │
│  │  │  5. Link reference (folio_id ↔ journal_id)    │                   │ │
│  │  │  6. Publish: integration.pms_to_acc.posted    │                   │ │
│  │  │                                                │                   │ │
│  │  └────────────────────────────────────────────────┘                   │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Database: shared.module_references                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id │ source_module │ source_entity     │ source_id │ target_module │  │ │
│  ├────┼───────────────┼───────────────────┼───────────┼───────────────┤  │ │
│  │ 1  │ pms           │ folio_payments    │ 12345     │ acc           │  │ │
│  │    │               │                   │           │               │  │ │
│  │    │ target_entity │ target_id         │           │               │  │ │
│  │    │ journal_entries│ 67890            │           │               │  │ │
│  └────┴───────────────┴───────────────────┴───────────┴───────────────┘   │
│                                                                             │
│  Reference: [Event Schema - Standard #18](./DEVELOPMENT_STANDARDS_V3.md)   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Module Configuration

### 7.1 Config-Driven Behavior

Setiap module behavior dikontrol via configuration, bukan hardcode.

**Reference**: [Config Governance - Standard #43](./DEVELOPMENT_STANDARDS_V12.md)
**Reference**: [Flexible Configuration - Section 9](./SHARED_CODE_STANDARDS.md)

### 7.2 Config Key Naming

**Format**: `{module}.{category}.{name}`

```yaml
# PMS Config Examples
pms.checkin.default_time: "14:00"
pms.checkout.default_time: "12:00"
pms.pricing.tax_rate: 11
pms.pricing.service_charge: 10
pms.folio.allow_negative_balance: false
pms.folio.require_deposit: true

# POS Config Examples
pos.order.auto_print_receipt: true
pos.pricing.tax_rate: 10
pos.receipt.footer_text: "Thank you for dining with us"

# ACC Config Examples
acc.fiscal.year_start_month: 1
acc.journal.require_approval: true
acc.period.auto_close: false

# Shared Config
shared.currency.default: "IDR"
shared.locale.timezone: "Asia/Jakarta"
```

**Reference**: [Section 1.7.7 - Config Key Naming](./DEVELOPMENT_STANDARDS.md)

### 7.3 Context-Aware Visibility

Data yang sama, visibility berbeda per context.

**Examples**:
- Payment methods: FO sees all, FB sees subset
- Menu items: Different per outlet
- Reports: Different per role

**Reference**: [Section 43.12 - Context-Aware Visibility](./DEVELOPMENT_STANDARDS_V12.md)

---

## 8. Subscription Scenarios

### 8.1 Common Scenarios

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SUBSCRIPTION SCENARIOS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO 1: Small Hotel (Budget)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: PMS only                                              │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ Full hotel operations                                             │   │
│  │ ✓ Folio & billing                                                   │   │
│  │ ✓ Basic city ledger                                                 │   │
│  │ ✓ Cash management                                                   │   │
│  │ ✓ Revenue reports                                                   │   │
│  │                                                                      │   │
│  │ Sufficient for: Small hotel, no F&B, basic accounting               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCENARIO 2: Medium Hotel                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: PMS + POS + CHM + ACC                                 │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ Full hotel operations                                             │   │
│  │ ✓ F&B operations with room charge                                   │   │
│  │ ✓ OTA integration (2-way sync)                                      │   │
│  │ ✓ Full accounting with auto-posting                                 │   │
│  │ ✓ Financial statements                                              │   │
│  │                                                                      │   │
│  │ Integration unlocked:                                                │   │
│  │ • PMS+ACC, PMS+CHM, PMS+POS, POS+ACC                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCENARIO 3: Restaurant (Non-Hotel)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: POS + INV + ACC                                       │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ Full F&B operations                                               │   │
│  │ ✓ Stock management with auto-deduction                              │   │
│  │ ✓ Full accounting                                                   │   │
│  │ ✓ Food cost analysis                                                │   │
│  │                                                                      │   │
│  │ No PMS features (not relevant for standalone restaurant)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCENARIO 4: Trading Company                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: ACC + INV + PROC                                      │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ Full accounting                                                   │   │
│  │ ✓ Inventory management                                              │   │
│  │ ✓ Procurement & PO                                                  │   │
│  │ ✓ AP/AR management                                                  │   │
│  │                                                                      │   │
│  │ This is "Supplier App" combination                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCENARIO 5: Channel Manager Only                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: CHM only (for hotel with other PMS)                   │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ OTA connections                                                   │   │
│  │ ✓ Rate management                                                   │   │
│  │ ✓ Manual availability sync                                          │   │
│  │                                                                      │   │
│  │ Limitation: No auto-sync with PMS (manual inventory)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCENARIO 6: HR Outsourcing Company                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Subscriptions: HRM + hrm.payroll + ACC                               │   │
│  │                                                                      │   │
│  │ Available:                                                           │   │
│  │ ✓ Employee management                                               │   │
│  │ ✓ Attendance & leave                                                │   │
│  │ ✓ Full payroll processing                                           │   │
│  │ ✓ Payroll → Journal integration                                     │   │
│  │ ✓ Tax calculation & reporting                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Module Code Registry

### 9.1 Official Module Codes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MODULE CODE REGISTRY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE MODULES                                                               │
│  ┌────────┬─────────────────────────┬───────────────────────────────────┐  │
│  │ Code   │ Name                    │ Description                       │  │
│  ├────────┼─────────────────────────┼───────────────────────────────────┤  │
│  │ pms    │ Property Management     │ Hotel operations                  │  │
│  │ pos    │ Point of Sale           │ F&B, Retail                       │  │
│  │ acc    │ Accounting              │ Financial accounting              │  │
│  │ inv    │ Inventory               │ Stock management                  │  │
│  │ hrm    │ Human Resources         │ HR operations                     │  │
│  │ chm    │ Channel Manager         │ OTA integration                   │  │
│  │ proc   │ Procurement             │ Purchasing                        │  │
│  │ ast    │ Asset Management        │ Fixed assets                      │  │
│  │ crm    │ Customer Relations      │ Guest/customer relationships      │  │
│  │ prj    │ Project Management      │ Projects & tasks                  │  │
│  │ ldr    │ Laundry                 │ Laundry operations                │  │
│  │ spa    │ Spa & Wellness          │ Day spa, wellness center          │  │
│  │ gym    │ Fitness Center          │ Gym, fitness club                 │  │
│  └────────┴─────────────────────────┴───────────────────────────────────┘  │
│                                                                             │
│  PLATFORM MODULES (Multi-Property / Chain)                                  │
│  ┌────────┬─────────────────────────┬───────────────────────────────────┐  │
│  │ Code   │ Name                    │ Description                       │  │
│  ├────────┼─────────────────────────┼───────────────────────────────────┤  │
│  │ crs    │ Central Reservation     │ Multi-property central system     │  │
│  │ snc    │ Sales & Catering        │ Corporate sales, group bookings   │  │
│  └────────┴─────────────────────────┴───────────────────────────────────┘  │
│                                                                             │
│  FEATURE MODULES                                                            │
│  ┌──────────────────┬─────────────────────────┬─────────────────────────┐  │
│  │ Code             │ Name                    │ Parent                  │  │
│  ├──────────────────┼─────────────────────────┼─────────────────────────┤  │
│  │ pms.membership   │ Guest Membership        │ PMS                     │  │
│  │ pms.events       │ Events & Banquet        │ PMS                     │  │
│  │ pms.hk           │ Housekeeping            │ PMS                     │  │
│  │ pms.concierge    │ Concierge Services      │ PMS                     │  │
│  │ pms.guest_app    │ Guest Mobile App        │ PMS                     │  │
│  │ pms.rms          │ Revenue Management      │ PMS                     │  │
│  │ pms.parking      │ Valet Parking           │ PMS                     │  │
│  │ pms.fleet        │ Shuttle & Transport     │ PMS                     │  │
│  │ pms.security     │ Visitor & Access Ctrl   │ PMS                     │  │
│  │ pms.ibe          │ Internet Booking Engine │ PMS                     │  │
│  │ hrm.payroll      │ Payroll                 │ HRM                     │  │
│  │ hrm.membership   │ Employee Benefits       │ HRM                     │  │
│  │ hrm.eng          │ Engineering Tasks       │ HRM (or PMS)            │  │
│  │ hrm.it           │ IT Support              │ HRM                     │  │
│  │ hrm.recruit      │ Recruitment             │ HRM                     │  │
│  │ hrm.training     │ Training                │ HRM                     │  │
│  │ hrm.security     │ Security Guard Mgmt     │ HRM                     │  │
│  │ acc.budget       │ Budgeting               │ ACC                     │  │
│  │ acc.tax          │ Tax Management          │ ACC                     │  │
│  │ acc.audit        │ Internal Audit          │ ACC                     │  │
│  │ acc.consol       │ Consolidation           │ ACC                     │  │
│  │ inv.supplier     │ Supplier Portal         │ INV                     │  │
│  │ pos.online       │ E-Commerce              │ POS                     │  │
│  │ pos.delivery     │ Delivery Management     │ POS                     │  │
│  │ pos.kitchen      │ Kitchen Display         │ POS                     │  │
│  │ pos.reservation  │ Table Reservation       │ POS                     │  │
│  │ ast.maintenance  │ Maintenance Schedule    │ AST                     │  │
│  └──────────────────┴─────────────────────────┴─────────────────────────┘  │
│                                                                             │
│  CROSS-MODULE ADD-ONS                                                       │
│  ┌────────┬─────────────────────────┬───────────────────────────────────┐  │
│  │ Code   │ Name                    │ Description                       │  │
│  ├────────┼─────────────────────────┼───────────────────────────────────┤  │
│  │ fda    │ Fraud Detection & Audit │ Fraud/anomaly detection           │  │
│  │ ich    │ Internal Collab Hub     │ Chat, notes, flags, tasks         │  │
│  └────────┴─────────────────────────┴───────────────────────────────────┘  │
│                                                                             │
│  SHARED (Not subscribed, always available)                                  │
│  ┌────────┬───────────────────────────────────────────────────────────────┐│
│  │ shared │ Shared data & services (payment methods, currencies, etc)    ││
│  │ lookup │ Lookup tables                                                 ││
│  │ integ  │ Integration services                                          ││
│  └────────┴───────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Python Enum

```python
# shared/constants/modules.py

from enum import Enum

class ModuleCode(str, Enum):
    """Core module codes"""
    PMS = "pms"
    POS = "pos"
    ACC = "acc"
    INV = "inv"
    HRM = "hrm"
    CHM = "chm"
    PROC = "proc"
    AST = "ast"
    CRM = "crm"
    PRJ = "prj"
    LDR = "ldr"   # Laundry - standalone capable
    SPA = "spa"   # Spa & Wellness - standalone capable
    GYM = "gym"   # Fitness Center - standalone capable

class PlatformModuleCode(str, Enum):
    """Platform module codes (multi-property / chain)"""
    CRS = "crs"   # Central Reservation System
    SNC = "snc"   # Sales & Catering

class CrossModuleCode(str, Enum):
    """Cross-module add-on codes (requires other modules)"""
    FDA = "fda"   # Fraud Detection & Audit Intelligence
    ICH = "ich"   # Internal Collaboration Hub

class FeatureModuleCode(str, Enum):
    """Feature module codes"""
    # PMS Features
    PMS_MEMBERSHIP = "pms.membership"
    PMS_EVENTS = "pms.events"
    PMS_HK = "pms.hk"
    PMS_CONCIERGE = "pms.concierge"
    PMS_GUEST_APP = "pms.guest_app"
    PMS_RMS = "pms.rms"
    PMS_PARKING = "pms.parking"
    PMS_FLEET = "pms.fleet"
    PMS_SECURITY = "pms.security"
    PMS_IBE = "pms.ibe"

    # HRM Features
    HRM_PAYROLL = "hrm.payroll"
    HRM_MEMBERSHIP = "hrm.membership"
    HRM_ENG = "hrm.eng"
    HRM_IT = "hrm.it"
    HRM_RECRUIT = "hrm.recruit"
    HRM_TRAINING = "hrm.training"
    HRM_SECURITY = "hrm.security"

    # ACC Features
    ACC_BUDGET = "acc.budget"
    ACC_TAX = "acc.tax"
    ACC_AUDIT = "acc.audit"
    ACC_CONSOL = "acc.consol"

    # INV Features
    INV_SUPPLIER = "inv.supplier"

    # POS Features
    POS_ONLINE = "pos.online"
    POS_DELIVERY = "pos.delivery"
    POS_KITCHEN = "pos.kitchen"
    POS_RESERVATION = "pos.reservation"

    # AST Features
    AST_MAINTENANCE = "ast.maintenance"
```

---

## Summary

| Aspect | Description | Reference |
|--------|-------------|-----------|
| **Philosophy** | Build once, use everywhere | This document |
| **Building Blocks** | 13 shared engines (incl. Observability) | Section 3 |
| **Core Modules** | 13 standalone-capable | Section 4 |
| **Platform Modules** | 2 multi-property/chain | Section 5.3 |
| **Cross-Module Add-ons** | 2 cross-module add-ons | Section 5.4 |
| **Feature Modules** | 25+ requiring parent | Section 5 |
| **Integration** | Auto-enabled when both subscribed | Section 6 |
| **Configuration** | Config-driven behavior | [Standard #43](./DEVELOPMENT_STANDARDS_V12.md) |
| **Naming** | Cross-module naming convention | [Section 1.7](./DEVELOPMENT_STANDARDS.md) |
| **Visibility** | Context-aware per module | [Section 43.12](./DEVELOPMENT_STANDARDS_V12.md) |

---

*Last Updated: 2025-12-11 (Observability Engine added to Core Building Blocks)*
