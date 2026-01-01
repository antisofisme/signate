# Caching & Performance Contradictions Analysis

**Analysis Date:** 2025-12-07
**Scope:** Development Standards vs Business Accounting Standards
**Focus:** Caching Strategy, Real-time Requirements, Performance Optimization

---

## Executive Summary

This analysis identifies **5 critical contradictions** between Development Standards (V1/V2) and Business Accounting Standards (V1/V2) regarding caching and performance requirements. The main issue is that Development Standards provide generic caching rules ("don't cache transaction data") while Accounting Standards demand specific real-time capabilities for financial data that requires sophisticated caching strategies.

### Severity Assessment

| Issue | Severity | Impact | Performance Risk |
|-------|----------|--------|------------------|
| 1. Trial Balance Real-time Requirement | 🔴 CRITICAL | High | Cache invalidation storm |
| 2. Journal/Invoice List Caching | 🟡 MEDIUM | Medium | Memory overhead |
| 3. Period Status Cache Invalidation | 🔴 CRITICAL | High | Data consistency |
| 4. Bank Reconciliation Freshness | 🟠 HIGH | Medium | User experience |
| 5. TimescaleDB Continuous Aggregates | 🟡 MEDIUM | Medium | Query performance |

---

## 1. What to Cache - CRITICAL CONTRADICTION

### Development Standards Says:

```yaml
# From DEVELOPMENT_STANDARDS.md - Section 5.4
JANGAN Cache:
  - Realtime data (availability, occupancy)
  - Data sensitif (password, tokens)
  - Data transaction (journals, folios aktif)  # ⚠️ PROBLEM
```

**TTL Strategy:**
- Platform Cache: Session (24hr), User profile (15min)
- Organization Cache: Settings (1hr), Permissions (15min), Roles (1hr)
- App Cache: List queries (5min), Single entity (15min)

### Accounting Standards Says:

**FROM BUSINESS_ACCOUNTING_STANDARDS.md:**

```yaml
Need to Cache (CONTRADICTS Development Standards):
  - Journal lists (for period closing workflow)
  - Invoice lists (AR/AP aging reports)
  - Trial Balance (comparative reports)
  - Bank reconciliation matches (semi-auto mode)
  - Consolidated trial balance (multi-entity)
  - Report line mappings (PSAK/USALI reports)
```

### CONTRADICTION DETAILS:

#### A. Journal Lists - Grey Area

**Development says:** "Don't cache transaction data"
**Accounting needs:** Journal entry lists for period closing checklist

```sql
-- Query yang dijalankan SERING during period closing:
SELECT * FROM journal_entries
WHERE organization_id = ?
  AND period_year = ?
  AND period_month = ?
  AND status = 'posted'
ORDER BY entry_date DESC;
```

**Performance Impact:**
- Volume: ~1,245 journals/month (per BUSINESS_ACCOUNTING_STANDARDS.md example)
- Frequency: Viewed 50+ times during month-end closing (multiple users)
- Without cache: 50 x DB roundtrip = high latency
- With cache (5min TTL): 1-2 DB queries during 4-hour closing window

**Recommendation:**
```yaml
Cache Strategy: HYBRID
  - Cache journal LISTS with short TTL (1-2 minutes)
  - NEVER cache individual journal data
  - Invalidate on: CREATE/UPDATE/DELETE/RESTORE journal
  - Scope: org:{org_id}:accounting:journals:list:{period_year}:{period_month}
  - TTL: 2 minutes (balance freshness vs DB load)
```

#### B. Invoice Lists (AR/AP) - Complex Case

**Development says:** "Don't cache transaction data"
**Accounting needs:** Invoice lists for aging reports

```sql
-- AR Aging Report Query (EXPENSIVE):
SELECT
  customer_id,
  invoice_number,
  invoice_date,
  due_date,
  total_amount,
  paid_amount,
  CASE
    WHEN days_overdue <= 0 THEN 'current'
    WHEN days_overdue <= 30 THEN '1-30'
    WHEN days_overdue <= 60 THEN '31-60'
    WHEN days_overdue <= 90 THEN '61-90'
    ELSE '>90'
  END as aging_bucket
FROM ar_invoices
WHERE organization_id = ?
  AND status IN ('open', 'partial')
ORDER BY customer_id, invoice_date;
```

**Performance Impact:**
- Volume: ~500 invoices/month (average hospitality property)
- Calculation overhead: Aging bucket computation for each row
- Query time: ~200-500ms (without cache)
- Report generation: 10-20 times/day by AR team

**Recommendation:**
```yaml
Cache Strategy: COMPUTED RESULT CACHE
  - Cache aging report RESULT, not raw invoice data
  - Key: org:{org_id}:accounting:ar_aging:report:{as_of_date}
  - TTL: 15 minutes (acceptable staleness for management reports)
  - Invalidate on: Payment received, Invoice created/updated
  - Note: Raw invoice queries BYPASS cache (for data entry)
```

#### C. Trial Balance - CRITICAL REAL-TIME REQUIREMENT

**Development says:** "Don't cache transaction data"
**Accounting requires:** Trial Balance MUST be real-time (no cache allowed)

**FROM BUSINESS_ACCOUNTING_STANDARDS.md - Section 5.4:**
```
Closing Checklist:
[✓] Trial Balance Review - Completed by: CFO
```

**Why Real-time is MANDATORY:**
- Debit = Credit verification (accounting fundamental)
- Detects posting errors immediately
- Required before financial statement generation
- Period closing cannot proceed without accurate TB

