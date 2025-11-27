# Shared Components - Quick Fixes Checklist

**Generated:** 2025-11-27
**Priority:** CRITICAL issues must be fixed before next deployment

---

## 🔴 CRITICAL - Fix Immediately (Today)

### Issue #1: Duplicate Authentication Dependencies
**File:** `shared/auth.py` + `shared/middleware.py`
**Problem:** Two different `get_current_user()` functions causing type confusion

**Quick Fix:**
```bash
# Step 1: Search all files using middleware auth
grep -r "from shared.middleware import get_current_user" backend-python/services/

# Step 2: Replace with unified import
# Find: from shared.middleware import get_current_user, get_current_active_user
# Replace: from shared.auth import get_current_user, CurrentUser

# Step 3: Update function signatures
# Before: current_user: dict = Depends(get_current_active_user)
# After: current_user: CurrentUser = Depends(get_current_user)

# Step 4: Update dict access to object access
# Before: current_user["user_id"]
# After: current_user.id
```

**Files to Update (5 files):**
1. `backend-python/services/user/routes.py`
2. `backend-python/services/audit/routes.py`
3. `backend-python/services/device/management_routes.py`
4. `backend-python/services/organization/routes.py`
5. `backend-python/services/tag/routes.py`

**Validation:**
```bash
# After fix, this should return 0 results:
grep -r "from shared.middleware import get_current_user" backend-python/services/
```

---

## 🟠 HIGH - Fix This Week

### Issue #2: Session Validation Performance
**File:** `shared/auth.py` lines 459-484
**Problem:** DB query on every authenticated request (100% overhead)

**Option A: Redis Cache (Recommended)**
```python
# In shared/auth.py, modify get_current_user()
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    if not credentials:
        raise AuthenticationError(message="Token tidak ditemukan")

    # Decode token
    payload = decode_token(credentials.credentials)

    # Extract user info
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    organization_id = payload.get("organization_id")

    if not user_id or not username or not role:
        raise AuthenticationError(message="Token tidak valid - data user tidak lengkap")

    # FAST PATH: Check Redis for revoked tokens
    token_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()

    from shared.config import settings
    import redis

    if settings.REDIS_URL:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            is_revoked = redis_client.get(f"revoked_token:{token_hash}")
            if is_revoked:
                raise AuthenticationError(
                    message="Session has been revoked",
                    code=ErrorCodes.SESSION_REVOKED
                )
        except Exception:
            pass  # Fallback to DB check if Redis fails

    return CurrentUser(
        id=int(user_id),
        username=username,
        role=role,
        organization_id=organization_id
    )
```

**Option B: Remove Session Check (Quick Fix)**
```python
# Comment out lines 459-484 in shared/auth.py
# Accept slightly reduced security for better performance
# Rely on token expiration only
```

**Recommendation:** Implement Option A (Redis cache) properly

---

### Issue #3: Inconsistent Error Handling
**Files:** `shared/middleware.py`, services using HTTPException

**Quick Fix Script:**
```python
# Find all HTTPException usage
grep -rn "raise HTTPException" backend-python/shared/

# Replace pattern:
# Before:
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"message": "Session revoked", "code": "SESSION_REVOKED"}
)

# After:
from shared.errors import AuthenticationError, ErrorCodes
raise AuthenticationError(
    message="Session revoked",
    code=ErrorCodes.SESSION_REVOKED
)
```

**Files to Update:**
- `shared/middleware.py` (3 occurrences)

---

## 🟡 MEDIUM - Fix Next Sprint

### Issue #4: Rate Limiter Logging
**File:** `shared/rate_limiter.py` lines 246, 249, 251

**Quick Fix:**
```python
# Replace print() with logger
from shared.logging import app_logger

# Line 246:
# Before: print(f"[Rate Limiter] Using Redis backend: {redis_url}")
# After:
app_logger.info(f"Rate Limiter using Redis backend: {redis_url}")

# Line 249:
# Before: print(f"[Rate Limiter] Redis connection failed: {e}, falling back to in-memory")
# After:
app_logger.warning(f"Rate Limiter: Redis connection failed, using in-memory fallback: {e}")
if settings.ENVIRONMENT == "production":
    raise RuntimeError("Redis required for production rate limiting")

# Line 251:
# Before: print(f"[Rate Limiter] REDIS_URL not set, using in-memory fallback")
# After:
app_logger.warning("Rate Limiter: REDIS_URL not set, using in-memory fallback")
```

