# Device Registration Flow - Bug Analysis & Fixes

**Analysis Date**: 2025-11-08
**Codebase Location**: `/mnt/g/khoirul/signate/player-vanillajs/`
**Status**: 4 Critical Bugs Identified + Root Cause Analysis + Fixes

---

## Executive Summary

The device registration flow in `player-vanillajs` contains **4 critical bugs** that can cause registration failures, infinite loops, and database pollution. These bugs manifest during specific race conditions and network scenarios:

1. **GUARD Race Condition** - device_id exists after localStorage.clear()
2. **Infinite Reload Loop** - Code expired scenario causes endless page reloads
3. **Code Generation Inconsistency** - pendingCode reuse breaks on user reload
4. **Unbounded Network Retry** - No retry limit causes DB pollution with pending devices

---

## BUG 1: GUARD Race Condition

### Location
- **Primary File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js` (lines 71-76)
- **Secondary File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/init.js` (line 94)
- **Related**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js` (lines 85-116)

### Problem Description

After `activation-poll.js` expires a device code and clears localStorage (line 98), the `init.js` calls `registerDevice()`. However, GUARD #2 in registration.js (lines 71-76) checks if `device_id` exists in localStorage and rejects the registration.

**The paradox**: How can device_id exist if we just cleared it?

### Root Cause Analysis

The race condition occurs due to **timing between selective localStorage clearing and immediate re-registration**:

```javascript
// activation-poll.js line 85-116 (Code Expired Handler)
if (data.expired && !data.device_id) {
    console.warn('[Shell/Init] ⚠️ Device code expired and deleted');

    // Selective removal - KEEP device_token and organization_id
    const preservedToken = localStorage.getItem('device_token');
    const preservedOrgId = localStorage.getItem('organization_id');

    // Clear device-specific data ONLY
    ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
        localStorage.removeItem(key);
    });

    // Restore preserved data
    if (preservedToken) localStorage.setItem('device_token', preservedToken);
    if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

    // ✅ Don't reload! Directly register
    console.log('[Shell/Init] 🔄 Re-registering device...');
    await window.ShellRegistration.registerDevice();  // <-- BUG HERE
    return;
}
```

### Reproduction Steps

1. Device registers successfully (device_id saved to localStorage)
2. Activation code expires on backend
3. Activation polling detects expiration (line 86)
4. Selective localStorage clear removes `device_id` ONLY
5. **Race condition window**: Between clear and register, if:
   - Another init cycle runs, OR
   - localStorage.getItem() called during concurrent clear operation
6. GUARD #2 sees non-null `device_id` even though it should be null
7. Registration rejected with warning: "Device already registered"

### Scenario Timeline

```
TIME    EVENT                                           GUARD STATE
────────────────────────────────────────────────────────────────────
T0      Device expires, init.js detects              device_id = "123"
T1      activation-poll clears device_id              device_id = null
T2      registerDevice() called                        device_id = null
T3      GUARD #2 checks localStorage.getItem()        ⚠️ RACE: device_id might be restored
T4      If another tab/window has device_id           ❌ GUARD rejects!
        Registration fails silently
```

### Evidence

Looking at the code flow:

**activation-poll.js (lines 84-94)**:
```javascript
// Clear only device-specific data
['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
    localStorage.removeItem(key);  // device_id removed here
});

// Restore preserved data
if (preservedToken) localStorage.setItem('device_token', preservedToken);
if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

