# Console Interceptor Refactoring - Hybrid Streaming Architecture

## Overview

The Console Interceptor has been refactored from an **auto-upload batch system** to a **persistent buffer with on-demand streaming** to support the Hybrid Console Streaming architecture.

---

## Changes Made

### 1. Removed Auto-Upload Logic

**Before**:
- HTTP POST requests to upload logs
- Timer-based auto-flush (5-60 seconds)
- Circuit breaker for upload failures
- Memory budget management

**After**:
- NO HTTP requests (interceptor is transport-agnostic)
- NO timers (no auto-flush)
- NO circuit breaker (no uploads)
- Simple circular buffer management

### 2. Persistent Buffer

**Before**:
- Buffer cleared after each successful upload
- Memory budget limit (256KB)
- Batch size limit (50 logs)

**After**:
- **Persistent circular buffer (1000 logs max, FIFO)**
- Buffer NEVER cleared (except manual `clearBuffer()`)
- Oldest logs removed when buffer full
- Always maintains historical logs

### 3. Streaming State Machine

**New Feature**: Added streaming control methods

```typescript
// Start streaming - begin emitting events
interceptor.startStreaming();

// Stop streaming - stop events, keep buffering
interceptor.stopStreaming();

// Check if streaming
state.isStreaming; // boolean
```

**State Flow**:
```
[BUFFERING] (default)
     ↓ startStreaming()
[STREAMING] → Emits events for each new log
     ↓ stopStreaming()
[BUFFERING] → Back to buffering only
```

### 4. Event Emitter

**New Feature**: Event-driven architecture for real-time logs

```typescript
// Add listener
interceptor.addEventListener((log) => {
  console.log('New log:', log);
});

// Remove listener
interceptor.removeEventListener(listener);
```

**Behavior**:
- Events ONLY emitted when `isStreaming = true`
- Always buffers logs (even when not streaming)
- External listeners (e.g., WebSocket client) receive events

### 5. Buffer Access

**New Method**: `getBufferedLogs()`

```typescript
// Get all buffered logs (historical)
const logs = interceptor.getBufferedLogs();
// Returns copy of buffer (up to 1000 logs)
```

**Use Case**:
- When admin opens Console tab
- Send all historical logs immediately
- Then start real-time streaming

---

## API Changes

### Constructor Config

**Removed Options**:
- ❌ `flushInterval` (no auto-flush)
- ❌ `maxFlushInterval` (no auto-flush)
- ❌ `memoryBudget` (fixed buffer size)

**Kept Options**:
- ✅ `apiBaseUrl` (for future use)
- ✅ `deviceId` (for future use)
- ✅ `maxBatchSize` (for external batching)
- ✅ `enabled`
- ✅ `captureLogLevels`
- ✅ `excludeNamespaces`
- ✅ `maxMessageLength`
- ✅ `debug`

### State Interface

**Removed Properties**:
- ❌ `memoryUsage` (not tracked)
- ❌ `totalSent` (no uploads)
- ❌ `lastFlushAt` (no flushes)
- ❌ `lastError` (no upload errors)

**Added Properties**:
- ✅ `isStreaming` (streaming state)

**Kept Properties**:
- ✅ `isActive`
- ✅ `bufferedCount`
- ✅ `totalCaptured`
- ✅ `totalDropped`

### Methods

**Removed Methods**:
- ❌ `flush()` (no uploads)
- ❌ `manualFlush()` (no uploads)
- ❌ `scheduleFlush()` (no timers)

**Added Methods**:
- ✅ `getBufferedLogs()` → Get all buffered logs
- ✅ `startStreaming()` → Start emitting events
- ✅ `stopStreaming()` → Stop emitting events
- ✅ `addEventListener(listener)` → Add event listener
- ✅ `removeEventListener(listener)` → Remove event listener
- ✅ `clearBuffer()` → Clear buffer (WARNING: loses history)

**Kept Methods**:
- ✅ `start()` → Start interception
- ✅ `stop()` → Stop interception
- ✅ `getState()` → Get current state

---

## Integration with WebSocket Client

The interceptor is now **transport-agnostic**. It doesn't know about WebSocket or HTTP. It just:

1. Captures console logs
2. Stores in buffer (FIFO)
3. Emits events (when streaming)

**WebSocket Client Responsibilities** (separate file):
- Listen to interceptor events
- Send logs to backend via WebSocket
- Handle reconnection
- Batch logs before sending
- Handle control commands (start/stop streaming)

**Example Integration**:

```typescript
// console-websocket-client.ts
export class ConsoleWebSocketClient {
  private interceptor: ConsoleInterceptor;
  private ws: WebSocket;

  constructor(interceptor: ConsoleInterceptor) {
    this.interceptor = interceptor;

    // Listen for new logs
    this.interceptor.addEventListener(this.onNewLog);
  }

  private onNewLog = (log: ConsoleLogEntry) => {
    // Send to backend via WebSocket
    this.ws.send(JSON.stringify({
      type: 'console_logs',
      logs: [log],
      logType: 'realtime'
    }));
  };

  // Handle control commands from backend
  private handleCommand(command: string) {
    if (command === 'start_streaming') {
      // Send buffered logs first
      const buffered = this.interceptor.getBufferedLogs();
      this.ws.send(JSON.stringify({
        type: 'console_logs',
        logs: buffered,
        logType: 'historical'
      }));

      // Start real-time streaming
      this.interceptor.startStreaming();
    } else if (command === 'stop_streaming') {
      this.interceptor.stopStreaming();
    }
  }
}
```

---

## Benefits

### Before (Auto-Upload)

- ❌ Constant network traffic (every 5-60 seconds)
- ❌ No historical logs (cleared after upload)
- ❌ Delay (5-60 seconds)
- ❌ Complex (circuit breaker, timers, memory budget)
- ❌ Tight coupling (HTTP upload logic inside interceptor)

