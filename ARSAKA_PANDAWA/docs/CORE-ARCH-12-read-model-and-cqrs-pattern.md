# ARCH-12: Read Model & CQRS Pattern

This document describes the **Command Query Responsibility Segregation (CQRS)** pattern used in ARSAKA_PANDAWA. CQRS separates the write path (commands) from the read path (queries), optimizing each independently.

**Core Principle**: *Commands and queries have different requirements. Optimize each separately: normalized writes for consistency, denormalized reads for performance.*

---

## Why CQRS Architecture

### Problems CQRS Solves

**Without CQRS** (single model for read/write):
- Complex joins needed for every report query
- Reporting queries slow down transactional system
- Scaling reads means scaling writes (inefficient)
- Single schema can't optimize for both transactions and queries

**With CQRS**:
- Write model optimized for consistency and validation
- Read models optimized for specific queries
- Independent scaling (more read replicas)
- Complex reports don't impact transactions

### Benefits

| Benefit | How Achieved |
|---------|-------------|
| **Fast Reporting** | Denormalized read models, pre-aggregated data |
| **Transaction Consistency** | Normalized write model with strict validation |
| **Independent Scaling** | Read replicas scale separately from writes |
| **Audit Trail** | Events are immutable source of truth |
| **Flexibility** | New read models added without changing writes |
| **Data Recovery** | Rebuild read models from event log |

---

## CQRS Principles (Locked)

### Principle 1: Write Model ≠ Read Model
```
Write model (normalized): optimized for data entry, consistency, validation
Read model (denormalized): optimized for queries, reports, UI
They are two different schemas serving different purposes.
```

### Principle 2: Write Model = Source of Truth
```
Write model is the only source of truth for the system.
All writes go through write model.
Write model enforces all business rules and constraints.
```

### Principle 3: Read Model = Event-Driven Projection
```
Read model is derived from write model via events.
NOT a copy of write model.
Denormalized, pre-aggregated, optimized for specific queries.
```

### Principle 4: Read Model Can Be Redundant
```
Multiple read models can exist for same domain.
Different read models serve different query patterns.
Redundancy is OK (normalization is not a goal for reads).
```

### Principle 5: No Business Logic in Read Model
```
Read models are projections only.
NO validation, NO calculations, NO side effects.
All business logic stays in write model.
```

---

## Write Model (Transactional)

The write path: where data is created and modified.

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Structure** | Normalized (3NF or higher) |
| **Update Pattern** | Direct database updates or event sourcing |
| **Validation** | Strict (all rules enforced) |
| **Consistency** | Strong (ACID transactions) |
| **Scope** | Tenant-isolated |
| **Immutability** | Financial tables append-only |

### Example: Write Model for Invoicing

```sql
-- Write Model (Normalized)

CREATE TABLE invoices (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  invoice_number VARCHAR NOT NULL,
  type ENUM ('AR', 'AP'),
  amount DECIMAL(18,2) NOT NULL,
  status ENUM ('draft', 'issued', 'paid', 'voided'),
  created_at TIMESTAMP,
  issued_at TIMESTAMP,
  paid_at TIMESTAMP
);

CREATE TABLE invoice_line_items (
  id UUID PRIMARY KEY,
  invoice_id UUID FK,
  description VARCHAR,
  amount DECIMAL(18,2)
);

CREATE TABLE payments (
  id UUID PRIMARY KEY,
  invoice_id UUID FK,
  amount DECIMAL(18,2),
  payment_date TIMESTAMP
);

-- Every UPDATE publishes event:
-- Invoice.Finalized.v1, Payment.Recorded.v1, etc.
```

### Business Rules Enforced in Write Model

✅ **Rules enforced**:
- Amount > 0
- Valid invoice type (AR or AP)
- Cannot delete posted invoice
- Cannot pay more than invoice amount
- Payment date must be ≥ invoice date
- Only 1 role per user per tenant
- tenant_id never changes

---

## Read Model (Projection)

The read path: optimized views for querying and reporting.

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Structure** | Denormalized (data joined and aggregated) |
| **Update Pattern** | Event-driven projections |
| **Validation** | None (trust write model) |
| **Consistency** | Eventual (may be slightly out of sync) |
| **Scope** | Tenant-isolated |
| **Query Pattern** | Single-table queries, fast |

