# REF-04: Subscription & Dependency Matrix

This document is the **definitive reference for subscription bundling rules, module dependencies, and validation logic**. It governs how modules are sold together, which combinations are valid, and what dependencies must be satisfied.

**Usage**: Consult this when:
- Designing subscription packages
- Validating module combinations before enabling
- Planning feature gating
- Implementing billing and licensing

---

## Core Principles (Locked)

### Principle 1: All Money-Receiving Modules Require Accounting
```
IF module receives payments/revenue
THEN module MUST bundle with Accounting Core

EXAMPLES:
✅ PMS + Accounting (required)
✅ POS (with or without bundling, but if standalone needs Accounting)
✅ SPA + Accounting (required)
❌ PMS alone (forbidden)
❌ SPA alone without Accounting (forbidden)
```

### Principle 2: Standalone ≠ Independent of Accounting
```
Standalone means: "Can operate without [other operational module like PMS]"
NOT "Can operate without Accounting"

POS is standalone = "Can operate without PMS"
POS is NOT standalone = "Can't operate without Accounting"
```

### Principle 3: Subscription Controls Access, Not Architecture
```
Architecture is fixed (all code present)
Subscription controls:
  ✅ Which features visible in UI
  ✅ Which API endpoints available
  ✅ Which modules can be used
  ❌ Does NOT change database schema
  ❌ Does NOT change code paths
  ❌ Does NOT add/remove tables
```

### Principle 4: Dependency Validation at Subscription Level
```
Validation location: Application layer (subscription service)
NOT in database constraints
NOT in hardcoded logic
NOT in stored procedures

Result: If dependency not met, return error to user
Example: "PMS requires Accounting. Please add Accounting to subscription."
```

### Principle 5: Subscription Status vs. Module Status (Two Layers)
```
LAYER 1: SUBSCRIPTION STATUS (Billing/Contract)
  subscription.status ∈ {active, inactive, expired, cancelled}
  Controls: Licensing rights, billing, contractual access
  Example: Tenant has paid for PMS (subscription.status = active)

LAYER 2: MODULE STATUS (Operations/Feature Gate)
  module.is_enabled ∈ {true, false}
  Controls: Runtime feature visibility, API access
  Example: Owner can disable PMS temporarily (module.is_enabled = false)

ACCESS DECISION:
  is_accessible = subscription.status = 'active' AND module.is_enabled = true

IMPORTANT:
  ✅ Disabling module (is_enabled = false) preserves data (not deleted)
  ✅ Can re-enable module later (data returns)
  ❌ Module status does NOT affect billing (subscription independent)
  ❌ Subscription status does NOT affect data (only query access)
```

---

## Module Category Mapping (Authoritative)

All modules in ARSAKA_PANDAWA fit into four categories:

### Category 1: Foundation (Core Infrastructure)
Foundation modules are required for all operations. Every tenant must have at least one to operate.

| Module | Code | Purpose | Standalone | Accounting Required |
|--------|------|---------|-----------|---------------------|
| **Accounting Core** | ACC | Financial ledger, GL, reporting | ✅ Yes (for accountants) | N/A (IS accounting) |

### Category 2: Engine (Cross-Module Services)
Engines provide services used by multiple domain modules. NOT sold standalone.

| Module | Code | Purpose | Standalone | Dependencies |
|--------|------|---------|-----------|--------------|
| **Notification Engine** | NOTIF | Email, SMS, push notifications | ❌ No | Any domain module |
| **Workflow Engine** | WF | Approvals, state machines | ❌ No | Used internally |
| **User & Tenant Mgmt** | AUTH | Identity, membership, RBAC | ❌ No | Internal platform |

### Category 3: Domain (Business Operations)
Domain modules implement specific business processes. Directly handle transactions.