**Performance Challenge:**
```sql
-- Trial Balance Query (COMPLEX):
SELECT
  account_id,
  account_code,
  account_name,
  SUM(CASE WHEN debit_credit = 'debit' THEN amount ELSE 0 END) as total_debit,
  SUM(CASE WHEN debit_credit = 'credit' THEN amount ELSE 0 END) as total_credit,
  SUM(CASE WHEN debit_credit = 'debit' THEN amount
           ELSE -amount END) as net_balance
FROM journal_entries je
JOIN journal_lines jl ON je.id = jl.journal_entry_id
WHERE je.organization_id = ?
  AND je.period_year = ?
  AND je.period_month = ?
  AND je.status = 'posted'
GROUP BY account_id, account_code, account_name
ORDER BY account_code;
```

**Estimated Query Time:**
- 1,000 journals x 3 lines avg = 3,000 rows to aggregate
- With proper indexes: 100-300ms
- Without indexes: 2-5 seconds ⚠️

**Recommendation:**
```yaml
Solution: TIMESCALEDB CONTINUOUS AGGREGATE (NOT Redis Cache)
  - Use TimescaleDB materialized view (real-time refresh)
  - Refresh on every journal POST (event-driven)
  - Zero staleness (always accurate)
  - Query time: <50ms (pre-aggregated)
  - No cache invalidation complexity
```

```sql
-- Continuous Aggregate for Trial Balance
CREATE MATERIALIZED VIEW accounting.trial_balance_monthly
WITH (timescaledb.continuous, timescaledb.materialized_only=false) AS
SELECT
  organization_id,
  period_year,
  period_month,
  account_id,
  SUM(CASE WHEN debit_credit = 'debit' THEN amount ELSE 0 END) as total_debit,
  SUM(CASE WHEN debit_credit = 'credit' THEN amount ELSE 0 END) as total_credit
FROM journal_entries je
JOIN journal_lines jl ON je.id = jl.journal_entry_id
WHERE status = 'posted'
GROUP BY organization_id, period_year, period_month, account_id;

-- Refresh policy: Every time journal is posted
SELECT add_continuous_aggregate_policy('trial_balance_monthly',
  start_offset => INTERVAL '1 month',
  end_offset => INTERVAL '0 seconds',
  schedule_interval => INTERVAL '1 minute'  -- Or event-driven trigger
);
```

---

## 2. TTL Strategy - Period Status Impact

### The Problem:

**Development Standards defines generic TTL:**
```yaml
Platform Cache:
  - User profile: 15 min
  - Session: 24 hr
Organization Cache:
  - Settings: 1 hr
  - Roles: 1 hr
  - Permissions: 15 min
App Cache:
  - List queries: 5 min
  - Single entity: 15 min
```

**Accounting Reality:**
TTL must be **context-aware** based on period status.

### Period Status Lifecycle:

```
OPEN → IN_CLOSING → CLOSED → REOPENED
  ↓        ↓           ↓          ↓
 5min    1min        ∞ (perm)   1min
```

### TTL Decision Matrix:

| Period Status | Journal Lists TTL | Invoice Lists TTL | Trial Balance | Rationale |
|---------------|-------------------|-------------------|---------------|-----------|
| **OPEN** | 5 min | 15 min | Real-time (0s) | Normal operations, balance freshness vs load |
| **IN_CLOSING** | 1 min | 5 min | Real-time (0s) | High activity, need fresh data for checklist |
| **CLOSED** | ∞ (permanent) | ∞ (permanent) | Cache forever | Immutable data, safe to cache indefinitely |
| **REOPENED** | 1 min | 2 min | Real-time (0s) | Exceptional case, need immediate visibility |

### Implementation Pattern:

```python
class AccountingCacheService:
    """Context-aware caching based on period status."""

    async def get_ttl_for_period(self, org_id: int, period_year: int, period_month: int) -> timedelta:
        """Determine TTL based on period status."""
        period = await self.period_repo.get_period(org_id, period_year, period_month)

        ttl_map = {
            PeriodStatus.OPEN: timedelta(minutes=5),
            PeriodStatus.IN_CLOSING: timedelta(minutes=1),
            PeriodStatus.CLOSED: timedelta(days=3650),  # 10 years = effectively permanent
            PeriodStatus.REOPENED: timedelta(minutes=1)
        }

        return ttl_map.get(period.status, timedelta(minutes=5))

    async def cache_journal_list(self, org_id: int, period_year: int, period_month: int, data: list):
        """Cache journal list with context-aware TTL."""
        key = f"org:{org_id}:accounting:journals:list:{period_year}:{period_month}"
        ttl = await self.get_ttl_for_period(org_id, period_year, period_month)

        await self.cache.set(key, data, ttl)
```

### CRITICAL INSIGHT:

**CLOSED period data is IMMUTABLE** - This is the secret to massive performance gains.

Once a period is CLOSED:
- No more journal entries allowed
- Trial balance is final
- Reports are frozen

**Cache Strategy for CLOSED periods:**
```yaml
What to Cache (Aggressively):
  - Trial balance: Cache forever (99% cache hit rate)
  - Financial statements: Cache forever
  - Aging reports: Cache as-of closing date
  - Journal lists: Cache full result set

Performance Impact:
  - Month 1 (OPEN): 70% cache hit
  - Month 2 (CLOSED): 99% cache hit (queried for comparisons)
  - Month 3+ (CLOSED): 99.9% cache hit (historical reports)

Result:
  - 90% reduction in database load for historical queries
  - Comparative reports load in <100ms (vs 2-5 seconds)
```

---

## 3. Cache Invalidation - Cross-Service Dependencies

### Development Standards Cache Invalidation Matrix:

```yaml
# From DEVELOPMENT_STANDARDS.md Section 5.1
CREATE → Invalidate LIST + RELATED
UPDATE → Invalidate ENTITY + LIST + RELATED
DELETE → Invalidate ENTITY + LIST + RELATED
Role change → Invalidate permission (all users with role)
User role change → Invalidate permission (user)
```

### Accounting-Specific Invalidation (MISSING from Development Standards):