### Example: Read Model for AR Aging

```sql
-- Read Model (Denormalized for reporting)

CREATE TABLE ar_aging_report (
  tenant_id UUID,
  customer_tenant_id UUID,  -- For inter-tenant
  invoice_id UUID,
  invoice_number VARCHAR,
  invoice_date DATE,
  due_date DATE,
  outstanding_amount DECIMAL(18,2),
  days_overdue INT,
  aging_bucket VARCHAR ('0-30', '31-60', '61-90', '90+'),
  last_updated TIMESTAMP
);

-- Query is simple (one table, no joins):
SELECT * FROM ar_aging_report
WHERE tenant_id = $1
  AND aging_bucket = '90+'
ORDER BY days_overdue DESC;

-- Result: fast, pre-calculated, ready for display
```

**Note**: This table is built from events, not directly updated.

---

## Projection Flow (Event-Driven)

How write model changes flow to read models:

```
┌──────────────────┐
│  Write Model     │
│  (normalized)    │
│                  │
│ POST /invoices   │
└────────┬─────────┘
         │
         │ 1. Create/update record
         │
         ▼
┌──────────────────┐
│  Event Published │
│                  │
│ Invoice.         │
│ Finalized.v1     │
└────────┬─────────┘
         │
         │ 2. Immutable event stored
         │
         ▼
┌──────────────────┐
│ Event Broker     │
│ (RabbitMQ)       │
└────────┬─────────┘
         │
         │ 3. Distribute to subscribers
         │
         ▼
┌──────────────────────────────────────┐
│ Projection Handlers                  │
│ (event consumers)                    │
│                                      │
│ Handler: AR Aging                    │
│ Handler: Revenue Summary             │
│ Handler: GL Posting                  │
└────────┬─────────────────────────────┘
         │
         │ 4. Idempotent update
         │
         ▼
┌────────────────────────────────────────┐
│ Read Models                            │
│ (denormalized views)                   │
│                                        │
│ ar_aging_report                        │
│ daily_revenue_summary                  │
│ journal_entry (GL posting)             │
└────────────────────────────────────────┘
```

### Idempotency Requirement

```typescript
// Projection handler MUST be idempotent
// (can be called multiple times with same event)

async function handleInvoiceFinalizedEvent(event) {
  // 1. Check if already processed
  const alreadyProcessed = await db.query(
    'SELECT * FROM ar_aging_report WHERE invoice_id = $1',
    [event.payload.invoice_id]
  );

  if (alreadyProcessed) {
    return;  // Skip if already projected
  }

  // 2. Insert/update read model
  await db.query(`
    INSERT INTO ar_aging_report (invoice_id, amount, aging_bucket, ...)
    VALUES ($1, $2, $3, ...)
    ON CONFLICT (invoice_id) DO UPDATE SET ...
  `, [event.payload.invoice_id, event.payload.amount, ...]);

  // 3. Mark as processed
  await db.query(
    'INSERT INTO projection_checkpoint (event_id) VALUES ($1)',
    [event.event_id]
  );
}
```

---

## Read Model Examples

### Example 1: AR Aging Report

**Purpose**: Show customer invoices by age (current, 30-60 days, etc.)

**Source Events**:
- `Accounting.Invoice.Finalized.v1`
- `Accounting.Payment.Recorded.v1`

**Projection**:
```typescript
async function projectARAgingReport(event) {
  if (event.event_type === 'Invoice.Finalized.v1') {
    // Add invoice to aging report
    const daysOverdue = calculateDaysOverdue(event.payload.due_date);
    const bucket = getAgingBucket(daysOverdue);

    await db.query(`
      INSERT INTO ar_aging_report
      (tenant_id, invoice_id, invoice_number, amount, aging_bucket, days_overdue, last_updated)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
      ON CONFLICT (invoice_id) DO UPDATE SET
        days_overdue = EXCLUDED.days_overdue,
        aging_bucket = EXCLUDED.aging_bucket,
        last_updated = NOW()
    `, [event.tenant_id, event.payload.invoice_id, ...]);
  }

  if (event.event_type === 'Payment.Recorded.v1') {
    // Update invoice as partially/fully paid
    const invoice = await db.query(
      'SELECT * FROM invoices WHERE id = $1',
      [event.payload.invoice_id]
    );
    const outstanding = invoice.amount - event.payload.amount;

    await db.query(`
      UPDATE ar_aging_report
      SET outstanding_amount = $1,
          aging_bucket = CASE WHEN outstanding > 0 THEN '0-30' ELSE 'paid' END
      WHERE invoice_id = $2
    `, [outstanding, event.payload.invoice_id]);
  }
}
```