| Module | Code | Purpose | Standalone | Accounting Required | Rule |
|--------|------|---------|-----------|-------------------|------|
| **PMS** | PMS | Hotel reservations, check-in | ❌ No | ✅ Yes | Rule A |
| **POS** | POS | Restaurant/retail sales | ✅ Yes | ✅ Yes (with Accounting) | Rule A |
| **Inventory** | INV | Stock tracking, COGS | ✅ Yes | ❌ Optional | Rule A |
| **Procurement** | PROC | Purchase orders, suppliers | ✅ Yes | ❌ Preferred with INV | Rule A |
| **HR & Payroll** | HRM | Employee management, payroll | ✅ Yes | ✅ Yes | Rule A |
| **SPA** | SPA | Spa/wellness services | ✅ Yes (own tenant) | ✅ Yes (always) | Rule B |
| **GYM** | GYM | Fitness/gym operations | ✅ Yes (own tenant) | ✅ Yes (always) | Rule B |
| **Laundry** | LDR | Laundry services | ✅ Yes (own tenant) | ✅ Yes (always) | Rule B |
| **CRS** | CRS | Multi-property central reservations | ✅ Yes | ✅ Yes (implied) | Rule C |
| **Sales & Content** | S&C | Events, banquets, content | ✅ Yes | ✅ Yes (implied) | Rule C |

### Category 4: Add-On (Domain Extensions)
Add-ons enhance domain modules. Cannot be sold alone.

| Module | Code | Purpose | Standalone | Minimum Required |
|--------|------|---------|-----------|-----------------|
| **Internal Collab Hub** | ICH | Team communication, collaboration | ❌ No | ≥1 domain module (Rule D) |
| **Fraud & Audit Intelligence** | FDA | Financial fraud detection | ❌ No | Accounting module (Rule D) |
| **Advanced Notification** | ADNOTIF | Enhanced notification features | ❌ No | Any module + Notification Engine (Rule D) |
| **Reporting & Analytics** | REPORT | BI dashboards, analytics | ❌ No | Any module (Rule D) |
| **Digital Signage** | SIGNAGE | Device/content/playlist management | ✅ Yes | None (fully standalone, Rule E) |

**Note on Digital Signage**: While technically an "add-on" structurally, it's FULLY STANDALONE (no dependencies). Can be sold independently.

### Category Reference Table (Quick Lookup)

Use this table to determine module properties:

| Module Code | Category | Standalone | Accounting Req | Bundling Hint |
|------------|----------|-----------|----------------|-|
| ACC | Foundation | ✅ | N/A | Core infrastructure |
| PMS | Domain | ❌ | ✅ REQUIRED | Must + Accounting |
| POS | Domain | ✅ | ✅ REQUIRED | Should + Accounting |
| INV | Domain | ✅ | ❌ | Optional, pair with PROC |
| PROC | Domain | ✅ | ❌ | Prefer + INV |
| HRM | Domain | ✅ | ✅ REQUIRED | For payroll processing |
| SPA/GYM/LDR | Domain | ✅ | ✅ REQUIRED | Service + Accounting |
| CRS | Domain | ✅ | ✅ | Multi-property + Accounting |
| S&C | Domain | ✅ | ✅ | Events + Accounting |
| NOTIF | Engine | ❌ | N/A | Supporting service |
| WF | Engine | ❌ | N/A | Internal support |
| AUTH | Engine | ❌ | N/A | Internal support |
| ICH | Add-On | ❌ | N/A | Requires domain module |
| FDA | Add-On | ❌ | N/A | Financial add-on for Accounting |
| ADNOTIF | Add-On | ❌ | N/A | Notification enhancement |
| REPORT | Add-On | ❌ | N/A | Analytics for any domain |
| SIGNAGE | Add-On | ✅ | N/A | Fully independent |

---

## Subscription Bundling Rules

### Rule A: Core Business Modules (With Financial Transactions)

These modules generate revenue and must include Accounting.

