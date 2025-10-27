# Migration 007 Quick Start Guide
## 5-Minute Testing Setup

---

## Step 1: Set Environment (30 seconds)

```bash
cd /mnt/g/khoirul/signate/backend/tests
export DB_PASSWORD="your_password_here"
```

---

## Step 2: Run Automated Tests (3-5 minutes)

```bash
# Option A: Full automated suite (RECOMMENDED)
./run_migration_007_tests.sh --full

# Option B: Step by step
./run_migration_007_tests.sh --pre      # Pre-migration tests
./run_migration_007_tests.sh --backup   # Create backup
./run_migration_007_tests.sh --migrate  # Execute migration
./run_migration_007_tests.sh --post     # Post-migration tests
./run_migration_007_tests.sh --api      # API endpoint tests
```

---

## Step 3: Review Results (1 minute)

```bash
# Check summary
cat results/post_migration_*.txt | grep -E "PASS|FAIL|WARNING" | tail -20

# View full report
ls -lt results/
less results/post_migration_*.txt
```

---

## Expected Output

### Success Indicators

```
✓ Database connection successful
✓ Pre-migration tests completed
✓ Baseline metrics saved
✓ Backup created successfully
✓ Migration executed successfully
✓ Table 'contents' verified
✓ Post-migration tests completed
✓ All critical tests passed!
✓ Record counts match!
✓ All foreign keys recreated correctly!
✓ Migration data integrity verified!
✓ All API endpoint tests passed!
```

### Test Summary

```
Test Summary:
  PASS: 20+
  FAIL: 0
  WARNING: 0
```

---

## If Tests Pass

```bash
# Restart backend API
docker-compose restart backend-api

# Test frontend
# Open: http://localhost:3000/content

# Monitor logs
docker-compose logs -f backend-api
```

---

## If Tests Fail

```bash
# Review failures
cat results/post_migration_*.txt | grep "FAIL"

# Rollback
./run_migration_007_tests.sh --rollback

# Investigate issue
cat results/post_migration_*.txt
```

---

## Rollback Command (Emergency)

```bash
# Quick rollback
DB_PASSWORD=secret ./run_migration_007_tests.sh --rollback

# Or restore from backup
docker exec -i signage-postgres psql -U signage_user signage_db \
  < ../backups/signage_db_pre_migration_007_*.sql
```

---

## Test Checklist

After migration passes all tests:

- [ ] Backend API responds: `curl http://192.168.5.12:8001/api/content`
- [ ] Frontend loads: http://localhost:3000/content
- [ ] Can upload content via UI
- [ ] Can create playlist with content
- [ ] Can assign content to device
- [ ] Settings shows media storage

---

## Files You Need

1. `run_migration_007_tests.sh` - Automated test runner
2. `test_migration_007_pre.sql` - Pre-migration tests
3. `test_migration_007_post.sql` - Post-migration tests
4. `MIGRATION_007_TEST_GUIDE.md` - Detailed manual (if needed)

---

## Common Issues

### Can't connect to database

```bash
# Check database running
docker-compose ps signage-postgres

# Verify password
echo $DB_PASSWORD
```

### Permission denied

```bash
chmod +x run_migration_007_tests.sh
```

### Script not found

```bash
cd /mnt/g/khoirul/signate/backend/tests
pwd  # Should show: /mnt/g/khoirul/signate/backend/tests
```

---

## Help Commands

```bash
# Show script help
./run_migration_007_tests.sh --help

# Check test files exist
ls -lah test_migration_007_*.sql

# View comprehensive guide
cat MIGRATION_007_TEST_GUIDE.md

# View detailed README
cat README.md
```

---

## Time Estimates

- Pre-migration tests: 30 seconds
- Database backup: 30-60 seconds
- Migration execution: 5-10 seconds
- Post-migration tests: 1-2 minutes
- API endpoint tests: 30 seconds
- **Total**: 3-5 minutes

---

## Contact & References

**Detailed Guide**: `MIGRATION_007_TEST_GUIDE.md`
**Full README**: `README.md`
**Migration Plan**: `/mnt/g/khoirul/signate/docs/archive/documentation-review-20251027/CONTENT_TABLE_RENAME_PLAN.md`

---

**Last Updated**: 2025-10-27
**Status**: Ready for use
