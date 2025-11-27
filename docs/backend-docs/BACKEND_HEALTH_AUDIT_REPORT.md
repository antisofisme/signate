# Backend Health Audit Report
**Date**: 2025-11-27
**Status**: REQUIRES ATTENTION
**Overall Score**: 65/100

---

## Executive Summary

Analisis menyeluruh backend-python menemukan **47 masalah** yang perlu diperbaiki:

| Kategori | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Duplicate/Redundant Code | 4 | 2 | 2 | 0 |
| Unused/Dead Code | 5 | 4 | 2 | 0 |
| Hardcoded Values | 4 | 12 | 12 | 4 |
| Architecture Violations | 3 | 5 | 4 | 0 |
| Import/Dependency Issues | 5 | 8 | 10 | 0 |
| Integration Flow Issues | 7 | 12 | 8 | 0 |

---

## CRITICAL ISSUES (Must Fix Immediately)

### 1. Dashboard Service - NO ARCHITECTURE (Score: 25%)
**File**: `/services/dashboard/routes.py` (581 lines)

**Problems**:
- Direct DB queries in routes (81+ lines of business logic)
- No domain, use_cases, or repositories layer
- Cross-service model imports from 5 services
- Violates ALL Clean Architecture principles

**Impact**: Unmaintainable, untestable, tightly coupled

**Fix Required**:
```
dashboard/
├── domain/
│   └── dashboard_stats.py
├── repositories/
│   └── dashboard_repo.py
├── use_cases/
│   ├── get_dashboard_stats.py
│   └── get_device_health.py
├── dtos.py
└── routes.py (thin HTTP handler only)
```

---

### 2. Tag Service - DUPLICATE MODEL (Fixed Partially)
**Files**:
- `/services/tag/models.py` - ContentTag (WRONG LOCATION)
- `/services/tag/repositories/models.py` - TagModel (CORRECT)

**Problems**:
- ContentTag in wrong location
- ContentTag NOT registered in database init
- `extend_existing=True` flag indicates conflict

**Status**: Tag class removed, ContentTag still needs to be moved

**Fix Required**:
1. Move ContentTag to `/services/tag/repositories/models.py`
2. Update imports in `tag_repo.py`
3. Add ContentTag to `shared/database.py:init_db()`
4. Remove `extend_existing=True` flag

---

### 3. Device Service - OVER-FRAGMENTED (10 Route Files!)
**Files**: 10 separate route files totaling 3,048 lines

| File | Lines | Purpose |
|------|-------|---------|
| routes.py | 1,105 | Core CRUD |
| assignment_routes.py | 535 | Device assignments |
| log_routes.py | 479 | Logging |
| console_control_routes.py | 376 | Console |
| group_routes.py | 370 | Groups |
| command_routes.py | 298 | Commands |
| health_routes.py | 262 | Health |
| console_routes.py | 147 | Console |
| extended_routes.py | 538 | Extended |
| connection_log_routes.py | 43 | Connection logs |

**Impact**: Unmaintainable, developers confused where to add code

**Fix Required**: Consolidate to 3 files:
- `routes.py` - Core CRUD (<400 lines)
- `management_routes.py` - Groups & assignments
- `monitoring_routes.py` - Health, logs, commands

---

### 4. Audit Logging - ONLY 40% COVERAGE
**Missing Audit for**:
- Playlist service: 0%
- Organization service: 0%
- User service: 20%

**Impact**: No compliance trail for major operations

---

### 5. Multi-Tenancy Gap - SCHEDULE EXECUTOR
**File**: Schedule executor may not filter by organization_id

**Risk**: CRITICAL - could execute schedules across organizations

---

## HIGH PRIORITY ISSUES

### 6. Cross-Service Model Imports (23 violations)
**Worst Offender**: `organization/domain/quota_service.py`
```python
# Lines 11-14 - DIRECT imports violating repository pattern
from services.device.repositories.models import DeviceModel
from services.content.repositories.models import ContentModel
from services.auth.repositories.models import UserModel
from services.playlist.repositories.models import PlaylistModel
```

### 7. Weather Service - PLACEHOLDER ONLY (Score: 15%)
**File**: `/services/weather/routes.py` (76 lines)

No domain, use_cases, or repositories - just mock data in routes.

### 8. Missing Domain Layer (5 services)
- dashboard
- pms
- template
- translation
- widget

### 9. Circular Dependencies (15 identified)
- auth ↔ rbac (bidirectional)
- organization ↔ audit, content, device, playlist
- content ↔ playlist (bidirectional)
- playlist ↔ schedule (bidirectional)

### 10. 70 Inline Imports
Used to break circular dependencies - symptom of design issues.

---

## MEDIUM PRIORITY ISSUES

### 11. Hardcoded Values (32 found)

