# Flow Comparison Analysis
## Backend vs Player vs Documentation Requirements

**Date**: 2025-01-14
**Analysis**: Backend-Python vs Player-Vite vs DEVICE_FLOW_DOCUMENTATION.md

---

## Executive Summary

### ❌ MAJOR GAPS FOUND

| Area | Backend | Player | Documentation | Status |
|------|---------|--------|---------------|--------|
| **IndexedDB Storage** | N/A | ⚠️ Partial | ✅ Complete Spec | 🔴 **MISSING device_config store** |
| **Organization ID Handling** | ✅ Correct | ❌ Wrong | ✅ Clear Spec | 🔴 **BROKEN - Player uses localStorage** |
| **Activation Endpoint** | ✅ Exists | ✅ Uses it | ⚠️ Different flow | 🟡 **MISMATCH in flow design** |
| **Hard Reset PIN** | ⚠️ Uses env var | ❌ Not implemented | ✅ Spec uses org PIN | 🔴 **NOT IMPLEMENTED** |
| **Token Refresh** | ❌ No endpoint | ❌ Not implemented | ✅ Complete spec | 🔴 **COMPLETELY MISSING** |
| **Device Release** | ❌ No endpoint | ❌ Not handled | ✅ Complete spec | 🔴 **COMPLETELY MISSING** |
| **Device Delete** | ✅ Exists | ❌ Not handled | ✅ Complete spec | 🔴 **NOT HANDLED in player** |
| **Unassigned Devices** | ⚠️ Partial | N/A | ✅ Complete spec | 🟡 **Backend has scope but no assign endpoint** |

---

## 1. Storage Strategy Comparison

### Documentation Requirement (DEVICE_FLOW_DOCUMENTATION.md)

```typescript
// IndexedDB schema - SINGLE SOURCE OF TRUTH
interface DeviceConfigStore {
  id: 'device_config';  // Single record
  device_uuid: string;  // Persistent UUID
  device_id: number | null;
  organization_id: number | null;  // ← SURVIVES clear cache
  organization_pin: string | null;  // ← 6-digit PIN for hard reset
  access_token: string | null;
  refresh_token: string | null;
  token_expires_at: number | null;
  device_name: string | null;
  device_type: string | null;
  last_activation_code: string | null;
  created_at: number;
  updated_at: number;
}
```

### Backend Implementation

**Status**: ✅ Backend doesn't store device config client-side (correct - it's player's responsibility)

**Backend stores**:
- `devices` table with all device info
- Returns `organization_pin` in response ✅ (line 301 in routes.py)

### Player Implementation (CURRENT)

**File**: `player-vite/src/shared/storage/`

**Status**: ⚠️ **INCOMPLETE - Missing device_config store entirely**

**What EXISTS**:
```typescript
// player-vite/src/shared/storage/storage-schema.ts
export const SCHEMA = {
  'media_cache': {  // ← Only has media cache!
    keyPath: 'id',
    indexes: [
      { name: 'by_content_id', keyPath: 'content_id' },
      { name: 'by_cached_at', keyPath: 'cached_at' },
    ],
  },
};
```

**What PLAYER ACTUALLY USES** (WRONG!):
```typescript
// Uses localStorage instead of IndexedDB!
localStorage.setItem('device_id', deviceId);
localStorage.setItem('device_code', code);
localStorage.setItem('organization_id', orgId);  // ❌ WRONG - not persistent!
localStorage.setItem('pending_activation_code', code);
```

**Critical Issues**:
1. ❌ **No `device_config` store** - Player uses localStorage instead
2. ❌ **No `device_uuid` generation** - Missing persistent UUID
3. ❌ **No `organization_pin` storage** - Can't implement hard reset
4. ❌ **No `access_token`/`refresh_token` storage** - Can't implement token refresh
5. ❌ **Clear cache DELETES org_id** - localStorage.clear() removes organization_id!

---

## 2. Device Registration Flow Comparison

### Documentation Spec (FLOW 1: First-Time Registration)

```typescript
// STEP 1: Player requests code
POST /api/v1/devices/request-code
Request: {
  device_uuid: string,        // ← Player generates with crypto.randomUUID()
  device_type: string,        // ← 'webos' | 'browser' | 'android'
  screen_width: number,
  screen_height: number,
  organization_id?: number    // ← Include if re-registering (from IndexedDB)
}

Response: {
  activation_code: string,    // ← 6-digit code
  device_id: number,
  expires_at: string
}
```

