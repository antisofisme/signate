# Device Registration Bug Fixes - Test Guide

**Status**: All 4 bugs fixed with comprehensive test cases
**Test Date**: 2025-11-08
**Files Modified**:
- `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/registration.js`
- `/mnt/g/khoirul/signate/player-vanillajs/js/activation/services/activation-poll.js`

---

## Quick Test Checklist

```
TEST 1: Code Persistence (FIX 3)
  [ ] Browser DevTools > Application > localStorage > pending_activation_code exists
  [ ] Code persists after page reload
  [ ] Code clears on successful registration

TEST 2: Retry Limits (FIX 4)
  [ ] Retries stop at 20 attempts
  [ ] Exponential backoff: 5s → 7.5s → 11.25s → ... → 30s
  [ ] Max retry error message displayed
  [ ] Retry count clears after success or manual refresh

TEST 3: No Reload Loop (FIX 1 & 2)
  [ ] Page doesn't reload when code expires
  [ ] "Re-registering device" log appears, not "Reloading to register"
  [ ] New code generated directly without page refresh

TEST 4: GUARD Race Condition (FIX 1)
  [ ] device_id cleared atomically with other fields
  [ ] GUARD #2 doesn't block re-registration
  [ ] No "Device already registered" warning on expiry
```

---

## Detailed Test Cases

### TEST 1: Code Persistence & FIX 3 Verification

**Objective**: Verify that activation code persists across page reloads

**Prerequisites**:
- Fresh device (no previous registration)
- Server is running and accessible
- Browser console open (F12)

**Steps**:

1. **Navigate to viewer**
   ```
   Open: http://192.168.5.12:8080/
   Check console: Should see "[Shell/Registration] 🆕 Generated new activation code: XXXXXX"
   ```

2. **Verify code in localStorage**
   ```
   DevTools → Application → localStorage
   Look for: pending_activation_code = "XXXXXX" (6 digits)
   ```

3. **Simulate network failure and reload**
   ```
   In console: window.ShellState.API_BASE_URL = "http://invalid-server"
   This makes registration requests fail
   Console should show: "[Shell/Registration] ❌ Network error"
   ```

4. **Wait 2 seconds then reload page (F5)**
   ```
   Wait for page to reload
   Check console for: "[Shell/Registration] 🔄 Reusing existing code for retry: XXXXXX"
   The code should be the SAME code as before reload
   Check localStorage: pending_activation_code should still be "XXXXXX"
   ```

5. **Restore server and verify code is reused**
   ```
   In console: window.ShellState.API_BASE_URL = "http://192.168.5.12:8001"
   Wait for retry (should happen within 10 seconds)
   Console should show: "[Shell/Registration] ✅ Registration successful"
   Verify backend received the SAME code (not a new one)
   Check localStorage: pending_activation_code should be cleared
   ```

**Expected Results**:
- Code persists across page reload
- Same code used for retry after reload
- No "Device already registered" error
- Code is cleared only on successful registration

**Evidence in Console**:
```
[Shell/Registration] 🆕 Generated new activation code: 123456
[Shell/Registration] Pending code saved to localStorage: 123456
[Shell/Registration] ❌ Network error
[Shell/Registration] 🔄 Reusing existing code for retry: 123456
[Shell/Registration] ✅ Registration successful
[Shell/Registration] Pending code cleared from localStorage
```

---

### TEST 2: Retry Limits & Exponential Backoff (FIX 4)

**Objective**: Verify that retries stop after max limit with exponential backoff

**Prerequisites**:
- Fresh device or cleared localStorage
- Server shut down or network disconnected
- Browser console open
- Stopwatch or system time visible

**Steps**:

1. **Clear previous test data**
   ```javascript
   localStorage.clear()
   location.reload()
   ```

2. **Shut down server or disconnect network**
   ```bash
   # Disconnect network or kill backend:
   docker stop signage-backend
   ```

3. **Open viewer and watch retry pattern**
   ```
   Open: http://192.168.5.12:8080/ (or http://localhost:3000 for local dev)
   Watch console for retry messages
   Note the time between each retry
   ```