#### A. Period Status Change Invalidation

**Trigger:** Period status changes from OPEN → IN_CLOSING

**Must Invalidate:**
```yaml
Direct Impact:
  - org:{org_id}:accounting:period:{year}:{month}
  - org:{org_id}:accounting:journals:list:{year}:{month}

Indirect Impact (OFTEN MISSED):
  - org:{org_id}:accounting:permissions:user:*  # UI permissions change!
  - org:{org_id}:pms:folios:new_charges_allowed  # PMS integration affected
  - org:{org_id}:accounting:closing_checklist:{year}:{month}
```

**Why UI Permissions?**
```javascript
// Frontend permission logic:
const canCreateJournal = computed(() => {
  if (currentPeriod.status === 'CLOSED') return false;  // ⚠️ Cached!
  return hasPermission('accounting.journal.create');
});
```

If period status is cached, users might still see "Create Journal" button even after period is closed!

#### B. Approval Status Invalidation

**Trigger:** Invoice approved (status: draft → approved)

**Must Invalidate:**
```yaml
Direct:
  - org:{org_id}:accounting:invoice:{invoice_id}
  - org:{org_id}:accounting:invoices:list

Indirect (CRITICAL):
  - org:{org_id}:accounting:ar_aging:report:*  # Aging bucket might change
  - org:{org_id}:accounting:dashboard:receivables  # KPI affected
  - org:{org_id}:accounting:customer:{customer_id}:balance  # Balance changes
```

**Performance Risk:**
Approval workflow might trigger 50+ invoice approvals in batch operation.

**Bad Invalidation:**
```python
# ❌ SLOW - Sequential invalidation
for invoice_id in approved_invoice_ids:
    await cache.delete(f"org:{org_id}:accounting:invoice:{invoice_id}")
    await cache.delete(f"org:{org_id}:accounting:invoices:list")  # DUPLICATE!
    await cache.delete_pattern(f"org:{org_id}:accounting:ar_aging:*")  # DUPLICATE!
```

**Good Invalidation:**
```python
# ✅ FAST - Batch invalidation with deduplication
invalidation_set = set()
for invoice_id in approved_invoice_ids:
    invalidation_set.add(f"org:{org_id}:accounting:invoice:{invoice_id}")

# Add common keys only once
invalidation_set.add(f"org:{org_id}:accounting:invoices:list")
invalidation_set.add(f"org:{org_id}:accounting:ar_aging:report:*")
invalidation_set.add(f"org:{org_id}:accounting:dashboard:receivables")

# Batch delete
await cache.delete_many(list(invalidation_set))
```

#### C. Cross-Service Cache Invalidation (PMS → Accounting)

**Scenario:** Guest checks out in PMS, folio posted to Accounting

**FROM BUSINESS_ACCOUNTING_STANDARDS_V2.md - Section 10.2:**
```yaml
Integration Mode: Real-time (setiap transaksi langsung create journal)
```

**Invalidation Flow:**
```
PMS Service                    Accounting Service
    │                              │
    ├─ Guest Check-out             │
    │   (folio_id=123)             │
    │                              │
    ├─ POST /accounting/           │
    │   integrate/folio-journal    │
    │                              │
    │                         ┌────▼─────┐
    │                         │ Create   │
    │                         │ Journal  │
    │                         └────┬─────┘
    │                              │
    │                         ┌────▼─────────────────────────┐
    │                         │ Cache Invalidation          │
    │                         ├─────────────────────────────┤
    │                         │ 1. Journals list            │
    │                         │ 2. Trial balance (refresh)  │
    │                         │ 3. Dashboard revenue        │
    │                         │ 4. GL account balance       │
    │                         └─────────────────────────────┘
    │                              │
    │◀─────────── Response ────────┤
    │   {journal_id: 456}          │
    │                              │
    ├─ Cache Invalidation (PMS)   │
    │  ├─ Folio cache              │
    │  ├─ Guest ledger list        │
    │  └─ Dashboard stats          │
```

**Problem:** Development Standards don't cover cross-service invalidation!

**Recommendation:**
```yaml
Add to DEVELOPMENT_STANDARDS.md Section 5:

5.9 Cross-Service Cache Invalidation

Pattern: Event-Driven Invalidation via Message Queue

When Service A triggers action that affects Service B cache:
  1. Service A publishes event to RabbitMQ
  2. Service B consumes event
  3. Service B invalidates own cache
  4. No direct cache coupling between services

Example:
  Event: folio.posted
  Payload: {folio_id, organization_id, total_amount, journal_id}
  Subscribers:
    - accounting-service (invalidate journal cache)
    - dashboard-service (invalidate KPI cache)
    - report-service (invalidate revenue cache)
```

---

## 4. Real-time Requirements - Performance Implications

### Accounting Data Freshness Requirements:

| Data Type | Staleness Tolerance | Current Strategy | Recommended Strategy |
|-----------|---------------------|------------------|----------------------|
| **Trial Balance** | 0 seconds (NONE) | ❌ Not specified | ✅ TimescaleDB Continuous Aggregate |
| **Bank Reconciliation Matches** | 5 minutes | ❌ Not specified | ✅ Cache with event invalidation |
| **AR Aging Report** | 15 minutes | ❌ Not specified | ✅ Materialized view + cache |
| **Dashboard Revenue KPI** | 5 minutes | 🟡 Generic "5min" | ✅ Event-driven cache refresh |
| **Invoice Approval Queue** | 30 seconds | ❌ Not specified | ✅ Redis pub/sub real-time |
| **Period Status** | 0 seconds | ❌ Not specified | ✅ No cache + DB query (lightweight) |

### Performance Analysis:

#### A. Trial Balance - ZERO Staleness Tolerance

