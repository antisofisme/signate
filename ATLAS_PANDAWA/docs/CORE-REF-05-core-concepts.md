# REF-05: Core Concepts - User, Tenant, App, & Membership

This document defines the **conceptual model** for ATLAS_PANDAWA with practical examples. It explains the core relationships between Users, Tenants, Applications, Roles, and Memberships.

**Prerequisite**: Read **REF-01 (Identity-Membership Model Foundation)** first for locked, non-negotiable principles.

**Purpose of REF-05**: Extend REF-01 with practical scenarios, derived concepts, and worked examples. REF-01 is the "constitution" (locked), REF-05 applies those principles to real situations.

---

## Core Relationship Model

The fundamental relationship can be expressed as:

```
User ←→ Membership ←→ Tenant ←→ Subscription ←→ App
```

**What this means**:
- User does NOT directly use App
- User accesses App **through** Tenant
- Tenant accesses App **through** Subscription
- No direct User-App relationship

---

## Five Core Principles (Locked)

### Principle 1: User is Global Identity
- One User = one global identity across platform
- Single authentication, single email, single password
- User exists independently of Tenants
- User can be deleted only after all Tenant associations removed

### Principle 2: Tenant is Isolated Business Entity
- One Tenant = one business/organization/entity
- Tenant data never mixes with other Tenants (hard isolation)
- Tenant has own ledger, own audit trail, own settings
- Tenant can operate independently from other Tenants

### Principle 3: App is Modular Functionality
- One App = one business capability (PMS, Accounting, Inventory, etc.)
- App is unaware of specific Users or other Tenants
- App only knows which Tenant it's currently operating in
- App is subscribed/enabled at Tenant level, not User level

### Principle 4: Role is Tenant-Contextual
- Role is **always** scoped to a Tenant
- No global roles (no "platform admin" as a role)
- Same User can have different roles in different Tenants
- Role determines what User can do **within that Tenant**

### Principle 5: No Global Roles
- There are NO platform-level roles
- All roles are Tenant-specific
- Exception: Internal system accounts (system, billing engine, etc.) - these are service accounts, not user roles
- Example: User A is "Owner" in Tenant 1, but "Staff" in Tenant 2 (different roles)

---

## Entity Definitions

### User

**Definition**: A global identity representing a person or service account.

**Characteristics**:
- Globally unique (by email)
- Singular authentication identity
- May belong to zero or more Tenants
- Persists even if all Tenant associations removed
- Has personal preferences (language, timezone, notification settings)

**Lifecycle**:
```
User Created
  ↓
User Verified (email)
  ↓
User Joins Tenant (via Membership)
  ↓
User Role Changes (via Membership update)
  ↓
User Leaves Tenant (Membership deleted)
  ↓
User Deactivated (or deleted after grace period)
```

**Example Users**:
- john@hotel.com (person at hotel)
- system-scheduler@platform.com (service account)
- api-integration@supplier.com (external integration account)

---

### Tenant

**Definition**: A complete, isolated business entity operating within ATLAS_PANDAWA.

**Characteristics**:
- Represents one business (e.g., "Hotel Jakarta", "ABC Laundry", "XYZ Supplier")
- Completely isolated data (no sharing with other Tenants)
- Own ledger, own audit trail, own settings
- Own subscription (which Apps are enabled)
- Can operate independently

**Data Owned by Tenant**:
- Guests/Customers
- Reservations/Orders
- Financial records (invoices, payments, ledger)
- Inventory
- Employees
- Settings and configurations

**Multi-Tenant Example**:
```
Tenant A: "Hotel Jakarta"
  ├─ Guests: 1000 unique guests
  ├─ Reservations: 500 active
  ├─ Ledger: $100,000 revenue YTD
  └─ Settings: Check-in time 3 PM, Check-out 11 AM

Tenant B: "Hotel Surabaya"
  ├─ Guests: 800 unique guests (completely different from Tenant A)
  ├─ Reservations: 300 active
  ├─ Ledger: $80,000 revenue YTD (separate from Tenant A)
  └─ Settings: Check-in time 2 PM, Check-out 10 AM
```

