# Player-Vite Fix Priority - Quick Reference
**Prioritas berdasarkan Impact vs Effort**

---

## 🚨 FIX SEKARANG (P0 - Hari Ini)

### 1. Token Leakage (15 menit) ⚡
**File**: `shell-registration.ts:156`
```typescript
// ❌ SEKARANG
console.log('Registration payload:', { device_token });

// ✅ UBAH JADI
SharedLogger.log('[Registration] Payload:', { device_token: '***' });
```

### 2. Race Condition Registration (15 menit) ⚡
**File**: `shell-registration.ts:98`
```typescript
// ✅ Tambahkan flag
private isRegistering = false;

async registerDevice(code: string) {
  if (this.isRegistering) return;
  this.isRegistering = true;
  try { /* ... */ } finally { this.isRegistering = false; }
}
```

### 3. API Timeout (30 menit) ⚡
**File**: `shared-api-client.ts:52`
```typescript
// ✅ Tambahkan timeout
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 30000);
fetch(url, { signal: controller.signal });
```

### 4. Missing Null Checks (1 jam)
**File**: `shell-registration.ts:131`
```typescript
// ✅ Validate response
if (!response?.data?.device?.id) {
  throw new Error('Invalid response');
}
```

### 5. Blob URL Leak (30 menit) ⚡
**File**: `player-videojs.ts:448`
```typescript
// ✅ Revoke after load
img.onload = () => URL.revokeObjectURL(blobUrl);
```

**Total Hari Ini: ~3 jam** → Mengatasi 5 critical issues!

---

## 🔴 FIX MINGGU INI (P0 - Week 1)

### 6. Circular Dependency (2-4 jam)
**File**: `shell-bootstrap.ts:23`
- Remove `import { PlayerBackgroundAudio } from '@player/services'`
- Move ke Player context
- Use ServiceRegistry

### 7. Event Listener Cleanup (4-6 jam)
**Files**: device-info-popup.ts, shell-activation-poll.ts, dll
```typescript
// ✅ Add cleanup method
private cleanup: Array<() => void> = [];

render() {
  const handler = () => {...};
  element.addEventListener('click', handler);
  this.cleanup.push(() => element.removeEventListener('click', handler));
}

destroy() {
  this.cleanup.forEach(fn => fn());
}
```

### 8. Timer/Interval Cleanup (2-3 jam)
**Files**: shell-activation-poll.ts, player-heartbeat.ts
```typescript
// ✅ Clear before create
startPolling() {
  this.stopPolling(); // Always clear first
  this.intervalId = setInterval(...);
}
```

### 9. XSS Prevention (2 jam)
**File**: `shared-device-state.ts`
```typescript
// ✅ Sanitize before storing
import DOMPurify from 'dompurify';
const sanitized = DOMPurify.sanitize(data.name);
```

### 10. Error Swallowing Fix (4-6 jam)
**Files**: 20+ catch blocks
```typescript
// ✅ Always log errors
catch (error) {
  SharedLogger.error('[Component] Failed:', error);
  SharedToast.error(`Error: ${error.message}`);
}
```

**Total Week 1: 16-24 jam** → Zero P0 issues!

---

## 🟡 FIX BULAN INI (P1/P2 - Weeks 2-4)

### Week 2 - Standardization (24-32 jam)
- Standardize events (SharedEventBus only)
- Fix type safety (remove 'any')
- Standardize imports (path aliases)
- Centralize localStorage
- Extract magic numbers

### Week 3 - Code Quality (16-24 jam)
- Remove duplication
- Split large files
- Migrate console.log to logger
- Complete ServiceRegistry

### Week 4 - Tech Debt (16-24 jam)
- Address TODO items
- Add missing features
- Documentation updates

---

## 📊 Impact Matrix