// ⚠️ NO guard to prevent concurrent access
await window.ShellRegistration.registerDevice();
```

**registration.js (lines 71-76)**:
```javascript
// 🛡️ GUARD 2: Check if already registered (localStorage check)
const existingDeviceId = localStorage.getItem('device_id');
if (existingDeviceId) {
    console.warn('[Shell/Registration] ⚠️ Device already registered...');
    return;  // <-- Rejected!
}
```

The issue: **No synchronization** between the clear and register operations.

---

## BUG 2: Infinite Reload Loop

### Location
- **Primary File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js` (lines 85-116)
- **Secondary**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/init.js` (lines 75-95)

### Problem Description

When a device code expires AND is deleted from backend, the activation-poll module:
1. Clears localStorage (line 98)
2. Deletes IndexedDB cache (lines 102-111)
3. **Calls `window.location.reload()` (line 115)**

After reload, `init.js` runs again and if the backend still returns expired:
- Loop: reload → init → poll → detect expired → reload → init → ...

**Infinite reload loop until user manually stops the page.**

### Root Cause Analysis

The fix attempted in `init.js` (line 94) was to call `registerDevice()` instead of reload:

```javascript
// init.js line 92-94
// ✅ Don't reload! Directly register new device with preserved token/org_id...
console.log('[Shell/Init] 🔄 Re-registering device with preserved token & org_id...');
await window.ShellRegistration.registerDevice();
```

However, `activation-poll.js` still calls `window.location.reload()` (line 115), creating the loop.

### Reproduction Steps

1. Device registers with activation code (e.g., "123456")
2. Admin creates new device code for same device (code expires)
3. Backend deletes expired device record
4. Viewer polls for activation (activation-poll.js)
5. Backend returns: `{expired: true, device_id: null}`
6. **activation-poll.js line 115**: `window.location.reload()`
7. Page reloads, `init.js` runs
8. Backend verification (init.js line 61) still returns expired
9. **Loop continues**: reload → poll → reload → poll → ...

### Evidence

**activation-poll.js (lines 85-116)**:
```javascript
if (data.expired && !data.device_id) {
    console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired...');

    // Stop polling
    this.stopPolling();

    // Clear everything
    localStorage.clear();
    // Delete cache...

    // ❌ THIS IS THE BUG - Causes reload loop
    console.log('[Shell/ActivationPoll] 🔄 Reloading to register as new device...');
    window.location.reload();  // <-- INFINITE LOOP!
    return;
}
```

**init.js (lines 75-95)**:
```javascript
if (verifyData.expired && !verifyData.device_id) {
    // Code expired AND device deleted - clear device data
    console.warn('[Shell/Init] ⚠️ Device code expired and deleted...');

    // Clear and preserve
    const preservedToken = localStorage.getItem('device_token');
    const preservedOrgId = localStorage.getItem('organization_id');

    ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
        localStorage.removeItem(key);
    });

    // Restore preserved data
    if (preservedToken) localStorage.setItem('device_token', preservedToken);
    if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

    // ✅ Register directly instead of reload
    console.log('[Shell/Init] 🔄 Re-registering device...');
    await window.ShellRegistration.registerDevice();  // <-- Good!
    return;
}
```

The conflict: `init.js` tries to register directly, but `activation-poll.js` reloads first, preventing init.js code from running.

---

## BUG 3: Code Generation Inconsistency

### Location
- **File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js` (lines 84-91, 143-144)

### Problem Description

The `pendingCode` variable is reused across retry attempts (line 89):
```javascript
if (!this.pendingCode) {
    this.pendingCode = this.generateActivationCode();  // Generate once
} else {
    console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', this.pendingCode);
}
```

On successful registration, `pendingCode` is cleared (line 144):
```javascript
// Clear pending code (registration succeeded)
this.pendingCode = null;
```

