# Migration 007 Testing Infrastructure

Comprehensive testing suite for the content table rename migration (`content` → `contents`).

---

## Quick Start

### Prerequisites

```bash
# Set database password
export DB_PASSWORD="your_password_here"

# Optional: Override defaults
export DB_HOST="192.168.5.12"
export DB_PORT="5433"
export DB_USER="signage_user"
export DB_NAME="signage_db"
export API_URL="http://192.168.5.12:8001"
```

### Run Tests

```bash
# Navigate to tests directory
cd /mnt/g/khoirul/signate/backend/tests

# Run pre-migration tests
./run_migration_007_tests.sh --pre

# Run full automated test suite
./run_migration_007_tests.sh --full

# Run post-migration verification
./run_migration_007_tests.sh --post

# Run API endpoint tests
./run_migration_007_tests.sh --api
```

---

## Files Overview

### 1. `test_migration_007_pre.sql` (8.9 KB)
**Purpose**: Capture baseline state before migration

**What it tests**:
- Table name is 'content' (not 'contents')
- Record counts (total, active, inactive, soft-deleted)
- All 4 foreign key constraints exist
- Self-referential FK (fallback_content_id)
- Indexes on content table
- Sample data integrity
- Related table relationships

**Run manually**:
```bash
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f test_migration_007_pre.sql > results/pre_migration_$(date +%Y%m%d_%H%M%S).txt
```

**Key outputs to record**:
- Total records: _______
- Foreign keys: 4 (expected)
- Indexes: _______
- Total file size: _______ bytes

---

### 2. `test_migration_007_post.sql` (17 KB)
**Purpose**: Verify migration success and data integrity

**What it tests** (14 comprehensive tests):
1. Table renamed to 'contents'
2. Record count matches pre-migration baseline
3. All 4 foreign keys recreated correctly
4. Individual FK verification (content_assignments, playlist_content, schedules, self-ref)
5. CASCADE DELETE behavior verification
6. Indexes still exist
7. Self-referential FK data integrity
8. CASCADE relationship simulation
9. Table schema intact
10. Column definitions unchanged
11. Sample data integrity
12. Related tables JOIN correctly
13. No orphaned records
14. Constraint names correct

**Run manually**:
```bash
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f test_migration_007_post.sql > results/post_migration_$(date +%Y%m%d_%H%M%S).txt
```

**Success criteria**: All tests show "PASS"

---

### 3. `MIGRATION_007_TEST_GUIDE.md` (17 KB)
**Purpose**: Comprehensive step-by-step testing manual

**Contents**:
- Testing strategy overview
- Pre-migration testing procedures
- Migration execution steps
- Post-migration verification
- API endpoint testing (7 endpoints)
- Frontend testing (9 test cases)
- Rollback procedures (2 methods)
- Troubleshooting guide
- Test results checklist (40+ checkboxes)
- Quick reference commands

**When to use**: First-time migration or training new team members

---

### 4. `run_migration_007_tests.sh` (22 KB)
**Purpose**: Automated test execution with color-coded output

**Features**:
- Color-coded PASS/FAIL/WARNING output
- Automated pre/post test comparison
- Database backup creation
- API endpoint testing
- Full test suite automation
- Test result reporting
- Rollback execution
- Error handling and validation

**Usage**:
```bash
# Show help
./run_migration_007_tests.sh --help

# Pre-migration tests only
DB_PASSWORD=secret ./run_migration_007_tests.sh --pre

# Create backup
DB_PASSWORD=secret ./run_migration_007_tests.sh --backup

# Execute migration
DB_PASSWORD=secret ./run_migration_007_tests.sh --migrate

# Post-migration verification
DB_PASSWORD=secret ./run_migration_007_tests.sh --post

# Compare results
./run_migration_007_tests.sh --compare

# Test API endpoints
./run_migration_007_tests.sh --api

# Full automated suite (recommended)
DB_PASSWORD=secret ./run_migration_007_tests.sh --full

# Rollback (if needed)
DB_PASSWORD=secret ./run_migration_007_tests.sh --rollback

# Generate report
./run_migration_007_tests.sh --report
```

---

## Testing Workflow

### Option A: Manual Testing (Recommended for first time)

Follow the comprehensive guide in `MIGRATION_007_TEST_GUIDE.md`

```bash
# Step 1: Read the guide
cat MIGRATION_007_TEST_GUIDE.md

# Step 2: Run pre-migration tests
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f test_migration_007_pre.sql > results/pre_migration.txt

# Step 3: Review output and record baseline metrics
less results/pre_migration.txt

# Step 4: Create backup
docker exec signage-postgres pg_dump -U signage_user signage_db \
  > ../backups/signage_db_pre_migration_007_$(date +%Y%m%d_%H%M%S).sql

# Step 5: Execute migration
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f ../migrations/007_rename_content_to_contents.sql

# Step 6: Run post-migration tests
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db \
  -f test_migration_007_post.sql > results/post_migration.txt

# Step 7: Compare results
diff -y results/pre_migration.txt results/post_migration.txt | less
```

### Option B: Automated Testing (Faster, recommended after first successful run)

```bash
# Set password
export DB_PASSWORD="your_password"

# Run full suite
./run_migration_007_tests.sh --full
```

