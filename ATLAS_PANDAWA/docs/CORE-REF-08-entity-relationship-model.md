# REF-08: Entity Relationship Model (Logical/Conceptual)

This document defines the **logical and conceptual entity relationship model** for ATLAS_PANDAWA. It shows the structure of data entities, their attributes, and relationships across all business domains.

**Purpose**: Reference for understanding the data model structure. This is logical design (independent of database technology), ready to be translated into physical schema.

**Audience**: Database architects, backend developers, data modeling teams, DBA.

---

## ERD Principles (Locked)

### Principle 1: Tenant Isolation
```
All business data scoped to tenant_id.
No data visible across tenant boundaries without explicit contract.
```

### Principle 2: No Cross-Tenant Foreign Keys (Except Contract)
```
Invoice cannot directly FK to another tenant's account.
Only exception: BusinessContract explicitly enables cross-tenant relationships.
```

### Principle 3: Accounting Immutability
```
Ledger (JournalEntry, JournalLine) is append-only.
No updates to posted entries.
No deletes from ledger.
Corrections issued as new reversing entries.
```

### Principle 4: Subscription Gates Features, Not Schema
```
Schema is complete for all features (all code present).
Subscription determines visibility/access, NOT whether tables exist.
All data always stored the same way.
```

### Principle 5: Events ≠ Query Source
```
Events published for integration and audit.
Events are NOT the source for queries.
Database remains source of truth for reading.
```

---

## Context 1: Identity & Access

The foundation: Who users are and what tenants they belong to.

### User Entity

**Purpose**: Global identity across platform

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique user identifier |
| `email` | VARCHAR | UNIQUE, NOT NULL | Email (globally unique) |
| `password_hash` | VARCHAR | NOT NULL | Bcrypt hash |
| `auth_provider` | ENUM | | 'local', 'google', 'microsoft' |
| `first_name` | VARCHAR | | User's first name |
| `last_name` | VARCHAR | | User's last name |
| `status` | ENUM | | 'active', 'inactive', 'suspended', 'deleted' |
| `created_at` | TIMESTAMP | NOT NULL | Account creation |
| `updated_at` | TIMESTAMP | | Last profile update |
| `deleted_at` | TIMESTAMP | | Soft delete timestamp |

**Notes**:
- Global identity (one across all tenants)
- Can belong to multiple tenants via Membership
- Status tracks account state (not tenant-specific)

---

### Tenant Entity

**Purpose**: Business entity (organization, hotel, supplier, service)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique tenant identifier |
| `name` | VARCHAR | NOT NULL | Tenant display name |
| `type` | ENUM | NOT NULL | 'hotel', 'supplier', 'service', 'laundry', 'gym', 'spa' |
| `status` | ENUM | NOT NULL | 'draft', 'active', 'suspended', 'deleted' |
| `created_at` | TIMESTAMP | NOT NULL | Tenant registration date |
| `activated_at` | TIMESTAMP | | When tenant became active |
| `suspended_at` | TIMESTAMP | | When tenant suspended (non-payment) |
| `deleted_at` | TIMESTAMP | | Soft delete date |

**Notes**:
- One tenant = one isolated business
- Data never shared with other tenants (hard isolation)
- Type determines module subscriptions applicable

---

### Membership Entity

**Purpose**: Association between User and Tenant with Role

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique membership record |
| `user_id` | UUID | FK→User, NOT NULL | Which user |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `role` | ENUM | NOT NULL | 'owner', 'admin', 'staff', 'guest' |
| `status` | ENUM | NOT NULL | 'active', 'inactive', 'suspended' |
| `invited_at` | TIMESTAMP | | When user was invited |
| `joined_at` | TIMESTAMP | | When user accepted invite |
| `left_at` | TIMESTAMP | | When user left tenant |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**: (user_id, tenant_id) - One role per user per tenant

**Notes**:
- User can have MANY memberships (one per tenant)
- Tenant can have MANY members
- Role is tenant-contextual (user can be Owner in Tenant A, Staff in Tenant B)
- Status independent from User.status (can leave while active user)

**Relationships**:
```
User 1--* Membership
Tenant 1--* Membership
```

---

## Context 2: App & Subscription

How tenants subscribe to business capabilities.

### App Entity

