# State Unification Phase 2 - Refactoring Plan

## 📋 Overview

**Goal**: Centralize device-related localStorage calls in bootstrap/activation logic
**Scope**: Focus on critical device data (device_id, device_status, device_code, organization_id, device_token)
**Approach**: Extend SharedDeviceState with device data helpers

---

## 🎯 Current State Analysis

### localStorage Usage Breakdown (100 total calls)

| Category | Count | Files | Status |
|----------|-------|-------|--------|
| **Device Bootstrap** | ~38 | init.js, activation-poll.js, registration.js | 🎯 **TARGET FOR PHASE 2** |
| **Device Model Internal** | ~8 | Device.js | ✅ Already encapsulated |
| **Preferences** | 0 | - | ✅ Phase 1 complete |
| **Sync/Commands** | ~20 | heartbeat.js, commands/ | 🟡 Keep as-is (isolated) |
| **Debug Flags** | ~10 | api-client.js, logger.js | 🟡 Keep as-is (developer tools) |
| **Cache/Other** | ~24 | Various | 🟡 Keep as-is (isolated) |

### Key Files for Phase 2

1. **js/activation/init.js** (11 calls)
   - Bootstrap device check
   - Backend verification
   - Selective localStorage clearing (preserve token)

2. **js/activation/services/activation-poll.js** (18 calls)
   - Activation status polling
   - Complex state transitions
   - Token preservation logic

3. **js/activation/services/registration.js** (9 calls)
   - Device registration flow
   - Token handling

---

## 🔧 Refactoring Strategy

### 1. Extend SharedDeviceState API

Add dedicated methods for device core data:

```javascript
// DEVICE CORE DATA (read-only, atomic operations)
SharedDeviceState.getDeviceId()
SharedDeviceState.getDeviceStatus()
SharedDeviceState.getDeviceCode()
SharedDeviceState.getOrganizationId()
SharedDeviceState.getDeviceToken()

// DEVICE CORE DATA (write operations with validation)
SharedDeviceState.setDeviceId(id)
SharedDeviceState.setDeviceStatus(status)  // validates: 'pending', 'active', 'inactive'
SharedDeviceState.setDeviceCode(code)
SharedDeviceState.setOrganizationId(orgId)
SharedDeviceState.setDeviceToken(token)

// ATOMIC OPERATIONS (prevent race conditions)
SharedDeviceState.markAsActivated(deviceId, deviceName, orgId)
SharedDeviceState.clearDeviceData({ preserveAuth: true })

// VERIFICATION
SharedDeviceState.hasDeviceId()
SharedDeviceState.isActivated()
```

### 2. Migration Pattern

**Before (scattered)**:
```javascript
const savedDeviceId = localStorage.getItem('device_id');
const savedStatus = localStorage.getItem('device_status');
const savedCode = localStorage.getItem('device_code');

if (savedDeviceId) {
    // ... logic
}
```

**After (centralized)**:
```javascript
const savedDeviceId = SharedDeviceState.getDeviceId();
const savedStatus = SharedDeviceState.getDeviceStatus();
const savedCode = SharedDeviceState.getDeviceCode();

if (SharedDeviceState.hasDeviceId()) {
    // ... logic
}
```

**Critical Operation (token preservation)**:
```javascript
// BEFORE (manual, error-prone)
const preservedToken = localStorage.getItem('device_token');
const preservedOrgId = localStorage.getItem('organization_id');

['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
    localStorage.removeItem(key);
});

if (preservedToken) localStorage.setItem('device_token', preservedToken);
if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

// AFTER (atomic, safe)
SharedDeviceState.clearDeviceData({ preserveAuth: true });
```

---

## 📊 Benefits

### 1. Safety
- ✅ Atomic operations prevent race conditions
- ✅ Token preservation can't be forgotten
- ✅ Validation on status changes

### 2. Maintainability
- ✅ Single place to modify device storage logic
- ✅ Self-documenting code (method names explain intent)
- ✅ Easier to add encryption, sync, or migration later

### 3. Testing
- ✅ Mock SharedDeviceState instead of localStorage
- ✅ Can inject test state easily
- ✅ Verify state transitions programmatically

### 4. Debugging
- ✅ Centralized logging of all device state changes
- ✅ Can add debug mode to trace state mutations
- ✅ Easier to reproduce issues

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Bootstrap Flow
**Mitigation**:
- Incremental changes (one file at a time)
- Test after each file
- Keep backward compatibility during transition

### Risk 2: Token Loss on Error
**Mitigation**:
- `clearDeviceData()` uses atomic preserve-and-restore
- Extensive logging at each step
- Test token preservation scenarios

### Risk 3: Regression in Activation
**Mitigation**:
- Test all activation scenarios:
  - Fresh activation
  - Re-activation (code expired)
  - Re-registration (same device, same org)
  - Re-registration (new device, same org)

---

## 📝 Implementation Steps

### Step 1: Extend SharedDeviceState ✅ TO DO
File: `js/activation/state/deviceState.js`

