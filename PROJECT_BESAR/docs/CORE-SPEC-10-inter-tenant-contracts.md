# SPEC-10: Inter-Tenant Contracts - Cross-Tenant Access Control

This document specifies how tenants establish formal business relationships and grant cross-tenant access through **BusinessContract** entities. Contracts are the ONLY mechanism for data sharing between tenants in PROJECT_BESAR.

**Prerequisite**: REF-01 (Identity & Membership), SEC-03 (Authorization)

**Related**: MULTI-SPEC-11 (Inter-Tenant Supplier Flow uses contracts), REF-08 (BusinessContract entity)

---

## Core Principles (Locked)

### Principle 1: Contracts are Explicit Agreements
- No implicit cross-tenant access (default = isolated)
- Contracts created by explicit request from one tenant
- Contracts require acceptance by other tenant
- All access traced to specific contract

### Principle 2: Contracts are Revocable
- Either party can revoke contract
- Revocation is immediate (no grace period)
- Revoking party can choose data cleanup option

### Principle 3: Contracts are Audited
- All contract lifecycle events logged
- Access under contracts logged and immutable
- Audit trail retained for 7 years (compliance)

### Principle 4: Contracts Have Scope
- Each contract specifies allowed access
- Access limited to specific resources or actions
- No blanket "access to everything" contracts

### Principle 5: Service Accounts Can't Bypass Contracts
- Even system services must operate through contracts
- No hidden/system-only contracts
- All contract access visible in audit logs

---

## Contract Lifecycle

### State Machine
```
DRAFT ──[accept]--> ACTIVE ──[revoke]--> REVOKED
                      │
                      └─[reject]--> REJECTED

Terminal states: ACTIVE (for 7 years), REVOKED, REJECTED
```

---

## Contract Types

### Type 1: Supplier Contract (Hotel ↔ Supplier)
Hotel (buyer) establishes relationship with Supplier (seller)
```
BusinessContract {
  contract_type: "SUPPLIER",
  buyer_tenant_id: "hotel-001",      // Hotel
  seller_tenant_id: "supplier-456",  // Supplier/Laundry/etc.
  scope: ["PO_CREATION", "INVOICE_VIEW", "PAYMENT_RECORDING"],
  payment_terms: "NET 30",
  contract_value: 100000.00,
  start_date: "2025-12-24",
  end_date: "2026-12-23"
}
```

### Type 2: Integration Contract (App ↔ Tenant)
Integration system (app) needs access to tenant data
```
BusinessContract {
  contract_type: "INTEGRATION",
  buyer_tenant_id: "integration-system-001",  // Integration app
  seller_tenant_id: "hotel-001",               // Hotel's data
  scope: ["DATA_EXPORT", "REPORT_ACCESS"],
  api_quota: 10000,                           // Requests/month
  encryption: "REQUIRED",
  start_date: "2025-12-24",
  end_date: "2026-12-23"
}
```

### Type 3: Service Provider Contract (Hotel ↔ Service)
Hotel outsources service to separate tenant
```
BusinessContract {
  contract_type: "SERVICE_PROVIDER",
  buyer_tenant_id: "hotel-001",              // Hotel
  seller_tenant_id: "laundry-service-789",   // Laundry tenant
  scope: ["INVOICE_ISSUANCE", "DELIVERY_TRACKING"],
  sla: "2-hour turnaround",
  start_date: "2025-12-24",
  end_date: "2026-12-23"
}
```

---

## Contract Permissions

Each contract specifies granular permissions for cross-tenant access:

| Permission | Meaning | Used By |
|-----------|---------|---------|
| `PO_CREATION` | Create purchase orders | Buyer creates PO for Seller |
| `PO_ACCEPTANCE` | Accept/reject POs | Seller accepts/rejects PO |
| `INVOICE_ISSUANCE` | Issue invoices | Seller issues invoice to Buyer |
| `INVOICE_APPROVAL` | Approve invoices | Buyer approves Seller's invoice |
| `INVOICE_VIEW` | View invoices | Either party views invoices |
| `PAYMENT_RECORDING` | Record payments | Buyer records payment to Seller |
| `DELIVERY_TRACKING` | Track deliveries | Either party tracks status |
| `REPORT_ACCESS` | Access reports | Integration reads buyer data |
| `DATA_EXPORT` | Export data | Integration exports buyer data |

---

## Contract Creation Workflow

### Phase 1: Initiation (Buyer creates contract)