**Purpose**: Business capability/module (PMS, Accounting, Inventory, etc.)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique app identifier |
| `code` | VARCHAR | UNIQUE, NOT NULL | 'PMS', 'ACC', 'INV', 'HR', 'POS', etc. |
| `name` | VARCHAR | NOT NULL | 'Property Management System', 'Accounting', etc. |
| `category` | ENUM | NOT NULL | 'foundation', 'engine', 'domain', 'addon', 'signage' |
| `description` | TEXT | | What the app does |
| `standalone_technical` | BOOLEAN | NOT NULL | Can run without other modules (code-wise) |
| `standalone_product` | BOOLEAN | NOT NULL | Can be sold alone (business-wise) |
| `created_at` | TIMESTAMP | NOT NULL | When app introduced |

**Notes**:
- Global registry of all available modules
- Fixed set (not changed per tenant)
- Subscription determines if tenant can USE it

---

### TenantApp Entity (Subscription Business Concept)

**Naming Convention**:
- **Physical**: Database table is `TenantApp`
- **Business**: API/concepts refer to this as a "Subscription"
- **Equivalent**: TenantApp table = Subscription business entity (see CORE-REF-01)

**Purpose**: Tenant's subscription to a specific App (module/feature)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique subscription record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `app_id` | UUID | FK→App, NOT NULL | Which app/module |
| `subscription_status` | ENUM | NOT NULL | Billing status: 'active', 'inactive', 'suspended', 'expired' |
| `is_enabled` | BOOLEAN | NOT NULL, DEFAULT true | Feature gate: can owner disable module? |
| `started_at` | TIMESTAMP | NOT NULL | Subscription start date |
| `ended_at` | TIMESTAMP | | Subscription end date (if expired) |
| `billing_cycle` | ENUM | | 'monthly', 'annual', 'lifetime' |
| `next_renewal` | TIMESTAMP | | When subscription auto-renews |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |
| `created_by` | UUID | FK→User | Who created subscription |

**Unique Constraint**: (tenant_id, app_id) - One subscription per tenant per app

**Access Decision**:
```
Module is accessible = (subscription_status = 'active' AND is_enabled = true)
```

**Notes**:
- Controls which apps are visible/available to tenant (subscription_status)
- Allows owner to disable module temporarily (is_enabled flag)
- Does NOT change database schema (all data stored same way)
- Feature gating at application layer checks this table

**Relationships**:
```
Tenant 1--* TenantApp
App 1--* TenantApp
```

---

## Context 3: Inter-Tenant Contract

Cross-tenant business relationships.

### BusinessContract Entity

**Purpose**: Formal agreement between two tenants (supplier relationship, service agreement)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique contract identifier |
| `buyer_tenant_id` | UUID | FK→Tenant, NOT NULL | Buyer (e.g., Hotel) |
| `seller_tenant_id` | UUID | FK→Tenant, NOT NULL | Seller (e.g., Laundry, Supplier) |
| `type` | ENUM | NOT NULL | 'supplier', 'service', 'affiliate' |
| `status` | ENUM | NOT NULL | 'draft', 'active', 'suspended', 'terminated' |
| `contract_number` | VARCHAR | UNIQUE | Legal contract reference |
| `terms` | JSONB | | Contract terms (discount %, payment terms, etc.) |
| `started_at` | TIMESTAMP | NOT NULL | When agreement became active |
| `ended_at` | TIMESTAMP | | When agreement ended |
| `created_at` | TIMESTAMP | NOT NULL | Record creation date |

**Notes**:
- **ONLY cross-tenant foreign keys allowed** (all others are tenant-scoped)
- Enables inter-tenant invoicing, PO, payments
- Requires explicit approval from both sides

---

## Context 4: Accounting Core

Financial records and ledger (append-only).

### ChartOfAccount Entity

**Purpose**: GL account structure

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique account identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant owns this account |
| `code` | VARCHAR | NOT NULL | Account number (1000, 2000, etc.) |
| `name` | VARCHAR | NOT NULL | Account name (Cash, AR, Revenue, etc.) |
| `type` | ENUM | NOT NULL | 'asset', 'liability', 'equity', 'revenue', 'expense' |
| `parent_account_id` | UUID | FK→ChartOfAccount | Hierarchical GL structure |
| `is_header` | BOOLEAN | | Is this a summary account (no transactions) |
| `is_active` | BOOLEAN | NOT NULL | Account in use (soft delete) |
| `created_at` | TIMESTAMP | NOT NULL | When account added |

