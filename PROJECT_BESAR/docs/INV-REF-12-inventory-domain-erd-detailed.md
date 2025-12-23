# REF-12: Inventory Domain ERD (Detailed)

This document defines the **detailed entity relationship design for the Inventory domain**. Inventory tracks stock quantity and movement, but does NOT own financial balances—COGS and valuation adjustments flow to Accounting.

**Critical Principle**: *Inventory is operational truth about what we have. Accounting is financial truth about what that costs. They are separate but integrated.*

---

## Inventory Principles (Locked - Non-Negotiable)

### Principle 1: Inventory = Quantity & Operational Value
```
Inventory tracks what we have (quantity).
Inventory provides cost estimates (unit cost, FIFO/AVG).
Accounting records actual financial impact (COGS, valuations).
```

### Principle 2: No Final Financial Balances in Inventory
```
Inventory balance is CACHE (current QoH).
Authoritative history = StockMovement (append-only).
Financial truth = GL account balance (Accounting).
```

### Principle 3: Every Stock Movement Leaves Trace
```
Cannot edit StockMovement after posting.
Corrections via new adjustment movement.
Complete audit trail of all changes.
```

### Principle 4: Valuation Creates Accounting Impact
```
COGS Entry records consumption/usage.
Generates event to Accounting.
Accounting posts GL (DR COGS, CR Inventory).
```

### Principle 5: Inventory Rebuild from Movement Log
```
Current stock = SUM(in movements) - SUM(out movements).
Current stock is CALCULATED, not stored.
Can rebuild any time from movement history.
```

---

## Domain 1: Master Data

### Item (Stock Keeping Unit)

**Purpose**: Definition of inventory items

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique item identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `sku` | VARCHAR | NOT NULL, UNIQUE (tenant_id) | Item code ("COFFEE-ARABICA", "TOWEL-WHT") |
| `name` | VARCHAR | NOT NULL | Item name |
| `category` | VARCHAR | NOT NULL | Category ("F&B", "Supplies", "Linen") |
| `unit_of_measure` | ENUM | NOT NULL | 'piece', 'kg', 'liter', 'box', 'dozen' |
| `reorder_level` | INT | | When to reorder |
| `reorder_quantity` | INT | | How much to order |
| `is_active` | BOOLEAN | NOT NULL | Currently tracked |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**:
- (tenant_id, sku) - One SKU per organization

**Notes**:
- sku is human-readable identifier
- unit_of_measure controls quantity units
- reorder_level triggers alerts

---

### Warehouse (Storage Location)

**Purpose**: Physical storage locations

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique warehouse identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `name` | VARCHAR | NOT NULL | Warehouse name ("Main Store", "Kitchen", "Outlet 2") |
| `type` | ENUM | NOT NULL | 'main', 'kitchen', 'outlet', 'storage' |
| `address` | TEXT | | Physical location |
| `capacity` | INT | | Storage capacity (if applicable) |
| `is_active` | BOOLEAN | NOT NULL | Currently used |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- Multiple warehouses per organization
- type affects reporting and movement logic
- capacity for space management

---

## Domain 2: Stock & Movement

### Stock (Current Inventory Position)

**Purpose**: Real-time stock quantity (cache, NOT source of truth)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique stock record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `item_id` | UUID | FK→Item, NOT NULL | Which item |
| `warehouse_id` | UUID | FK→Warehouse, NOT NULL | Which location |
| `quantity_on_hand` | INT | NOT NULL, ≥0 | Current quantity |
| `last_updated_at` | TIMESTAMP | NOT NULL | When quantity changed |

**Unique Constraint**:
- (tenant_id, item_id, warehouse_id) - One stock position per item-warehouse combo

**CRITICAL NOTE**:
```
quantity_on_hand is a CACHE (current snapshot).
NOT the source of truth for historical accuracy.
Source of truth = StockMovement log (append-only).

Current quantity calculated as:
SELECT SUM(quantity) FROM stock_movements
WHERE item_id = $1 AND warehouse_id = $2
  AND movement_type IN ('in', 'transfer_in')
MINUS
SELECT SUM(quantity) FROM stock_movements
WHERE item_id = $1 AND warehouse_id = $2
  AND movement_type IN ('out', 'transfer_out')
```

---

### StockMovement (Audit Trail of All Changes)