**Result**: Single-table query for reporting
```sql
SELECT * FROM ar_aging_report
WHERE tenant_id = 'hotel-jakarta'
  AND aging_bucket = '90+'
ORDER BY days_overdue DESC;
```

---

### Example 2: Occupancy Snapshot

**Purpose**: Daily occupancy summary by room type

**Source Events**:
- `PMS.Guest.CheckedIn.v1`
- `PMS.Guest.CheckedOut.v1`

**Projection**:
```typescript
async function projectOccupancySnapshot(event) {
  if (event.event_type === 'Guest.CheckedIn.v1') {
    // Increment occupied count for room type
    const { room_type, room_id } = event.payload;
    const today = new Date().toISOString().split('T')[0];

    await db.query(`
      INSERT INTO occupancy_snapshot (tenant_id, date, room_type, occupied_count)
      VALUES ($1, $2, $3, 1)
      ON CONFLICT (tenant_id, date, room_type) DO UPDATE SET
        occupied_count = occupied_count + 1
    `, [event.tenant_id, today, room_type]);
  }

  if (event.event_type === 'Guest.CheckedOut.v1') {
    // Decrement occupied count
    const { room_type } = event.payload;
    const today = new Date().toISOString().split('T')[0];

    await db.query(`
      UPDATE occupancy_snapshot
      SET occupied_count = GREATEST(0, occupied_count - 1)
      WHERE tenant_id = $1 AND date = $2 AND room_type = $3
    `, [event.tenant_id, today, room_type]);
  }
}
```

**Result**: Fast occupancy queries
```sql
SELECT date, room_type, occupied_count, total_rooms,
       ROUND(occupied_count * 100.0 / total_rooms, 2) as occupancy_pct
FROM occupancy_snapshot
WHERE tenant_id = 'hotel-jakarta' AND date = CURRENT_DATE;
```

---

### Example 3: Daily Revenue Summary

**Purpose**: Revenue aggregation by date

**Source Events**:
- `Accounting.Journal.Posted.v1` (filtered for revenue accounts)

**Projection**:
```typescript
async function projectRevenueSnapshot(event) {
  if (event.event_type === 'Journal.Posted.v1') {
    const { tenant_id, payload } = event;
    const entryDate = payload.entry_date;

    // Only track revenue account postings
    const revenueLines = payload.lines.filter(
      line => line.account_type === 'revenue'
    );

    if (revenueLines.length > 0) {
      const totalRevenue = revenueLines.reduce(
        (sum, line) => sum + (line.credit || 0),
        0
      );

      await db.query(`
        INSERT INTO daily_revenue_summary (tenant_id, date, amount)
        VALUES ($1, $2, $3)
        ON CONFLICT (tenant_id, date) DO UPDATE SET
          amount = amount + EXCLUDED.amount
      `, [tenant_id, entryDate, totalRevenue]);
    }
  }
}
```

**Result**: Simple revenue queries
```sql
SELECT date, amount, SUM(amount) OVER (ORDER BY date) as ytd_revenue
FROM daily_revenue_summary
WHERE tenant_id = 'hotel-jakarta'
  AND date >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY date;
```

---

## Cross-Tenant Read Models

Read models for multi-tenant queries (supplier-hotel reconciliation, etc.)

### Rules

✅ **Can create cross-tenant read model if**:
- BusinessContract exists between tenants
- Contract explicitly allows data sharing
- Data filtered by contract_id

❌ **Cannot create if**:
- No contract
- One tenant hasn't authorized
- Would expose confidential data

