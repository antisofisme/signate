# SPEC-11: Inter-Tenant Supplier Flow

This document specifies the **cross-tenant business process** for supplier relationships in ATLAS_PANDAWA. It defines how a Buyer Tenant (e.g., Hotel) and Seller Tenant (e.g., Supplier) interact through the platform without sharing databases.

**Key Concept**: Two completely isolated Tenants interact through events and API calls, maintaining separate accounting records and complete data isolation.

---

## Core Principles (Locked)

### Principle 1: Tenants are Completely Separate
- Hotel Tenant and Supplier Tenant have separate databases
- No shared tables or schemas
- Complete data isolation (no cross-tenant queries)
- Separate audit trails

### Principle 2: Integration via Events & Contracts
- No direct database access between tenants
- Communication through:
  - Events (PO issued, invoice created, payment made)
  - Synchronous API calls (with explicit permission)
  - Business contracts (formal agreements)

### Principle 3: Both Tenants Must Have Accounting
- Hotel needs Accounting (to track AP - Accounts Payable)
- Supplier needs Accounting (to track AR - Accounts Receivable)
- Financial integrity: two separate ledgers, no shared journal

### Principle 4: Inventory is Optional (For Goods Suppliers Only)
- Service suppliers (laundry, cleaning): no inventory tracking
- Goods suppliers (FMCG, warehouse): inventory tracking enabled
- Inventory state managed in supplier's Tenant only

### Principle 5: Business Contract Governs Relationship
- Formal contract between Hotel and Supplier
- Specifies: pricing, payment terms, service levels
- Contract ID links all transactions
- Enables audit trail of relationship

---

## Supplier Types

### Type A: Service Supplier
**Examples**: Laundry, Cleaning, Maintenance, Spa Partner, Consulting

**Characteristics**:
- No physical goods inventory
- Service performed on-demand or scheduled
- No stock reduction (no Inventory module needed)
- Invoice generated after service completion

**Modules Required**:
- Supplier App (to accept POs, track service)
- Accounting (to issue invoices and track AR)
- ❌ Inventory (not needed)

**Data Model**:
```
PurchaseOrder → ServiceScheduled → ServiceCompleted → Invoice → Payment
```

---

### Type B: Goods Supplier
**Examples**: FMCG supplier, warehouse, food supplier, maintenance materials

**Characteristics**:
- Physical goods with inventory
- Stock managed in supplier's system
- Goods shipped to buyer
- Invoice generated after delivery and receipt

**Modules Required**:
- Supplier App (to manage inventory and accept POs)
- Accounting (to issue invoices and track AR)
- ✅ Inventory (to track stock, deductions, receipts)

**Data Model**:
```
PurchaseOrder → InventoryReserved → GoodsPicked → ShippingNotice →
GoodsReceived → Invoice → Payment
```

---

## Main Flow: Supplier Invitation to Payment

### Phase 1: Supplier Invitation & Business Contract

**Trigger**: Hotel wants to establish relationship with Supplier

**Steps**:

#### 1.1: Hotel Invites Supplier
1. Hotel admin navigates to "Add Supplier"
2. Enters Supplier details (name, email, contact)
3. Sends invitation to Supplier

**Event Published** (Hotel Tenant):
```json
{
  "event_type": "Supplier.Invited.v1",
  "event_version": "v1",
  "event_id": "evt-supplier-invited-001",
  "correlation_id": "supplier-123",
  "tenant_id": "hotel-123",
  "signature": "a7f3e1b9d8c4f2e6a9b3d7f1c5e8a2b6d9f3e7a1b5c9d3e7f1a5b9c3d7e1f5",
  "data": {
    "supplier_email": "supplier@company.com",
    "supplier_name": "ABC Laundry",
    "invitation_token": "token-xyz"
  }
}
```

#### 1.2: Supplier Accepts Invitation
1. Supplier receives email with acceptance link
2. Supplier clicks link (creates account or logs in)
3. Supplier accepts invitation

**Event Published** (Supplier Tenant created):
```json
{
  "event_type": "Supplier.InvitationAccepted.v1",
  "event_version": "v1",
  "event_id": "evt-invitation-accepted-001",
  "correlation_id": "supplier-123",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "signature": "f2e7d1b9a5c8e3f6d2a7b1c9e4f8a3b6c1d5e9f2a7b3c6d1e5f8a2b6c9d3e",
  "data": {
    "supplier_name": "ABC Laundry",
    "from_tenant_id": "hotel-123",
    "contract_id": "contract-999"
  }
}
```

#### 1.3: Business Contract Created
1. Platform creates Business Contract record
2. Links Hotel Tenant ↔ Supplier Tenant
3. Records contract terms (optional: pricing, payment terms)

**Contract Record**:
```
BusinessContract {
  id: "contract-999",
  buyer_tenant_id: "hotel-123",     // Hotel
  seller_tenant_id: "supplier-456", // Supplier
  status: "ACTIVE",
  contract_date: "2025-12-21",
  payment_terms: "NET 30",
  created_at: timestamp
}
```

#### 1.4: Supplier Sets Up (Initial Configuration)
1. Supplier configures:
   - Bank account for payments
   - Delivery address (if goods)
   - Service areas (if services)
   - Pricing (per service or per item)
2. Supplier marks as "Ready to Accept Orders"

**Output**: Business relationship active, both tenants aware

---

### Phase 2: Purchase Order (PO) Creation & Acceptance

**Trigger**: Hotel needs service or goods from Supplier

**Steps**:

#### 2.1: Hotel Creates PO
1. Hotel procurement staff creates PO:
   - Supplier: ABC Laundry
   - Items/Services: Laundry services (qty, rate)
   - Delivery date: Tomorrow
   - Total amount: $500

**PO Record** (Hotel Tenant):
```
PurchaseOrder {
  id: "po-12345",
  tenant_id: "hotel-123",
  contract_id: "contract-999",
  supplier_tenant_id: "supplier-456",
  status: "DRAFT" | "ISSUED" | "ACCEPTED" | "REJECTED" | "COMPLETED",

  line_items: [
    {
      description: "Laundry service - 50 kg",
      quantity: 50,
      unit: "kg",
      unit_price: 10,
      total: 500
    }
  ],

  total_amount: 500,
  delivery_date: "2025-12-22",

  // Rejection fields (only populated if status = REJECTED)
  rejection_reason: string | null,      // Why supplier rejected (e.g., "Capacity exceeded for this date")
  rejected_by: UUID | null,             // Supplier user who rejected
  rejected_at: timestamp | null,        // When rejection occurred

  created_by: "procurement-staff-123",
  created_at: timestamp
}
```

#### 2.2: Hotel Sends PO to Supplier
1. Hotel publishes event: "PO Issued"
2. Event sent to Supplier Tenant (via contract)

**Event Published**:
```json
{
  "event_type": "Procurement.PurchaseOrder.Issued.v1",
  "event_version": "v1",
  "event_id": "evt-po-issued-123",
  "correlation_id": "po-12345",
  "tenant_id": "hotel-123",
  "from_tenant_id": "hotel-123",
  "to_tenant_id": "supplier-456",
  "contract_id": "contract-999",
  "signature": "c9d3e7f1a5b2c6d1e8f2a9b3c7d1e5f9a2b6c3d7e1f5a9b3c7d1e5f9a2b6c",

  "payload": {
    "po_id": "po-12345",
    "supplier_tenant_id": "supplier-456",
    "items": [
      {
        "description": "Laundry service - 50 kg",
        "quantity": 50,
        "unit_price": 10,
        "total": 500
      }
    ],
    "total_amount": 500,
    "delivery_date": "2025-12-22"
  }
}
```

#### 2.3: Supplier Receives & Reviews PO
1. Supplier receives event
2. Supplier staff reviews PO in their system
3. Supplier checks capacity/availability

**Decision Gateway**: Can Supplier fulfill?

**Path A: Supplier Accepts**
1. Supplier clicks "Accept PO"
2. System creates PO copy in Supplier Tenant (for their records)

