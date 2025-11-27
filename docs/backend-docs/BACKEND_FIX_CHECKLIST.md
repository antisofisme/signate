# Backend Fix Checklist
**Priority**: Critical → High → Medium

---

## CRITICAL (Fix Today)

### [ ] 1. Move ContentTag to Correct Location
```bash
# Current (WRONG):
services/tag/models.py → ContentTag

# Target (CORRECT):
services/tag/repositories/models.py → ContentTag
```

**Steps**:
1. Copy ContentTag class to `repositories/models.py`
2. Update imports in `tag_repo.py` (6 locations)
3. Delete `services/tag/models.py`
4. Add ContentTag to `shared/database.py:init_db()`

---

### [ ] 2. Add Playlist Audit Logging
**File**: `/services/playlist/routes.py`

**Add audit log to**:
- create_playlist (line ~80)
- update_playlist (line ~120)
- delete_playlist (line ~160)
- assign_to_devices (line ~200)
- assign_to_tags (line ~240)

**Pattern**:
```python
audit_logger.log_action(
    user_id=current_user["user_id"],
    action="playlist.create",
    resource_type="playlist",
    resource_id=playlist.id,
    details={"name": playlist.name},
    organization_id=current_user["organization_id"]
)
```

---

### [ ] 3. Add Organization Audit Logging
**File**: `/services/organization/routes.py`

**Add audit log to**:
- create_organization
- update_organization
- delete_organization

---

### [ ] 4. Verify Schedule Executor Multi-Tenancy
**File**: `/services/schedule/domain/schedule_executor.py`

**Check**:
```python
# MUST have organization_id filter in all queries
schedules = db.query(ScheduleModel).filter(
    ScheduleModel.organization_id == org_id  # THIS MUST EXIST
)
```

---

## HIGH (Fix This Week)

### [ ] 5. Dashboard Service Refactor
**Current**: 581 lines in routes.py with direct DB queries
**Target**: Proper Clean Architecture

**Create**:
```
services/dashboard/
├── domain/
│   └── dashboard_stats.py
├── repositories/
│   └── dashboard_repo.py
├── use_cases/
│   ├── get_dashboard_stats.py
│   └── get_device_health.py
├── dtos.py
└── routes.py (< 100 lines)
```

---

### [ ] 6. Consolidate Device Routes
**Current**: 10 files, 3,048 lines
**Target**: 3 files, ~1,000 lines each

**Merge**:
- `routes.py` + `extended_routes.py` → `routes.py`
- `assignment_routes.py` + `group_routes.py` → `management_routes.py`
- `health_routes.py` + `log_routes.py` + `command_routes.py` + `console_*.py` + `connection_log_routes.py` → `monitoring_routes.py`

---

### [ ] 7. Fix quota_service Cross-Service Imports
**File**: `/services/organization/domain/quota_service.py`

**Current (WRONG)**:
```python
from services.device.repositories.models import DeviceModel
from services.content.repositories.models import ContentModel
```

**Fix**: Use repository interfaces or service calls instead of direct model imports.

---

### [ ] 8. Move Hardcoded Values to ENV

**shared/cache.py:83**:
```python
# Before
DEFAULT_TTL = 300

# After
DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
```

**celery_app.py:52-62**:
```python
# Before
task_soft_time_limit=300

# After
task_soft_time_limit=int(os.getenv("CELERY_TASK_SOFT_LIMIT", "300"))
```

**virus_scanner.py:33**:
```python
# Before
timeout=30

# After
timeout=int(os.getenv("CLAMAV_TIMEOUT", "30"))
```

---

## MEDIUM (Fix Next Sprint)

### [ ] 9. Add Domain Layer to Services
- [ ] `/services/pms/domain/`
- [ ] `/services/template/domain/`
- [ ] `/services/translation/domain/`
- [ ] `/services/widget/domain/`
- [ ] `/services/weather/domain/`

### [ ] 10. Standardize Error Handling
**Create**: `/shared/exceptions.py`
```python
class ValidationError(Exception):
    pass

class NotFoundError(Exception):
    pass

class AuthorizationError(Exception):
    pass
```

**Update error handler in main.py** to catch these.

### [ ] 11. Remove Unused Code
- [ ] Delete `device_repo.list_all()` (security risk)
- [ ] Remove unused `ConnectionLogEntryDTO` import
- [ ] Clean up duplicate user repo methods

### [ ] 12. Fix Schedule JSONB → M2M Tables
**Current**:
```python
device_ids = Column(JSONB)  # No FK constraint
tag_ids = Column(JSONB)     # No FK constraint
```

**Target**:
```sql
CREATE TABLE schedule_devices (
    schedule_id INT REFERENCES schedules(id) ON DELETE CASCADE,
    device_id INT REFERENCES devices(id) ON DELETE CASCADE
);

CREATE TABLE schedule_tags (
    schedule_id INT REFERENCES schedules(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE
);
```

---

## Verification Commands

```bash
# Check for duplicate models
grep -r "extend_existing" backend-python/services/

# Check for direct model imports across services
grep -r "from services\.[a-z]*\.repositories\.models import" backend-python/services/ | grep -v "from services\.\($(basename $PWD)\)"

# Check audit logging coverage
grep -r "audit_logger.log_action" backend-python/services/ | wc -l

# Find hardcoded values
grep -rn "= 300\|= 30\|= 50\|= 100\|= 500" backend-python/services/
```

---

## After Fixes - Run Tests

```bash
# Start backend
cd backend-python
docker compose up -d backend-api

# Test Tag operations
curl -X GET http://localhost:8001/api/v1/tags
curl -X POST http://localhost:8001/api/v1/tags -d '{"tag_name":"test"}'
curl -X PUT http://localhost:8001/api/v1/tags/1 -d '{"tag_name":"updated"}'
curl -X DELETE http://localhost:8001/api/v1/tags/1

# Test Playlist with audit
curl -X POST http://localhost:8001/api/v1/playlists -d '{"name":"test"}'
# Check audit logs
curl http://localhost:8001/api/v1/audit-logs?resource_type=playlist

# Test Dashboard
curl http://localhost:8001/api/v1/dashboard/stats
```