### Example: Inter-Tenant Invoice Reconciliation

```sql
-- Read Model (cross-tenant, filtered by contract)

CREATE TABLE invoice_reconciliation_report (
  contract_id UUID,
  buyer_tenant_id UUID,
  seller_tenant_id UUID,
  buyer_invoice_id UUID,
  seller_invoice_id UUID,
  buyer_amount DECIMAL,
  seller_amount DECIMAL,
  variance DECIMAL,
  match_status ENUM ('matched', 'unmatched', 'disputed'),
  last_updated TIMESTAMP
);

-- Query only shows data for authorized contract
SELECT * FROM invoice_reconciliation_report
WHERE contract_id = $1
  AND (buyer_tenant_id = $2 OR seller_tenant_id = $2);
```

---

## Storage Strategies

Different storage technologies for read models depending on needs:

### Option 1: PostgreSQL (Denormalized Table)

**Use when**:
- Query patterns well-defined
- Data volume < 10GB
- ACID consistency needed

**Advantages**:
- Single database (simpler ops)
- ACID transactions
- Standard SQL queries

**Disadvantages**:
- Less flexible than others
- Not optimized for full-text search

**Example**: ar_aging_report, daily_revenue_summary

---

### Option 2: Elasticsearch (Search & Analytics)

**Use when**:
- Full-text search needed
- Large data volume (100GB+)
- Ad-hoc queries/filtering
- Time-series analytics

**Advantages**:
- Fast full-text search
- Powerful aggregations
- Scales horizontally

**Disadvantages**:
- Separate cluster to maintain
- Eventual consistency
- More complex

**Example**: Guest search (by name, email, phone), Audit log search

---

### Option 3: Redis (Hot Cache)

**Use when**:
- Sub-millisecond response needed
- High-frequency queries
- Real-time dashboards
- Small dataset

**Advantages**:
- Extremely fast
- Supports lists, sets, sorted sets
- Good for counters, leaderboards

**Disadvantages**:
- Limited query flexibility
- All data in memory
- Single-node or replication complexity

**Example**: Current occupancy counter, session cache, user preferences

---

## Consistency Model

### Strong vs Eventual Consistency

**Write model**: Strong consistency
```
POST /api/v1/invoices
  ↓ (immediately)
Invoice in database ✅
All business rules validated ✅
Response sent to user ✅
```

**Read models**: Eventual consistency
```
Invoice.Finalized event published
  ↓ (milliseconds to seconds delay)
Event handler processes
  ↓
ar_aging_report updated
  ↓
Query sees new data
```

### Acceptable Latency (SLA for Each Read Model)

| Read Model | Category | Max Acceptable Latency | Trigger | Reason |
|-----------|----------|----------------------|---------|--------|
| Occupancy snapshot (operational) | Real-time | < 5 seconds | RoomStatus.Changed | Hotel staff needs immediate view |
| Revenue summary (daily reporting) | Daily | < 1 minute | Invoice.Finalized | Hotel managers check revenue frequently |
| AR aging (monthly close) | Monthly | < 1 hour | Payment.Recorded | Monthly reconciliation, not time-critical |
| Audit log search (compliance) | Compliance | < 5 minutes | Any sensitive action | Investigators need access within session |

**Latency Implementation**:
- **Real-time (< 5s)**: Use in-memory cache + WebSocket updates, rebuild every 5s
- **Operational (< 1m)**: Use database projections, background job every 30-60s
- **Reporting (< 1h)**: Use batch jobs, can run overnight or during low-traffic hours
- **Compliance (< 5m)**: Use event log direct search if projection too slow

**Monitoring**:
- Track projection lag for each read model
- Alert if lag exceeds SLA threshold
- Log slow projections for optimization

---

## Failure & Recovery

### Scenario: Read Model Falls Behind

**Cause**: Projection handler crashes, message broker down, etc.

**Recovery**:
```
1. Identify problem (lag monitoring alert)
2. Restart projection handler
3. Handler replays events from last checkpoint
4. Read model catches up automatically
```

### Scenario: Read Model Corrupted