**Event Published**:
```json
{
  "event_type": "Procurement.PurchaseOrder.Accepted.v1",
  "event_version": "v1",
  "event_id": "evt-po-accepted-456",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "d1e5f9a2b6c3d7e1f5a9b3c7d1e5f9a2b6c3d7e1f5a9b3c7d1e5f9a2b6c3d",

  "payload": {
    "po_id": "po-12345",
    "status": "ACCEPTED",
    "expected_completion_date": "2025-12-22"
  }
}
```

**Path B: Supplier Rejects**
1. Supplier clicks "Reject PO" (with optional reason)

**Event Published**:
```json
{
  "event_type": "Procurement.PurchaseOrder.Rejected.v1",
  "event_version": "v1",
  "event_id": "evt-po-rejected-789",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "e2f6a3b7c1d5e8f2a6b3c7d1e5f8a2b6c3d7e1f5a9b2c6d1e5f8a2b6c3d7",
  "payload": {
    "po_id": "po-12345",
    "reason": "Capacity exceeded for this date"
  }
}
```

---

### Phase 3: Fulfillment

This phase differs based on supplier type.

#### 3A: Service Supplier Fulfillment (Laundry Example)

**Steps**:
1. Supplier schedules laundry pickup/delivery
2. Hotel provides dirty laundry
3. Supplier processes laundry
4. Supplier delivers clean laundry

**Event Published** (completion):
```json
{
  "event_type": "Supplier.Service.Completed.v1",
  "event_version": "v1",
  "event_id": "evt-service-completed-789",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "f3a7b1c5d9e2f6a3b7c1d5e8f2a6b3c7d1e5f9a2b6c3d7e1f5a9b3c7d1e5",

  "payload": {
    "po_id": "po-12345",
    "service_type": "laundry",
    "completion_date": "2025-12-22",
    "quantity_processed": 50,
    "status": "COMPLETED"
  }
}
```

#### 3B: Goods Supplier Fulfillment (Warehouse Example)

**Steps**:
1. Supplier reserves inventory (in their Inventory module)
2. Supplier picks goods from warehouse
3. Supplier packs and ships goods
4. Hotel receives goods and verifies

**Events Published**:

**Event 1**: Goods Shipped
```json
{
  "event_type": "Procurement.Goods.Shipped.v1",
  "event_version": "v1",
  "event_id": "evt-goods-shipped-001",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "a4b8c2d6e9f3a7b1c5d8e2f6a3b7c1d5e8f2a6b3c7d1e5f8a2b6c3d7e1f5a",
  "payload": {
    "po_id": "po-12345",
    "tracking_number": "TRACK-12345",
    "shipped_date": "2025-12-21"
  }
}
```

**Event 2**: Goods Received (Hotel confirms receipt)
```json
{
  "event_type": "Procurement.Goods.Received.v1",
  "event_version": "v1",
  "event_id": "evt-goods-received-001",
  "correlation_id": "po-12345",
  "tenant_id": "hotel-123",
  "from_tenant_id": "hotel-123",
  "to_tenant_id": "supplier-456",
  "contract_id": "contract-999",
  "signature": "b5c9d3e7f1a4b8c2d6e9f3a7b1c5d8e2f6a3b7c1d5e8f2a6b3c7d1e5f8a2b",
  "payload": {
    "po_id": "po-12345",
    "received_date": "2025-12-22",
    "quantity_received": 50,
    "quantity_damaged": 0,
    "status": "RECEIVED"
  }
}
```

---

### Phase 4: Invoice Issuance (Inter-Tenant Invoice)

**Trigger**: Service completed OR goods received

**Steps**:

#### 4.1: Supplier Creates Invoice
1. Supplier system creates invoice based on:
   - PO details (quantity, unit price)
   - Actual fulfillment (service completed, goods received)
   - Contract terms (payment terms, taxes)

**Invoice Record** (Supplier Tenant):
```
Invoice {
  id: "inv-001",
  tenant_id: "supplier-456",
  po_id: "po-12345",
  contract_id: "contract-999",
  buyer_tenant_id: "hotel-123",

  line_items: [
    {
      description: "Laundry service - 50 kg",
      quantity: 50,
      unit_price: 10,
      total: 500
    }
  ],

  subtotal: 500,
  tax: 50,  // Assume 10% tax
  total: 550,

  invoice_date: "2025-12-22",
  due_date: "2026-01-21",  // NET 30 per contract
  status: "ISSUED",

  accounting: {
    account_code: "4100",  // Service Revenue
    ar_account_code: "1200"  // Accounts Receivable
  }
}
```

**HIGH GUARDRAIL - Invoice-PO Matching (3-Way Match)**:
```
RULE: Invoice must match PO and GoodsReceipt (or ServiceCompletion) before posting
RULE: Discrepancies > 1% must be reviewed and approved before posting AP
```
**Matching Process**:
- PO Validation: Invoice.po_id must reference existing, ACCEPTED PO
- Quantity Match: Invoice quantity ≤ PO quantity (for partial invoices)
- Amount Match: Invoice total must match PO amount (within 1% tolerance)
- If Invoice > PO amount by > 1%:
  - Create PO-Invoice mismatch alert
  - Set AP status = PENDING_MATCH
  - Require manual review + approval before payment
- GoodsReceipt Match (for goods):
  - Invoice quantity ≤ GoodsReceipt quantity received
  - Prevents invoicing for undelivered goods
- ServiceCompletion Match (for services):
  - Invoice issued AFTER service marked COMPLETED
  - Prevents premature invoicing
- Once matched: AP status = APPROVED, ready for payment

