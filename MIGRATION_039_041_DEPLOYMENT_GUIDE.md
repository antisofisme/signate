# Migration 039-041 Deployment Guide
## Standardize Database Naming Conventions

**Date**: 2025-11-13
**Migrations**: 039, 040, 041
**Impact**: MEDIUM - Breaking changes to column names
**Downtime Required**: ~5 minutes (recommended maintenance window)

---

## Overview

These migrations fix naming inconsistencies in the database:

1. **Migration 039**: Standardize FK naming - Add `_id` suffix to audit trail columns
2. **Migration 040**: Remove duplicate `users.role` column
3. **Migration 041**: Rename `organizations.organization_pin` to `pin`

### Changes Summary:
- **13 columns renamed** (created_by → created_by_id, etc.)
- **1 column removed** (users.role)
- **1 column renamed** (organization_pin → pin)
- **34 Python files updated** automatically
- **55 code references updated**

---

## Pre-Deployment Checklist

### ✅ Before You Start:

1. **Backup Database** ✅ CRITICAL
   ```bash
   # Create backup
   cd /mnt/g/khoirul/signate
   sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
     "docker exec signage-postgres pg_dump -U signage_user -d signage_db --clean --if-exists" \
     > backups/pre_migration_039_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Stop Backend Service** (to prevent errors during migration)
   ```bash
   sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
     "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"
   ```

3. **Verify Migration Files**
   ```bash
   ls -lah backend-python/migrations/039*.sql
   ls -lah backend-python/migrations/040*.sql
   ls -lah backend-python/migrations/041*.sql
   ```

---

## Deployment Steps

### Step 1: Upload Migration Files to Server

```bash
cd /mnt/g/khoirul/signate

# Upload migration files
sshpass -p 'Password@2021' scp \
  backend-python/migrations/039_standardize_fk_naming.sql \
  backend-python/migrations/040_remove_duplicate_role_column.sql \
  backend-python/migrations/041_rename_organization_pin.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/
```

### Step 2: Run Migrations (ONE BY ONE)

**IMPORTANT**: Run migrations sequentially, verify each one succeeds before next!

#### Migration 039: Standardize FK Naming

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/039_standardize_fk_naming.sql"
```

**Expected Output**:
```
ALTER TABLE
ALTER TABLE
ALTER TABLE
...
NOTICE:  ✅ Migration successful: All audit trail columns renamed with _id suffix
```

**Verify**:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c '\d devices'" | grep created_by
```
Should show: `created_by_id` (NOT `created_by`)

---

#### Migration 040: Remove Duplicate Role Column

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/040_remove_duplicate_role_column.sql"
```

**Expected Output**:
```
NOTICE:  ✅ All users already have role_id populated
NOTICE:  ✅ Created backup of role data in temp table users_role_backup
ALTER TABLE
NOTICE:  ✅ Migration successful: Duplicate role column removed, role_id retained
```

**Verify**:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c '\d users'" | grep role
```
Should show ONLY: `role_id` (NOT `role`)

---

#### Migration 041: Rename organization_pin

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/041_rename_organization_pin.sql"
```

**Expected Output**:
```
ALTER TABLE
NOTICE:  ✅ Migration successful: organization_pin renamed to pin
```

**Verify**:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c '\d organizations'" | grep pin
```
Should show: `pin` (NOT `organization_pin`)

---

### Step 3: Sync Updated Python Code to Server

```bash
cd /mnt/g/khoirul/signate

# Sync entire backend-python directory (includes model updates)
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  backend-python/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/
```

**Verify**:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "grep -r 'created_by_id' /home/gzjbbk/signate/backend-python/services/ | head -5"
```
Should show references to `created_by_id` (not `created_by`)

---

### Step 4: Rebuild and Restart Backend

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml up -d --build backend-api"
```

**Wait for container to be healthy** (~30 seconds):
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend --tail 20"
```

**Expected**: Should see "Application startup complete" with no errors

---

### Step 5: Verify Backend is Running

```bash
# Check health endpoint
curl http://192.168.5.12:8001/health

# Should return: {"status": "healthy"}
```

---

## Post-Deployment Verification

