# Documentation Update Summary
## DEVICE_FLOW_DOCUMENTATION.md - Version 2.0

**Date**: 2025-01-14
**Updated By**: System
**Reason**: Corrected Hard Reset & Release flows based on user clarification

---

## 🔄 Major Changes

### 1. **Terminology Update**

#### OLD (v1.0):
- Hard Reset = Clear ALL data with organization PIN validation (client-side)
- Release Device = CMS action only

#### NEW (v2.0 - CORRECT):
- **Hard Reset (Factory Reset)** = Password-validated (backend) action that clears ALL IndexedDB + backend sets status='released' → device re-registers to **GLOBAL pending**
- **CMS Release (Soft Release)** = Admin action that sets status='released' + player clears tokens but **KEEPS org_id** → device re-registers to **SAME org pending**
- **Reset Password** = Single password (env var) for ALL devices, validated by backend
- **Organization PIN** = Currently NOT used (reserved for future)

---

### 2. **FLOW 3: Hard Reset - Completely Rewritten**

#### OLD Approach (WRONG):
```typescript
// Client-side PIN validation
if (pin !== config.organization_pin) {
  setError('Invalid PIN');
  return;
}

// Clear all data
await deviceConfigStorage.hardReset();
window.location.reload();
```

#### NEW Approach (CORRECT):
```typescript
// STEP 1: Backend password validation
const validateResponse = await SharedAPIClient.post('/api/v1/devices/validate-reset-password', {
  password: password,
  device_id: config.device_id
});

if (!validateResponse.valid) {
  setError('Invalid password');
  return;
}

// STEP 2: Backend hard reset
await SharedAPIClient.post(`/api/v1/devices/${config.device_id}/hard-reset`, {});

// STEP 3: Clear ALL IndexedDB
await deviceConfigStorage.hardReset();

// STEP 4: Reload (no org_id → global pending)
window.location.reload();
```

**Key Changes**:
1. ✅ Password validated by **BACKEND** (not client-side)
2. ✅ Backend sets `status='released'` for audit trail
3. ✅ Player clears **ALL** IndexedDB data (including org_id)
4. ✅ Device re-registers to **GLOBAL** pending (not same org)

---

### 3. **FLOW 4: CMS Release - Clarified Difference**

Added clear explanation:
- **CMS Release = Soft Release**
- Player clears tokens but **KEEPS org_id**
- Device re-registers to **SAME org** pending

**Code Update**:
```typescript
async handleDeviceReleased() {
  // Clear tokens but KEEP org_id (soft release)
  await deviceConfigStorage.setDeviceConfig({
    access_token: null,
    refresh_token: null,
    token_expires_at: null,
    device_id: null,
  });

  // Clear media cache
  await deviceConfigStorage.clearMediaCache();

  // Request new code (WITH org_id from IndexedDB)
  const activationCode = await this.registrationService.requestActivationCode();

  // Shows: "Re-registering to same organization..."
}
```

---

### 4. **Backend API Specifications - 3 New Endpoints**

#### Endpoint 5: POST /devices/{device_id}/release
- **Purpose**: CMS admin releases device (soft release)
- **Called By**: CMS Admin (with auth)
- **Action**: Sets status='released'
- **Player Response**: Heartbeat gets 403 → clear tokens, keep org_id

#### Endpoint 5b: POST /devices/validate-reset-password (✅ Already Exists)
- **Purpose**: Validate password for hard reset
- **Called By**: Player device
- **Action**: Check password == DEVICE_RESET_PASSWORD env var
- **Response**: {valid: boolean}

#### Endpoint 5c: POST /devices/{device_id}/hard-reset (❌ NEW - Need to Implement)
- **Purpose**: Factory reset device
- **Called By**: Player device (after password validated)
- **Action**: Sets status='released' (same as CMS release)
- **Player Response**: Clear ALL IndexedDB → re-register to global

---

### 5. **Added Comparison Table**

Added comprehensive comparison table:

| Aspect | CMS Release (Soft) | Player Hard Reset (Factory) |
|--------|-------------------|----------------------------|
| **Initiated By** | Admin in CMS | User in Player |
| **Password Required** | ❌ No | ✅ YES (env var) |
| **Backend Endpoint** | /devices/{id}/release | /devices/{id}/hard-reset |
| **Backend Action** | status='released' | status='released' |
| **Player IndexedDB** | Clear tokens, **KEEP org_id** | **Clear EVERYTHING** |
| **Device Appears In** | **SAME org** pending | **GLOBAL** pending |
| **Use Case** | Temporary disable | Move to different org |

---

### 6. **State Transitions - Updated**

Updated transition table to distinguish 2 release types:

| From | To | Trigger | Player Action | Backend Action |
|------|----|---------|--------------|-----------------|
| PLAYING | PENDING | **CMS Release (Soft)** | Clear tokens, **KEEP org_id** | UPDATE status='released' |
| PLAYING | PENDING | **Hard Reset (Factory)** | Clear ALL data (no org_id) | UPDATE status='released' |

---

## 📋 Implementation Checklist

### Backend - Need to Implement:

- [x] **POST /devices/validate-reset-password** - ✅ Already exists (line 750 in routes.py)
- [ ] **POST /devices/{device_id}/release** - ❌ Missing (CMS admin release)
- [ ] **POST /devices/{device_id}/hard-reset** - ❌ Missing (Player factory reset)
- [ ] **Heartbeat return 403** when status='released' - ❌ Missing

### Player - Need to Implement:

- [ ] **IndexedDB device_config store** - ❌ Currently uses localStorage
- [ ] **Hard reset dialog** - ⚠️ Exists but needs backend integration
- [ ] **Heartbeat 403 handler** - ❌ Missing
- [ ] **CMS release handler** - ❌ Missing

---

## 🎯 Key Takeaways

1. **2 Types of Release**:
   - **CMS Release**: Admin action, keep org_id, same org pending
   - **Hard Reset**: User action with password, clear all, global pending

2. **Backend Validation**:
   - Hard reset password validated by **BACKEND** (not client-side)
   - Single password for all devices (env var `DEVICE_RESET_PASSWORD`)

3. **IndexedDB Clearing**:
   - **CMS Release**: Clear tokens only
   - **Hard Reset**: Clear EVERYTHING (including org_id)

4. **Re-registration Target**:
   - **CMS Release**: SAME organization's pending list
   - **Hard Reset**: GLOBAL pending list (unassigned)

5. **Backend Status**:
   - Both set `status='released'` (same database action)
   - Difference is in **player behavior** (what gets cleared)

---

## 📝 Files Updated

1. **DEVICE_FLOW_DOCUMENTATION.md** (Version 1.0 → 2.0)
   - Updated terminology table
   - Rewritten FLOW 3 (Hard Reset)
   - Clarified FLOW 4 (CMS Release)
   - Added 3 backend endpoint specs
   - Added release comparison table
   - Updated state transitions

2. **DOCUMENTATION_UPDATE_SUMMARY.md** (This file)
   - Summary of all changes
   - Implementation checklist
   - Key differences explained

---

## 🔗 Related Documents

- **DEVICE_FLOW_DOCUMENTATION.md** - Main reference (v2.0)
- **FLOW_COMPARISON_ANALYSIS.md** - Gap analysis (backend vs player vs docs)
- **PLAYER_VITE_ANALYSIS.md** - Original player analysis (600+ lines)

---

**Next Steps**: Implement missing backend endpoints and update player to match documentation.
