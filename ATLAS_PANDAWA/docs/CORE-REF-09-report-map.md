# REF-09: Report Map & Requirements

This document maps all required reports across ATLAS_PANDAWA. It serves as a catalog of reporting needs, data requirements, and governance rules.

**Purpose**: Reference for understanding what reports must be available, who can access them, and what data they depend on.

**Usage**:
- Business analysts: Understand reporting landscape
- Backend engineers: Design read models and projections
- Frontend engineers: Build report UI and export functionality
- Auditors: Verify required reports exist and are compliant

---

## Report Principles (Locked)

### Principle 1: Reports ≠ OLTP Queries
```
Reports are generated from read models (projections).
NOT queries against transactional tables.
Rationale: Reporting queries can be complex and expensive.
OLTP databases must remain optimized for writes.
```

### Principle 2: Accounting = Source of Financial Truth
```
Any financial report MUST derive from GL (General Ledger).
AR Aging comes from JournalEntry + JournalLine, not Invoice table.
Rationale: GL is immutable, versioned, auditable.
```

### Principle 3: Reports Follow Period & Approval
```
Closed periods: reports locked (no changes possible).
Approval-required reports: only approved data shown.
Rationale: Financial reporting integrity and audit compliance.
```

### Principle 4: Cross-Tenant Reports via Contract Only
```
Supplier-Hotel consolidated report ONLY if BusinessContract exists.
Cannot query other tenant's data without explicit agreement.
Rationale: Tenant isolation, data privacy.
```

---

## Report Categories

### Category 1: PMS Operational Reports

Reports for daily hotel operations management.

#### Daily Operations Group

**1. Occupancy Report**
```
Purpose: Room occupancy status and percentage
Frequency: Daily (end of day)
Data Source: Folio (checked-in status)
Dimensions: Room type, floor, status
Metrics: Occupied rooms, vacant rooms, occupancy %
Access: Staff+
```

**2. Room Status Report**
```
Purpose: Real-time room status (clean, dirty, out-of-service, occupied)
Frequency: Real-time
Data Source: Folio, Housekeeping module
Dimensions: Room number, floor, status, last cleaned
Metrics: Room count by status
Access: Staff+
```

**3. Arrival & Departure List**
```
Purpose: Expected check-ins/check-outs for the day
Frequency: Daily (overnight)
Data Source: Reservation
Dimensions: Guest name, room, time, status
Metrics: Arrival count, departure count
Access: Staff+
```

**4. In-House Guest Report**
```
Purpose: All currently checked-in guests
Frequency: Real-time
Data Source: Folio (active)
Dimensions: Guest name, room, check-in date, check-out date, nights
Metrics: Total in-house count
Access: Staff+
Notes: For guest services, housekeeping coordination
```

---

#### Revenue Group

**5. Daily Revenue by Room Type**
```
Purpose: Revenue breakdown by room type
Frequency: Daily (after night audit)
Data Source: Folio → GL posting (Room Revenue account)
Dimensions: Room type, occupancy, average daily rate (ADR)
Metrics: Rooms sold, revenue, ADR, RevPAR
Access: Admin+
Notes: Sourced from GL, not Folio table directly
```

**6. Revenue by Channel**
```
Purpose: Revenue attribution by booking channel (OTA, Direct, etc.)
Frequency: Daily
Data Source: Reservation (source field) → GL
Dimensions: Channel (Booking.com, Direct, Agoda, etc.)
Metrics: Bookings, revenue, average rate by channel
Access: Admin+
```

**7. No-Show & Cancellation Report**
```
Purpose: Track no-shows and cancellations
Frequency: Daily/Weekly
Data Source: Reservation (cancelled, no-show status)
Dimensions: Reservation status, reason code
Metrics: Count, revenue impact, cancellation rate
Access: Admin+
Notes: For revenue management analysis
```

---

#### Control Group

**8. Night Audit Summary**
```
Purpose: Daily reconciliation and audit results
Frequency: Daily (post night audit)
Data Source: Folio (closed), GL postings
Dimensions: Room revenue, other revenue, discounts, adjustments
Metrics: Revenue summary, variance from expected
Access: Admin+
Notes: Critical control report
```

