# Content Table Rename Plan: `content` → `contents`

## Executive Summary

Rencana untuk merubah nama tabel database dari singular `content` ke plural `contents` untuk konsistensi penamaan dengan tabel lain (devices, playlists, tags, dll).

**Status**: Draft - Belum Dieksekusi
**Impact Level**: HIGH - Perubahan database schema yang critical
**Estimated Time**: 2-3 jam termasuk testing
**Rollback Plan**: Ya, tersedia

---

## Table of Contents

1. [Files That Need Changes](#files-that-need-changes)
2. [Database Schema Changes](#database-schema-changes)
3. [Migration Strategy](#migration-strategy)
4. [Backend Code Changes](#backend-code-changes)
5. [Testing Checklist](#testing-checklist)
6. [Rollback Plan](#rollback-plan)
7. [Risk Assessment](#risk-assessment)

---

## Files That Need Changes

### 1. SQLAlchemy Model Definition (1 file)

**File**: `/mnt/g/khoirul/signate/backend/app/models/content.py`

```python
# Line 55 - BEFORE
__tablename__ = "content"

# Line 55 - AFTER
__tablename__ = "contents"
```

```python
# Line 98 - BEFORE
fallback_content_id = Column(Integer, ForeignKey("content.id", ondelete="SET NULL"), nullable=True)

# Line 98 - AFTER
fallback_content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)
```

---

### 2. Foreign Key References (3 files)

#### A. ContentAssignment Model

**File**: `/mnt/g/khoirul/signate/backend/app/models/assignment.py`

```python
# Line 43 - BEFORE
content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)

# Line 43 - AFTER
content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
```

**Note**: Line 65 `content = relationship("Content", ...)` - NO CHANGE (refers to class name, not table)

#### B. PlaylistContent Model

**File**: `/mnt/g/khoirul/signate/backend/app/models/playlist.py`

```python
# Line 114 - BEFORE
content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)

# Line 114 - AFTER
content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
```

**Note**: Line 125 `content = relationship("Content")` - NO CHANGE

#### C. Schedule Model

**File**: `/mnt/g/khoirul/signate/backend/app/models/schedule.py`

```python
# Line 45 - BEFORE
content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)

# Line 45 - AFTER
content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
```

---

### 3. SQL Migration Files (2 files)

#### A. Migration 001: Create Playlist Tables

**File**: `/mnt/g/khoirul/signate/backend/migrations/001_create_playlist_tables.sql`

```sql
-- Line 25 - BEFORE
content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,

-- Line 25 - AFTER
content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
```

```sql
-- Line 33 - BEFORE
CREATE INDEX IF NOT EXISTS idx_playlist_content_content_id ON playlist_content(content_id);

-- Line 33 - AFTER (NO CHANGE - index pada column, bukan table)
CREATE INDEX IF NOT EXISTS idx_playlist_content_content_id ON playlist_content(content_id);
```

#### B. Migration 003: Hotel Integration Foundation

**File**: `/mnt/g/khoirul/signate/backend/migrations/003_hotel_integration_foundation.sql`

```sql
-- Line 143 - BEFORE
ADD COLUMN IF NOT EXISTS fallback_content_id INTEGER REFERENCES content(id) ON DELETE SET NULL;

-- Line 143 - AFTER
ADD COLUMN IF NOT EXISTS fallback_content_id INTEGER REFERENCES contents(id) ON DELETE SET NULL;
```

```sql
-- Line 153 - BEFORE
COMMENT ON COLUMN content.fallback_content_id IS 'Fallback content if template fails';

-- Line 153 - AFTER
COMMENT ON COLUMN contents.fallback_content_id IS 'Fallback content if template fails';
```

---

### 4. Raw SQL Queries (1 file)

**File**: `/mnt/g/khoirul/signate/backend/app/api/settings.py`

```python
# Line 132-133 - BEFORE
result = db.execute(text(
    "SELECT COALESCE(SUM(file_size), 0)::BIGINT FROM content WHERE is_active = true"
))

# Line 132-133 - AFTER
result = db.execute(text(
    "SELECT COALESCE(SUM(file_size), 0)::BIGINT FROM contents WHERE is_active = true"
))
```

---

### 5. Files That DO NOT Need Changes

**SQLAlchemy ORM Queries** - These all reference the model class `Content`, not the table name:
- `/mnt/g/khoirul/signate/backend/app/api/content.py` (all `db.query(Content)` statements)
- `/mnt/g/khoirul/signate/backend/app/api/playlists.py` (all `db.query(Content)` statements)
- `/mnt/g/khoirul/signate/backend/app/api/client.py` (JOIN with `Content` model)
- `/mnt/g/khoirul/signate/backend/app/services/preview_service.py` (JOIN with `Content` model)
- `/mnt/g/khoirul/signate/backend/scripts/backfill_metadata.py` (all queries)

**Frontend Files** - API contracts tidak berubah:
- All files in `/mnt/g/khoirul/signate/web-admin/src/` - NO CHANGES NEEDED

**Schemas** - Field names tidak berubah:
- `/mnt/g/khoirul/signate/backend/app/schemas/content.py` - NO CHANGES
- `/mnt/g/khoirul/signate/backend/app/schemas/playlist.py` - NO CHANGES

---

## Database Schema Changes

### Current Schema

```sql
-- Main table
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    -- ... columns ...
    fallback_content_id INTEGER REFERENCES content(id) ON DELETE SET NULL
);

-- Related tables with foreign keys
CREATE TABLE content_assignments (
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE
);

CREATE TABLE playlist_content (
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE
);

CREATE TABLE schedules (
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE
);
```

### Target Schema

```sql
-- Main table
CREATE TABLE contents (
    id SERIAL PRIMARY KEY,
    -- ... columns ...
    fallback_content_id INTEGER REFERENCES contents(id) ON DELETE SET NULL
);

-- Related tables with foreign keys
CREATE TABLE content_assignments (
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE
);

CREATE TABLE playlist_content (
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE
);

CREATE TABLE schedules (
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE
);
```

---

## Migration Strategy

### New Migration File: `004_rename_content_to_contents.sql`

```sql
-- ============================================================================
-- Migration 004: Rename content table to contents for naming consistency
-- ============================================================================

BEGIN;

-- Step 1: Drop dependent foreign key constraints
ALTER TABLE content_assignments DROP CONSTRAINT IF EXISTS content_assignments_content_id_fkey;
ALTER TABLE playlist_content DROP CONSTRAINT IF EXISTS playlist_content_content_id_fkey;
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS schedules_content_id_fkey;
ALTER TABLE content DROP CONSTRAINT IF EXISTS content_fallback_content_id_fkey;

-- Step 2: Rename the table
ALTER TABLE content RENAME TO contents;

-- Step 3: Recreate foreign key constraints with new table name
ALTER TABLE content_assignments
    ADD CONSTRAINT content_assignments_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE;

ALTER TABLE playlist_content
    ADD CONSTRAINT playlist_content_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE;

ALTER TABLE schedules
    ADD CONSTRAINT schedules_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE;

ALTER TABLE contents
    ADD CONSTRAINT content_fallback_content_id_fkey
    FOREIGN KEY (fallback_content_id) REFERENCES contents(id) ON DELETE SET NULL;

-- Step 4: Update any sequences (if needed)
-- ALTER SEQUENCE content_id_seq RENAME TO contents_id_seq;

-- Step 5: Update column comment
COMMENT ON COLUMN contents.fallback_content_id IS 'Fallback content if template fails';

COMMIT;

-- Verification
SELECT
    'contents' as renamed_table,
    COUNT(*) as record_count
FROM contents;

SELECT
    conname as constraint_name,
    conrelid::regclass as table_name,
    confrelid::regclass as referenced_table
FROM pg_constraint
WHERE confrelid = 'contents'::regclass
   OR conrelid = 'contents'::regclass;
```

### Rollback Migration: `004_rollback_rename_contents_to_content.sql`

```sql
-- ============================================================================
-- Rollback Migration 004: Rename contents back to content
-- ============================================================================

BEGIN;

-- Step 1: Drop dependent foreign key constraints
ALTER TABLE content_assignments DROP CONSTRAINT IF EXISTS content_assignments_content_id_fkey;
ALTER TABLE playlist_content DROP CONSTRAINT IF EXISTS playlist_content_content_id_fkey;
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS schedules_content_id_fkey;
ALTER TABLE contents DROP CONSTRAINT IF EXISTS content_fallback_content_id_fkey;

-- Step 2: Rename the table back
ALTER TABLE contents RENAME TO content;

-- Step 3: Recreate foreign key constraints with original table name
ALTER TABLE content_assignments
    ADD CONSTRAINT content_assignments_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE;

ALTER TABLE playlist_content
    ADD CONSTRAINT playlist_content_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE;

ALTER TABLE schedules
    ADD CONSTRAINT schedules_content_id_fkey
    FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE;

ALTER TABLE content
    ADD CONSTRAINT content_fallback_content_id_fkey
    FOREIGN KEY (fallback_content_id) REFERENCES content(id) ON DELETE SET NULL;

-- Step 4: Update column comment
COMMENT ON COLUMN content.fallback_content_id IS 'Fallback content if template fails';

COMMIT;
```

---

## Backend Code Changes

### Order of Changes (CRITICAL - Must follow this order!)

1. **Create migration file first** (`004_rename_content_to_contents.sql`)
2. **Run migration on development database**
3. **Test migration thoroughly**
4. **Update backend code files** (in this order):
   - Step 1: Models (`app/models/content.py`)
   - Step 2: Foreign keys (`assignment.py`, `playlist.py`, `schedule.py`)
   - Step 3: Raw SQL queries (`settings.py`)
   - Step 4: Update old migration files (for fresh installs)
5. **Restart backend**
6. **Test all endpoints**
7. **Deploy to production**

### Code Changes Summary

| File | Lines to Change | Type |
|------|----------------|------|
| `models/content.py` | 55, 98 | Table name, self-FK |
| `models/assignment.py` | 43 | Foreign key |
| `models/playlist.py` | 114 | Foreign key |
| `models/schedule.py` | 45 | Foreign key |
| `api/settings.py` | 132-133 | Raw SQL query |
| `migrations/001_*.sql` | 25 | Foreign key |
| `migrations/003_*.sql` | 143, 153 | Foreign key, comment |

**Total**: 7 files, 9 locations

---

## Testing Checklist

### Pre-Migration Tests

- [ ] Backup production database
- [ ] Test migration on local development database
- [ ] Verify all foreign keys work correctly
- [ ] Verify all indexes still exist
- [ ] Check constraint names are correct
- [ ] Run all existing tests
- [ ] Test content upload
- [ ] Test content assignment
- [ ] Test playlist creation with content
- [ ] Test schedule creation

### Post-Migration Tests

- [ ] Verify table rename successful: `\dt contents`
- [ ] Verify all foreign keys recreated: `\d content_assignments`
- [ ] Verify self-referential FK works: `\d contents`
- [ ] Test all Content API endpoints:
  - [ ] GET `/api/content` - List all content
  - [ ] POST `/api/content/upload` - Upload new content
  - [ ] GET `/api/content/{id}` - Get content details
  - [ ] PUT `/api/content/{id}` - Update content
  - [ ] DELETE `/api/content/{id}` - Delete content
- [ ] Test Playlist API endpoints:
  - [ ] POST `/api/playlists` - Create playlist with content
  - [ ] PUT `/api/playlists/{id}/content` - Add content to playlist
- [ ] Test Content Assignment:
  - [ ] POST `/api/content/{id}/assign` - Assign content to device
- [ ] Test Settings API:
  - [ ] GET `/api/settings/system/info` - Media storage should work
- [ ] Test Frontend:
  - [ ] Content page loads
  - [ ] Content upload works
  - [ ] Playlist management works
  - [ ] Device content assignment works
  - [ ] Settings page shows correct media storage

### Performance Tests

- [ ] Query performance unchanged
- [ ] Index performance unchanged
- [ ] Foreign key cascade delete works correctly

---

## Rollback Plan

### If Migration Fails During Execution

```bash
# Step 1: Check if transaction was committed
psql -U signage_user -d signage_db -c "SELECT tablename FROM pg_tables WHERE tablename IN ('content', 'contents');"

# Step 2: If contents exists but foreign keys broken, run rollback migration
psql -U signage_user -d signage_db -f migrations/004_rollback_rename_contents_to_content.sql

# Step 3: Verify rollback successful
psql -U signage_user -d signage_db -c "\dt content"
```

### If Backend Code Deployed But Broken

```bash
# Step 1: Revert backend code to previous commit
git revert HEAD

# Step 2: Rebuild backend container
docker-compose build backend-api

# Step 3: Restart backend
docker-compose restart backend-api

# Step 4: If database already migrated, run rollback migration
psql -U signage_user -d signage_db -f migrations/004_rollback_rename_contents_to_content.sql
```

### Recovery Steps

1. **Immediate**: Stop all write operations to database
2. **Backup**: Create emergency backup: `pg_dump signage_db > emergency_backup.sql`
3. **Rollback**: Execute rollback migration
4. **Verify**: Run all tests from testing checklist
5. **Restore**: If rollback fails, restore from backup
6. **Communicate**: Notify team about rollback

---

## Risk Assessment

### High Risk Areas

1. **Foreign Key Constraints** - Most complex part
   - Risk: Constraints not recreated correctly
   - Mitigation: Transaction-based migration with verification
   - Test: Verify all FK constraints after migration

2. **Self-Referential Foreign Key** - `fallback_content_id`
   - Risk: Circular dependency issue during rename
   - Mitigation: Drop all FKs before rename, recreate after
   - Test: Test content with fallback_content_id set

3. **Production Data Integrity**
   - Risk: Data loss or corruption
   - Mitigation: Full backup before migration, transaction-based migration
   - Test: Row count verification before/after

### Medium Risk Areas

1. **Existing Migration Files** - Old references
   - Risk: Fresh installs will fail if old migrations not updated
   - Mitigation: Update old migration files
   - Test: Test fresh database creation

2. **Backend Restart Timing**
   - Risk: Downtime during deployment
   - Mitigation: Blue-green deployment or maintenance window
   - Test: Estimated 2-3 minutes downtime

### Low Risk Areas

1. **Frontend Code** - No changes needed
2. **API Contracts** - Unchanged
3. **ORM Queries** - Automatically handled by SQLAlchemy

---

## Implementation Timeline

### Phase 1: Preparation (30 minutes)
- [ ] Create migration files (forward & rollback)
- [ ] Test migration on local development database
- [ ] Review all code changes
- [ ] Prepare rollback documentation

### Phase 2: Code Changes (45 minutes)
- [ ] Update all 7 files with code changes
- [ ] Run linters and type checkers
- [ ] Commit changes to feature branch
- [ ] Create pull request for review

### Phase 3: Testing (60 minutes)
- [ ] Run all automated tests
- [ ] Manual testing of all affected endpoints
- [ ] Performance testing
- [ ] Load testing (if applicable)

### Phase 4: Deployment (30 minutes)
- [ ] Schedule maintenance window
- [ ] Backup production database
- [ ] Deploy migration to production
- [ ] Deploy backend code changes
- [ ] Verify all systems operational
- [ ] Monitor for 30 minutes

**Total Estimated Time**: 2.5 - 3 hours

---

## Decision: Proceed or Not?

### Arguments FOR Proceeding

1. **Consistency** - Matches naming convention of other tables (devices, playlists, tags)
2. **Best Practice** - Django/Rails convention is plural table names
3. **Clarity** - More intuitive for new developers
4. **ORM Compatibility** - SQLAlchemy works better with plural table names

### Arguments AGAINST Proceeding

1. **Risk** - Database schema changes are always risky
2. **Effort** - 2-3 hours of work + testing time
3. **Stability** - System currently works fine with singular name
4. **Business Value** - No direct business value from this change

### Recommendation

**WAIT** - Recommend postponing this refactoring until:
1. You have a dedicated maintenance window
2. You have comprehensive test coverage
3. You have a staging environment to test thoroughly
4. There's a compelling business reason (e.g., major refactoring already planned)

**Alternative**: Keep singular name `content` but document the inconsistency for future reference.

---

## Approval Required

- [ ] Technical Lead Review
- [ ] Database Administrator Review
- [ ] DevOps Engineer Review
- [ ] Business Stakeholder Approval (for maintenance window)

---

## Post-Implementation

### Documentation Updates

- [ ] Update database schema documentation
- [ ] Update API documentation (if any table names exposed)
- [ ] Update developer onboarding guide
- [ ] Update this file status to "COMPLETED"

### Monitoring

- [ ] Monitor error logs for 48 hours
- [ ] Monitor database performance metrics
- [ ] Monitor API response times
- [ ] Check for any foreign key constraint violations

---

**Document Version**: 1.0
**Created**: 2025-10-26
**Last Updated**: 2025-10-26
**Status**: Draft - Awaiting Review
**Next Review**: Before implementation decision
