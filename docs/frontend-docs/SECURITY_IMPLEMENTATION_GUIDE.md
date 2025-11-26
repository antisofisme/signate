# Security Implementation Guide - Console Interceptor

**Quick Start Guide for Critical Security Fixes**

This guide provides ready-to-use code for implementing the CRITICAL security fixes identified in the security audit.

---

## Phase 1: Critical Security Fixes (Week 1)

### 1. Add Device Token Authentication (Priority: CRITICAL)

**Estimated Time:** 4 hours

#### Backend Changes

**File:** `backend-python/services/device/log_routes.py`

```python
# Add these imports at the top
from fastapi import Header, HTTPException
from sqlalchemy import text

# Modify the create_device_log endpoint
@router.post("/devices/{device_id}/logs", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    authorization: str = Header(..., description="Bearer {device_token}"),
    db: Session = Depends(get_db)
):
    """
    Create device log entry - REQUIRES DEVICE AUTHENTICATION

    Devices must send valid device_token in Authorization header.
    """
    # Extract token from "Bearer {token}"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer {token}"
        )

    device_token = authorization[7:]  # Remove "Bearer " prefix

    # Verify device token belongs to this device
    device_check = db.execute(
        text("""
            SELECT d.id, d.organization_id, d.device_token
            FROM devices d
            WHERE d.id = :device_id AND d.device_token = :device_token
        """),
        {"device_id": device_id, "device_token": device_token}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token or device_id mismatch"
        )

    # Validate log level
    valid_levels = ['log', 'info', 'warn', 'error', 'debug']
    if request.log_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log_level. Must be one of: {', '.join(valid_levels)}"
        )

    # Insert log (rest of the function remains the same)
    query = text("""
        INSERT INTO device_logs (
            device_id, organization_id, log_level, message, source,
            stack_trace, user_agent, url, recorded_at
        )
        VALUES (
            :device_id, :organization_id, :log_level, :message, :source,
            :stack_trace, :user_agent, :url, NOW()
        )
        RETURNING id, device_id, log_level, message, source,
                  stack_trace, user_agent, url, recorded_at
    """)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "log_level": request.log_level,
        "message": request.message,
        "source": request.source,
        "stack_trace": request.stack_trace,
        "user_agent": request.user_agent,
        "url": request.url
    }).fetchone()

    db.commit()

    return LogResponse(
        id=result.id,
        device_id=result.device_id,
        log_level=result.log_level,
        message=result.message,
        source=result.source,
        stack_trace=result.stack_trace,
        user_agent=result.user_agent,
        url=result.url,
        recorded_at=result.recorded_at
    )
```

#### Frontend Changes

**File:** `player-vite/src/shared/logger/shared-logger.ts`

```typescript
// Modify the flush() method (around line 298-333)
async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const deviceId = localStorage.getItem('device_id');
    const deviceToken = localStorage.getItem('device_token');

    if (!deviceId || !deviceToken) {
      this.originalConsole.warn('[SharedLogger] Device not activated - logs not sent');
      return;
    }

    const logsToSend = [...this.logBuffer];
    this.logBuffer = []; // Clear buffer

    try {
      const response = await fetch(`${config.api.baseURL}/api/client/logs/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // ✅ ADD AUTHENTICATION HEADER
          Authorization: `Bearer ${deviceToken}`,
        },
        body: JSON.stringify({
          device_id: parseInt(deviceId, 10),
          logs: logsToSend,
        }),
      });

      // ✅ HANDLE AUTHENTICATION ERRORS
      if (response.status === 401 || response.status === 403) {
        this.originalConsole.error('[SharedLogger] Authentication failed - stopping log sync');
        this.originalConsole.error('[SharedLogger] Device token may be invalid or expired');
        this.stopPeriodicFlush();  // Stop sending if auth fails

        // Put logs back in buffer for later retry
        this.logBuffer = [...logsToSend, ...this.logBuffer];
        return;
      }

      if (!response.ok) {
        // Silent fail in dev mode - backend might not be running
        if (config.debug.debugMode) {
          this.originalConsole.warn('[SharedLogger] Failed to send logs:', response.statusText);
        }

        // Put logs back in buffer
        this.logBuffer = [...logsToSend, ...this.logBuffer];
      }
    } catch (error) {
      // Silent fail - backend might not be available (development mode)
      if (config.debug.debugMode) {
        this.originalConsole.warn('[SharedLogger] Backend unavailable, logs not sent');
      }

      // Put logs back in buffer for retry
      this.logBuffer = [...logsToSend, ...this.logBuffer];
    }
}
```

#### Testing

```bash
# Test 1: Without token (should fail with 401)
curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
  -H "Content-Type: application/json" \
  -d '{"device_id":1,"log_level":"error","message":"Test log"}'