**9. Open Folio Report**
```
Purpose: Identify folios not yet closed/paid
Frequency: Weekly
Data Source: Folio (status = 'open')
Dimensions: Guest, folio number, open date, age
Metrics: Open folio count, total unpaid amount, aging buckets
Access: Admin+
Notes: Credit management
```

---

### Category 2: Accounting Reports (Audit-Safe)

Financial statements and ledger reports. **All sourced from GL (JournalEntry + JournalLine).**

#### Financial Statements

**10. Balance Sheet**
```
Purpose: Assets, Liabilities, Equity position
Frequency: Monthly (post period-close)
Data Source: GL (asset, liability, equity accounts)
Dimensions: Account hierarchy
Metrics: Account balance (debit/credit)
Access: Owner/Admin
Period: Closed periods only
Notes: Regulatory compliance
```

**11. Profit & Loss (Income Statement)**
```
Purpose: Revenue, expenses, net income
Frequency: Monthly (post period-close)
Data Source: GL (revenue, expense accounts)
Dimensions: Account hierarchy, time period
Metrics: Revenue, expenses, gross profit, net income
Access: Owner/Admin
Period: Closed periods only
Notes: Management performance metric
```

**12. Cash Flow Statement**
```
Purpose: Cash inflows/outflows (operating, investing, financing)
Frequency: Monthly
Data Source: GL (cash accounts), Payment records
Dimensions: Activity type (operating, investing, financing)
Metrics: Cash inflows, outflows, net change
Access: Owner/Admin
Notes: Liquidity analysis
```

---

#### Sub-Ledger Reports

**13. AR Aging Report**
```
Purpose: Accounts Receivable aged by invoice date
Frequency: Weekly/Monthly
Data Source: Invoice (AR) + Payment, not yet fully paid
Dimensions: Aging bucket (current, 30, 60, 90+ days)
Metrics: Invoice count, total amount by bucket, % aging
Access: Admin+
Notes: Credit management, DSO analysis
```

**14. AP Aging Report**
```
Purpose: Accounts Payable aged by invoice date
Frequency: Weekly/Monthly
Data Source: Invoice (AP) + Payment, not yet fully paid
Dimensions: Aging bucket (current, 30, 60, 90+ days), supplier
Metrics: Invoice count, total amount by bucket, % aging
Access: Admin+
Notes: Cash planning, supplier management
```

**15. Cash & Bank Position**
```
Purpose: Current cash and bank balances
Frequency: Daily
Data Source: GL (cash and bank accounts)
Dimensions: Account (cash, bank A, bank B, etc.)
Metrics: Closing balance, today's transactions
Access: Owner/Admin
Notes: Liquidity position
```

---

#### Control & Compliance

**16. Trial Balance**
```
Purpose: Verify GL balance (debits = credits)
Frequency: Monthly (pre period-close)
Data Source: GL (all accounts)
Dimensions: Account
Metrics: Debit total, credit total (must equal)
Access: Owner/Admin
Period: Any period
Notes: Internal control, must balance
```

**17. Journal Listing (GL Audit Report)**
```
Purpose: All posted journal entries for audit
Frequency: On-demand
Data Source: JournalEntry + JournalLine
Dimensions: Entry date, source type, account, amount
Metrics: Entry count, total debits, total credits
Access: Owner/Admin
Filters: Date range, source type, account
Notes: Audit trail
```

**18. Period Closing Report**
```
Purpose: Closing checklist and reconciliation
Frequency: Monthly (post period-close)
Data Source: JournalEntry, AccountingPeriod
Dimensions: Period
Metrics: Entry count, amount, closing status
Access: Owner/Admin
Notes: Period integrity verification
```

---

### Category 3: Procurement & Supplier Reports

#### Buyer (Hotel) Side

**19. Purchase Order Outstanding**
```
Purpose: Open POs not yet fulfilled/invoiced
Frequency: Weekly
Data Source: PurchaseOrder (status != 'fulfilled')
Dimensions: Supplier, PO age, status
Metrics: PO count, total amount outstanding, delivery status
Access: Admin+
Notes: Procurement management
```

**20. Supplier Invoice List**
```
Purpose: All invoices from suppliers (AP invoices)
Frequency: Weekly/Monthly
Data Source: Invoice (type = 'AP')
Dimensions: Supplier (counterparty), invoice date, due date, payment status
Metrics: Invoice count, total amount, paid %, aging
Access: Admin+
Notes: Payables management
```