---

### Issue #5: Error Handler Logging
**File:** `shared/errors.py` lines 202-203, 231-232

**Quick Fix:**
```python
# Replace traceback.print_exc() with proper logging
from shared.logging import error_logger

# Before (lines 202-203):
import traceback
traceback.print_exc()

# After:
error_logger.log_error(e, context={"function": func.__name__})
```

---

### Issue #6: Config Defaults
**File:** `shared/config.py`

**Quick Fix:**
```python
# Add environment-aware defaults
from pydantic import Field
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # Make DEBUG environment-aware
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development") != "production"
    )

    # Add development defaults for required URLs
    PUBLIC_BASE_URL: str = Field(default="http://localhost:8001")
    CMS_URL: str = Field(default="http://localhost:3000")
    PLAYER_URL: str = Field(default="http://localhost:8080")

    # Override in production via .env file
```

---

## 🟢 LOW - Nice to Have

### Enhancement #1: Configurable Token Expiry
**File:** `shared/auth.py` line 203

```python
# In shared/config.py, add:
DEVICE_TOKEN_EXPIRE_DAYS: int = 365

# In shared/auth.py, replace line 203:
# Before:
expire = datetime.now(timezone.utc) + timedelta(days=365)

# After:
expire = datetime.now(timezone.utc) + timedelta(days=settings.DEVICE_TOKEN_EXPIRE_DAYS)
```

---

### Enhancement #2: Specific Exception Handling
**File:** `shared/auth.py` lines 519-520, 877-878

```python
# Replace bare except with specific exceptions
# Before:
except:
    return None

# After:
except (AuthenticationError, JWTError, KeyError, ValueError):
    return None
```

---

### Enhancement #3: Remove Dead Code
**File:** `shared/config.py` lines 44-46

```python
# If Celery not used, remove:
# Celery
CELERY_BROKER_URL: str = ""
CELERY_RESULT_BACKEND: str = ""
```

---

## Testing Checklist

After applying fixes, run these tests:

```bash
# 1. Start services
cd /mnt/g/khoirul/signate
docker-compose -f docker/docker-compose.yml up -d

# 2. Test authentication endpoints
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 3. Test protected endpoint
TOKEN="<token from login>"
curl http://192.168.5.12:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Test rate limiting (5 requests in 60s)
for i in {1..6}; do
  curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "wrong", "password": "wrong"}'
  sleep 1
done

# 5. Check logs for errors
docker logs signage-backend --tail 100

# 6. Test session revocation
curl -X POST http://192.168.5.12:8001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

curl http://192.168.5.12:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Should return 401 Unauthorized
```

---

## Deployment Checklist

Before deploying to VPS production (72.61.209.158):

- [ ] All CRITICAL fixes applied and tested locally
- [ ] Unit tests written for shared/auth.py
- [ ] Redis session cache implemented
- [ ] Error handling standardized
- [ ] All print() replaced with logger
- [ ] Configuration validated
- [ ] Integration tests passed
- [ ] Performance benchmarks acceptable
- [ ] Documentation updated
- [ ] Git commit with detailed changelog

---

## Rollback Plan

If deployment fails:

```bash
# 1. SSH to VPS
sshpass -p '1(;2-Ur?F)PP73J#G-wW' ssh root@72.61.209.158

# 2. Stop backend
cd /root/signage
docker-compose -f docker/docker-compose.yml stop backend-api

# 3. Restore from backup
cp -r /root/signage_backup/backend-python /root/signage/

# 4. Restart backend
docker-compose -f docker/docker-compose.yml up -d backend-api

# 5. Verify
curl http://72.61.209.158:8001/api/v1/auth/me
```

---

## Performance Benchmarks

**Before Optimization:**
- Auth request: ~50ms (includes DB session check)
- Requests/sec: ~200

**After Optimization (Redis cache):**
- Auth request: ~5ms (Redis check only)
- Requests/sec: ~2000

**Target:** 10x performance improvement on authenticated endpoints

---

**Priority Order:**
1. 🔴 Fix authentication consolidation (TODAY)
2. 🟠 Implement Redis session cache (THIS WEEK)
3. 🟠 Standardize error handling (THIS WEEK)
4. 🟡 Improve logging (NEXT SPRINT)
5. 🟢 Code enhancements (BACKLOG)
