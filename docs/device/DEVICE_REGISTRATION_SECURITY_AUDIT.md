# Device Registration API - Security & Architecture Audit

**Date**: 2025-11-08
**Auditor**: Backend System Architect
**Scope**: Device registration flow from player-vanillajs to backend-python

---

## Executive Summary

This audit identifies **CRITICAL security vulnerabilities** in the device registration flow that could allow:
1. **Organization ID hijacking** - Malicious devices can register to any organization
2. **Missing JWT device_token implementation** - No device authentication after registration
3. **Weak activation code generation** - Potential collision and brute force risks
4. **API design inconsistencies** - Field naming and contract mismatches

**Risk Level**: 🔴 **CRITICAL** - Immediate action required

---

## 1. Security Vulnerabilities

### 🔴 CRITICAL: Organization ID Hijacking (CVE-Level Risk)

**Location**: `/api/v1/devices/monitor` endpoint

**Vulnerability**:
```python
# backend-python/services/device/extended_routes.py:156-206
@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    """
    VULNERABLE: organization_id is sent by UNTRUSTED player!
    Malicious player can register to ANY organization by sending different org_id
    """
    query = text("""
        INSERT INTO devices (
            ...
            organization_id,  # ⚠️ SECURITY HOLE - from untrusted client!
            ...
        ) VALUES (..., :organization_id, ...)
    """)

    result = db.execute(query, {
        "organization_id": request.organization_id  # ⚠️ ATTACKER CONTROLS THIS!
    })
```

**Frontend Code** (player-vanillajs/js/activation/services/registration.js):
```javascript
// Line 100-110: Player sends organization_id to backend
const requestBody = {
    activation_code: code,
    device_name: deviceName,
    platform: platform,
    device_type: 'monitor'
};

// If organization_id exists in localStorage (re-registration)
if (organizationId) {
    requestBody.organization_id = organizationId;  // ⚠️ ATTACKER CAN MODIFY THIS!
}
```

**Attack Scenario**:
1. Attacker opens browser DevTools
2. Sets localStorage: `localStorage.setItem('organization_id', 999)`
3. Reloads player → Registers to organization 999 WITHOUT authorization
4. Attacker's device appears in organization 999's device list
5. Attacker can view organization 999's content/playlists

**Impact**:
- **Data Breach**: Unauthorized access to organization content
- **Privacy Violation**: Device appears in wrong organization
- **Content Hijacking**: Wrong organization pays for attacker's bandwidth
- **Compliance Risk**: Violates tenant isolation requirements

**Correct Flow** (how it SHOULD work):
```
1. Player registers WITHOUT organization_id (always null on registration)
2. Device created with status='pending', organization_id=NULL
3. Admin activates device from CMS with JWT token
4. Backend assigns device.organization_id = admin.organization_id (from JWT!)
5. Device now belongs to admin's organization securely
```

**Current Broken Flow**:
```
1. Player sends organization_id=999 (attacker-controlled)
2. Device created with organization_id=999 (NO VALIDATION!)
3. Device belongs to organization 999 WITHOUT any admin approval
```

---

### 🔴 CRITICAL: Missing JWT Device Token Implementation

**Problem**: Frontend expects `device_token` but backend NEVER generates it!

**Frontend Code** (registration.js:129):
```javascript
const device = new window.Device({
    id: data.id,
    code: code,
    name: deviceName,
    status: 'pending',
    organization_id: data.organization_id,
    platform: platform,
    device_token: data.device_token  // ⚠️ Backend returns undefined!
});
```

**Backend Response** (extended_routes.py:194-206):
```python
return {
    "success": True,
    "data": {
        "id": result.id,
        "device_name": result.device_name,
        "unique_code": result.unique_code,
        "code_expires_at": result.code_expires_at,
        "organization_id": result.organization_id,
        "status": result.status,
        "created_at": result.created_at
        # ⚠️ MISSING: "device_token": "JWT_TOKEN_HERE"
    }
}
```

