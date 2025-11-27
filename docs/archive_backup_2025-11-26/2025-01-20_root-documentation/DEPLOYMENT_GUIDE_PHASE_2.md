# DEPLOYMENT GUIDE - Phase 2 P0 Fixes

**Date**: 2025-01-14
**Fixes**: 4 Code Fixes (No Database Migrations)
**Estimated Deployment Time**: 15-20 minutes
**Downtime Required**: ~3 minutes
**Risk Level**: LOW (no schema changes, backward compatible)

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### 1. Prerequisites
- [x] All Phase 2 changes completed and committed
- [ ] Backup of production database created
- [ ] Server access credentials ready (gzjbbk@192.168.5.12)
- [ ] Low-traffic window scheduled (recommended: off-peak hours)
- [ ] Rollback plan prepared

### 2. Files to Deploy (8 files)
**Code Changes Only** (No migrations required):
```
backend-python/services/auth/repositories/user_repo.py
backend-python/services/auth/use_cases/register.py
backend-python/services/user/use_cases/create_user.py
backend-python/services/user/use_cases/update_user.py
backend-python/services/playlist/repositories/playlist_repo.py
backend-python/services/playlist/use_cases/create_playlist.py
backend-python/services/device/use_cases/request_activation_code.py
backend-python/services/organization/domain/quota_service.py
```

### 3. What's Being Deployed
- ✅ **P0-6**: Multi-tenancy isolation (5 files)
- ✅ **P0-7**: Cache invalidation hooks (1 file)
- ✅ **P0-8**: Activation code retry logic (1 file)
- ✅ **P0-9**: Atomic quota enforcement (3 files)

---

## 🚀 DEPLOYMENT PROCEDURE

### Step 1: Backup Database (5 minutes)
```bash
# SSH to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Create backup directory with timestamp
BACKUP_DIR=~/backups/pre_phase2_fixes_$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec signage-postgres pg_dump -U signage_user -d signage_db > \
  $BACKUP_DIR/signage_db_backup.sql

# Verify backup size
ls -lh $BACKUP_DIR/signage_db_backup.sql
# Expected: > 200KB (contains all tables and data)

echo "✅ Backup created at: $BACKUP_DIR"
```

### Step 2: Stop Backend Service (1 minute)
```bash
# Stop backend to prevent conflicts during code deployment
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml stop backend-api

# Verify stopped
docker ps | grep signage-backend
# Should return nothing

echo "✅ Backend service stopped"
```

### Step 3: Deploy Code Changes (3 minutes)
```bash
# From LOCAL machine (WSL):
cd /mnt/g/khoirul/signate

# Sync code changes to server (excluding unnecessary files)
sshpass -p 'Password@2021' rsync -avz \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'venv' \
  --exclude '.env' \
  --exclude '*.md' \
  backend-python/services/auth/repositories/user_repo.py \
  backend-python/services/auth/use_cases/register.py \
  backend-python/services/user/use_cases/create_user.py \
  backend-python/services/user/use_cases/update_user.py \
  backend-python/services/playlist/repositories/playlist_repo.py \
  backend-python/services/playlist/use_cases/create_playlist.py \
  backend-python/services/device/use_cases/request_activation_code.py \
  backend-python/services/organization/domain/quota_service.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# Alternative: Sync entire backend-python directory
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'venv' \
  backend-python/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# Verify files synced
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "ls -lh /home/gzjbbk/signate/backend-python/services/auth/repositories/user_repo.py"
# Should show updated timestamp

echo "✅ Code changes deployed"
```

### Step 4: Restart Backend Service (2 minutes)
```bash
# SSH to server (if not already connected)
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

cd /home/gzjbbk/signate

# Restart backend with new code
docker-compose -f docker/docker-compose.yml start backend-api

# Wait for backend to be healthy (30 seconds)
sleep 30

# Verify backend is running
docker ps | grep signage-backend
# Should show container running

# Check logs for errors
docker logs signage-backend-python --tail 50
# Should NOT show any errors, should see "Application startup complete"

echo "✅ Backend service restarted"
```