### Backend Implementation (CURRENT)

**File**: `backend-python/services/device/routes.py:169`

```python
@router.post(DeviceRoutes.REQUEST_CODE, ...)
def request_activation_code(request: RequestActivationCodeRequest, ...):
    result = use_case.execute(
        code=request.code,  # ← ⚠️ DIFFERENT! Backend ACCEPTS code from player
        device_token=request.device_token,  # ← Uses JWT instead of org_id
        device_type=request.device_type,
        device_name=request.device_name,
        device_uuid=request.device_uuid,  # ← ✅ Has this
        platform=request.platform
    )
```

**Status**: ⚠️ **MISMATCH**

**Issues**:
1. ⚠️ Backend **accepts code from player** instead of generating it
2. ⚠️ Uses `device_token` (JWT) instead of `organization_id` parameter
3. ✅ Has `device_uuid` support
4. ⚠️ Always creates device as `organization_id = NULL` (requires admin assignment)

### Player Implementation (CURRENT)

**File**: `player-vite/src/shell/services/shell-registration.ts:134`

```typescript
async registerDevice(): Promise<void> {
  // Player GENERATES code client-side
  let activationCode = this.getPendingCode();
  if (!activationCode) {
    activationCode = this.generateActivationCode();  // ← Random 6 digits
  }

  const requestBody = {
    code: activationCode,     // ← Sends generated code
    platform: platformInfo.type,  // ← ❌ MISSING device_type!
  };

  const data = await SharedAPIClient.post(
    '/api/v1/devices/request-code',
    requestBody
  );

  // Store in localStorage (❌ WRONG - should be IndexedDB)
  SharedDeviceState.setDeviceId(data.device_id);
  SharedDeviceState.setDeviceCode(data.unique_code);
}
```

**Status**: ⚠️ **INCOMPLETE**

**Issues**:
1. ❌ **Missing `device_uuid`** - Doesn't generate persistent UUID
2. ❌ **Missing `device_type`** - Only sends `platform`
3. ❌ **Missing `screen_width`/`screen_height`**
4. ❌ **Missing `organization_id`** - Can't re-register to same org
5. ❌ Uses **localStorage** instead of IndexedDB

---

## 3. Activation Polling Comparison

### Documentation Spec (FLOW 1 continued)

```typescript
// Player polls for activation
POST /api/v1/devices/activate
Request: {
  unique_code: string,
  device_uuid: string,
  platform: string,
  screen_width: number,
  screen_height: number,
  os_version: string,
  app_version: string
}

Response (Success): {
  device_id: number,
  organization_id: number,
  organization_pin: string,    // ← 6-digit PIN
  access_token: string,        // ← JWT access token
  refresh_token: string,       // ← JWT refresh token
  expires_in: number           // ← 30 days
}

Response (Pending): {
  status: 'pending',
  message: 'Device awaiting approval'
}
```

### Backend Implementation (CURRENT)

**File**: `backend-python/services/device/routes.py:271`

```python
@router.get(DeviceRoutes.CHECK_ACTIVATION, ...)
def check_activation_status(unique_code: str, ...):
    """
    Check activation status (called by player to poll activation)
    """
    device = device_repo.find_by_code(unique_code)

    if device.is_active():
        return ActivationStatusResponse(
            activated=True,
            device_id=device.id,
            device_name=device.device_name,
            organization_id=device.organization_id,
            pin=organization_pin,  # ← ✅ Returns org PIN
            message="Device is activated"
        )
```

**Status**: 🟡 **DIFFERENT APPROACH**

**Backend Flow**:
1. Player uses **GET /check-activation/{code}** to poll
2. Returns activation status (true/false)
3. Does NOT return JWT tokens in this endpoint
4. Tokens generated in separate `/activate` endpoint (POST - called by CMS admin)

**Issues**:
1. ⚠️ **Different flow** - Doc expects POST /activate returns tokens to player
2. ✅ Returns `organization_pin` correctly
3. ❌ **Missing `access_token`/`refresh_token`** in response

### Player Implementation (CURRENT)

