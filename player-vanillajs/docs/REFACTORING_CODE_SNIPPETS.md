# Refactored Code - Quick Reference

This document contains code snippets showing what was extracted from index.html into separate modules.

## Toast Module Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/core/ui/toast.js`

### Show Toast Notification
```javascript
// Basic usage
window.Toast.show(type, title, message, duration)

// Type can be: 'success', 'error', 'warning', 'info'
window.Toast.show('success', 'Success!', 'Operation completed', 5000)

// Convenience methods
window.Toast.success('Success!', 'Data saved successfully')
window.Toast.error('Error!', 'Something went wrong')
window.Toast.warning('Warning!', 'Please review this')
window.Toast.info('Info!', 'Here is some information')

// Auto-dismiss (0 = no auto-dismiss)
window.Toast.success('Quick message', 'Dismissed after 3 seconds', 3000)
window.Toast.info('Sticky message', 'Click X to close manually', 0)
```

### Toast Object Structure
```javascript
window.Toast = {
    icons: {
        success: '...',   // SVG icon
        error: '...',     // SVG icon
        warning: '...',   // SVG icon
        info: '...',      // SVG icon
        close: '...'      // SVG icon
    },
    show(type, title, message, duration),
    remove(toast),
    success(title, message, duration),
    error(title, message, duration),
    warning(title, message, duration),
    info(title, message, duration)
}
```

---

## Modal Module Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/core/ui/modal.js`

### Password Modal

```javascript
// Show password modal and get password
const password = await window.PasswordModal.show(
    'Hard Reset Device',
    'This will erase all data. Enter admin password:'
);

// With error handling
try {
    const password = await window.PasswordModal.show('Title', 'Message');
    console.log('User entered:', password);
} catch (err) {
    console.log('User cancelled');
}

// Verify password
const RESET_PASSWORD = window.ENV?.RESET_PASSWORD || 'admin123';
if (password === RESET_PASSWORD) {
    // Password correct
} else {
    window.Toast.error('Incorrect Password', 'Please try again');
}
```

### Organization PIN Modal

```javascript
// Show PIN modal and validate with server
const pin = await window.OrganizationPINModal.show();

// Features:
// - Validates PIN against server (/api/organizations/validate-pin)
// - Shows current PIN if already set
// - Allows changing/updating PIN
// - Returns PIN string on success
// - Rejects on cancel

// Server validation happens automatically
// Returns 404 if PIN not found
// Shows error toast if validation fails
```

### Modal Features

```javascript
// Both modals support:
// - Enter key to submit
// - Escape key to cancel
// - Promise-based API (async/await)
// - Toast integration for errors
// - Button state management
// - Modal styling and animations

// Example with error handling
window.PasswordModal.show('Title', 'Message')
    .then(password => {
        // User submitted password
        console.log('Password entered');
    })
    .catch(err => {
        // User cancelled
        console.log('Modal cancelled');
    })
```

---

## Fullscreen Module Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/fullscreen.js`

### Initialize Fullscreen Manager

```javascript
// Call on DOMContentLoaded
window.FullscreenManager.init()

// This initializes:
// - Mouse hover detection (top-right corner)
// - Fullscreen change listeners
// - Enter/exit button handlers
// - Display rotation recalculation
// - Player reload on viewport change
```

### Fullscreen Button Behavior

```javascript
// Enter fullscreen button
// - Click to enter fullscreen
// - Shows when hovering top-right corner
// - Only visible when NOT in fullscreen

// Exit fullscreen button
// - Click to exit fullscreen
// - Shows when hovering top-right corner
// - Only visible when IN fullscreen

// Hover area: right 150px, top 220px
// Buttons fade out when cursor leaves hover area
```

### Display Rotation Updates

```javascript
// When entering/exiting fullscreen:
// 1. Recalculate rotation (new viewport size)
// 2. Reload player if activated (viewport changed)
// 3. Update body.is-fullscreen class

// Calls window.ShellDisplaySettings.applyRotation() if available
// Calls window.ShellUI.loadPlayer() if device is activated
```

---

## Keyboard Module Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/keyboard.js`

### Initialize Keyboard Shortcuts

```javascript
// Call on DOMContentLoaded
window.KeyboardShortcuts.init()

// This enables:
// - 's' key: Toggle shell debug info
// - 'r' key: Reload player
// - 'f' key: Toggle fullscreen
// - 'Esc' key: Exit fullscreen
```

### Keyboard Shortcuts

```javascript
// Press 's' or 'S'
// - Toggle shell debug info display
// - Updates device_id, device_status, heartbeat
// - Visibility controlled by #shell-info display

// Press 'r' or 'R'
// - Calls window.reloadPlayer() if available
// - Reloads player iframe only

// Press 'f' or 'F'
// - Toggle fullscreen mode
// - If in fullscreen: exit
// - If not in fullscreen: enter (with fallback error)
// - Shows toast error if fullscreen not supported

// Press 'Escape'
// - Only if currently in fullscreen
// - Exits fullscreen mode
// - Document.exitFullscreen()
```

