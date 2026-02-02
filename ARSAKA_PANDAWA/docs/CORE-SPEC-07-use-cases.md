# SPEC-07: Use Cases & Functional Requirements

This document defines the **functional use cases and actors** for ARSAKA_PANDAWA (Hospitality App Family). It establishes what each role can do in the system, serving as the foundation for detailed business process flows (BPMNs) and system design.

**Key Principle:** Identity is global; roles are tenant-contextual through Membership. One user can have multiple roles across multiple tenants.

---

## Foundational Concepts

### Identity vs. Membership vs. Role

- **Identity**: Global user account (email, password, profile) — singular, platform-wide
- **Tenant**: Organization/business entity (hotel, restaurant group, franchise)
- **Membership**: User's association with a tenant (relationship)
- **Role**: Permissions within a tenant (Owner, Admin, Staff) — contextual, not global

**Example:**
```
User: john@example.com (global identity)
  └─ Tenant A: Hotel Bali
      └─ Role: Owner (can manage tenant, approve corrections)
  └─ Tenant B: Hotel Jakarta
      └─ Role: Admin (can manage staff, view reports)
  └─ Tenant C: Restaurant Medan
      └─ Role: Staff (can only operate daily transactions)
```

### Access Control Rule

```
User Access = Authentication (Identity) × Authorization (Membership × Role)
```

A user can perform action X only if:
1. User is authenticated (valid identity)
2. User has membership in the target tenant
3. User's role in that tenant grants permission for action X

---

## Actors (Roles)

### 1. Owner

**Definition:** User who initiated subscription for a tenant and holds full administrative authority.

**How to become Owner:**
- Subscribe to platform and create new tenant
- Existing Owner invites and promotes user to Owner role

**Tenant & Subscription Management**
- Create new tenant (new subscription)
- Manage multiple tenants (franchise, group enterprise)
- View and modify tenant subscription (upgrade/downgrade modules)
- Enable/disable application modules per tenant
- View subscription status and billing information
- Configure billing contacts and payment methods

**Governance & Access Control**
- Invite users to tenant
- Assign roles to users (Admin, Staff)
- Revoke user access
- Transfer ownership to another user
- Define role permissions and approval workflows

**Financial Control & Approval**
- Approve large corrections in accounting (write-off, reversal)
- Approve high-value transactions (large refunds, manual invoices)
- View financial dashboards and audit trails
- Manage financial period closure

**Monitoring & Insights**
- Access tenant dashboard (KPIs, metrics)
- View cross-module reports (revenue, occupancy, inventory)
- Access activity logs and audit trails
- Monitor tenant usage and resource consumption

**Data Management**
- Export tenant data
- Request data deletion (GDPR right to erasure)
- Configure data retention policies

---

### 2. Admin

**Definition:** User delegated by Owner to assist with tenant management and operations.

**How to become Admin:**
- Owner invites and assigns Admin role

**Tenant Management**
- Manage users and memberships (invite, remove, change roles)
- Configure application settings (within scope)
- Manage master data (properties, rooms, departments, etc.)
- Manage access controls and permissions (if Owner allows)

**Operational Management**
- Monitor daily activities and operations
- Manage staff schedules and assignments
- Respond to staff requests and escalations
- View real-time operational dashboards

**Data Management**
- Create and manage data (guest profiles, inventory, etc.)
- Bulk import/export data (with approval if large volume)
- Correct non-critical data errors
- Archive historical data

**Reporting & Analysis**
- Generate operational reports
- View role-based dashboards
- Export data for analysis

**Financial (Limited)**
- View financial summaries (not detailed ledger)
- Create invoices (within approval limits)
- Process refunds (within configured limits)

---

### 3. Staff

**Definition:** Operational user working daily in tenant business (hotel receptionist, restaurant cashier, inventory manager, etc.).

**How to become Staff:**
- Admin or Owner invites and assigns Staff role

**Operations - PMS (Property Management System)**
- Create and modify guest reservations
- Check-in and check-out guests
- Manage room status and assignments
- Create and manage guest requests
- Print confirmations and documents

**Operations - Point of Sale / Transactions**
- Sell products and services (room charges, food, services)
- Create invoices and billing documents
- Process payments (cash, card, bank transfer)
- Issue refunds (within configured limits)
- Apply discounts and promotions (within approval limits)

**Guest Management**
- Create and update guest profiles
- Manage guest contact information
- Record guest preferences and history
- Process guest complaints and requests