**Impact**:
- **No Device Authentication**: Any client can call `/heartbeat` with device_id
- **Impersonation Risk**: Attacker can send heartbeat for device_id=123
- **Command Hijacking**: Attacker can fetch commands for any device
- **Content Theft**: Attacker can get playlist for any device

**Required Fix**:
```python
import jwt
from datetime import datetime, timedelta

def generate_device_token(device_id: int, organization_id: int) -> str:
    """Generate JWT token for device authentication"""
    payload = {
        "device_id": device_id,
        "organization_id": organization_id,
        "type": "device",
        "exp": datetime.utcnow() + timedelta(days=365)  # 1 year expiry
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# In register_monitor_device():
device_token = generate_device_token(result.id, result.organization_id)

return {
    "data": {
        "id": result.id,
        "device_token": device_token  # ✅ Return token to frontend
    }
}
```

Then protect endpoints:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_device_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Verify device JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload["device_id"]
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid device token")

@router.post("/devices/{device_id}/heartbeat")
def heartbeat(
    device_id: int,
    verified_device_id: int = Depends(verify_device_token)
):
    # Verify device_id matches token
    if device_id != verified_device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")
```

---

### 🟡 MEDIUM: Weak Activation Code Generation

**Current Implementation** (extended_routes.py:89-93):
```python
def generate_activation_code() -> str:
    """Generate 6-digit activation code"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 32 characters
    return ''.join(random.choice(chars) for _ in range(6))
```

**Issues**:
1. **Small Keyspace**: 32^6 = ~1 billion combinations (not enough for global scale)
2. **No Collision Prevention**: No check if code already exists in database
3. **Predictable Random**: Uses `random.choice()` instead of `secrets.choice()`
4. **No Rate Limiting**: Attacker can brute force codes

**Attack Scenario**:
```python
# Brute force attack (1000 tries/second)
import requests
for code in generate_all_codes():  # 1 billion combinations
    response = requests.post('/api/devices/activate', json={'unique_code': code})
    if response.status_code == 200:
        print(f"Found valid code: {code}")
```

**Recommended Fix**:
```python
import secrets
from sqlalchemy import exists

def generate_activation_code(db: Session) -> str:
    """Generate cryptographically secure unique activation code"""
    max_attempts = 10

    for _ in range(max_attempts):
        # Use secrets module for cryptographic randomness
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        code = ''.join(secrets.choice(chars) for _ in range(6))

        # Check uniqueness in database
        code_exists = db.query(
            exists().where(Device.unique_code == code)
        ).scalar()

        if not code_exists:
            return code

    raise ValueError("Failed to generate unique code after 10 attempts")
```

Add rate limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/devices/activate")
@limiter.limit("5/minute")  # Max 5 activation attempts per minute per IP
def activate_device(request, ...):
    ...
```

---

### 🟡 MEDIUM: Code Expiry Handling Inconsistency

**Issue**: Unclear responsibility for expired code cleanup

**Current Behavior**:
- Frontend polls `/check-activation/{code}` every 5 seconds
- Backend marks expired codes but doesn't auto-delete them
- No grace period before deletion
- Frontend handles expiry by reloading (clears localStorage)

**Problems**:
1. **Database Bloat**: Expired pending devices accumulate in database
2. **No Grace Period**: Code expires at exactly 10 minutes (harsh UX)
3. **Race Condition**: Admin might activate at 9:59, expires at 10:00
4. **Zombie Devices**: Expired devices with status='pending' never cleaned up

**Recommended Strategy**:

```python
# 1. Add grace period (5 minutes after expiry before deletion)
def can_activate(device: Device) -> bool:
    """Check if device can still be activated (with 5-min grace period)"""
    if not device.code_expires_at:
        return False

    grace_period = timedelta(minutes=5)
    expiry_with_grace = device.code_expires_at + grace_period

    return datetime.utcnow() < expiry_with_grace

# 2. Cleanup job (runs hourly via Celery/cron)
@celery.task
def cleanup_expired_devices():
    """Delete expired pending devices (after grace period)"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=15)  # 10min expiry + 5min grace

    deleted = db.query(Device).filter(
        Device.status == 'pending',
        Device.code_expires_at < cutoff_time
    ).delete()

    print(f"Cleaned up {deleted} expired pending devices")