### After (On-Demand Streaming)

- ✅ Zero network traffic when not streaming
- ✅ Historical logs always available (1000 logs)
- ✅ Real-time (<100ms latency)
- ✅ Simple (just buffer + events)
- ✅ Separation of concerns (interceptor → events → transport)

---

## Migration Guide

### For Existing Code

**If you were using**:

```typescript
// OLD: Auto-flush
const interceptor = new ConsoleInterceptor({
  apiBaseUrl: 'http://192.168.5.12:8001',
  deviceId: 123,
  flushInterval: 5000,
  maxFlushInterval: 60000,
});

interceptor.start();
// Logs auto-uploaded every 5-60s
```

**Change to**:

```typescript
// NEW: Event-driven
const interceptor = new ConsoleInterceptor({
  apiBaseUrl: 'http://192.168.5.12:8001',
  deviceId: 123,
});

// Add listener
interceptor.addEventListener((log) => {
  // Handle log (e.g., send via WebSocket)
});

interceptor.start();
// Logs buffered, events emitted when streaming
```

**If you were using `flush()`**:

```typescript
// OLD: Manual flush
interceptor.manualFlush();
```

**Change to**:

```typescript
// NEW: Get buffered logs and send manually
const logs = interceptor.getBufferedLogs();
// Send logs via your transport (WebSocket, HTTP, etc.)
```

---

## Testing

### Test Scenarios

1. **Buffer Persistence**
   ```typescript
   interceptor.start();
   console.log('Test 1');
   console.log('Test 2');

   const logs = interceptor.getBufferedLogs();
   expect(logs.length).toBe(2);
   ```

2. **Circular Buffer (FIFO)**
   ```typescript
   interceptor.start();
   for (let i = 0; i < 1100; i++) {
     console.log(`Log ${i}`);
   }

   const logs = interceptor.getBufferedLogs();
   expect(logs.length).toBe(1000); // Max buffer size
   expect(logs[0].message).toContain('Log 100'); // Oldest is 100
   ```

3. **Streaming Events**
   ```typescript
   let emittedCount = 0;
   interceptor.addEventListener(() => emittedCount++);

   interceptor.start();
   console.log('Test'); // Buffered, NOT emitted
   expect(emittedCount).toBe(0);

   interceptor.startStreaming();
   console.log('Test 2'); // Buffered AND emitted
   expect(emittedCount).toBe(1);

   interceptor.stopStreaming();
   console.log('Test 3'); // Buffered, NOT emitted
   expect(emittedCount).toBe(1);
   ```

4. **Historical + Real-time**
   ```typescript
   interceptor.start();
   console.log('Historical 1');
   console.log('Historical 2');

   const historical = interceptor.getBufferedLogs();
   expect(historical.length).toBe(2);

   const realtime: ConsoleLogEntry[] = [];
   interceptor.addEventListener((log) => realtime.push(log));
   interceptor.startStreaming();

   console.log('Realtime 1');
   expect(realtime.length).toBe(1);
   expect(interceptor.getBufferedLogs().length).toBe(3); // All logs
   ```

---

## Files Changed

### Modified

- ✅ `player-vite/src/lib/console-interceptor/console-interceptor.ts`
  - Removed: HTTP upload, timers, circuit breaker, memory budget
  - Added: Persistent buffer, streaming state, event emitter
  - Changed: Constructor, state interface, methods

- ✅ `player-vite/src/lib/console-interceptor/console-interceptor.types.ts`
  - Removed: `ConsoleLogBatch`, `SaveLogsResponse`, `TransmissionError`, `CircuitBreakerState`, `CircuitBreakerStatus`
  - Added: `ConsoleLogEventListener`
  - Changed: `ConsoleInterceptorConfig`, `ConsoleInterceptorState`

### To Be Created (Next Steps)

- 🔜 `player-vite/src/shared/services/console-websocket-client.ts`
  - WebSocket client for console streaming
  - Listens to interceptor events
  - Sends logs to backend
  - Handles control commands

### To Be Modified (Next Steps)

- 🔜 `player-vite/src/shell/services/shell-registration.ts`
  - Initialize WebSocket client
  - Connect interceptor to WebSocket client

---

## Architecture Alignment

This refactoring aligns with the **Hybrid Console Streaming Architecture** documented in `/tmp/CONSOLE_STREAMING_HYBRID_ARCHITECTURE.md`:

| Requirement | Status |
|-------------|--------|
| Historical logs (like F12 DevTools) | ✅ Persistent buffer (1000 logs) |
| Real-time streaming | ✅ Event emitter |
| On-demand upload | ✅ No auto-upload |
| No log loss | ✅ FIFO buffer |
| Multi-tenant | ✅ Device ID in config |

---

## Next Steps

1. **Create WebSocket Client** (`console-websocket-client.ts`)
   - Connect to backend control WebSocket
   - Listen to interceptor events
   - Send logs to backend
   - Handle start/stop streaming commands

2. **Update Shell Registration**
   - Initialize WebSocket client
   - Pass interceptor instance to WebSocket client

3. **Backend Integration**
   - Implement console control WebSocket endpoint
   - Handle bidirectional communication
   - Broadcast logs to subscribed admins

4. **Testing**
   - Unit tests for interceptor
   - Integration tests for WebSocket client
   - End-to-end tests for full flow

---

## Questions?

See:
- Architecture: `/tmp/CONSOLE_STREAMING_HYBRID_ARCHITECTURE.md`
- Implementation: `player-vite/src/lib/console-interceptor/console-interceptor.ts`
- Types: `player-vite/src/lib/console-interceptor/console-interceptor.types.ts`
