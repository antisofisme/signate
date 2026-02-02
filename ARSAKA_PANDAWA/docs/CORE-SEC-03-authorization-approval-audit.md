# SEC-03: Authorization, Approval & Audit

This document specifies the **authorization model, approval workflows, and audit requirements** for ARSAKA_PANDAWA. It defines how access control is enforced, how approvals are managed, and how all actions are audited.

**Prerequisite**: SEC-01 (Authentication), SEC-02 (Data Protection), ARCH-08 (Security Architecture)

---

## Core Principles (Locked)

### Principle 1: Security is Tenant-Scoped
- No access across tenants without explicit business contract
- Tenant is security boundary
- Cross-tenant operations require formal approval workflow

### Principle 2: Permissions Trump Roles (Permission-Based Access Control)
- **Roles are containers** of permissions (convenience, not enforcement)
- **Permissions are atomic units** of authorization (the real gatekeepers)
- **System checks permissions, not role names** - Role name is just a label
- **Same role can have different permissions** in different tenants
- **Runtime check**: `if (user.membership.permissions.contains('invoice.approve')) then allow()`

**Key Distinction**:
```
❌ WRONG (Role-Based):
   if (user.role == 'Admin') then allow()

✅ CORRECT (Permission-Based):
   if (user.permissions.includes('invoice.approve')) then allow()
```

**Why This Matters**:
- Admin role in Hotel A has: ['invoice.approve', 'journal.post', 'user.create']
- Admin role in Hotel B has: ['invoice.approve'] only (CFO approval required for journal)
- Same role, different permissions → different access
- Runtime checks the actual permission list, not the role name

### Principle 3: Approval is Business Logic, Not UI
- Approval is part of domain (not bolted on to UI)
- Approval workflow defined in Workflow Engine
- Approval can happen via API, webhook, or UI
- Approval decisions trigger events and change domain state

### Principle 4: No Direct Financial Data Modification
- Ledger entries never edited after posting
- Corrections use reversals (new entries reversing old)
- Keeps audit trail intact
- Maintains immutability guarantee

### Principle 5: Audit is Mandatory, Not Optional
- Every sensitive action logged
- Immutable audit trail (append-only, no deletes)
- Includes: who, when, what, before/after values
- Enables forensics and compliance

### Principle 6: Service Accounts Use Tenant Membership (No Global Roles)
- System accounts (scheduler, integration service, migration tool) are Users
- They have Membership in specific tenants (not "global admin")
- **CRITICAL RESTRICTION**: Service accounts can ONLY have Membership in:
  - System/Platform tenants (e.g., "Platform-Operations", "System-Audit")
  - NOT in any customer operational tenants
- **Support team exception**: Temporary Membership in customer tenants requires:
  - Explicit approval request with justification
  - Time-limited access (auto-revoke after 30 days)
  - Audit logging of all access during support session
- Example: ✅ Scheduler has Membership(role=staff) in "Platform-System" tenant
- Example: ❌ Scheduler cannot have blanket Membership in "Hotel-A", "Hotel-B", etc.
- No "Super Admin" role exists anywhere in the system

---

## Financial Data Immutability (Specification)

**Applies To**: JournalEntry, JournalLine, GLAccount, AuditLog, any table with posted_at field

### Rule 1: Posted Financial Data Cannot Be Modified

```
AFTER posting (posted_at IS NOT NULL):
  ❌ Cannot UPDATE any field
  ❌ Cannot DELETE the record
  ✅ Can only REVERSE (create opposite entry)
```

### Rule 2: Immutable Core Fields

These fields cannot change after posting:

| Field | Reason | Enforcement |
|-------|--------|-------------|
| `posted_at` | Marks point of no return | Database constraint: once set, cannot change |
| `amount` | GL balance integrity | Database constraint: once set, cannot change |
| `debit_account_id` | Audit trail clarity | Database constraint: once set, cannot change |
| `credit_account_id` | Audit trail clarity | Database constraint: once set, cannot change |
| `transaction_id` | Source traceability | Database constraint: once set, cannot change |
| `tenant_id` | Multi-tenant isolation | Database constraint: once set, cannot change |

### Rule 3: Correction Pattern (Reversal Entry)

To correct posted data, create new entries (never modify original):

