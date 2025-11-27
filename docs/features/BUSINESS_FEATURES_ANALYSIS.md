# Business Features Analysis Report

## Executive Summary

Analisis mendalam 6 fitur bisnis utama sebelum integrasi dengan 5 Core Services (Auth, User, Organization, RBAC, Audit).

**Fitur yang Dianalisis:**
1. Device Service
2. Device Group Service
3. Content Service
4. Playlist Service
5. Schedule Service
6. Tag Service

---

## Consolidated Gap Matrix

### Legend
- ✅ Fully Implemented
- ⚠️ Partially Implemented
- ❌ Not Implemented

| Aspect | Device | Device Group | Content | Playlist | Schedule | Tag |
|--------|--------|--------------|---------|----------|----------|-----|
| **Multi-Tenancy (organization_id)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **created_by_id tracking** | ✅ | ✅ | ✅ (uploaded_by_id) | ✅ | ✅ | ❌ |
| **updated_by_id tracking** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **RBAC Permission Checks** | ⚠️ Org-level only | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Audit Logging (AuditLogger)** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| **Soft Delete Pattern** | ❌ Hard delete | ✅ | ✅ | ✅ | ❌ Hard delete | ❌ Hard delete |

---

## Detailed Analysis Per Feature

### 1. DEVICE SERVICE

**Location:** `backend-python/services/device/`

#### Strengths ✅
- **Multi-tenancy:** Excellent - organization_id enforced at every layer
- **Audit tracking:** created_by_id, updated_by_id columns exist
- **AuditLogger:** Comprehensive logging for activate, update, delete, hard_reset
- **Security:** Device JWT tokens, cryptographic codes, race condition handling
- **Clean Architecture:** Proper layer separation

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| RBAC not enforced | HIGH | Only org-level isolation, no role-based checks |
| Hard delete | MEDIUM | Device deletion is permanent (should be soft delete) |
| Health metrics no user context | LOW | Metrics from device, can't track who requested |

#### Files to Fix:
- `services/device/routes.py` - Add RBAC decorators
- `services/device/repositories/models.py` - Add deleted_at column

---

### 2. DEVICE GROUP SERVICE

**Location:** `backend-python/services/device/` (management_routes.py)

#### Strengths ✅
- **Multi-tenancy:** Strong - triple-checked (device org + group org match)
- **Hierarchy:** Self-referential parent_group_id for nested groups
- **Soft delete:** Uses deleted_at pattern
- **Membership tracking:** added_by_id tracked

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| No updated_by_id | CRITICAL | Cannot audit who modified groups |
| No deleted_by_id | CRITICAL | Cannot audit who deleted groups |
| No RBAC enforcement | HIGH | VIEWER can delete groups! |
| No audit_logs entries | HIGH | Metadata only, no centralized audit trail |
| Computed fields null | MEDIUM | device_count, parent_name not populated |

#### Files to Fix:
- `services/device/repositories/models.py` - Add updated_by_id, deleted_by_id
- `services/device/management_routes.py` - Add RBAC + AuditLogger

---

### 3. CONTENT SERVICE

**Location:** `backend-python/services/content/`

#### Strengths ✅
- **Multi-tenancy:** Row-level org_id filters everywhere
- **User tracking:** uploaded_by_id (immutable), assigned_by_id
- **Audit logging:** Comprehensive (upload, update, delete, bulk ops)
- **Security:** Virus scanning, path traversal prevention, quota enforcement
- **Soft delete:** Uses deleted_at pattern

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| RBAC NOT enforced | CRITICAL | Routes don't check permissions! |
| No updated_by_id | HIGH | Can't track who edited content metadata |
| UpdateUseCase no org filter | MEDIUM | Gets content without org check first |

#### RBAC Permissions Defined but NOT Used:
```python
'contents': {
    'SUPER_ADMIN': ['view', 'create', 'edit', 'delete', 'manage'],
    'ADMIN': ['view', 'create', 'edit', 'delete'],
    'CONTENT_MANAGER': ['view', 'create', 'edit', 'delete'],
    'VIEWER': ['view']  # <-- NOT ENFORCED!
}
```