**Notes**:
- Tenant-scoped (each tenant has own COA)
- Hierarchical structure for GL reporting
- Immutable once created (only soft-delete)

---

### AccountingPeriod Entity

**Purpose**: Monthly/quarterly accounting periods (open/closed state)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique period record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `period` | VARCHAR | NOT NULL | "2025-01", "2025-Q1", etc. |
| `period_start` | DATE | NOT NULL | First day of period |
| `period_end` | DATE | NOT NULL | Last day of period |
| `status` | ENUM | NOT NULL | 'open', 'locked', 'closed' |
| `locked_at` | TIMESTAMP | | When period locked (no new posting) |
| `closed_at` | TIMESTAMP | | When period officially closed |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- Controls whether GL posting allowed for date range
- Locked = no new posting, but can view
- Closed = archival, reporting finalized

---

### JournalEntry Entity

**Purpose**: Double-entry transaction (one entry = 2+ lines)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique journal entry identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `entry_date` | DATE | NOT NULL | Effective date of transaction |
| `source_type` | ENUM | NOT NULL | 'invoice', 'payment', 'adjustment', 'reversal' |
| `source_id` | VARCHAR | | FK to Invoice, Payment, etc. (polymorphic) |
| `description` | VARCHAR | | What this entry is for |
| `status` | ENUM | NOT NULL | 'draft', 'posted', 'reversed' |
| `posted_at` | TIMESTAMP | NOT NULL | When posted to GL |
| `posted_by` | UUID | FK→User | Who posted this entry |
| `created_at` | TIMESTAMP | NOT NULL | Entry creation time |

**Notes**:
- Immutable once posted
- source_type + source_id allows traceability to origin
- Posted entries never deleted (soft-delete only if absolutely necessary)

---

### JournalLine Entity

**Purpose**: Individual debit/credit line in a journal entry

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique line identifier |
| `journal_entry_id` | UUID | FK→JournalEntry, NOT NULL | Which entry this belongs to |
| `account_id` | UUID | FK→ChartOfAccount, NOT NULL | Which GL account |
| `debit_amount` | DECIMAL(18,2) | | Debit side (one of debit/credit) |
| `credit_amount` | DECIMAL(18,2) | | Credit side (one of debit/credit) |
| `description` | VARCHAR | | Line description |
| `created_at` | TIMESTAMP | NOT NULL | Line creation |

**Constraint**: EXACTLY ONE of debit_amount or credit_amount is non-zero

**Notes**:
- Always in same tenant as JournalEntry
- Immutable (append-only pattern)
- No updates to posted lines

**Relationships**:
```
JournalEntry 1--* JournalLine
ChartOfAccount 1--* JournalLine
```

---

## Context 5: AR/AP (Accounts Receivable/Payable)

Customer and supplier invoices.

### Invoice Entity

**Purpose**: Billing document (from tenant or to tenant)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique invoice identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Issuer tenant |
| `counterparty_tenant_id` | UUID | FK→Tenant | For inter-tenant invoices (buyer/supplier) |
| `contract_id` | UUID | FK→BusinessContract | If from business contract |
| `invoice_number` | VARCHAR | NOT NULL | "INV-2025-001" |
| `type` | ENUM | NOT NULL | 'AR' (receivable), 'AP' (payable) |
| `status` | ENUM | NOT NULL | 'draft', 'issued', 'paid', 'voided', 'reversed' |
| `amount` | DECIMAL(18,2) | NOT NULL | Invoice total |
| `currency` | VARCHAR | NOT NULL | 'IDR', 'USD', etc. |
| `description` | TEXT | | What invoice is for |
| `issued_at` | TIMESTAMP | NOT NULL | Issue date |
| `due_date` | DATE | NOT NULL | Payment due date |
| `paid_at` | TIMESTAMP | | When fully paid |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- AR: tenant_id is seller, counterparty is buyer
- AP: tenant_id is buyer, counterparty is seller
- counterparty_tenant_id ONLY populated for inter-tenant invoices
- Domestic invoices have counterparty_tenant_id = NULL
- contract_id links to BusinessContract if inter-tenant

---

### Payment Entity