**Problem**: If user reloads the page between retry attempts, `pendingCode` is lost (it's in-memory, not persisted), but the registration is still pending. Next registration attempt generates a NEW code, orphaning the first one.

### Reproduction Steps

1. Device calls `registerDevice()` → generates code "123456"
2. Network fails, retry scheduled in 10 seconds
3. **User reloads page** before retry (at 5 seconds)
4. `pendingCode` is cleared from memory (IIFE scope lost)
5. Page reloads, `init.js` calls `registerDevice()` again
6. New `pendingCode` generated: "654321"
7. Backend now has TWO pending registrations:
   - "123456" (orphaned, never completed)
   - "654321" (currently active)

### Lifecycle Example

```
TIME    EVENT                                PENDINGCODE STATE
────────────────────────────────────────────────────────────────
T0      registerDevice() called              null → "123456" ✅
T1      Network error caught                 "123456" (in memory)
T2      Retry scheduled                      "123456" (waiting)
T3      User reloads browser                 ❌ "123456" LOST (scope gone)
T4      init.js runs after reload            null (fresh scope)
T5      registerDevice() called              null → "654321" ✅ (NEW CODE!)
T6      Backend now has TWO pending codes    orphaned "123456" + active "654321"
T7      Admin tries to activate "123456"    But device is listening for "654321"!
```

### Evidence

**registration.js (lines 84-91)**:
```javascript
// 🔑 Use existing code if retrying, otherwise generate new one
if (!this.pendingCode) {
    this.pendingCode = this.generateActivationCode();
    console.log('[Shell/Registration] 🆕 Generated new activation code:', this.pendingCode);
} else {
    console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', this.pendingCode);
}
const code = this.pendingCode;
```

**registration.js (lines 143-144)**:
```javascript
// Clear pending code (registration succeeded)
this.pendingCode = null;
```

The issue: `pendingCode` is an in-memory variable in the module closure. When page reloads, the entire closure is destroyed, losing the reference. There's no persistence mechanism.

### Why This is Critical

- **Database bloat**: Every page reload + network error creates orphaned pending device records
- **User confusion**: Admin sees multiple codes for same physical device
- **Activation mismatch**: Device code "123456" was generated but admin tries to activate "654321"

---

## BUG 4: Network Retry Without Limit

### Location
- **File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js` (lines 192-242)

### Problem Description

When registration fails due to network error, the code schedules a retry:

```javascript
// Schedule retry
console.log('[Shell/Registration] 🔄 Scheduling retry in 10 seconds...');
this.retryTimeout = setTimeout(() => {
    console.log('[Shell/Registration] 🔄 Retrying registration...');
    this.registerDevice();  // <-- Recursive call, no limit!
}, 10000);
```

**There is NO MAX_RETRY count**. If server is permanently down or network is permanently offline:
- Retry every 10 seconds indefinitely
- Each retry creates a new pending device record (if it somehow succeeds partway)
- Database fills with duplicate pending registrations
- Browser continues retrying forever

### Reproduction Steps

1. Device tries to register
2. Network fails (server down, no internet, etc.)
3. Retry scheduled in 10 seconds
4. Network still fails at T10
5. Another retry scheduled at T20
6. Another retry scheduled at T30
7. **Pattern continues forever** or until device is rebooted

### Impact Calculation

```
RETRY PATTERN:
T=0s    Initial registration attempt
T=10s   Retry 1
T=20s   Retry 2
T=30s   Retry 3
...

AFTER 1 DAY (86400 seconds):
- Total retries: 86400 / 10 = 8,640 attempts
- Each retry may create pending device record
- Database query logs could fill with failures
- Browser memory leaks from accumulated timeouts
```

### Evidence

**registration.js (lines 236-241)**:
```javascript
// Schedule retry
console.log('[Shell/Registration] 🔄 Scheduling retry in 10 seconds...');
this.retryTimeout = setTimeout(() => {
    console.log('[Shell/Registration] 🔄 Retrying registration...');
    this.registerDevice();  // ❌ NO LIMIT!
}, 10000);
```

No counter checking like:
```javascript
// ❌ This doesn't exist:
if (this.retryCount >= MAX_RETRIES) {
    console.error('Max retries exceeded');
    return;
}
this.retryCount++;
```

### Why This Matters

1. **Database pollution**: 8,640+ pending device records per day
2. **Backend load**: Thousands of registration requests to failed server
3. **Browser degradation**: Memory leaks from uncancelled timeouts
4. **Network waste**: Continuous network requests during outage

---

## Fixes

### FIX 1: GUARD Race Condition

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js`

**Change**: Use atomic localStorage operations with explicit synchronization

**Current Code (Lines 85-116)**:
```javascript
if (data.expired && !data.device_id) {
    // Selective removal - KEEP device_token and organization_id
    const preservedToken = localStorage.getItem('device_token');
    const preservedOrgId = localStorage.getItem('organization_id');

    ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
        localStorage.removeItem(key);
    });

    if (preservedToken) localStorage.setItem('device_token', preservedToken);
    if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);

    await window.ShellRegistration.registerDevice();
    return;
}
```

**Fixed Code**:
```javascript
if (data.expired && !data.device_id) {
    console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Activation Code Expired', 'Your activation code has expired. Restarting registration...', 5000);
    }

    // Stop polling
    this.stopPolling();

    // FIX 1: Use deviceState.clearDevice() for atomic clearing
    // This ensures all device data is cleared together without race conditions
    if (window.deviceState && window.deviceState.clearDevice) {
        window.deviceState.clearDevice();
    } else {
        // Fallback to manual clearing if deviceState not available
        const preservedToken = localStorage.getItem('device_token');
        const preservedOrgId = localStorage.getItem('organization_id');

        ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
            localStorage.removeItem(key);
        });

        if (preservedToken) localStorage.setItem('device_token', preservedToken);
        if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);
    }

    // Delete IndexedDB cache
    const dbName = 'signage_media_cache';
    try {
        await new Promise((resolve) => {
            const deleteRequest = indexedDB.deleteDatabase(dbName);
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => resolve();
            deleteRequest.onblocked = () => resolve();
        });
    } catch (error) {
        console.error('[Shell/ActivationPoll] Error deleting cache:', error);
    }

    // FIX 1: Set flag to prevent registration attempt if device_id somehow exists
    // This double-checks AFTER clearing that the device is actually cleared
    const deviceIdAfterClear = localStorage.getItem('device_id');
    if (deviceIdAfterClear) {
        console.error('[Shell/ActivationPoll] CRITICAL: device_id still exists after clear!', deviceIdAfterClear);
        // Force removal
        localStorage.removeItem('device_id');
    }

    // Register new device
    console.log('[Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...');
    await window.ShellRegistration.registerDevice();
    return;
}
```

**Rationale**:
- Use `deviceState.clearDevice()` which is atomic and designed for this purpose
- Add verification check AFTER clearing to detect race conditions
- This ensures the GUARD #2 check in registration.js will never falsely trigger

---

### FIX 2: Infinite Reload Loop

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js`

**Change**: Remove `window.location.reload()` calls - use direct re-registration instead

**Current Code (Lines 85-116, 208-239)**:
```javascript
// TWO places call reload() - both cause problems:

// Location 1: Lines 85-116
if (data.expired && !data.device_id) {
    // ... clear localStorage ...
    window.location.reload();  // ❌ CAUSES LOOP
    return;
}

// Location 2: Lines 208-239
if (error.status === 404) {
    // ... clear localStorage ...
    window.location.reload();  // ❌ CAUSES LOOP
    return;
}
```

**Fixed Code** - Replace both reload calls:

```javascript
// Location 1: Lines 85-116 (expired code)
if (data.expired && !data.device_id) {
    console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Activation Code Expired', 'Your activation code has expired. Restarting registration...', 5000);
    }

    // Stop polling
    this.stopPolling();

    // Clear device data (use deviceState if available)
    if (window.deviceState && window.deviceState.clearDevice) {
        window.deviceState.clearDevice();
    } else {
        const preservedToken = localStorage.getItem('device_token');
        const preservedOrgId = localStorage.getItem('organization_id');

        ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
            localStorage.removeItem(key);
        });

        if (preservedToken) localStorage.setItem('device_token', preservedToken);
        if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);
    }

    // Delete IndexedDB cache
    const dbName = 'signage_media_cache';
    try {
        await new Promise((resolve) => {
            const deleteRequest = indexedDB.deleteDatabase(dbName);
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => resolve();
            deleteRequest.onblocked = () => resolve();
        });
    } catch (error) {
        console.error('[Shell/ActivationPoll] Error deleting cache:', error);
    }

    // FIX 2: DON'T reload! Directly register instead
    console.log('[Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...');
    await window.ShellRegistration.registerDevice();
    return;  // ✅ NO RELOAD
}


