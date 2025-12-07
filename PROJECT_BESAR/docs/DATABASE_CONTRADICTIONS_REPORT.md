# Database Contradictions Report
## Development Standards vs Business Accounting Standards

**Generated**: 2025-12-07
**Scope**: Database schema design contradictions
**Documents Analyzed**:
- `DEVELOPMENT_STANDARDS.md` (3,037 lines)
- `DEVELOPMENT_STANDARDS_V2.md` (4,150 lines)
- `BUSINESS_ACCOUNTING_STANDARDS.md` (3,193 lines)
- `BUSINESS_ACCOUNTING_STANDARDS_V2.md` (3,016 lines)

---

## Executive Summary

Found **7 critical** and **3 moderate** database design contradictions between Development Standards and Business Accounting Standards that will cause:
- ❌ Schema incompatibility issues
- ❌ Migration failures
- ❌ Audit trail gaps
- ❌ Data recovery problems
- ❌ Inconsistent business logic

**Impact**: High - These contradictions affect core database architecture and must be resolved before implementation.

---

## Critical Contradictions

### 1. ❌ CRITICAL: Numeric Precision for Monetary Amounts

**Development Standard Rule** (Line 731):
```sql
-- Rule: NUMERIC(15,4) untuk semua monetary amounts
total_amount NUMERIC(15,4) NOT NULL,
tax_amount NUMERIC(15,4) NOT NULL DEFAULT 0,
discount_amount NUMERIC(15,4) NOT NULL DEFAULT 0,
```
- **Precision**: 15 digits total, 4 decimal places
- **Max Value**: 99,999,999,999.9999
- **Rationale**: "4 decimal places: precision untuk tax calculations"

**Accounting Standards V2 Implementation** (Lines 881-931):
```sql
acquisition_cost DECIMAL(18,2) NOT NULL,
salvage_value DECIMAL(18,2) DEFAULT 0,
current_book_value DECIMAL(18,2) NOT NULL,
depreciation_amount DECIMAL(18,2) NOT NULL,
total_cost DECIMAL(18,2) NOT NULL,
```
- **Precision**: 18 digits total, **2 decimal places only**
- **Max Value**: 9,999,999,999,999,999.99

**Contradiction**:
- ✅ Dev Standard: NUMERIC(15,4) - 4 decimal precision
- ❌ Accounting V2: DECIMAL(18,2) - **2 decimal precision only**

**Impact**:
- ⚠️ **Critical** - Loss of precision for tax calculations
- ⚠️ Rounding errors in calculations like (amount * 0.11) → need 4 decimals
- ⚠️ Incompatible with Python `Decimal("0.0001")` quantize pattern shown in Dev Standards

**Recommended Fix**:
```sql
-- Change ALL monetary amounts in accounting schema to:
acquisition_cost NUMERIC(15,4) NOT NULL,
salvage_value NUMERIC(15,4) DEFAULT 0,
current_book_value NUMERIC(15,4) NOT NULL,
depreciation_amount NUMERIC(15,4) NOT NULL,
total_cost NUMERIC(15,4) NOT NULL,
unit_cost NUMERIC(15,4) NOT NULL,
-- etc.
```

**Affected Tables** (14+ tables):
- `fixed_assets` (7 amount columns)
- `depreciation_history` (3 amount columns)
- `asset_disposals` (4 amount columns)
- `asset_revaluations` (3 amount columns)
- `items` (4 cost columns)
- `stock_on_hand` (1 cost column)
- `stock_layers` (1 cost column)
- `stock_transactions` (2 cost columns)
- `budget_lines` (multiple amount columns)
- All AR/AP tables
- All journal entry tables

---

### 2. ❌ CRITICAL: Multi-Tenancy - organization_id Should NOT Exist

**Development Standard Rule** (Lines 562-567, 614, 936):
```sql
-- Rule: Database per Org + Schema per App
-- organization_id TIDAK PERLU di organization database

-- Schema accounting: tabel khusus Accounting
CREATE TABLE accounting.journals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- ⚠️ organization_id TIDAK PERLU (database sudah terpisah)
    journal_date DATE NOT NULL,
    ...
);
```

**Clear Statement** (Line 407):
| Aspek | Platform DB | Organization DB |
|-------|-------------|-----------------|
| `organization_id` | Ya (untuk relasi) | **TIDAK PERLU** |

**Accounting Standards V2 Implementation** (Lines 217, 246, 865, 943, etc.):
```sql
CREATE TABLE integration_mappings (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ...
);

CREATE TABLE fixed_assets (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ...
);
```

**Found**: 14+ tables with `organization_id` column