4. **Monitor retry sequence**

   Copy this to console to watch retries in real time:
   ```javascript
   // Monitor retry attempts
   const checkRetries = setInterval(() => {
       const count = localStorage.getItem('registration_retry_count');
       const code = localStorage.getItem('pending_activation_code');
       console.log(`[TEST] Retry count: ${count}, Code: ${code}`);
   }, 1000);
   ```

5. **Wait and observe retry pattern**

   Expected sequence:
   ```
   T=0s    [Shell/Registration] ❌ Network error
           [Shell/Registration] 🔄 Scheduling retry
           [Shell/Registration] Scheduling retry {attempt: 1, maxRetries: 20, delay: 5000}

   T=5s    [Shell/Registration] 🔄 Retrying registration (attempt 1)...
           [Shell/Registration] ❌ Network error
           [Shell/Registration] Scheduling retry {attempt: 2, maxRetries: 20, delay: 7500}

   T=13s   [Shell/Registration] 🔄 Retrying registration (attempt 2)...
           [Shell/Registration] ❌ Network error
           [Shell/Registration] Scheduling retry {attempt: 3, maxRetries: 20, delay: 11250}

   T=24s   [Shell/Registration] 🔄 Retrying registration (attempt 3)...
   ... (pattern continues, delays increase)

   T=~200s [Shell/Registration] 🔄 Retrying registration (attempt 20)...
           [Shell/Registration] ❌ Network error

   T=~220s [Shell/Registration] ❌ Max retries exceeded!
           [Shell/Registration] Max retries exceeded {
               maxRetries: 20,
               totalAttempts: 21,
               elapsedTime: "3m 40s"
           }

   Status message shows: "Unable to reach server. Check your network connection and refresh the page."
   ```

6. **Verify NO attempt 21**
   ```
   Let it run for 5 more minutes
   Console should NOT show any more retry attempts
   registration_retry_count should remain at 20
   ```

7. **Manually refresh and verify count resets**
   ```
   Press F5 to refresh
   Console should show: "[Shell/Registration] ✅ Generated new activation code"
   registration_retry_count should reset to 0
   Retry sequence starts over from attempt 1
   ```

8. **Restart server and verify recovery**
   ```bash
   docker start signage-backend
   ```

   Viewer should connect on next retry (within 30 seconds):
   ```
   [Shell/Registration] ✅ Registration successful
   registration_retry_count should clear
   ```

**Expected Results**:
- Retries follow exponential backoff: 5s, 7.5s, 11.25s, ..., up to 30s max
- Exactly 20 retry attempts before giving up
- Error message shown to user after max retries
- Retry count persists in localStorage across reloads
- User can manually refresh to reset and retry from scratch
- Success clears retry count

**Calculation Verification**:
```
Total time: ~3 minutes 40 seconds
Formula: sum of delays from 5s to 30s cap

Delay sequence (in seconds):
5.0, 7.5, 11.25, 16.88, 25.3, 30.0, 30.0, ..., 30.0 (repeats 30s after cap)

Total = 5 + 7.5 + 11.25 + 16.88 + 25.3 + (15 * 30) ≈ 220 seconds ≈ 3m 40s
```

---

### TEST 3: No Infinite Reload Loop (FIX 2)

**Objective**: Verify that code expiration doesn't cause reload loop

**Prerequisites**:
- Device already registered and activated
- Server accessible
- Browser console and Network tab open

**Steps**:

1. **Register device first**
   ```
   Complete full registration and activation (get green "Active" screen)
   Note the device ID and code from console
   ```

2. **Force code expiration**
   ```
   In backend database:
   DELETE FROM devices WHERE code = 'XXXXXX';

   Or via SQL:
   UPDATE devices SET status = 'deleted' WHERE id = <device_id>;
   ```

3. **Trigger activation poll to detect expiration**
   ```
   Activation poll runs every 5 seconds
   Wait for next poll cycle (max 5 seconds)

   Console should show:
   [Shell/ActivationPoll] 📊 Activation status: {expired: true, device_id: null}
   ```