**21. Supplier Spend Analysis**
```
Purpose: Spending by supplier for the period
Frequency: Monthly
Data Source: Invoice (AP) + Payment, grouped by supplier
Dimensions: Supplier, category (if tracked), time period
Metrics: Spend amount, invoice count, avg invoice, top suppliers
Access: Admin+
Notes: Vendor management, negotiation support
```

---

#### Supplier (Seller) Side

**22. Sales by Customer (Hotel)**
```
Purpose: Revenue from each hotel customer
Frequency: Monthly
Data Source: Invoice (AR to hotels), via BusinessContract
Dimensions: Customer (buyer tenant), time period
Metrics: Sales amount, invoice count, avg invoice, growth
Access: Owner/Admin (Supplier tenant only)
Notes: Customer concentration analysis
```

**23. Outstanding AR Report (Supplier)**
```
Purpose: Supplier's AR (hotels that owe them)
Frequency: Weekly/Monthly
Data Source: Invoice (AR to hotels), unpaid
Dimensions: Customer hotel, aging bucket
Metrics: Invoice count, total amount, aging distribution
Access: Owner/Admin (Supplier tenant only)
Notes: Credit management from supplier perspective
```

**24. Delivery Performance Report (Supplier)**
```
Purpose: On-time delivery metrics to customers
Frequency: Monthly
Data Source: PurchaseOrder (fulfillment date vs. promised date)
Dimensions: Customer hotel, on-time %, delivery lateness
Metrics: Orders fulfilled, % on-time, avg days late
Access: Owner/Admin (Supplier tenant only)
Notes: Service quality metric
```

---

### Category 4: Inventory Reports

**25. Stock On Hand**
```
Purpose: Current inventory quantity and value
Frequency: Real-time (or daily snapshot)
Data Source: Inventory (quantity-on-hand, unit cost)
Dimensions: Item, location, SKU
Metrics: Quantity, unit cost, total value (quantity × cost)
Access: Staff+
Notes: Stock valuation method (FIFO/LIFO) configurable
```

**26. Stock Movement**
```
Purpose: In/out of inventory during period
Frequency: Daily/Weekly
Data Source: InventoryMovement (receipt, usage, adjustment)
Dimensions: Item, movement type, date, location
Metrics: Inbound quantity, outbound quantity, net change
Access: Staff+
Notes: For tracking usage patterns
```

**27. Low Stock Alert**
```
Purpose: Items below minimum stock threshold
Frequency: Daily
Data Source: Inventory (quantity < min_quantity)
Dimensions: Item, current quantity, minimum, reorder quantity
Metrics: Item count, reorder amount
Access: Admin+
Notes: Procurement trigger
```

**28. Inventory Valuation**
```
Purpose: Total inventory value (cost of goods)
Frequency: Monthly (period-end)
Data Source: Inventory (quantity × unit cost)
Dimensions: Location, category, item
Metrics: Total value, variance from GL (Inventory account)
Access: Owner/Admin
Notes: GL reconciliation required
```

---

### Category 5: HR & Payroll Reports

**29. Payroll Summary**
```
Purpose: Monthly payroll amount and breakdown
Frequency: Monthly (pre-payroll)
Data Source: Payroll (employee, amount, deductions)
Dimensions: Department, employee type, deduction type
Metrics: Gross payroll, deductions, net payroll
Access: Owner/Admin
Notes: Before approval for payment
```

**30. Employee Cost by Department**
```
Purpose: Labor cost breakdown by business unit
Frequency: Monthly
Data Source: Payroll, Department assignment
Dimensions: Department, cost category (base, benefits, taxes)
Metrics: Total cost, cost per employee, % of revenue
Access: Owner/Admin
Notes: Cost management analysis
```

**31. Attendance Summary**
```
Purpose: Attendance tracking (presence, absence, OT)
Frequency: Monthly
Data Source: Attendance (clock in/out)
Dimensions: Employee, attendance status (present, absent, late, OT)
Metrics: Attendance rate, OT hours, absence count
Access: Admin+
Notes: HR management
```

---

### Category 6: Inter-Tenant Reports

Reports involving multiple tenants (Hotel + Supplier, etc.).

