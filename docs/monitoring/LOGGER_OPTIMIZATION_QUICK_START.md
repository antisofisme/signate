# Logger Optimization Quick Start Guide

**For Developers:** Fast implementation guide for console logger optimizations

---

## TL;DR - Critical Numbers

**Current Performance:**
- Buffer: 50 logs max
- Flush: Every 30 seconds
- No throttling, no circuit breaker
- Risk: 60 logs/sec in video loops

**Optimized Performance:**
- Buffer: 256KB memory limit
- Flush: Adaptive 5-60s based on activity
- Throttling: 5 logs/sec per namespace
- Circuit breaker: Auto-disable after 3 failures

**Expected Results:**
- 60-80% less network requests
- Zero frame drops during video playback
- Auto-recovery from backend outages

---

## Quick Implementation Checklist

### Phase 1: Critical Fixes (1 Week) - P0

**1. Add Circuit Breaker**
```typescript
// Location: player-vite/src/shared/logger/circuit-breaker.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.4
// Integrate into: shared-logger.ts flush() method

✅ Benefits: Stops wasted requests to failing backend
✅ Risk: LOW
✅ Impact: HIGH
```

**2. Add Memory Budget System**
```typescript
// Location: player-vite/src/shared/logger/memory-buffer.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.3
// Replace current: this.logBuffer array with MemoryAwareBuffer

✅ Benefits: Prevents memory spikes
✅ Risk: LOW
✅ Impact: MEDIUM
```

**3. Add Per-Namespace Throttling**
```typescript
// Location: player-vite/src/shared/logger/throttler.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.2
// Integrate into: createLogMethod() before buffering

✅ Benefits: 80-90% reduction in high-frequency logs
✅ Risk: MEDIUM (may lose some debug logs)
✅ Impact: HIGH
```

**4. Add Web Worker for Serialization**
```typescript
// Location: player-vite/src/shared/logger/serialization-worker.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.5
// Use in: flush() method for JSON.stringify()

✅ Benefits: Zero main thread blocking
✅ Risk: LOW
✅ Impact: HIGH (smooth video playback)
```

---

### Phase 2: Optimizations (2-4 Weeks) - P1

**5. Add Priority Queue**
```typescript
// Location: player-vite/src/shared/logger/priority-queue.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.1

✅ Benefits: Critical errors never lost
✅ Risk: LOW
✅ Impact: MEDIUM
```

**6. Add Adaptive Batching**
```typescript
// Location: player-vite/src/shared/logger/adaptive-batcher.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 2.1

✅ Benefits: 20-30% additional network reduction
✅ Risk: MEDIUM
✅ Impact: MEDIUM
```

**7. Add Metrics Collection**
```typescript
// Location: player-vite/src/shared/logger/metrics-collector.ts
// Copy implementation from: docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md Section 3.1

✅ Benefits: Real-time monitoring
✅ Risk: LOW
✅ Impact: LOW (debugging/monitoring only)
```

---

## Backend Changes Required

**1. Add Batch Endpoint**
```python
# Location: backend-python/services/device/log_routes.py

@router.post("/devices/{device_id}/logs/batch")
def create_device_logs_batch(
    device_id: int,
    dto: BatchCreateLogsDTO,
    db: Session = Depends(get_db)
):
    """Accept array of logs in single request"""
    # Validate batch size
    if len(dto.logs) > 500:
        raise HTTPException(400, "Batch too large")

    # Bulk insert (better performance)
    db.bulk_insert_mappings(DeviceLog, [
        {
            "device_id": device_id,
            "log_level": log.log_level,
            "message": log.message,
            # ... other fields
        }
        for log in dto.logs
    ])
    db.commit()

    return {"count": len(dto.logs)}
```

**2. Add Rate Limiting**
```python
from slowapi import Limiter

@router.post("/devices/{device_id}/logs/batch")
@limiter.limit("10/minute")  # Max 10 batches per minute per device
def create_device_logs_batch(...):
    # ... implementation
```

---

## Configuration Changes

**Update Environment Variables:**
```bash
# .env
VITE_LOG_SEND_INTERVAL=30000          # 30s (default)
VITE_LOG_BUFFER_SIZE=50               # 50 logs (default)
VITE_LOG_MEMORY_BUDGET=262144         # 256KB (new)
VITE_LOG_THROTTLE_RATE=5              # 5 logs/sec (new)
VITE_CIRCUIT_BREAKER_THRESHOLD=3      # 3 failures (new)
VITE_USE_WEB_WORKER=true              # Enable worker (new)
```