**Inventory & Procurement**
- Manage inventory levels
- Create purchase orders
- Receive supplier deliveries
- Track consumption and stock movements

**Administration**
- Manage supplier information
- Manage product/service catalogs
- Create and manage documents (contracts, policies)
- Access training materials

**Restrictions:**
- Cannot access accounting ledger
- Cannot approve large transactions
- Cannot modify configurations
- Cannot manage other users
- Cannot access financial reports (unless specific role granted)

---

### 4. Guest / Customer

**Definition:** Person staying at/using the property or purchasing services. May be registered member or unregistered walk-in.

**Without Account (Anonymous Guest)**
- Check-in to property (staff initiates)
- Use services (room, F&B, amenities)
- Pay bills (via staff, no direct payment)
- Depart/check-out

**With Account (Optional Membership)**
- Register account (email, password, profile)
- View own bookings and reservations
- View own invoices and payment history
- Make online payments
- Cancel or modify own reservations
- Participate in loyalty program (if subscribed)
- Submit guest feedback and requests
- Download receipts and documents

**Member-Specific (If Enrolled in Loyalty Program)**
- View member status and benefits
- Earn and redeem points
- Access member-exclusive rates and offers
- Update member profile and preferences

---

### 5. System / Automated Actors

**Definition:** Non-human actors that perform operations via integrations or scheduled jobs.

**External System Integrations**
- **OTA (Online Travel Agency)**
  - Receive bookings from OTA platforms
  - Receive reservation cancellations
  - Send updated inventory/pricing
  - Sync payment status

- **Payment Gateway**
  - Receive payment notifications
  - Receive refund confirmations
  - Update transaction status
  - Handle payment failures and retries

- **Email Service**
  - Send confirmation emails
  - Send reminders (checkout, late payment)
  - Send receipts and documents

**Internal Scheduled Tasks**
- **Night Audit**
  - Calculate room charges
  - Generate daily reports
  - Close day's transactions
  - Reconcile cash and accounting

- **Background Jobs**
  - Period closure (month-end, quarter-end)
  - Data archival and cleanup
  - Report generation (daily, weekly, monthly)
  - Expiry processing (expired offers, bookings)

- **Real-time Processing**
  - Broadcast notifications to clients
  - Publish events to other modules
  - Update read models from write events
  - Calculate aggregates and metrics

---

## Use Case Matrix

| Actor | PMS | Accounting | Inventory | Membership | Reporting |
|-------|-----|------------|-----------|------------|-----------|
| **Owner** | View all | Full access | View all | Full control | Full access |
| **Admin** | Manage (partial) | View summary | Manage | Manage users | Generate reports |
| **Staff** | Operations | Limited | Operations | View own | Operational only |
| **Guest** | View own booking | View own invoices | N/A | Manage own | N/A |
| **System** | Audit, Jobs | Post entries, Close period | Recount, Archive | Sync external | Generate reports |

---

## Access Control Patterns

### Pattern 1: Tenant Isolation
```
User can access Tenant A data only if:
- User has membership in Tenant A
- User's role in Tenant A grants permission
- Request explicitly specifies Tenant A
```

### Pattern 2: Role-Based Permissions
```
Staff cannot:
  ✗ Access accounting ledger
  ✗ Approve transactions > limit
  ✗ Modify configurations
  ✗ Manage other users
  ✗ Access financial reports

Staff can:
  ✓ Perform daily operations
  ✓ Create and process transactions
  ✓ View own data and limited reports
  ✓ Request assistance from Admin/Owner
```

### Pattern 3: Owner as Super-Role
```
Owner in Tenant A has all permissions in Tenant A.
Owner in Tenant A has NO permissions in Tenant B.
Owner cannot become Staff in another tenant's operation.
(Each tenant relationship has independent role)
```

### Pattern 4: Admin as Delegated Owner
```
Admin has subset of Owner permissions:
  ✓ Can manage users and staff
  ✓ Can manage operational data
  ✓ Cannot modify subscription/billing
  ✗ Cannot modify core configurations
  ✗ Cannot approve financial corrections
```

---

## Cross-Tenant Scenarios

### Multi-Property Owner
```
Owner operates Hotel A, Hotel B, Hotel C (three separate tenants).
Owner can:
  ✓ Switch between properties
  ✓ View dashboard for each
  ✓ Manage staff in each
  ✗ Transfer guest directly between properties
  ✗ Consolidate financial reporting (must query separately)
```

### Inter-Tenant Supplier Transaction
```
Supplier is registered in Tenant A.
Tenant B (another organization) wants to purchase from Tenant A's supplier.
Current scope: Each tenant has independent supplier list.
Future: Shared supplier registry with cross-tenant transactions (TBD in later version).
```