```
ORIGINAL ENTRY:
  JournalEntry {
    id: 'je-001',
    posted_at: '2025-12-20T10:00:00Z',
    amount: 1000,
    debit_account_id: '1000',  // Revenue
    credit_account_id: '1200'   // AR
  }

CORRECTION DISCOVERED (double post):
  ✅ CORRECT: Create REVERSAL entry
  JournalEntry {
    id: 'je-002',
    posted_at: '2025-12-21T09:00:00Z',
    amount: -1000,  // Negative to reverse
    debit_account_id: '1200',    // Reverse the AR
    credit_account_id: '1000',   // Reverse the Revenue
    reversal_of: 'je-001'        // Link to original
  }

  ❌ WRONG: Modify original entry
  UPDATE journal_entries SET amount = 500 WHERE id = 'je-001';
```

### Rule 4: Database Enforcement

Implement these constraints in schema:

```sql
-- Prevent updates to posted entries
CREATE TRIGGER prevent_posted_update
BEFORE UPDATE ON journal_entries
FOR EACH ROW
WHEN (OLD.posted_at IS NOT NULL)
BEGIN
  RAISE EXCEPTION 'Posted journal entries are immutable';
END;

-- Prevent deletes of posted entries
CREATE TRIGGER prevent_posted_delete
BEFORE DELETE ON journal_entries
FOR EACH ROW
WHEN (OLD.posted_at IS NOT NULL)
BEGIN
  RAISE EXCEPTION 'Posted journal entries cannot be deleted';
END;

-- Ensure immutable core fields
ALTER TABLE journal_entries ADD CONSTRAINT immutable_posted_at
  CHECK (posted_at IS NULL OR posted_at <= NOW());
```

### Rule 5: Audit Trail for Corrections

Every correction must be logged:

```
AuditLog {
  id: 'audit-001',
  tenant_id: 'hotel-123',
  action: 'REVERSE_JOURNAL_ENTRY',
  original_entry_id: 'je-001',
  reversal_entry_id: 'je-002',
  reason: 'Double posting detected during period close',
  approved_by: 'cfo-user-id',
  approved_at: '2025-12-21T09:30:00Z',
  amount_reversed: 1000,
  is_immutable: true
}
```

### Rule 6: What CAN Be Modified Before Posting

Before posting (posted_at IS NULL), normal modifications allowed:

| Action | Before Posting | After Posting |
|--------|---------------|---------------|
| Create new entry | ✅ Yes | ✅ Yes (only reversal) |
| Modify draft entry | ✅ Yes | ❌ No |
| Delete draft entry | ✅ Yes | ❌ No (reversal only) |
| Add attachment | ✅ Yes | ✅ Yes (read-only) |
| Change description | ✅ Yes | ❌ No |

---

## Terminology (Clarification)

To avoid confusion, these terms have specific meanings:

| Term | Definition | Example |
|------|-----------|---------|
| **Membership Role** | User's access level in a specific Tenant (Owner, Admin, Staff, Guest) | "alice is Staff in Hotel A" |
| **Permission** | Atomic capability that user can perform (requires permission + role) | "invoice.approve", "user.create" |
| **Approval Authority** | User's limit for approving transactions (dollar amount or escalation level) | "Can approve invoices < $50,000" |
| **Access Control Decision** | Authentication × Membership × Permission × (optionally Approval Authority) | User can perform action if all required conditions met |

**Key Insight**: Roles are groups of permissions, but system enforces permissions, not roles. Same role can have different permissions in different tenants (tenant-specific RBAC).

---

## Role-Based Access Control (RBAC)

### Standard Roles

Every tenant has these roles. Permissions can vary per tenant.

#### Role 1: Owner
**Definition**: User who created tenant and has ultimate authority

**Typical Permissions**:
- ✅ Create and delete users
- ✅ Assign roles
- ✅ Change tenant settings
- ✅ Approve large transactions (no amount limit)
- ✅ Access financial statements
- ✅ Cancel subscriptions
- ✅ Override approvals (with audit log)

**Scope**: Full access to tenant

#### Role 2: Admin
**Definition**: User delegated by Owner to manage operations