| Module | Standalone Product | Bundling | Dependencies | Notes |
|--------|-------------------|----------|--------------|-------|
| **ACC** (Accounting App) | ✅ Yes | Not required | Accounting Core | Can be sold alone |
| **PMS** | ❌ No | **✅ Must bundle with Accounting** | Accounting Core | Hotels need accounting |
| **POS** | ✅ Yes (Optional bundling) | **✅ Should bundle with Accounting** | Accounting Core | Retail/F&B can be standalone |
| **INV** (Inventory) | ✅ Yes | Optional | None | Can operate alone |
| **PROC** (Procurement) | ✅ Yes | **✅ Usually bundle with INV** | INV (preferred) | Better with inventory |
| **HRM** (HR & Payroll) | ✅ Yes | **✅ Should bundle with Accounting** | Accounting Core | Payroll needs ledger |

---

### Rule B: Service Business Modules (Can be Standalone or Hotel-Integrated)

These can operate as independent businesses OR integrate with hotel.

| Module | Standalone Business | Hotel Integration | Bundling Required |
|--------|-------------------|-------------------|-------------------|
| **SPA** | ✅ Yes (own tenant) | ✅ Yes (with PMS) | **Accounting** (always) |
| **GYM** | ✅ Yes (own tenant) | ✅ Yes (with PMS) | **Accounting** (always) |
| **LDR** (Laundry) | ✅ Yes (own tenant) | ✅ Yes (with PMS) | **Accounting** (always) |

**Key**: Can exist as separate tenant or integrated into hotel. Either way, requires Accounting.

---

### Rule C: Distribution & Sales Modules

| Module | Standalone Product | Depends On | Notes |
|--------|-------------------|-----------|-------|
| **CRS** (Central Reservation System) | ✅ Yes | PMS (if managing reservations) | Multi-property bookings |
| **S&C** (Sales & Content) | ✅ Yes | PMS (if managing events/banquets) | Event and banquet management |

---

### Rule D: Cross-Module Add-Ons (Cannot be Sold Alone)

| Module | Standalone | Minimum Active | Notes |
|--------|-----------|-----------------|-------|
| **ICH** (Internal Collab Hub) | ❌ No | ≥1 domain module | Requires PMS/POS/etc. |
| **FDA** (Fraud & Audit Intelligence) | ❌ No | Accounting | Financial module add-on |
| **Advanced Notification** | ❌ No | Any module | Enhancement to Notification Engine |
| **Reporting & Analytics** | ❌ No | Any module | BI add-on for any domain |

---

### Rule E: Digital Signage Domain (Fully Standalone)

| Module | Standalone | Depends On |
|--------|-----------|-----------|
| **Device Management** | ✅ Yes | None |
| **Content Management** | ✅ Yes | None |
| **Playlist & Schedule** | ✅ Yes | None |
| **Realtime Player** | ✅ Yes | None |
| **Device Monitoring** | ✅ Yes | None |

Can be sold as complete signage solution without any operational modules.

---

## Valid Subscription Combinations

### ✅ Valid: Accounting Only
```
Modules: Accounting (ACC)
Use Case: Tax accountant, external bookkeeper
Features: Manual invoice entry, period close, reporting
Restrictions: No operational data (no PMS/POS/etc.)
```

### ✅ Valid: Hotel Basic
```
Modules: PMS + Accounting
Use Case: Standard hotel operation
Features: Reservations, check-in/out, auto-accounting
```

### ✅ Valid: Hotel Premium
```
Modules: PMS + Accounting + Inventory + CRS
Use Case: Hotel with inventory and multi-property
Features: Operations + Financial + Distribution
```

### ✅ Valid: Restaurant Standalone
```
Modules: POS + Accounting (+ optional Inventory)
Use Case: Standalone restaurant or F&B
Features: Sales, payments, accounting
No PMS required
```

### ✅ Valid: Laundry Standalone (Own Tenant)
```
Tenant: "ABC Laundry"
Modules: Laundry + Accounting
Use Case: Independent laundry service
Features: Service tracking, billing, accounting
Completely separate from hotel
```

### ✅ Valid: Laundry + Hotel Integration (Two Tenants)
```
Tenant 1 (Hotel): PMS + Accounting
Tenant 2 (Laundry): Laundry + Accounting
Integration: Inter-tenant invoice (Laundry issues invoice to Hotel)
```