**32. Inter-Tenant Invoice Reconciliation**
```
Purpose: Reconcile invoices between buyer and seller
Frequency: Monthly
Data Source: Invoice (AR from supplier, AP from buyer)
Dimensions: BusinessContract, invoice number, date
Metrics: Invoice count, matched %, variance amount
Access: Owner/Admin (both tenants must approve)
Notes: Cross-tenant reconciliation
```

**33. Contract Performance Report**
```
Purpose: Performance metrics per BusinessContract
Frequency: Monthly
Data Source: Invoice, PurchaseOrder, Payment (filtered by contract)
Dimensions: Contract, metric type
Metrics: Fulfillment rate, on-time %, payment timeliness, disputes
Access: Owner/Admin (both tenants)
Notes: Partnership performance tracking
```

**34. Dispute & Adjustment Report**
```
Purpose: Outstanding disputes and adjustments between tenants
Frequency: Weekly/Monthly
Data Source: ApprovalRequest (disputed invoices), Adjustment records
Dimensions: Contract, dispute type, status (pending, resolved)
Metrics: Dispute count, total amount in dispute, resolution time
Access: Owner/Admin (both tenants)
Notes: Issue resolution tracking
```

---

### Category 7: Executive & Owner Dashboard

High-level business intelligence for ownership.

**35. Multi-Tenant Revenue Overview** (Multi-Property Owner)
```
Purpose: Revenue summary across all owned properties
Frequency: Daily
Data Source: Folio → GL (per tenant)
Dimensions: Property (tenant), revenue type
Metrics: Daily revenue, month-to-date, YTD, growth %
Access: Owner (all owned tenants)
Note: Requires ownership across multiple tenants
```

**36. Profitability by Business Unit**
```
Purpose: Profit/loss by operational unit
Frequency: Monthly
Data Source: GL (per tenant) - Revenue accounts, Expense accounts
Dimensions: Department/unit, property
Metrics: Revenue, COGS, operating expenses, profit, margin %
Access: Owner/Admin
Notes: Strategic decision support
```

**37. Subscription & Cost Overview**
```
Purpose: Current subscriptions and associated costs
Frequency: Monthly
Data Source: TenantApp (subscriptions), Billing records
Dimensions: App/module, tenant, billing status
Metrics: Active subscriptions, monthly cost, cost per module, renewal dates
Access: Owner/Admin
Notes: SaaS cost management
```

**38. Key Performance Indicators (KPI) Dashboard**
```
Purpose: Critical business metrics
Frequency: Real-time/Daily
Data Source: Folio, Invoice, Attendance, etc.
Metrics (configurable):
  - Revenue metrics (daily, monthly, YTD)
  - Occupancy %, ADR, RevPAR
  - Guest satisfaction score
  - Labor cost %
  - Cash position
Access: Owner/Admin
Notes: Executive decision support
```

---

### Category 8: System & Audit Reports

**39. Data Sync & Import Report**
```
Purpose: Track data imports and sync operations
Frequency: On-demand
Data Source: AuditLog (import actions)
Dimensions: Import date, source system, record count, status
Metrics: Records imported, succeeded, failed, errors
Access: Admin
Notes: Data integrity verification
```

**40. Access & Audit Log Report**
```
Purpose: Who accessed what and when
Frequency: On-demand
Data Source: AuditLog
Dimensions: User, action, entity type, date, result
Metrics: Action count, user activity
Filters: Date range, user, entity type
Access: Owner/Admin
Notes: Compliance, security monitoring
```

**41. Error & Exception Report**
```
Purpose: System errors and exceptions during period
Frequency: Daily
Data Source: AuditLog (failed actions), Error logs
Dimensions: Error type, module, severity, date
Metrics: Error count, affected records, resolution status
Access: Admin
Notes: System health monitoring
```

---

## Report Governance

### Access Control

All reports follow tenant-scoped RBAC:

| Role | PMS Reports | Accounting Reports | Procurement Reports | Executive Reports |
|------|-------------|-------------------|-------------------|------------------|
| Guest | ❌ | ❌ | ❌ | ❌ |
| Staff | ✅ Limited | ❌ | ❌ | ❌ |
| Admin | ✅ Full | ✅ Full | ✅ Full | ✅ Limited |
| Owner | ✅ Full | ✅ Full | ✅ Full | ✅ Full |