**Problem:**
```python
# ❌ WRONG - Cached trial balance
async def get_trial_balance(org_id: int, year: int, month: int):
    key = f"org:{org_id}:accounting:trial_balance:{year}:{month}"
    cached = await cache.get(key)
    if cached:
        return cached  # ⚠️ MIGHT BE STALE!

    # Expensive query: 100-300ms
    data = await db.query("""
        SELECT account_id, SUM(debit), SUM(credit)
        FROM journal_lines
        WHERE ...
        GROUP BY account_id
    """)

    await cache.set(key, data, ttl=300)  # 5 min TTL
    return data
```

**Why it fails:**
- CFO reviews trial balance at 4:55 PM
- AP team posts accrual at 4:56 PM
- CFO refreshes at 4:57 PM
- **Sees stale data** (cache hit, but wrong!)
- **Approves closing with incorrect balance** 💥

**Solution: TimescaleDB Continuous Aggregate**
```sql
-- Real-time materialized view (auto-refresh on write)
CREATE MATERIALIZED VIEW accounting.trial_balance_live
WITH (timescaledb.continuous, timescaledb.materialized_only=false) AS
SELECT
  organization_id,
  period_year,
  period_month,
  account_id,
  account_code,
  SUM(CASE WHEN debit_credit = 'debit' THEN amount ELSE 0 END) as total_debit,
  SUM(CASE WHEN debit_credit = 'credit' THEN amount ELSE 0 END) as total_credit,
  time_bucket('1 hour', created_at) as bucket  -- Hourly buckets
FROM journal_lines
GROUP BY organization_id, period_year, period_month, account_id, account_code, bucket;

-- Query (FAST: <50ms)
SELECT
  account_id,
  account_code,
  SUM(total_debit) as debit,
  SUM(total_credit) as credit
FROM accounting.trial_balance_live
WHERE organization_id = ?
  AND period_year = ?
  AND period_month = ?
GROUP BY account_id, account_code;
```

**Performance Benefits:**
- Query time: 300ms → 50ms (6x faster)
- Staleness: 5 minutes → 0 seconds
- Cache complexity: High → None
- Accuracy: 95% → 100%

#### B. Bank Reconciliation - 5 Minute Tolerance

**FROM BUSINESS_ACCOUNTING_STANDARDS.md Section 7.3:**
```
Bank Reconciliation:
  - Mode: Semi-Auto (import statement, auto-match by amount + date tolerance)
  - Matching confidence: 100% = auto-match, <100% = manual review
```

**Performance Challenge:**
```sql
-- Auto-matching query (EXPENSIVE):
SELECT
  bs.id as statement_id,
  je.id as journal_id,
  bs.amount,
  bs.transaction_date,
  je.reference,
  ABS(EXTRACT(EPOCH FROM (bs.transaction_date - je.entry_date)) / 86400) as date_diff_days,
  CASE
    WHEN bs.amount = je.total_amount
     AND ABS(EXTRACT(EPOCH FROM (bs.transaction_date - je.entry_date)) / 86400) <= 3
    THEN 100
    ELSE 80
  END as confidence
FROM bank_statements bs
LEFT JOIN journal_entries je
  ON je.organization_id = bs.organization_id
  AND je.account_id = bs.bank_account_id
  AND ABS(bs.amount - je.total_amount) < 1.00  -- Tolerance Rp 1
WHERE bs.organization_id = ?
  AND bs.reconciliation_id IS NULL
  AND je.status = 'posted'
ORDER BY confidence DESC;
```

**Query Performance:**
- Bank statements: 500 rows/month
- Journal entries: 1,000 rows/month
- Cartesian join with filters: **2-5 seconds** ⚠️

**Recommendation: Cache Match Results**
```yaml
Cache Key: org:{org_id}:banking:recon_matches:{bank_account_id}:{month}
TTL: 5 minutes
Invalidation Triggers:
  - New bank statement imported
  - New journal entry posted (if bank account affected)
  - Manual match/unmatch action

Performance Gain:
  - First query: 2-5 seconds (cache miss)
  - Subsequent: <50ms (cache hit)
  - User Experience: Smooth during reconciliation workflow
```

```python
class BankReconciliationService:
    async def get_auto_matches(self, org_id: int, bank_account_id: int, month: str):
        cache_key = f"org:{org_id}:banking:recon_matches:{bank_account_id}:{month}"

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Expensive query
        matches = await self.repo.find_auto_matches(org_id, bank_account_id, month)

        # Cache for 5 minutes
        await self.cache.set(cache_key, matches, ttl=300)

        return matches

    async def on_journal_posted(self, journal: JournalEntry):
        """Invalidate cache when journal affects bank account."""
        if journal.account_id in await self.get_bank_accounts(journal.organization_id):
            # Invalidate matches cache
            month = journal.entry_date.strftime('%Y-%m')
            await self.cache.delete(
                f"org:{journal.organization_id}:banking:recon_matches:{journal.account_id}:{month}"
            )
```

#### C. Dashboard Revenue KPI - Event-Driven Refresh

**Problem: Generic 5-minute cache doesn't align with business needs**

```python
# ❌ Time-based cache (suboptimal)
async def get_revenue_kpi(org_id: int, date: date):
    key = f"org:{org_id}:dashboard:revenue:{date}"
    cached = await cache.get(key)
    if cached:
        return cached  # Stale for up to 5 minutes

    revenue = await db.query("SELECT SUM(amount) FROM folios WHERE ...")
    await cache.set(key, revenue, ttl=300)
    return revenue
```

**Business Reality:**
- Revenue posts when folios are settled (event-driven)
- Check-out times: 8am-12pm (burst), 12pm-6pm (low), 6pm-11pm (burst)
- During low period: Cache hit 100% (no updates)
- During burst: Cache thrashes (many updates within 5 min window)

