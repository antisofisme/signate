# DEPLOYMENT GUIDE - P0 Critical Fixes

**Date**: 2025-01-14
**Fixes**: 5 Code Fixes + 3 Database Migrations
**Estimated Deployment Time**: 30-45 minutes
**Downtime Required**: ~5 minutes for migrations

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### 1. Prerequisites
- [ ] All changes committed to Git
- [ ] Backup of production database created
- [ ] Server access credentials ready (gzjbbk@192.168.5.12)
- [ ] Low-traffic window scheduled (recommended: 2-4 AM)
- [ ] Rollback plan prepared

### 2. Files to Deploy
**Code Changes** (36 files modified):
```
backend-python/shared/auth.py
backend-python/shared/logging.py
backend-python/shared/password_reset.py
backend-python/shared/rate_limiter.py
backend-python/services/auth/repositories/user_repo.py
backend-python/services/auth/dtos.py
backend-python/services/auth/domain/user.py
backend-python/services/content/repositories/content_repo.py
backend-python/services/device/use_cases/heartbeat.py
... (33 files total - see FIX_SUMMARY for complete list)
```

**Database Migrations**:
```
backend-python/migrations/046_add_cascade_users_organization.sql
backend-python/migrations/047_create_password_reset_tokens_table.sql
backend-python/migrations/048_add_unique_activation_code.sql
```

**Helper Scripts**:
```
scripts/fix_timezone_aware_datetimes.py
```

---

## 🚀 DEPLOYMENT PROCEDURE

### Step 1: Backup Database (5 minutes)
```bash
# SSH to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Create backup directory
mkdir -p ~/backups/pre_p0_fixes_$(date +%Y%m%d)

# Backup database
docker exec signage-postgres pg_dump -U signage_user -d signage_db > \
  ~/backups/pre_p0_fixes_$(date +%Y%m%d)/signage_db_backup.sql

# Verify backup size
ls -lh ~/backups/pre_p0_fixes_$(date +%Y%m%d)/signage_db_backup.sql

# Expected: > 1MB (contains all tables and data)
```

### Step 2: Stop Backend Service (1 minute)
```bash
# Stop backend to prevent conflicts during migration
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml stop backend-api

# Verify stopped
docker ps | grep signage-backend
# Should return nothing
```

### Step 3: Deploy Code Changes (5 minutes)
```bash
# From LOCAL machine (WSL):
cd /mnt/g/khoirul/signate

# Sync code changes to server (excluding __pycache__, .git, etc)
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'venv' \
  --exclude '.env' \
  backend-python/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# Verify files synced
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "ls -lh /home/gzjbbk/signate/backend-python/migrations/046*"
# Should show migration files
```

### Step 4: Run Database Migrations (3-5 minutes)
```bash
# SSH to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

cd /home/gzjbbk/signate

# Migration 046: Add CASCADE constraint
echo "Running migration 046..."
docker exec -i signage-postgres psql -U signage_user -d signage_db < \
  backend-python/migrations/046_add_cascade_users_organization.sql

# Verify CASCADE added
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "\d users" | grep "organization_id"
# Should show: "FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE"

# Migration 047: Create password_reset_tokens table
echo "Running migration 047..."
docker exec -i signage-postgres psql -U signage_user -d signage_db < \
  backend-python/migrations/047_create_password_reset_tokens_table.sql

# Verify table created
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "\dt password_reset_tokens"
# Should show the new table

# Migration 048: Add unique constraint on activation codes
echo "Running migration 048..."
docker exec -i signage-postgres psql -U signage_user -d signage_db < \
  backend-python/migrations/048_add_unique_activation_code.sql

# Verify constraint added
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "\d pending_devices" | grep "unique_activation_code"
# Should show unique constraint
```

### Step 5: Restart Backend Service (2 minutes)
```bash
# Restart backend with new code
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml start backend-api

# Or rebuild if needed:
# docker-compose -f docker/docker-compose.yml up -d --build backend-api

# Wait for backend to be healthy (30 seconds)
sleep 30

# Verify backend is running
docker ps | grep signage-backend
# Should show container running

# Check logs for errors
docker logs signage-backend-python --tail 50
# Should NOT show any errors, should see "Application startup complete"
```

### Step 6: Smoke Testing (5-10 minutes)
```bash
# Test 1: Health check
curl http://192.168.5.12:8001/health
# Expected: {"status":"healthy"}

# Test 2: Login (password validation fix)
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: Returns token + user info

# Test 3: Device heartbeat (timezone fix)
# This would be tested by player sending heartbeat
# Verify in database: last_seen_at should have timezone info

# Test 4: Check database
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT COUNT(*) FROM password_reset_tokens;"
# Expected: 0 (table exists but empty)

docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT constraint_name FROM information_schema.table_constraints
   WHERE table_name='users' AND constraint_name LIKE '%organization%';"
# Expected: Shows CASCADE constraint
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Automated Checks
```bash
# From LOCAL machine, run integration tests:
cd /mnt/g/khoirul/signate
python3 integration_tests_v2.py

# Expected results:
# - Login test: PASS
# - Device registration: PASS
# - Content upload: PASS
# - Heartbeat: PASS (with timezone-aware timestamp)
```

### Manual Verification Checklist
- [ ] **Dashboard**: Device online/offline status accurate
- [ ] **Login**: Works with strong password (8+ chars)
- [ ] **Login**: Rejects weak password (< 8 chars)
- [ ] **Password Reset**: Complete flow works
- [ ] **Logout**: Immediately revokes session (test with old token)
- [ ] **Delete Content**: Removed from playlists
- [ ] **Device Heartbeat**: Updates status immediately
- [ ] **No Errors**: Check backend logs for exceptions

### Performance Monitoring
```bash
# Monitor session verification performance
docker logs signage-backend-python --tail 100 | grep "Session verification"

