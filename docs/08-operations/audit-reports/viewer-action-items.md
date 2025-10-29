# Viewer Audit - Action Items

**Date**: October 28, 2025
**Priority**: Based on audit findings

---

## 🔴 Critical (Before Production Deployment)

### None Found ✅
The viewer is production-ready with no critical issues.

---

## 🟡 High Priority (Should Fix This Sprint)

### 1. Security: Migrate to WSS for Production
**File**: Configuration files, WebSocket initialization
**Current**: `ws://192.168.5.12:8001`
**Target**: `wss://your-domain.com`

**Files to Update**:
- `viewer/js/config/env.js` - Update API_BASE_URL
- `viewer/js/shared/websocket.js` - Already supports wss://
- Backend CORS configuration

**Estimated Effort**: 1 hour
**Priority**: High (security)

```javascript
// Current
const API_BASE_URL = 'http://192.168.5.12:8001';
const wsUrl = 'ws://192.168.5.12:8001/ws/device/123';

// Target
const API_BASE_URL = 'https://your-domain.com';
const wsUrl = 'wss://your-domain.com/ws/device/123';
```

---

## 🟢 Medium Priority (Next Sprint)

### 2. Remove Duplicate WebSocket Client
**File**: `viewer/js/shared/websocket-client.js`
**Status**: Appears unused (395 lines)

**Actions**:
1. Search codebase for references to `WebSocketClient`
2. If unused, remove file
3. If backup/alternative, document purpose in README

**Verification**:
```bash
grep -r "WebSocketClient" viewer/js --include="*.js"
```

**Estimated Effort**: 30 minutes
**Priority**: Medium (cleanup)

---

### 3. Migrate Remaining Modules to APIClient
**Files**:
- `viewer/js/shell/display-settings.js` (line ~20)
- `viewer/js/shell/init.js` (line ~80)

**Current**:
```javascript
const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`);
const data = await response.json();
```

**Target**:
```javascript
const data = await APIClient.get(`${API_BASE_URL}/api/devices/${deviceId}`);
```

**Benefits**:
- Consistent error handling
- Auto-unwrapping of standardized responses
- Better debugging with request IDs

**Estimated Effort**: 1 hour
**Priority**: Medium (consistency)

---

## 🔵 Low Priority (Future Enhancements)

### 4. Add Automated Tests
**Scope**: Unit + Integration tests

**Recommended Framework**: Jest + Playwright

**Test Coverage**:
```javascript
// Unit Tests
- WebSocket client (connection, reconnect, heartbeat)
- API client (unwrapping, error handling)
- HLS player (quality switching, error recovery)

// Integration Tests
- Player-backend integration
- Shell-backend integration
- Cache synchronization

// E2E Tests (Playwright)
- Complete activation flow
- Playlist assignment and playback
- WebSocket updates
- Command execution
```

**Estimated Effort**: 1 week
**Priority**: Low (code quality is already high)

---

### 5. Code Splitting
**Goal**: Separate player and shell bundles

**Current**: Single bundle (~400KB)

**Target**:
```
shell.bundle.js  (~200KB) - Activation screen only
player.bundle.js (~200KB) - Loaded after activation
```

**Benefits**:
- Faster initial load
- Better caching
- Reduced memory usage

**Recommended Tool**: Webpack or Rollup

**Estimated Effort**: 2 days
**Priority**: Low (performance is already good)

---

### 6. Centralized Logging
**Goal**: Add log level control

**Current**: Console logs in all 33 files

**Target**:
```javascript
// Create logger utility
const Logger = {
  level: 'INFO', // DEBUG, INFO, WARN, ERROR

  debug: (module, ...args) => {
    if (this.level === 'DEBUG') {
      console.log(`[${module}]`, ...args);
    }
  },

  info: (module, ...args) => {
    if (['DEBUG', 'INFO'].includes(this.level)) {
      console.log(`[${module}]`, ...args);
    }
  },

  // ... warn, error
};
```

**Benefits**:
- Control log verbosity
- Production vs development logging
- Better performance (skip log generation)

**Estimated Effort**: 1 day
**Priority**: Low (current logging is acceptable)

---

### 7. TypeScript Migration
**Goal**: Add type safety

**Benefits**:
- Catch type errors at compile time
- Better IDE autocomplete
- Improved maintainability

**Migration Path**:
1. Add `tsconfig.json`
2. Rename `.js` → `.ts` (start with shared modules)
3. Add type definitions
4. Fix type errors
5. Gradually migrate all modules

**Estimated Effort**: 2 weeks
**Priority**: Low (nice to have)

---

### 8. Bundle Optimization
**Goal**: Reduce bundle size

**Current**: ~400KB uncompressed

**Target**: ~150KB compressed (gzip)

**Optimizations**:
1. Minification (Terser)
2. Tree shaking (Webpack/Rollup)
3. Compression (gzip/brotli)
4. Code splitting
5. Dynamic imports for HLS.js

**Estimated Effort**: 1 day
**Priority**: Low (performance is good)

---

## Verification Checklist

After implementing fixes, verify:

### Security (Priority 1)
- [ ] WSS protocol used in production
- [ ] HTTPS enabled on backend
- [ ] CORS updated for wss:// origin
- [ ] Test WebSocket connection from viewer
- [ ] Verify auto-reconnect works with wss://

### Code Cleanup (Priority 2-3)
- [ ] Unused WebSocket client removed or documented
- [ ] All modules using APIClient
- [ ] Error handling consistent across codebase
- [ ] No duplicate code patterns

### Testing (Priority 4)
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Coverage > 80%

### Performance (Priority 5-8)
- [ ] Bundle size reduced
- [ ] Lighthouse score > 90
- [ ] Load time < 3s
- [ ] Memory usage stable

---

## Quick Wins (30 minutes each)

These can be done immediately:

### 1. Document Unused WebSocket Client
**File**: Add comment to `websocket-client.js`
```javascript
/**
 * BACKUP WEBSOCKET CLIENT
 *
 * This is an alternative WebSocket implementation kept as backup.
 * Primary implementation is in websocket.js (SignageWebSocket class).
 *
 * Status: Not currently used in production
 * Purpose: Fallback/alternative implementation
 */
```

### 2. Add WSS Support in ENV Template
**File**: `viewer/js/config/env.template.js`
```javascript
// Add comment
window.ENV = {
  // For production: Use wss:// for secure WebSocket
  // For development: Use ws:// for local testing
  API_BASE_URL: 'http://192.168.5.12:8001', // Change to https:// in prod
  // ...
};
```

### 3. Add Browser Compatibility Notice
**File**: `viewer/README.md`
```markdown
## Browser Requirements

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+
- WebOS TV 4.0+

**Not Supported**: Internet Explorer 11 (requires ES6+ features)
```

---

## Summary

| Priority | Count | Total Effort | Status |
|----------|-------|--------------|--------|
| 🔴 Critical | 0 | - | ✅ None |
| 🟡 High | 1 | 1 hour | Security fix |
| 🟢 Medium | 2 | 1.5 hours | Cleanup |
| 🔵 Low | 5 | 4 weeks | Enhancements |
| **Quick Wins** | 3 | 1.5 hours | Documentation |

**Recommended Next Steps**:
1. ✅ Deploy current version to production (no blockers)
2. 🟡 Fix WSS migration for security (1 hour)
3. 🟢 Clean up duplicate WebSocket client (30 min)
4. 🟢 Migrate to APIClient consistently (1 hour)
5. 🔵 Consider long-term enhancements (testing, TypeScript, etc.)

---

**Generated**: October 28, 2025
**Status**: Ready for production with recommended security fix