# 3. Return grace period info to frontend
@router.get("/devices/check-activation/{code}")
def check_activation(code: str):
    device = find_device_by_code(code)

    if device.status == 'pending':
        expired = datetime.utcnow() > device.code_expires_at
        in_grace = can_activate(device)

        return {
            "activated": False,
            "expired": expired,
            "in_grace_period": in_grace,  # Frontend can show "Code expired but still valid for 5 min"
            "expires_in_seconds": (device.code_expires_at - datetime.utcnow()).total_seconds()
        }
```

---

## 2. API Design Issues

### 🟡 Response Format Inconsistency

**Problem**: Inconsistent field names between frontend and backend

**Backend DTO** (dtos.py:164):
```python
class ActivationStatusResponse(BaseModel):
    activated: bool  # ✅ Frontend expects this
    expired: bool
    device_id: Optional[int]
    device_name: Optional[str]
    organization_id: Optional[int]
    message: str
```

**BUT** in routes.py:234:
```python
# Backend uses device.is_active() method
if device.is_active():
    return ActivationStatusResponse(
        activated=True,  # ✅ Correct
        ...
    )
```

**Status Code Usage**:
- ✅ Good: `201 CREATED` for registration
- ✅ Good: `404 NOT FOUND` for invalid code
- ⚠️ Issue: Returns `200 OK` for expired codes (should return specific status)

**Recommended**:
```python
# Use 410 Gone for expired codes (semantic HTTP)
@router.get("/devices/check-activation/{code}")
def check_activation(code: str):
    device = find_device_by_code(code)

    if not device:
        raise HTTPException(status_code=404, detail="Code not found")

    if device.is_pending() and not device.can_activate():
        # Code expired - return 410 Gone
        raise HTTPException(
            status_code=410,
            detail={
                "expired": True,
                "message": "Activation code has expired"
            }
        )
```

---

### 🟢 Good: Field Naming Alignment

**Frontend expects** (activation-poll.js:119):
```javascript
if (data.activated && data.device_id) {
    // ✅ Backend returns correct fields
}
```

**Backend returns** (routes.py:236):
```python
return ActivationStatusResponse(
    activated=True,  # ✅ Matches frontend expectation
    device_id=device.id,  # ✅ Matches (not "id")
    device_name=device.device_name,  # ✅ Matches
    organization_id=device.organization_id  # ✅ Matches
)
```

✅ **This is correctly aligned!**

---

## 3. Backend Logic Issues

### 🔴 CRITICAL: Organization Assignment Vulnerability

**VULNERABLE CODE** (activate_device.py:87-89):
```python
# 🆕 Assign device to admin's organization (from JWT token)
device.organization_id = organization_id  # ✅ Correct (from JWT!)
device.status = 'active'
```

**BUT** registration endpoint is vulnerable:
```python
# extended_routes.py:189 - WRONG!
result = db.execute(query, {
    "organization_id": request.organization_id  # ⚠️ From untrusted player!
})
```

**Correct Flow**:
1. Registration: `organization_id = NULL` (always)
2. Activation: `organization_id = admin.organization_id` (from JWT)

**Fix Required**:
```python
@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    """
    FIXED: Never trust organization_id from player!
    """
    query = text("""
        INSERT INTO devices (
            device_type, device_name, unique_code, code_expires_at,
            platform, organization_id, status, created_at
        )
        VALUES (
            'monitor', :device_name, :unique_code, :code_expires_at,
            :platform, NULL, 'pending', NOW()  # ✅ organization_id = NULL always!
        )
        RETURNING id, device_name, unique_code, code_expires_at, status, created_at
    """)

    # Don't include organization_id in params!
    result = db.execute(query, {
        "device_name": device_name,
        "unique_code": code,
        "code_expires_at": code_expires,
        "platform": request.platform
        # ✅ NO organization_id parameter
    }).fetchone()

    return {
        "data": {
            "id": result.id,
            "organization_id": None,  # ✅ Return null (not assigned yet)
            "device_token": generate_device_token(result.id)  # ✅ Add token
        }
    }