**Typical Permissions**:
- ✅ Create and manage staff (but not other admins)
- ✅ Approve medium transactions (e.g., < $50,000)
- ✅ Access operational dashboards
- ✅ Manage configurations (within limits)
- ❌ Cannot delete users
- ❌ Cannot change subscription
- ❌ Cannot approve large amounts (escalated to Owner)

**Scope**: Operational and partial financial access

#### Role 3: Staff
**Definition**: Operational user performing daily tasks

**Typical Permissions**:
- ✅ Create reservations (PMS)
- ✅ Process sales (POS)
- ✅ Post charges
- ✅ View own data
- ❌ Cannot approve invoices
- ❌ Cannot modify financial records
- ❌ Cannot access user management
- ❌ Cannot view reports (unless specific permission granted)

**Scope**: Daily operations only

#### Role 4: Guest
**Definition**: External user (customer/guest)

**Typical Permissions**:
- ✅ View own reservations
- ✅ View own invoices
- ✅ Make payments
- ✅ Submit feedback
- ❌ Cannot view other guests' data
- ❌ Cannot access operational areas

**Scope**: Self-service only

---

## Permission-Based Authorization

### Permission Structure

```typescript
interface Permission {
  id: string;                    // "invoice.approve"
  resource: string;              // "invoice"
  action: string;                // "approve"
  description: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";  // For fraud detection
  requires_approval: boolean;   // Does using this require approval?
  approval_level?: string;      // "admin", "owner", etc.
}
```

### Permission Examples

| Permission | Resource | Action | Risk | Description |
|-----------|----------|--------|------|-------------|
| `invoice.create` | invoice | create | LOW | Create invoice |
| `invoice.approve` | invoice | approve | HIGH | Approve and post invoice |
| `payment.post` | payment | post | MEDIUM | Record payment |
| `journal.post` | journal | post | HIGH | Post GL entry |
| `user.delete` | user | delete | CRITICAL | Delete user account |
| `config.modify` | config | modify | HIGH | Change settings |
| `po.issue` | po | issue | MEDIUM | Issue purchase order |
| `po.approve` | po | approve | MEDIUM | Approve PO from supplier |
| `contract.accept` | contract | accept | MEDIUM | Accept inter-tenant contract |

### Permission Naming Standard (Authoritative)

**Format**: `{resource}.{action}`

**Rules** (LOCKED - all code must conform):

1. **Always lowercase**
   - ✅ `invoice.approve`
   - ❌ `Invoice.Approve`
   - ❌ `INVOICE.APPROVE`

2. **No special characters except dot**
   - ✅ `po.issue` (underscore would be `po_issue`, NOT `po-issue`)
   - ❌ `po-issue` (use dot, not dash)
   - ❌ `po/issue` (no slashes)

3. **Resource-first (domain.entity pattern)**
   - ✅ `invoice.approve` (what resource, what action)
   - ❌ `approve.invoice` (action-first is not standard)

4. **Action verbs from standardized list**
   - ✅ `{resource}.create`, `.read`, `.update`, `.delete`
   - ✅ `{resource}.approve`, `.reject`, `.publish`
   - ✅ `{resource}.post`, `.submit`, `.export`
   - ⚠️ Custom actions OK if clear: `.issue`, `.reconcile`, `.override`
   - ❌ `{resource}.get` (use `.read`)
   - ❌ `{resource}.put` (use `.update`)