**No sharing**: Guest in Tenant A cannot appear in Tenant B. Ledger in Tenant A is completely separate from Tenant B.

---

### App (Module)

**Definition**: A business capability or module that provides functionality.

**Characteristics**:
- Represents one functional domain (PMS, Accounting, Inventory, etc.)
- Unaware of specific Users (only knows current user context)
- Unaware of other Tenants
- Only knows the Tenant it's operating within
- Subscribed at Tenant level (not per User)
- Can be enabled/disabled per Tenant

**Examples**:
- PMS (Property Management System) - reservations, check-in
- Accounting - invoices, ledger, reporting
- Inventory - stock tracking
- HR - employee management, payroll
- CRM - guest/customer relationships

**Key Rule**: App is never directly assigned to User. App is assigned to Tenant via Subscription.

---

### Role

**Definition**: A set of permissions within a specific Tenant.

**Characteristics**:
- Always scoped to a Tenant (role-in-tenant, not global role)
- Determines what User can do within that Tenant
- Example roles: Owner, Admin, Staff, Guest
- Same User can have different roles in different Tenants

**Example**:
```
User: alice@example.com

In Tenant A (Hotel):
  Role: Owner
  Permissions: Create/delete users, modify settings, approve refunds

In Tenant B (Laundry):
  Role: Staff
  Permissions: Process orders, track inventory, cannot modify settings

Same user, different roles, different permissions in each Tenant
```

---

### Membership

**Definition**: The join table that binds User + Tenant + Role.