Add methods:
```javascript
// Core device data accessors
getDeviceId() { return localStorage.getItem('device_id'); }
getDeviceStatus() { return localStorage.getItem('device_status'); }
getDeviceCode() { return localStorage.getItem('device_code'); }
getOrganizationId() { return localStorage.getItem('organization_id'); }
getDeviceToken() { return localStorage.getItem('device_token'); }

// Core device data mutators (with logging)
setDeviceId(id) {
    localStorage.setItem('device_id', id);
    SharedLogger.log(`[SharedDeviceState] Device ID set: ${id}`);
}

setDeviceStatus(status) {
    const validStatuses = ['pending', 'active', 'inactive'];
    if (!validStatuses.includes(status)) {
        SharedLogger.error(`[SharedDeviceState] Invalid status: ${status}`);
        return;
    }
    localStorage.setItem('device_status', status);
    SharedLogger.log(`[SharedDeviceState] Device status set: ${status}`);
}

// Atomic operations
markAsActivated(deviceId, deviceName, orgId) {
    this.setDeviceId(deviceId);
    this.setDeviceStatus('active');
    if (deviceName) localStorage.setItem('device_name', deviceName);
    if (orgId) this.setOrganizationId(orgId);
    SharedLogger.log('[SharedDeviceState] Device marked as activated');
}

clearDeviceData({ preserveAuth = false } = {}) {
    const keysToRemove = ['device_id', 'device_code', 'device_name', 'device_status', 'platform'];

    if (preserveAuth) {
        // Preserve auth data
        const preservedToken = this.getDeviceToken();
        const preservedOrgId = this.getOrganizationId();

        // Clear device data
        keysToRemove.forEach(key => localStorage.removeItem(key));

        // Restore auth data
        if (preservedToken) this.setDeviceToken(preservedToken);
        if (preservedOrgId) this.setOrganizationId(preservedOrgId);

        SharedLogger.log('[SharedDeviceState] Device data cleared (auth preserved)');
    } else {
        // Clear everything
        keysToRemove.forEach(key => localStorage.removeItem(key));
        localStorage.removeItem('device_token');
        localStorage.removeItem('organization_id');

        SharedLogger.log('[SharedDeviceState] Device data cleared (including auth)');
    }
}

// Verification helpers
hasDeviceId() { return !!this.getDeviceId(); }
isActivated() { return this.getDeviceStatus() === 'active'; }
```

### Step 2: Refactor init.js ✅ TO DO
File: `js/activation/init.js`

**Changes**:
```javascript
// Line 38-40: Replace direct localStorage access
// BEFORE:
const savedDeviceId = localStorage.getItem('device_id');
const savedStatus = localStorage.getItem('device_status');
const savedCode = localStorage.getItem('device_code');

// AFTER:
const savedDeviceId = SharedDeviceState.getDeviceId();
const savedStatus = SharedDeviceState.getDeviceStatus();
const savedCode = SharedDeviceState.getDeviceCode();

// Line 71-72: Use setter methods
// BEFORE:
localStorage.setItem('device_id', verifyData.device_id);
localStorage.setItem('device_status', 'active');

// AFTER:
SharedDeviceState.markAsActivated(verifyData.device_id, verifyData.device_name);

// Line 80-90: Use atomic clear
// BEFORE:
const preservedToken = localStorage.getItem('device_token');
const preservedOrgId = localStorage.getItem('organization_id');
['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
    localStorage.removeItem(key);
});
if (preservedToken) localStorage.setItem('device_token', preservedToken);
if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

// AFTER:
SharedDeviceState.clearDeviceData({ preserveAuth: true });
```

### Step 3: Refactor activation-poll.js ✅ TO DO
File: `js/activation/services/activation-poll.js`

**Changes**:
```javascript
// Line 20: Use getter
// BEFORE:
const activationCode = localStorage.getItem('device_code') || state.activationCode || state.deviceCode;

// AFTER:
const activationCode = SharedDeviceState.getDeviceCode() || state.activationCode || state.deviceCode;

// Line 103-111: Use atomic clear
// BEFORE: (same manual preservation logic)
// AFTER:
SharedDeviceState.clearDeviceData({ preserveAuth: true });

// Line 177-182: Use atomic activation
// BEFORE:
localStorage.setItem('device_id', newDeviceId);
localStorage.setItem('device_status', 'active');
if (data.organization_id) {
    localStorage.setItem('organization_id', data.organization_id);
}

// AFTER:
SharedDeviceState.markAsActivated(newDeviceId, data.device_name, data.organization_id);
```

### Step 4: Refactor registration.js ✅ TO DO
File: `js/activation/services/registration.js`

Similar pattern - replace direct localStorage access with SharedDeviceState methods.

### Step 5: Test & Verify ✅ TO DO
Test scenarios:
- [ ] Fresh activation (first time)
- [ ] Re-activation after code expiry
- [ ] Page reload during pending state
- [ ] Page reload during active state
- [ ] Token preservation on re-registration
- [ ] Hard reset flow

---

## 📈 Expected Results

| Metric | Before Phase 2 | After Phase 2 | Improvement |
|--------|-----------------|---------------|-------------|
| localStorage calls | 100 | ~60 | 40% reduction |
| Device data calls unified | 0% | 100% | Complete |
| Bootstrap code clarity | Low | High | Much better |
| Token loss risk | Medium | Low | Safer |
| Testability | Hard | Easy | Much easier |

---

## ⏱️ Time Estimate

- Step 1 (Extend SharedDeviceState): 30 minutes
- Step 2 (Refactor init.js): 20 minutes
- Step 3 (Refactor activation-poll.js): 30 minutes
- Step 4 (Refactor registration.js): 20 minutes
- Step 5 (Testing): 30 minutes
- **Total: ~2 hours**

---

## 🎯 Success Criteria

✅ All device data access goes through SharedDeviceState
✅ No direct localStorage access for device core data
✅ Token preservation works reliably
✅ All activation scenarios tested
✅ No regressions in bootstrap flow
✅ Code is cleaner and more maintainable

---

**Status**: 📝 Planning Complete - Ready for Implementation
**Next**: Implement Step 1 (Extend SharedDeviceState)