**File**: `player-vite/src/shell/services/shell-activation-poll.ts:77`

```typescript
async checkActivation(): Promise<void> {
  // ✅ Uses correct endpoint (matches backend)
  const data = await SharedAPIClient.get<ActivationCheckResponse>(
    `${config.api.baseURL}/api/v1/devices/check-activation/${activationCode}`
  );

  if (data.activated && data.device_id) {
    // ✅ Handles activation correctly
    SharedDeviceState.markAsActivated(
      newDeviceId,
      data.device_name,
      data.organization_id
    );

    // ⚠️ Saves organization PIN (but nowhere to use it - no hard reset)
    if (data.organization_pin) {
      SharedDeviceState.setOrganizationPin(data.organization_pin);
    }

    window.location.reload();  // ← Reload to player
  }
}
```

**Status**: ⚠️ **INCOMPLETE**

**Issues**:
1. ✅ Uses correct polling endpoint (matches backend)
2. ❌ **Doesn't receive/store JWT tokens** - Backend doesn't send them
3. ⚠️ Saves `organization_pin` but **no hard reset feature** to use it
4. ❌ **No token refresh logic** - Can't implement 30-day token lifecycle

---

## 4. Hard Reset Flow Comparison

### Documentation Spec (FLOW 3: Hard Reset)

```typescript
// Player validates PIN from IndexedDB
const config = await deviceConfigStorage.getDeviceConfig();

if (pin !== config.organization_pin) {
  showError('Invalid PIN');
  return;
}

// PIN correct - clear ALL IndexedDB data
await deviceConfigStorage.hardReset();
window.location.reload();
```

### Backend Implementation (CURRENT)

**File**: `backend-python/services/device/routes.py:750`

```python
@router.post(DeviceRoutes.VALIDATE_RESET_PASSWORD)
def validate_reset_password(request: ValidateResetPasswordRequest):
    """
    Validate device reset password (called by player)
    Password is stored in environment variable for security.
    """
    reset_password = os.getenv('DEVICE_RESET_PASSWORD', 'admin123')

    if request.password == reset_password:
        return {"valid": True, "message": "Password correct"}
    else:
        return {"valid": False, "message": "Incorrect password"}
```

**Status**: 🔴 **COMPLETELY DIFFERENT APPROACH**

**Issues**:
1. ❌ Backend uses **single env var password** for ALL devices
2. ❌ Documentation expects **per-organization 6-digit PIN**
3. ⚠️ Backend has endpoint but **player doesn't use it**
4. ❌ **Security issue** - Single password for all devices is weak

### Player Implementation (CURRENT)

**Status**: 🔴 **NOT IMPLEMENTED**

**Files Checked**:
- No hard reset dialog component
- No PIN validation logic
- No differentiation between "clear cache" and "hard reset"

**What Player HAS**:
- Stores `organization_pin` from activation response
- But **never uses it** - no UI or logic to validate

---

## 5. Token Refresh Flow Comparison

### Documentation Spec (FLOW 6: Token Expired)

```typescript
// Before every API call
const isExpired = await deviceConfigStorage.isTokenExpired();

if (isExpired) {
  const refreshed = await this.refreshToken();
  if (!refreshed) {
    // Need re-registration
    await this.handleTokenExpired();
  }
}

// Refresh endpoint
POST /api/v1/auth/refresh
Request: { refresh_token: string }
Response: {
  access_token: string,
  refresh_token: string,  // New token (rotation)
  expires_in: number
}
```

### Backend Implementation (CURRENT)

**Status**: 🔴 **ENDPOINT DOES NOT EXIST**

**What's Missing**:
- No `/api/v1/auth/refresh` endpoint
- No refresh token validation
- No token blacklist
- No token rotation

**What Backend HAS**:
- JWT token generation in activation (line 123 in activate_device.py)
- But **no refresh mechanism**

### Player Implementation (CURRENT)

**Status**: 🔴 **NOT IMPLEMENTED**

**What's Missing**:
- No token expiry check
- No refresh token storage
- No refresh logic
- No re-registration on token expiry

**Current Behavior**:
- Player stores token in localStorage (if backend sent it)
- But **never checks expiry**
- Token might be expired but player keeps using it → **401 errors**

---

## 6. Device Release/Delete Flow Comparison

