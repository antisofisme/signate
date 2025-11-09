# CRITICAL SECURITY FIXES REQUIRED

**Status**: 🔴 **URGENT - Security Vulnerabilities Found**
**Date**: 2025-11-08
**Priority**: P0 - Fix Immediately

---

## TL;DR - What's Wrong

Your device registration API has **3 critical security holes**:

1. **Organization ID Hijacking** - Any device can register to ANY organization
2. **Missing Device Authentication** - No JWT tokens for device endpoints
3. **Weak Code Generation** - Codes can collide, not cryptographically secure

**Risk**: Attackers can:
- Register devices to organizations they don't own
- Impersonate any device
- Access content/playlists of any organization
- Brute force activation codes

---

## Fix #1: Organization ID Hijacking (CRITICAL)

### The Problem

**File**: `backend-python/services/device/extended_routes.py:156-206`

```python
# CURRENT CODE (VULNERABLE):
@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    query = text("""
        INSERT INTO devices (
            ...
            organization_id,  # ⚠️ ACCEPTS org_id FROM UNTRUSTED PLAYER!
            ...
        ) VALUES (..., :organization_id, ...)
    """)

    result = db.execute(query, {
        "organization_id": request.organization_id  # ❌ ATTACKER CONTROLS THIS
    })
```

**Attack**:
```javascript
// Attacker opens DevTools in player
localStorage.setItem('organization_id', 999);
location.reload();
// Device now registers to organization 999 WITHOUT permission!
```

### The Fix

```python
# FIXED CODE:
@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    """
    SECURITY FIX: Never trust organization_id from player!
    Device must be activated by admin to get organization assignment.
    """
    code = request.activation_code or generate_activation_code()
    code_expires = datetime.now() + timedelta(minutes=10)
    device_name = request.device_name or f"Monitor-{code}"

    query = text("""
        INSERT INTO devices (
            device_type, device_name, unique_code, code_expires_at,
            platform, organization_id, status, created_at
        )
        VALUES (
            'monitor', :device_name, :unique_code, :code_expires_at,
            :platform, NULL, 'pending', NOW()
        )
        RETURNING id, device_name, unique_code, code_expires_at, status
    """)

    result = db.execute(query, {
        "device_name": device_name,
        "unique_code": code,
        "code_expires_at": code_expires,
        "platform": request.platform
        # ✅ NO organization_id - will be assigned during activation!
    }).fetchone()

    db.commit()

    # Return clean response (no wrapper)
    return {
        "id": result.id,
        "device_name": result.device_name,
        "unique_code": result.unique_code,
        "code_expires_at": result.code_expires_at.isoformat(),
        "organization_id": None,  # ✅ Explicitly null until activated
        "status": result.status,
        "created_at": result.created_at.isoformat()
    }
```

**Also update DTO** (`dtos.py:39-46`):
```python
class MonitorRegisterRequest(BaseModel):
    """Monitor device registration"""
    # ✅ REMOVE organization_id field - don't accept from player!
    activation_code: str
    device_name: Optional[str] = None
    platform: Optional[str] = "browser"
    device_type: str = "monitor"
```

**Test**:
```bash
# Test that org_id is NOT set on registration
curl -X POST http://localhost:8001/api/v1/devices/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "TEST01",
    "device_name": "Test Monitor"
  }'

# Response should have organization_id: null
# {
#   "id": 123,
#   "organization_id": null,  ✅
#   "status": "pending"
# }
```

---

## Fix #2: Missing Device JWT Tokens (CRITICAL)

### The Problem

Player expects `device_token` but backend never generates it:

```javascript
// Frontend (registration.js:129)
const device = new window.Device({
    device_token: data.device_token  // ⚠️ Backend returns undefined!
});
```

Without device tokens:
- Any client can call `/heartbeat` for any device_id
- Any client can fetch commands/content for any device
- No way to verify device authenticity

### The Fix

**Step 1**: Create device authentication module

**File**: `backend-python/shared/device_auth.py` (NEW)