#### Files to Fix:
- `services/content/routes.py` - Add require_permission decorators
- `services/content/repositories/models.py` - Add updated_by_id column
- `services/content/use_cases/update_content.py` - Fix org filter

---

### 4. PLAYLIST SERVICE

**Location:** `backend-python/services/playlist/`

#### Strengths ✅
- **Multi-tenancy:** Always filtered on every query
- **created_by_id:** Tracked in database
- **Audit logging:** 10 actions logged (create, update, delete, assign, etc.)
- **Content relationships:** Proper M2M with ordering
- **Cache invalidation:** P0-7 fix for content resolver

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| No RBAC enforcement | CRITICAL | Only authentication, no role checks |
| No updated_by_id | HIGH | Individual content additions not attributed |
| Client endpoints public | MEDIUM | No auth for player endpoints |

#### Files to Fix:
- `services/playlist/routes.py` - Add RBAC decorators
- `services/playlist/repositories/models.py` - Add updated_by_id

---

### 5. SCHEDULE SERVICE

**Location:** `backend-python/services/schedule/`

#### Strengths ✅
- **Multi-tenancy:** organization_id on all queries
- **Audit trail:** created_by_id, updated_by_id (Migration 046)
- **AuditLogger:** Actions logged (create, update, delete)
- **Background executor:** ScheduleExecutor with device targeting

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| RBAC NOT enforced | CRITICAL | Permissions defined but not checked! |
| No FK to devices/tags | MEDIUM | JSONB arrays, no referential integrity |
| updated_by_id null on create | LOW | Only set on updates |
| Hard delete | MEDIUM | Should use soft delete |

#### RBAC Defined but NOT Enforced:
```python
'schedules': {
    'SUPER_ADMIN': ['view', 'create', 'edit', 'delete', 'manage'],
    'ADMIN': ['view', 'create', 'edit', 'delete'],
    'CONTENT_MANAGER': ['view', 'create', 'edit'],
    'VIEWER': ['view']  # <-- NOT ENFORCED!
}
```

#### Files to Fix:
- `services/schedule/routes.py` - Add RBAC decorators
- `services/schedule/repositories/models.py` - Add deleted_at

---

### 6. TAG SERVICE

**Location:** `backend-python/services/tag/`

#### Strengths ✅
- **Multi-tenancy:** Excellent - org_id enforced everywhere
- **Clean Architecture:** Proper domain → use cases → repository
- **Audit logging:** All mutations logged
- **Bulk operations:** With metrics (assigned/skipped/failed)

#### Gaps ❌
| Issue | Severity | Details |
|-------|----------|---------|
| No created_by_id column | CRITICAL | Database doesn't track creator |
| No updated_by_id column | CRITICAL | Database doesn't track updater |
| No RBAC checks | HIGH | All authenticated users can do everything |
| Hard delete | MEDIUM | Should use soft delete |

#### Files to Fix:
- `services/tag/repositories/models.py` - Add created_by_id, updated_by_id, deleted_at
- `services/tag/routes.py` - Add RBAC decorators

---

## Cross-Feature Integration Issues

### 1. Device → Content/Playlist Assignment
- Device has `assigned_playlist_id` (FK) ✅
- Device has `background_audio_id` (FK to content) ✅
- **Issue:** No audit when playlist/content assigned to device

### 2. Schedule → Device/Tag Targeting
- Schedule uses JSONB arrays for device_ids, tag_ids
- **Issue:** No referential integrity - orphan IDs possible
- **Issue:** No audit when schedule targeting changes

### 3. Content → Playlist Items
- Proper M2M via playlist_contents table
- **Issue:** No tracking of who added content to playlist

### 4. Tag → Device/Content
- M2M via device_tags, content_tags
- device_tags has assigned_by_id ✅
- **Issue:** content_tags missing assigned_by_id

