# Contradictions Resolution: Development Standards vs Business Accounting Standards

> **Date**: 2025-12-07
> **Status**: Resolved (21 contradictions)
> **Decisions**: #79 - #99

---

## Overview

Dokumen ini merangkum hasil analisis kontradiksi antara:
- **Development Standards** (V1 & V2): Technical implementation standards
- **Business Accounting Standards** (V1 & V2): Business rules & accounting requirements

Analisis dilakukan menggunakan 4 specialized agents:
1. Database Architect - Schema conflicts
2. Backend Architect - API patterns
3. Security Auditor - Compliance gaps
4. Performance Engineer - Caching issues

---

## Summary of Resolutions

| Category | Count | Decisions |
|----------|-------|-----------|
| Database Schema | 5 | #79, #80, #81, #82, #89 |
| Architecture Patterns | 5 | #84, #85, #86, #92, #93 |
| API Design | 2 | #83, #87 |
| Performance | 3 | #88, #96, #97 |
| Business Rules | 4 | #90, #94, #95, #99 |
| Error Handling | 2 | #91, #98 |

---

## Detailed Resolutions

### 1. NUMERIC Precision (Decision #79)

**Contradiction:**
- Dev Standards V1: `DECIMAL(15,4)`
- Business Standards: `DECIMAL(18,2)` dan `DECIMAL(18,4)`

**Resolution:** Unified `DECIMAL(18,4)` untuk semua monetary values

**Rationale:**
- 18 digits cukup untuk konsolidasi holding company besar
- 4 decimal places untuk exchange rates dan unit prices
- Konsisten di seluruh sistem

---

### 2. Data Retention Period (Decision #80)

**Contradiction:**
- Dev Standards V1: 7 tahun retention
- Business Standards: 10 tahun (UU Perpajakan Indonesia)

**Resolution:** Perpetual (no auto-delete), archive ke cold storage

**Rationale:**
- Tidak ada risiko compliance violation
- Cold storage untuk cost efficiency
- Audit trail tersimpan selamanya

---

### 3. Soft Delete Implementation (Decision #81)

**Contradiction:**
- Dev Standards: `deleted_at` timestamp only
- Business Standards: Campuran `is_deleted` dan `deleted_at`

**Resolution:** Both columns: `is_deleted` + `deleted_at` + `deleted_by_id`

**Schema:**
```sql
is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
deleted_at TIMESTAMP WITH TIME ZONE,
deleted_by_id INTEGER REFERENCES users(id)
```

**Rationale:**
- `is_deleted`: Fast query dengan boolean index
- `deleted_at`: Audit trail kapan dihapus
- `deleted_by_id`: Audit trail siapa yang hapus

---

### 4. Organization ID for Reference Data (Decision #82)

**Contradiction:**
- Dev Standards: `organization_id` wajib di SEMUA tabel
- Business Standards: Tabel referensi global (currencies, tax_types) tanpa org_id

**Resolution:** System Organization (org_id = 1) untuk global data

**Implementation:**
```sql
-- System organization (always id = 1)
INSERT INTO organizations (id, name, code, is_system)
OVERRIDING SYSTEM VALUE
VALUES (1, 'System', 'SYSTEM', TRUE);

-- Global data uses org_id = 1
INSERT INTO currencies (organization_id, code, name)
VALUES (1, 'IDR', 'Indonesian Rupiah');

-- Query for tenant (gets system + own data)
SELECT * FROM currencies
WHERE organization_id IN (1, :tenant_org_id);
```

**Rationale:**
- Semua tabel tetap punya `org_id NOT NULL`
- FK constraint valid
- Tenant bisa extend (tambah currency sendiri)

---

### 5. Period Lock Enforcement (Decision #83)

**Contradiction:**
- Dev Standards: Tidak ada mechanism
- Business Standards: OPEN → CLOSED → LOCKED status

**Resolution:** Defense in Depth (Use Case + Database Trigger)

**Layer 1 - Use Case (Primary):**
```python
if period.status == 'CLOSED':
    raise BusinessRuleError(
        code="PERIOD_CLOSED",
        message=f"Period {period.name} sudah ditutup"
    )
```

**Layer 2 - Database Trigger (Safety Net):**
```sql
CREATE TRIGGER trg_journal_period_lock
BEFORE INSERT OR UPDATE ON journal_entries
FOR EACH ROW EXECUTE FUNCTION check_period_lock();
```

**Rationale:**
- Use Case: User-friendly error messages
- Trigger: Safety net yang tidak bisa di-bypass

---

### 6. Atomic Multi-table Operations (Decision #84)

