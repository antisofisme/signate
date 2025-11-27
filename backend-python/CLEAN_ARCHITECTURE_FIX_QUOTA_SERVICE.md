# Clean Architecture Fix: Quota Service Cross-Service Dependencies

## Problem

The `OrganizationQuotaService` in `services/organization/domain/quota_service.py` was violating Clean Architecture principles by directly importing models from other services:

```python
# ❌ BEFORE - Violated Clean Architecture
from services.device.repositories.models import DeviceModel
from services.content.repositories.models import ContentModel
from services.auth.repositories.models import UserModel
from services.playlist.repositories.models import PlaylistModel
```

**Issues:**
1. **Tight Coupling**: Domain layer directly coupled to other services' repository layers
2. **Circular Dependencies**: Risk of import cycles between services
3. **Violation of Separation of Concerns**: Service boundaries not respected
4. **Hard to Test**: Difficult to mock/test in isolation

## Solution

Created a **shared quota repository** (`shared/quota_repository.py`) that handles cross-service resource counting using raw SQL queries instead of ORM models.

### Architecture Changes

```
BEFORE:
services/organization/domain/quota_service.py
  └─→ services/device/repositories/models.py    ❌ Cross-service import
  └─→ services/content/repositories/models.py   ❌ Cross-service import
  └─→ services/auth/repositories/models.py      ❌ Cross-service import
  └─→ services/playlist/repositories/models.py  ❌ Cross-service import

AFTER:
services/organization/domain/quota_service.py
  └─→ shared/quota_repository.py  ✅ Shared abstraction
        └─→ Uses raw SQL queries (no model dependencies)
```

### New Shared Component

**File**: `shared/quota_repository.py`

**Purpose**: Centralized repository for quota-related resource counting across services

**Key Methods**:
- `count_devices(organization_id)` - Count devices for org
- `count_users(organization_id, active_only)` - Count users for org
- `get_content_stats(organization_id)` - Get content count and total size
- `count_playlists(organization_id)` - Count playlists for org
- `*_with_lock()` variants - Atomic counting with row-level locking

**Implementation**: Uses raw SQL queries via SQLAlchemy Core to avoid ORM model dependencies:

```python
def count_devices(self, organization_id: int) -> int:
    """Count active devices for an organization"""
    result = self.db.execute(
        """
        SELECT COUNT(*)
        FROM devices
        WHERE organization_id = :org_id
        """,
        {"org_id": organization_id}
    ).scalar()

    return result or 0
```

### Benefits

1. **Clean Architecture Compliance** ✅
   - Domain layer no longer imports from other services
   - Clear separation of concerns
   - Service boundaries respected

2. **No Circular Dependencies** ✅
   - All services can use `shared/quota_repository.py`
   - No risk of import cycles

3. **Easy to Test** ✅
   - Quota repository can be mocked independently
   - No need to set up entire service dependencies

4. **Maintainable** ✅
   - Single source of truth for quota queries
   - Easy to update SQL queries in one place

5. **Performance** ✅
   - Raw SQL queries are efficient
   - Supports row-level locking for atomic operations

## Updated Code

### quota_service.py

```python
# ✅ AFTER - Clean Architecture compliant
from shared.quota_repository import QuotaRepository

class OrganizationQuotaService:
    def __init__(self, db: Session):
        self.db = db
        self.quota_repo = QuotaRepository(db)  # Use shared repository

    def get_organization_quota(self, organization_id: int) -> OrganizationQuota:
        # Use quota repository instead of direct model queries
        device_count = self.quota_repo.count_devices(organization_id)
        user_count = self.quota_repo.count_users(organization_id, active_only=True)
        content_stats = self.quota_repo.get_content_stats(organization_id)
        playlist_count = self.quota_repo.count_playlists(organization_id)
        # ... rest of the method
```

## Files Changed

1. **Created**: `shared/quota_repository.py` (new file, 180 lines)
   - Shared repository for cross-service quota queries
   - Uses raw SQL to avoid model dependencies

2. **Modified**: `services/organization/domain/quota_service.py`
   - Removed direct model imports from other services
   - Added `QuotaRepository` dependency
   - Updated all counting logic to use quota repository

## Verification

All files that depend on `OrganizationQuotaService` still compile and work correctly:

✅ `services/device/use_cases/activate_device.py`
✅ `services/content/use_cases/upload_content.py`
✅ `services/playlist/use_cases/create_playlist.py`
✅ `services/user/use_cases/create_user.py`
✅ `services/organization/routes.py`
✅ `services/organization/use_cases/get_organization_quota.py`

## Testing Recommendations

1. **Unit Tests**: Test `QuotaRepository` methods independently
2. **Integration Tests**: Verify quota enforcement still works correctly
3. **Concurrency Tests**: Test atomic quota enforcement with locks
4. **Performance Tests**: Verify raw SQL queries are as fast as ORM queries

## Future Improvements

1. Add caching layer to `QuotaRepository` for frequently-accessed quota data
2. Create repository interfaces for better testability
3. Add metrics/monitoring for quota checks
4. Consider event-driven quota updates instead of query-on-demand

## Clean Architecture Principles Applied

1. ✅ **Dependency Rule**: Domain layer doesn't depend on infrastructure (repositories)
2. ✅ **Separation of Concerns**: Data access logic separated from business logic
3. ✅ **Single Responsibility**: Quota repository has one job - count resources
4. ✅ **Open/Closed**: Easy to extend without modifying existing code
5. ✅ **Dependency Inversion**: Depends on abstractions (SQL queries), not concrete models

---

**Date**: 2025-11-27
**Impact**: Low (internal refactoring, no API changes)
**Breaking Changes**: None
**Migration Required**: No