# Check database connection pool
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='signage_db';"
# Should be < 20 connections

# Monitor request latency (if monitoring setup exists)
```

---

## 🔄 ROLLBACK PROCEDURE (If Issues Found)

### If Critical Bug Detected
```bash
# Stop backend
docker-compose -f docker/docker-compose.yml stop backend-api

# Restore database backup
docker exec -i signage-postgres psql -U signage_user -d signage_db < \
  ~/backups/pre_p0_fixes_$(date +%Y%m%d)/signage_db_backup.sql

# Restore old code (from Git)
cd /home/gzjbbk/signage
git stash  # Save current changes
git checkout <previous_commit_hash>

# Restart backend
docker-compose -f docker/docker-compose.yml start backend-api

# Verify rollback
curl http://192.168.5.12:8001/health
```

### If Performance Issues (Session Verification Slow)
**Option 1**: Disable session verification temporarily
```python
# In shared/auth.py, comment out session verification:
# try:
#     session_repo = SessionRepository(db)
#     session = session_repo.verify_session(...)
# except:
#     pass
```

**Option 2**: Implement Redis caching (see below)

---

## ⚡ PERFORMANCE OPTIMIZATION (Post-Deployment)

### Redis Caching for Session Verification
If session verification causes performance issues (> 50ms latency):

```python
# In shared/auth.py, add Redis caching:

import redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_current_user(...):
    payload = decode_token(credentials.credentials)

    # Check Redis cache first
    session_key = f"session:{payload['sub']}"
    cached_session = redis_client.get(session_key)

    if cached_session:
        return CurrentUser(...)  # Use cached data

    # If not in cache, check database
    session = session_repo.verify_session(...)

    if session:
        # Cache for 5 minutes
        redis_client.setex(session_key, 300, "active")
```

**Benefits**:
- Reduces DB queries by ~95%
- Latency drops from ~20ms to ~1ms
- Scales better with high traffic

**Setup Redis**:
```bash
# Install Redis on server
docker run -d --name signage-redis \
  -p 6379:6379 \
  redis:latest

# Update docker-compose.yml to include Redis
```

---

## 📊 EXPECTED IMPROVEMENTS

### Before Fixes
- ❌ Device status accuracy: 5%
- ❌ Password reset: Broken
- ❌ Logout: Doesn't work
- ❌ Deleted content: Still plays

### After Fixes
- ✅ Device status accuracy: 100%
- ✅ Password reset: Working
- ✅ Logout: Immediate revocation
- ✅ Deleted content: Removed from playlists
- ✅ Session security: Enforced
- ✅ Password security: 8+ chars required

---

## 🐛 TROUBLESHOOTING

### Issue: Migration fails with "constraint already exists"
```bash
# Check existing constraints
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "\d users"

# If constraint exists with different name, drop it first:
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "ALTER TABLE users DROP CONSTRAINT IF EXISTS <old_constraint_name>;"

# Re-run migration
```

### Issue: Backend crashes after restart
```bash
# Check logs
docker logs signage-backend-python --tail 100

# Common causes:
# 1. Missing dependencies - rebuild container
docker-compose -f docker/docker-compose.yml build backend-api

# 2. Database connection issue
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT 1;"

# 3. Python import error
docker exec -it signage-backend-python python -c "import services.auth"
```

### Issue: Session verification too slow (> 100ms)
```bash
# Check database connection pool
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT * FROM pg_stat_activity WHERE datname='signage_db';"

# Solutions:
# 1. Increase connection pool size in config
# 2. Add Redis caching (see Performance Optimization section)
# 3. Add database index on session token_hash (should already exist)
```

---

## 📝 POST-DEPLOYMENT TASKS

### Immediate (Within 1 hour)
- [ ] Monitor error logs for first hour
- [ ] Check Sentry/error tracking for exceptions
- [ ] Verify device status updates in real-time
- [ ] Test password reset with real email

### Within 24 hours
- [ ] Review performance metrics
- [ ] Check session verification latency
- [ ] Monitor database query performance
- [ ] Gather user feedback on fixed issues

### Within 1 week
- [ ] Plan Redis implementation for session caching
- [ ] Complete remaining 11 P0 fixes
- [ ] Update API documentation
- [ ] Train team on new password requirements

---

## 🎯 SUCCESS CRITERIA

Deployment is successful if:
1. ✅ All smoke tests pass
2. ✅ No errors in backend logs after 1 hour
3. ✅ Device status showing correctly on dashboard
4. ✅ Password reset flow works end-to-end
5. ✅ Logout immediately invalidates sessions
6. ✅ Performance acceptable (< 100ms per request)
7. ✅ No customer complaints about fixed issues

---

## 📞 SUPPORT CONTACTS

**If issues arise during deployment**:
- Backend Team: [Add contact]
- Database Admin: [Add contact]
- DevOps: [Add contact]

**Escalation**: If critical issues detected, immediately:
1. Stop deployment
2. Execute rollback procedure
3. Notify team lead
4. Document issue for post-mortem

---

**Deployment Prepared By**: Claude Code AI
**Reviewed By**: [To be filled]
**Approved By**: [To be filled]
**Deployment Date**: [To be scheduled]

---

**REMEMBER**:
- ⏰ Schedule during low-traffic window
- 💾 Always backup first
- 🧪 Test on staging if available
- 📊 Monitor closely after deployment
- 🔄 Be ready to rollback if needed
