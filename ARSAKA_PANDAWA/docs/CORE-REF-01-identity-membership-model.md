# REF-01: Identity-Membership Model (Foundation)

This document defines the **foundational identity and access control model** for ARSAKA_PANDAWA. It is the authoritative source for how users, tenants, roles, and permissions relate.

**CRITICAL**: This is the "constitution" of the system. All use cases, ERD, events, and implementations MUST conform to this model. Changes require architectural review.

---

## Foundational Principles (Locked - Non-Negotiable)

### Principle 1: Identity is Global
```
One user = one identity across entire platform.
Single email, single password, single authentication.
User exists independently of tenants.
```

### Principle 2: Role is NEVER Global
```
There are NO platform-level roles like "Super Admin".
Every role is scoped to a specific Tenant.
Same user can have different roles in different tenants.
```

### Principle 3: Membership is the Access Contract
```
Membership = User + Tenant + Role
Membership determines what User can access in that Tenant.
All access rights flow from Membership.
```

### Principle 4: Tenant is the Isolation Boundary
```
One Tenant = one isolated business entity.
No data sharing between tenants without explicit contract.
Tenant is the pagar (fence) that protects data.
```

### Principle 5: Subscription Enables Features
```
Tenant subscribes to Apps (modules).
Subscription controls feature visibility and access.
No app = no features for that tenant (feature gate).
```

### Principle 6: One User, Many Tenants
```
User can be member of multiple tenants.
Each membership can have different role.
Example: Alice is Owner of Hotel A, Staff of Laundry B.
```

### Principle 7: Guest is Optional
```
Guest may not have user account.
Can still check in, stay, make charges.
If signup: User account created, Membership(role=guest) added.
```

---

## Soft Delete & Data Retention Policy

All entities with customer-created data follow soft delete pattern:

```
Soft Delete Pattern:
  ✅ deleted_at IS NULL → Record is active
  ✅ deleted_at IS NOT NULL → Record is soft-deleted (hidden from queries)
  ❌ No physical deletion (preserve audit trail)

Applies To:
  - User (user soft-deleted when account deactivated)
  - Tenant (tenant soft-deleted when business closes)
  - Membership (membership soft-deleted when user removed from tenant)
  - All operational data (reservations, invoices, etc.)

Query Pattern:
  SELECT * FROM users WHERE deleted_at IS NULL
  (all queries exclude soft-deleted records by default)

Retention:
  - Soft-deleted records kept indefinitely (regulatory compliance)
  - Permanent deletion only after retention period (default 90 days)
  - Configurable per tenant (for compliance)
```

---

## Core Entities

### User (Global Identity)

**What it is**: A person or system account with a global identity.

**Attributes**:
```
id (UUID, globally unique)
email (globally unique, case-insensitive)
password_hash (bcrypt or similar)
auth_provider (local, google, microsoft, etc.)
first_name
last_name
status (active, inactive, suspended, deleted)
profile (language, timezone, preferences)
created_at
deleted_at (soft delete)
```

**Lifecycle**:
```
1. User Created (registration or admin create)
2. User Verified (email confirmed, if required)
3. User Joins Tenant (via Membership)
4. User Role Changes (via Membership update)
5. User Leaves Tenant (Membership deleted, User remains)
6. User Deactivated (status change or delete)
```

**Key Rules**:
- ✅ User can exist without any Tenant
- ✅ User can belong to multiple Tenants
- ✅ User cannot be deleted if active Memberships exist
- ❌ User does NOT have an inherent role (role only via Membership)
- ❌ User does NOT have a "tenant_id" field (users are global)

**Examples**:
```
alice@hotel.com          → Person working at hotel
john@supplier.com        → Person at laundry supplier
system-scheduler@platform.com  → Service account
api-integration@partner.io     → External integration
```

---

### Tenant (Isolated Business Entity)

**What it is**: A complete, isolated business operating within ARSAKA_PANDAWA.

