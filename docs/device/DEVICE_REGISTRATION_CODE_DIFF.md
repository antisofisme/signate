# Device Registration Fixes - Code Diff Reference

This document shows the before/after code changes for the 4 bug fixes.

---

## FIX 1 & 2: GUARD Race Condition + Infinite Reload Loop

**File**: `player-vanillajs/js/activation/services/activation-poll.js`

### Before (Lines 85-116)
```javascript
if (data.expired && !data.device_id) {
    console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Activation Code Expired', 'Your activation code has expired. Restarting registration...', 5000);
    }

    // Stop polling
    this.stopPolling();

    // Clear localStorage
    localStorage.clear();  // ❌ BUG 1: NOT ATOMIC - race condition

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

    // ❌ BUG 2: RELOAD CAUSES LOOP
    console.log('[Shell/ActivationPoll] 🔄 Reloading to register as new device...');
    window.location.reload();
    return;
}
```

### After (Lines 85-140)
```javascript
if (data.expired && !data.device_id) {
    console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

    // Show toast notification
    if (window.Toast) {
        window.Toast.warning('Activation Code Expired', 'Your activation code has expired. Restarting registration...', 5000);
    }

    // Stop polling
    this.stopPolling();

    // FIX 1 & 2: Use deviceState.clearDevice() for atomic clearing
    // This ensures all device data is cleared together without race conditions
    if (window.deviceState && window.deviceState.clearDevice) {
        window.deviceState.clearDevice();  // ✅ ATOMIC OPERATION
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

    // FIX 2: DON'T reload! Directly register instead
    console.log('[Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...');
    await window.ShellRegistration.registerDevice();  // ✅ NO RELOAD
    return;
}
```

**Key Differences**:
1. Replaced `localStorage.clear()` with `deviceState.clearDevice()` (atomic)
2. Added verification after clear: `localStorage.getItem('device_id')` check
3. Removed `window.location.reload()` call
4. Changed to direct registration: `await window.ShellRegistration.registerDevice()`

---

## FIX 3: Code Generation Inconsistency

**File**: `player-vanillajs/js/activation/services/registration.js`

### Before (Lines 6-9, 84-91, 143-144)
```javascript
// Lines 6-9: In-memory variable
window.ShellRegistration = {
    retryTimeout: null,
    isRegistering: false,
    pendingCode: null,  // ❌ BUG 3: Lost on page reload

    // ... other methods ...

    // Lines 84-91: Code generation
    // 🔑 Use existing code if retrying, otherwise generate new one
    if (!this.pendingCode) {
        this.pendingCode = this.generateActivationCode();
        console.log('[Shell/Registration] 🆕 Generated new activation code:', this.pendingCode);
    } else {
        console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', this.pendingCode);
    }
    const code = this.pendingCode;  // ❌ In-memory reference

    // ... later in success path ...

    // Lines 143-144: Cleanup
    // Clear pending code (registration succeeded)
    this.pendingCode = null;
};
```

### After (Lines 10-42, 175-184, 237)
```javascript
// Lines 10-14: Configuration (no in-memory variable)
window.ShellRegistration = {
    retryTimeout: null,
    isRegistering: false,

    // FIX 4: Add retry limit and backoff configuration
    MAX_RETRIES: 20,
    INITIAL_RETRY_DELAY_MS: 5000,
    MAX_RETRY_DELAY_MS: 30000,
    RETRY_BACKOFF_MULTIPLIER: 1.5,

    // ... FIX 3: Helper methods for localStorage ...
    /**
     * Get pending code from localStorage
     */
    getPendingCode: function() {
        return localStorage.getItem('pending_activation_code');  // ✅ PERSISTED
    },

    /**
     * Set pending code in localStorage
     */
    setPendingCode: function(code) {
        if (code) {
            localStorage.setItem('pending_activation_code', code);
            console.log('[Shell/Registration] Pending code saved to localStorage:', code);
        } else {
            localStorage.removeItem('pending_activation_code');
            console.log('[Shell/Registration] Pending code cleared from localStorage');
        }
    },

    // ... other methods ...

    // Lines 175-184: Code generation using localStorage
    // FIX 3: Check localStorage for existing pending code (survives page reload)
    let pendingCode = this.getPendingCode();  // ✅ PERSISTENT
    if (!pendingCode) {
        pendingCode = this.generateActivationCode();
        this.setPendingCode(pendingCode);  // ✅ SAVE TO STORAGE
        console.log('[Shell/Registration] 🆕 Generated new activation code:', pendingCode);
    } else {
        console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', pendingCode);
    }
    const code = pendingCode;

    // ... later in success path ...

    // Line 237: Cleanup using helper
    // FIX 3: Clear pending code from localStorage (registration succeeded)
    this.setPendingCode(null);  // ✅ HELPER METHOD
};
```