5. **NO role suffixes** (❌ DO NOT do this):
   - ❌ `invoice.approve.admin` (role is checked separately, not in permission name)
   - ❌ `invoice.approve.owner` (same reason)
   - ✅ Just `invoice.approve` (role has this permission or doesn't)

6. **NO amount suffixes** (❌ DO NOT do this):
   - ❌ `invoice.approve.under_5000` (amounts are enforced in role/approval rules, not permission name)
   - ❌ `invoice.approve.unlimited` (same reason)
   - ✅ Just `invoice.approve` (approval_authority entity defines limit by user/role)

**Standard Permission List**:
```
CRUD Operations:
  resource.create
  resource.read
  resource.update
  resource.delete

Financial Operations:
  invoice.create, invoice.approve, invoice.post, invoice.reverse
  payment.create, payment.post, payment.refund
  journal.post, journal.reverse
  expense.approve, expense.reimburse

Operational:
  po.issue, po.approve, po.cancel
  reservation.create, reservation.modify, reservation.cancel
  room.update_status

User Management:
  user.create, user.read, user.update, user.delete
  membership.grant, membership.revoke
  role.assign

Sensitive:
  config.modify
  account.list_all (cross-account read)
  contract.accept, contract.revoke

Reporting & Export:
  report.view, report.export
  data.export, data.import
```

### Permission Assignment

Permissions assigned to:
1. **Roles** (default set)
2. **Individual users** (override, per tenant)

**Example**:
```
Role: Staff
  Permissions: invoice.create, payment.post

User: john (Staff role in Hotel A)
  Additional: po.issue (one-off grant for procurement task)

Result: john in Hotel A has: invoice.create, payment.post, po.issue
        john in Hotel B (also staff) has: invoice.create, payment.post (no po.issue)
```

### Permission Checks

Every action checked:

```typescript
function canUserPerformAction(user, tenant, permission) {
  // 1. Is user authenticated?
  if (!user.authenticated) return false;

  // 2. Does user have membership in tenant?
  const membership = findMembership(user, tenant);
  if (!membership) return false;

  // 3. Does user/role have permission?
  const userPermissions = getPermissions(user, membership.role, tenant);
  if (!userPermissions.includes(permission)) return false;

  // 4. Is app subscribed (if permission is module-specific)?
  if (permission.requires_app && !isTenantSubscribedTo(tenant, permission.app)) {
    return false;
  }

  return true;
}
```

---

## Approval Workflows

### Principle: Generic Approval Engine

Approvals are **not hardcoded per module**. All approvals use **Workflow Engine**.

### Approval Structure

```typescript
interface Approval {
  id: string;
  resource_type: string;        // "invoice", "po", "refund"
  resource_id: string;          // "inv-001"
  tenant_id: string;
  requested_by: string;         // User who initiated action
  requested_at: DateTime;

  approval_rules: ApprovalRule[]; // Who must approve, when, amount threshold

  status: "PENDING" | "APPROVED" | "REJECTED";
  approvals: ApprovalDecision[];  // Track each approval step
  completed_at?: DateTime;
  reason?: string;              // If rejected
}

interface ApprovalRule {
  level: number;                // Order (1st level, 2nd level, etc.)
  approver_permission: string;  // "invoice.approve.admin"
  threshold?: number;           // If amount > X, requires this level
  description: string;
}

interface ApprovalDecision {
  approver_id: string;
  approver_role: string;
  decision: "APPROVED" | "REJECTED";
  decided_at: DateTime;
  reason?: string;
  comment?: string;
}
```

### Example 1: Invoice Approval (Amount-Based)

**Rule Definition**:
```
Invoice Approval Rules:
  Level 1: Amount < $5,000
    Approver: Staff with invoice.approve permission
    Auto-approved if posted by admin

  Level 2: Amount $5,000 - $50,000
    Approver: Admin
    Requires explicit approval

  Level 3: Amount > $50,000
    Approver: Owner
    Requires explicit approval
```

**Flow**:
```
1. Invoice created for $30,000
2. System determines: requires Level 2 approval (Admin)
3. Triggers Approval record (status: PENDING)
4. Notifies all Admin users in tenant
5. Admin reviews invoice, clicks "Approve"
6. Approval decision recorded
7. Status → APPROVED
8. Event published: "invoice.approved"
9. Accounting posts journal entry
```

### Example 2: PO Approval (Inter-Tenant)

**Rule Definition**:
```
PO Approval Rules:
  Level 1: Amount < $10,000
    Approver: Any supplier staff
    Auto-approved

  Level 2: Amount $10,000 - $100,000
    Approver: Supplier admin
    Manual approval required

  Level 3: Amount > $100,000
    Approver: Supplier owner
    Manual approval required
```

**Flow**:
```
1. Hotel issues PO for $50,000 to Supplier
2. Event published to Supplier tenant
3. System creates Approval record in Supplier tenant
4. Requires Level 2 approval (Supplier admin)
5. Supplier admin reviews:
   - Can we fulfill?
   - Is pricing correct?
   - Do we have inventory?
6. Supplier admin approves (or rejects with reason)
7. Approval decision sent back to Hotel (via event)
8. Hotel records PO status: ACCEPTED or REJECTED
```

### Example 3: Refund Approval (Risk-Based)

**Rule Definition**:
```
Refund Approval Rules:
  Risk: LOW (guest error, small amount)
    Approver: Staff (any staff can approve)
    Threshold: < $500

  Risk: MEDIUM
    Approver: Admin
    Threshold: $500 - $5,000

  Risk: HIGH (large refund, corporate guest, dispute)
    Approver: Owner
    Threshold: > $5,000
    Additional: Requires fraud check
```

---

## Audit Trail

### Audit Log Structure

Every sensitive action logged with:

```typescript
interface AuditLog {
  id: string;                   // Unique identifier
  tenant_id: string;            // Which tenant
  actor_type: "USER" | "SYSTEM" | "EXTERNAL";
  actor_id: string;             // user-123, system, webhook-caller
  action: string;               // "invoice.approved", "user.created"
  resource_type: string;        // "invoice", "user", "config"
  resource_id: string;          // inv-001, user-456

  timestamp: DateTime;          // When action happened
  ip_address?: string;          // For user actions
  user_agent?: string;          // Browser/client info

  old_value: Record<string, any>;   // Before values
  new_value: Record<string, any>;   // After values
  delta: Record<string, any>;       // What changed

  reason?: string;              // Why (if approval)
  approval_id?: string;         // If part of approval

  status: "SUCCESS" | "FAILED";
  error_message?: string;       // If failed

  created_at: DateTime;         // Immutable timestamp
  hash?: string;                // For integrity verification
}
```

### Mandatory Audit Events

**Authentication Events**:
- `auth.login` — User logged in
- `auth.logout` — User logged out
- `auth.failed_login` — Failed authentication attempt

**User Management Events**:
- `user.created` — New user created
- `user.role_changed` — User role modified
- `user.deleted` — User deleted
- `membership.created` — User added to tenant
- `membership.removed` — User removed from tenant

**Financial Events**:
- `invoice.created` — Invoice created
- `invoice.approved` — Invoice approved and posted
- `journal_entry.posted` — GL entry posted
- `payment.recorded` — Payment processed
- `refund.issued` — Refund created

**Configuration Events**:
- `config.modified` — Settings changed
- `permission.granted` — Permission added
- `permission.revoked` — Permission removed
- `contract.created` — Inter-tenant contract created

**Approval Events**:
- `approval.requested` — Approval needed
- `approval.approved` — Approval granted
- `approval.rejected` — Approval denied

### Audit Log Immutability

```
RULE: Audit logs are append-only
  ✅ Can INSERT new log entries
  ❌ Cannot UPDATE existing entries
  ❌ Cannot DELETE entries

ENFORCEMENT:
  - Database trigger prevents updates/deletes
  - Application never calls UPDATE on audit log
  - Archival process: move to read-only storage
```

### Audit Log Retention Policy

**See CORE-REF-01 Section "Soft Delete & Data Retention Policy" for authoritative retention rules**

**Summary**:
- **Active Retention**: 7 years (regulatory compliance for financial records)
- **Soft Delete Pattern**: Audit logs NEVER physically deleted, only logically archived
- **Archive Timeline**:
  - Hot storage (0-1 year): Fast access, query-able
  - Warm storage (1-7 years): Slower access, retained for compliance
  - Cold storage (7+ years): Optional archival (per tenant config)
  - Destruction: After 7 years + retention period extension

**Immutability During Retention**:
- ✅ Can INSERT new audit entries
- ✅ Can READ audit entries (all 7 years)
- ✅ Can ARCHIVE/move to cold storage
- ❌ Cannot UPDATE entries (even if soft-deleting parent record)
- ❌ Cannot DELETE entries (ever, until after 7 years)
- ❌ Cannot MODIFY entries (immutable facts)

**Compliance Guarantees**:
- All audit entries retained for 7 years minimum
- Complete audit trail for any resource (invoice, user, config change)
- Regulatory audits can request full audit trail with proof of immutability
- Hash/signature verification available (hash field in AuditLog)

**Example Query** (with retention filtering):
```sql
SELECT * FROM audit_logs
WHERE tenant_id = $1
  AND resource_id = 'inv-12345'
  AND created_at >= NOW() - INTERVAL '7 years'
  AND deleted_at IS NULL  -- Never include soft-deleted entries
ORDER BY created_at DESC;
```

### Audit Log Access Control

**Who can view audit logs**:
- Owner: Full access to tenant audit logs
- Admin: Can view specific domains (operations, approvals)
- Staff: Can only view own actions

**Who can export**:
- Owner: Full audit export for compliance
- Admin: Operational audit export only

**Restrictions**:
- ❌ Cannot modify audit logs
- ❌ Cannot delete audit logs
- ❌ Cannot export and re-import (creates new logs)

---

## Correction & Reversal Model

### Principle: No Direct Editing of Financial Records

Once a journal entry is posted, it cannot be edited. Corrections use reversals.

### Reversal Process

**Step 1: Identify Error**
- User discovers financial record error
- Example: Invoice posted for $1,000, should be $500

**Step 2: Create Reversal Entry**
- Approver creates reversal journal entry
- Entry reverses the original (negative amounts)
- Records reason for reversal

**Example**:
```
Original Entry (je-001):
  Account 1200 (AR): +$1,000 debit
  Account 4100 (Revenue): +$1,000 credit

Reversal Entry (je-002):
  Reverses: je-001
  Account 1200 (AR): -$1,000 debit (credit)
  Account 4100 (Revenue): -$1,000 credit (debit)
  Description: "Reversal of je-001 - incorrect amount"
  Reason: "Invoice amount error, should be $500 not $1,000"
  Approved by: admin-456
  Timestamp: 2025-12-22
```

**Step 3: Create Corrected Entry**
- Create new entry with correct amounts
- Links to reversal for traceability

**Corrected Entry (je-003)**:
```
Account 1200 (AR): +$500 debit
Account 4100 (Revenue): +$500 credit
Description: "Corrected invoice posting (replaces je-001)"
Related entries: je-002 (reversal), je-001 (original error)
```

**Step 4: Audit Trail**
```
Audit Log Entry:
  Action: journal_entry.reversed
  Original entry: je-001
  Reversal entry: je-002
  Reason: "User 123 initiated reversal due to amount error"
  Approver: admin-456
  Timestamp: 2025-12-22
```

### Credit Notes (For Invoices)

Instead of reversing entire invoice, issue credit note:

```
Original Invoice (inv-001):
  Amount: $1,000
  Status: PAID

Guest returns goods ($200 value):
  Create Credit Note (cn-001):
    Against: inv-001
    Amount: -$200
    Reason: "Return of defective items"
    Status: PENDING

Admin approves credit note:
  Accounting posts reversing GL entry:
    Account 4100 (Revenue): -$200 debit
    Account 1200 (AR): -$200 credit

Result:
  Invoice effectively reduced from $1,000 to $800
  Refund: $200 issued to customer
  Audit trail complete
```

---

## Fraud Detection & Risk Scoring

### Principle: Detect and Escalate, Not Block

Fraud engine does NOT block transactions. It:
1. Calculates risk score
2. Triggers higher approval level
3. Alerts security team
4. Logs suspicious activity

### Risk Scoring Factors

**Factor 1: Amount Anomaly**
- Transaction significantly different from average
- Example: Average invoice $1,000, current $50,000
- Risk score: +20 points

**Factor 2: Velocity**
- Multiple transactions in short time
- Example: 10 invoices from same supplier in 1 hour
- Risk score: +15 points

**Factor 3: New Actor**
- User performing action for first time
- Example: Staff member approving large refund (never done before)
- Risk score: +10 points

**Factor 4: New Supplier**
- Transaction with supplier created < 30 days ago
- Example: PO from supplier created yesterday
- Risk score: +25 points

**Factor 5: Time Anomaly**
- Transaction outside normal business hours
- Example: Large approval at 3 AM
- Risk score: +5 points

**Factor 6: Geographic Anomaly**
- User in different location than usual
- Example: Login from new country
- Risk score: +10 points

### Risk Score & Action

```
Total Risk Score Calculation:
  sum(all_factors)

Action Taken:
  Score < 20:  Normal approval workflow
  Score 20-50: Escalate to higher level (require admin approval)
  Score 50+:   Escalate to owner + security review
  Score 80+:   Mandatory fraud check + owner approval
```

### Example: Fraud Detection in Action

```
Invoice Approval Request:
  Amount: $100,000 (normal avg: $1,000) → +20 points
  From new supplier (created 5 days ago) → +25 points
  Posted at 2 AM → +5 points
  By staff user (first time approving) → +10 points

Total Risk Score: 60 points
Action: Escalate to Owner + Security Review

Owner receives:
  - Notification: "High-risk invoice approval required"
  - Risk summary with factors
  - Supplier details
  - Link to supplier's history
  - Option to approve, reject, or investigate further

Security team receives:
  - Fraud alert in security dashboard
  - Similar pattern alerts (if any)
  - Related transactions from same supplier
```

---

## Inter-Tenant Approval

### Principle: Two-Way Explicit Approval

Cross-tenant operations require approval from BOTH sides.

### Example: Supplier Approval Chain

```
Hotel creates PO:
  1. PO created in Hotel tenant
  2. PO event published to Supplier
  3. Supplier creates Approval record
  4. Supplier admin must approve

Supplier issues Invoice:
  1. Invoice created in Supplier tenant
  2. Invoice event published to Hotel
  3. Hotel creates Approval record
  4. Hotel accounting must approve

No auto-accept or silent approval
All steps audited on both sides
```

### Contract Approval

```
Business Contract Created:
  1. Hotel invites Supplier
  2. Contract in PENDING state on Supplier side
  3. Supplier must explicitly accept
  4. Contract moves to ACTIVE state
  5. Only then can transactions proceed

No implicit acceptance
Both parties aware and on record
```

---

## Enforcement Mechanisms

### At Application Layer

```typescript
// Before executing sensitive action
function executeApproval(approval) {
  // 1. Verify approver has permission
  if (!canApprove(approval.approver, approval.resource_type)) {
    throw new Error("User does not have approval permission");
  }

  // 2. Verify all required approval levels completed
  const rules = getApprovalRules(approval.resource_type);
  for (const rule of rules) {
    const decision = approval.approvals.find(a => a.level === rule.level);
    if (!decision) {
      throw new Error(`Missing approval from level ${rule.level}`);
    }
  }

  // 3. Verify no approval override without reason
  if (approval.overridden && !approval.override_reason) {
    throw new Error("Override requires reason");
  }

  // 4. Execute business logic (post journal entry, etc)
  const result = executeBusinessLogic(approval);

  // 5. Log success
  auditLog("approval.executed", approval, result);

  return result;
}
```

### At Database Layer

```sql
-- Prevent journal entry update after posting
CREATE TRIGGER prevent_journal_update
BEFORE UPDATE ON journal_entries
FOR EACH ROW
WHEN (OLD.status = 'POSTED')
BEGIN
  RAISE EXCEPTION 'Cannot modify posted journal entry';
END;

-- Prevent audit log modification
CREATE TRIGGER prevent_audit_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
  RAISE EXCEPTION 'Audit logs are immutable';
END;
```

---

## Compliance Checklist

- [ ] RBAC model defined (roles and permissions)
- [ ] Permission check implemented for all actions
- [ ] Approval workflow engine integrated
- [ ] Approval rules configurable per tenant
- [ ] Audit logs immutable (database constraints + application logic)
- [ ] Audit logs capture: who, what, when, before/after
- [ ] Fraud detection engine integrated
- [ ] Risk score calculation working
- [ ] High-risk transactions escalated
- [ ] No direct financial data edits (reversals only)
- [ ] Credit notes implemented for invoice corrections
- [ ] Inter-tenant approvals require both parties
- [ ] Approval decisions published as events
- [ ] Audit logs tested for integrity
- [ ] Access controls tested (permission checks)
- [ ] Approval workflows tested (happy path + exceptions)

---

## Related Documents

- **SEC-01**: Security & Authentication — Identity and authentication
- **SEC-02**: Data Protection & Privacy — Data encryption and isolation
- **ARCH-08**: Security Architecture — Overall security philosophy
- **ARCH-07**: Design Patterns — Error handling and state machines
- **STD-19**: Event Model — How approval events are structured
- **REF-05**: Core Concepts — User, Tenant, Role relationships