# Expected: {"detail":"Invalid authorization header format..."}

# Test 2: With invalid token (should fail with 401)
curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token_here" \
  -d '{"device_id":1,"log_level":"error","message":"Test log"}'

# Expected: {"detail":"Invalid device token or device_id mismatch"}

# Test 3: With valid token (should succeed)
# Get device token from database first:
# docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT device_token FROM devices WHERE id=1;"

curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_DEVICE_TOKEN_HERE" \
  -d '{"device_id":1,"log_level":"error","message":"Test log"}'

# Expected: {"id":123,"device_id":1,"log_level":"error",...}
```

---

### 2. Implement Rate Limiting (Priority: CRITICAL)

**Estimated Time:** 6 hours

#### Install Dependencies

```bash
cd /mnt/g/khoirul/signate/backend-python
pip install slowapi redis
```

#### Create Rate Limiter Middleware

**File:** `backend-python/shared/middleware/rate_limiter.py` (NEW)

```python
"""
Rate Limiting Middleware
Prevents DoS attacks via log flooding
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
from typing import Optional

# Initialize limiter (uses in-memory storage by default)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
)

# Rate limit configurations
RATE_LIMITS = {
    "log_submission": "10 per minute",      # Individual log submissions
    "batch_log_submission": "2 per minute", # Batch log submissions
    "log_viewing": "60 per minute",         # CMS viewing logs
    "log_clearing": "5 per minute",         # Clear logs action
}

# Exception handler for rate limit exceeded
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom error response for rate limit exceeded"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )


class DeviceRateLimiter:
    """Per-device rate limiting using Redis"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize device rate limiter

        Args:
            redis_client: Redis client for distributed rate limiting.
                         If None, uses local dict (not recommended for production)
        """
        self.redis = redis_client
        self.local_cache = {}  # Fallback for development

    def check_log_rate(self, device_id: int, max_logs: int = 100, window_seconds: int = 3600) -> tuple[bool, int]:
        """
        Check if device is within rate limit

        Args:
            device_id: Device ID
            max_logs: Maximum logs allowed in time window (default: 100)
            window_seconds: Time window in seconds (default: 3600 = 1 hour)

        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        key = f"log_rate:device:{device_id}"

        if self.redis:
            # Use Redis for production
            current = self.redis.get(key)

            if current is None:
                # First log in this window
                self.redis.setex(key, window_seconds, 1)
                return True, max_logs - 1

            current_count = int(current)

            if current_count >= max_logs:
                return False, 0  # Rate limit exceeded

            # Increment counter (preserve TTL)
            self.redis.incr(key)
            return True, max_logs - current_count - 1

        else:
            # Fallback to local cache (dev mode only)
            import time

            if device_id not in self.local_cache:
                self.local_cache[device_id] = {'count': 1, 'reset_at': time.time() + window_seconds}
                return True, max_logs - 1

            cache = self.local_cache[device_id]

            # Reset if window expired
            if time.time() > cache['reset_at']:
                self.local_cache[device_id] = {'count': 1, 'reset_at': time.time() + window_seconds}
                return True, max_logs - 1

            if cache['count'] >= max_logs:
                return False, 0

            cache['count'] += 1
            return True, max_logs - cache['count']

    def get_remaining_quota(self, device_id: int, max_logs: int = 100) -> int:
        """Get remaining log quota for device"""
        key = f"log_rate:device:{device_id}"

        if self.redis:
            current = self.redis.get(key)
            return max_logs - int(current or 0)
        else:
            if device_id not in self.local_cache:
                return max_logs
            return max_logs - self.local_cache[device_id]['count']