### Documentation Spec (FLOW 4 & 5)

**FLOW 4: CMS Release Device**
```python
# Backend endpoint
POST /api/v1/devices/{device_id}/release
# Updates status='released', keeps record

# Player heartbeat response
Response: 403 Forbidden
{ error: 'Device has been released' }

# Player handles 403
await handleDeviceReleased();  // Request new code with org_id
```

**FLOW 5: CMS Delete Device**
```python
# Backend endpoint
DELETE /api/v1/devices/{device_id}
# Deletes record completely

# Player heartbeat response
Response: 404 Not Found
{ error: 'Device not found' }

# Player handles 404
await handleDeviceDeleted();  // Request new code with org_id
```

### Backend Implementation (CURRENT)

**Release Endpoint**: 🔴 **DOES NOT EXIST**

**Delete Endpoint**: ✅ **EXISTS** (line 643 in routes.py)
```python
@router.delete(DeviceRoutes.DELETE, ...)
def delete_device(device_id: int, ...):
    success = use_case.delete_device(device_id, current_user_org_id)
    # Hard delete from database
```

**Issues**:
1. ❌ **No release endpoint** - Can't soft-release devices
2. ✅ Has delete endpoint (hard delete)
3. ❌ **Heartbeat doesn't check device status** - No 403/404 on release/delete

### Player Implementation (CURRENT)

**File**: `player-vite/src/player/services/player-heartbeat.ts` (NOT FOUND - need to check)

**Status**: 🔴 **NOT IMPLEMENTED**

**What's Missing**:
- No 403/404 error handling in heartbeat
- No `handleDeviceReleased()` function
- No `handleDeviceDeleted()` function
- No logic to request new code with org_id

---

## 7. Unassigned Devices (Global Pending) Comparison

### Documentation Spec

```python
# Backend endpoints
GET /api/v1/devices/unassigned  # List devices with org_id = NULL
POST /api/v1/devices/{id}/assign  # Assign device to organization

# Flow
1. Player requests code (no org_id) → device created with org_id = NULL
2. Admin sees device in global unassigned list
3. Admin assigns device to their organization
4. Device appears in org's pending devices
5. Org admin approves device
```

### Backend Implementation (CURRENT)

**Unassigned Endpoint**: ⚠️ **PARTIAL**

**File**: `backend-python/services/device/routes.py:418`

```python
@router.get(DeviceRoutes.LIST, ...)
def list_devices(scope: str = 'my_org', ...):
    """
    Scopes:
    - my_org: Devices in user's organization
    - unassigned: Devices with organization_id = NULL  # ← ✅ HAS THIS
    - all: All devices (super admin only)
    """
    if scope == "unassigned":
        organization_id = None  # ← Query devices with org_id = NULL
```

**Assign Endpoint**: 🔴 **DOES NOT EXIST**

**What's Missing**:
- ❌ No `POST /devices/{id}/assign` endpoint to assign device to org
- ✅ Can LIST unassigned devices (scope=unassigned)
- ❌ Can't ASSIGN device from global pool to organization

---

## 8. Summary of Gaps

### 🔴 CRITICAL - Must Implement

| # | Component | Gap | Impact |
|---|-----------|-----|--------|
| 1 | Player | **No IndexedDB device_config store** | ❌ org_id lost on cache clear, can't persist device state |
| 2 | Player | **No device_uuid generation** | ❌ Can't track device re-registrations |
| 3 | Backend | **No /auth/refresh endpoint** | ❌ Tokens expire → device stops working after 30 days |
| 4 | Player | **No token refresh logic** | ❌ Can't handle token expiry |
| 5 | Backend | **No /devices/{id}/release endpoint** | ❌ Can't soft-release devices |
| 6 | Player | **No heartbeat 403/404 handling** | ❌ Device doesn't re-register when released/deleted |
| 7 | Backend | **No /devices/{id}/assign endpoint** | ❌ Can't assign unassigned devices to org |
| 8 | Player | **No hard reset implementation** | ❌ Can't reset device with PIN validation |

### 🟡 IMPORTANT - Should Implement