**Purpose**: Immutable record of every stock movement (append-only)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique movement identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `item_id` | UUID | FK→Item, NOT NULL | Which item |
| `warehouse_id` | UUID | FK→Warehouse, NOT NULL | Which warehouse |
| `movement_type` | ENUM | NOT NULL | 'in', 'out', 'transfer_in', 'transfer_out', 'adjustment' |
| `quantity` | INT | NOT NULL | Quantity moved (positive) |
| `unit_cost` | DECIMAL(12,4) | | Unit cost at time of movement (for COGS) |
| `reference_type` | ENUM | NOT NULL | 'po', 'goods_receipt', 'issue', 'count', 'manual' |
| `reference_id` | VARCHAR | | FK to originating document |
| `occurred_at` | TIMESTAMP | NOT NULL | When movement happened |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Constraints**:
- Cannot delete or edit StockMovement
- quantity always positive (sign determined by movement_type)
- reference_id links to source document (PO, GoodsReceipt, etc.)

**Movement Types**:
- in: Stock received (purchase, transfer in)
- out: Stock issued (usage, sale, transfer out)
- transfer_in: Received from another warehouse
- transfer_out: Sent to another warehouse
- adjustment: Recount adjustment

**Relationships**:
```
StockMovement N--1 Item
StockMovement N--1 Warehouse
StockMovement → GoodsReceipt (via reference_id)
```

**Notes**:
- Append-only log (immutable history)
- unit_cost captured at time of movement
- Allows rebuild of stock at any point in time

---

## Domain 3: Procurement Integration

### GoodsReceipt (Receiving Inventory)

**Purpose**: Record of goods received (from PO or supplier)

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique receipt identifier |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `supplier_tenant_id` | UUID | FK→Tenant | If from supplier tenant |
| `po_id` | UUID | FK→PurchaseOrder | Which PO being received |
| `receipt_number` | VARCHAR | NOT NULL | "GR-2025-001" |
| `status` | ENUM | NOT NULL | 'draft', 'received', 'inspected', 'posted' |
| `received_at` | TIMESTAMP | NOT NULL | When goods received |
| `inspected_at` | TIMESTAMP | | When QC passed |
| `posted_at` | TIMESTAMP | | When GL posted |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Relationships**:
```
GoodsReceipt 1--* GoodsReceiptLine
GoodsReceipt → StockMovement (via reference_id)
```

---

### GoodsReceiptLine (Line Items)

**Purpose**: Individual items in receipt

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique line identifier |
| `goods_receipt_id` | UUID | FK→GoodsReceipt, NOT NULL | Which receipt |
| `item_id` | UUID | FK→Item, NOT NULL | Which item |
| `warehouse_id` | UUID | FK→Warehouse, NOT NULL | Which warehouse receives |
| `po_qty` | INT | NOT NULL | PO quantity |
| `received_qty` | INT | NOT NULL | Actual received |
| `unit_price` | DECIMAL(12,4) | NOT NULL | Cost per unit |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Notes**:
- received_qty may differ from po_qty (shortage, overage)
- unit_price used for COGS calculation
- Triggers StockMovement creation

---

## Domain 4: Valuation & COGS

### InventoryValuation (Unit Cost)

**Purpose**: Track unit cost for COGS calculation

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique valuation record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `item_id` | UUID | FK→Item, NOT NULL | Which item |
| `valuation_method` | ENUM | NOT NULL | 'FIFO', 'AVG', 'LIFO' |
| `current_unit_cost` | DECIMAL(12,4) | NOT NULL | Current unit cost |
| `effective_date` | DATE | NOT NULL | When this cost became current |
| `previous_unit_cost` | DECIMAL(12,4) | | Prior cost (for history) |
| `previous_effective_date` | DATE | | When previous cost ended |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Valuation Method Rules**:

| Method | How It Works | When to Use | Pros | Cons |
|--------|-------------|------------|------|------|
| **FIFO** | Consume oldest inventory first | Default for perishables (food, pharma) | Matches physical flow, lower tax burden in inflation | Can distort COGS in volatile markets |
| **AVG** | Use weighted average cost | Default for most businesses | Smooths cost fluctuations | Less intuitive |
| **LIFO** | Consume newest inventory first | High-inflation environments (rare) | Matches inflationary impact | Backward inventory flow |

**Business Rules** (LOCKED - Cannot Change Mid-Fiscal Year):
```
1. Method set at: FIRST goods receipt for item
2. Lock period: Full fiscal year (Jan 1 - Dec 31)
3. Change allowed: Only at fiscal year boundary
4. Approval required: CFO approval to change method
5. Adjustment: If changed, create adjustment entry for the difference

EXAMPLE:
  Item ABC uses FIFO (cost=$10/unit)
  At Dec 31: Switch to AVG (cost=$9.50/unit)
  Adjustment: -$0.50 per unit × 500 units = -$250 impact
  → Create adjustment JE in GL
  → Log change in audit trail
  → Effective: Jan 1 next year
```

**Implementation**:
- Unit cost updated when new goods received
- COGS calculated using appropriate method
- No mid-year method changes allowed
- All changes logged in audit trail with approval