### Test 1: Device Creation (uses created_by_id)

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Request device code (should use created_by_id internally)
curl -s -X POST http://192.168.5.12:8001/api/v1/devices/request-code \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"organization_id":4}' | jq
```

**Expected**: Should return device code successfully (no errors about `created_by`)

---

### Test 2: Playlist Creation (uses created_by_id)

```bash
curl -s -X POST http://192.168.5.12:8001/api/v1/playlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Playlist Migration","organization_id":4}' | jq
```

**Expected**: Should create playlist successfully (no errors about `created_by`)

---

### Test 3: User Query (uses role_id only)

```bash
curl -s -X GET "http://192.168.5.12:8001/api/v1/users" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected**: Should return users with `role_id` (NO `role` string field)

---

### Test 4: Organization Query (uses pin)

```bash
curl -s -X GET "http://192.168.5.12:8001/api/v1/organizations" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected**: Should return organizations with `pin` field (NO `organization_pin`)

---

## Rollback Procedure (If Needed)

### If Migration Fails:

**Step 1: Restore Database Backup**
```bash
cd /mnt/g/khoirul/signate/backups

# Stop backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"

# Restore backup
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backups/pre_migration_039_YYYYMMDD_HHMMSS.sql"

# Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml start backend-api"
```

**Step 2: Revert Code Changes**
```bash
cd /mnt/g/khoirul/signate
git checkout backend-python/  # If using git
# OR manually revert files
```

---

## Known Issues & Solutions

### Issue 1: "Column created_by does not exist"
**Cause**: Migration 039 not run, but code updated
**Solution**: Run migration 039 first, then restart backend

### Issue 2: "Role field missing in response"
**Cause**: Frontend/tests expect `role` string field
**Solution**: Update frontend to use `role_id` or join with roles table

### Issue 3: Foreign key constraint violation
**Cause**: Old code still using old column names
**Solution**: Ensure all Python code updated (check MODEL_UPDATE_REPORT.txt)

---

## Files Changed

### Migration Files (3):
- `backend-python/migrations/039_standardize_fk_naming.sql`
- `backend-python/migrations/040_remove_duplicate_role_column.sql`
- `backend-python/migrations/041_rename_organization_pin.sql`

### Python Code (34 files):
See `MODEL_UPDATE_REPORT.txt` for complete list

**Key Files Updated**:
- All `models.py` files (SQLAlchemy models)
- All `routes.py` files (API endpoints)
- All `*_repo.py` files (repositories)
- All `use_cases/*.py` files (business logic)
- DTOs in `services/*/dtos.py`

---

## Manual Review Required

### 1. CurrentUser Pydantic Model
**File**: `backend-python/shared/dependencies.py` or `services/auth/dtos.py`

Check if `CurrentUser` has `role` field:
```python
class CurrentUser(BaseModel):
    id: int
    username: str
    role: str  # ❌ Remove this if exists
    role_id: int  # ✅ Keep this
    organization_id: int
```

### 2. Frontend Integration
If frontend uses `user.role` string, update to:
```typescript
// OLD
const role = user.role;  // ❌

// NEW - Option A: Use role_id
const roleId = user.role_id;  // ✅

// NEW - Option B: Join with roles
const role = user.role_details?.name;  // ✅ If backend provides join
```

### 3. Tests
Update test assertions:
```python
# OLD
assert device.created_by == user_id  # ❌

# NEW
assert device.created_by_id == user_id  # ✅
```

---

## Success Criteria

✅ All 3 migrations run without errors
✅ Backend starts successfully (no import errors)
✅ Health endpoint returns 200 OK
✅ Device creation works (uses created_by_id)
✅ Playlist creation works (uses created_by_id)
✅ User queries work (returns role_id, not role)
✅ Organization queries work (returns pin, not organization_pin)
✅ No foreign key errors in logs

---

## Timeline Estimate

| Step | Duration |
|------|----------|
| Backup database | 1 min |
| Stop backend | 30 sec |
| Run migrations | 2 min |
| Sync code | 1 min |
| Rebuild backend | 2 min |
| Verification tests | 2 min |
| **Total** | **~9 minutes** |

---

## Support & Troubleshooting

### Check Backend Logs:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend --tail 100"
```

### Check Database Schema:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c '\d+ devices'"
```

### Grep for Old Column Names (should find none):
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "grep -r 'created_by[^_]' /home/gzjbbk/signate/backend-python/services/"
```

---

## Conclusion

After successful deployment:
- ✅ FK naming is **consistent** (all use `_id` suffix)
- ✅ No data redundancy (`users.role` removed)
- ✅ Cleaner naming (`pin` instead of `organization_pin`)
- ✅ Database score improves from **62/100 to ~85/100**

**Next Steps**: Consider running integration tests again to verify all functionality still works!