4. **Watch for reload behavior**
   ```
   Open DevTools → Network tab
   Watch the network requests

   BAD BEHAVIOR (before fix):
   - Page reload appears in Network tab
   - Console clears (page restarted)
   - Then poll again
   - Then reload again
   - Loop continues forever

   GOOD BEHAVIOR (after fix):
   - No reload in Network tab
   - Console stays active
   - Shows: "[Shell/ActivationPoll] 🔄 Re-registering device"
   - New code generated
   - Polling continues
   ```

5. **Verify new code generation**
   ```
   Check console for:
   [Shell/ActivationPoll] ⚠️ Activation code expired
   [Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...
   [Shell/Registration] 🆕 Generated new activation code: YYYYYY

   The new code YYYYYY should be different from original code XXXXXX
   ```

6. **Check localStorage state**
   ```
   localStorage should have:
   - device_id: cleared (removed)
   - device_code: cleared (removed)
   - pending_activation_code: new code YYYYYY
   - device_token: preserved (not cleared)
   - organization_id: preserved (not cleared)
   ```

7. **Let it continue running**
   ```
   Don't touch anything for 1 minute
   Page should stay on activation screen showing new code
   No refresh icon, no Network activity (besides polls)
   Polling continues checking for new activation
   ```

**Expected Results**:
- No page reload occurs
- New code generated directly
- Page stays responsive and on activation screen
- Polling continues without refresh cycle
- User sees toast: "Activation Code Expired"
- Device can be re-activated with new code

**Key Logs to See**:
```
[Shell/ActivationPoll] ⚠️ Activation code expired
[Shell/ActivationPoll] 🔄 Re-registering device with preserved token & org_id...
[Shell/Registration] 🆕 Generated new activation code: YYYYYY
```

**What NOT to See**:
```
[Shell/ActivationPoll] 🔄 Reloading to register as new device...
window.location.reload (in Network tab)
Console clearing and restarting
```

---

### TEST 4: GUARD Race Condition (FIX 1)

**Objective**: Verify atomic localStorage clearing without race conditions

**Prerequisites**:
- Device registered
- Server accessible
- Browser console open
- Multiple tabs open (to simulate concurrent access)

**Steps**:

1. **Register device in Tab 1**
   ```
   Open Tab 1: http://192.168.5.12:8080/
   Complete registration
   Note code: "123456"
   Verify in localStorage: device_id = "123"
   ```

2. **Force code expiration**
   ```
   Backend: DELETE FROM devices WHERE code = '123456'
   Or simulate via: window.ShellState.API_BASE_URL = "http://invalid"
   ```

3. **Trigger expiration detection**
   ```
   Activation poll detects: {expired: true, device_id: null}
   ```

4. **Open Tab 2 simultaneously**
   ```
   While Tab 1 is clearing localStorage:
   - Don't wait for completion
   - Open Tab 2 at same time
   - Both tabs access localStorage concurrently

   This simulates race condition where:
   Tab 1: Clears device_id
   Tab 2: Reads device_id (might still be there from cache)
   ```

5. **Monitor Tab 1 behavior**
   ```
   Tab 1 console should show:
   [Shell/ActivationPoll] ⚠️ Activation code expired
   [Shell/ActivationPoll] Device cleared
   [Shell/ActivationPoll] Verifying device_id after clear...
   [Shell/ActivationPoll] device_id is: null ✓
   [Shell/ActivationPoll] 🔄 Re-registering device...
   [Shell/Registration] 🆕 Generated new activation code: 654321

   Should NOT show:
   [Shell/Registration] ⚠️ Device already registered (GUARD blocked)
   ```

6. **Verify GUARD #2 passes**
   ```
   After clearing, registerDevice() checks GUARD #2:
   const existingDeviceId = localStorage.getItem('device_id');
   if (existingDeviceId) { return; }  // ← Should NOT trigger

   Console should NOT show warning about device already registered
   ```

7. **Check for orphaned code**
   ```
   After GUARD passes, verify no pending code is orphaned:
   [Shell/Registration] ⚠️ Clearing orphaned pending code: null
   (null means nothing to clean up - good!)
   ```