**Recommended: Event-Driven Cache Refresh**
```python
class DashboardKPIService:
    async def get_revenue_kpi(self, org_id: int, date: date):
        key = f"org:{org_id}:dashboard:revenue:{date}"

        # Long TTL (1 hour)
        cached = await self.cache.get(key)
        if cached:
            return cached

        revenue = await self.calculate_revenue(org_id, date)
        await self.cache.set(key, revenue, ttl=3600)
        return revenue

    async def on_folio_posted(self, folio: Folio):
        """Event-driven cache refresh."""
        date = folio.check_out_date
        key = f"org:{folio.organization_id}:dashboard:revenue:{date}"

        # Invalidate cache (will refresh on next query)
        await self.cache.delete(key)

        # Optional: Preemptive refresh (avoid cache miss)
        new_revenue = await self.calculate_revenue(folio.organization_id, date)
        await self.cache.set(key, new_revenue, ttl=3600)
```

**Performance Impact:**
- Cache hit rate: 70% → 95% (fewer invalidations)
- Staleness: Max 5 min → Max 1 second (event latency)
- Database load: Constant → Event-driven (aligned with actual changes)

---

## 5. TimescaleDB Considerations - Accounting Usage

### Development Standards V2 - Section 14.1:

```yaml
TimescaleDB Hypertables untuk:
  - shared.audit_logs (1 bulan chunk, compress > 1 bulan, retain 7 tahun)
  - pms.folio_transactions (1 bulan chunk, compress > 3 bulan, retain 7 tahun)
  - pms.daily_statistics (1 bulan chunk, compress > 3 bulan, retain 10 tahun)
  - accounting.ar_aging_history (1 bulan chunk, compress > 6 bulan, retain 7 tahun)
  - pms.housekeeping_logs (1 bulan chunk, compress > 1 bulan, retain 3 tahun)
```

### Accounting Standards - MISSING Guidance

**Problem:** Accounting Standards V1/V2 don't mention TimescaleDB at all!

**Should These Be Hypertables?**

| Table | Current | Should Be Hypertable? | Rationale |
|-------|---------|----------------------|-----------|
| `journal_entries` | ❌ Regular | ✅ YES | Time-series, 1000+ rows/month, compress >6 months |
| `journal_lines` | ❌ Regular | ✅ YES | Time-series, 3000+ rows/month, needed for trial balance |
| `ar_invoices` | ❌ Regular | ⚠️ MAYBE | Moderate volume, but frequent updates (payments) |
| `ap_invoices` | ❌ Regular | ⚠️ MAYBE | Same as AR |
| `bank_statements` | ❌ Regular | ✅ YES | Time-series, append-only, compress >3 months |
| `bank_reconciliations` | ❌ Regular | ❌ NO | Low volume, complex FK relationships |
| `fixed_assets` | ❌ Regular | ❌ NO | Master data, not time-series |
| `depreciation_runs` | ❌ Regular | ✅ YES | Time-series, monthly runs, historical queries |

### Detailed Analysis:

#### A. journal_entries & journal_lines - STRONG CANDIDATE

**Characteristics:**
- Append-mostly (posted journals are immutable)
- High volume (1,000+ entries/month)
- Time-series queries (by period)
- Historical reporting (comparative financial statements)
- Retention: 7-10 years (regulatory)

**Hypertable Benefits:**
```sql
-- Before (regular table):
SELECT account_id, SUM(amount)
FROM journal_lines jl
JOIN journal_entries je ON jl.journal_entry_id = je.id
WHERE je.organization_id = 123
  AND je.entry_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY account_id;
-- Query time: 300-500ms (full table scan on 36,000 rows)

-- After (hypertable with chunk pruning):
-- Same query, but TimescaleDB only scans 12 chunks (1 per month)
-- Query time: 50-100ms (5x faster)
```

**Compression Savings:**
```yaml
Scenario: 500 tenants, 7 years retention
Without compression:
  - 500 orgs x 1000 journals/month x 12 months x 7 years = 42M rows
  - Average row size: 200 bytes
  - Total: 8.4 GB

With compression (>6 months):
  - Recent 6 months: 8.4 GB x (6/84) = 600 MB (uncompressed)
  - Historical 78 months: 8.4 GB x (78/84) x 0.1 = 780 MB (90% compression)
  - Total: 1.38 GB (84% space savings)
```

**Implementation:**
```sql
-- Convert journal_lines to hypertable
ALTER TABLE accounting.journal_lines
  ADD COLUMN entry_date TIMESTAMPTZ;  -- Denormalize from journal_entries

UPDATE accounting.journal_lines jl
SET entry_date = je.entry_date
FROM accounting.journal_entries je
WHERE jl.journal_entry_id = je.id;

-- Add to composite PK
ALTER TABLE accounting.journal_lines
  DROP CONSTRAINT journal_lines_pkey,
  ADD PRIMARY KEY (id, entry_date);

-- Create hypertable
SELECT create_hypertable(
  'accounting.journal_lines',
  'entry_date',
  chunk_time_interval => INTERVAL '1 month',
  if_not_exists => TRUE
);

-- Compression policy
ALTER TABLE accounting.journal_lines SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'organization_id,account_id'
);

SELECT add_compression_policy('accounting.journal_lines', INTERVAL '6 months');

-- Retention policy
SELECT add_retention_policy('accounting.journal_lines', INTERVAL '10 years');
```