**Attributes**:
```
id (UUID, tenant-specific)
name (display name: "Hotel Jakarta", "ABC Laundry")
type (hotel, supplier, laundry, gym, spa, service, etc.)
status (draft, trial, active, suspended, deleted)
timezone
currency (default currency: IDR, USD, etc.)
settings (checkin time, checkout time, etc.)
created_at
activated_at
suspended_at (if suspended)
deleted_at (soft delete)
```

**Principles**:
- ✅ One Tenant = one complete business entity
- ✅ Tenant can operate independently
- ✅ Tenant has its own ledger, audit trail, settings
- ✅ Tenant can subscribe to apps
- ❌ Data NEVER shared with other tenants (except via contract)
- ❌ Cannot query another tenant's data without contract

**Data Owned by Tenant**:
- Guests/Customers
- Reservations/Orders
- Financial records (invoices, payments, ledger)
- Inventory
- Employees
- Settings and configurations
- All operational data

**Example**:
```
Tenant A: Hotel Jakarta
  - Guests: 1000 unique
  - Reservations: 500 active
  - Revenue YTD: $100,000
  - Check-in: 3 PM, Check-out: 11 AM

Tenant B: Hotel Surabaya (completely different data)
  - Guests: 800 unique (different from A)
  - Reservations: 300 active (different from A)
  - Revenue YTD: $80,000 (separate from A)
  - Check-in: 2 PM, Check-out: 10 AM
```

---

### Membership (User ↔ Tenant ↔ Role)

**What it is**: The binding that grants User access to Tenant with a specific Role.

**Attributes**:
```
id (UUID)
user_id (FK → User)
tenant_id (FK → Tenant)
role (owner, admin, staff, guest)
status (invited, active, left, suspended)
invited_at
joined_at (when user accepted invite)
left_at (when user left)
created_at
```

**Unique Constraint**:
```
(user_id, tenant_id) must be unique.
ONE role per user per tenant.
If promoted: UPDATE existing membership (don't create new).
```

**Role Meanings**:

| Role | Who | Permissions | Examples |
|------|-----|-----------|----------|
| **Owner** | Business owner or founder | Full control (create users, modify settings, approve high transactions) | Hotel owner, laundry owner |
| **Admin** | Manager | Moderate control (manage staff, approve medium transactions, view reports) | Shift manager, front desk supervisor |
| **Staff** | Worker | Operational access (process orders, check in guests, post charges) | Receptionist, server, cashier |
| **Guest** | Customer | Self-service access (view own folio, request services) | Hotel guest, customer |

**Lifecycle**:
```
1. Owner invites User to Tenant
   → Membership created (status=invited)

2. User accepts invite
   → Membership.status = active
   → User can access Tenant

3. Owner promotes/demotes User
   → Membership.role updated
   → Permissions change immediately

4. User leaves Tenant
   → Membership.status = left
   → User can no longer access Tenant

5. Owner removes User
   → Membership deleted or status=suspended
   → User denied access
```

**Multi-Tenant Example**:
```
User: alice@example.com

Membership 1:
  tenant_id: hotel-jakarta
  role: owner
  status: active
  → Can: full control of Hotel Jakarta

Membership 2:
  tenant_id: laundry-abc
  role: staff
  status: active
  → Can: operational access to Laundry ABC only

Result: Alice is Owner of one business, Staff of another.
         Different permissions in each.
```

---

### App (Module/Capability)

**What it is**: A business capability or module (PMS, Accounting, Inventory, HR, etc.)

**Attributes**:
```
id (UUID)
code (PMS, ACC, INV, HR, POS, SPA, GYM, etc.)
name (Property Management System, Accounting, etc.)
category (foundation, engine, domain, addon)
standalone_technical (can code run without other modules?)
standalone_product (can sell alone as product?)
```

**Examples**:
- PMS: Property Management System (reservations, check-in)
- Accounting: Financial ledger and reporting
- Inventory: Stock tracking and valuation
- HR: Employee management and payroll
- CRS: Central Reservation System
- Digital Signage: Display management