```

#### Apply Rate Limiting to Routes

**File:** `backend-python/services/device/log_routes.py`

```python
# Add imports at the top
from fastapi import Request
from shared.middleware.rate_limiter import limiter, RATE_LIMITS, DeviceRateLimiter

# Initialize device rate limiter
device_rate_limiter = DeviceRateLimiter()  # Use Redis in production

# Apply rate limiting to log submission
@router.post("/devices/{device_id}/logs", response_model=LogResponse)
@limiter.limit(RATE_LIMITS["log_submission"])  # IP-based rate limit
async def create_device_log(
    request: Request,  # Required by slowapi
    device_id: int,
    log_request: CreateLogRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Create device log entry - RATE LIMITED"""

    # Check device-specific rate limit
    allowed, remaining = device_rate_limiter.check_log_rate(device_id, max_logs=100, window_seconds=3600)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Device rate limit exceeded. Maximum 100 logs per hour.",
            headers={"Retry-After": "3600"}
        )

    # Add rate limit info to response headers
    response = create_device_log_impl(device_id, log_request, authorization, db)

    # Note: Cannot modify headers in Pydantic response model directly
    # Use Response parameter if needed

    return response

# Apply to other endpoints
@router.get("/devices/{device_id}/logs", response_model=LogListResponse)
@limiter.limit(RATE_LIMITS["log_viewing"])
async def get_device_logs(
    request: Request,
    device_id: int,
    log_level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get device logs - RATE LIMITED"""
    # ... existing code

@router.delete("/devices/{device_id}/logs")
@limiter.limit(RATE_LIMITS["log_clearing"])
async def clear_device_logs(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db)
):
    """Clear device logs - RATE LIMITED"""
    # ... existing code
```

#### Register Rate Limiter in Main App

**File:** `backend-python/main.py`

```python
from shared.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add to app initialization
app = FastAPI(title="Signage Backend API")

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

#### Testing

```bash
# Test IP-based rate limit (send 11 requests in 1 minute)
for i in {1..11}; do
  echo "Request $i:"
  curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{"device_id":1,"log_level":"error","message":"Test '"$i"'"}'
  echo ""
done

# Expected: Requests 1-10 succeed, request 11 returns 429

# Test device-based rate limit (modify device_rate_limiter to allow only 5 logs for testing)
# Then send 6 logs
```

---

### 3. Add Authorization to Log Viewing (Priority: CRITICAL)

**Estimated Time:** 3 hours

**File:** `backend-python/services/device/log_routes.py`