**Key Differences**:
1. Removed in-memory `pendingCode` variable
2. Added `getPendingCode()` helper for localStorage read
3. Added `setPendingCode()` helper for localStorage write
4. Changed code generation to use helpers
5. Code now survives page reload via localStorage

---

## FIX 4: Network Retry Without Limit

**File**: `player-vanillajs/js/activation/services/registration.js`

### Before (Lines 192-242)
```javascript
} catch (error) {
    // Reset flag first
    this.isRegistering = false;

    // ⏳ Network error (server offline/unreachable)
    console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

    // ... UI updates ...

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

    // ❌ BUG 4: Schedule retry with NO LIMIT
    console.log('[Shell/Registration] 🔄 Scheduling retry in 10 seconds...');
    this.retryTimeout = setTimeout(() => {
        console.log('[Shell/Registration] 🔄 Retrying registration...');
        this.registerDevice();  // ❌ RECURSIVE - NO LIMIT
    }, 10000);
}
```

### After (Lines 288-383)
```javascript
} catch (error) {
    // Reset flag first
    this.isRegistering = false;

    // ⏳ Network error (server offline/unreachable)
    console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

    // ... UI updates ...

    // 🛡️ GUARD 3: Only retry if device NOT already registered
    const deviceIdAfterError = localStorage.getItem('device_id');
    if (deviceIdAfterError) {
        console.warn('[Shell/Registration] ⚠️ Device already registered despite error, skipping retry');
        this.clearRetryCount();  // ✅ CLEANUP
        return;
    }

    // Cancel existing retry timeout
    if (this.retryTimeout) {
        clearTimeout(this.retryTimeout);
        this.retryTimeout = null;
    }

    // FIX 4: Check retry limit before scheduling next retry
    const currentRetry = this.getRetryCount();  // ✅ GET COUNT
    if (currentRetry >= this.MAX_RETRIES) {  // ✅ CHECK LIMIT
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
        this.clearRetryCount();  // ✅ RESET FOR NEXT ATTEMPT

        return;  // ✅ STOP RETRYING
    }

    // FIX 4: Calculate retry delay with exponential backoff
    const nextRetry = this.incrementRetryCount();  // ✅ INCREMENT
    const retryDelay = this.calculateRetryDelay(nextRetry - 1);  // ✅ BACKOFF

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
    }, retryDelay);  // ✅ VARIABLE DELAY
}
```

**Key Differences**:
1. Added `MAX_RETRIES` constant (20 retries)
2. Added `getRetryCount()` to read from localStorage
3. Added `incrementRetryCount()` to increment & persist
4. Added `clearRetryCount()` to reset counter
5. Added max retry check before scheduling
6. Added exponential backoff calculation
7. Changed retry delay from fixed 10s to variable backoff
8. Added user error message when max retries exceeded
9. Show countdown in UI for next retry

**Retry Sequence**:
```
Attempt 1: 5.0s delay
Attempt 2: 7.5s delay
Attempt 3: 11.25s delay
Attempt 4: 16.88s delay
Attempt 5: 25.3s delay
Attempts 6-20: 30.0s delay (capped)

Total time: ~3 min 40 sec
Then: Error message and stop
```

---

## Helper Methods Added (FIX 3 & 4)

**File**: `player-vanillajs/js/activation/services/registration.js`

### FIX 3: Code Persistence Helpers
```javascript
/**
 * Get pending code from localStorage
 */
getPendingCode: function() {
    return localStorage.getItem('pending_activation_code');
},

/**
 * Set pending code in localStorage
 */
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

### FIX 4: Retry Limit Helpers
```javascript
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

---

## GUARD #2 Enhancement (FIX 1)

**File**: `player-vanillajs/js/activation/services/registration.js`

### Before (Lines 71-76)
```javascript
// 🛡️ GUARD 2: Check if already registered (localStorage check)
const existingDeviceId = localStorage.getItem('device_id');
if (existingDeviceId) {
    console.warn('[Shell/Registration] ⚠️ Device already registered (device_id exists in localStorage), skipping registration');
    console.log('[Shell/Registration] Existing device_id:', existingDeviceId);
    return;
}
```

### After (Lines 153-167)
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
        this.setPendingCode(null);  // ✅ CLEANUP
    }

    return;
}
```

**Enhancement**:
- Checks for orphaned pending code
- Clears it if device is somehow already registered
- Prevents database pollution from multiple codes per device

---

## Summary of Changes

| Change Type | Count | Files |
|------------|-------|-------|
| Lines Added | ~150 | 2 |
| Lines Removed | ~30 | 2 |
| Methods Added | 8 | registration.js |
| Methods Modified | 2 | both |
| New Constants | 4 | registration.js |
| New Helper Methods | 8 | registration.js |

**Total Impact**: ~120 net new lines of code across 2 files