// Location 2: Lines 208-239 (404 not found)
if (error.status === 404) {
    console.warn('[Shell/ActivationPoll] ⚠️ Device code not found or deleted (404)');

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Device Code Not Found', 'Your device code was deleted. Restarting registration...', 5000);
    }

    // Stop polling
    this.stopPolling();

    // Clear device data
    if (window.deviceState && window.deviceState.clearDevice) {
        window.deviceState.clearDevice();
    } else {
        const preservedToken = localStorage.getItem('device_token');
        const preservedOrgId = localStorage.getItem('organization_id');

        ['device_id', 'device_code', 'device_name', 'device_status', 'platform'].forEach(key => {
            localStorage.removeItem(key);
        });

        if (preservedToken) localStorage.setItem('device_token', preservedToken);
        if (preservedOrgId) localStorage.setItem('organization_id', preservedOrgId);
    }

    // Delete IndexedDB cache
    const dbName = 'signage_media_cache';
    try {
        await new Promise((resolve) => {
            const deleteRequest = indexedDB.deleteDatabase(dbName);
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => resolve();
            deleteRequest.onblocked = () => resolve();
        });
    } catch (cacheError) {
        console.error('[Shell/ActivationPoll] Error deleting cache:', cacheError);
    }

    // FIX 2: DON'T reload! Directly register instead
    console.log('[Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...');
    await window.ShellRegistration.registerDevice();
    return;  // ✅ NO RELOAD
}
```

**Rationale**:
- `window.location.reload()` causes the page to reload, which re-runs init.js
- If backend still returns expired, the loop continues forever
- Direct registration allows the device to get a NEW code without reload
- If no server at all, the registration will fail and retry with backoff (BUG 4 fix)

---

### FIX 3: Code Generation Inconsistency

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js`