```python
# Add import
from services.auth.dependencies import get_current_user
from services.auth.models import UserModel

@router.get("/devices/{device_id}/logs", response_model=LogListResponse)
@limiter.limit(RATE_LIMITS["log_viewing"])
async def get_device_logs(
    request: Request,
    device_id: int,
    log_level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),  # ✅ Require authentication
    db: Session = Depends(get_db)
):
    """
    Get device logs - REQUIRES CMS ADMIN AUTHENTICATION

    Returns paginated list of device logs.
    Only accessible by admins from the same organization as the device.
    """
    # ✅ Verify device belongs to user's organization
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # ✅ Multi-tenancy check
    if device_check.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Device belongs to another organization"
        )

    # Build query (rest of function remains the same)
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if log_level:
        where_clause += " AND log_level = :log_level"
        params["log_level"] = log_level

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_logs {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get logs
    query = text(f"""
        SELECT id, device_id, log_level, message, source,
               stack_trace, user_agent, url, recorded_at
        FROM device_logs
        {where_clause}
        ORDER BY recorded_at DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    logs = []
    for row in results:
        logs.append(LogResponse(
            id=row.id,
            device_id=row.device_id,
            log_level=row.log_level,
            message=row.message,
            source=row.source,
            stack_trace=row.stack_trace,
            user_agent=row.user_agent,
            url=row.url,
            recorded_at=row.recorded_at
        ))

    return LogListResponse(total=total, items=logs)

# Apply same authorization to other GET/DELETE endpoints
@router.get("/devices/{device_id}/logs/latest", response_model=LogListResponse)
async def get_latest_device_logs(
    device_id: int,
    count: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),  # ✅ Add auth
    db: Session = Depends(get_db)
):
    # ✅ Add same organization check
    device_check = db.execute(
        text("SELECT organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(status_code=404, detail="Device not found")

    if device_check.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ... rest of function

@router.delete("/devices/{device_id}/logs")
@limiter.limit(RATE_LIMITS["log_clearing"])
async def clear_device_logs(
    request: Request,
    device_id: int,
    current_user: UserModel = Depends(get_current_user),  # ✅ Add auth
    db: Session = Depends(get_db)
):
    # ✅ Add same organization check
    device_check = db.execute(
        text("SELECT organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(status_code=404, detail="Device not found")

    if device_check.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ... rest of function
```

---

### 4. Sanitize Logs to Prevent XSS (Priority: CRITICAL)

**Estimated Time:** 2 hours

#### Backend Sanitization

**File:** `backend-python/services/device/log_routes.py`

```python
import html
import re

def sanitize_log_message(message: str, max_length: int = 10000) -> str:
    """
    Sanitize log message to prevent XSS and injection attacks

    Args:
        message: Raw log message from device
        max_length: Maximum allowed message length

    Returns:
        Sanitized message safe for storage and display
    """
    if not message:
        return message

    # Limit length to prevent storage DoS
    message = message[:max_length]

    # Escape HTML to prevent XSS
    message = html.escape(message)

    # Remove null bytes (can cause SQL issues)
    message = message.replace('\x00', '')

    return message

def sanitize_log_field(field: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Sanitize optional log fields (source, user_agent, url, stack_trace)"""
    if not field:
        return field

    field = field[:max_length]
    field = html.escape(field)
    field = field.replace('\x00', '')

    return field

# Apply in create_device_log endpoint
@router.post("/devices/{device_id}/logs", response_model=LogResponse)
async def create_device_log(
    request: Request,
    device_id: int,
    log_request: CreateLogRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    # ... authentication code ...

    # ✅ SANITIZE ALL USER INPUT
    sanitized_message = sanitize_log_message(log_request.message, max_length=10000)
    sanitized_source = sanitize_log_field(log_request.source, max_length=500)
    sanitized_stack_trace = sanitize_log_field(log_request.stack_trace, max_length=5000)
    sanitized_user_agent = sanitize_log_field(log_request.user_agent, max_length=500)
    sanitized_url = sanitize_log_field(log_request.url, max_length=1000)

    # Insert with sanitized data
    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "log_level": log_request.log_level,
        "message": sanitized_message,
        "source": sanitized_source,
        "stack_trace": sanitized_stack_trace,
        "user_agent": sanitized_user_agent,
        "url": sanitized_url
    })

    # ... rest of function
```

#### Frontend Sanitization (Defense in Depth)

**File:** `cms-vite/package.json`

```json
{
  "dependencies": {
    "dompurify": "^3.0.8",
    "@types/dompurify": "^3.0.5"
  }
}
```

```bash
cd /mnt/g/khoirul/signate/cms-vite
npm install dompurify @types/dompurify
```

**File:** `cms-vite/src/features/devices/components/DeviceLogsViewer.tsx`

```typescript
import DOMPurify from 'dompurify';

// In the log rendering section (around line 348-349)
<p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all line-clamp-2">
  {/* ✅ SANITIZE BEFORE RENDERING */}
  {DOMPurify.sanitize(log.message)}
</p>

// Also sanitize in LogDetailModal
{log.source && (
  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
    Source: {DOMPurify.sanitize(log.source)}
  </p>
)}
```