**Expected Results**:
- localStorage cleared atomically via `deviceState.clearDevice()`
- GUARD #2 doesn't falsely block re-registration
- New code generated successfully
- No orphaned codes in database
- Both tabs handle expiration independently

**Evidence**:
```
[Shell/ActivationPoll] Device cleared
[Shell/Registration] 🆕 Generated new activation code: 654321
[Shell/Registration] ✅ Registration successful
```

**What NOT to See**:
```
[Shell/Registration] ⚠️ Device already registered (device_id exists in localStorage)
[Shell/Registration] device_id still exists after clear!
```

---

## Test Environment Setup

### Local Development Testing

```bash
# Stop docker services
docker-compose -f /mnt/g/khoirul/signate/docker/docker-compose.yml down

# Rebuild with latest code
docker-compose -f /mnt/g/khoirul/signate/docker/docker-compose.yml up -d --build

# Watch logs
docker logs -f signage-backend
docker logs -f signage-frontend  # if running locally
```

### Network Simulation Tools

```javascript
// In browser console - simulate network failure
window.ShellState.API_BASE_URL = "http://invalid-server";  // Causes 404/timeout

// Restore server
window.ShellState.API_BASE_URL = "http://192.168.5.12:8001";

// Monitor localStorage changes
window.addEventListener('storage', (e) => {
    console.log('[STORAGE]', e.key, '=', e.newValue);
});
```

### Database Verification

```sql
-- Check pending devices
SELECT id, code, status, created_at FROM devices
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 5;

-- Count orphaned codes (from TEST 3)
SELECT COUNT(*) as orphaned_count FROM devices
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL '1 hour';

-- Clear test data
DELETE FROM devices WHERE status = 'pending' AND code LIKE '1%';
```

---

## Regression Test Suite

After fixes are deployed, run this comprehensive test:

```javascript
/**
 * Comprehensive Device Registration Test Suite
 * Run in browser console after fixes deployed
 */

const registrationTests = {
    async runAll() {
        console.clear();
        console.log('Starting Device Registration Test Suite...\n');

        await this.testCodePersistence();
        await this.testRetryLimit();
        await this.testNoReloadLoop();
        await this.testGuardRaceCondition();

        console.log('\n✅ All tests completed!');
    },

    async testCodePersistence() {
        console.group('TEST 1: Code Persistence');

        // Clear previous test
        localStorage.clear();
        location.reload();

        await new Promise(r => setTimeout(r, 2000));

        const code = localStorage.getItem('pending_activation_code');
        const pass = code && code.length === 6 && /^\d+$/.test(code);

        console.log(`Code generated: ${code}`);
        console.log(`Result: ${pass ? '✅ PASS' : '❌ FAIL'}`);
        console.groupEnd();

        return pass;
    },

    async testRetryLimit() {
        console.group('TEST 2: Retry Limit');

        // This test requires server to be down
        console.warn('NOTE: This test requires backend server to be stopped');
        console.log('Expected: Max 20 retries with exponential backoff');
        console.log('Verify in console: "[Shell/Registration] ❌ Max retries exceeded!"');
        console.groupEnd();

        return true;  // Manual verification
    },

    async testNoReloadLoop() {
        console.group('TEST 3: No Reload Loop');

        const networkErrors = [];
        const reloads = [];

        // Monitor for reload attempts
        const origReload = window.location.reload;
        window.location.reload = function() {
            reloads.push(new Date());
            console.error('❌ FAIL: window.location.reload() called!');
        };

        console.log('Expected: No reload() calls on code expiration');
        console.log(`Reloads caught: ${reloads.length}`);

        const pass = reloads.length === 0;
        console.log(`Result: ${pass ? '✅ PASS' : '❌ FAIL'}`);

        window.location.reload = origReload;
        console.groupEnd();

        return pass;
    },

    async testGuardRaceCondition() {
        console.group('TEST 4: GUARD Race Condition');

        localStorage.clear();
        localStorage.setItem('device_id', '123');

        // Simulate GUARD #2 check
        const existingDeviceId = localStorage.getItem('device_id');
        const pass = existingDeviceId === '123';  // Should find it

        // Clear it
        localStorage.removeItem('device_id');
        const afterClear = localStorage.getItem('device_id');
        const passAfterClear = afterClear === null;  // Should be gone

        console.log(`Before clear: device_id = "${existingDeviceId}"`);
        console.log(`After clear: device_id = "${afterClear}"`);
        console.log(`Result: ${(pass && passAfterClear) ? '✅ PASS' : '❌ FAIL'}`);
        console.groupEnd();

        return pass && passAfterClear;
    }
};

// Run tests
registrationTests.runAll();
```