The automated script will:
1. Test database connection
2. Run pre-migration tests
3. Save baseline metrics
4. Create database backup
5. Prompt for confirmation
6. Execute migration
7. Run post-migration tests
8. Compare results
9. Test API endpoints
10. Generate summary report

---

## Test Results Location

All test outputs are saved to `results/` directory:

```
results/
├── pre_migration_YYYYMMDD_HHMMSS.txt
├── post_migration_YYYYMMDD_HHMMSS.txt
├── baseline_metrics_YYYYMMDD_HHMMSS.txt
├── migration_execution_YYYYMMDD_HHMMSS.txt
├── rollback_execution_YYYYMMDD_HHMMSS.txt
└── migration_007_report_YYYYMMDD_HHMMSS.md
```

---

## Success Criteria Checklist

### Database Level
- [ ] Table 'contents' exists
- [ ] Table 'content' no longer exists
- [ ] Record count matches baseline (0 lost records)
- [ ] All 4 foreign keys recreated
- [ ] All indexes preserved
- [ ] No orphaned records

### Application Level
- [ ] All API endpoints return 2xx responses
- [ ] No 500 errors in backend logs
- [ ] Frontend content page loads
- [ ] Content upload works
- [ ] Playlist creation works
- [ ] Device assignment works

### Data Integrity
- [ ] Sample data matches pre-migration
- [ ] JOINs work correctly
- [ ] CASCADE DELETE behavior correct
- [ ] Self-referential FK works

---

## Troubleshooting

### Issue: Permission denied when running script

```bash
chmod +x run_migration_007_tests.sh
```

### Issue: Database connection failed

```bash
# Check database is running
docker-compose ps signage-postgres

# Test connection manually
psql -h 192.168.5.12 -p 5433 -U signage_user -d signage_db -c "SELECT 1;"
```

### Issue: Migration hangs

```sql
-- Check for locks
SELECT * FROM pg_locks WHERE relation = 'content'::regclass;

-- Terminate blocking sessions
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE datname = 'signage_db' AND pid <> pg_backend_pid();
```

### Issue: Tests show FAIL

1. Review the specific test failure
2. Check test results in `results/` directory
3. Verify data integrity manually
4. Consider rollback if critical

---

## Rollback Procedures

### Method 1: Restore from backup (Recommended)

```bash
# Stop backend
docker-compose stop backend-api

# Restore database
docker exec -i signage-postgres psql -U signage_user signage_db \
  < ../backups/signage_db_pre_migration_007_[timestamp].sql

# Restart backend
docker-compose up -d backend-api
```

### Method 2: Run rollback migration

```bash
DB_PASSWORD=secret ./run_migration_007_tests.sh --rollback
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | 192.168.5.12 | Database host |
| `DB_PORT` | 5433 | Database port |
| `DB_USER` | signage_user | Database user |
| `DB_NAME` | signage_db | Database name |
| `DB_PASSWORD` | (required) | Database password |
| `API_URL` | http://192.168.5.12:8001 | Backend API URL |

---

## Test Coverage

### SQL Tests: 14 comprehensive tests
- Pre-migration: 10 baseline checks
- Post-migration: 14 verification checks
- Comparison: 4 integrity checks

### API Tests: 7 endpoints
- GET /api/content
- GET /api/content/{id}
- POST /api/content/upload
- PUT /api/content/{id}
- DELETE /api/content/{id}
- GET /api/playlists
- GET /api/settings/system/info

### Frontend Tests: 9 test cases
- Content page load
- Content list display
- Content upload
- Content details
- Content edit
- Content delete
- Playlist creation
- Device assignment
- Settings page

---

## Best Practices

1. **Always run pre-migration tests first**
   - Establishes baseline for comparison
   - Identifies issues before migration

2. **Create backup before migration**
   - Essential safety net
   - Fast rollback option

3. **Review test output carefully**
   - Don't proceed if any FAIL appears
   - Investigate WARNINGs

4. **Test on development environment first**
   - Validate process before production
   - Identify edge cases

5. **Document deviations**
   - Record any unexpected behavior
   - Note manual interventions

6. **Keep backups for 7 days**
   - Allow time to discover issues
   - Safety margin for rollback

---

## Support

**Documentation**: `MIGRATION_007_TEST_GUIDE.md`
**Migration Plan**: `/mnt/g/khoirul/signate/docs/archive/documentation-review-20251027/CONTENT_TABLE_RENAME_PLAN.md`
**Migration File**: `/mnt/g/khoirul/signate/backend/migrations/007_rename_content_to_contents.sql`

---

## Quick Reference Commands

```bash
# Full automated test (recommended)
DB_PASSWORD=secret ./run_migration_007_tests.sh --full

# Pre-migration only
DB_PASSWORD=secret ./run_migration_007_tests.sh --pre

# Post-migration only
DB_PASSWORD=secret ./run_migration_007_tests.sh --post

# API tests only
./run_migration_007_tests.sh --api

# Rollback
DB_PASSWORD=secret ./run_migration_007_tests.sh --rollback

# View test results
ls -lt results/
cat results/post_migration_*.txt | grep -E "PASS|FAIL|WARNING"
```

---

**Last Updated**: 2025-10-27
**Migration Version**: 007
**Status**: Ready for testing