**File:** `cms-vite/src/features/devices/components/LogDetailModal.tsx` (if exists)

```typescript
import DOMPurify from 'dompurify';

// Sanitize all user-controlled fields
<div>
  <h4>Message:</h4>
  <pre>{DOMPurify.sanitize(log.message)}</pre>
</div>

<div>
  <h4>Stack Trace:</h4>
  <pre>{log.stack_trace ? DOMPurify.sanitize(log.stack_trace) : 'N/A'}</pre>
</div>
```

#### Testing

```bash
# Test XSS prevention
curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "device_id": 1,
    "log_level": "error",
    "message": "<script>alert(\"XSS\")</script>Test log"
  }'

# Check database - should be escaped:
docker exec signage-postgres psql -U signage_user -d signage_db \
  -c "SELECT message FROM device_logs ORDER BY id DESC LIMIT 1;"

# Expected: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;Test log

# Test in CMS - should render as text, not execute script
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All code changes committed to Git
- [ ] Backend dependencies installed (`slowapi`, `redis`, `dompurify`)
- [ ] Database migrations run (if any)
- [ ] Environment variables set (Redis URL, encryption keys)
- [ ] Unit tests written for new security functions
- [ ] Integration tests passed

### Deployment Steps

```bash
# 1. Backup database
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/pre_security_fixes_$(date +%Y%m%d_%H%M%S).sql

# 2. Stop backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"

# 3. Upload backend changes
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  /mnt/g/khoirul/signate/backend-python/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# 4. Install new dependencies in container
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-backend pip install slowapi redis"

# 5. Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml start backend-api"

# 6. Verify backend is running
curl http://192.168.5.12:8001/docs

# 7. Upload frontend changes
sshpass -p 'Password@2021' rsync -avz \
  /mnt/g/khoirul/signate/cms-vite/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/cms-vite/

# 8. Rebuild frontend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate/cms-vite && npm install && npm run build"

# 9. Upload player changes
sshpass -p 'Password@2021' rsync -avz \
  /mnt/g/khoirul/signate/player-vite/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/

# 10. Rebuild player
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate/player-vite && npm install && npm run build"
```

### Post-Deployment Verification

```bash
# Test authentication
curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
  -H "Content-Type: application/json" \
  -d '{"device_id":1,"log_level":"error","message":"Test"}'

# Expected: 401 Unauthorized

# Test rate limiting
for i in {1..11}; do
  curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"device_id":1,"log_level":"error","message":"Test"}' &
done

# Expected: Some requests return 429

# Test XSS sanitization
# (See testing section above)

# Check backend logs
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend --tail 50"
```

---

## Rollback Plan

If critical issues occur after deployment:

```bash
# 1. Stop services
ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop"

# 2. Restore database backup
cat backups/pre_security_fixes_TIMESTAMP.sql | \
  ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db"

# 3. Restore code from Git
ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && git checkout PREVIOUS_COMMIT_HASH"

# 4. Restart services
ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml up -d"
```

---

## Next Steps (Phase 2-5)

After completing Phase 1 (Critical Security Fixes), proceed with:

- **Phase 2:** GDPR Compliance (Retention policy, HTTPS)
- **Phase 3:** Enhanced Security (HMAC signatures, PII patterns)
- **Phase 4:** Encryption (Field-level encryption)
- **Phase 5:** Monitoring (Audit logs, alerts)

See `CONSOLE_INTERCEPTOR_SECURITY_AUDIT.md` for detailed implementation guides for Phases 2-5.

---

## Support

For questions or issues during implementation:
1. Review security audit document
2. Check error logs: `docker logs signage-backend`
3. Test with curl commands provided above
4. Verify database state: `psql` commands

**Security Contact:** security@signage.local
**Emergency Rollback:** See Rollback Plan above