**Key Rule**:
```
App is NEVER directly assigned to User.
App is assigned to Tenant via Subscription.
User accesses App only if:
  (1) User has Membership in Tenant
  (2) User has required role/permission
  (3) Tenant has subscribed to App
```

---

### Subscription (TenantApp)

**What it is**: Tenant's subscription to a specific App.

**Attributes**:
```
id (UUID)
tenant_id (FK → Tenant)
app_id (FK → App)
status (active, inactive, suspended, expired)
started_at
ended_at (if expired)
billing_cycle (monthly, annual, lifetime)
next_renewal
```

**Unique Constraint**:
```
(tenant_id, app_id) must be unique.
ONE subscription per tenant per app.
```

**Purpose**:
```
Controls which apps are visible/available to tenant.
Feature gating happens here.
Affects billing and licensing.
```

**Example**:
```
Tenant: Hotel Bali
Subscriptions:
  - PMS → ACTIVE
  - Accounting → ACTIVE
  - Inventory → ACTIVE
  - HR → INACTIVE
  - Loyalty → INACTIVE

Result:
  Staff can access: PMS, Accounting, Inventory
  Staff cannot access: HR, Loyalty (not subscribed)
```

---

### Guest (Tenant Customer)

**What it is**: A customer/guest of a Tenant business. Guest may or may not have a User account.

**Two Scenarios**:

#### Scenario A: Authenticated Guest (Has User Account)
1. Guest creates User account (registers email/password)
2. Guest checks into hotel/joins loyalty program
3. Membership created: Membership(user_id=alice, tenant_id=hotel-123, role=guest)
4. Guest can: View own folio, request services, manage profile

**Attributes** (Part of User entity):
```
id (UUID) - User ID
email
password_hash
first_name
last_name
```

#### Scenario B: Anonymous Guest (No User Account)
1. Guest checks into hotel via front desk
2. No User account created (staff handles manually)
3. Guest identified by: folio_id, room_number, phone number
4. Guest cannot: Self-service login, manage profile
5. Guest can: Use services, have charges posted to folio

**Attributes** (Part of Folio/Reservation entity):
```
id (UUID) - Folio ID (operational, not identity)
tenant_id (FK → Tenant)
guest_name
guest_email (optional, for notifications)
guest_phone (optional, for contact)
room_number
check_in_date
check_out_date
```

**Guest ≠ User (Important Distinction)**:
- Guest: A customer of the Tenant business (operational concept)
- User: A person with global identity and authentication (identity concept)
- Relationship: Guest MAY BECOME User if they register for account
- Example: Guest "John Smith" checks in at hotel (anonymous), later registers email (becomes User)

**Guest Lifecycle**:

```
SCENARIO A (With Account):
1. Person creates User account (registers)
   → User exists (globally)
   → No membership yet

2. Person checks in at Hotel
   → Membership created (role=guest)
   → User+Tenant binding established

3. Person checks out
   → Membership soft-deleted (status=left)
   → User remains (for future visits)

4. Person returns later
   → Membership activated again
   → User's folio history available

SCENARIO B (Without Account):
1. Guest checks in at Hotel (via front desk)
   → No User created
   → Folio/Reservation created (guest_name, guest_email)
   → Guest handled operationally only

2. Guest wants to use self-service (check folio, request service)
   → Hotel can send activation link
   → Guest registers User account
   → System links User to existing Folio
   → Membership(role=guest) created

3. Guest is now authenticated
   → Can use self-service features
   → But: Previous folio history may not sync
```

**Guest Permissions**:

| Action | Authenticated Guest | Anonymous Guest |
|--------|-------------------|-----------------|
| View own folio | ✅ Yes | ❌ No (need link sent by email) |
| Request services | ✅ Yes (via app) | ✅ Yes (via phone/in-person) |
| Modify profile | ✅ Yes | ❌ No |
| Check in | ✅ Yes (self-checkin, if enabled) | ✅ Yes (staff checks in) |
| View charges | ✅ Yes (personal folio) | ❌ No (staff verbally informs) |
| Make payment | ✅ Yes (via app/portal) | ✅ Yes (cash/card at desk) |