**Continuous Aggregate for Trial Balance:**
```sql
CREATE MATERIALIZED VIEW accounting.trial_balance_monthly
WITH (timescaledb.continuous, timescaledb.materialized_only=false) AS
SELECT
  time_bucket('1 month', entry_date) as month,
  organization_id,
  account_id,
  SUM(CASE WHEN debit_credit = 'debit' THEN amount ELSE 0 END) as total_debit,
  SUM(CASE WHEN debit_credit = 'credit' THEN amount ELSE 0 END) as total_credit
FROM accounting.journal_lines jl
JOIN accounting.journal_entries je ON jl.journal_entry_id = je.id
WHERE je.status = 'posted'
GROUP BY month, organization_id, account_id;

-- Refresh policy (every 1 minute for recent data)
SELECT add_continuous_aggregate_policy('trial_balance_monthly',
  start_offset => INTERVAL '1 month',
  end_offset => INTERVAL '0 seconds',
  schedule_interval => INTERVAL '1 minute'
);
```

**Performance Impact:**
- Trial balance query: 300ms → 20ms (15x faster)
- Historical reports (comparative): 2s → 100ms (20x faster)
- Storage: 8.4 GB → 1.4 GB (84% reduction)
- Cache complexity: Eliminated (continuous aggregate handles freshness)

#### B. ar_invoices / ap_invoices - NOT RECOMMENDED

**Why NOT hypertable:**
- Frequent updates (status changes, payment applications)
- Complex FK relationships (payments reference invoices)
- Not pure append-only (invoices can be edited before posting)

**Recommendation:**
```yaml
Strategy: Keep as regular table + selective materialized view
  - ar_invoices: Regular table (frequent updates)
  - ar_aging_snapshot: Hypertable (daily snapshot for historical reporting)
```

```sql
-- Daily snapshot table (hypertable)
CREATE TABLE accounting.ar_aging_snapshot (
  snapshot_date TIMESTAMPTZ NOT NULL,
  organization_id INTEGER NOT NULL,
  customer_id INTEGER NOT NULL,
  invoice_id INTEGER NOT NULL,
  invoice_number VARCHAR(50),
  invoice_date DATE,
  due_date DATE,
  total_amount NUMERIC(15,2),
  paid_amount NUMERIC(15,2),
  balance NUMERIC(15,2),
  days_overdue INTEGER,
  aging_bucket VARCHAR(10),
  PRIMARY KEY (snapshot_date, invoice_id)
);

SELECT create_hypertable(
  'accounting.ar_aging_snapshot',
  'snapshot_date',
  chunk_time_interval => INTERVAL '1 month'
);

-- Compression: >3 months
ALTER TABLE accounting.ar_aging_snapshot SET (timescaledb.compress);
SELECT add_compression_policy('accounting.ar_aging_snapshot', INTERVAL '3 months');

-- Retention: 7 years
SELECT add_retention_policy('accounting.ar_aging_snapshot', INTERVAL '7 years');
```

**Benefits:**
- Real-time AR queries: Use `ar_invoices` table (no change)
- Historical aging reports: Use `ar_aging_snapshot` (fast, compressed)
- Trend analysis: Compare aging snapshots across months
- Storage: Minimal overhead (1 snapshot/day/invoice vs real-time updates)

#### C. bank_statements - STRONG CANDIDATE

**Characteristics:**
- Pure append-only (statements are imported, never updated)
- Time-series by nature (transaction_date)
- High volume (500+ transactions/month/bank account)
- Historical queries (reconciliation, trend analysis)

**Hypertable Implementation:**
```sql
ALTER TABLE accounting.bank_statements
  DROP CONSTRAINT bank_statements_pkey,
  ADD PRIMARY KEY (id, transaction_date);

SELECT create_hypertable(
  'accounting.bank_statements',
  'transaction_date',
  chunk_time_interval => INTERVAL '1 month'
);

-- Compression: >3 months (reconciliation typically within 2 months)
ALTER TABLE accounting.bank_statements SET (timescaledb.compress);
SELECT add_compression_policy('accounting.bank_statements', INTERVAL '3 months');

-- Retention: 7 years
SELECT add_retention_policy('accounting.bank_statements', INTERVAL '7 years');
```

#### D. depreciation_runs - STRONG CANDIDATE

**Why hypertable:**
- Monthly depreciation runs (time-series)
- Historical comparison (YoY depreciation expense)
- Audit trail (regulatory requirement)
- Append-only (runs are never modified)

```sql
CREATE TABLE accounting.depreciation_run_details (
  run_date TIMESTAMPTZ NOT NULL,
  organization_id INTEGER NOT NULL,
  run_id INTEGER NOT NULL,
  asset_id INTEGER NOT NULL,
  depreciation_amount NUMERIC(15,2),
  accumulated_depreciation NUMERIC(15,2),
  net_book_value NUMERIC(15,2),
  PRIMARY KEY (run_date, run_id, asset_id)
);

SELECT create_hypertable(
  'accounting.depreciation_run_details',
  'run_date',
  chunk_time_interval => INTERVAL '1 year'  -- Annual chunk (low volume)
);

-- Compression: >1 year
ALTER TABLE accounting.depreciation_run_details SET (timescaledb.compress);
SELECT add_compression_policy('accounting.depreciation_run_details', INTERVAL '1 year');
```

### Summary - TimescaleDB Recommendations for Accounting:

| Table | Hypertable? | Chunk Interval | Compression | Retention | Priority |
|-------|-------------|----------------|-------------|-----------|----------|
| journal_entries | ✅ YES | 1 month | >6 months | 10 years | 🔴 HIGH |
| journal_lines | ✅ YES | 1 month | >6 months | 10 years | 🔴 HIGH |
| ar_invoices | ❌ NO | - | - | - | - |
| ar_aging_snapshot | ✅ YES | 1 month | >3 months | 7 years | 🟡 MEDIUM |
| bank_statements | ✅ YES | 1 month | >3 months | 7 years | 🟠 HIGH |
| bank_reconciliations | ❌ NO | - | - | - | - |
| depreciation_run_details | ✅ YES | 1 year | >1 year | 10 years | 🟢 LOW |
| fixed_assets | ❌ NO | - | - | - | - |