```

---

### 🟡 MEDIUM: Activation Code Generation Not Unique

**Request Activation Code Use Case** (request_activation_code.py:95-101):
```python
def _generate_code(self) -> str:
    """Generate random 6-digit alphanumeric code"""
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    return ''.join(random.choice(chars) for _ in range(6))  # ⚠️ No uniqueness check!
```

**Issue**: No database check for existing codes

**Fix**:
```python
def _generate_code(self, max_attempts: int = 10) -> str:
    """Generate unique activation code"""
    for _ in range(max_attempts):
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        code = ''.join(secrets.choice(chars) for _ in range(6))

        # Check uniqueness
        existing = self.device_repo.find_by_code(code)
        if not existing:
            return code

    raise ValueError("Failed to generate unique code")
```

---

## 4. Frontend-Backend Contract Issues

### Response Format

**Backend** (extended_routes.py:194):
```python
return {
    "success": True,  # ⚠️ Wrapper object
    "data": {
        "id": result.id,
        "unique_code": result.unique_code,
        ...
    }
}
```

**Frontend expects** (registration.js:113-116):
```javascript
const data = await window.APIClient.post(...);  // Expects data.id directly

const device = new window.Device({
    id: data.id,  // ⚠️ Should be data.data.id if backend wraps in "data"
});
```

**Issue**: Inconsistency - some endpoints wrap in `{success, data}`, others return data directly

**Recommendation**: **Standardize ALL responses**

```python
# Option 1: Always wrap (consistent)
return {
    "success": True,
    "data": {...},
    "message": "..."
}