**Contradiction:**
- Dev Standards: Tidak ada pattern
- Business Standards: Journal butuh atomic insert ke 3+ tabel

**Resolution:** UnitOfWork Pattern

**Implementation:**
```python
async with self.uow:
    journal = await self.journal_repo.create(dto)
    await self.line_repo.create_lines(journal.id, dto.lines)
    await self.balance_repo.update_balances(dto.lines)
    await self.uow.commit()
# Auto-rollback jika exception
```

**Note:** Detail implementasi mungkin perlu penyesuaian

---

### 7. Hard vs Soft Rules (Decision #85)

**Contradiction:**
- Dev Standards: Validasi embedded in code
- Business Standards: Banyak rules configurable per organization

**Resolution:** Developer Settings / Feature Flags

**Concept:**
```python
SYSTEM_SETTINGS = {
    "delete_mode": "soft",           # Toggle soft/hard delete
    "period_lock_enforcement": True, # Toggle period lock
    "default_depreciation": "SL",    # Default method
    "enable_consolidation": True,    # Feature flag
}
```

**Note:** Konsep saja, detail dibahas nanti

---

### 8. Validation Architecture (Decision #86)

**Contradiction:**
- Dev Standards: Pydantic only
- Business Standards: Complex business rules butuh database checks

**Resolution:** 2-layer validation

**Layer 1 - Pydantic (Schema):**
```python
class CreateJournalDTO(BaseModel):
    transaction_date: date
    lines: List[JournalLineDTO]

    @field_validator('lines')
    def min_two_lines(cls, v):
        if len(v) < 2:
            raise ValueError("Minimum 2 lines")
        return v
```

**Layer 2 - Validator Service (Business):**
```python
class JournalValidator:
    async def validate(self, dto) -> List[ValidationError]:
        errors = []
        # Journal must balance
        if total_debit != total_credit:
            errors.append(ValidationError("JOURNAL_NOT_BALANCED"))
        # Period must be open
        if period.status != 'OPEN':
            errors.append(ValidationError("PERIOD_NOT_OPEN"))
        return errors
```

---

### 9. Action API Endpoints (Decision #87)

**Contradiction:**
- Dev Standards: CRUD patterns only
- Business Standards: Butuh action endpoints (post, reverse, close)

**Resolution:** Verb in URL pattern

**Convention:**
```
POST /api/v1/{resource}/{id}/{action}

Examples:
POST /api/v1/journals/{id}/post
POST /api/v1/journals/{id}/reverse
POST /api/v1/periods/{id}/close
POST /api/v1/periods/{id}/reopen
```

**Rationale:** Industry standard (GitHub, Stripe, PayPal)

---

### 10. Caching Strategy (Decision #88)

**Contradiction:**
- Dev Standards: Fixed TTL (5 menit)
- Business Standards: Accounting data butuh context-aware

**Resolution:** Hybrid: Context-aware TTL + Event-driven invalidation

**TTL by Period Status:**
| Status | TTL |
|--------|-----|
| OPEN | 30 seconds |
| CLOSED | 1 hour |
| LOCKED | 24 hours |

**Event Invalidation:**
- On journal post → invalidate balance cache
- On period close → update TTL

---

### 11. TimescaleDB for Accounting (Decision #89)

**Contradiction:**
- Dev Standards: TimescaleDB untuk operational only
- Business Standards: Account balances butuh time-series

**Resolution:** Extend TimescaleDB usage

**Hypertable (append-only):**
- `account_balance_snapshots`
- `journal_audit_log`
- `exchange_rate_history`

**Regular Table (transactional):**
- `journal_entries`
- `journal_lines`
- `invoices`

---

### 12. Separation of Duties (Decision #90)

**Contradiction:**
- Dev Standards: Permission-based only
- Business Standards: SOD required (creator ≠ approver)

**Resolution:** 3 options dicatat untuk dibahas nanti

| Option | Approach |
|--------|----------|
| B | Simple: `created_by_id ≠ current_user` check |
| C | SOD Matrix configurable per organization |
| D | Full Workflow engine dengan approval chain |

---

### 13. Audit Trail Granularity (Decision #91)

**Contradiction:**
- Dev Standards: Row-level audit
- Business Standards: Field-level untuk sensitive data

**Resolution:** Field-level audit untuk semua perubahan

**Schema:**
```sql
CREATE TABLE audit_logs (
    entity_type VARCHAR(100),
    entity_id INTEGER,
    action VARCHAR(20),
    field_name VARCHAR(100),   -- Which field
    old_value TEXT,            -- Before
    new_value TEXT,            -- After
    changed_by_id INTEGER,
    changed_at TIMESTAMPTZ
);
```