---

## External Integration Points

### OTA Integration
- **Inbound**: Bookings, cancellations, guest info
- **Outbound**: Inventory (room availability), pricing, payment status
- **Actor**: OTA System (automated)
- **Permission**: Admin role (or Owner) configures integration

### Payment Gateway Integration
- **Inbound**: Payment confirmations, failures, refunds
- **Outbound**: Charge requests, refund requests
- **Actor**: Payment System (automated)
- **Permission**: System account (scoped to specific tenant)

### Email/SMS Service
- **Inbound**: Delivery status, bounce notifications
- **Outbound**: Confirmation, reminders, receipts
- **Actor**: Notification System (automated)
- **Permission**: System account (platform-wide)

---

## Data Flow by Use Case

### Use Case: Guest Check-in

**Actors**: Guest (or Staff on behalf of guest), PMS System

**Prerequisites**:
- Valid reservation exists
- Guest has completed registration or is identified
- Room is ready (housekeeping status = clean)

**Flow**:
1. Staff searches guest by name/reservation ID
2. System displays guest profile and booking details
3. Staff verifies guest identity
4. Staff marks room as occupied
5. System records check-in timestamp
6. System initiates posting of room charges to ledger
7. Staff provides room key/access
8. Guest receives check-in confirmation

**Post-conditions**:
- Guest is checked in
- Room status is "occupied"
- Check-in recorded in audit log
- Room charges posted to billing ledger

---

### Use Case: Owner Approves Large Refund

**Actors**: Staff (initiates), Admin (optional reviewer), Owner (approver)

**Prerequisites**:
- Valid invoice with paid balance exists
- Refund reason is documented
- Refund amount is > configured threshold

**Flow**:
1. Staff creates refund request with reason and amount
2. System marks refund as "pending approval"
3. Notification sent to Owner
4. Owner reviews refund request and guest details
5. Owner approves or rejects
6. If approved:
   - System creates reversing ledger entry
   - System initiates payment to guest (payment gateway)
   - System records approval in audit log
7. Guest receives refund confirmation email

**Post-conditions**:
- Refund entry is immutable in ledger
- Payment processed to original payment method
- Approval recorded with timestamp and Owner identity

---

### Use Case: System Runs Night Audit

**Actors**: Night Audit System (automated)

**Trigger**: Scheduled at end of business day (e.g., 2 AM)

**Prerequisites**:
- All day's transactions completed
- No open invoices or pending approvals

**Flow**:
1. System queries all rooms and occupied status
2. For each occupied room, calculate room charges for the night
3. System posts charges to guest invoices
4. System posts corresponding accounting entries
5. System calculates totals by payment method
6. System generates daily report (revenue, occupancy, counts)
7. System marks business day as closed

**Post-conditions**:
- All room charges posted
- Accounting balanced
- Daily report available to Owner/Admin
- Can no longer modify yesterday's transactions

---

## Design Principles from Use Cases

### 1. Tenant Context is Immutable
- User cannot specify tenant_id directly
- System derives tenant from authentication + membership
- Every request operates in single tenant context

### 2. Role Determines Capability, Not Vice Versa
- Role is assigned to user in tenant
- Capability/permission is derived from role
- UI shows only capabilities user's role allows

### 3. Financial Transactions Require Approval
- Staff cannot unilaterally approve large transactions
- Owner/Admin approval required above threshold
- All approvals audited and immutable

### 4. No Shared Accounts
- Each person has unique account
- Staff cannot share login
- Activity traceable to individual user

### 5. Guests Can Self-Service
- Registered guests can view own data
- No cross-guest data visibility
- Unauthenticated guests (walk-in) = Staff handles

---

## Related Documents

- **00-identity-membership.md**: Identity and membership concepts (prerequisite)
- **ARCH-02**: Module architecture (how modules map to use cases)
- **SPEC-01**: API Contracts (how use cases map to API endpoints)
- **BPMNs #02-04**: Detailed process flows (how actors perform use cases)
- **ERD #14-20**: Data structures (what data supports these use cases)

---

## Notes for Implementation

- Use case descriptions are functional requirements
- Detailed step-by-step flows are in BPMN documents
- Data structures are defined in ERD documents
- API endpoints are defined in SPEC-01
- UI mockups are in UI-01, UI-02, UI-03
- Database constraints enforce role-based access at data layer
- Business logic validates permissions before executing operations