# Option 2: Never wrap (REST standard)
return {
    "id": result.id,
    "device_name": result.device_name,
    ...
}
```

Choose Option 2 (REST standard) for cleaner API.

---

## 5. Security Recommendations

### Immediate Actions (Critical)

1. **Fix Organization ID Hijacking** ⏰ **DO TODAY**
   ```python
   # In register_monitor_device():
   # ALWAYS set organization_id = NULL on registration
   # Let activation endpoint assign it from JWT token
   ```

2. **Implement Device JWT Tokens** ⏰ **DO THIS WEEK**
   ```python
   # Generate device_token on registration
   # Validate token on heartbeat/commands/content endpoints
   ```

3. **Add Rate Limiting** ⏰ **DO THIS WEEK**
   ```python
   # Limit activation attempts to 5/minute per IP
   # Limit registration to 10/hour per IP
   ```

### Short-term (Within 1 month)

4. **Improve Code Generation**
   - Use `secrets` module instead of `random`
   - Check uniqueness in database
   - Consider 8-character codes for larger keyspace

5. **Add Code Cleanup Job**
   - Delete expired pending devices after grace period
   - Run hourly via Celery

6. **Standardize API Responses**
   - Remove `{success, data}` wrapper
   - Use HTTP status codes for success/failure
   - Document all endpoints with OpenAPI

### Long-term (Within 3 months)

7. **Add Device Certificate Authentication**
   - Generate unique certificate per device
   - Use mTLS for device-to-server communication
   - Rotate certificates annually

8. **Implement Audit Logging**
   - Log all registration attempts with IP
   - Log all activation attempts
   - Alert on suspicious patterns (many failed activations)

9. **Add Device Fingerprinting**
   - Store device_uuid, user_agent, screen_width
   - Detect device impersonation
   - Require re-activation if fingerprint changes

---

## 6. API Endpoint Summary

### Public Endpoints (No Auth)

| Endpoint | Method | Auth | Status |
|----------|--------|------|--------|
| `/api/v1/devices/monitor` | POST | ❌ None | 🔴 **VULNERABLE** (org_id hijack) |
| `/api/devices/check-activation/{code}` | GET | ❌ None | 🟢 OK |
| `/api/v1/devices/{id}/heartbeat` | POST | ❌ **MISSING** | 🔴 **NO AUTH** |
| `/api/client/logs/batch` | POST | ❌ **MISSING** | 🔴 **NO AUTH** |

### Protected Endpoints (JWT Auth)

| Endpoint | Method | Auth | Status |
|----------|--------|------|--------|
| `/api/v1/devices/activate` | POST | ✅ JWT | 🟢 OK (uses admin org_id) |
| `/api/v1/devices` | GET | ✅ JWT | 🟢 OK |
| `/api/v1/devices/{id}` | PUT | ✅ JWT | 🟢 OK |
| `/api/v1/devices/{id}` | DELETE | ✅ JWT | 🟢 OK |

---

## 7. Testing Recommendations

### Security Tests

```python
# Test 1: Organization ID Hijacking
def test_cannot_register_to_arbitrary_organization():
    """Attacker cannot register device to org they don't own"""
    response = client.post('/api/v1/devices/monitor', json={
        'activation_code': '123456',
        'organization_id': 999  # Attacker tries to register to org 999
    })

    device = db.get_device(response.json()['data']['id'])
    assert device.organization_id is None  # ✅ Should be NULL!

# Test 2: Device Token Required
def test_heartbeat_requires_device_token():
    """Heartbeat endpoint requires valid device token"""
    response = client.post('/api/v1/devices/123/heartbeat', json={
        'unique_code': '123456'
    })  # No Authorization header

    assert response.status_code == 401  # ✅ Unauthorized

# Test 3: Code Uniqueness
def test_activation_codes_are_unique():
    """Generated activation codes must be unique"""
    codes = set()
    for _ in range(100):
        code = generate_activation_code(db)
        assert code not in codes  # ✅ No duplicates
        codes.add(code)

# Test 4: Rate Limiting
def test_activation_rate_limiting():
    """Activation attempts are rate limited"""
    for i in range(10):
        response = client.post('/api/v1/devices/activate', json={
            'unique_code': f'TEST{i:02d}'
        })

    # 11th attempt should be rate limited
    response = client.post('/api/v1/devices/activate', json={
        'unique_code': 'TEST99'
    })
    assert response.status_code == 429  # ✅ Too Many Requests
```

---

## 8. Migration Plan

### Phase 1: Emergency Patch (Day 1)

```python
# File: backend-python/services/device/extended_routes.py

@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(request: MonitorRegisterRequest, db: Session):
    """
    HOTFIX: Never trust organization_id from client!
    """
    # Generate code
    code = request.activation_code or generate_activation_code()

    # CRITICAL FIX: Always set organization_id = NULL
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
        "code_expires_at": datetime.now() + timedelta(minutes=10),
        "platform": request.platform
        # ✅ NO organization_id parameter!
    }).fetchone()

    db.commit()

    return {
        "id": result.id,  # Remove wrapper for consistency
        "device_name": result.device_name,
        "unique_code": result.unique_code,
        "organization_id": None,  # ✅ Explicitly return null
        "status": result.status
    }
```

### Phase 2: Device Token Implementation (Week 1)

```python
# File: backend-python/shared/device_auth.py

import jwt
from datetime import datetime, timedelta
from shared.config import settings