**Recovery Options**:
1. **Rebuild from scratch** (if event log intact):
```typescript
async function rebuildARAgingReport() {
  // 1. Truncate read model
  await db.query('TRUNCATE ar_aging_report');

  // 2. Replay all events from event log
  const events = await db.query(
    'SELECT * FROM event_log WHERE event_type IN (\'Invoice.Finalized\', \'Payment.Recorded\') ORDER BY occurred_at'
  );

  // 3. Re-project each event
  for (const event of events) {
    await handleInvoiceEvent(event);
  }

  console.log(`Rebuilt ar_aging_report with ${events.length} events`);
}
```

2. **Partial rebuild** (if specific date range corrupted):
```typescript
async function rebuildFromDate(startDate) {
  // Delete projections for date range
  await db.query(
    'DELETE FROM ar_aging_report WHERE last_updated >= $1',
    [startDate]
  );

  // Re-project events from that date forward
  const events = await db.query(
    'SELECT * FROM event_log WHERE occurred_at >= $1 ORDER BY occurred_at',
    [startDate]
  );

  for (const event of events) {
    await handleInvoiceEvent(event);
  }
}
```

### Key Point: Read Models Rebuilding Doesn't Affect Writes

Write model (source of truth) is never affected by read model corruption. Only read models need rebuilding.

---

## Anti-Patterns (Forbidden)

### ❌ Anti-Pattern 1: Query Write Model for Reports

```typescript
// WRONG: Direct query on write model
const query = `
  SELECT i.id, i.amount, SUM(p.amount) as paid
  FROM invoices i
  LEFT JOIN payments p ON i.id = p.invoice_id
  WHERE i.tenant_id = $1
    AND i.status = 'issued'
  GROUP BY i.id
`;

// RIGHT: Query pre-built read model
const query = `
  SELECT invoice_id, amount, outstanding_amount
  FROM ar_aging_report
  WHERE tenant_id = $1
    AND aging_bucket = '0-30'
`;
```

**Consequence**: Slow reports, impact on transactional system

---

### ❌ Anti-Pattern 2: Business Logic in Read Model

```typescript
// WRONG: Calculating approval threshold in projection
async function projectApprovalRead(event) {
  const threshold = 5000000;
  if (event.amount > threshold) {
    // Logic here: determine who approves, send notification
    // DON'T DO THIS
  }
}

// RIGHT: Projection is dumb, logic in write model
async function projectApprovalRead(event) {
  // Just record the data as-is
  await db.query(`
    INSERT INTO approval_read_model (invoice_id, amount, required_approver)
    VALUES ($1, $2, $3)
  `, [event.invoice_id, event.amount, event.required_approver]);
}
```

**Consequence**: Duplicate logic, hard to test, inconsistency

---

### ❌ Anti-Pattern 3: Updating Financial Data from Read Model

```typescript
// WRONG: Treating read model as source of truth
app.post('/api/invoices/:id/write-off', (req, res) => {
  // Updating read model (WRONG!)
  db.query('UPDATE ar_aging_report SET amount = 0 WHERE invoice_id = $1', [id]);
});

// RIGHT: All writes go through write model with validation
app.post('/api/invoices/:id/write-off', (req, res) => {
  // Write to write model (validated)
  const result = db.transaction(async () => {
    const invoice = await db.getInvoice(id);
    if (invoice.status === 'issued') {
      await invoice.markWrittenOff();
      await publishEvent({ event_type: 'Invoice.WrittenOff.v1', ... });
    }
  });
});
```

**Consequence**: Financial data corruption, audit trail gaps

---

## Implementation Patterns

### Pattern 1: Event Handler Projection