**Contradiction**:
- ✅ Dev Standard: Accounting tables should be in **organization database** with **schema = accounting**
- ❌ Accounting V2: All tables have `organization_id INTEGER NOT NULL`

**Impact**:
- ⚠️ **Critical** - Schema design fundamentally wrong
- ⚠️ Cannot implement "Database per Org" architecture
- ⚠️ All queries will have unnecessary `organization_id` filter
- ⚠️ Violates isolation principle (database already separates orgs)

**Recommended Fix**:
```sql
-- REMOVE organization_id from ALL accounting schema tables
-- These tables should be in: db_hotel_grandjaya → schema: accounting

CREATE TABLE accounting.fixed_assets (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    -- ❌ REMOVE: organization_id INTEGER NOT NULL...

    -- Classification
    category_id INTEGER NOT NULL REFERENCES accounting.asset_categories(id),
    ...
);
```

**Affected Tables** (14 tables):
- `integration_mappings`
- `integration_queue`
- `fixed_assets`
- `asset_disposals`
- `asset_revaluations`
- `warehouses`
- `item_categories`
- `items`
- `stock_transactions`
- `stock_transfers`
- `stock_counts`
- `cycle_count_schedule`
- `budget_scenarios`
- All other accounting schema tables

---

### 3. ❌ CRITICAL: Missing Soft Delete Columns

**Development Standard Rule** (Lines 464-466, 502-503, 517-521):
```sql
-- Minimal Audit Columns
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
created_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_at      TIMESTAMP WITH TIME ZONE,
updated_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,

-- Untuk table yang support soft delete (hampir semua)
deleted_at      TIMESTAMP WITH TIME ZONE,
deleted_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL
```

**Rule Statement** (Line 518):
> **Rule:** Semua table menggunakan soft delete, KECUALI:
> - Log tables (audit_logs, activity_logs) → tidak perlu delete
> - Temporary/session tables → bisa hard delete
> - Junction tables tanpa data penting → bisa hard delete

**Accounting Standards V2 Implementation**:
```bash
# Count of deleted_at/deleted_by_id occurrences: 0
```

**Contradiction**:
- ✅ Dev Standard: **ALL** business tables must have `deleted_at` and `deleted_by_id`
- ❌ Accounting V2: **ZERO** tables have soft delete columns

**Impact**:
- ⚠️ **Critical** - Cannot recover deleted records
- ⚠️ Audit trail incomplete (who deleted, when deleted)
- ⚠️ No way to restore accidentally deleted data
- ⚠️ Violates "hampir semua" (almost all) tables requirement

**Recommended Fix**:
```sql
-- ADD to ALL business tables:
CREATE TABLE accounting.fixed_assets (
    ...

    -- Audit trail (MISSING IN CURRENT SCHEMA)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Soft delete (MISSING IN CURRENT SCHEMA)
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Update indexes to respect soft delete
CREATE INDEX idx_fixed_assets_status
    ON accounting.fixed_assets(status)
    WHERE deleted_at IS NULL;  -- ⚠️ MISSING IN CURRENT SCHEMA
```

**Affected Tables**: ALL business tables (~30+ tables in accounting schema)

---

### 4. ❌ CRITICAL: Missing updated_by_id Column

**Development Standard Rule** (Lines 461-462, 500-501):
```sql
-- Minimal Audit Columns
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
created_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_at      TIMESTAMP WITH TIME ZONE,
updated_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- ⚠️ WAJIB
```

**Accounting Standards V2 Implementation**:
```bash
# Count of updated_by_id occurrences: 1 (only in fixed_assets)
```

**Examples Missing updated_by_id**:
```sql
-- integration_mappings (Lines 237-239)
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE,
-- ❌ MISSING: updated_by_id

-- integration_queue (Line 259)
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
-- ❌ MISSING: updated_at AND updated_by_id

-- items (Lines 1550-1551)
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE,
-- ❌ MISSING: updated_by_id
```

**Contradiction**:
- ✅ Dev Standard: **EVERY** table must have `updated_by_id`
- ❌ Accounting V2: Only 1 out of 30+ tables has it

**Impact**:
- ⚠️ **Critical** - Cannot track who modified records
- ⚠️ Audit trail incomplete
- ⚠️ Compliance issues (ISO 27001, SOC2 require change tracking)

**Recommended Fix**:
```sql
-- ADD updated_by_id to ALL tables:
updated_at TIMESTAMP WITH TIME ZONE,
updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
```

**Affected Tables**: 29+ tables missing `updated_by_id`

---

### 5. ❌ CRITICAL: Wrong ON DELETE Action for Audit Columns