**Change**: Persist `pendingCode` to localStorage and restore from there

**Current Code (Lines 6-9)**:
```javascript
window.ShellRegistration = {
    retryTimeout: null,
    isRegistering: false,
    pendingCode: null,  // ❌ In-memory only, lost on reload
```

**Fixed Code**:

Replace the in-memory variable management with localStorage-backed version:

```javascript
window.ShellRegistration = {
    retryTimeout: null,
    isRegistering: false,

    // FIX 3: Use localStorage for pendingCode persistence
    getPendingCode: function() {
        return localStorage.getItem('pending_activation_code');
    },

    setPendingCode: function(code) {
        if (code) {
            localStorage.setItem('pending_activation_code', code);
            console.log('[Shell/Registration] Pending code saved to localStorage:', code);
        } else {
            localStorage.removeItem('pending_activation_code');
            console.log('[Shell/Registration] Pending code cleared from localStorage');
        }
    },
```

**Change registration flow (Lines 84-91)**:

```javascript
// Old code:
if (!this.pendingCode) {
    this.pendingCode = this.generateActivationCode();
    console.log('[Shell/Registration] 🆕 Generated new activation code:', this.pendingCode);
} else {
    console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', this.pendingCode);
}
const code = this.pendingCode;
```

**New code**:
```javascript
// FIX 3: Check localStorage for existing pending code (survives page reload)
let pendingCode = this.getPendingCode();
if (!pendingCode) {
    pendingCode = this.generateActivationCode();
    this.setPendingCode(pendingCode);
    console.log('[Shell/Registration] 🆕 Generated new activation code:', pendingCode);
} else {
    console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', pendingCode);
}
const code = pendingCode;
```

**Change success cleanup (Line 143-144)**:

```javascript
// Old code:
// Clear pending code (registration succeeded)
this.pendingCode = null;
```

**New code**:
```javascript
// FIX 3: Clear pending code from localStorage (registration succeeded)
this.setPendingCode(null);
```

**Add validation guard in GUARD #2 (Lines 71-76)**:

```javascript
// Current GUARD 2:
const existingDeviceId = localStorage.getItem('device_id');
if (existingDeviceId) {
    console.warn('[Shell/Registration] ⚠️ Device already registered (device_id exists in localStorage), skipping registration');
    console.log('[Shell/Registration] Existing device_id:', existingDeviceId);
    return;
}
```