**CRITICAL GUARDRAIL - AP Payment Authorization (Contradiction #5 Resolution)**:
```
RULE: AP can ONLY be paid if status = APPROVED
RULE: PENDING_MATCH is a pre-approval state that BLOCKS payment
RULE: Payment cannot proceed until matching discrepancies resolved
```

**Payment Authorization Matrix**:

| AP Amount | Approval Authority | Escalation SLA |
|-----------|-------------------|----------------|
| $0 - $1,000 | Procurement Manager | Auto-approve if exact match |
| $1,000 - $5,000 | Procurement Manager | 1 business day |
| $5,001 - $25,000 | Finance Manager | 2 business days |
| $25,001+ | Finance Director | 3 business days |

**Approval Workflow**:
1. If AP status = PENDING_MATCH AND amount > $1K:
   - Create approval request
   - Assign to appropriate authority based on amount
   - Block payment until approval received
   - SLA timer starts (if not approved within SLA, auto-escalate)

2. If PENDING_MATCH > 7 days without approval:
   - Auto-escalate to Finance Director
   - Send notification: "AP inv-XXX pending match > 7 days, requires immediate attention"
   - Flag in aging report as "STUCK IN MATCHING"

3. Approval Decision Outcomes:
   - APPROVED → AP status = APPROVED, payment can proceed
   - REJECTED → AP status = REJECTED, supplier notified, PO cancelled or amended
   - PARTIAL_APPROVED → Amount adjusted, AP updated, payment proceeds with new amount

4. Timeout Policy:
   - If no decision after 14 days: Auto-reject with reason "Approval timeout"
   - Supplier notified of rejection
   - Procurement can resubmit with corrected invoice

**Implementation Pseudocode**:
```typescript
async function payInvoice(apId: string) {
  const ap = await getAccountsPayable(apId);

  // CRITICAL CHECK: Block payment if not APPROVED
  if (ap.status !== 'APPROVED') {
    throw new PaymentBlockedError(
      `Cannot pay AP ${apId}. Status = ${ap.status}. ` +
      `Payment only allowed when status = APPROVED. ` +
      `Current status indicates: ${getStatusExplanation(ap.status)}`
    );
  }

  // Check approval authority
  const approvalRequired = getRequiredApproval(ap.total_amount);
  if (!ap.approved_by || !hasAuthority(ap.approved_by, approvalRequired)) {
    throw new InsufficientApprovalError(
      `AP ${apId} requires ${approvalRequired} approval. ` +
      `Current approval: ${ap.approved_by || 'NONE'}`
    );
  }

  // Proceed with payment
  const payment = await processPayment(ap);
  return payment;
}

function getStatusExplanation(status: string): string {
  const explanations = {
    'PENDING_MATCH': 'Invoice-PO discrepancy requires manual review',
    'REJECTED': 'Invoice rejected, cannot pay',
    'DRAFT': 'Invoice not yet posted to GL',
  };
  return explanations[status] || 'Unknown status';
}
```

**Audit Trail Requirements**:
- All approval decisions logged with: approver_id, timestamp, decision, reason
- Payment attempts logged (successful and blocked)
- Escalations logged with SLA breach notification
- Aging report shows: days_in_pending_match, escalation_count, assigned_approver

#### 4.2: Supplier Publishes Inter-Tenant Invoice Event
```json
{
  "event_type": "Accounting.Invoice.Issued.v1",
  "event_version": "v1",
  "event_id": "evt-invoice-issued-001",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "c6d1e5f8a2b6c3d7e1f5a9b2c6d1e5f8a2b6c3d7e1f5a9b2c6d1e5f8a2b6c3",

  "payload": {
    "invoice_id": "inv-001",
    "po_id": "po-12345",
    "buyer_tenant_id": "hotel-123",
    "seller_name": "ABC Laundry",
    "invoice_date": "2025-12-22",
    "due_date": "2026-01-21",
    "line_items": [
      {
        "description": "Laundry service - 50 kg",
        "quantity": 50,
        "unit_price": 10,
        "total": 500
      }
    ],
    "subtotal": 500,
    "tax": 50,
    "total": 550
  }
}
```

#### 4.3: Hotel Receives Invoice (Creates AP)
1. Hotel Accounting service consumes event
2. Creates **Accounts Payable** (AP) record

**AP Record** (Hotel Tenant):
```
AccountsPayable {
  id: "ap-001",
  tenant_id: "hotel-123",
  invoice_id: "inv-001",
  supplier_tenant_id: "supplier-456",
  contract_id: "contract-999",

  invoice_details: [
    {
      description: "Laundry service",
      amount: 500
    }
  ],

  subtotal: 500,
  tax: 50,
  total_due: 550,

  invoice_date: "2025-12-22",
  due_date: "2026-01-21",
  status: "RECEIVED",  // Not yet approved

  accounting: {
    expense_account: "6100",  // Service Expense
    ap_account: "2200"  // Accounts Payable
  }
}
```

**Supplier Accounting**:
- Supplier records AR (Accounts Receivable) for $550
- Account 1200: AR increase
- Account 4100: Service Revenue

**Hotel Accounting**:
- Hotel records AP (Accounts Payable) for $550
- Account 2200: AP increase
- Account 6100: Service Expense (or 4100 if cost of goods)

---

### Phase 5: Invoice Approval & Journal Posting

**Trigger**: Hotel receives invoice and reviews

**Steps**:

#### 5.1: Hotel Reviews & Approves Invoice
1. Accounting staff reviews invoice in AP
2. Verifies:
   - Amount matches PO
   - Service/goods actually received
   - Invoice date and terms correct
3. Clicks "Approve"

**Event Published**:
```json
{
  "event_type": "Accounting.Invoice.Approved.v1",
  "event_version": "v1",
  "event_id": "evt-invoice-approved-001",
  "correlation_id": "po-12345",
  "tenant_id": "hotel-123",
  "from_tenant_id": "hotel-123",
  "to_tenant_id": "supplier-456",
  "contract_id": "contract-999",
  "signature": "d7e2f6a3b7c1d5e8f2a6b3c7d1e5f8a2b6c3d7e1f5a9b2c6d1e5f8a2b6c3d",
  "payload": {
    "invoice_id": "inv-001",
    "approved_by": "accounting-staff-123",
    "approved_at": "2025-12-23"
  }
}
```

#### 5.2: Hotel Accounting Posts Journal Entry

**Supplier's Perspective** (Supplier Tenant):
```
Journal Entry {
  entry_id: "je-supplier-001",
  description: "Service revenue recognized",

  lines: [
    {
      account: "1200",  // AR
      debit: 550,
      credit: 0
    },
    {
      account: "4100",  // Service Revenue
      debit: 0,
      credit: 500
    },
    {
      account: "2300",  // Tax Payable
      debit: 0,
      credit: 50
    }
  ]
}
```

**Hotel's Perspective** (Hotel Tenant):
```
Journal Entry {
  entry_id: "je-hotel-001",
  description: "Service expense - laundry",

  lines: [
    {
      account: "6100",  // Service Expense
      debit: 500,
      credit: 0
    },
    {
      account: "2300",  // Tax Payable
      debit: 50,
      credit: 0
    },
    {
      account: "2200",  // AP
      debit: 0,
      credit: 550
    }
  ]
}
```

**Key**: Two completely separate journal entries in two separate ledgers. No shared GL accounts.

---

### Phase 6: Payment Settlement

**Trigger**: Invoice approved and due date approaching

**Steps**:

#### 6.1: Hotel Pays Invoice
1. Hotel accounting initiates payment
2. Payment method: bank transfer, credit card, etc.
3. Sends payment to Supplier

**Payment Record** (Hotel Tenant):
```
Payment {
  id: "pay-001",
  tenant_id: "hotel-123",
  ap_id: "ap-001",
  invoice_id: "inv-001",

  amount: 550,
  payment_method: "BANK_TRANSFER",
  reference: "bank-txn-12345",
  payment_date: "2025-12-30",
  status: "COMPLETED"
}
```

#### 6.2: Hotel Posts Payment Journal Entry
```
Journal Entry {
  entry_id: "je-hotel-002",
  description: "Payment to ABC Laundry",

  lines: [
    {
      account: "2200",  // AP
      debit: 550,
      credit: 0
    },
    {
      account: "1000",  // Cash / Bank
      debit: 0,
      credit: 550
    }
  ]
}
```

Result: AP is now $0 (closed)

#### 6.3: Payment Notification to Supplier
1. Hotel publishes payment event

**Event Published**:
```json
{
  "event_type": "Accounting.Payment.Received.v1",
  "event_version": "v1",
  "event_id": "evt-payment-received-001",
  "correlation_id": "po-12345",
  "tenant_id": "hotel-123",
  "from_tenant_id": "hotel-123",
  "to_tenant_id": "supplier-456",
  "contract_id": "contract-999",
  "signature": "e8f3a7b1c5d8e2f6a3b7c1d5e8f2a6b3c7d1e5f8a2b6c3d7e1f5a9b2c6d1",

  "payload": {
    "invoice_id": "inv-001",
    "amount_paid": 550,
    "payment_date": "2025-12-30",
    "payment_reference": "bank-txn-12345"
  }
}
```

#### 6.4: Supplier Posts Payment Journal Entry
```
Journal Entry {
  entry_id: "je-supplier-002",
  description: "Payment received from Hotel",

  lines: [
    {
      account: "1000",  // Cash / Bank
      debit: 550,
      credit: 0
    },
    {
      account: "1200",  // AR
      debit: 0,
      credit: 550
    }
  ]
}
```

Result: AR is now $0 (settled)

---

## Status Lifecycle & Cross-Tenant Synchronization

### PurchaseOrder Status Lifecycle

**Status Machine**:
```
DRAFT ──[send]--> ISSUED ──[supplier_accepts]──> ACCEPTED ──[fulfill]--> COMPLETED
  │                  │
  │                  └──[supplier_rejects]──> REJECTED
  │
  └──[cancel]──> CANCELLED
```

**Status Meanings**:

| Status | Owned By | Meaning | Actions Allowed |
|--------|----------|---------|-----------------|
| DRAFT | Buyer | PO created, not sent yet | Edit, send, cancel |
| ISSUED | Buyer | PO sent to supplier, awaiting response | Track supplier response, retract, cancel |
| ACCEPTED | Supplier | Supplier accepted the PO | Proceed with fulfillment |
| REJECTED | Supplier | Supplier rejected the PO | View rejection reason, re-send modified PO |
| COMPLETED | Buyer | Fulfillment complete, invoiced | View history, reference for future |
| CANCELLED | Buyer | Buyer cancelled PO | View history (cannot reactivate) |

### HIGH GUARDRAIL - PO Modification Rules

**Modification Allowed**:
- DRAFT: Full modification allowed (amount, items, delivery date)
- ISSUED: Buyer can retract, Supplier has NOT accepted yet
- REJECTED: Buyer can create new PO with modifications

**Modification NOT Allowed**:
- ACCEPTED: No modifications (supplier committed to PO)
- COMPLETED: Read-only (historical record)
- CANCELLED: Cannot reactivate (create new PO instead)

**Amount Changes**:
- If line items changed: Must increase tolerance by ≤ 10%
- If increase > 10%: Requires re-negotiation (cancel + new PO)
- Any amount change AFTER supplier accepted: New negotiation required

**Implementation**:
- Check PO.status before allowing modification
- Log all modifications with reason and approval chain
- If ACCEPTED and modification attempted: Block with message "Cannot modify accepted PO"
- Prevents invoice-PO mismatch disputes

### Cross-Tenant Status Synchronization

**Problem**: Hotel's PO status and Supplier's copy may diverge due to:
- Event delivery delays
- Network timeouts
- Both tenants updating independently

**Solution**: Event-Driven Sync with Optimistic Lock

**Hotel's View**:
```
PurchaseOrder {
  id: "po-12345",
  status: "ISSUED",
  supplier_status: "ISSUED",     // What we know supplier thinks
  supplier_status_as_of: timestamp,  // When we last confirmed
  version: 1                      // Optimistic lock version
}
```

**Supplier's View**:
```
PurchaseOrder {
  id: "po-12345",
  status: "ACCEPTED",             // What supplier actually did
  buyer_status: "ISSUED",         // What we know hotel thinks
  buyer_status_as_of: timestamp,
  version: 1
}
```

**Synchronization Flow**:

```
1. Hotel creates PO (status=DRAFT)
   → Hotel: status=DRAFT
   → Supplier: (doesn't exist yet)

2. Hotel sends PO (status=ISSUED)
   → Publishes: Procurement.PurchaseOrder.Issued.v1
   → Hotel: status=ISSUED, supplier_status=UNKNOWN
   → Supplier: receives event, creates local copy

3. Supplier receives event (async processing)
   → Creates PurchaseOrder (status=ISSUED)
   → Supplier: status=ISSUED, buyer_status=ISSUED
   → Publishes: Procurement.PurchaseOrder.Received.v1
   → Hotel: receives "supplier received our PO"
   → Hotel: Updates supplier_status=ISSUED

4. Supplier accepts (status=ACCEPTED)
   → Publishes: Procurement.PurchaseOrder.Accepted.v1
   → Supplier: status=ACCEPTED, buyer_status=ISSUED (old, will sync)
   → Hotel: receives event, updates supplier_status=ACCEPTED
   → Hotel: status=ISSUED → ACCEPTED (matches supplier)

5. If conflict (both updating):
   → Use optimistic lock (version number)
   → Last-write-wins with audit trail
   → Log conflict resolution
```

**Reconciliation Query** (Detect Mismatches):
```sql
-- Find POs where Hotel and Supplier status disagree
SELECT
  h.po_id,
  h.status as hotel_status,
  h.supplier_status as hotel_knows_supplier_status,
  CASE WHEN h.supplier_status != h.actual_supplier_status THEN 'MISMATCH' ELSE 'OK' END as sync_status
FROM (
  -- Hotel's view
  SELECT po_id, status, supplier_status, supplier_status_as_of
  FROM purchase_orders
  WHERE tenant_id = 'hotel-123'
) h
LEFT JOIN (
  -- Supplier's actual status (pulled via API or event)
  SELECT po_id, status as actual_supplier_status
  FROM purchase_orders
  WHERE tenant_id = 'supplier-456'
) s ON h.po_id = s.po_id
WHERE h.supplier_status != s.actual_supplier_status;
```

### Status Sync Rules (LOCKED)

**Rule 1: Status Changes via Events Only**
- ❌ DO NOT poll supplier system to check status
- ✅ DO listen to status-change events
- ✅ DO accept events as source of truth for status

**Rule 2: Idempotency**
- Status change event received twice → No change (idempotent)
- Retries don't cause duplicate status updates

**Rule 3: Order Guarantee**
- Events must be processed in order per PO
- Queue events by PO ID to maintain order
- Use sequence_number field to detect out-of-order

**CRITICAL GUARDRAIL - Event Order vs Idempotency (Contradiction #8 Resolution)**:
```
RULE: Use sequence_number to guarantee order, even if duplicates arrive out-of-order
RULE: Idempotency prevents duplicate processing; Order guarantee prevents state corruption
RULE: These are COMPLEMENTARY, not conflicting mechanisms
```

**Order Guarantee + Idempotency Implementation**:

When event arrives at receiver tenant:

```typescript
async function processInterTenantEvent(event: InterTenantEvent) {
  const { po_id, sequence_number, event_id } = event;

  // Step 1: Idempotency check (prevent duplicate processing)
  const alreadyProcessed = await checkEventIdProcessed(event_id);
  if (alreadyProcessed) {
    logger.info(`Event ${event_id} already processed, skipping`);
    return; // Idempotent: No side effects from duplicate
  }

  // Step 2: Sequence number ordering check
  const expectedSeq = await getNextExpectedSequence(po_id);

  if (sequence_number > expectedSeq) {
    // Future event arrived before earlier events
    logger.warn(
      `Out-of-order event: PO ${po_id}, ` +
      `expected seq ${expectedSeq}, got ${sequence_number}. Queueing.`
    );
    await queueOutOfOrderEvent(po_id, sequence_number, event);
    return; // Don't process yet, wait for earlier events
  }

  if (sequence_number < expectedSeq) {
    // Late-arriving duplicate (already processed by sequence)
    logger.warn(
      `Late event: PO ${po_id}, ` +
      `expected seq ${expectedSeq}, got ${sequence_number}. Ignoring.`
    );
    await markEventProcessed(event_id); // Mark as seen for idempotency
    return;
  }

  // Step 3: Process event (sequence matches expected)
  await processEvent(event);
  await markEventProcessed(event_id);
  await incrementExpectedSequence(po_id);

  // Step 4: Check if any queued out-of-order events can now be processed
  await processQueuedEvents(po_id, expectedSeq + 1);
}

async function processQueuedEvents(po_id: string, nextSeq: number) {
  const queuedEvent = await getQueuedEvent(po_id, nextSeq);

  if (queuedEvent) {
    logger.info(`Processing queued event seq ${nextSeq} for PO ${po_id}`);
    await processInterTenantEvent(queuedEvent); // Recursive processing
  }
}
```

**Example Scenario - Events Arrive Out of Order**:

Timeline:
1. Supplier publishes events in order:
   - Event A (seq=1): PO.Issued
   - Event B (seq=2): PO.Accepted
   - Event C (seq=3): Invoice.Issued

2. Network delay causes events to arrive at Hotel in this order:
   - Event C arrives first (seq=3)
   - Event A arrives second (seq=1)
   - Event B arrives third (seq=2)

Processing:
```
Hotel receives Event C (seq=3):
  - Expected seq = 1
  - seq 3 > 1 → Queue Event C, don't process yet
  - Event stored in out_of_order_queue

Hotel receives Event A (seq=1):
  - Expected seq = 1
  - seq 1 = 1 → Process Event A immediately
  - Increment expected to 2
  - Check queue: Event B (seq=2) not yet arrived, wait

Hotel receives Event B (seq=2):
  - Expected seq = 2
  - seq 2 = 2 → Process Event B immediately
  - Increment expected to 3
  - Check queue: Event C (seq=3) found!
  - Process Event C from queue
  - All events processed in correct order: A → B → C
```

**Database Schema Addition**:

```sql
CREATE TABLE inter_tenant_event_sequence (
  po_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  next_expected_sequence INT NOT NULL DEFAULT 1,
  last_processed_at TIMESTAMP,

  PRIMARY KEY (po_id, tenant_id)
);

CREATE TABLE inter_tenant_event_queue (
  id UUID PRIMARY KEY,
  po_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  sequence_number INT NOT NULL,
  event_payload JSONB NOT NULL,
  queued_at TIMESTAMP DEFAULT NOW(),

  UNIQUE (po_id, tenant_id, sequence_number)
);

CREATE TABLE processed_event_ids (
  event_id VARCHAR(255) PRIMARY KEY,
  po_id UUID,
  processed_at TIMESTAMP DEFAULT NOW(),

  INDEX idx_processed_event_po (po_id, processed_at)
);
```

**Audit Trail**:
- All out-of-order events logged with: event_id, expected_seq, actual_seq, queued_at
- Sequence gaps detected and alerted (missing event detection)
- Processing order verified in logs

**Rule 4: Conflict Resolution**
- If both parties update simultaneously → Last write wins (by timestamp)
- But: Sequence number determines "latest"
- Conflict logged in audit trail

---

## Alternative Flows

### Flow A: Partial Delivery / Partial Invoice

**Scenario**: Supplier delivers part of order, invoices for partial amount

**Steps**:
1. Supplier ships only 30 kg (instead of 50 kg)
2. Supplier creates partial invoice for $300 (30 × $10)
3. Hotel receives partial invoice
4. AP recorded for $300
5. Remaining $200 PO remains open
6. Supplier delivers remaining 20 kg later
7. Supplier creates second invoice for $200

**Implementation**: Multiple invoices, multiple APs, same PO

**MEDIUM GUARDRAIL - Partial Invoice Tracking**:
- PO tracks: total_qty_ordered, total_qty_invoiced, total_qty_received
- Invoice must reference: po_id, percentage_of_po (if partial)
- If invoice < 100% of PO:
  - Flag as "partial" in AP system
  - Remaining balance tracked separately
  - Cannot mark PO COMPLETED until all invoices received
- Prevent duplicate invoicing: System checks cumulative qty invoiced ≤ qty ordered
- Reports available: Outstanding partial deliveries by supplier
- Prevents: Over-invoicing, lost partial shipments

**CLARIFICATION - Partial Invoice Definition (Ambiguity #5 Resolution)**:
```
RULE: "Partial" is based on BOTH quantity AND amount
RULE: Supplier can invoice partial quantity OR partial amount OR both
RULE: System tracks BOTH dimensions independently
```

**Partial Invoice Scenarios**:

**Scenario 1: Partial Quantity (Full Rate)**
- PO: 100 units @ $10/unit = $1,000
- Supplier ships 50 units only
- Supplier invoices: 50 units @ $10/unit = $500
- **Result**: Partial quantity (50%), full rate, partial amount (50%)
- System tracks: qty_invoiced = 50, amount_invoiced = $500
- Remaining: 50 units, $500

**Scenario 2: Full Quantity (Partial Rate - Discount)**
- PO: 100 units @ $10/unit = $1,000
- Supplier ships 100 units with 20% discount
- Supplier invoices: 100 units @ $8/unit = $800
- **Result**: Full quantity (100%), discounted rate (80%), partial amount (80%)
- System validation: Amount < PO amount triggers mismatch alert
- Require approval: Procurement Manager must approve discount

**Scenario 3: Partial Quantity + Different Rate**
- PO: 100 units @ $10/unit = $1,000
- Supplier ships 60 units @ $12/unit (price increase)
- Supplier invoices: 60 units @ $12/unit = $720
- **Result**: Partial quantity (60%), increased rate (120%), partial amount (72%)
- System validation: Rate mismatch detected
- Require approval: Procurement + Finance Manager approval required

**Validation Rules**:

1. **Quantity Validation**:
   ```typescript
   const totalQtyInvoiced = sumPreviousInvoices(po_id, 'quantity') + currentInvoice.quantity;
   if (totalQtyInvoiced > po.total_quantity) {
     throw new ValidationError(
       `Over-invoicing detected: PO ${po_id} qty = ${po.total_quantity}, ` +
       `total invoiced = ${totalQtyInvoiced}`
     );
   }
   ```

2. **Amount Validation**:
   ```typescript
   const totalAmountInvoiced = sumPreviousInvoices(po_id, 'amount') + currentInvoice.amount;
   if (totalAmountInvoiced > po.total_amount * 1.01) { // 1% tolerance
     throw new ValidationError(
       `Over-invoicing detected: PO ${po_id} amount = ${po.total_amount}, ` +
       `total invoiced = ${totalAmountInvoiced}`
     );
   }
   ```

3. **Rate Validation**:
   ```typescript
   const expectedUnitPrice = po.unit_price;
   const actualUnitPrice = invoice.amount / invoice.quantity;

   if (Math.abs(actualUnitPrice - expectedUnitPrice) / expectedUnitPrice > 0.01) {
     // Rate differs by > 1%
     createMismatchAlert({
       type: 'RATE_MISMATCH',
       po_id,
       expected_rate: expectedUnitPrice,
       actual_rate: actualUnitPrice,
       variance_pct: ((actualUnitPrice - expectedUnitPrice) / expectedUnitPrice) * 100
     });
   }
   ```

**Approval Matrix for Mismatches (Ambiguity #4 Resolution)**:

| Mismatch Type | Amount | Required Approval | SLA |
|---------------|--------|------------------|-----|
| Qty < PO (partial delivery) | Any | Procurement Manager | 1 business day |
| Amount < PO (discount) | $1 - $5K | Procurement Manager | 1 business day |
| Amount < PO (discount) | $5K - $25K | Finance Manager | 2 business days |
| Amount > PO (price increase) | $1 - $5K | Procurement + Finance Manager | 2 business days |
| Amount > PO (price increase) | $5K+ | Finance Director | 3 business days |
| Rate mismatch > 5% | Any | Procurement + Finance Manager | 2 business days |

**SLA Escalation Policy**:
- If not approved within SLA → Auto-escalate to next level
- Example: $10K price increase not approved in 2 days → escalate to Finance Director
- After 7 days total: Finance Director must approve or reject (cannot ignore)
- After 14 days: Auto-reject with notification to supplier

**Database Schema**:
```sql
ALTER TABLE invoices ADD COLUMN is_partial_qty BOOLEAN DEFAULT FALSE;
ALTER TABLE invoices ADD COLUMN is_partial_amount BOOLEAN DEFAULT FALSE;
ALTER TABLE invoices ADD COLUMN qty_percentage DECIMAL(5,2); -- 50.00 = 50%
ALTER TABLE invoices ADD COLUMN amount_percentage DECIMAL(5,2);

ALTER TABLE purchase_orders ADD COLUMN total_qty_invoiced DECIMAL(18,2) DEFAULT 0;
ALTER TABLE purchase_orders ADD COLUMN total_amount_invoiced DECIMAL(18,2) DEFAULT 0;
```

**Reports**:
- **Partial Delivery Report**: All POs with qty_invoiced < qty_ordered
- **Invoice Mismatch Report**: All invoices with rate variance > 1%
- **Pending Approval Aging**: All mismatches awaiting approval, grouped by SLA status

---

### Flow B: Invoice Dispute

**Scenario**: Hotel questions invoice amount or quality

**Steps**:
1. Invoice received, status: "RECEIVED"
2. Accounting staff finds discrepancy (overcharge or quality issue)
3. Accounting holds invoice (status: "DISPUTED")
4. Sends dispute message to Supplier
5. Supplier and Hotel negotiate
6. **Option 1**: Supplier issues credit note (reduces invoice)
7. **Option 2**: Supplier re-delivers (removes invoice)
8. AP updated once resolved

**Implementation**: Workflow status, dispute tracking, comment thread

**MEDIUM GUARDRAIL - Invoice Dispute Resolution SLA**:
- Disputed invoice must be resolved within 14 days
- After 14 days: Automatically escalate to Finance Director
- Resolution options: Credit note, accept invoice, reject+return, price adjustment
- Payment hold: Cannot pay disputed invoice until resolved
- Comment trail: All negotiations documented for audit
- Credit note validation: Must match dispute amount
- Prevents: Indefinite payment holds, lost disputes

---

### Flow C: Credit Note / Return

**Scenario**: Hotel returns goods or rejects service, Supplier issues credit note

**Steps**:
1. Hotel returns 10 kg of laundry (damaged)
2. Hotel creates "Return" record
3. Supplier issues credit note for $100 (10 × $10)

**Event Published**:
```json
{
  "event_type": "Accounting.CreditNote.Issued.v1",
  "event_version": "v1",
  "event_id": "evt-creditnote-issued-001",
  "correlation_id": "po-12345",
  "tenant_id": "supplier-456",
  "from_tenant_id": "supplier-456",
  "to_tenant_id": "hotel-123",
  "contract_id": "contract-999",
  "signature": "f1a5b9c3d7e1f5a9b3c7d1e5f9a2b6c3d7e1f5a9b3c7d1e5f9a2b6c3d7e1f5",
  "payload": {
    "invoice_id": "inv-001",
    "credit_note_id": "cn-001",
    "reason": "Damaged laundry return",
    "amount": -100
  }
}
```

**Supplier Accounting**:
```
Journal Entry {
  lines: [
    {
      account: "4100",  // Service Revenue
      debit: 100,       // Reverse revenue
      credit: 0
    },
    {
      account: "1200",  // AR
      debit: 0,
      credit: 100       // Reduce AR
    }
  ]
}
```

**Hotel Accounting**:
```
Journal Entry {
  lines: [
    {
      account: "2200",  // AP
      debit: 100,       // Reduce AP
      credit: 0
    },
    {
      account: "6100",  // Service Expense
      debit: 0,
      credit: 100       // Reverse expense
    }
  ]
}
```

---

## Key Events (Cross-Tenant Event Contracts)

All inter-tenant events follow this pattern:

```json
{
  "event_type": "...",
  "event_id": "...",
  "correlation_id": "po-id",  // Links all related events
  "tenant_id": "source-tenant",
  "from_tenant_id": "source-tenant",
  "to_tenant_id": "target-tenant",
  "contract_id": "business-contract-id",
  "payload": { ... }
}
```

**Critical Fields**:
- `from_tenant_id`: Which tenant is sending
- `to_tenant_id`: Which tenant receives
- `contract_id`: Business contract binding them
- `correlation_id`: Trace all related transactions

---

## Accounting Rules (Non-Negotiable)

### Rule 1: Separate Ledgers
- Supplier has own ledger (AR for Hotel invoice)
- Hotel has own ledger (AP for Supplier invoice)
- No shared journals, no shared accounts

### Rule 2: No Direct GL Writes
- Events do NOT write to ledger directly
- Accounting service consumes events
- Accounting service creates journal entries
- Ensures audit trail and validation

### Rule 3: Event Doesn't Equal Recognition
- Invoice event published ≠ revenue recognized
- Revenue recognized only after:
  - Invoice received
  - Invoice approved
  - Journal entry posted
- Same for expense (Hotel side)

### Rule 4: Complete Audit Trail
- Every transaction traced: PO → Invoice → Payment → Journal
- Correlation IDs link all steps
- Both tenants have audit records
- Can answer: "What happened with PO-12345?"

### Rule 5: Rejection Reason Capture
- When Supplier rejects PO, rejection_reason MUST be captured
- Rejection reason is immutable (cannot be edited after rejection)
- Hotel can use reason to improve PO and resubmit
- Rejection reason must be logged in audit trail
- Hotel can query: "Why was PO-12345 rejected?"

### MEDIUM GUARDRAIL - Payment Terms Enforcement & Early Payment Discounts

**Payment Terms Management**:
- Contract specifies: payment_terms (e.g., "NET 30", "2/10 NET 30")
- Due date calculated as: invoice_date + payment_terms (days)
- Early payment discount: If "2/10" = 2% discount if paid within 10 days
- System tracks: invoice_date, due_date, discount_date, discount_percentage
- Payment validation:
  - If payment date ≤ discount_date: Apply discount automatically
  - If payment date > due_date: Flag as "late" and include in aging report
  - If payment date = due_date: Mark as "on-time"
- Reports: Aging of payables, early payment opportunities
- Prevents: Missed discount opportunities, payment date errors

### Rule 6: Cross-Tenant Currency Handling

When Hotel and Supplier operate in different currencies:

**Currency Recording**:
- Invoice generated in Supplier's currency (supplier's GL perspective)
- Hotel records AP in Hotel's currency (hotel's GL perspective)
- Both must maintain original currency + amount

**Multi-Currency Invoice Record**:
```
Invoice {
  invoice_id: "inv-001",
  supplier_currency: "USD",           // Supplier's home currency
  supplier_amount: 550.00             // In supplier's currency

  buyer_currency: "IDR",              // Hotel's home currency
  buyer_amount: 8,250,000.00          // Converted for hotel's records
  exchange_rate: 15000 USD/IDR        // Rate at invoice_date
  rate_date: "2025-12-22"             // When rate locked
}
```

**Exchange Rate Determination** (LOCKED RULE):
- **Source**: Exchange rate at invoice_date (when invoice created)
- **Lock Point**: Rate is immutable once invoice posted
- **If changing suppliers**: Use published rate (no manual adjustment)
- **Rate Provider**: Central bank rate or contract-specified provider

**Journal Entries** (Both Tenants):
```
Supplier Accounting (Supplier Tenant):
  Currency: USD (supplier's currency)

  DR 1200 (AR)        550.00 USD
    CR 4100 (Revenue) 500.00 USD
    CR 2300 (Tax)      50.00 USD

Hotel Accounting (Hotel Tenant):
  Currency: IDR (hotel's currency)

  DR 2200 (AP)        8,250,000 IDR
    CR 6100 (Expense) 7,500,000 IDR  (500 × 15000)
    CR 2300 (Tax)       750,000 IDR  (50 × 15000)

Note: Each tenant uses their OWN currency. No currency conversion in GL.
```

**Payment Settlement**:
```
Payment Example:
  Supplier wants payment in USD
  Hotel has IDR

Option 1: Hotel converts and sends USD
  - Hotel: DR 2200 (AP) 8,250,000 IDR, CR Bank (USD equivalent)
  - Exchange loss/gain: Posted to GL (FX Gain/Loss account)
  - Supplier: Receives 550 USD, records: DR Bank 550, CR AR 550

Option 2: Agreed middle currency (if multi-supply)
  - Contract specifies payment currency
  - Both calculate final amount at payment time
  - Lock rate: Rate at payment_date
  - Difference in rate → FX gain/loss for payor
```

**Revaluation**:
- ❌ DO NOT revalue payables after posting
- ✅ DO record FX gain/loss at payment time (separate transaction)
- ✅ DO lock rate at invoice date (do not update)

---

## Business Contract

### Contract Structure
```
BusinessContract {
  id: "contract-999",
  buyer_tenant_id: "hotel-123",
  seller_tenant_id: "supplier-456",

  status: "ACTIVE" | "SUSPENDED" | "CANCELLED",

  terms: {
    payment_terms: "NET 30",
    default_tax_rate: 0.10,
    price_list_version: 1
  },

  created_at: timestamp,
  created_by: "buyer-admin",

  modifications: [
    { date, field, old_value, new_value, modified_by }
  ]
}
```

### Contract Governance
- Buyer initiates (sends invitation)
- Seller accepts (creates relationship)
- Either party can suspend/cancel
- All changes audited
- Modifications require both parties' awareness

**MEDIUM GUARDRAIL - Supplier Performance Metrics & Scorecards**:
- System tracks per supplier:
  - On-time delivery rate (% POs delivered by due date)
  - Quality acceptance rate (% goods accepted vs rejected)
  - Invoice accuracy rate (% invoices matching PO without disputes)
  - Response time (avg hours to accept/reject PO)
- Monthly scorecard generated:
  - Score = (on_time × 40%) + (quality × 30%) + (accuracy × 20%) + (response × 10%)
  - Threshold: If score < 70% → Manager review triggered
  - If score < 60% → Automatic suspension notice sent
- Reports available: Supplier performance trends, benchmark against peers
- Prevents: Silent supplier degradation, quality issues going unnoticed

**MEDIUM GUARDRAIL - Contract Renewal & Termination Procedures**:
- Contract has: effective_date, renewal_date, termination_date
- 30 days before renewal: System sends renewal notification
- No auto-renewal (manual approval required)
- Termination requires: 30-day notice, settlement of all open POs/invoices
- Upon termination:
  - Block new POs to this supplier
  - Complete all in-flight transactions
  - Archive all contract history (never delete)
  - Send termination confirmation event
- Prevents: Accidental contract expiration, orphaned transactions

### Contract Revocation & Data Cleanup
When a Business Contract is revoked (see SPEC-10 for details):

**Handling of Rejected POs**:
- Rejected POs (status = REJECTED) are archived (not deleted)
- Rejection reasons are preserved for audit trail
- Hotel can still view rejection history
- New POs cannot be created under revoked contract
- Open/Accepted POs must be cancelled (with notification to Supplier)

**Data Cleanup Options**:
- **ARCHIVE** (default): Keep all PO history (including rejections), mark as inactive
- **DELETE_CROSS_REFERENCES** (Buyer only): Remove supplier_tenant_id from POs, preserve local copy
- **KEEP** (Read-only): Maintain references, revoke write access, can still view rejection reasons

---

## Critical Failure Scenario Guardrails

**CRITICAL GUARDRAIL: Cross-Tenant Event Delivery Failure (Missing Guardrail #6)**

**RULE**: Events between tenants (e.g., Invoice.Created from Supplier to Buyer) MUST be delivered reliably with guaranteed delivery semantics. Failures MUST be retried with compensation pattern. Dead-letter queue required for undeliverable events.

**Problem**: If Supplier publishes Invoice.Created event to Buyer tenant but event delivery fails, Buyer won't create AP, leaving Buyer without record of liability and Supplier without record of revenue. Systems become inconsistent.

**Implementation Requirement**:

**Cross-Tenant Event Delivery Pattern**:
```typescript
// Event delivery with guaranteed semantics
async function publishInterTenantEventWithGuarantee(
  event: InterTenantEvent,
  buyerTenantId: string,
  supplierId: string
): Promise<{ success: boolean, deliveryId: string }> {
  // STEP 1: Create delivery record (for tracking)
  const delivery = await eventDeliveryService.create({
    id: generateId('evt-del'),
    event_id: event.event_id,
    event_type: event.event_type,
    from_tenant_id: event.from_tenant_id,
    to_tenant_id: buyerTenantId,
    supplier_id: supplierId,
    event_payload: event,
    status: 'PENDING',  // Not yet delivered
    retry_count: 0,
    next_retry_at: new Date(),
    created_at: new Date(),
    delivery_attempts: []
  });

  // STEP 2: Attempt immediate delivery
  try {
    await deliverEventToBuyerTenant({
      event,
      buyerTenantId,
      deliveryId: delivery.id
    });

    // Success - mark as delivered
    await eventDeliveryService.markDelivered(delivery.id, {
      delivered_at: new Date(),
      status: 'SUCCESS'
    });

    return { success: true, deliveryId: delivery.id };

  } catch (error) {
    // STEP 3: Delivery failed - schedule retry
    const retrySchedule = getExponentialBackoffMs(0);  // Start with 1s

    await eventDeliveryService.update(delivery.id, {
      status: 'PENDING_RETRY',
      retry_count: 1,
      next_retry_at: new Date(Date.now() + retrySchedule),
      last_error: error.message,
      delivery_attempts: [
        {
          attempted_at: new Date(),
          error: error.message,
          backoff_ms: retrySchedule
        }
      ]
    });

    // Schedule async retry job
    await scheduleEventDeliveryRetry({
      deliveryId: delivery.id,
      nextRetryAt: new Date(Date.now() + retrySchedule)
    });

    return { success: false, deliveryId: delivery.id };
  }
}

// Async retry logic with exponential backoff
async function retryEventDelivery(deliveryId: string) {
  const delivery = await eventDeliveryService.get(deliveryId);
  const maxRetries = 48;  // 24+ hours of retries

  if (delivery.retry_count >= maxRetries) {
    // Max retries exceeded - move to dead-letter queue
    await moveToDeadLetterQueue(delivery);
    return;
  }

  try {
    // STEP 1: Verify contract is still active
    const contract = await businessContractService.getContract(
      delivery.from_tenant_id,
      delivery.to_tenant_id,
      delivery.event_payload.contract_id
    );

    if (!contract || contract.status !== 'ACTIVE') {
      // Contract no longer active - move to dead-letter
      await moveToDeadLetterQueue(delivery, {
        reason: 'CONTRACT_NO_LONGER_ACTIVE',
        contract_status: contract?.status
      });
      return;
    }

    // STEP 2: Attempt delivery
    await deliverEventToBuyerTenant({
      event: delivery.event_payload,
      buyerTenantId: delivery.to_tenant_id,
      deliveryId
    });

    // Success - mark as delivered
    await eventDeliveryService.markDelivered(deliveryId, {
      delivered_at: new Date(),
      status: 'SUCCESS',
      final_retry_count: delivery.retry_count
    });

  } catch (error) {
    // STEP 3: Retry failed - schedule next attempt
    const nextRetryCount = delivery.retry_count + 1;
    const backoffMs = getExponentialBackoffMs(nextRetryCount);

    const newAttempt = {
      attempted_at: new Date(),
      error: error.message,
      retry_count: nextRetryCount,
      backoff_ms: backoffMs
    };

    await eventDeliveryService.update(deliveryId, {
      retry_count: nextRetryCount,
      next_retry_at: new Date(Date.now() + backoffMs),
      last_error: error.message,
      delivery_attempts: [...delivery.delivery_attempts, newAttempt]
    });

    // Schedule next retry
    await scheduleEventDeliveryRetry({
      deliveryId,
      nextRetryAt: new Date(Date.now() + backoffMs)
    });
  }
}

// Dead-letter queue for undeliverable events
async function moveToDeadLetterQueue(
  delivery: EventDelivery,
  details?: { reason: string, [key: string]: any }
) {
  await eventDeliveryService.update(delivery.id, {
    status: 'DEAD_LETTERED',
    dead_lettered_at: new Date(),
    dead_letter_reason: details?.reason || 'MAX_RETRIES_EXCEEDED',
    dead_letter_details: details
  });

  // Create dead-letter event
  const dlEvent = await deadLetterQueueService.create({
    id: generateId('dlq'),
    event_id: delivery.event_id,
    event_type: delivery.event_type,
    from_tenant_id: delivery.from_tenant_id,
    to_tenant_id: delivery.to_tenant_id,
    event_payload: delivery.event_payload,
    original_delivery_id: delivery.id,
    retry_count: delivery.retry_count,
    last_error: delivery.last_error,
    created_at: new Date()
  });

  // Send alert to operations team
  await sendAlert({
    to: 'operations-team@company.com',
    subject: `CRITICAL: Cross-Tenant Event Undeliverable - Dead Letter Queue`,
    body: `
Event ID: ${delivery.event_id}
Event Type: ${delivery.event_type}
From Tenant: ${delivery.from_tenant_id}
To Tenant: ${delivery.to_tenant_id}
Retry Attempts: ${delivery.retry_count}
Last Error: ${delivery.last_error}
Dead Letter Reason: ${details?.reason || 'MAX_RETRIES_EXCEEDED'}

ACTION REQUIRED:
1. Investigate why Buyer tenant is not accepting events
2. Check network connectivity between tenants
3. Check if Buyer system is down or busy
4. Manually deliver event to Buyer if needed
5. Update dead-letter event status when resolved

Link: /operations/dead-letter-queue/${dlEvent.id}

NOTE: Supplier's revenue is in ledger (AR posted).
      Buyer's liability is NOT in ledger (AP not created).
      Manual reconciliation may be required.
    `
  });

  // Log dead-letter event for audit
  await auditService.log({
    action: 'EVENT_DEAD_LETTERED',
    event_id: delivery.event_id,
    reason: details?.reason,
    retry_count: delivery.retry_count,
    timestamp: new Date()
  });
}
```

**Guaranteed Delivery Pattern Enforcement**:
- ✅ Schema: event_deliveries table tracks every cross-tenant event
- ✅ Every event has delivery_id and status (PENDING, SUCCESS, PENDING_RETRY, DEAD_LETTERED)
- ✅ Exponential backoff retry: 1s, 2s, 4s, 8s... up to 1h, max 48 times (24+ hours)
- ✅ Delivery attempts logged with timestamp and error
- ✅ Dead-letter queue for undeliverable events (manual intervention point)
- ✅ Contract validation before retry (reject if contract terminated)
- ✅ Alerts to operations team for dead-lettered events
- ✅ Test: Simulate Buyer tenant unavailable; verify event retries and eventually dead-letters
- ✅ Test: Verify contract termination prevents delivery of new events
- ✅ Test: Verify dead-letter events can be manually redelivered

---

## Multi-Tenant Isolation Guardrails

**CRITICAL GUARDRAIL: Cross-Tenant Event Publishing Requires BusinessContract Validation (Multi-Tenant Gap #2)**

**RULE**: No event can be published between two tenants without validating an active BusinessContract exists.

**Problem**: If Supplier Tenant publishes Invoice.Created event to Buyer Tenant without verifying the contract is active, invoices could be created under expired/revoked contracts, violating contractual obligations and creating orphaned financial records.

**Implementation Requirement**:
```typescript
async function publishInterTenantEvent(
  event: InterTenantEvent,
  fromTenantId: string,
  toTenantId: string,
  contractId?: string
): Promise<void> {
  // STEP 1: Fetch BusinessContract from SHARED registry
  const contract = await businessContractService.getContract(
    fromTenantId,
    toTenantId,
    contractId  // Optional: validate specific contract if provided
  );

  // STEP 2: Validate contract exists and is ACTIVE
  if (!contract) {
    throw new Error(
      `No active BusinessContract between tenant ${fromTenantId} and ${toTenantId}. ` +
      `Event publishing blocked. Create contract first.`
    );
  }

  if (contract.status !== 'ACTIVE') {
    throw new Error(
      `BusinessContract ${contract.id} is ${contract.status}, not ACTIVE. ` +
      `Cannot publish events on inactive contract.`
    );
  }

  if (contract.terminated_at !== null) {
    throw new Error(
      `BusinessContract ${contract.id} was terminated on ${contract.terminated_at}. ` +
      `No events allowed after termination.`
    );
  }

  // STEP 3: Attach contract_id to event for audit trail
  const eventWithContract = {
    ...event,
    contract_id: contract.id,
    from_tenant_id: fromTenantId,
    to_tenant_id: toTenantId
  };

  // STEP 4: Publish event
  await eventPublisher.publish(eventWithContract);
}
```

**Enforcement**:
- ✅ Code: EVERY cross-tenant event must call publishInterTenantEvent() (not direct publish())
- ✅ Test: Unit test must verify event is REJECTED if contract is INACTIVE or TERMINATED
- ✅ Test: Unit test must verify event is REJECTED if no contract exists
- ✅ Code review: Zero tolerance for direct publish() calls in inter-tenant flows
- ✅ Database: Foreign key constraint: events.contract_id REFERENCES business_contracts.id
- ✅ Audit: All contract validation attempts logged (success and failures)

---

**CRITICAL GUARDRAIL: AP Creation Requires Active Supplier Contract Validation (Multi-Tenant Gap #3)**

**RULE**: Buyer Tenant can ONLY create AP from received invoice if Supplier Tenant has an active BusinessContract.

**Problem**: If Buyer creates AP from invoice without validating the Supplier contract is active, the invoice could be from a supplier who is no longer authorized to do business, or the contract was already terminated.

**Implementation Requirement**:
```typescript
async function createAPFromSupplierInvoice(
  event: SupplierInvoiceReceivedEvent,
  buyerTenantId: string
): Promise<AccountsPayable> {
  // STEP 1: Verify BusinessContract exists and is ACTIVE
  const contract = await businessContractService.getActiveContract(
    supplierId: event.supplier_tenant_id,
    buyerId: buyerTenantId
  );

  if (!contract || contract.status !== 'ACTIVE') {
    throw new Error(
      `Cannot create AP. Supplier ${event.supplier_tenant_id} has no active ` +
      `BusinessContract with Buyer ${buyerTenantId}. ` +
      `Invoice from unauthorized supplier.`
    );
  }

  // STEP 2: Verify supplier is not terminated
  if (contract.terminated_at !== null) {
    throw new Error(
      `Cannot create AP. Contract with Supplier was terminated on ` +
      `${contract.terminated_at}. No new AP allowed after termination.`
    );
  }

  // STEP 3: Verify PO exists and was issued under THIS contract
  const po = await poService.getPO(event.po_id);

  if (!po || po.contract_id !== contract.id) {
    throw new Error(
      `Invoice ${event.invoice_id} references PO ${event.po_id}, ` +
      `but PO was issued under different contract. Contract mismatch.`
    );
  }

  // STEP 4: Create AP with contract_id reference
  const ap = await accountsPayableService.create({
    invoice_id: event.invoice_id,
    po_id: event.po_id,
    supplier_tenant_id: event.supplier_tenant_id,
    contract_id: contract.id,  // MANDATORY: Link to contract
    amount: event.amount,
    status: 'PENDING_MATCH',
    buyer_tenant_id: buyerTenantId
  });

  return ap;
}
```

**Enforcement**:
- ✅ Schema: AP table MUST have contract_id column (NOT NULL, FOREIGN KEY)
- ✅ Code: Every AP creation MUST validate supplier contract is ACTIVE
- ✅ Test: Unit test must verify AP creation is REJECTED if contract is TERMINATED
- ✅ Test: Unit test must verify AP creation is REJECTED if no contract exists
- ✅ Test: Unit test must verify PO contract matches supplier contract
- ✅ Code review: Zero tolerance for AP creation without contract validation
- ✅ Audit: Contract validation failure logged with: timestamp, user, invoice_id, reason

---

## Implementation Checklist

When implementing inter-tenant supplier flow:

- [ ] Business Contract model created
- [ ] PO model supports inter-tenant reference
- [ ] PO can be sent via event to supplier
- [ ] Supplier receives and can accept/reject PO
- [ ] Invoice model supports inter-tenant reference
- [ ] Invoice can be sent via event to buyer
- [ ] Buyer AP created from received invoice
- [ ] Supplier AR created from issued invoice
- [ ] Payment event sent from buyer to seller
- [ ] Journal entries created in both ledgers
- [ ] No shared database tables between tenants
- [ ] All events have correlation_id for tracing
- [ ] Audit logs show both buyer and seller perspective
- [ ] Tests verify complete transaction flow
- [ ] Tests verify accounting balancing (both sides)

---

## Related Documents

- **REF-05**: Core Concepts — User, Tenant, App relationships
- **SPEC-10**: Accounting Core Process — How AP/AR and journal entries work
- **SPEC-09**: PMS Core Process — How hotel operations generate requirements
- **STD-19**: Event Model — How cross-tenant events are structured
- **ARCH-09**: Modularization Principles — How modules interact
- **SEC-02**: Data Protection — How data isolation is enforced