**Development Standard Rule** (Lines 460-466):
```sql
-- Audit Columns MUST use ON DELETE SET NULL
created_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
deleted_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL
```

**Rationale**: User can be deleted, but we still need to know "user ID 123 created this" even if user 123 is gone.

**Accounting Standards V2 Implementation** (Lines 913, 915, 1005, etc.):
```sql
-- Wrong: No ON DELETE action specified (defaults to NO ACTION)
created_by_id INTEGER REFERENCES users(id),
updated_by_id INTEGER REFERENCES users(id),
```

**Contradiction**:
- ✅ Dev Standard: Audit FKs must have `ON DELETE SET NULL`
- ❌ Accounting V2: No `ON DELETE` action → will **fail** when user deleted

**Impact**:
- ⚠️ **Critical** - Cannot delete users who have created/updated records
- ⚠️ FK constraint violation errors at runtime
- ⚠️ User deletion will fail or require CASCADE (data loss)

**Recommended Fix**:
```sql
-- Change ALL audit column FK constraints:
created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
```

**Affected Tables**: ALL tables with audit columns (~30+ tables)

---

### 6. ❌ CRITICAL: Inconsistent Timestamp Column Names

**Development Standard Rule** (Line 40, 694-700):
```sql
-- Rule: Semua timestamp WITH TIME ZONE, suffix _at
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
updated_at TIMESTAMP WITH TIME ZONE
deleted_at TIMESTAMP WITH TIME ZONE
```

**Accounting Standards V2 Implementation** - Inconsistent:
```sql
-- ✅ Correct pattern:
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE
processed_at TIMESTAMP WITH TIME ZONE
expired_at TIMESTAMP WITH TIME ZONE

-- ⚠️ Found but inconsistent application
```

**Analysis**:
- Most tables follow `_at` suffix ✅
- But some special timestamps are missing ❌

**Impact**:
- ⚠️ Moderate - Naming inconsistency
- Query patterns become unpredictable

**Recommended Fix**: Verify ALL timestamp columns end with `_at` suffix

---

### 7. ❌ CRITICAL: Cross-Database Foreign Keys Not Handled

**Development Standard Rule** (Lines 635-648):
```sql
-- Link ke Platform User (cross-database reference)
CREATE TABLE hrm.employees (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL,  -- FK ke platform.users (cross-database, tidak enforce FK)
    employee_code VARCHAR(20),
    ...
);

-- Audit columns pakai user_id dari platform (cross-database)
created_by_id INTEGER,  -- user_id dari platform (NO FK constraint)
updated_by_id INTEGER,  -- user_id dari platform (NO FK constraint)
```

**Accounting Standards V2 Implementation** (Lines 913, 915):
```sql
-- Wrong: FK to users(id) assumes same database
created_by_id INTEGER REFERENCES users(id),
updated_by_id INTEGER REFERENCES users(id),
```

**Contradiction**:
- ✅ Dev Standard: Audit columns in ORG database → **NO FK constraint** (cross-database ref)
- ❌ Accounting V2: `REFERENCES users(id)` → assumes users table exists in same DB

**Impact**:
- ⚠️ **Critical** - FK constraint will fail (users table is in platform DB, not org DB)
- ⚠️ Migration will fail with "relation users does not exist"
- ⚠️ Schema cannot be created

**Recommended Fix**:
```sql
-- REMOVE REFERENCES clause for cross-database references
created_by_id INTEGER,  -- user_id from platform.users (cross-db ref, no FK)
updated_by_id INTEGER,
deleted_by_id INTEGER,

-- Or add comment to clarify:
created_by_id INTEGER,  -- FK to platform.users.id (cross-database, not enforced)
```

**Affected**: ALL tables with `created_by_id`, `updated_by_id`, `deleted_by_id`

---

## Moderate Contradictions

### 8. ⚠️ MODERATE: Index Naming Pattern Incomplete

**Development Standard Example** (Lines 889-891):
```sql
-- Pattern: idx_{table_name}_{columns}
CREATE INDEX idx_{table_name}_org ON {table_name}(organization_id);
CREATE INDEX idx_{table_name}_status ON {table_name}(status) WHERE deleted_at IS NULL;
```

**Accounting Standards V2 Implementation**:
```sql
-- ✅ Good examples:
CREATE INDEX idx_integration_queue_status ON integration_queue(organization_id, status);
CREATE INDEX idx_fixed_assets_org ON fixed_assets(organization_id);

-- ⚠️ Missing schema prefix for clarity:
-- Should be: idx_accounting_fixed_assets_org or idx_acc_fixed_assets_org
```