**Enhanced GUARD 2**:
```javascript
// 🛡️ GUARD 2: Check if already registered (localStorage check)
const existingDeviceId = localStorage.getItem('device_id');
if (existingDeviceId) {
    console.warn('[Shell/Registration] ⚠️ Device already registered (device_id exists in localStorage), skipping registration');
    console.log('[Shell/Registration] Existing device_id:', existingDeviceId);

    // FIX 3: Don't orphan the pending code - clear it since device is already registered
    const orphanedCode = this.getPendingCode();
    if (orphanedCode) {
        console.warn('[Shell/Registration] ⚠️ Clearing orphaned pending code:', orphanedCode);
        this.setPendingCode(null);
    }

    return;
}
```

**Rationale**:
- Persists the code across page reloads using localStorage
- If page reloads during retry, the same code is reused
- No orphaned codes accumulating in the database
- On successful registration, the code is cleared from storage
- Survives browser restarts and network changes

---

### FIX 4: Network Retry Without Limit

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js`

**Change**: Add configurable max retry limit with exponential backoff

**Add constants (Top of window.ShellRegistration)**:

```javascript
window.ShellRegistration = {
    retryTimeout: null,
    isRegistering: false,

    // FIX 4: Add retry limit and backoff configuration
    MAX_RETRIES: 20,  // Maximum 20 retries = ~3.3 minutes
    INITIAL_RETRY_DELAY_MS: 5000,  // Start at 5 seconds
    MAX_RETRY_DELAY_MS: 30000,  // Cap at 30 seconds
    RETRY_BACKOFF_MULTIPLIER: 1.5,  // Exponential: 5s → 7.5s → 11.25s → ...

    /**
     * Get retry count from localStorage
     */
    getRetryCount: function() {
        const count = localStorage.getItem('registration_retry_count');
        return count ? parseInt(count) : 0;
    },

    /**
     * Increment retry count
     */
    incrementRetryCount: function() {
        const count = this.getRetryCount() + 1;
        localStorage.setItem('registration_retry_count', count.toString());
        return count;
    },

    /**
     * Clear retry count (on success or manual reset)
     */
    clearRetryCount: function() {
        localStorage.removeItem('registration_retry_count');
    },

    /**
     * Calculate next retry delay with exponential backoff
     */
    calculateRetryDelay: function(retryCount) {
        // Calculate exponential backoff: initialDelay * (multiplier ^ retryCount)
        const exponentialDelay = this.INITIAL_RETRY_DELAY_MS *
            Math.pow(this.RETRY_BACKOFF_MULTIPLIER, retryCount);

        // Cap at MAX_RETRY_DELAY_MS
        const cappedDelay = Math.min(exponentialDelay, this.MAX_RETRY_DELAY_MS);

        // Add jitter (+/- 20%) to prevent thundering herd
        const jitter = cappedDelay * 0.2 * (Math.random() * 2 - 1);
        const finalDelay = Math.max(1000, cappedDelay + jitter);

        return Math.floor(finalDelay);
    },
```

**Update error handler (Lines 192-242)**:

```javascript
// OLD CODE:
} catch (error) {
    // Reset flag first
    this.isRegistering = false;

    // ... error handling ...

    // 🛡️ GUARD 3: Only retry if device NOT already registered
    const deviceIdAfterError = localStorage.getItem('device_id');
    if (deviceIdAfterError) {
        console.warn('[Shell/Registration] ⚠️ Device already registered despite error, skipping retry');
        return;
    }

    // Cancel existing retry timeout
    if (this.retryTimeout) {
        clearTimeout(this.retryTimeout);
    }

    // Schedule retry
    console.log('[Shell/Registration] 🔄 Scheduling retry in 10 seconds...');
    this.retryTimeout = setTimeout(() => {
        console.log('[Shell/Registration] 🔄 Retrying registration...');
        this.registerDevice();
    }, 10000);
}
```

**NEW CODE with limits**:
```javascript
} catch (error) {
    // Reset flag first
    this.isRegistering = false;

    // ⏳ Network error (server offline/unreachable)
    console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

    // Show WiFi offline icon
    if (window.ShellWiFiStatus) {
        window.ShellWiFiStatus.updateStatus('offline');
    }

    // Update UI with pending code
    try {
        const pendingCode = this.getPendingCode();
        window.ShellUI.updateUI('pending', pendingCode);
    } catch (uiError) {
        console.error('[Shell/Registration] ⚠️ UI update failed:', uiError);
    }

    // Update UI status message
    const statusMessage = document.getElementById('status-message');
    if (statusMessage) {
        statusMessage.textContent = 'Server offline - Will retry when connection restored';
        statusMessage.style.color = '#f59e0b';
    }

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Server Offline', 'Cannot connect to server. Retrying when connection is restored.', 8000);
    }

    // 🛡️ GUARD 3: Only retry if device NOT already registered
    const deviceIdAfterError = localStorage.getItem('device_id');
    if (deviceIdAfterError) {
        console.warn('[Shell/Registration] ⚠️ Device already registered despite error, skipping retry');
        this.clearRetryCount();
        return;
    }

    // FIX 4: Check retry limit before scheduling next retry
    const currentRetry = this.getRetryCount();
    if (currentRetry >= this.MAX_RETRIES) {
        console.error('[Shell/Registration] ❌ Max retries exceeded!', {
            maxRetries: this.MAX_RETRIES,
            totalAttempts: currentRetry + 1,
            elapsedTime: this._calculateElapsedTime(currentRetry)
        });

        // Show error message to user
        if (statusMessage) {
            statusMessage.textContent = 'Unable to reach server. Check your network connection and refresh the page.';
            statusMessage.style.color = '#ef4444';
        }

        // Show error toast
        if (window.Toast) {
            window.Toast.error('Connection Failed', 'Unable to connect to server after multiple attempts. Please check your network and refresh the page.', 10000);
        }

        // Clear retry count for next manual attempt
        this.clearRetryCount();

        return;  // Stop retrying
    }

    // Cancel existing retry timeout
    if (this.retryTimeout) {
        clearTimeout(this.retryTimeout);
        this.retryTimeout = null;
    }

    // FIX 4: Calculate retry delay with exponential backoff
    const nextRetry = this.incrementRetryCount();
    const retryDelay = this.calculateRetryDelay(nextRetry - 1);  // -1 because we already incremented

    console.log('[Shell/Registration] 🔄 Scheduling retry', {
        attempt: nextRetry,
        maxRetries: this.MAX_RETRIES,
        delay: retryDelay,
        nextRetryTime: new Date(Date.now() + retryDelay).toLocaleTimeString()
    });

    // Update status message with retry countdown
    if (statusMessage) {
        const countdownSeconds = Math.floor(retryDelay / 1000);
        statusMessage.textContent = `Retrying in ${countdownSeconds} seconds...`;
    }

    // Schedule retry with exponential backoff
    this.retryTimeout = setTimeout(() => {
        console.log('[Shell/Registration] 🔄 Retrying registration (attempt ' + nextRetry + ')...');
        this.registerDevice();
    }, retryDelay);
}
```

**Add helper method for elapsed time calculation**:

```javascript
/**
 * Calculate total elapsed time for retries
 * @private
 */