### ✅ Valid: Enterprise Full Suite
```
Modules: PMS + POS + Accounting + Inventory + PROC + HRM + Reporting
Use Case: Large hotel/resort with multiple operations
Features: Full hospitality management
```

### ✅ Valid: Signage Only
```
Modules: Device Management + Content Management + Playlist + Player + Monitoring
Use Case: Digital signage provider (no operational modules)
Features: Signage management and playback
```

---

## ❌ Invalid Subscription Combinations

### ❌ Invalid: PMS Without Accounting
```
Requested: PMS only
Problem: No ledger, no period close, no financial statements
Error: "PMS requires Accounting. Please add to subscription."
Resolution: Add Accounting module
```

### ❌ Invalid: POS Without Accounting
```
Requested: POS only (standalone restaurant)
Problem: No way to track financial records, tax liability
Error: "POS requires Accounting. Please add to subscription."
Resolution: Add Accounting module
```

### ❌ Invalid: SPA/GYM/Laundry Without Accounting
```
Requested: SPA service only
Problem: No revenue tracking, no tax reporting
Error: "SPA requires Accounting. Please add to subscription."
Resolution: Add Accounting module (can be standalone tenant)
```

### ❌ Invalid: Procurement Without Inventory
```
Requested: PROC module only
Problem: No stock tracking, no goods receipt
Warning: "PROC works best with Inventory. Recommend adding."
Workaround: Can technically work, but user must manually track stock
```

### ❌ Invalid: Cross-Module Add-on Without Base Module
```
Requested: Reporting & Analytics only (no PMS/POS/Accounting)
Problem: No data to report on
Error: "Reporting requires at least one operational module."
Resolution: Add PMS, POS, or Accounting
```

### ❌ Invalid: ICH (Chat) Without Any Domain
```
Requested: Internal Collab Hub only
Problem: Nothing to collaborate about
Error: "ICH requires at least one operational module (PMS, POS, etc.)."
Resolution: Add PMS or other operational module
```

---

## Dependency Validation Logic

### Validation Rules (Automated Checks)

```typescript
// When user tries to enable module
function validateSubscription(tenantId: string, moduleToEnable: string): ValidationResult {

  const subscription = getTenantSubscription(tenantId);
  const requirements = MODULE_REQUIREMENTS[moduleToEnable];

  // Check mandatory dependencies
  if (requirements.requiresAtLeastOne) {
    // At least ONE module from mandatory array must be subscribed
    const hasAtLeastOne = requirements.mandatory.some(m => subscription.hasModule(m));
    if (!hasAtLeastOne) {
      const modules = requirements.mandatory.join(' OR ');
      return INVALID(`${moduleToEnable} requires at least one of: ${modules}`);
    }
  } else if (requirements.requiresAll !== false) {
    // Default: ALL modules in mandatory array required
    for (const required of requirements.mandatory) {
      if (!subscription.hasModule(required)) {
        return INVALID(`${moduleToEnable} requires ${required}`);
      }
    }
  }

  // Check recommended dependencies
  for (const recommended of requirements.recommended) {
    if (!subscription.hasModule(recommended)) {
      return WARNING(`${moduleToEnable} recommends ${recommended}`);
    }
  }

  return VALID();
}
```

### Module Requirements Matrix

```typescript
const MODULE_REQUIREMENTS = {
  PMS: {
    mandatory: ['Accounting'],
    requiresAll: true,  // ALL modules in mandatory array required
    recommended: ['Reporting']
  },
  POS: {
    mandatory: ['Accounting'],
    requiresAll: true,
    recommended: ['Inventory', 'Reporting']
  },
  PROC: {
    mandatory: [],
    requiresAll: true,
    recommended: ['Inventory']
  },
  ICH: {
    mandatory: ['PMS', 'POS', 'Accounting', 'HRM', 'Inventory'],
    requiresAtLeastOne: true,  // AT LEAST ONE module required
    recommended: []
  },
  FDA: {
    mandatory: ['Accounting'],
    requiresAll: true,
    recommended: []
  },
  Reporting: {
    mandatory: ['PMS', 'POS', 'Accounting', 'Inventory'],
    requiresAtLeastOne: true,  // AT LEAST ONE module required
    recommended: []
  },
  // ...
};
```