**Impact**:
- ⚠️ Low-Moderate - No technical issue, but harder to identify which schema index belongs to
- Recommendation: Add schema prefix for org database tables

**Recommended Fix**:
```sql
-- For tables in accounting schema:
CREATE INDEX idx_accounting_fixed_assets_org ON accounting.fixed_assets(...);
-- Or shorter:
CREATE INDEX idx_acc_fixed_assets_org ON accounting.fixed_assets(...);
```

---

### 9. ⚠️ MODERATE: Missing Partial Index for Soft Delete

**Development Standard Rule** (Line 511, 891):
```sql
-- Index should exclude deleted records
CREATE INDEX idx_example_table_status
    ON example_table(status)
    WHERE deleted_at IS NULL;  -- ⚠️ Important for performance
```

**Accounting Standards V2 Implementation**:
```sql
-- No WHERE deleted_at IS NULL clause in any index
CREATE INDEX idx_fixed_assets_status ON fixed_assets(organization_id, status);
-- ❌ Should be: WHERE deleted_at IS NULL
```

**Impact**:
- ⚠️ Moderate - Indexes will include deleted records (wasted space)
- Performance degradation on large tables with many soft-deleted records

**Recommended Fix**:
```sql
CREATE INDEX idx_accounting_fixed_assets_status
    ON accounting.fixed_assets(status)
    WHERE deleted_at IS NULL;
```

---

### 10. ⚠️ MODERATE: Missing UUID Column

**Development Standard Rule** (Lines 484, 675-686, 903):
```sql
-- External UUID (untuk API exposure)
uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

-- API exposure: pakai uuid
GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000
```

**Accounting Standards V2 Implementation**:
- No `uuid` column found in any table schema

**Impact**:
- ⚠️ Moderate - Cannot expose IDs safely in API (predictable integer IDs)
- Security concern (ID enumeration attacks possible)

**Recommended Fix**:
```sql
CREATE TABLE accounting.fixed_assets (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,  -- ⚠️ ADD THIS
    ...
);
```

---

## Summary Table

| # | Issue | Severity | Affected Tables | Migration Impact |
|---|-------|----------|-----------------|------------------|
| 1 | NUMERIC(15,4) vs DECIMAL(18,2) | **CRITICAL** | 14+ tables | All amount columns need ALTER |
| 2 | organization_id should not exist | **CRITICAL** | 14+ tables | Major schema redesign |
| 3 | Missing deleted_at/deleted_by_id | **CRITICAL** | 30+ tables | Add columns to all tables |
| 4 | Missing updated_by_id | **CRITICAL** | 29+ tables | Add column to all tables |
| 5 | Wrong ON DELETE for audit FKs | **CRITICAL** | 30+ tables | Modify all FK constraints |
| 6 | Timestamp naming | **CRITICAL** | Few tables | Minor rename if found |
| 7 | Cross-DB FK constraints | **CRITICAL** | 30+ tables | Remove FK constraints |
| 8 | Index naming pattern | **MODERATE** | All indexes | Add schema prefix |
| 9 | Missing partial index clause | **MODERATE** | All indexes | Add WHERE deleted_at IS NULL |
| 10 | Missing uuid column | **MODERATE** | All tables | Add uuid to all tables |

---

## Recommended Action Plan

### Phase 1: Critical Fixes (MUST DO before implementation)

1. **Remove organization_id** from all accounting schema tables
   - These tables will live in organization database → schema accounting
   - organization_id provides NO value (database already separates orgs)

2. **Change monetary precision** from DECIMAL(18,2) to NUMERIC(15,4)
   - Affects 50+ columns across 14+ tables
   - Required for tax calculation precision

3. **Add soft delete columns** to ALL business tables:
   ```sql
   deleted_at TIMESTAMP WITH TIME ZONE,
   deleted_by_id INTEGER  -- No FK, cross-database ref
   ```

4. **Add updated_by_id** to ALL tables:
   ```sql
   updated_by_id INTEGER  -- No FK, cross-database ref
   ```

5. **Remove FK constraints** from audit columns:
   ```sql
   -- Change from:
   created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
   -- To:
   created_by_id INTEGER,  -- FK to platform.users.id (cross-db, not enforced)
   ```

### Phase 2: Moderate Fixes (SHOULD DO for consistency)

6. **Add uuid column** to all tables:
   ```sql
   uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
   ```

7. **Update index naming** with schema prefix:
   ```sql
   CREATE INDEX idx_acc_table_name_column ON accounting.table_name(...);
   ```