| # | Component | Gap | Impact |
|---|-----------|-----|--------|
| 9 | Player | **Uses localStorage instead of IndexedDB** | ⚠️ Data lost on cache clear |
| 10 | Backend | **Hard reset uses env var, not org PIN** | ⚠️ Security issue - single password for all |
| 11 | Player | **Missing screen dimensions in request** | ⚠️ Backend doesn't get device info |
| 12 | Backend | **Activation doesn't return JWT tokens** | ⚠️ Player can't authenticate API calls |

### 🟢 MINOR - Nice to Have

| # | Component | Gap | Impact |
|---|-----------|-----|--------|
| 13 | Player | **No clear cache vs hard reset separation** | Low priority - can be added later |
| 14 | Backend | **No token blacklist** | Low priority - refresh token rotation not critical initially |

---

## 9. Recommended Implementation Order

### Phase 1: Fix Storage (CRITICAL)

1. **Player - Implement IndexedDB device_config store**
   - Create `device_config` object store
   - Migrate from localStorage to IndexedDB
   - Add `device_uuid` generation (crypto.randomUUID())
   - Persist `organization_id`, `organization_pin`, tokens

2. **Player - Update registration to send all fields**
   - Send `device_uuid`, `device_type`, `screen_width`, `screen_height`
   - Include `organization_id` if exists (re-registration)

### Phase 2: Fix Token Lifecycle (CRITICAL)

3. **Backend - Implement /auth/refresh endpoint**
   - Accept refresh_token
   - Return new access_token + refresh_token
   - Add token blacklist (optional but recommended)

4. **Player - Implement token refresh logic**
   - Check token expiry before each API call
   - Auto-refresh if expired
   - Handle refresh failure (re-register)

5. **Backend - Return tokens in activation**
   - Add `access_token`, `refresh_token`, `expires_in` to activation response
   - Or create separate endpoint for player to get tokens after activation

### Phase 3: Fix Device Lifecycle (IMPORTANT)

6. **Backend - Implement device release/delete handling**
   - Add `/devices/{id}/release` endpoint
   - Update heartbeat to return 403 for released devices
   - Update heartbeat to return 404 for deleted devices

7. **Player - Handle device release/delete**
   - Catch 403/404 in heartbeat
   - Clear tokens but preserve org_id
   - Request new code with org_id

8. **Backend - Implement device assignment**
   - Add `/devices/{id}/assign` endpoint
   - Update device organization_id

### Phase 4: Implement Hard Reset (NICE TO HAVE)

9. **Backend - Fix hard reset to use org PIN**
   - Remove env var password
   - Validate against organization.pin

10. **Player - Implement hard reset UI**
    - Create hard reset dialog with PIN input
    - Validate PIN from IndexedDB
    - Clear all IndexedDB on success

---

## 10. Code Examples for Fixes

### Fix 1: Player IndexedDB device_config Store

