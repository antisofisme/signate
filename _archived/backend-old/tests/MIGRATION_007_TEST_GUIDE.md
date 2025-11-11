# Migration 007 Testing Guide
## Content Table Rename: `content` → `contents`

**Migration File**: `backend/migrations/007_rename_content_to_contents.sql`
**Impact Level**: HIGH - Critical database schema change
**Estimated Testing Time**: 30-45 minutes
**Database**: PostgreSQL (port 5433)

---

## Table of Contents

1. [Testing Strategy Overview](#testing-strategy-overview)
2. [Pre-Migration Testing](#pre-migration-testing)
3. [Migration Execution](#migration-execution)
4. [Post-Migration Verification](#post-migration-verification)
5. [API Endpoint Testing](#api-endpoint-testing)
6. [Frontend Testing](#frontend-testing)
7. [Rollback Procedure](#rollback-procedure)
8. [Test Results Checklist](#test-results-checklist)

---

## Testing Strategy Overview

### Test Phases

```
Phase 1: Pre-Migration Tests     → Capture baseline state
Phase 2: Database Backup         → Safety checkpoint
Phase 3: Migration Execution     → Apply schema changes
Phase 4: Post-Migration Tests    → Verify data integrity
Phase 5: API Testing             → Validate application layer
Phase 6: Frontend Testing        → End-to-end validation
Phase 7: Rollback Test (Optional)→ Disaster recovery validation
```

### Success Criteria

- All 14 post-migration SQL tests pass
- Record counts match pre-migration baseline
- All 4 foreign keys recreated correctly
- All API endpoints return 200/201 responses
- Frontend content management works without errors
- No orphaned records in dependent tables

---

## Pre-Migration Testing

### Step 1: Connect to Database

```bash
# From server (192.168.5.12)
psql -h localhost -p 5433 -U signage_user -d signage_db

# Or from local machine
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db
```

**Password**: Check `.env` file for `POSTGRES_PASSWORD`

### Step 2: Run Pre-Migration Test Script

```bash
# Execute pre-migration tests
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f /home/gzjbbk/signage/backend/tests/test_migration_007_pre.sql \
  > /tmp/migration_007_pre_results.txt 2>&1

# View results
cat /tmp/migration_007_pre_results.txt
```

### Step 3: Review Pre-Migration Output

**Critical Values to Record**:

```
✓ Table "content" exists: YES
✓ Table "contents" exists: NO (expected)
✓ Total records: _______ (record this number)
✓ Active records: _______
✓ Foreign keys: 4 (expected)
✓ Indexes: _______ (record this number)
✓ Total file size: _______ bytes
```

**Save this file** - you'll compare it with post-migration results.

---

## Migration Execution

### Step 1: Create Database Backup

```bash
# Connect to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Create backup directory
mkdir -p ~/backups

# Full database backup
docker exec signage-postgres pg_dump \
  -U signage_user signage_db \
  > ~/backups/signage_db_pre_migration_007_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh ~/backups/signage_db_pre_migration_007_*.sql
```

**CRITICAL**: Do not proceed without a valid backup!

### Step 2: Stop Backend API (Optional but Recommended)

```bash
# Stop backend to prevent concurrent operations
docker-compose stop backend-api

# Verify stopped
docker-compose ps backend-api
```

### Step 3: Execute Migration

```bash
# Run migration 007
psql -h localhost -p 5433 -U signage_user -d signage_db \
  -f /home/gzjbbk/signage/backend/migrations/007_rename_content_to_contents.sql

# Check for errors
echo $?  # Should return 0 for success
```

**Expected Output**:
```
BEGIN
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
COMMENT
COMMIT
 renamed_table | record_count
---------------+--------------
 contents      | [your count]
```

### Step 4: Verify Migration Completed

```bash
# Quick verification
psql -h localhost -p 5433 -U signage_user -d signage_db -c "\dt contents"

# Should show:
#  Schema | Name     | Type  | Owner
# --------+----------+-------+-------------
#  public | contents | table | signage_user
```

---

## Post-Migration Verification

### Step 1: Run Post-Migration Test Script

```bash
# Execute post-migration tests
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f /home/gzjbbk/signage/backend/tests/test_migration_007_post.sql \
  > /tmp/migration_007_post_results.txt 2>&1

# View results
cat /tmp/migration_007_post_results.txt
```

### Step 2: Compare Pre and Post Results

**Side-by-Side Comparison**:

```bash
# Extract key metrics
echo "=== PRE-MIGRATION ==="
grep "total_records\|active_records\|fk_count" /tmp/migration_007_pre_results.txt

echo "=== POST-MIGRATION ==="
grep "total_contents\|active_contents" /tmp/migration_007_post_results.txt
```

**All numbers must match exactly!**

### Step 3: Review Test Summary

Look for the **POST-MIGRATION SUMMARY REPORT** section:

```
Check Item               | Status
-------------------------|----------
Table Renamed            | PASS
Old Table Removed        | PASS
Foreign Keys Count       | PASS (4/4)
Indexes Preserved        | PASS
Self-Referential FK      | PASS
No Orphaned Records      | PASS
```

**All items must show PASS** before proceeding.

---

## API Endpoint Testing

### Step 1: Restart Backend API

```bash
# On server
docker-compose up -d backend-api

# Wait for startup (check logs)
docker-compose logs -f backend-api

# Press Ctrl+C when you see: "Application startup complete"
```

### Step 2: Test Content API Endpoints

#### A. List All Content

```bash
curl -X GET http://192.168.5.12:8001/api/content \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected: 200 OK with content array
```

#### B. Get Content Details

```bash
# Replace {id} with actual content ID from previous response
curl -X GET http://192.168.5.12:8001/api/content/{id} \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected: 200 OK with content details
```

#### C. Upload New Content (Functional Test)

```bash
# Create test image
echo "Test content" > /tmp/test_content.txt

# Upload content
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -F "file=@/tmp/test_content.txt" \
  -F "content_type=text" \
  | jq '.'

# Expected: 201 Created with new content ID
# Record the ID: _______
```

#### D. Update Content

```bash
# Replace {id} with ID from upload test
curl -X PUT http://192.168.5.12:8001/api/content/{id} \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}' \
  | jq '.'

# Expected: 200 OK with updated content
```

#### E. Delete Content

```bash
# Replace {id} with test content ID
curl -X DELETE http://192.168.5.12:8001/api/content/{id} \
  -H "Content-Type: application/json"

# Expected: 200 OK or 204 No Content
```

### Step 3: Test Playlist API

```bash
# Create playlist with content
curl -X POST http://192.168.5.12:8001/api/playlists \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Playlist Migration 007",
    "content_ids": [1, 2]
  }' \
  | jq '.'

# Expected: 201 Created with playlist details
```

### Step 4: Test Settings API

```bash
# Get system info (includes media storage from contents table)
curl -X GET http://192.168.5.12:8001/api/settings/system/info \
  -H "Content-Type: application/json" \
  | jq '.media_storage'

# Expected: 200 OK with storage statistics
```

---

## Frontend Testing

### Step 1: Start Web Admin (if not running)

```bash
# From local machine in /mnt/g/khoirul/signate/web-admin
npm run dev

# Open browser: http://localhost:3000
```

### Step 2: Content Page Tests

**Test Cases**:

1. **Navigate to Content page**
   - URL: http://localhost:3000/content
   - Expected: Page loads without errors

2. **View content list**
   - Expected: All content items displayed
   - Check: File names, types, sizes visible

3. **Upload new content**
   - Click "Upload Content" button
   - Select a test file (image or video)
   - Expected: Upload progress → Success message → Content appears in list

4. **View content details**
   - Click on a content item
   - Expected: Modal opens with full details

5. **Edit content metadata**
   - Click edit button on a content item
   - Change name or description
   - Expected: Save successful → Changes reflected in UI

6. **Delete content**
   - Click delete button on test content
   - Confirm deletion
   - Expected: Content removed from list

### Step 3: Playlist Management Tests

**Test Cases**:

1. **Navigate to Playlists page**
   - URL: http://localhost:3000/playlists
   - Expected: Page loads without errors

2. **Create playlist with content**
   - Click "Create Playlist"
   - Add content items
   - Expected: Playlist created successfully

3. **Add content to existing playlist**
   - Edit an existing playlist
   - Add/remove content items
   - Expected: Changes saved correctly

### Step 4: Device Content Assignment Tests

**Test Cases**:

1. **Navigate to Devices page**
   - URL: http://localhost:3000/devices
   - Expected: Page loads without errors

2. **Assign content to device**
   - Click on a device
   - Click "Assign Content"
   - Select content or playlist
   - Expected: Assignment successful

3. **Verify assignment persists**
   - Refresh page
   - Check device details
   - Expected: Assigned content still shown

### Step 5: Settings Page Tests

**Test Cases**:

1. **Navigate to Settings page**
   - URL: http://localhost:3000/settings
   - Expected: Page loads without errors

2. **View system information**
   - Check "System" tab
   - Look for "Media Storage" section
   - Expected: Storage stats displayed correctly

---

## Rollback Procedure

### When to Rollback

Rollback if:
- Any post-migration test FAILS
- API endpoints return 500 errors
- Frontend shows errors loading content
- Data integrity checks fail

### Rollback Steps

#### Option A: Restore from Backup (Recommended)

```bash
# Connect to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Stop backend
docker-compose stop backend-api

# Restore database
docker exec -i signage-postgres psql \
  -U signage_user signage_db \
  < ~/backups/signage_db_pre_migration_007_[timestamp].sql

# Verify restoration
docker exec signage-postgres psql \
  -U signage_user signage_db \
  -c "\dt content"

# Should show "content" table exists

# Restart backend
docker-compose up -d backend-api
```

#### Option B: Run Rollback Migration

```bash
# Execute rollback migration
psql -h localhost -p 5433 -U signage_user -d signage_db \
  -f /home/gzjbbk/signage/backend/migrations/007_rollback_rename_contents_to_content.sql

# Verify rollback
psql -h localhost -p 5433 -U signage_user -d signage_db -c "\dt content"

# Restart backend
docker-compose up -d backend-api
```

### Post-Rollback Verification

```bash
# Run pre-migration tests again to verify state
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f /home/gzjbbk/signage/backend/tests/test_migration_007_pre.sql

# Verify backend API works
curl http://192.168.5.12:8001/api/content | jq '.'
```

---

## Test Results Checklist

### Pre-Migration Tests

- [ ] Table "content" exists
- [ ] Table "contents" does NOT exist
- [ ] Record count recorded: _______
- [ ] Foreign keys count: 4
- [ ] Indexes count recorded: _______
- [ ] Backup created successfully
- [ ] Backup file size > 0 bytes

### Database Migration

- [ ] Migration script executed without errors
- [ ] Table "contents" now exists
- [ ] Table "content" no longer exists
- [ ] Verification query shows record count

### Post-Migration SQL Tests (14 Tests)

- [ ] TEST 1: Table renamed to "contents" - PASS
- [ ] TEST 2: Record count matches baseline - PASS
- [ ] TEST 3: All 4 foreign keys exist - PASS (4/4)
- [ ] TEST 4: Individual FK verification - PASS (all 4)
- [ ] TEST 5: CASCADE DELETE behavior correct - PASS
- [ ] TEST 6: Indexes preserved - PASS
- [ ] TEST 7: Self-referential FK works - PASS
- [ ] TEST 8: CASCADE relationships intact - PASS
- [ ] TEST 9: Table schema intact - PASS
- [ ] TEST 10: Column definitions unchanged - PASS
- [ ] TEST 11: Sample data matches pre-migration - PASS
- [ ] TEST 12: Related tables JOIN correctly - PASS
- [ ] TEST 13: No orphaned records - PASS
- [ ] TEST 14: Constraint names correct - PASS

### API Endpoint Tests

- [ ] GET /api/content - 200 OK
- [ ] GET /api/content/{id} - 200 OK
- [ ] POST /api/content/upload - 201 Created
- [ ] PUT /api/content/{id} - 200 OK
- [ ] DELETE /api/content/{id} - 200/204 OK
- [ ] POST /api/playlists (with content) - 201 Created
- [ ] GET /api/settings/system/info - 200 OK

### Frontend Tests

- [ ] Content page loads without errors
- [ ] Content list displays correctly
- [ ] Content upload works
- [ ] Content details modal opens
- [ ] Content edit saves successfully
- [ ] Content delete works
- [ ] Playlist creation with content works
- [ ] Device content assignment works
- [ ] Settings page shows media storage

### Final Validation

- [ ] No console errors in browser
- [ ] No 500 errors in backend logs
- [ ] Application fully functional
- [ ] Performance unchanged
- [ ] All team members notified of schema change

---

## Quick Reference Commands

### Database Connection

```bash
# Local to server
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db

# On server
docker exec -it signage-postgres psql -U signage_user signage_db
```

### Quick Table Check

```bash
# Check if migration completed
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -c "SELECT tablename FROM pg_tables WHERE tablename IN ('content', 'contents');"
```

### Quick Record Count

```bash
# Before migration
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -c "SELECT COUNT(*) FROM content;"

# After migration
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -c "SELECT COUNT(*) FROM contents;"
```

### Quick FK Check

```bash
# Check foreign keys
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -c "SELECT conname FROM pg_constraint WHERE confrelid = 'contents'::regclass;"
```

### Backend API Health Check

```bash
curl http://192.168.5.12:8001/api/content | jq 'length'
```

---

## Troubleshooting

### Issue: Migration hangs or times out

**Cause**: Active connections or locks on content table

**Solution**:
```sql
-- Check for active locks
SELECT * FROM pg_locks WHERE relation = 'content'::regclass;

-- Terminate blocking connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'signage_db'
  AND pid <> pg_backend_pid();
```

### Issue: Foreign key constraint errors

**Cause**: Orphaned records or constraint violations

**Solution**:
```sql
-- Check for orphaned records
SELECT * FROM content_assignments
WHERE content_id NOT IN (SELECT id FROM content);

-- Clean up orphans before migration
DELETE FROM content_assignments
WHERE content_id NOT IN (SELECT id FROM content);
```

### Issue: API returns 500 errors after migration

**Cause**: Backend using old table name or cache issues

**Solution**:
```bash
# Rebuild backend container
docker-compose down backend-api
docker-compose up -d --build backend-api

# Check logs
docker-compose logs -f backend-api
```

### Issue: Frontend shows "Network Error"

**Cause**: Backend not running or CORS issues

**Solution**:
```bash
# Check backend status
docker-compose ps backend-api

# Check backend logs for errors
docker-compose logs backend-api | grep -i error

# Verify API responds
curl http://192.168.5.12:8001/docs
```

---

## Success Confirmation

When all tests pass, you should see:

1. **Database Level**:
   - Table "contents" exists with all data
   - All 4 foreign keys recreated
   - No orphaned records

2. **API Level**:
   - All endpoints return 2xx responses
   - No 500 errors in logs

3. **Frontend Level**:
   - All pages load without errors
   - Content CRUD operations work
   - No console errors

4. **Business Level**:
   - Users can upload content
   - Playlists can be created with content
   - Devices can be assigned content
   - System shows correct storage stats

---

## Post-Testing Actions

After successful testing:

1. **Notify Team**: Inform all developers of schema change
2. **Update Documentation**: Mark migration as completed
3. **Monitor Production**: Watch logs for any issues in first 24 hours
4. **Keep Backup**: Retain pre-migration backup for 7 days
5. **Update Local Environments**: Ensure all devs run migration

---

## Contact & Support

**Migration Owner**: [Your Name]
**Testing Date**: [Date]
**Migration Version**: 007
**Documentation**: `/mnt/g/khoirul/signage/docs/archive/documentation-review-20251027/CONTENT_TABLE_RENAME_PLAN.md`

---

**Remember**:
- Test on development database first
- Always create backup before migration
- When in doubt, rollback and investigate
- Document any deviations from this guide