---

## 6. Recommendations - Unified Caching Strategy

### A. Update DEVELOPMENT_STANDARDS.md Section 5.4

**Add Financial Data Exception:**

```yaml
# EXISTING (Keep):
JANGAN Cache:
  - Realtime data (availability, occupancy)
  - Data sensitif (password, tokens)
  - Data transaction (journals, folios aktif)  # ← CLARIFY THIS

# ADD NEW SECTION:
5.4.1 Financial Data Caching Exception

FINANCIAL DATA RULES:
  1. NEVER cache raw transaction data (journal entries, payments)
  2. CAN cache COMPUTED results (aging reports, KPIs) with SHORT TTL
  3. CAN cache LIST queries (journal lists, invoice lists) with CONTEXT-AWARE TTL
  4. MUST cache IMMUTABLE data (closed period data) with LONG TTL

Context-Aware TTL by Period Status:
  - OPEN period: 5 minutes
  - IN_CLOSING period: 1 minute
  - CLOSED period: Permanent (cache forever)
  - REOPENED period: 1 minute

Real-time Requirements (NO CACHE):
  - Trial Balance (use TimescaleDB continuous aggregate)
  - Period status (lightweight DB query)
  - Approval workflows (Redis pub/sub for real-time updates)

Example:
  # ✅ CORRECT - Cache computed aging report
  key: org:{org_id}:accounting:ar_aging:report:{as_of_date}
  ttl: 15 minutes
  invalidate_on: invoice_created, payment_received

  # ✅ CORRECT - Cache journal list (context-aware)
  key: org:{org_id}:accounting:journals:list:{year}:{month}
  ttl: dynamic (based on period status)
  invalidate_on: journal_created, journal_posted

  # ❌ WRONG - Cache raw journal entry
  key: org:{org_id}:accounting:journal:{id}
  # Don't cache individual journal data
```

### B. Update DEVELOPMENT_STANDARDS_V2.md Section 14.1

**Add Accounting Tables to Hypertable List:**

```yaml
14.1.2 Tabel yang Menjadi Hypertable (EXPANDED)

| Schema | Table | Chunk Interval | Compression | Retention |
|--------|-------|----------------|-------------|-----------|
| shared | audit_logs | 1 bulan | > 1 bulan | 7 tahun |
| pms | folio_transactions | 1 bulan | > 3 bulan | 7 tahun |
| pms | daily_statistics | 1 bulan | > 3 bulan | 10 tahun |
| pms | housekeeping_logs | 1 bulan | > 1 bulan | 3 tahun |
| accounting | journal_entries | 1 bulan | > 6 bulan | 10 tahun | ← NEW
| accounting | journal_lines | 1 bulan | > 6 bulan | 10 tahun | ← NEW
| accounting | ar_aging_snapshot | 1 bulan | > 3 bulan | 7 tahun | ← NEW
| accounting | bank_statements | 1 bulan | > 3 bulan | 7 tahun | ← NEW
| accounting | depreciation_run_details | 1 tahun | > 1 tahun | 10 tahun | ← NEW

14.1.6 Continuous Aggregates for Accounting (NEW SECTION)

Trial Balance Real-time Materialized View:
  - Refresh every 1 minute
  - Zero cache staleness
  - Query time: <50ms (vs 300ms without)
  - Eliminates cache invalidation complexity

AR Aging Summary View:
  - Refresh every 15 minutes
  - Pre-computed aging buckets
  - Supports dashboard KPIs

Revenue Trend View:
  - Daily aggregation
  - Year-over-year comparison
  - Executive dashboard
```

### C. Add to BUSINESS_ACCOUNTING_STANDARDS_V2.md

**New Section 16: Performance & Caching Strategy**

```markdown
## 16. Performance & Caching Strategy

### 16.1 Caching Rules for Financial Data

| Data Type | Cache Strategy | TTL | Invalidation |
|-----------|----------------|-----|--------------|
| Trial Balance | NO CACHE (use continuous aggregate) | - | Real-time refresh |
| Journal Lists | Context-aware cache | 1-5 min* | On journal CRUD |
| Invoice Lists | Context-aware cache | 2-15 min* | On invoice CRUD |
| Aging Reports | Computed result cache | 15 min | On invoice/payment |
| Bank Matches | Computed result cache | 5 min | On statement import |
| Period Status | NO CACHE | - | Lightweight query |
| Approval Queue | Real-time (pub/sub) | - | Event-driven |

*TTL varies by period status:
  - OPEN: 5 min (journals), 15 min (invoices)
  - IN_CLOSING: 1 min (journals), 2 min (invoices)
  - CLOSED: Permanent (immutable data)
  - REOPENED: 1 min (both)

### 16.2 TimescaleDB Implementation

**Hypertables:**
- journal_entries / journal_lines (primary focus)
- ar_aging_snapshot (historical aging)
- bank_statements (transaction history)
- depreciation_run_details (monthly runs)

**Continuous Aggregates:**
- trial_balance_monthly (real-time trial balance)
- ar_aging_summary (pre-computed aging buckets)
- revenue_daily (trend analysis)

**Performance Gains:**
- Trial balance: 300ms → 20ms (15x faster)
- Historical reports: 2s → 100ms (20x faster)
- Storage: 84% reduction with compression
- Cache complexity: Eliminated for trial balance

### 16.3 Cross-Service Cache Invalidation

**Event-Driven Pattern:**

When PMS posts folio to Accounting:
  1. PMS → RabbitMQ: folio.posted event
  2. Accounting consumes event
  3. Accounting invalidates:
     - Journal list cache
     - Trial balance refresh trigger
     - Dashboard revenue cache
  4. Dashboard service also consumes event
  5. Dashboard invalidates KPI cache

**No direct cache coupling between services.**
```