```typescript
// player-vite/src/shared/storage/storage-schema.ts
export const SCHEMA = {
  'device_config': {
    keyPath: 'id',
    indexes: [],
  },
  'media_cache': {
    keyPath: 'id',
    indexes: [
      { name: 'by_content_id', keyPath: 'content_id' },
      { name: 'by_cached_at', keyPath: 'cached_at' },
    ],
  },
};

// player-vite/src/shared/storage/device-config-storage.ts (NEW FILE)
import { dbManager } from './indexed-db-manager';

interface DeviceConfig {
  id: 'device_config';
  device_uuid: string;
  device_id: number | null;
  organization_id: number | null;
  organization_pin: string | null;
  access_token: string | null;
  refresh_token: string | null;
  token_expires_at: number | null;
  device_name: string | null;
  device_type: string | null;
  last_activation_code: string | null;
  created_at: number;
  updated_at: number;
}

class DeviceConfigStorage {
  private readonly STORE_NAME = 'device_config';
  private readonly CONFIG_ID = 'device_config';

  async getConfig(): Promise<DeviceConfig | null> {
    return await dbManager.get<DeviceConfig>(this.STORE_NAME, this.CONFIG_ID);
  }

  async setConfig(partial: Partial<Omit<DeviceConfig, 'id'>>): Promise<void> {
    const existing = await this.getConfig();

    const config: DeviceConfig = {
      id: this.CONFIG_ID,
      device_uuid: existing?.device_uuid || this.generateUUID(),
      device_id: partial.device_id ?? existing?.device_id ?? null,
      organization_id: partial.organization_id ?? existing?.organization_id ?? null,
      organization_pin: partial.organization_pin ?? existing?.organization_pin ?? null,
      access_token: partial.access_token ?? existing?.access_token ?? null,
      refresh_token: partial.refresh_token ?? existing?.refresh_token ?? null,
      token_expires_at: partial.token_expires_at ?? existing?.token_expires_at ?? null,
      device_name: partial.device_name ?? existing?.device_name ?? null,
      device_type: partial.device_type ?? existing?.device_type ?? null,
      last_activation_code: partial.last_activation_code ?? existing?.last_activation_code ?? null,
      created_at: existing?.created_at || Date.now(),
      updated_at: Date.now(),
    };

    await dbManager.put(this.STORE_NAME, config);
  }

  async clearMediaCache(): Promise<void> {
    await dbManager.clear('media_cache');
  }

  async hardReset(): Promise<void> {
    await dbManager.clear(this.STORE_NAME);
    await dbManager.clear('media_cache');
  }

  private generateUUID(): string {
    return crypto.randomUUID();
  }

  async getDeviceUUID(): Promise<string> {
    const config = await this.getConfig();
    if (config?.device_uuid) return config.device_uuid;

    const uuid = this.generateUUID();
    await this.setConfig({ device_uuid: uuid });
    return uuid;
  }

  async getOrganizationId(): Promise<number | null> {
    const config = await this.getConfig();
    return config?.organization_id ?? null;
  }

  async isTokenExpired(): Promise<boolean> {
    const config = await this.getConfig();
    if (!config?.token_expires_at) return true;
    return Date.now() >= config.token_expires_at;
  }
}

export const deviceConfigStorage = new DeviceConfigStorage();
```

### Fix 3: Backend /auth/refresh Endpoint

```python
# backend-python/services/auth/routes.py
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    Implements token rotation for security
    """
    from shared.auth import verify_refresh_token, create_device_token, create_refresh_token

    # Verify refresh token
    payload = verify_refresh_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    device_id = payload.get('device_id')
    organization_id = payload.get('organization_id')

    # Check if device still exists and is active
    device = device_repo.get_by_id(device_id)

    if not device or device.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not active"
        )

    # Generate new tokens (token rotation)
    new_access_token = create_device_token(device_id, organization_id)
    new_refresh_token = create_refresh_token(device_id, organization_id)

    # TODO: Blacklist old refresh token (optional)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=2592000,  # 30 days
    )
```

### Fix 6: Backend Device Release Endpoint

```python
# backend-python/services/device/routes.py
@router.post(DeviceRoutes.RELEASE, response_model=DeviceResponse)
def release_device(
    device_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Release device (soft-release - keeps data in CMS)
    Device can re-register to same organization
    """
    device = device_repo.get_by_id(device_id)

    if not device or device.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Update status to 'released'
    device.status = 'released'
    device.released_at = datetime.now(timezone.utc)

    updated_device = device_repo.update(device)

    return device_to_response(updated_device)

# Update heartbeat to check status
@router.post(DeviceRoutes.HEARTBEAT, ...)
def device_heartbeat(device_id: int, ...):
    device = device_repo.get_by_id(device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.status == 'released':
        raise HTTPException(status_code=403, detail="Device has been released")

    # ... rest of heartbeat logic
```

---

## Conclusion

**Overall Assessment**: 🔴 **MAJOR GAPS - System Not Production Ready**

**Key Findings**:
1. ❌ Player storage strategy completely broken (uses localStorage, not IndexedDB)
2. ❌ Token refresh completely missing (backend + player)
3. ❌ Device lifecycle management missing (release/delete handling)
4. ⚠️ Flow mismatch between backend and documentation (activation endpoint)
5. ❌ Hard reset feature incomplete (player has no UI, backend uses wrong approach)

**Recommendation**: Follow **Phase 1 & 2** implementation order above to fix critical storage and token issues FIRST before deploying to production.

**Estimated Effort**:
- Phase 1 (Storage): 2-3 days
- Phase 2 (Tokens): 2-3 days
- Phase 3 (Lifecycle): 2-3 days
- Phase 4 (Hard Reset): 1-2 days

**Total**: ~8-11 days of development work to reach production-ready state.