**Purpose**: Payment allocation to invoice

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique payment record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant recorded payment |
| `invoice_id` | UUID | FK→Invoice, NOT NULL | Which invoice being paid |
| `amount` | DECIMAL(18,2) | NOT NULL | Payment amount |
| `currency` | VARCHAR | NOT NULL | Currency of payment |
| `method` | ENUM | NOT NULL | 'cash', 'check', 'transfer', 'gateway' |
| `reference` | VARCHAR | | Bank reference, check #, etc. |
| `status` | ENUM | NOT NULL | 'recorded', 'cleared', 'reversed' |
| `paid_at` | TIMESTAMP | NOT NULL | When payment was made |
| `cleared_at` | TIMESTAMP | | When payment confirmed/cleared |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- Multiple payments can be allocated to one invoice
- Partial payments allowed (pay_amount < invoice_amount)
- Status tracks reconciliation state

**Relationships**:
```
Invoice 1--* Payment
```

---

## Context 6: Procurement

Purchase orders (buyer side).

### PurchaseOrder Entity

**Purpose**: Buyer's order to supplier

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique PO identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Buyer (who issued PO) |
| `supplier_tenant_id` | UUID | FK→Tenant, NOT NULL | Seller (who receives PO) |
| `contract_id` | UUID | FK→BusinessContract, NOT NULL | Links to supplier agreement |
| `po_number` | VARCHAR | NOT NULL | "PO-2025-001" |
| `status` | ENUM | NOT NULL | 'draft', 'issued', 'acknowledged', 'fulfilled', 'cancelled' |
| `total_amount` | DECIMAL(18,2) | NOT NULL | PO total |
| `currency` | VARCHAR | NOT NULL | Currency of PO |
| `delivery_date` | DATE | NOT NULL | Expected delivery |
| `issued_at` | TIMESTAMP | NOT NULL | When PO sent to supplier |
| `fulfilled_at` | TIMESTAMP | | When goods received |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- Always has two tenants (buyer + supplier)
- Must reference BusinessContract
- Triggers AP invoice when supplier invoices

---

## Context 7: Approval & Audit

Workflow and compliance tracking.

### ApprovalRequest Entity

**Purpose**: Approval task for high-value transactions

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique approval request |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `entity_type` | ENUM | NOT NULL | 'invoice', 'po', 'payment', 'adjustment' |
| `entity_id` | UUID | NOT NULL | Which entity needs approval |
| `amount` | DECIMAL(18,2) | | Amount being approved |
| `required_role` | ENUM | NOT NULL | 'admin', 'owner' (minimum role required) |
| `status` | ENUM | NOT NULL | 'pending', 'approved', 'rejected' |
| `requested_by` | UUID | FK→User | Who requested approval |
| `approved_by` | UUID | FK→User | Who approved |
| `rejected_reason` | TEXT | | If rejected, why |
| `requested_at` | TIMESTAMP | NOT NULL | When request created |
| `decided_at` | TIMESTAMP | | When decision made |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- Thresholds defined in policy (e.g., >$5K needs approval)
- Multiple approvals possible (chain of approvals)
- Immutable once decided

---

### AuditLog Entity

**Purpose**: Immutable audit trail (append-only)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | BIGSERIAL | PK | Sequence number (append-only) |
| `event_id` | UUID | UNIQUE | Correlation to event log |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which tenant |
| `actor_id` | UUID | FK→User | Who performed action (null if system) |
| `action` | VARCHAR | NOT NULL | 'create', 'update', 'delete', 'post', 'approve' |
| `entity_type` | VARCHAR | NOT NULL | 'invoice', 'journal_entry', 'user', etc. |
| `entity_id` | UUID | | Which entity affected |
| `changes` | JSONB | | {field: {old: x, new: y}} |
| `ip_address` | VARCHAR | | Source IP |
| `user_agent` | VARCHAR | | Browser/client info |
| `status` | ENUM | NOT NULL | 'success', 'failure' |
| `error_message` | TEXT | | If failure, why |
| `created_at` | TIMESTAMP | NOT NULL | When action occurred |

**Constraints**:
- Append-only (no updates, no deletes)
- Database trigger prevents modification
- Immutable sequence number

**Notes**:
- Complete audit trail for compliance
- Linked to events via event_id for tracing
- Cannot be edited (only added to)