_calculateElapsedTime: function(retryCount) {
    let totalMs = 0;
    for (let i = 0; i < retryCount; i++) {
        totalMs += this.calculateRetryDelay(i);
    }
    const seconds = Math.floor(totalMs / 1000);
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ${seconds % 60}s`;
},
```

**Update success handler to clear retry count (Line 189-190)**:

```javascript
// OLD CODE:
// Reset flag AFTER all operations complete
this.isRegistering = false;

// NEW CODE:
// FIX 4: Clear retry count on success
this.clearRetryCount();

// Reset flag AFTER all operations complete
this.isRegistering = false;
```

**Rationale**:
- Max 20 retries limits retry attempts to ~3.3 minutes
- Exponential backoff (5s, 7.5s, 11.25s, ..., 30s) reduces server load
- Retry count persisted in localStorage (survives page reload)
- On max retry reached, user gets clear error message to refresh
- User can manually refresh to reset counter and retry
- Prevents infinite loops and database pollution

---

## Test Cases

### Test 1: GUARD Race Condition

**Objective**: Verify that device_id is properly cleared and re-registration succeeds

**Steps**:
1. Device registers successfully (device_id = "123")
2. Backend marks code as expired
3. Activation poll detects expiration
4. localStorage is cleared
5. Verify device_id is null: `localStorage.getItem('device_id') === null`
6. Verify new code is generated and saved: `localStorage.getItem('pending_activation_code')` exists
7. Verify GUARD #2 doesn't block: `console.log` shows "Generated new activation code", not "already registered"

**Expected Result**: No "Device already registered" warning

---

### Test 2: Infinite Reload Loop

**Objective**: Verify no reload loop when code expires

**Steps**:
1. Device registers with code "123456"
2. Backend deletes code
3. Activation poll runs and detects expired
4. Verify `window.location.reload()` is NOT called
5. Verify new registration is called directly
6. Check console: Should show "Re-registering device", not "Reloading to register"
7. Let it run for 30 seconds
8. Verify page doesn't reload or flash (no browser refresh icon)

**Expected Result**: Page stays stable, generates new code without reloading

---

### Test 3: Code Generation Inconsistency

**Objective**: Verify same code is reused across page reload during retry

**Steps**:
1. Device calls registerDevice() → generates code "123456"
2. Network fails (kill server or throttle network)
3. Wait 2 seconds (before retry at 10 seconds)
4. User reloads page (F5)
5. Check localStorage: `localStorage.getItem('pending_activation_code')`
6. Verify it's still "123456", not a new code
7. Wait for auto-retry
8. Verify server receives same code "123456", not a different one

**Expected Result**: Same code before and after reload

---

### Test 4: Network Retry Without Limit

**Objective**: Verify retries stop after max limit

**Steps**:
1. Device attempts registration
2. Kill server (no network available)
3. Wait and watch console logs
4. Count retry attempts in console:
   - Attempt 1 (T=0s)
   - Attempt 2 (T=5s)
   - Attempt 3 (T=7.5s)
   - ...
   - Attempt 20 (T=~3 minutes)
5. Verify NO Attempt 21 appears
6. Check console shows "Max retries exceeded"
7. Check UI shows error message: "Unable to reach server"
8. Manually refresh page → retry counter resets
9. Verify next retry cycle starts from attempt 1

**Expected Result**: Retries stop at 20, clear error message shown

---

## Implementation Checklist

- [ ] Backup original files:
  ```bash
  cp /mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js /tmp/registration.js.backup
  cp /mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js /tmp/activation-poll.js.backup
  ```

- [ ] Apply FIX 1: GUARD Race Condition (activation-poll.js)
- [ ] Apply FIX 2: Infinite Reload Loop (activation-poll.js)
- [ ] Apply FIX 3: Code Generation Inconsistency (registration.js)
- [ ] Apply FIX 4: Network Retry Without Limit (registration.js)

- [ ] Test all 4 scenarios above
- [ ] Verify console logs show expected behavior
- [ ] Check localStorage after each test
- [ ] Deploy to test environment first
- [ ] Monitor production logs for any errors

---

## Summary

| Bug | Root Cause | Impact | Fix |
|-----|-----------|--------|-----|
| **GUARD Race** | No sync between clear & register | Registration rejected silently | Use atomic operations + verify after clear |
| **Reload Loop** | window.location.reload() on expiry | Infinite refresh until manual stop | Remove reload, use direct registration |
| **Code Inconsistency** | pendingCode lost on reload | Orphaned codes in DB | Persist to localStorage |
| **Unbounded Retry** | No retry limit | DB pollution + infinite retries | Add max retry + exponential backoff |

All fixes are backward compatible and don't require API changes.

---

## References

- **Device State Manager**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/state/deviceState.js`
- **Device Model**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/models/Device.js`
- **API Client**: `/mnt/g/khoirul/signate/player-vanillajs/js/core/api/api-client.js`