### D. Create New Document: CACHING_DECISION_TREE.md

```markdown
# Caching Decision Tree - Financial Data

## Question 1: Is this data IMMUTABLE (closed period)?

YES → Cache with TTL=∞ (permanent)
  - Closed period trial balance
  - Closed period financial statements
  - Historical aging reports (as-of closed date)

NO → Go to Question 2

## Question 2: Is REAL-TIME accuracy CRITICAL?

YES → NO CACHE (use alternative optimization)
  - Trial Balance → TimescaleDB continuous aggregate
  - Period Status → Lightweight DB query (indexed)
  - Approval Status → Redis pub/sub real-time

NO → Go to Question 3

## Question 3: Is this COMPUTED result (not raw data)?

YES → Cache with SHORT TTL
  - Aging Report → 15 min TTL
  - Bank Matches → 5 min TTL
  - Dashboard KPIs → 5 min TTL (or event-driven)

NO → Go to Question 4

## Question 4: Is this LIST query (not entity)?

YES → Cache with CONTEXT-AWARE TTL
  - Journal List → 1-5 min (depends on period status)
  - Invoice List → 2-15 min (depends on period status)
  - Use CacheInvalidator helper

NO → DON'T CACHE
  - Individual journal entry
  - Individual invoice
  - Payment record
```

---

## 7. Performance Benchmarks

### Expected Performance After Implementation:

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Trial Balance Query | 300ms | 20ms | 15x |
| Historical TB (comparative) | 2000ms | 100ms | 20x |
| AR Aging Report (first hit) | 500ms | 500ms | 1x |
| AR Aging Report (cached) | 500ms | 50ms | 10x |
| Journal List (OPEN period) | 200ms | 150ms | 1.3x |
| Journal List (CLOSED period) | 200ms | 30ms | 6.7x |
| Bank Auto-Match (first hit) | 3000ms | 3000ms | 1x |
| Bank Auto-Match (cached) | 3000ms | 50ms | 60x |
| Dashboard Revenue KPI | 400ms | 80ms | 5x |
| Period Status Check | 50ms | 50ms | 1x (lightweight) |

### Storage Savings (500 tenants, 7 years):

| Table | Without Compression | With Compression | Savings |
|-------|---------------------|------------------|---------|
| journal_lines | 8.4 GB | 1.4 GB | 84% |
| ar_aging_snapshot | 2.1 GB | 300 MB | 86% |
| bank_statements | 1.5 GB | 200 MB | 87% |
| depreciation_run_details | 500 MB | 80 MB | 84% |
| **TOTAL** | **12.5 GB** | **2.0 GB** | **84%** |

### Cache Hit Rate Projections:

| Scenario | Hit Rate | Explanation |
|----------|----------|-------------|
| Month 1 (OPEN) | 70% | Frequent updates during month |
| Month 2 (CLOSED) | 99% | Immutable, queried for comparisons |
| Month 3+ (CLOSED) | 99.9% | Historical queries fully cached |
| Year-end (many closed months) | 95% | Mix of current + historical |

---

## 8. Migration Plan

### Phase 1: Critical Performance Issues (Week 1-2)

**Priority: Trial Balance & Journal Lines**

```sql
-- Day 1-3: Setup TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Day 4-7: Convert journal_lines to hypertable
-- (Detailed steps in Section 5A)

-- Day 8-10: Create continuous aggregate for trial balance
-- (SQL in Section 4A)

-- Day 11-14: Testing & validation
```

### Phase 2: Caching Strategy (Week 3-4)

**Priority: Context-Aware TTL & Invalidation**

```python
# Week 3: Implement AccountingCacheService
class AccountingCacheService:
    # Code from Section 2
    pass

# Week 4: Update all use cases to use new cache service
```

### Phase 3: Remaining Hypertables (Week 5-6)

**Priority: ar_aging_snapshot, bank_statements, depreciation_run_details**

### Phase 4: Documentation & Training (Week 7-8)

**Priority: Update all standards documents**

---

## 9. Conclusion

### Critical Issues Identified:

1. **Trial Balance Zero-Staleness Requirement** 🔴
   - Current: No specification
   - Risk: Financial statement errors
   - Solution: TimescaleDB continuous aggregate

2. **Context-Unaware TTL Strategy** 🟡
   - Current: Generic 5-minute TTL
   - Risk: Poor cache hit rate, unnecessary invalidations
   - Solution: Period-status-aware TTL

3. **Missing Cross-Service Invalidation** 🟠
   - Current: No pattern defined
   - Risk: Stale data when PMS posts to Accounting
   - Solution: Event-driven invalidation via RabbitMQ

4. **No TimescaleDB for Accounting Tables** 🟡
   - Current: Only PMS tables use hypertables
   - Risk: Poor performance at scale, high storage costs
   - Solution: Convert journal_lines, ar_aging_snapshot, bank_statements

5. **Unclear Financial Data Caching Rules** 🔴
   - Current: "Don't cache transaction data" (too broad)
   - Risk: Developers avoid caching entirely (poor performance)
   - Solution: Clear decision tree with examples

### Expected Outcomes:

- **15-20x faster trial balance** (300ms → 20ms)
- **84% storage reduction** (12.5 GB → 2.0 GB)
- **95% cache hit rate** for historical data
- **Zero staleness** for critical financial queries
- **Clear developer guidelines** for caching financial data

### Next Steps:

1. Review & approve recommendations with architecture team
2. Update DEVELOPMENT_STANDARDS.md Section 5.4
3. Update DEVELOPMENT_STANDARDS_V2.md Section 14.1
4. Add new section to BUSINESS_ACCOUNTING_STANDARDS_V2.md
5. Begin Phase 1 migration (TimescaleDB for journal_lines)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Author:** Performance Engineering Team
**Status:** Draft - Awaiting Review