8. **Add partial index clauses**:
   ```sql
   CREATE INDEX ... WHERE deleted_at IS NULL;
   ```

### Phase 3: Documentation

9. **Update BUSINESS_ACCOUNTING_STANDARDS_V2.md** with:
   - Database context (organization DB → accounting schema)
   - Reason for NO organization_id
   - Standard audit columns template
   - Standard soft delete pattern

10. **Create migration scripts** following:
    - Naming: `XXX_fix_accounting_schema_standards.sql`
    - Test on copy of database first
    - Document breaking changes

---

## Migration Script Template

```sql
-- Migration: 046
-- Description: Fix accounting schema to match development standards
-- Date: 2025-12-07
-- BREAKING CHANGES: Yes - Major schema modifications

BEGIN;

-- ==================================================
-- STEP 1: Add missing audit columns
-- ==================================================

-- Add updated_by_id to all tables
ALTER TABLE accounting.integration_mappings
    ADD COLUMN updated_by_id INTEGER;  -- cross-db ref, no FK

ALTER TABLE accounting.fixed_assets
    ADD COLUMN updated_by_id INTEGER;  -- cross-db ref, no FK

-- ... repeat for all tables ...

-- ==================================================
-- STEP 2: Add soft delete columns
-- ==================================================

ALTER TABLE accounting.fixed_assets
    ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN deleted_by_id INTEGER;  -- cross-db ref, no FK

-- ... repeat for all business tables ...

-- ==================================================
-- STEP 3: Remove organization_id (MAJOR CHANGE)
-- ==================================================

-- ⚠️ WARNING: This assumes data already filtered by database separation
-- Only run if tables are already in organization database

ALTER TABLE accounting.fixed_assets
    DROP COLUMN organization_id;

ALTER TABLE accounting.integration_mappings
    DROP COLUMN organization_id;

-- ... repeat for all tables ...

-- ==================================================
-- STEP 4: Change DECIMAL(18,2) to NUMERIC(15,4)
-- ==================================================

ALTER TABLE accounting.fixed_assets
    ALTER COLUMN acquisition_cost TYPE NUMERIC(15,4),
    ALTER COLUMN salvage_value TYPE NUMERIC(15,4),
    ALTER COLUMN current_book_value TYPE NUMERIC(15,4),
    ALTER COLUMN accumulated_depreciation TYPE NUMERIC(15,4);

-- ... repeat for all amount columns ...

-- ==================================================
-- STEP 5: Remove FK constraints from audit columns
-- ==================================================

-- If FK was added, drop it:
ALTER TABLE accounting.fixed_assets
    DROP CONSTRAINT IF EXISTS fixed_assets_created_by_id_fkey,
    DROP CONSTRAINT IF EXISTS fixed_assets_updated_by_id_fkey;

-- ==================================================
-- STEP 6: Add uuid column
-- ==================================================

ALTER TABLE accounting.fixed_assets
    ADD COLUMN uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE;

-- ... repeat for all tables ...

-- ==================================================
-- STEP 7: Recreate indexes with proper naming and partial clause
-- ==================================================

DROP INDEX IF EXISTS accounting.idx_fixed_assets_status;

CREATE INDEX idx_acc_fixed_assets_status
    ON accounting.fixed_assets(status)
    WHERE deleted_at IS NULL;

-- ... repeat for all indexes ...

COMMIT;
```

---

## Conclusion

The Business Accounting Standards document has **significant deviations** from the Development Standards that will prevent successful implementation of the multi-database architecture.

**Key Issues**:
1. Wrong database design (includes organization_id when shouldn't)
2. Wrong data types (DECIMAL 18,2 instead of NUMERIC 15,4)
3. Missing critical audit columns (deleted_at, deleted_by_id, updated_by_id)
4. Wrong FK constraints (cross-database references)

**Recommendation**:
- **DO NOT implement** current accounting schema as-is
- **MUST apply** all Critical fixes before any deployment
- **SHOULD update** documentation to reflect correct architecture

**Estimated Effort**:
- Schema redesign: 2-3 days
- Migration script creation: 2 days
- Testing: 3-4 days
- **Total**: ~1.5 weeks

---

## References

- Development Standards: Lines 289-1100 (Database Patterns section)
- Accounting Standards V2: Lines 215-2250 (All CREATE TABLE statements)
- Multi-Tenancy Architecture: DEVELOPMENT_STANDARDS.md lines 333-450
- Audit Trail Requirements: DEVELOPMENT_STANDARDS.md lines 453-558

---

**Report Generated By**: Claude Code (Database Architect)
**Date**: 2025-12-07
**Status**: ⚠️ Critical Issues Found - Action Required