```python
"""
Device JWT Authentication
Secure authentication for player/viewer devices
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from shared.config import settings

# Bearer token security scheme
security = HTTPBearer()


def generate_device_token(device_id: int) -> str:
    """
    Generate JWT token for device authentication

    Args:
        device_id: Device ID from database

    Returns:
        JWT token string
    """
    payload = {
        "device_id": device_id,
        "type": "device",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=365)  # 1 year validity
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def verify_device_token(token: str) -> int:
    """
    Verify device JWT token

    Args:
        token: JWT token string

    Returns:
        device_id from token

    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        # Verify token type
        if payload.get("type") != "device":
            raise ValueError("Invalid token type")

        device_id = payload.get("device_id")
        if not device_id:
            raise ValueError("Missing device_id in token")

        return device_id

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


async def get_current_device(
    credentials: HTTPAuthCredentials = Depends(security)
) -> int:
    """
    FastAPI dependency to get current authenticated device

    Usage:
        @router.post("/devices/{device_id}/heartbeat")
        def heartbeat(
            device_id: int,
            current_device: int = Depends(get_current_device)
        ):
            if device_id != current_device:
                raise HTTPException(403, "Device ID mismatch")

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        device_id from verified token

    Raises:
        HTTPException 401: If token is invalid or missing
    """
    try:
        device_id = verify_device_token(credentials.credentials)
        return device_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def verify_device_id_matches(
    device_id: int,
    current_device: int = Depends(get_current_device)
) -> int:
    """
    Verify that device_id in path matches authenticated device

    Usage:
        @router.post("/devices/{device_id}/heartbeat")
        def heartbeat(
            device_id: int = Depends(verify_device_id_matches)
        ):
            # device_id is verified to match token

    Raises:
        HTTPException 403: If device_id doesn't match token
    """
    if device_id != current_device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID in path does not match authenticated device"
        )

    return device_id
```

**Step 2**: Return token on registration

**File**: `backend-python/services/device/extended_routes.py`

```python
from shared.device_auth import generate_device_token

@router.post(DeviceRoutes.MONITOR_REGISTER, status_code=status.HTTP_201_CREATED)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    """Register monitor device"""
    # ... existing code to insert device ...

    result = db.execute(query, {...}).fetchone()
    db.commit()

    # ✅ GENERATE DEVICE TOKEN
    device_token = generate_device_token(result.id)

    return {
        "id": result.id,
        "device_name": result.device_name,
        "unique_code": result.unique_code,
        "code_expires_at": result.code_expires_at.isoformat(),
        "organization_id": None,
        "status": result.status,
        "created_at": result.created_at.isoformat(),
        "device_token": device_token  # ✅ RETURN TOKEN TO PLAYER
    }
```

**Step 3**: Protect device endpoints

**File**: `backend-python/services/device/routes.py`

```python
from shared.device_auth import verify_device_id_matches

@router.post(DeviceRoutes.HEARTBEAT, response_model=HeartbeatResponse)
def device_heartbeat(
    device_id: int = Depends(verify_device_id_matches),  # ✅ REQUIRE AUTH
    request: HeartbeatRequest = ...,
    use_case: DeviceHeartbeatUseCase = Depends(get_heartbeat_use_case)
):
    """
    Device heartbeat (requires device JWT token)

    Authorization header required:
        Authorization: Bearer <device_token>
    """
    # device_id is already verified by verify_device_id_matches
    # ... existing heartbeat logic ...
```

**Step 4**: Update frontend to send token

**File**: `player-vanillajs/js/core/api/client.js`

```javascript
// Existing APIClient should already send Authorization header
// Just verify it includes device_token:

class APIClient {
    static getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        // Add device token if available
        const deviceToken = localStorage.getItem('device_token');
        if (deviceToken) {
            headers['Authorization'] = `Bearer ${deviceToken}`;  // ✅
        }

        return headers;
    }

    static async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: this.getHeaders(),  // ✅ Includes device_token
            body: JSON.stringify(data)
        });
        // ... rest of implementation
    }
}
```

**Test**:
```bash
# 1. Register device (get token)
curl -X POST http://localhost:8001/api/v1/devices/monitor \
  -H "Content-Type: application/json" \
  -d '{"activation_code": "TEST01"}' | jq -r '.device_token' > token.txt

# 2. Try heartbeat WITHOUT token (should fail)
curl -X POST http://localhost:8001/api/v1/devices/123/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"unique_code": "TEST01"}'
# Expected: 401 Unauthorized

# 3. Try heartbeat WITH token (should succeed)
curl -X POST http://localhost:8001/api/v1/devices/123/heartbeat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat token.txt)" \
  -d '{"unique_code": "TEST01"}'
# Expected: 200 OK

# 4. Try heartbeat with wrong device_id (should fail)
curl -X POST http://localhost:8001/api/v1/devices/999/heartbeat \
  -H "Authorization: Bearer $(cat token.txt)" \
  -d '{"unique_code": "TEST01"}'
# Expected: 403 Forbidden (device_id mismatch)
```

---

## Fix #3: Weak Code Generation (MEDIUM)

### The Problem

```python
# CURRENT (WEAK):
def generate_activation_code() -> str:
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(6))  # ❌
```

Issues:
- Uses `random.choice()` (not cryptographically secure)
- No uniqueness check (codes can collide)
- Small keyspace (32^6 = ~1B combinations)

### The Fix