**Characteristics**:
- Represents: User has Role in Tenant
- One User can have many Memberships (one per Tenant they're in)
- One Membership = User + Tenant + Role combination
- Determines User's access to Tenant and its data

**Example Membership Records**:
```
Membership 1:
  user_id: alice-123
  tenant_id: hotel-jakarta
  role: owner
  created_at: 2025-01-01
  status: active

Membership 2:
  user_id: alice-123
  tenant_id: laundry-abc
  role: staff
  created_at: 2025-02-15
  status: active

Result: alice@example.com is owner of hotel-jakarta AND staff of laundry-abc
```

---

### Subscription

**Definition**: Tenant's subscription to one or more Apps.

**Characteristics**:
- Tenant subscribes to Apps, not Users
- Controls which Apps are enabled for Tenant
- Example: Hotel subscribes to PMS + Accounting + Inventory
- Affects what features Users can access (feature gating)
- Tied to billing

**Example**:
```
Tenant: Hotel Bali

Subscription:
  App: PMS → Status: ACTIVE
  App: Accounting → Status: ACTIVE
  App: Inventory → Status: ACTIVE
  App: HR → Status: INACTIVE

Result:
  - All staff can access PMS (if they have membership)
  - All staff can access Accounting (if they have membership)
  - No staff can access HR (module not subscribed)
```

---

## Access Control Formula

User's access to functionality is determined by:

```
User Access = Authentication × Membership × App Subscription
```

**Breaking it down**:

### Factor 1: Authentication
- User must be logged in
- Valid session/token required
- Example: Unauthenticated user = NO access

### Factor 2: Membership
- User must have Membership in the Tenant
- User must have appropriate Role
- Example: User not in Tenant A = NO access to Tenant A

### Factor 3: App Subscription
- Tenant must have subscribed to the App
- Enabled subscription required
- Example: PMS not subscribed = NO access to PMS features

**Combination**:
```
IF (user authenticated) AND (user has membership in tenant) AND (app is subscribed) THEN
  user can access features based on role permissions
ELSE
  deny access
```

**Example Scenarios**:

**Scenario 1: Can Access**
```
User: alice
Tenant: Hotel Jakarta
Role: Admin (via Membership)
App: PMS
Subscription: PMS is ACTIVE for Hotel Jakarta

Result: ✅ alice can access PMS
```

**Scenario 2: Cannot Access (No Membership)**
```
User: bob
Tenant: Hotel Jakarta
Status: bob is NOT a member of Hotel Jakarta

Result: ❌ bob cannot access Hotel Jakarta's data
```

**Scenario 3: Cannot Access (App Not Subscribed)**
```
User: charlie
Tenant: Hotel Surabaya
Role: Admin (via Membership)
App: HR
Subscription: HR is INACTIVE for Hotel Surabaya

Result: ❌ charlie cannot access HR (module not subscribed)
```

---

## Multi-Tenant Scenarios

### Scenario 1: User is Owner of Multiple Tenants

**User**: john@example.com

**Memberships**:
```
Membership 1: Hotel A (Owner)
Membership 2: Hotel B (Owner)
Membership 3: Laundry C (Owner)
```

**Access**:
- john can manage Hotel A (as owner)
- john can manage Hotel B (as owner)
- john can manage Laundry C (as owner)
- john's data is completely separate in each Tenant

**Data Isolation**:
- Hotel A guests ≠ Hotel B guests (different Tenants, different data)
- Hotel A ledger ≠ Hotel B ledger (separate financial records)

---

### Scenario 2: User has Multiple Roles (Different Tenant per Role)

**User**: alice@example.com

**Memberships**:
```
Membership 1: Hotel A (Owner)
Membership 2: Laundry B (Staff)
Membership 3: Supplier C (Admin)
```

**Access & Permissions**:
- Hotel A: Full control (Owner) - can create users, modify settings, approve transactions
- Laundry B: Limited access (Staff) - can only process orders
- Supplier C: Moderate access (Admin) - can manage staff but not approve payments

**Data Isolation**:
- Hotel A guests cannot be seen in Laundry B (different Tenants)
- Supplier C inventory cannot be seen in Hotel A (different Tenants)

---

### Scenario 3: Team Member Across Tenants

**User**: bob@example.com

**Memberships**:
```
Membership 1: Hotel A (Staff)
Membership 2: Hotel A (Upgraded to Admin)  [OVERWRITE: only one role per tenant]
```

Actually, correction:
```
Membership 1: Hotel A (Admin)
```

Can only have ONE role per Tenant. If bob is promoted from Staff to Admin, the Membership is updated (not duplicated).

---

### Scenario 4: Tenant Multi-App

**Tenant**: Hotel Bangkok

**Subscriptions**:
```
App: PMS → ACTIVE
App: Accounting → ACTIVE
App: Inventory → ACTIVE
App: HR → INACTIVE
App: Loyalty → INACTIVE
```

**User Access** (alice is Staff at Hotel Bangkok):
```
PMS: ✅ Accessible (alice has staff role, app is subscribed)
Accounting: ❌ Not accessible (alice is staff, lacks permissions for accounting)
Inventory: ✅ Accessible (alice has staff role for inventory operations)
HR: ❌ Not accessible (app is not subscribed for this tenant)
Loyalty: ❌ Not accessible (app is not subscribed for this tenant)
```

---

## Inter-Tenant Integration

### Principle: Tenants Never Share Database

Tenants are completely isolated. Integration happens through:

1. **Events** (asynchronous)
2. **API Calls** (synchronous, with explicit permission)
3. **Business Contracts** (formal agreements)

### Example 1: Hotel + Laundry Integration

**Tenant A**: Hotel Bangkok
**Tenant B**: ABC Laundry

**Integration Flow**:
```
1. Hotel guest requests laundry service
2. Hotel (Tenant A) creates event: "laundry.service_requested"
3. Laundry (Tenant B) receives event
4. Laundry processes request in their own Tenant
5. Laundry creates invoice to Hotel (inter-tenant invoice, not shared DB)
6. Hotel receives invoice via event
7. Hotel records as expense in their Accounting
```

**No shared database**, everything through events and APIs.

---

### Example 2: Multi-Property Owner (Same Person, Different Tenants)

**User**: john@hotelgroup.com

**Tenants**:
- Hotel A (john is Owner)
- Hotel B (john is Owner)

**Consolidated Reporting**:
- john logs into Hotel A → sees Hotel A data only
- john logs into Hotel B → sees Hotel B data only
- If john needs consolidated report, must aggregate manually or through separate reporting tenant

**No automatic cross-tenant visibility**. Data strictly isolated.

---

## Anti-Patterns (Forbidden)

### ❌ Anti-Pattern 1: Direct User-App Assignment
```
WRONG: User → App
User john directly gets access to PMS app

CORRECT: User → Tenant → App (via Subscription)
User john has membership in Hotel A
Hotel A subscribes to PMS
Therefore john can access PMS (if role permits)
```

### ❌ Anti-Pattern 2: Global Roles
```
WRONG: User assigned "Admin" role globally
john is Admin → can manage all Tenants

CORRECT: User assigned role within Tenant
john is Admin in Hotel A (can manage Hotel A only)
john is Staff in Hotel B (limited access to Hotel B)
```

### ❌ Anti-Pattern 3: Cross-Tenant Data Sharing
```
WRONG: Hotel A guests table shared with Hotel B
SELECT * FROM guests (no tenant filter)

CORRECT: Tenant context enforced
SELECT * FROM guests WHERE tenant_id = 'hotel-a'
```

### ❌ Anti-Pattern 4: App Bypassing Membership
```
WRONG: App checks only app subscription
IF PMS.is_subscribed THEN show_pms_features()

CORRECT: App checks both membership and subscription
IF user.has_membership(tenant) AND app.is_subscribed(tenant) THEN
  show_pms_features()
```

---

## Data Access Rules

### Rule 1: Tenant Always Filters Data
Every query must be filtered by tenant_id:
```sql
SELECT * FROM reservations
WHERE tenant_id = :tenant_id  -- MANDATORY
AND user_id = :user_id        -- If user-specific data
```

### Rule 2: No Cross-Tenant Joins
```sql
-- WRONG: Could expose data from both tenants
SELECT r.*, g.* FROM reservations r
JOIN guests g ON r.guest_id = g.id

-- CORRECT: Explicit tenant context
SELECT r.*, g.* FROM reservations r
JOIN guests g ON r.guest_id = g.id
WHERE r.tenant_id = :tenant_id AND g.tenant_id = :tenant_id
```

### Rule 3: User Cannot Specify Tenant
```typescript
// WRONG: User specifies tenant
const data = await db.getReservations(
  tenant_id: req.query.tenant_id  // User could request any tenant!
);

// CORRECT: Tenant from authenticated session
const tenantId = req.user.tenant_id;  // From JWT
const data = await db.getReservations(tenantId);
```

---

## Implementation Checklist

When implementing these concepts:

- [ ] User entity created (global identity)
- [ ] Tenant entity created (isolated business entity)
- [ ] Membership join table created (User + Tenant + Role)
- [ ] TenantApp subscription table created (Tenant + App + Status)
- [ ] Authentication validates User
- [ ] Tenant context injected from auth token
- [ ] All data queries filtered by tenant_id
- [ ] No cross-tenant queries without explicit permission
- [ ] Role permissions defined per Role
- [ ] Feature gating checks: Membership × App Subscription
- [ ] Tests verify tenant isolation
- [ ] Audit logs show User + Tenant context

---

## Related Documents

- **REF-03**: Module Catalog — What each App does
- **REF-04**: Subscription Matrix — Which Apps bundle together
- **ARCH-09**: Modularization Principles — How Apps are designed
- **SPEC-07**: Use Cases — What Roles can do (per Tenant)
- **SPEC-08**: Tenant & Subscription Lifecycle — How Tenants are created
- **SEC-02**: Data Protection — How Tenant data is isolated and encrypted
- **ARCH-06**: Repository Governance — How code repos align with Tenants/Apps
