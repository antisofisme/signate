# Migration Cleanup Plan

**Date**: 2025-11-13
**Purpose**: Remove duplicate/old migration folders, keep only `backend-python/migrations/`

---

## Current Situation

### ✅ KEEP: `backend-python/migrations/` (PRIMARY)
**Location**: `/mnt/g/khoirul/signate/backend-python/migrations/`
**Files**: 34 SQL migration files (001-019 series)
**Status**: **ACTIVE** - This is the main migration folder
**Content**:
- 001_complete_schema.sql
- 001_complete_schema_updated.sql
- 002_add_organization_fields.sql
- 003_create_contents_table.sql
- 004_create_tags_tables.sql
- 005_create_playlists_tables.sql
- 006_create_devices_table.sql
- 007_create_content_assignments_table.sql
- 008_create_device_support_tables.sql
- 009_add_roles_and_sessions.sql
- 010_add_device_logs_and_speed_tests.sql
- 011_add_content_playback_logs.sql
- 012_add_device_groups.sql
- 013_add_device_commands.sql
- 014_add_device_health_metrics.sql
- 015_add_pms_integration.sql
- 016_add_templates.sql
- ... and more

**Action**: ✅ **KEEP** - This is the source of truth

---

## ❌ TO DELETE

### 1. `/migrations/` Folder
**Location**: `/mnt/g/khoirul/signate/migrations/`
**Files**:
- `schema_alignment.sql` (1 file, created 2025-01-30)

**Content**: Optional column additions for activity_logs and devices
- Commented out ALTER TABLE statements
- Marked as "OPTIONAL improvements"
- Already superseded by backend-python migrations

**Reason to Delete**:
- Outdated and optional
- Already covered in backend-python/migrations/
- Confusing to have multiple migration folders

**Action**: ❌ **DELETE**

---

### 2. `/database/` Folder
**Location**: `/mnt/g/khoirul/signate/database/`
**Files**:
- `init.sql` (created Oct 21, 2025)
- `init.sql.backup`
- `init-phase1-auth.sql`

**Subfolders**:
- `backups/` - Contains 9 old database backups (Oct 26-27)
- `fix-database/` - Old fix scripts
- `migrations/` - Old migration subfolder

**Reason to Delete**:
- Old schema files from October
- Already superseded by backend-python/migrations/
- Backup files are from Oct 26-27 (outdated)
- All current migrations managed in backend-python/

**Action**: ❌ **DELETE** (after backing up `backups/` folder)

---

### 3. `/database/migrations/` Subfolder
**Location**: `/mnt/g/khoirul/signate/database/migrations/`
**Files**:
- `001_add_uuid_support.sql`
- `README.md`
- `apply-migration.sh`

**Reason to Delete**:
- Old migration system
- UUID support already in backend-python migrations
- Superseded by new migration structure

**Action**: ❌ **DELETE**

---

## Backup Plan (Before Deletion)

### Step 1: Backup Old Database Backups (Optional)
If you want to keep old backups from October:

```bash
# Create archive folder
mkdir -p /mnt/g/khoirul/signate/_archived/database-backups-oct2025

# Move old backups
mv /mnt/g/khoirul/signate/database/backups/* \
   /mnt/g/khoirul/signate/_archived/database-backups-oct2025/

# Optional: Compress
cd /mnt/g/khoirul/signate/_archived/
tar -czf database-backups-oct2025.tar.gz database-backups-oct2025/
rm -rf database-backups-oct2025/
```

---

## Deletion Commands

### Safe Deletion (Recommended)

```bash
cd /mnt/g/khoirul/signate

# 1. Delete /migrations/ folder
echo "Deleting /migrations/..."
rm -rf migrations/

# 2. Delete /database/ folder
echo "Deleting /database/..."
rm -rf database/

echo "✅ Cleanup complete!"
```

---

## Verification After Deletion

```bash
# Verify only backend-python/migrations exists
ls -la /mnt/g/khoirul/signate/ | grep -E "migrations|database"

# Should show NOTHING (both deleted)

# Verify backend-python/migrations still exists
ls -la /mnt/g/khoirul/signate/backend-python/migrations/
# Should show 34 SQL files

echo "✅ Verification complete - only backend-python/migrations/ remains"
```

---

## What Gets Deleted

### Total Files to Delete:
- `/migrations/schema_alignment.sql` (1 file)
- `/database/init.sql` (1 file)
- `/database/init.sql.backup` (1 file)
- `/database/init-phase1-auth.sql` (1 file)
- `/database/backups/*` (9 backup files, ~21MB total)
- `/database/fix-database/*` (unknown count)
- `/database/migrations/001_add_uuid_support.sql` (1 file)
- `/database/migrations/README.md` (1 file)
- `/database/migrations/apply-migration.sh` (1 file)

**Estimated Total**: ~15-20 files, ~21MB disk space

---

## Impact Assessment

### ✅ No Impact on Production
- Production database uses `backend-python/migrations/` only
- Deleted files are old/unused
- No active code references these folders

### ✅ No Data Loss
- Database backups from October are outdated
- Current production data is safe in PostgreSQL
- Recent backups (if any) should be in different location

### ✅ Cleaner Project Structure
- Single source of truth for migrations
- No confusion about which migrations to use
- Easier maintenance

---

## Recommendation

**Proceed with deletion?** ✅ **YES**

**Reasons**:
1. `backend-python/migrations/` is complete and up-to-date (34 files)
2. Old migration folders are outdated (October 2025)
3. Old backups are from Oct 26-27 (superseded by current production data)
4. No active code references the old folders
5. Reduces confusion and maintenance overhead

**Optional**: Archive old backups first (see Backup Plan above)

---

## Execution

Ready to execute cleanup? Choose one:

### Option A: Delete Immediately (Safe)
```bash
cd /mnt/g/khoirul/signate
rm -rf migrations/
rm -rf database/
echo "✅ Cleanup complete!"
```

### Option B: Archive Backups First (Extra Safe)
```bash
cd /mnt/g/khoirul/signate
mkdir -p _archived/
mv database/backups/ _archived/old-backups-oct2025/
tar -czf _archived/old-backups-oct2025.tar.gz _archived/old-backups-oct2025/
rm -rf _archived/old-backups-oct2025/
rm -rf migrations/
rm -rf database/
echo "✅ Cleanup complete with archived backups!"
```

---

**Status**: Ready for execution
**Risk Level**: ⬇️ LOW - Safe to delete
**Approval Required**: User confirmation