---

### COGSEntry (Cost of Goods Sold)

**Purpose**: Record of consumption/usage with cost impact

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique COGS entry |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `item_id` | UUID | FK→Item, NOT NULL | Which item used |
| `quantity` | INT | NOT NULL | Quantity consumed |
| `unit_cost` | DECIMAL(12,4) | NOT NULL | Cost per unit (FIFO/AVG) |
| `cost_amount` | DECIMAL(15,2) | NOT NULL | Calculated: quantity × unit_cost |
| `source` | ENUM | NOT NULL | 'pos', 'pms', 'adjustment' |
| `reference_id` | VARCHAR | | FK to source (POS order, PMS charge) |
| `occurred_at` | TIMESTAMP | NOT NULL | When consumed |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Relationships**:
```
COGSEntry → StockMovement (via reference_id)
COGSEntry → Accounting.Adjustment (via event)
```

**Flow**:
```
POS.SaleCompleted event
  ↓
Inventory.COGS handler consumes
  ↓
Creates COGSEntry (quantity × unit_cost)
  ↓
Publishes Inventory.COGS.Calculated event
  ↓
Accounting.Adjustment handler consumes
  ↓
Posts GL (DR COGS Expense, CR Inventory Asset)
```

**Notes**:
- COGSEntry does NOT modify GL
- Creates event for Accounting to consume
- Maintains separation of concerns

### COGS Approval Workflow (For Manual Adjustments)

When COGS needs to be manually adjusted (not from POS/PMS), it requires approval:

**Scenario**: Inventory count revealed spoilage (20 kg of coffee damaged, cost $200)

**Step 1: Warehouse Staff Reports Damage**
```
COGSAdjustmentRequest {
  id: "adj-req-001",
  tenant_id: "org-123",
  item_id: "item-coffee-001",
  quantity_affected: 20,
  reason: "Spoilage - coffee mold damage",
  unit_cost: 10.00,
  estimated_cogs_impact: 200.00,  // 20 × $10
  created_by: "warehouse-staff-123",
  created_at: timestamp
}
```

**Step 2: Approval Workflow Triggered**
```
Event: Approval.Submitted.v1
{
  workflow_instance_id: "wf-cogs-001",
  entity_type: "COGSAdjustmentRequest",
  entity_id: "adj-req-001",
  required_approval_level: "admin",  // Inventory manager
  amount_affected: 200.00
}
```

**Step 3: Inventory Manager Reviews & Approves**

Manager checks:
- Is spoilage documented? ✅
- Is cost calculation correct? ✅ (20 × $10 = $200)
- Should this be recorded as waste (COGS) or insurance claim?
- Click "Approve"

```
Event: Approval.Approved.v1
{
  workflow_instance_id: "wf-cogs-001",
  entity_type: "COGSAdjustmentRequest",
  entity_id: "adj-req-001",
  approved_by: "manager-456",
  approved_at: timestamp,
  approval_reason: "Verified spoilage, documented in photos"
}
```

**Step 4: System Creates COGS Entry**

Upon approval:
```
COGSEntry {
  id: "cogs-entry-spoi-001",
  tenant_id: "org-123",
  item_id: "item-coffee-001",
  quantity: 20,
  unit_cost: 10.00,
  cost_amount: 200.00,
  source: "adjustment",
  reference_id: "adj-req-001",
  occurred_at: count_date,
  created_at: NOW()
}
```

**Step 5: Accounting Posts GL Entry**

Event: `Inventory.COGS.Calculated.v1` triggers:
```
Journal Entry {
  DR 6200 (COGS Expense)     200.00
    CR 1300 (Inventory Asset) 200.00
  Description: "COGS adjustment - spoilage (approved adj-req-001)"
}
```

### COGS Approval Rules (LOCKED)

**Rule 1: Manual COGS Adjustments Require Approval**
- ✅ Automatic COGS from POS/PMS: No approval needed (event-driven)
- ✅ Manual adjustments (spoilage, theft, sample): MUST have approval
- ❌ Staff cannot create manual COGS entries without approval

**Rule 2: Approval Authority by Amount**

| Amount | Required Approval |
|--------|-------------------|
| < $500 | Warehouse Manager |
| $500 - $5,000 | Inventory Director |
| > $5,000 | Owner/CFO |

**Rule 3: Supporting Documentation Required**
- Reason must be documented (spoilage report, theft report, sample disposal)
- Photos/evidence required for > $1,000 adjustments
- Reference to count/inspection date

**Rule 4: Audit Trail**
- COGS adjustment record immutable (cannot delete)
- Approval decision logged
- GL entries created atomically with approval
- Complete traceability: warehouse staff → manager → GL posting