**Key Rules**:
- ✅ Guest can exist without User account (anonymous guest)
- ✅ Guest with account has Membership(role=guest)
- ✅ Anonymous guest can become authenticated by registering
- ❌ Guest cannot become Staff/Admin (different role with different permissions)
- ❌ Guest account cannot be transferred between tenants (single tenant guest)

---

## Access Control Formula

**User access to functionality**:

```
User Access = Authentication × Membership × App Subscription × Permissions
```

**Breaking it down**:

### Factor 1: Authentication
```
User must be logged in (valid session/token).
Examples of failure:
  ❌ Not logged in
  ❌ Token expired
  ❌ Invalid credentials
```

### Factor 2: Membership
```
User must have Membership in the Tenant.
User must have acceptable role for the action.

Examples of failure:
  ❌ User not member of Tenant A (cannot see Tenant A data)
  ❌ User is Guest (cannot create invoices)
```

### Factor 3: App Subscription
```
Tenant must have subscribed to the App.
Enabled subscription required (not inactive/expired).

Examples of failure:
  ❌ PMS not subscribed → cannot access PMS features
  ❌ Accounting subscription expired → cannot post GL
```

### Factor 4: Permissions
```
User's role in tenant must have required permission.
Permissions are atomic (e.g., "invoice.approve", "user.create").

Examples of failure:
  ❌ Staff role cannot approve high-value invoices
  ❌ Guest cannot modify settings
```

---

## Access Control Examples

### Scenario 1: Can Access ✅

```
User: alice
Tenant: Hotel Jakarta
Membership: Admin role (active)
App: PMS
Subscription: PMS is ACTIVE for Hotel Jakarta
Permission: admin has "reservation.create"

Result: ✅ alice CAN create reservations
```

### Scenario 2: Cannot Access (No Membership) ❌

```
User: bob
Tenant: Hotel Jakarta
Status: NOT a member

Result: ❌ bob CANNOT access Hotel Jakarta
         (no membership exists)
```

### Scenario 3: Cannot Access (App Not Subscribed) ❌

```
User: charlie
Tenant: Hotel Surabaya
Membership: Admin role
App: HR (Human Resources)
Subscription: HR is INACTIVE for Hotel Surabaya

Result: ❌ charlie CANNOT access HR
         (hotel doesn't subscribe to HR)
```

### Scenario 4: Cannot Access (Insufficient Permission) ❌

```
User: diana
Tenant: Restaurant XYZ
Membership: Staff role
App: Accounting
Subscription: Accounting is ACTIVE

Action: Try to approve $100,000 invoice
Permission: staff role cannot approve transactions >$5,000

Result: ❌ diana CANNOT approve (lacks permission)
         (only admin/owner can approve >$5,000)
```

---

## Multi-Tenant Scenarios

### Scenario 1: Franchise Owner (Multiple Tenants, Same Role)

```
User: john@hotelgroup.com

Membership 1:
  Tenant: Hotel A
  Role: Owner

Membership 2:
  Tenant: Hotel B
  Role: Owner

Membership 3:
  Tenant: Laundry C
  Role: Owner

Access:
  ✅ Full control over Hotel A (as owner)
  ✅ Full control over Hotel B (as owner)
  ✅ Full control over Laundry C (as owner)
  ❌ Cannot see data from other owners' tenants
  ❌ Data strictly isolated by tenant
```

---

### Scenario 2: Staff with Multiple Roles (Different Tenants)