**Relationships**:
```
Tenant 1--* ApprovalRequest
Tenant 1--* AuditLog
User 1--* AuditLog (as actor)
```

---

## Boundary Checks (Anti-Patterns)

### ❌ Forbidden Schema Patterns

| Anti-Pattern | Why Forbidden | Consequence |
|------|------|---|
| Invoice FK directly to another tenant | Violates tenant isolation | Data leak across tenants |
| JournalLine referencing account in different tenant | Breaks GL integrity | Can post to wrong COA |
| TenantApp modifying table schema | Subscription should gate features, not schema | Inconsistent data structures |
| Deleting from JournalEntry/JournalLine | Breaks immutability, breaks audit | Can't trace financial history |
| Membership to non-existent Tenant | Referential integrity | Orphaned access records |
| Invoice without either AR or AP designation | Ambiguity | Can't determine if receivable or payable |

---

## Data Isolation Rules

### Tenant Filter on All Queries

```sql
-- ALL queries must include tenant context:

-- ✅ CORRECT
SELECT * FROM invoices
WHERE tenant_id = $1 AND invoice_number = 'INV-001';

-- ❌ WRONG (no tenant filter)
SELECT * FROM invoices
WHERE invoice_number = 'INV-001';

-- ✅ CORRECT (multi-table join)
SELECT i.*, p.*
FROM invoices i
JOIN payments p ON i.id = p.invoice_id
WHERE i.tenant_id = $1 AND p.tenant_id = $1;
```

### Cross-Tenant Join Only via Contract

```sql
-- ❌ WRONG (direct cross-tenant)
SELECT h.*, l.*
FROM hotel_invoices h
JOIN laundry_invoices l ON h.supplier_tenant_id = l.tenant_id;

-- ✅ CORRECT (via BusinessContract)
SELECT h.*, l.*, bc.*
FROM hotel_invoices h
JOIN business_contracts bc ON h.contract_id = bc.id
JOIN laundry_invoices l ON l.tenant_id = bc.seller_tenant_id
WHERE h.tenant_id = $1;
```

---

## Implementation Notes

### Physical Schema Generation

This logical model can be translated to physical schema using:
- PostgreSQL tables (recommended)
- Column naming: snake_case
- Indexes on FK, tenant_id, status fields
- Partitioning by tenant_id for very large tables (invoices, journal_entries, audit_log)

### Soft Deletes

Most entities support soft delete via NULL timestamp:
- `User.deleted_at`
- `Tenant.deleted_at`
- `Invoice.voided_at`

Only `AuditLog` has NO soft delete (pure append-only).

### Temporal Tracking

All entities have creation timestamp:
```sql
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```

Most have update/state-change tracking:
```sql
posted_at, locked_at, paid_at, closed_at, decided_at
```

---

## Relationship Summary

```
User 1--* Membership
Tenant 1--* Membership
Tenant 1--* TenantApp
App 1--* TenantApp
Tenant 1--* ChartOfAccount
Tenant 1--* AccountingPeriod
Tenant 1--* JournalEntry
JournalEntry 1--* JournalLine
ChartOfAccount 1--* JournalLine
Tenant 1--* Invoice
Invoice 1--* Payment
Tenant 1--* PurchaseOrder
PurchaseOrder M--* Invoice (via supplier response)
Tenant 1--* ApprovalRequest
Tenant 1--* AuditLog
BusinessContract (cross-tenant only)
```

---

## How to Use This Reference

1. **For Database Design**: Translate each entity to table schema
2. **For API Design**: Each entity typically has CRUD endpoints
3. **For Feature Development**: Reference entity relationships when adding business logic
4. **For Data Validation**: Understand constraints and unique keys
5. **For Backup/Restore**: Understand dependencies between entities
6. **For Reporting**: Understand which tables to join and how

---

## Related Documents

- **REF-03**: Module Catalog — What each app contains
- **REF-04**: Subscription & Dependency Matrix — How apps relate
- **REF-05**: Core Concepts — User, Tenant, App, Membership definitions
- **ARCH-05**: Frontend Architecture — How entities are exposed to UI
- **SPEC-07**: Use Cases — What users can do with these entities
- **SEC-02**: Data Protection & Privacy — Encryption and PII handling for these entities
- **SEC-03**: Authorization, Approval & Audit — How access to these entities is controlled