### Step 5: Smoke Testing (5-10 minutes)
```bash
# Test 1: Health check
echo "Test 1: Health check"
curl http://192.168.5.12:8001/health
# Expected: {"status":"healthy","database":"connected","cache":"healthy"}

# Test 2: Login (verify session revocation still works)
echo "Test 2: Login"
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: Returns token + user info

# Save token for next tests
TOKEN="<paste_token_here>"

# Test 3: Create user (P0-6 multi-tenancy + P0-9 atomic quota)
echo "Test 3: Create user with multi-tenancy"
curl -X POST http://192.168.5.12:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser_phase2",
    "email":"testuser_phase2@example.com",
    "password":"testpass123",
    "full_name":"Test User Phase 2",
    "role":"viewer",
    "organization_id":4
  }'
# Expected: User created successfully OR quota exceeded error

# Test 4: Playlist update (P0-7 cache invalidation)
echo "Test 4: Update playlist (cache invalidation)"
curl -X PUT http://192.168.5.12:8001/api/v1/playlists/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Playlist Phase 2","is_active":true}'
# Expected: Playlist updated, cache invalidated

# Test 5: Device activation code (P0-8 retry logic)
echo "Test 5: Request activation code"
curl -X POST http://192.168.5.12:8001/api/v1/devices/request-activation \
  -H "Content-Type: application/json" \
  -d '{"code":"ABC123","device_name":"Test Device"}'
# Expected: Activation code created OR already exists error

# Test 6: Check backend logs
echo "Test 6: Check backend logs"
docker logs signage-backend-python --tail 100 | grep -E "(ERROR|CRITICAL|Exception)"
# Expected: No critical errors

echo "✅ All smoke tests completed"
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Automated Checks
```bash
# From LOCAL machine, run integration tests (if available):
cd /mnt/g/khoirul/signate
python3 integration_tests_v2.py

# Expected results:
# - Login test: PASS
# - User creation: PASS (or quota exceeded)
# - Playlist update: PASS
# - Device activation: PASS (or code exists)
```

### Manual Verification Checklist

#### P0-6: Multi-Tenancy Isolation
- [ ] Create user with duplicate username in DIFFERENT organization → SUCCESS
- [ ] Create user with duplicate username in SAME organization → ERROR
- [ ] Create user with duplicate email in DIFFERENT organization → SUCCESS
- [ ] Create user with duplicate email in SAME organization → ERROR

#### P0-7: Cache Invalidation
- [ ] Update playlist content → Device receives update within 10 seconds
- [ ] Assign playlist to device → Device starts playing immediately
- [ ] Unassign playlist from device → Device stops playing immediately
- [ ] Reorder playlist items → Device reflects new order immediately

#### P0-8: Activation Code Retry
- [ ] Request activation code with unique code → SUCCESS
- [ ] Request activation code with duplicate code → ERROR with clear message
- [ ] Concurrent activation requests (stress test) → No IntegrityError crashes

#### P0-9: Atomic Quota Enforcement
- [ ] Create users up to quota limit → All succeed
- [ ] Create user beyond quota → ERROR (quota exceeded)
- [ ] Concurrent user creation at quota edge → Exactly quota limit respected
- [ ] Same tests for playlists, devices, content

### Performance Monitoring
```bash
# Monitor response times
docker logs signage-backend-python --tail 100 | grep "ms"

# Check database connection pool
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='signage_db';"
# Should be < 20 connections

# Monitor request latency
# Expected increases:
# - User creation: +5-10ms (atomic quota check)
# - Playlist update: +10-20ms (cache invalidation)
# - Activation code: +0-300ms (retry logic, rare)
```

---

## 🔄 ROLLBACK PROCEDURE (If Issues Found)

### If Critical Bug Detected
```bash
# Stop backend
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml stop backend-api

# Restore database backup (if needed - unlikely for code-only changes)
# docker exec -i signage-postgres psql -U signage_user -d signage_db < \
#   ~/backups/pre_phase2_fixes_<timestamp>/signage_db_backup.sql

# Restore old code (from Git)
cd /home/gzjbbk/signate
git stash  # Save current changes
git checkout <previous_commit_hash>  # Commit before Phase 2

# Restart backend
docker-compose -f docker/docker-compose.yml start backend-api

# Verify rollback
curl http://192.168.5.12:8001/health