```
User: alice@example.com

Membership 1:
  Tenant: Hotel A
  Role: Owner
  Permissions: Full

Membership 2:
  Tenant: Laundry B
  Role: Staff
  Permissions: Limited (process orders only)

Membership 3:
  Tenant: Supplier C
  Role: Admin
  Permissions: Manage supply

Access & Permissions:
  Hotel A: ✅ Full control (owner)
  Laundry B: ✅ Limited access (staff)
  Supplier C: ✅ Moderate access (admin)

Key: Same user, different roles, different permissions in each tenant.
     No automatic cross-tenant visibility.
```

---

## Data Access Rules

### Rule 1: Tenant Always Filters Data

Every query MUST be filtered by tenant_id:

```sql
-- ✅ CORRECT
SELECT * FROM reservations
WHERE tenant_id = $1
  AND created_at >= $2;

-- ❌ WRONG (no tenant context)
SELECT * FROM reservations
WHERE created_at >= $1;
```

### Rule 2: No Cross-Tenant Joins (Except via Contract)

```sql
-- ❌ WRONG (could expose data from both tenants)
SELECT r.*, g.* FROM reservations r
JOIN guests g ON r.guest_id = g.id;

-- ✅ CORRECT (explicit tenant context)
SELECT r.*, g.* FROM reservations r
JOIN guests g ON r.guest_id = g.id
WHERE r.tenant_id = $1 AND g.tenant_id = $1;
```

### Rule 3: User CANNOT Specify Tenant

```typescript
// ❌ WRONG: User specifies tenant
const data = await db.getReservations({
  tenant_id: req.query.tenant_id  // User could request ANY tenant!
});

// ✅ CORRECT: Tenant from authenticated context
const tenantId = req.user.tenant_id;  // From JWT token
const data = await db.getReservations({ tenant_id: tenantId });
```

---

## Anti-Patterns (Forbidden)

### ❌ Anti-Pattern 1: Global Roles

```
WRONG:
  User john gets role "Super Admin" globally
  → john can manage ALL tenants
  → This violates tenant isolation

CORRECT:
  User john gets role "Admin" in Tenant 1 (can manage Tenant 1 only)
  User john gets role "Staff" in Tenant 2 (limited access to Tenant 2)
```

---

### ❌ Anti-Pattern 2: Direct User-App Assignment

```
WRONG:
  User john → directly assigned to PMS app
  john can access PMS everywhere

CORRECT:
  Tenant 1 subscribes to PMS
  User john has Membership in Tenant 1
  Therefore john can access PMS (if role permits)
```

---

### ❌ Anti-Pattern 3: Cross-Tenant Data Sharing Without Contract

```
WRONG:
  SELECT * FROM guests
  → Returns guests from ALL tenants

CORRECT:
  SELECT * FROM guests WHERE tenant_id = $1
  → Returns guests from ONE tenant only
```

---

### ❌ Anti-Pattern 4: App Bypassing Membership

```
WRONG:
  IF PMS.is_subscribed() THEN show_features()
  → Doesn't check if user is member

CORRECT:
  IF user.has_membership(tenant) AND app.is_subscribed(tenant)
    THEN show_features()
```

---

## Implementation Checklist

When building identity/membership features:

- [ ] User entity created (global, not tenant-scoped)
- [ ] Tenant entity created (isolated business)
- [ ] Membership join table created (User + Tenant + Role)
- [ ] One role per user per tenant (unique constraint)
- [ ] Role permissions defined and checked
- [ ] Subscription table created (Tenant + App)
- [ ] Feature gates check subscription
- [ ] All queries filtered by tenant_id (no exceptions)
- [ ] User cannot specify tenant_id (derived from auth)
- [ ] Cross-tenant access requires contract
- [ ] Tests verify tenant isolation
- [ ] Tests verify authorization checks

---

## Related Documents

- **REF-05**: Core Concepts (User, Tenant, App, Membership) — Extended version with examples
- **REF-08**: Entity Relationship Model (Core) — Database structure
- **SEC-03**: Authorization, Approval & Audit — Permission enforcement
- **SPEC-07**: Use Cases & Functional Requirements — Who can do what
- **GUIDE-08**: Implementation Checklist — Build order for identity system