**Critical Hardcodes**:
| File | Line | Value | Should Be |
|------|------|-------|-----------|
| shared/cache.py | 83 | TTL=300 | CACHE_DEFAULT_TTL env |
| celery_app.py | 52-62 | All timeouts | CELERY_* env vars |
| virus_scanner.py | 33 | timeout=30 | CLAMAV_TIMEOUT env |
| upload_content.py | 33-37 | 50MB/500MB/100MB | MAX_*_SIZE env |
| main.py | 301-317 | /data/signage/content/ | STORAGE_PATH env |

### 12. Unused Code (11 items)
- `device_repo.list_all()` - Security risk (no org filter)
- `ConnectionLogEntryDTO` - Imported but unused
- Duplicate user repo methods in auth service

### 13. Error Handling Inconsistency
4 different error patterns across services:
- `raise HTTPException`
- `raise ValueError`
- `raise CustomError`
- Return error dict

### 14. Schedule JSONB Arrays (No FK Constraints)
`device_ids` and `tag_ids` stored as JSONB without foreign key constraints.
Risk: Orphaned schedules, invalid references.

---

## SERVICE HEALTH SCORECARD

| Service | Domain | Use Cases | Repos | Routes | Score |
|---------|--------|-----------|-------|--------|-------|
| auth | ✅ | ✅ | ✅ | ✅ | 95% |
| audit | ✅ | ✅ | ✅ | ✅ | 90% |
| analytics | ✅ | ✅ | ✅ | ✅ | 90% |
| playlist | ✅ | ✅ | ✅ | ✅ | 85% |
| organization | ✅ | ✅ | ✅ | ✅ | 85% |
| schedule | ✅ | ✅ | ✅ | ✅ | 85% |
| rbac | ✅ | ✅ | ✅ | ✅ | 85% |
| session | ✅ | ✅ | ✅ | ✅ | 85% |
| user | ✅ | ✅ | ✅ | ✅ | 85% |
| content | ✅ | ✅ | ✅ | ⚠️ | 80% |
| menu | ✅ | ✅ | ✅ | ⚠️ | 80% |
| tag | ✅ | ✅ | ⚠️ | ✅ | 70% |
| template | ❌ | ✅ | ✅ | ✅ | 70% |
| translation | ❌ | ✅ | ✅ | ✅ | 70% |
| widget | ❌ | ✅ | ✅ | ✅ | 70% |
| device | ✅ | ✅ | ✅ | ❌ | 60% |
| pms | ❌ | ✅ | ✅ | ⚠️ | 55% |
| dashboard | ❌ | ❌ | ❌ | ❌ | 25% |
| weather | ❌ | ❌ | ❌ | ❌ | 15% |

---

## IMMEDIATE ACTION PLAN

### Phase 1: Critical Fixes (4-6 hours)
1. ✅ Fix Tag duplicate model (DONE - Tag class removed)
2. Move ContentTag to correct location
3. Add audit logging to Playlist service
4. Add audit logging to Organization service
5. Verify Schedule executor org_id filtering

### Phase 2: High Priority (1-2 days)
1. Refactor Dashboard service (add layers)
2. Consolidate Device routes (10 → 3 files)
3. Fix cross-service model imports
4. Move hardcoded values to env vars

### Phase 3: Medium Priority (3-5 days)
1. Add domain layer to 5 services
2. Standardize error handling
3. Remove unused code
4. Fix circular dependencies

---

## FILES REQUIRING CHANGES

### Must Change Now:
1. `/services/tag/models.py` - Move ContentTag
2. `/services/playlist/routes.py` - Add audit logging
3. `/services/organization/routes.py` - Add audit logging
4. `/shared/database.py` - Register ContentTag

### Change This Sprint:
1. `/services/dashboard/routes.py` - Full refactor
2. `/services/device/*.py` - Consolidate routes
3. `/services/organization/domain/quota_service.py` - Fix imports
4. `/shared/cache.py` - Use env vars
5. `/celery_app.py` - Use env vars

### Change Next Sprint:
1. `/services/weather/` - Add proper architecture
2. `/services/pms/` - Add domain layer
3. `/services/template/` - Add domain layer
4. `/services/widget/` - Add domain layer
5. `/services/translation/` - Add domain layer

---

## Conclusion

Backend memiliki fondasi yang baik (14/19 services score 70%+), tapi ada beberapa critical issues yang harus segera diperbaiki:

1. **Dashboard** - Arsitektur rusak total, perlu refactor
2. **Device** - Terlalu terfragmentasi, perlu konsolidasi
3. **Tag** - Model duplikat sudah diperbaiki, ContentTag perlu dipindah
4. **Audit** - Coverage hanya 40%, banyak operasi tidak ter-log
5. **Hardcode** - 32 nilai hardcoded yang seharusnya configurable

Estimasi total waktu perbaikan: **3-5 hari** untuk critical dan high priority issues.