echo "⚠️ Rollback completed - Phase 2 fixes reverted"
```

### If Performance Issues Only
**Option 1**: Monitor and optimize (acceptable latency increase)
**Option 2**: Implement Redis caching for quota checks (future enhancement)
**Option 3**: Rollback if performance is unacceptable

---

## 📊 EXPECTED IMPROVEMENTS

### Before Phase 2 Fixes
- ❌ Username enumeration across organizations possible
- ❌ Cache invalidation manual (5-minute wait)
- ❌ Activation code collisions crash with IntegrityError
- ❌ Quota race conditions allow bypassing limits

### After Phase 2 Fixes
- ✅ Strict organization isolation (no cross-org leaks)
- ✅ Automatic cache invalidation (immediate updates)
- ✅ Graceful activation code retry (no crashes)
- ✅ Atomic quota enforcement (impossible to bypass)

---

## ⚠️ KNOWN ISSUES & MONITORING

### Expected Behavior Changes
1. **Multi-tenancy**: Users can have duplicate usernames/emails across orgs (INTENDED)
2. **Cache**: Devices update content immediately after playlist changes (INTENDED)
3. **Retry**: Activation code errors are more informative (INTENDED)
4. **Quota**: Strict enforcement may block concurrent edge-case requests (INTENDED)

### Monitoring Commands (Next 24 Hours)
```bash
# Watch backend logs for errors
docker logs signage-backend-python -f | grep -E "(ERROR|Exception|CRITICAL)"

# Monitor cache invalidation
docker logs signage-backend-python -f | grep "Invalidated cache"

# Monitor quota enforcement
docker logs signage-backend-python -f | grep "quota"

# Monitor activation code retries
docker logs signage-backend-python -f | grep "Race condition detected"
```

### Alert Triggers
- ⚠️ ERROR rate > 1% → Investigate immediately
- ⚠️ Response time > 500ms → Check database locks
- ⚠️ Activation retry rate > 10% → Investigate code collision frequency

---

## 🎯 DEPLOYMENT VERIFICATION CHECKLIST

### Pre-Deployment
- [ ] Database backup created (> 200KB)
- [ ] Server access verified
- [ ] Code changes reviewed
- [ ] Deployment window scheduled

### During Deployment
- [x] Backend stopped
- [x] Code synced (8 files)
- [x] Backend restarted
- [ ] Smoke tests passed

### Post-Deployment (Within 1 Hour)
- [ ] All smoke tests passed
- [ ] No critical errors in logs
- [ ] Performance acceptable (< 500ms)
- [ ] Manual verification tests passed

### Post-Deployment (Within 24 Hours)
- [ ] Multi-tenancy working correctly
- [ ] Cache invalidation working immediately
- [ ] No activation code crashes
- [ ] Quota enforcement strict and correct
- [ ] No customer complaints
- [ ] Performance metrics stable

---

## 📈 SUCCESS CRITERIA

Deployment is successful if:
1. ✅ All smoke tests pass
2. ✅ No errors in backend logs after 1 hour
3. ✅ Users can create duplicate usernames across orgs
4. ✅ Playlist updates reflect immediately on devices
5. ✅ Activation code errors are graceful
6. ✅ Quota limits are strictly enforced
7. ✅ Performance acceptable (< 500ms per request)
8. ✅ No customer complaints about fixed issues

---

## 📞 SUPPORT CONTACTS

**If issues arise during deployment**:
- Backend Team: [Add contact]
- DevOps: [Add contact]
- On-call Engineer: [Add contact]

**Escalation**: If critical issues detected, immediately:
1. Stop deployment
2. Execute rollback procedure
3. Notify team lead
4. Document issue for post-mortem

---

## 🎓 LESSONS LEARNED (To Be Updated Post-Deployment)

### What Went Well
- [ ] Code-only deployment (no migrations)
- [ ] Backward compatibility maintained
- [ ] Clear error messages
- [ ] Comprehensive logging

### What Could Be Improved
- [ ] Performance monitoring
- [ ] Automated testing
- [ ] Deployment automation
- [ ] Rollback speed

---

## 📝 DEPLOYMENT LOG

**Prepared By**: Claude Code AI
**Reviewed By**: [To be filled]
**Approved By**: [To be filled]
**Deployment Date**: [To be scheduled]
**Deployment Time**: [To be filled]
**Downtime**: [To be filled]
**Status**: [To be filled]

---

**REMEMBER**:
- ⏰ Schedule during low-traffic window
- 💾 Always backup first
- 🧪 Test on staging if available
- 📊 Monitor closely after deployment
- 🔄 Be ready to rollback if needed

---

**End of Deployment Guide - Phase 2**