---

### 14. Cross-Module References (Decision #92)

**Contradiction:**
- Dev Standards: Modular, loose coupling
- Business Standards: Banyak FK lintas module

**Resolution:** Shared Kernel pattern

**Shared Kernel (boleh FK):**
- `journal_entries`
- `coa_accounts`
- `fiscal_periods`
- `organizations`
- `users`

**Module-specific (FK ke shared only):**
- Billing: `invoices`, `payments`
- Assets: `fixed_assets`, `depreciation`
- Inventory: `items`, `stock_movements`

---

### 15. Report Architecture (Decision #93)

**Contradiction:**
- Dev Standards: Tidak ada pattern
- Business Standards: Butuh financial reports

**Resolution:** WYSIWYG pattern (sesuai standard yang sudah ada)

**Components:**
- Data Config (system-defined): Query, parameters
- Print Config (user-customizable): Layout, columns, fonts
- Report Engine: Merge data + config → output

---

### 16. Multi-Currency Storage (Decision #94)

**Contradiction:**
- Dev Standards: Tidak ada pattern
- Business Standards: Multi-currency support needed

**Resolution:** Store all three values

**Schema:**
```sql
original_amount DECIMAL(18,4),      -- 1,000.00 USD
exchange_rate DECIMAL(18,6),        -- 15,678.5432
base_amount DECIMAL(18,4),          -- 15,678,543.20 IDR
original_currency_id INTEGER,
```

**Rationale:** Fast query tanpa recalculation

---

### 17. Rounding Rules (Decision #95)

**Contradiction:**
- Dev Standards: Tidak ada standard
- Business Standards: Consistent rounding needed

**Resolution:** Configurable per organization

**Settings:**
```sql
rounding_method VARCHAR(20) DEFAULT 'half_up',
rounding_precision INTEGER DEFAULT 2,
adjustment_account_id INTEGER  -- Untuk selisih
```

**Methods:** half_up, half_even (banker's), down, up

---

### 18. Concurrent Edit Handling (Decision #96)

**Contradiction:**
- Dev Standards: Tidak ada pattern
- Business Standards: Protection dari concurrent edit

**Resolution:** Hybrid locking

| Data Type | Locking |
|-----------|---------|
| Regular entities | Optimistic (version check) |
| Critical (journal posting, period closing) | Pessimistic |

---

### 19. Batch Processing (Decision #97)

**Contradiction:**
- Dev Standards: Tidak ada pattern
- Business Standards: Bulk operations needed

**Resolution:** Hybrid: Celery + Database batch

**Flow:**
1. API receives bulk request
2. Create Celery task (async)
3. Celery job uses DB batch operations (COPY, bulk insert)
4. Update progress in Redis
5. Notify completion via WebSocket

---

### 20. Error Recovery for Batch (Decision #98)

**Contradiction:**
- Dev Standards: Generic error handling
- Business Standards: Financial transactions need specific recovery

**Resolution:** Per-item Atomic

**Principle:**
- Single transaction: All-or-nothing
- Batch of independent items: Each item atomic, batch allows partial success

**Result:**
```json
{
  "success": [1, 2, 3, ..., 99],
  "failed": [{"id": 51, "error": "Account inactive"}]
}
```

---

### 21. Decimal Calculation Precision (Decision #99)

**Contradiction:**
- Storage decided as DECIMAL(18,4)
- But intermediate calculations may need more precision

**Resolution:** 3-level rounding

| Stage | Precision | When to Round |
|-------|-----------|---------------|
| Calculation | 10 decimal | Never |
| Storage | 4 decimal | Before save to DB |
| Display | 0-2 decimal | Before show to user |

**Distribution:** Last item gets adjustment to balance total

---

## Implementation Priority

### Phase 1: Blocking (Week 1-2)
- #79 DECIMAL precision standardization
- #81 Soft delete columns
- #82 System Organization setup

### Phase 2: Core Patterns (Week 3-4)
- #83 Period lock enforcement
- #84 UnitOfWork implementation
- #86 Validation layers

### Phase 3: API & Caching (Week 5-6)
- #87 Action endpoints
- #88 Context-aware caching
- #92 Shared kernel structure

### Phase 4: Advanced (Week 7-8)
- #89 TimescaleDB for accounting
- #91 Field-level audit
- #94-99 Remaining patterns

---

## Notes

Decisions yang perlu detail lebih lanjut:
- **#84**: UnitOfWork implementation details
- **#85**: Feature flags structure
- **#90**: SOD enforcement approach (B, C, or D)

---

*Last Updated: 2025-12-07*