**Key Difference**:
- `requiresAll: true` — ALL modules in `mandatory` array must be subscribed
- `requiresAtLeastOne: true` — AT LEAST ONE module from `mandatory` array must be subscribed
- If neither specified, default is `requiresAll: true`

---

## Real-World Scenarios

### Scenario 1: Accountant Office (Accounting Only)

**Tenant**: "ABC Tax Consultants"

**Subscription**:
```
✅ Accounting (ACC)
```

**What they can do**:
- ✅ Create invoices manually
- ✅ Record payments
- ✅ Post journal entries
- ✅ Close periods and generate financial statements
- ✅ Run tax reports

**What they cannot do**:
- ❌ No PMS (can't track hotel operations)
- ❌ No POS (can't process sales)
- ❌ All data manual entry or import

**Business Model**: Service provider, not operational business

---

### Scenario 2: Hotel with Basic Operations

**Tenant**: "Hotel Bali"

**Subscription**:
```
✅ PMS
✅ Accounting
```

**Data Flow**:
```
1. Guest makes reservation → PMS records
2. Guest checks in → PMS opens folio
3. Guest stays, charges posted → PMS records charges
4. Guest checks out → PMS event triggers
5. Event published → Accounting adapter converts
6. Invoice created → Accounting posts journal entries
7. Period close → Accounting locks transactions
8. Financial statements generated
```

**What they can do**:
- ✅ Full hotel operations (reservations, check-in, billing)
- ✅ Automatic accounting (PMS events → GL entries)
- ✅ Financial statements and tax reporting
- ✅ Period closing

**Optional add-ons**:
- Reporting & Analytics (see operational dashboards)
- CRS (distribute to OTAs)

---

### Scenario 3: Restaurant (POS Standalone)

**Tenant**: "Restaurant XYZ"

**Subscription**:
```
✅ POS
✅ Accounting (required)
✅ Inventory (optional)
```

**Data Flow**:
```
1. Customer orders → POS records sale
2. Customer pays → Payment Service processes
3. Sale event published → Accounting adapter converts
4. Invoice created → Revenue posted to GL
5. Daily close → Revenue summarized
6. Monthly close → Tax liability calculated
```

**What they can do**:
- ✅ Sales transactions
- ✅ Payment processing
- ✅ Inventory tracking (optional)
- ✅ Financial reporting and tax filing

**What they cannot do**:
- ❌ Hotel operations (no PMS)

---

### Scenario 4: Laundry as Standalone Business (Separate Tenant)

**Tenant 1**: "Hotel Bali" (PMS + Accounting)

**Tenant 2**: "ABC Laundry" (Laundry + Accounting)

**Integration**: Inter-tenant invoicing

**How it works**:
```
Hotel Guest dirty laundry
  ↓
Hotel staff orders from Laundry service
  ↓
Laundry processes and invoices Hotel
  ↓
Laundry Accounting issues invoice
  ↓
Hotel Accounting receives and records expense
  ↓
Both settle payment
```

**Key**: Completely separate tenants, separate accounting records, integration only at invoice level

---

### Scenario 5: Hotel with All Add-Ons

**Tenant**: "Luxury Resort"

**Subscription**:
```
✅ PMS (core)
✅ Accounting (required)
✅ Inventory (operational)
✅ PROC (procurement)
✅ HRM (payroll)
✅ SPA (service)
✅ GYM (service)
✅ Laundry (service)
✅ CRS (distribution)
✅ S&C (events/banquets)
✅ Reporting & Analytics (add-on)
✅ ICH (add-on)
✅ FDA (add-on)
```

**Result**: Complete hospitality management platform

---

### Scenario 6: Multi-Tenant Hotel Group (Franchise)

**Tenant 1**: "Hotel Jakarta"
```
PMS + Accounting + Reporting
```

**Tenant 2**: "Hotel Surabaya"
```
PMS + Accounting + Reporting
```

**Tenant 3**: "Corporate Finance" (shared)
```
Accounting (consolidation ledger)
```

**Integration**: Each hotel sends PMS events to own Accounting. Corporate Finance imports consolidated data.

---

## Feature Gating Implementation

### Level 1: Module Enable/Disable

```typescript
// Is module enabled for tenant?
if (!isTenantSubscribedTo(tenantId, 'PMS')) {
  hideNavigationMenu('PMS');
  return 403 Forbidden if user tries /pms/* routes;
}
```

### Level 2: Feature Gating Based on Add-ons

```typescript
// Advanced reporting only if subscribed to Reporting add-on
if (isTenantSubscribedTo(tenantId, 'Reporting')) {
  showReportingDashboard();
} else {
  showBasicReporting();
}
```

### Level 3: Inter-Module Dependencies

```typescript
// Check if Accounting required for PMS
if (moduleToEnable === 'PMS' && !isTenantSubscribedTo(tenantId, 'Accounting')) {
  throw Error('PMS requires Accounting');
}
```

### Level 4: API Endpoint Gating

```typescript
// Route guard: check subscription before allowing access
app.get('/api/pms/reservations', (req, res) => {
  const tenantId = req.user.tenant_id;

  if (!isTenantSubscribedTo(tenantId, 'PMS')) {
    return res.status(403).json({ error: 'PMS module not subscribed' });
  }

  // Proceed with request
});
```

---

## Billing & Packaging

### Package: Solo Accountant
```
Modules: ACC (Accounting)
Base Price: $50/month
Features: Manual invoicing, ledger, reporting
```

### Package: Hotel Starter
```
Modules: PMS + Accounting
Base Price: $200/month
Features: Reservations, billing, accounting
```

### Package: Hotel Professional
```
Modules: PMS + Accounting + Reporting + CRS
Base Price: $400/month
Features: Hotel ops + financial + distribution
```

### Package: Restaurant
```
Modules: POS + Accounting + Inventory (optional)
Base Price: $150/month (POS + ACC)
Add-ons: Inventory $50/month, Reporting $50/month
```

### Package: Signage Provider
```
Modules: Device Management + Content Management + Playlist + Player + Monitoring
Base Price: $300/month
Features: Complete digital signage solution
```

---

## Migration Scenarios

### Upgrade: Restaurant adds Accounting

**Before**:
```
POS only (INVALID - error shown)
```

**Action**: User clicks "Add Accounting"

**After**:
```
POS + Accounting (VALID)
Billing: Additional $50/month for Accounting
```

### Upgrade: Hotel adds Reporting

**Before**:
```
PMS + Accounting (valid, basic reporting)
```

**Action**: User subscribes to Reporting add-on

**After**:
```
PMS + Accounting + Reporting (advanced dashboards now visible)
Billing: Additional $50/month for Reporting
```

### Downgrade: Restaurant removes Inventory

**Before**:
```
POS + Accounting + Inventory
```

**Action**: User removes Inventory

**After**:
```
POS + Accounting (still valid)
Billing: Reduced by $50/month
Inventory data: Archived (can be re-enabled)
```

---

## Compliance Checklist

When adding new module:

- [ ] Module categorized (Core/Engine/Domain/Add-on)
- [ ] Standalone technical vs. product determined
- [ ] Dependencies listed (mandatory and recommended)
- [ ] Bundling rules documented
- [ ] Accounting requirement specified (if financial)
- [ ] Validation logic implemented
- [ ] Feature gating coded
- [ ] Error messages for invalid combos defined
- [ ] Billing implications documented
- [ ] Documentation examples created
- [ ] Product team trained on rules

---

## References

- **REF-03**: Module Catalog — What each module does
- **ARCH-09**: Modularization Principles — Why these rules exist
- **SPEC-08**: Tenant & Subscription Lifecycle — Subscription management
- **STD-19**: Event Model — How modules integrate