### Debug Info Toggle

```javascript
// When 's' key pressed:
// #shell-info display toggled
// Updates with:
// - device_id: from localStorage
// - device_status: from localStorage
// - logger: status indicator
// - heartbeat: indicator

document.getElementById('shell-info') // Toggle visibility
document.getElementById('debug-device-id') // Update value
document.getElementById('debug-status') // Update value
```

---

## Hard Reset Module Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/hard-reset.js`

### Initialize Hard Reset Handler

```javascript
// Call on DOMContentLoaded
window.HardResetHandler.init()

// This initializes hard reset button click handler
// - Shows password modal
// - Verifies password
// - Clears localStorage
// - Deletes IndexedDB
// - Reloads page
```

### Hard Reset Process

```javascript
// 1. Click hard reset button
// 2. Password modal appears
// 3. Enter password (admin123 by default)
// 4. If correct:
//    - localStorage.clear() (all data including device)
//    - indexedDB.deleteDatabase('signage_media_cache')
//    - location.reload() after cleanup
// 5. If wrong: Toast error "Incorrect Password"
// 6. If cancelled: Reset aborted

// Note: Organization PIN is cleared too!
// Use window.clearLocalStoragePreservePIN() to preserve PIN
```

### Data Cleared

```javascript
// localStorage.clear() removes:
// - device_id
// - device_status
// - device_code
// - activation_status
// - organization_pin (if hardReset, not preserved)
// - All other device data

// indexedDB.deleteDatabase() removes:
// - signage_media_cache (media cache)
// - All cached content

// After clear: Page reloads automatically
// Device shows activation screen again
// Requires re-activation with 6-digit code
```

### Password Verification

```javascript
// Password from ENV:
const RESET_PASSWORD = window.ENV?.RESET_PASSWORD || 'admin123'

// Default password: 'admin123'
// Can be overridden in ENV config
// Compared with user input from modal

if (password !== RESET_PASSWORD) {
    window.Toast.error('Incorrect Password', 'Reset cancelled')
    return
}

// If correct, proceed with reset
```

### Double-Click Prevention

```javascript
// isResetting flag prevents double-click
// Set to true when password verified
// Check at button click handler:

if (isResetting) {
    console.warn('Hard reset already in progress')
    return
}

// Reset completed automatically by page reload
```

---

## CSS Reference

**File**: `/mnt/g/khoirul/signate/player-vanillajs/styles/shell.css`

### CSS Sections Included

```css
/* Global Styles */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: ...; background: ...; color: white; }

/* Activation Screen */
#activation-screen { display: flex; ... }
.activation-card { background: ...; border: ...; ... }
.spinner { animation: spin 1s linear infinite; }

/* Player Container */
#player-container { display: none; position: fixed; ... }
#player-iframe { width: 100%; height: 100%; ... }

/* Control Buttons */
#enter-fullscreen-btn { position: fixed; top: 20px; right: 20px; ... }
#exit-fullscreen-btn { position: fixed; top: 20px; right: 20px; ... }
#org-pin-btn { position: fixed; top: 86px; right: 20px; ... }
#hard-reset-btn { position: fixed; top: 152px; right: 20px; ... }

/* Button States */
.show { opacity: 1; }
:hover { background: ...; transform: scale(1.1); ... }

/* Toast System */
#toast-container { position: fixed; bottom: 20px; right: 20px; ... }
.toast { display: flex; gap: 12px; animation: slideIn 0.3s; ... }
.toast.success { border-left: 3px solid #22c55e; }
.toast.error { border-left: 3px solid #ef4444; }
.toast.warning { border-left: 3px solid #f59e0b; }
.toast.info { border-left: 3px solid #3b82f6; }

/* Modals */
#password-modal { position: fixed; top: 0; left: 0; ... }
#org-pin-modal { position: fixed; top: 0; left: 0; ... }
.modal-content { background: ...; padding: 32px; ... }
.modal-input { width: 100%; padding: 12px 16px; ... }
.modal-btn { padding: 10px 20px; ... }

/* Animations */
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes slideIn { from { ... } to { ... } }
@keyframes slideOut { from { ... } to { ... } }
```

---

## Index.html Load Order

**File**: `/mnt/g/khoirul/signate/player-vanillajs/index.html`