**Rules**:
- Tenant isolation: Cannot view other tenant's reports
- Role-based: Specific reports require specific roles
- Period-based: Closed periods = view-only, no edits

---

### Data Currency & Latency

| Report Category | Latency | Update Frequency |
|---|---|---|
| Operational (occupancy, guest list) | Real-time to 1 hour | Every transaction |
| Daily operations (revenue, night audit) | Daily (post-close) | Daily |
| Accounting (GL, statements) | Daily (post-GL posting) | Nightly |
| AR/AP aging | Daily | Daily |
| Executive dashboards | Daily | Daily |
| Audit reports | On-demand | Immediate |

---

### Period Control

```
Open Period:
  ✅ Reports available for viewing
  ✅ New data can be posted
  ✅ Can adjust current period data

Locked Period:
  ✅ Reports available for viewing
  ❌ Cannot post new data
  ✅ Can view historical data
  ❌ Cannot adjust past data

Closed Period:
  ✅ Reports view-only (snapshot)
  ❌ No modifications allowed
  ✅ Archived for compliance
```

---

### Report Export & Distribution

**Allowed Formats**:
- CSV (raw data export)
- Excel (formatted)
- PDF (snapshot, signed)

**Governance**:
- Export = snapshot at export time
- Not live query (point-in-time)
- Audit logged (who exported, when)
- Sensitive data masked if requested

---

## Data Requirements for Reports

### Read Models (CQRS Projections)

To support efficient reporting without OLTP overhead:

| Report Group | Read Model Required |
|---|---|
| PMS Daily Operations | Daily snapshot of Folio status |
| Revenue reports | Daily GL posting summary |
| AR/AP Aging | Real-time Invoice + Payment join |
| Executive KPI | Daily aggregate metrics |

**Implementation Pattern**:
1. OLTP system processes transactions (create folio, post GL)
2. Event published (GuestCheckedOut, InvoiceFinalized)
3. Read model handler subscribes
4. Projection updated asynchronously
5. Report queries against read model

---

## Cross-Tenant Reporting Rules

### Requirements for Cross-Tenant Report

✅ **Can create if**:
- BusinessContract exists between tenants
- Both tenants have agreed to data sharing
- Report is explicitly listed in contract terms

❌ **Cannot create if**:
- No BusinessContract
- One tenant hasn't authorized
- Report exposes confidential data beyond contract scope

### Example: Hotel + Supplier Invoice Reconciliation

```
Prerequisites:
- BusinessContract (hotel.id, supplier.id) exists
- Status = 'active'
- Contract includes: "Invoice reconciliation report allowed"

Implementation:
SELECT h.invoice_id, h.amount as hotel_ap,
       s.invoice_id, s.amount as supplier_ar
FROM hotel.invoices h
  JOIN public.business_contracts bc ON bc.buyer_tenant_id = h.tenant_id
  JOIN supplier.invoices s ON s.tenant_id = bc.seller_tenant_id
WHERE h.counterparty_tenant_id = s.tenant_id
  AND h.contract_id = bc.id
  AND h.tenant_id = $hotel_tenant_id
  AND s.tenant_id = $supplier_tenant_id;
```

---

## Compliance Checklist

When creating a new report:

- [ ] Report mapped in this document
- [ ] Data source identified (OLTP table or read model)
- [ ] Access control defined (which roles can view)
- [ ] Frequency documented (real-time, daily, on-demand)
- [ ] Period control specified (open, locked, closed periods)
- [ ] Accounting reports: sourced from GL only
- [ ] Cross-tenant reports: BusinessContract verified
- [ ] Test data prepared for UAT
- [ ] Documentation written (what report shows, how to interpret)
- [ ] Export functionality tested (CSV, Excel, PDF)
- [ ] Performance tested (< 5 second load time for typical queries)

---

## Related Documents

- **REF-03**: Module Catalog — What modules produce operational data
- **REF-05**: Core Concepts — Tenant, User, Membership context
- **REF-08**: Entity Relationship Model — Data structure for reports
- **ARCH-07**: Design Patterns & Concepts — CQRS/Read Models
- **SPEC-07**: Use Cases — What users need to do with reports
- **SEC-03**: Authorization, Approval & Audit — Access control for reports
- **STD-17**: Logging & Observability — Audit log data for compliance reports