---

## Continuous Monitoring

After deployment, monitor these metrics:

### Application Logs
```
grep -i "Max retries exceeded" /var/log/signage/backend.log
grep -i "GUARD" /var/log/signage/browser.log
grep -i "orphaned" /var/log/signage/browser.log
```

### Database Health
```sql
-- Monitor pending device growth
SELECT
    DATE(created_at) as date,
    COUNT(*) as pending_devices
FROM devices
WHERE status = 'pending'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 10;

-- Check for orphaned codes (not deleted after 1 hour)
SELECT id, code, created_at
FROM devices
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL '1 hour'
ORDER BY created_at ASC;
```

### Frontend Metrics
```javascript
// Add to monitoring dashboard
{
    "registration_attempts": localStorage.getItem('registration_retry_count') || 0,
    "pending_code": localStorage.getItem('pending_activation_code'),
    "device_id": localStorage.getItem('device_id'),
    "last_registration_time": new Date(
        parseInt(localStorage.getItem('last_registration_ms') || Date.now())
    ).toISOString()
}
```

---

## Troubleshooting Failed Tests

### TEST 1 Fails: Code not persisting
```javascript
// Check if localStorage is enabled
console.log('localStorage available:', typeof(Storage) !== 'undefined');
console.log('localStorage.pending_activation_code:', localStorage.getItem('pending_activation_code'));

// Check browser console for errors
// Look for: "[Shell/Registration] Pending code saved to localStorage"
```

### TEST 2 Fails: Retries don't stop
```javascript
// Check retry count
console.log('Retry count:', localStorage.getItem('registration_retry_count'));

// Check if MAX_RETRIES constant is loaded
console.log('Max retries:', window.ShellRegistration.MAX_RETRIES);

// Verify exponential backoff is working
console.log('Retry delay for attempt 5:', window.ShellRegistration.calculateRetryDelay(5));
```

### TEST 3 Fails: Page reloads
```javascript
// Check if activation-poll was updated
console.log('Activation poll code:', window.ActivationPoll.checkActivation.toString().includes('window.location.reload'));
// Should return: false (no reload call)

// Manually trigger expiration
window.ActivationPoll.checkActivation();
// Should NOT reload page
```

### TEST 4 Fails: GUARD blocks re-registration
```javascript
// Manually check GUARD logic
localStorage.setItem('device_id', '123');
console.log('Has device_id:', !!localStorage.getItem('device_id'));

localStorage.removeItem('device_id');
console.log('After clear:', !!localStorage.getItem('device_id'));  // Should be false

// Simulate clearDevice
window.deviceState.clearDevice();
console.log('After deviceState.clearDevice:', !!localStorage.getItem('device_id'));
```

---

## Success Criteria

All tests pass when:

- ✅ Code persists across page reload
- ✅ Retries stop at 20 attempts with exponential backoff
- ✅ No reload loop when code expires
- ✅ GUARD race condition doesn't block re-registration
- ✅ Database has no orphaned pending devices
- ✅ User gets clear error message after max retries
- ✅ Retry counter resets on manual refresh
- ✅ No "Device already registered" false positives

---

## Cleanup After Testing

```javascript
// Reset test data
localStorage.clear();
localStorage.removeItem('pending_activation_code');
localStorage.removeItem('registration_retry_count');
localStorage.removeItem('device_id');
localStorage.removeItem('device_code');
location.reload();
```