---

## Domain 5: Stock Count & Adjustment

### StockCount (Physical Inventory Count)

**Purpose**: Periodic physical count of inventory

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique count record |
| `tenant_id` | UUID | FK→Tenant, NOT NULL | Which organization |
| `warehouse_id` | UUID | FK→Warehouse, NOT NULL | Which warehouse |
| `count_date` | DATE | NOT NULL, UNIQUE (tenant_id, warehouse_id) | When count done |
| `status` | ENUM | NOT NULL | 'open', 'in_progress', 'completed', 'reconciled' |
| `counted_by` | UUID | FK→User | Who did count |
| `reconciled_at` | TIMESTAMP | | When variance resolved |
| `reconciled_by` | UUID | FK→User | Who reviewed |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |

**Unique Constraint**:
- (tenant_id, warehouse_id, count_date) - One count per warehouse per day

---

### StockCountLine (Count Detail)

**Purpose**: Item counts from physical count

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `id` | UUID | PK | Unique line identifier |
| `stock_count_id` | UUID | FK→StockCount, NOT NULL | Which count |
| `item_id` | UUID | FK→Item, NOT NULL | Which item |
| `system_quantity` | INT | NOT NULL | Quantity in system |
| `counted_quantity` | INT | NOT NULL | Quantity physically counted |
| `variance` | INT | NOT NULL | Difference (counted - system) |

**Variance Handling**:
```
If variance = 0: No action needed
If variance > 0: Shortage → StockMovement (in) + COGS reversal
If variance < 0: Overage → StockMovement (out)
```

---

## Domain 6: Event Emission

Events published by Inventory for other modules:

| Event | When | Consumers |
|-------|------|-----------|
| `Inventory.Stock.Received.v1` | GoodsReceipt finalized | Stock updated, GL posted (asset) |
| `Inventory.Stock.Issued.v1` | StockMovement out | COGS calculated |
| `Inventory.Stock.Adjusted.v1` | Stock count variance resolved | GL adjustment posted |
| `Inventory.COGS.Calculated.v1` | COGS entry created | Accounting posts COGS expense |
| `Inventory.LowStock.Alert.v1` | Item below reorder level | Procurement triggered |

---

## Domain 7: Boundary Rules (Strict)

### ❌ Hard Rules (Cannot Be Broken)

| Rule | Why | Consequence |
|------|-----|-------------|
| **Inventory cannot write JournalLine** | Maintains separation | GL integrity compromised |
| **Cannot edit StockMovement** | Audit trail immutability | Recalculation errors |
| **COGS requires event** | Ensures Accounting posts GL | Financial disconnect |
| **Stock without reference** | Traceability required | Lost audit trail |
| **Quantity always positive** | Movement_type determines direction | Data confusion |

### ✅ Allowed Operations

| Operation | How |
|-----------|-----|
| **Receive goods** | Create GoodsReceipt, triggers StockMovement |
| **Issue stock** | Create StockMovement (out), triggers COGS |
| **Transfer between warehouses** | Create two movements (out, transfer_in) |
| **Count variance** | Create adjustment StockMovement |
| **Recalculate cost** | Update InventoryValuation |

---

## Data Isolation & Tenant Rules

All inventory data tenant-scoped:

```sql
-- All queries must include tenant_id:

SELECT * FROM stock_movements
WHERE tenant_id = $1  -- MANDATORY
  AND occurred_at >= $2;

SELECT SUM(quantity) FROM stock_movements
WHERE tenant_id = $1  -- MANDATORY
  AND item_id = $2 AND warehouse_id = $3
  AND movement_type IN ('in', 'transfer_in')
UNION ALL
SELECT -SUM(quantity) FROM stock_movements
WHERE tenant_id = $1  -- MANDATORY
  AND item_id = $2 AND warehouse_id = $3
  AND movement_type IN ('out', 'transfer_out');
```

---

## Compliance Checklist

When designing inventory features:

- [ ] All entities have tenant_id
- [ ] No direct GL posting from Inventory
- [ ] StockMovement immutable (append-only)
- [ ] Quantity = SUM(movements), not stored
- [ ] COGS publishes event
- [ ] Stock count variance triggers adjustment
- [ ] Unit cost captured per movement
- [ ] All movements have reference
- [ ] Low stock alerts configured
- [ ] Tenant isolation enforced
- [ ] Tests verify movement integrity

---

## Related Documents

- **REF-10**: Accounting Domain ERD (Detailed) — GL accounts for inventory assets and COGS
- **REF-08**: Entity Relationship Model (Core) — Foundation model
- **ARCH-12**: Read Model & CQRS Pattern — Stock and valuation read models
- **STD-19**: Event Contract Standard — Events published by Inventory