```html
<!-- External Stylesheets -->
<link rel="stylesheet" href="styles/shell.css">

<!-- Helper Function (inline - must stay) -->
<script>
    window.clearLocalStoragePreservePIN = function() { ... }
</script>

<!-- Core Configuration (existing) -->
<script src="js/core/config/env.js"></script>
<script src="js/core/api/endpoints.js"></script>
<!-- ... other existing scripts ... -->

<!-- UI Modules (NEW - load after core) -->
<script src="js/core/ui/toast.js"></script>
<script src="js/core/ui/modal.js"></script>
<script src="js/activation/ui/fullscreen.js"></script>
<script src="js/activation/ui/keyboard.js"></script>
<script src="js/activation/ui/hard-reset.js"></script>

<!-- Initialization (DOMContentLoaded) -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        if (window.FullscreenManager) window.FullscreenManager.init();
        if (window.KeyboardShortcuts) window.KeyboardShortcuts.init();
        if (window.HardResetHandler) window.HardResetHandler.init();
        console.log('[Shell] UI modules initialized');
    });
</script>
```

---

## Module Export Format

Each module uses IIFE (Immediately Invoked Function Expression) with dual export:

```javascript
(function() {
    'use strict';

    // Define window global
    window.ModuleName = {
        // Implementation
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.ModuleName;
    }
})();
```

This ensures:
- Modules are immediately available as window globals
- No namespace pollution (IIFE scope)
- Can be imported as ES6 modules if needed
- Strict mode enabled
- Compatible with old browsers

---

## Testing in Browser Console

```javascript
// Test Toast
window.Toast.success('Test', 'This is a test notification');

// Test Modal
window.PasswordModal.show('Test', 'Enter password')
    .then(pw => console.log('Password:', pw))
    .catch(err => console.log('Cancelled'));

// Test PIN Modal
window.OrganizationPINModal.show()
    .then(pin => console.log('PIN:', pin))
    .catch(err => console.log('Cancelled'));

// Test Fullscreen
window.FullscreenManager.init();
// Then move mouse to top-right - buttons appear

// Test Keyboard
window.KeyboardShortcuts.init();
// Then press 's', 'r', 'f', or 'Esc'

// Test Hard Reset
window.HardResetHandler.init();
// Then click hard reset button

// Check all modules loaded
console.log({
    toast: window.Toast,
    passwordModal: window.PasswordModal,
    orgPinModal: window.OrganizationPINModal,
    fullscreen: window.FullscreenManager,
    keyboard: window.KeyboardShortcuts,
    hardReset: window.HardResetHandler
});
```

---

## File Locations Summary

| Component | File Path |
|-----------|-----------|
| CSS | `/mnt/g/khoirul/signate/player-vanillajs/styles/shell.css` |
| Toast | `/mnt/g/khoirul/signate/player-vanillajs/js/core/ui/toast.js` |
| Modal | `/mnt/g/khoirul/signate/player-vanillajs/js/core/ui/modal.js` |
| Fullscreen | `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/fullscreen.js` |
| Keyboard | `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/keyboard.js` |
| Hard Reset | `/mnt/g/khoirul/signate/player-vanillajs/js/activation/ui/hard-reset.js` |
| HTML | `/mnt/g/khoirul/signate/player-vanillajs/index.html` |

---

## JSDoc Comments

All modules include comprehensive JSDoc comments:
- Function descriptions
- Parameter types and descriptions
- Return value documentation
- Usage examples
- Implementation notes

Example:
```javascript
/**
 * Show a toast notification with the specified type
 *
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {string} title - Toast title text
 * @param {string} [message] - Optional toast message text
 * @param {number} [duration=5000] - Duration in ms before auto-dismiss
 * @returns {HTMLElement} The created toast element
 */
show: function(type, title, message, duration = 5000) { ... }
```

---

## Error Handling

All modules include error handling:

```javascript
// Toast shows error messages
window.Toast.error('Error Title', 'Error description')

// Modals handle Promise rejection
window.PasswordModal.show(...).catch(err => {
    // User cancelled
})

// Fullscreen handles browser API errors
requestFullscreen().catch(err => {
    window.Toast.error('Fullscreen Failed', err.message)
})

// Hard reset has try/catch for IndexedDB
try {
    indexedDB.deleteDatabase(dbName)
} catch (error) {
    console.error('Error deleting IndexedDB:', error)
}
```

---

## Console Logging

All modules use console logging for debugging:

```javascript
console.log('[Shell] Message')
console.warn('[Shell] Warning')
console.error('[Shell] Error')

// Prefixed with [Shell] for easy filtering
// Use localStorage/DevTools console to monitor
```

---

## Performance Considerations

1. **CSS**: Cacheable, loaded before scripts
2. **JS Modules**: Loaded in order, after CSS
3. **Initialization**: Runs on DOMContentLoaded
4. **Event Listeners**: Attached only once
5. **DOM Queries**: Cached when used multiple times
6. **Animations**: CSS-based (hardware accelerated)

---

This document serves as a quick reference for understanding the refactored code structure.
For detailed implementation, see the actual module files.