**Actor**: Tenant A (Buyer/Initiator)
**Permission Required**: `tenant.contract.create`

```
POST /api/v1/contracts/propose

Request:
{
  "contract_type": "SUPPLIER",
  "seller_tenant_id": "supplier-456",
  "scope": ["PO_CREATION", "INVOICE_VIEW"],
  "proposed_by": "hotel-admin-123",
  "business_justification": "Establish laundry service relationship",
  "proposed_terms": {
    "payment_terms": "NET 30",
    "contract_value": 50000.00,
    "start_date": "2025-12-24",
    "end_date": "2026-12-23"
  }
}

Response:
{
  "contract_id": "contract-999",
  "status": "DRAFT",
  "created_at": "2025-12-24T10:00:00Z",
  "created_by": "hotel-admin-123",
  "awaiting_acceptance_from": "supplier-456"
}
```

**Events**:
- `Contract.Proposed.v1` published (to both tenants)

### Phase 2: Acceptance (Seller accepts contract)

**Actor**: Tenant B (Seller/Responder)
**Permission Required**: `tenant.contract.accept`

```
POST /api/v1/contracts/{contract_id}/accept

Request:
{
  "accepted_by": "supplier-owner-456",
  "acceptance_terms": {
    "payment_terms_confirmed": "NET 30",
    "service_start_date": "2025-12-28"
  }
}

Response:
{
  "contract_id": "contract-999",
  "status": "ACTIVE",
  "activated_at": "2025-12-24T14:30:00Z",
  "accepted_by": "supplier-owner-456"
}
```

**Events**:
- `Contract.Accepted.v1` published (to both tenants)

### Phase 3: Rejection (Optional)

**Actor**: Tenant B (Seller)
**Permission Required**: `tenant.contract.reject`

```
POST /api/v1/contracts/{contract_id}/reject

Request:
{
  "rejected_by": "supplier-owner-456",
  "rejection_reason": "Cannot support NET 30 terms, need NET 15"
}

Response:
{
  "contract_id": "contract-999",
  "status": "REJECTED",
  "rejected_at": "2025-12-24T14:35:00Z"
}
```

**Events**:
- `Contract.Rejected.v1` published

**Next Steps**: Buyer can modify terms and re-propose

---

## Contract Revocation

Either party can revoke an active contract at any time.

### Revocation by Initiating Party (Buyer)

```
POST /api/v1/contracts/{contract_id}/revoke

Request:
{
  "revoked_by": "hotel-admin-123",
  "revocation_reason": "Ending supplier relationship",
  "data_cleanup": "ARCHIVE"  // or DELETE_CROSS_REFERENCES
}

Response:
{
  "contract_id": "contract-999",
  "status": "REVOKED",
  "revoked_at": "2025-12-24T15:00:00Z",
  "revoked_by_tenant": "hotel-001",
  "data_cleanup_started": true,
  "cleanup_job_id": "job-123"
}
```

**Events**:
- `Contract.Revoked.v1` published (to both tenants)

### Revocation by Responding Party (Seller)

```
POST /api/v1/contracts/{contract_id}/revoke

Request:
{
  "revoked_by": "supplier-owner-456",
  "revocation_reason": "Supplier ceasing operations",
  "data_cleanup": "KEEP"  // Seller can't delete data, just unlink
}
```

**Note**: Responder can revoke but cannot DELETE data (only KEEP/ARCHIVE)

---

## Data Cleanup on Revocation

When contract revoked, decide what to do with cross-tenant data references:

### Option 1: ARCHIVE (Default)
```
- Cross-tenant references marked as inactive
- Data preserved for audit trail (7 years)
- Can be reactivated if contract renewed
- Historical reports still visible
```

### Option 2: DELETE_CROSS_REFERENCES (Buyer only)
```
- Delete all cross-tenant foreign keys
- Keep local records (for audit)
- Remove access to shared data
- Reports show "data no longer available"
- Cannot be reactivated without data recovery
```

### Option 3: KEEP (Read-only)
```
- Maintain references but revoke write access
- Buyer can still view historical data
- No new data can be shared
- Audit trail stays intact
```

**Implementation**:
```
POST /api/v1/contracts/{contract_id}/cleanup

Request:
{
  "cleanup_option": "ARCHIVE",
  "affected_records": {
    "purchase_orders": 142,
    "invoices": 387,
    "payments": 156
  }
}

Response:
{
  "cleanup_started": true,
  "estimated_duration": "5 minutes",
  "progress_url": "/api/v1/jobs/job-123"
}
```