| Issue | Impact | Effort | Priority | When |
|-------|--------|--------|----------|------|
| Token Leakage | 🔴 Critical | 15m | P0 | Today |
| Race Condition | 🔴 Critical | 15m | P0 | Today |
| API Timeout | 🔴 Critical | 30m | P0 | Today |
| Null Checks | 🔴 Critical | 1h | P0 | Today |
| Blob URL Leak | 🔴 Critical | 30m | P0 | Today |
| Circular Dep | 🔴 High | 2-4h | P0 | Week 1 |
| Event Cleanup | 🔴 Critical | 4-6h | P0 | Week 1 |
| Timer Cleanup | 🔴 Critical | 2-3h | P0 | Week 1 |
| XSS Prevention | 🔴 High | 2h | P0 | Week 1 |
| Error Swallow | 🟡 High | 4-6h | P0 | Week 1 |
| Event Pattern | 🟡 Medium | 8-10h | P1 | Week 2 |
| Type Safety | 🟡 Medium | 12-16h | P1 | Week 2 |
| Import Pattern | 🟢 Low | 4-6h | P1 | Week 2 |
| Code Dup | 🟢 Low | 6-8h | P2 | Week 3 |
| Large Files | 🟢 Low | 8-12h | P2 | Week 3 |

---

## 🎯 ROI (Return on Investment)

### Best ROI - Fix First! 💰

1. **Token Leakage** - 15 min → Prevents security breach
2. **Race Condition** - 15 min → Prevents duplicate devices
3. **API Timeout** - 30 min → Prevents device hangs
4. **Blob URL Leak** - 30 min → Prevents crashes

**Total: 1.5 jam → Mencegah 4 critical production issues!**

### Good ROI - Fix This Week 💵

5. **Event Cleanup** - 4-6 jam → Prevents memory leaks
6. **Timer Cleanup** - 2-3 jam → Prevents resource exhaustion
7. **Null Checks** - 1 jam → Prevents crashes
8. **Circular Dep** - 2-4 jam → Improves architecture

**Total: 10-15 jam → Production-safe codebase**

---

## 📋 Daily Checklist

### Hari 1 (3 jam) ✅
- [ ] Fix token leakage (15m)
- [ ] Fix race condition (15m)
- [ ] Add API timeout (30m)
- [ ] Add null checks (1h)
- [ ] Fix blob URL leak (30m)
- [ ] Test all fixes

### Hari 2 (4 jam) ✅
- [ ] Fix event listener cleanup (4h)
- [ ] Test memory leaks

### Hari 3 (3 jam) ✅
- [ ] Fix timer cleanup (2h)
- [ ] Fix XSS prevention (1h)

### Hari 4 (4 jam) ✅
- [ ] Fix circular dependency (4h)
- [ ] Test architecture

### Hari 5 (6 jam) ✅
- [ ] Fix error swallowing (6h)
- [ ] Full regression test

**Week 1 Total: ~20 jam → Zero P0 issues!**

---

## 🧪 Testing Strategy

### After Each Fix
```bash
# 1. Type check
npm run type-check

# 2. Build
npm run build

# 3. Deploy to dev
rsync -avz dist/ server:/path/to/player-vite/

# 4. Manual test in browser
# - Check console for errors
# - Monitor memory usage (F12 → Memory tab)
# - Test affected feature
```

### After All P0 Fixes
```bash
# Full regression test
npm run test
npm run test:e2e

# Memory leak test (run for 1 hour)
# - Open player in browser
# - Take memory snapshot every 10 minutes
# - Memory should be stable (< 10MB growth)

# Load test
# - Run 10 concurrent devices
# - Monitor server resources
# - Check for crashes/hangs
```

---

## 📞 Questions?

- **Architecture questions**: See PLAYER_VITE_COMPREHENSIVE_ANALYSIS.md
- **Security details**: See SECURITY_VULNERABILITY_ANALYSIS.md
- **Implementation guide**: See ERROR_FIX_REMEDIATION.md
- **Quick checklist**: See CRITICAL_ISSUES_CHECKLIST.txt

---

**Created**: 2025-11-19
**Total Issues**: 56 (13 P0, 18 P1, 25 P2)
**Estimated Total Effort**: 56-80 hours over 1 month
**Week 1 Priority**: 20 hours → Zero critical issues