```python
import secrets
from sqlalchemy import exists, text

def generate_activation_code(db: Session) -> str:
    """
    Generate cryptographically secure unique activation code

    Args:
        db: Database session

    Returns:
        6-character unique code

    Raises:
        ValueError: If unable to generate unique code after 10 attempts
    """
    # Use cryptographically secure random
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 32 chars (exclude O, 0, I, 1)

    max_attempts = 10
    for attempt in range(max_attempts):
        # Generate code using secrets module (CSPRNG)
        code = ''.join(secrets.choice(chars) for _ in range(6))

        # Check uniqueness in database
        query = text("""
            SELECT EXISTS(
                SELECT 1 FROM devices WHERE unique_code = :code
            )
        """)

        code_exists = db.execute(query, {"code": code}).scalar()

        if not code_exists:
            return code

        # Log collision (should be rare)
        print(f"[WARNING] Activation code collision detected (attempt {attempt + 1}): {code}")

    # Failed to generate unique code after max_attempts
    raise ValueError(f"Failed to generate unique activation code after {max_attempts} attempts")
```

**Update call sites**:

```python
# File: extended_routes.py
@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    # Pass db session to code generator
    code = request.activation_code or generate_activation_code(db)  # ✅
```

```python
# File: request_activation_code.py
class RequestActivationCodeUseCase:
    def execute(self, ...):
        # Get database session from repository
        code = self._generate_code()  # Update this method

    def _generate_code(self) -> str:
        """Generate unique code using repository"""
        max_attempts = 10
        for _ in range(max_attempts):
            chars = string.ascii_uppercase + string.digits
            chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
            code = ''.join(secrets.choice(chars) for _ in range(6))  # ✅ Use secrets

            # Check uniqueness via repository
            existing = self.device_repo.find_by_code(code)
            if not existing:
                return code

        raise ValueError("Failed to generate unique code")
```

---

## Fix #4: Add Rate Limiting (RECOMMENDED)

Prevent brute force attacks on activation codes:

```python
# File: backend-python/requirements.txt
# Add:
slowapi==0.1.9
```

```python
# File: backend-python/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# File: backend-python/services/device/routes.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post(DeviceRoutes.ACTIVATE)
@limiter.limit("5/minute")  # ✅ Max 5 activation attempts per minute per IP
@handle_errors
def activate_device(
    request_body: ActivateDeviceRequest,
    http_request: Request,
    ...
):
    """Activate device (rate limited to prevent brute force)"""
    # ... existing activation logic
```

---

## Deployment Checklist

### Before Deploy

- [ ] Review all code changes
- [ ] Update unit tests
- [ ] Test in local environment
- [ ] Backup production database

### Deploy Steps

1. **Deploy Backend Changes**
   ```bash
   cd /home/gzjbbk/prototipe2
   git pull origin main
   docker-compose -f docker/docker-compose.yml up -d --build backend-api
   ```

2. **Verify Backend**
   ```bash
   # Check logs
   docker logs signage-backend --tail 50

   # Test registration endpoint
   curl http://192.168.5.12:8001/api/v1/devices/monitor \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"activation_code": "TEST01"}' | jq
   ```

3. **No Frontend Changes Needed**
   - Frontend already expects `device_token` and sends it
   - Frontend already stores `organization_id` separately
   - No code changes required in player-vanillajs

4. **Test End-to-End**
   - Open viewer in browser: http://192.168.5.12:8080
   - Should show activation code
   - Verify code appears in CMS device list
   - Activate from CMS
   - Verify viewer loads player

### After Deploy

- [ ] Monitor error logs for issues
- [ ] Test device registration flow
- [ ] Test device activation flow
- [ ] Verify heartbeat still works
- [ ] Check existing devices still functional

---

## Estimated Timeline

| Task | Effort | Priority |
|------|--------|----------|
| Fix #1: Org ID hijacking | 2 hours | 🔴 P0 - Today |
| Fix #2: Device JWT tokens | 1 day | 🔴 P0 - This week |
| Fix #3: Code generation | 4 hours | 🟡 P1 - This week |
| Fix #4: Rate limiting | 4 hours | 🟡 P1 - This month |
| Testing | 1 day | 🔴 P0 - Before deploy |

**Total**: ~3 days of focused work

---

## Questions?

**Q**: Will this break existing devices?
**A**: No. Existing active devices will continue working. Only affects new registrations.

**Q**: Do I need to update the frontend?
**A**: No. Frontend already expects `device_token` and handles it correctly.

**Q**: What about devices currently pending activation?
**A**: They may have wrong `organization_id`. Run this SQL to fix:
```sql
-- Reset all pending devices to null organization
UPDATE devices
SET organization_id = NULL
WHERE status = 'pending';
```

**Q**: How do I test this locally?
**A**:
1. Apply fixes to `backend-python/`
2. Rebuild container: `docker-compose up -d --build backend-api`
3. Open viewer: http://192.168.5.12:8080
4. Test registration → activation flow

---

## Need Help?

Contact the backend team or open an issue with:
- Error logs from `docker logs signage-backend`
- Steps to reproduce
- Expected vs actual behavior