---

## Contract Access Control

### During Active Contract

Access allowed if:
```
✅ contract.status = ACTIVE
✅ current_date >= contract.start_date
✅ current_date <= contract.end_date
✅ requested_action IN contract.scope
✅ requester has Permission (e.g., PO_CREATION)
```

Example:
```
Buyer tries to: Create PO for Supplier
Check:
  - Contract ACTIVE? ✅
  - Includes PO_CREATION? ✅
  - User has tenant.contract.use? ✅
  - User has po.create? ✅
Result: ALLOWED
```

### After Contract Revoked

```
✅ Can read historical data (audit trail)
❌ Cannot create new cross-tenant references
❌ Cannot modify shared data
❌ Cannot view new data from other tenant
```

---

## Contract Audit Trail

Every contract action logged immutably:

```
ContractAuditLog {
  id: UUID,
  contract_id: UUID,
  action: enum,                // PROPOSED, ACCEPTED, REJECTED, REVOKED, ACCESSED
  actor_tenant_id: UUID,       // Which tenant made action
  actor_user_id: UUID,         // Which user
  action_at: timestamp,

  // For access actions
  accessed_resource: string,   // e.g., "Invoice #INV-001"
  accessed_action: string,     // e.g., "VIEW", "APPROVE"

  // For lifecycle actions
  contract_state_before: enum,
  contract_state_after: enum,
  reason: text,

  is_immutable: true
}
```

**Query Example**: "Show all invoices accessed under contract-999"
```sql
SELECT * FROM contract_audit_log
WHERE contract_id = 'contract-999'
  AND accessed_resource LIKE 'Invoice%'
  AND accessed_action = 'VIEW'
ORDER BY action_at DESC;
```

---

## Contract Templates

Tenants can customize contract templates per tenant:

```
ContractTemplate {
  id: UUID,
  tenant_id: UUID,
  name: string,                // "Standard Supplier Contract"
  contract_type: enum,        // SUPPLIER, SERVICE_PROVIDER, etc.
  default_scope: [string],    // Default permissions
  default_terms: {
    payment_terms: "NET 30",
    duration_months: 12
  },
  created_at: timestamp
}
```

**Usage**:
```
POST /api/v1/contracts/propose

Request:
{
  "template_id": "template-supplier-001",  // Use template
  "seller_tenant_id": "supplier-789",
  "override_terms": {
    "payment_terms": "NET 15"  // Override template default
  }
}
```

---

## Integration Points

### How Supplier Flow Uses Contracts

```
1. Hotel Admin creates contract for Supplier
   → Contract.Proposed.v1 event

2. Supplier Owner accepts contract
   → Contract.Accepted.v1 event
   → Contract becomes ACTIVE

3. Hotel procurement staff tries to create PO for Supplier
   → System checks: Is contract ACTIVE?
   → System checks: Does contract include PO_CREATION permission?
   → ✅ Allowed (PO created)

4. PO event published: Procurement.PurchaseOrder.Issued.v1
   → Supplier receives notification
   → Supplier logs into system (via contract)

5. Supplier reviews PO (via contract access)
   → System verifies: Can supplier access this PO?
   → Checks: Is contract ACTIVE? Does supplier have access?
   → ✅ Allowed (Supplier views PO)

6. Supplier approves PO
   → System verifies: Can supplier approve?
   → Checks: Does contract include PO_ACCEPTANCE?
   → ✅ Allowed

7. Later: Hotel revokes contract
   → Contract.Revoked.v1 event
   → Supplier: Can no longer view new POs
   → But: Can still see old POs (archived)
```

---

## Implementation Checklist

- [ ] BusinessContract CRUD operations
- [ ] Contract state machine (DRAFT → ACTIVE → REVOKED)
- [ ] Contract permissions enforcement
- [ ] Contract proposal workflow (with notifications)
- [ ] Contract acceptance/rejection
- [ ] Contract revocation (with data cleanup options)
- [ ] Access control integration (check contract before cross-tenant access)
- [ ] Audit trail logging (all contract actions immutable)
- [ ] Contract templates
- [ ] API endpoints:
  - POST /contracts/propose
  - POST /contracts/{id}/accept
  - POST /contracts/{id}/reject
  - POST /contracts/{id}/revoke
  - GET /contracts/{id}
  - GET /contracts (list active/historical)
- [ ] Notifications (email when contract proposed/accepted/revoked)
- [ ] Dashboard: active contracts, pending acceptance
- [ ] Admin: manage contract templates