```typescript
// Subscribe to events and update read models

const eventBroker = new EventBroker();

eventBroker.subscribe('Invoice.Finalized.v1', async (event) => {
  const { tenant_id, payload } = event;

  // Calculate aging bucket
  const daysOverdue = Math.floor(
    (Date.now() - new Date(payload.due_date)) / (1000 * 60 * 60 * 24)
  );
  const bucket = daysOverdue <= 30 ? '0-30'
               : daysOverdue <= 60 ? '31-60'
               : daysOverdue <= 90 ? '61-90'
               : '90+';

  // Upsert into read model
  await db.query(`
    INSERT INTO ar_aging_report
    (tenant_id, invoice_id, invoice_number, amount, days_overdue, aging_bucket, last_updated)
    VALUES ($1, $2, $3, $4, $5, $6, NOW())
    ON CONFLICT (invoice_id) DO UPDATE SET
      days_overdue = EXCLUDED.days_overdue,
      aging_bucket = EXCLUDED.aging_bucket,
      last_updated = NOW()
  `, [tenant_id, payload.invoice_id, payload.invoice_number, payload.amount, daysOverdue, bucket]);

  // Record projection checkpoint
  await db.query(
    'INSERT INTO projection_checkpoint (event_id, model_name, processed_at) VALUES ($1, $2, NOW())',
    [event.event_id, 'ar_aging_report']
  );
});

// Handle errors with retry + dead-letter queue
eventBroker.onError(async (event, error) => {
  console.error(`Failed to project ${event.event_type}:`, error);
  await deadLetterQueue.push(event);
  // Alert ops team
});
```

### Pattern 2: Batch Projection (Nightly)

```typescript
// For read models that don't need real-time, rebuild nightly

async function rebuildDailyRevenueSnapshot() {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = yesterday.toISOString().split('T')[0];

  // Truncate yesterday's data
  await db.query(
    'DELETE FROM daily_revenue_summary WHERE date = $1',
    [dateStr]
  );

  // Re-aggregate from GL
  const revenues = await db.query(`
    SELECT i.tenant_id, j.entry_date, SUM(jl.credit) as revenue
    FROM journal_entries j
    JOIN journal_lines jl ON j.id = jl.journal_entry_id
    JOIN chart_of_accounts coa ON jl.account_id = coa.id
    WHERE j.entry_date = $1
      AND coa.type = 'revenue'
    GROUP BY i.tenant_id, j.entry_date
  `, [dateStr]);

  // Insert into read model
  for (const row of revenues) {
    await db.query(`
      INSERT INTO daily_revenue_summary (tenant_id, date, amount)
      VALUES ($1, $2, $3)
    `, [row.tenant_id, row.entry_date, row.revenue]);
  }
}

// Schedule nightly
schedule.scheduleJob('0 1 * * *', rebuildDailyRevenueSnapshot);
```

---

## Monitoring & Observability

### Metrics to Track

| Metric | Why | Alert If |
|--------|-----|----------|
| Projection lag | How behind are read models | > 1 minute |
| Handler errors | Projection failures | Any error |
| Rebuild time | How long to rebuild read model | > 5 minutes |
| Read model size | Storage usage | > threshold |
| Query latency (read model) | User experience | > 1 second |

### Dashboards

```
Projection Health
├─ Lag by read model (occupancy, ar_aging, etc.)
├─ Error rate (per handler)
├─ Last successful projection (per model)
└─ Rebuild history (when/how long)

Read Model Performance
├─ Query latency (p50, p95, p99)
├─ Data freshness (last updated timestamp)
├─ Storage size (per model)
└─ Error rate (per query)
```

---

## Compliance Checklist

When designing a read model:

- [ ] Purpose clearly defined (what queries does it serve)
- [ ] Source events identified
- [ ] Projection logic designed (idempotent handler)
- [ ] Storage technology chosen (PostgreSQL/Elasticsearch/Redis)
- [ ] Consistency requirement understood (strong vs eventual)
- [ ] Lag tolerance defined (max acceptable latency)
- [ ] Cross-tenant rule verified (if applicable)
- [ ] Rebuild strategy documented
- [ ] Error handling (retries, dead-letter queue)
- [ ] Monitoring configured (lag, errors, performance)
- [ ] Tests written (event → projection → query)
- [ ] Documentation updated (schema, purpose, refresh frequency)

---

## Related Documents

- **ARCH-10**: Event-Driven Architecture — Events feed projections
- **REF-08**: Entity Relationship Model — Write model structure
- **REF-09**: Report Map — What read models are needed
- **ARCH-07**: Design Patterns & Concepts — CQRS as design pattern
- **STD-19**: Event Contract Standard — Events that trigger projections
- **GUIDE-06**: Reporting & BI Guide — How to query read models