def generate_device_token(device_id: int) -> str:
    """Generate JWT token for device authentication"""
    payload = {
        "device_id": device_id,
        "type": "device",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=365)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_device_token(token: str) -> int:
    """Verify device token and return device_id"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "device":
            raise ValueError("Invalid token type")
        return payload["device_id"]
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

# Dependency for FastAPI
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_device(
    credentials: HTTPAuthCredentials = Depends(security)
) -> int:
    """Get current device from JWT token"""
    try:
        device_id = verify_device_token(credentials.credentials)
        return device_id
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired device token"
        )
```

Update registration endpoint:
```python
from shared.device_auth import generate_device_token

@router.post(DeviceRoutes.MONITOR_REGISTER)
def register_monitor_device(...):
    # ... existing code ...

    # Generate device token
    device_token = generate_device_token(result.id)

    return {
        "id": result.id,
        "device_token": device_token,  # ✅ Return token
        ...
    }
```

Protect endpoints:
```python
from shared.device_auth import get_current_device

@router.post("/devices/{device_id}/heartbeat")
def heartbeat(
    device_id: int,
    request: HeartbeatRequest,
    current_device: int = Depends(get_current_device)  # ✅ Require auth
):
    # Verify device_id matches token
    if device_id != current_device:
        raise HTTPException(status_code=403, detail="Device ID mismatch")

    # ... existing heartbeat logic ...
```

---

## 9. Conclusion

### Critical Findings

1. **Organization ID Hijacking** - Allows unauthorized device registration
2. **Missing Device Authentication** - No JWT token validation on device endpoints
3. **Weak Code Generation** - No uniqueness checks, predictable randomness

### Priority Actions

| Priority | Action | Timeline | Risk if Not Fixed |
|----------|--------|----------|-------------------|
| 🔴 P0 | Fix org_id hijacking | **TODAY** | Data breach, tenant isolation failure |
| 🔴 P0 | Implement device JWT | **This Week** | Device impersonation, content theft |
| 🟡 P1 | Add rate limiting | This Week | Brute force attacks |
| 🟡 P1 | Improve code generation | This Month | Code collisions, database errors |
| 🟢 P2 | Add cleanup job | This Month | Database bloat |
| 🟢 P2 | Standardize API responses | This Month | Frontend bugs, confusion |

### Estimated Effort

- **Emergency Patch** (org_id fix): 2 hours
- **Device JWT Implementation**: 1 day
- **Rate Limiting**: 4 hours
- **Code Generation Improvements**: 4 hours
- **Cleanup Job**: 1 day
- **API Standardization**: 2 days

**Total**: ~5 days of focused development

---

## Appendix: Secure Registration Flow Diagram

### Current (INSECURE) Flow
```
Player                     Backend                    Database
  |                          |                          |
  |--POST /register--------->|                          |
  | {org_id: 999} ❌        |                          |
  |                          |--INSERT device---------->|
  |                          | org_id=999 ❌           |
  |<-------device_id---------|                          |
  |                          |                          |
  | ❌ Device registered to org 999 WITHOUT validation!
```

### Recommended (SECURE) Flow
```
Player                     Backend                    CMS Admin
  |                          |                          |
  |--POST /register--------->|                          |
  | {code: "ABC123"}        |                          |
  | ✅ NO org_id sent       |                          |
  |                          |--INSERT device---------->|
  |                          | org_id=NULL ✅          |
  |<------device_token-------|                          |
  | device_id + JWT ✅      |                          |
  |                          |                          |
  |--- Poll activation ----->|                          |
  |                          |                          |
  |                          |<--POST /activate---------|
  |                          |  {code: "ABC123"}        |
  |                          |  JWT: {org_id: 123} ✅  |
  |                          |--UPDATE device---------->|
  |                          | org_id=123 (from JWT) ✅|
  |<------activated----------|                          |
  |                          |                          |
  | ✅ Device assigned to admin's org securely!
```

---

**End of Audit Report**