**Update Config Type:**
```typescript
// player-vite/src/shared/config/config.types.ts
export interface DeviceConfig {
  // Existing
  logSendInterval: number;
  logBufferSize: number;

  // New
  logMemoryBudget: number;
  logThrottleRate: number;
  circuitBreakerThreshold: number;
  useWebWorker: boolean;
}
```

---

## Testing Checklist

**Before Deployment:**
- [ ] High-frequency logging test (100 logs/sec)
- [ ] Large object logging test (1MB object)
- [ ] Circuit breaker test (backend down)
- [ ] Video playback test (no frame drops)
- [ ] Memory leak test (24h runtime)
- [ ] Backend batch endpoint test

**Performance Benchmarks:**
```typescript
// Test 1: High-frequency logging
for (let i = 0; i < 1000; i++) {
  logger.debug('[Test]', 'Log', i);
}
// Expected: < 100ms, buffer < 20 logs (throttled)

// Test 2: Video playback
const frameDropRate = measureFrameDrops();
// Expected: < 1% drop rate

// Test 3: Memory usage
const memoryUsage = logger.getMemoryUsage();
// Expected: < 256KB
```

---

## Monitoring Dashboards

**Key Metrics to Watch:**

**1. Buffer Health**
```
Current Buffer Size: 25 / 50 logs (50% utilization)
Memory Usage: 128KB / 256KB (50%)
Eviction Rate: 0 logs/min
```

**2. Network Efficiency**
```
Flushes/min: 2
Avg Batch Size: 25 logs
Success Rate: 98%
Circuit State: CLOSED
```

**3. Performance**
```
Avg Serialization: 15ms
Frame Drop Rate: 0.2%
Logs Throttled: 45/min
```

**4. Alerts**
```
⚠️ Buffer >90% full
⚠️ Network error rate >10%
⚠️ Logs/second >50
```

---

## Rollback Plan

**If Issues Occur:**

**1. Disable Web Worker**
```typescript
// config/index.ts
useWebWorker: false,  // Fallback to main thread
```

**2. Disable Throttling**
```typescript
// config/index.ts
logThrottleRate: 0,  // Disable throttling
```

**3. Disable Circuit Breaker**
```typescript
// config/index.ts
circuitBreakerEnabled: false,  // Always attempt flush
```

**4. Revert to Original Buffer**
```typescript
// shared-logger.ts
// Replace MemoryAwareBuffer with simple array
private logBuffer: LogEntry[] = [];
```

---

## FAQ

**Q: Will throttling cause me to lose important debug logs?**
A: No - critical errors are never throttled. Only high-frequency debug/info logs are throttled. You'll see a summary log like: "Logged 'Buffering...' 100x in 1s (throttled)"

**Q: What happens if the backend is down for hours?**
A: Circuit breaker opens after 3 failures, stops sending requests. Logs are buffered locally (up to 256KB). When backend recovers, circuit closes automatically.

**Q: Will Web Worker work on all devices?**
A: Yes - Web Workers are supported on all modern browsers, including WebOS TVs. Fallback to main thread if not supported.

**Q: How do I debug circuit breaker issues?**
A: Check circuit state: `logger.circuitBreaker.getState()`. Manually reset: `logger.circuitBreaker.reset()`

**Q: Can I customize throttle rates per namespace?**
A: Yes - see Section 2.2 in main analysis document for namespace-specific configurations.

---

## Quick Reference: Code Snippets

**Get Logger Status:**
```typescript
// Check buffer
const buffer = SharedLogger.getBuffer();
console.log('Buffer size:', buffer.length);

// Check memory
const memory = SharedLogger.getMemoryUsage();
console.log('Memory:', memory.bytes, 'bytes');

// Check circuit breaker
const circuit = SharedLogger.circuitBreaker.getState();
console.log('Circuit:', circuit.state);
```

**Manual Flush:**
```typescript
// Force flush logs immediately
await SharedLogger.flush();
```

**Clear Buffer:**
```typescript
// Clear all buffered logs
SharedLogger.clearBuffer();
```

**Change Log Level:**
```typescript
// Temporarily increase verbosity
SharedLogger.setLevel('debug');

// Reset to normal
SharedLogger.setLevel('info');
```

---

## Success Criteria

**After Implementation:**
- ✅ Network requests reduced by 60-80%
- ✅ Zero frame drops during video playback
- ✅ Memory usage capped at 256KB
- ✅ Backend outages handled gracefully
- ✅ Critical errors always captured
- ✅ Monitoring dashboard operational

---

**Document Version:** 1.0
**Last Updated:** 2025-01-22

For detailed implementation, see: `docs/CONSOLE_INTERCEPTOR_PERFORMANCE_ANALYSIS.md`