---

## Priority Fix Matrix

### CRITICAL (Must Fix Before Production)

| # | Feature | Issue | Fix Required |
|---|---------|-------|--------------|
| 1 | ALL | RBAC not enforced | Add require_permission decorators |
| 2 | Device Group | No updated_by_id | Add column + track in routes |
| 3 | Device Group | No deleted_by_id | Add column + track in routes |
| 4 | Tag | No created_by_id | Add column + migration |
| 5 | Tag | No updated_by_id | Add column + migration |
| 6 | Content | RBAC bypass | Add permission checks |

### HIGH (Should Fix Soon)

| # | Feature | Issue | Fix Required |
|---|---------|-------|--------------|
| 7 | Content | No updated_by_id | Add column |
| 8 | Playlist | No updated_by_id | Add column |
| 9 | Schedule | Hard delete | Add soft delete |
| 10 | Tag | Hard delete | Add soft delete |
| 11 | Device | Hard delete | Add soft delete |

### MEDIUM (Nice to Have)

| # | Feature | Issue | Fix Required |
|---|---------|-------|--------------|
| 12 | Device Group | Computed fields null | Populate device_count |
| 13 | Schedule | JSONB integrity | Consider FK tables |
| 14 | Content Tags | No assigned_by_id | Add to junction table |

---

## Implementation Plan

### Phase 1: Database Migrations (New Migration 052+)

```sql
-- Migration 052: Add audit trail columns to business tables

-- 1. Device Groups
ALTER TABLE device_groups ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE device_groups ADD COLUMN deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 2. Tags
ALTER TABLE tags ADD COLUMN created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE tags ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE tags ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE tags ADD COLUMN deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 3. Contents
ALTER TABLE contents ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 4. Playlists
ALTER TABLE playlists ADD COLUMN updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 5. Devices (soft delete)
ALTER TABLE devices ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE devices ADD COLUMN deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 6. Schedules (soft delete)
ALTER TABLE schedules ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE schedules ADD COLUMN deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 7. Content Tags (assigned_by)
ALTER TABLE content_tags ADD COLUMN assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
```

### Phase 2: Model Updates

Update SQLAlchemy models for all affected tables:
- Add new columns
- Add relationships for created_by, updated_by, deleted_by
- Update `_to_entity` methods

### Phase 3: RBAC Integration

Add to ALL route files:
```python
from shared.auth import require_permission

@router.post("/...")
@require_permission("contents", "create")
def create_content(...):
    ...
```

### Phase 4: Audit Trail Updates

Update all routes to pass user context:
```python
# In use case calls
use_case.execute(
    ...,
    created_by_id=current_user.id,  # Add where missing
    updated_by_id=current_user.id,  # Add where missing
)

# In delete operations
use_case.soft_delete(
    ...,
    deleted_by_id=current_user.id,
)
```

---

## Files Reference

### Routes to Update (RBAC)
- `services/device/routes.py`
- `services/device/management_routes.py`
- `services/content/routes.py`
- `services/playlist/routes.py`
- `services/schedule/routes.py`
- `services/tag/routes.py`

### Models to Update (Audit Columns)
- `services/device/repositories/models.py`
- `services/content/repositories/models.py`
- `services/playlist/repositories/models.py`
- `services/schedule/repositories/models.py`
- `services/tag/repositories/models.py`

### Use Cases to Update
- All create/update/delete use cases need user_id parameter

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Features Analyzed | 6 |
| Critical Issues | 6 |
| High Issues | 5 |
| Medium Issues | 3 |
| Tables Needing Migration | 7 |
| Route Files Needing RBAC | 6 |

**Overall Assessment:** Good foundation with consistent multi-tenancy, but RBAC enforcement and complete audit trails are missing across all business features.

---

*Generated: 2025-11-27*
*Next Step: Apply core-services-integration skill for standardized fixes*
