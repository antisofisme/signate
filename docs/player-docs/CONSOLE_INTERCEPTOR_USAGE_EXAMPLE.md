# Console Interceptor - Usage Examples

## Basic Usage

### 1. Initialize Interceptor

```typescript
import { ConsoleInterceptor } from '@/lib/console-interceptor/console-interceptor';

const interceptor = new ConsoleInterceptor({
  apiBaseUrl: 'http://192.168.5.12:8001',
  deviceId: 123,
  enabled: true,
  debug: true, // Enable debug logs
  excludeNamespaces: ['[Toast]', '[ClearCache]'], // Exclude specific logs
});

// Start intercepting
interceptor.start();
```

### 2. Check State

```typescript
const state = interceptor.getState();

console.log('Is active:', state.isActive);
console.log('Is streaming:', state.isStreaming);
console.log('Buffered logs:', state.bufferedCount);
console.log('Total captured:', state.totalCaptured);
console.log('Total dropped:', state.totalDropped);
```

### 3. Get Historical Logs

```typescript
// Get all buffered logs (up to 1000)
const logs = interceptor.getBufferedLogs();

logs.forEach((log) => {
  console.log(`[${log.level}] ${log.message}`);
});
```

---

## Streaming Mode

### 4. Start Streaming

```typescript
// Add event listener first
interceptor.addEventListener((log) => {
  console.log('New log:', log);

  // Send to WebSocket, HTTP, etc.
  // ...
});

// Start streaming (emits events for new logs)
interceptor.startStreaming();

// All new console logs will trigger the event listener
console.log('This will emit an event!');
```

### 5. Stop Streaming

```typescript
// Stop emitting events (but continue buffering)
interceptor.stopStreaming();

// This will be buffered but NOT emit an event
console.log('This will NOT emit an event');
```

---

## WebSocket Integration Example

### 6. WebSocket Client (Simplified)

```typescript
class ConsoleWebSocketClient {
  private interceptor: ConsoleInterceptor;
  private ws: WebSocket | null = null;
  private batchBuffer: ConsoleLogEntry[] = [];
  private batchTimer: number | null = null;

  constructor(interceptor: ConsoleInterceptor, deviceId: number) {
    this.interceptor = interceptor;
    this.connect(deviceId);
  }

  private connect(deviceId: number): void {
    const wsUrl = `ws://192.168.5.12:8001/devices/${deviceId}/console/control`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[ConsoleWS] Connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleCommand(data.command);
    };

    this.ws.onerror = (error) => {
      console.error('[ConsoleWS] Error:', error);
    };

    this.ws.onclose = () => {
      console.log('[ConsoleWS] Disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(deviceId), 5000);
    };

    // Listen for new logs
    this.interceptor.addEventListener(this.onNewLog);
  }

  private onNewLog = (log: ConsoleLogEntry): void => {
    // Add to batch buffer
    this.batchBuffer.push(log);

    // Schedule batch send (debounce)
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    this.batchTimer = window.setTimeout(() => {
      this.sendBatch('realtime');
    }, 100); // Send every 100ms
  };

  private sendBatch(logType: 'historical' | 'realtime'): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    if (this.batchBuffer.length === 0) {
      return;
    }

    // Send batch
    this.ws.send(JSON.stringify({
      type: 'console_logs',
      logs: this.batchBuffer,
      logType,
    }));

    // Clear batch
    this.batchBuffer = [];
  }

  private handleCommand(command: string): void {
    if (command === 'start_streaming') {
      // Send all buffered logs (historical)
      const buffered = this.interceptor.getBufferedLogs();

      if (buffered.length > 0) {
        this.ws?.send(JSON.stringify({
          type: 'console_logs',
          logs: buffered,
          logType: 'historical',
        }));
      }

      // Start real-time streaming
      this.interceptor.startStreaming();

    } else if (command === 'stop_streaming') {
      // Stop real-time streaming (keep buffering)
      this.interceptor.stopStreaming();

      // Flush pending batch
      this.sendBatch('realtime');
    }
  }

  disconnect(): void {
    // Stop streaming
    this.interceptor.stopStreaming();

    // Remove listener
    this.interceptor.removeEventListener(this.onNewLog);

    // Close WebSocket
    this.ws?.close();
  }
}
```

### 7. Initialize WebSocket Client

```typescript
// In shell-registration.ts or similar
const interceptor = new ConsoleInterceptor({
  apiBaseUrl: 'http://192.168.5.12:8001',
  deviceId: getDeviceId(),
});

interceptor.start();

const wsClient = new ConsoleWebSocketClient(interceptor, getDeviceId());

// Store references for cleanup
window.consoleInterceptor = interceptor;
window.consoleWSClient = wsClient;
```

---

## Advanced Usage

### 8. Multiple Listeners

```typescript
// Listener 1: WebSocket
const wsListener = (log: ConsoleLogEntry) => {
  ws.send(JSON.stringify(log));
};

// Listener 2: Local storage
const storageListener = (log: ConsoleLogEntry) => {
  const logs = JSON.parse(localStorage.getItem('console_logs') || '[]');
  logs.push(log);
  localStorage.setItem('console_logs', JSON.stringify(logs.slice(-100)));
};

// Listener 3: Analytics
const analyticsListener = (log: ConsoleLogEntry) => {
  if (log.level === 'error') {
    trackError(log.message, log.stack_trace);
  }
};

interceptor.addEventListener(wsListener);
interceptor.addEventListener(storageListener);
interceptor.addEventListener(analyticsListener);
```

### 9. Conditional Streaming

```typescript
// Only stream errors in production
if (import.meta.env.PROD) {
  interceptor.addEventListener((log) => {
    if (log.level === 'error') {
      sendToBackend(log);
    }
  });
}

// Stream all logs in development
if (import.meta.env.DEV) {
  interceptor.addEventListener((log) => {
    console.log('[Intercepted]', log);
  });
}
```

### 10. Batch Sending

```typescript
class BatchSender {
  private buffer: ConsoleLogEntry[] = [];
  private timer: number | null = null;

  constructor(
    private interceptor: ConsoleInterceptor,
    private batchSize: number = 50,
    private batchInterval: number = 5000
  ) {
    interceptor.addEventListener(this.onLog);
  }

  private onLog = (log: ConsoleLogEntry): void => {
    this.buffer.push(log);

    // Send if batch size reached
    if (this.buffer.length >= this.batchSize) {
      this.flush();
      return;
    }

    // Schedule flush
    if (!this.timer) {
      this.timer = window.setTimeout(() => {
        this.flush();
      }, this.batchInterval);
    }
  };

  private flush(): void {
    if (this.buffer.length === 0) return;

    // Send batch
    sendToBackend(this.buffer);

    // Clear
    this.buffer = [];
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}

const batchSender = new BatchSender(interceptor, 50, 5000);
```

### 11. Cleanup

```typescript
// Stop intercepting
interceptor.stop();

// Or just stop streaming (keep buffering)
interceptor.stopStreaming();

// Clear buffer (WARNING: loses history)
interceptor.clearBuffer();
```

---

## Complete Example

### Full Integration with Shell Registration

```typescript
// shell-registration.ts
import { ConsoleInterceptor } from '@/lib/console-interceptor/console-interceptor';
import { ConsoleWebSocketClient } from '@/shared/services/console-websocket-client';

export async function initializeConsoleStreaming(): Promise<void> {
  try {
    // Get device ID from storage
    const deviceId = parseInt(localStorage.getItem('deviceId') || '0');
    if (!deviceId) {
      console.warn('[ConsoleStreaming] No device ID, skipping console streaming');
      return;
    }

    // Initialize interceptor
    const interceptor = new ConsoleInterceptor({
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://192.168.5.12:8001',
      deviceId,
      enabled: true,
      debug: import.meta.env.DEV,
      excludeNamespaces: ['[Toast]', '[ClearCache]'], // Don't stream UI logs
      maxMessageLength: 5000,
    });

    // Start intercepting
    interceptor.start();

    // Initialize WebSocket client
    const wsClient = new ConsoleWebSocketClient(interceptor, deviceId);

    // Store references for cleanup
    window.consoleInterceptor = interceptor;
    window.consoleWSClient = wsClient;

    console.log('[ConsoleStreaming] Initialized successfully');

    // Log state every 30 seconds (debugging)
    if (import.meta.env.DEV) {
      setInterval(() => {
        const state = interceptor.getState();
        console.log('[ConsoleStreaming] State:', state);
      }, 30000);
    }

  } catch (error) {
    console.error('[ConsoleStreaming] Initialization failed:', error);
  }
}

// Call during shell registration
initializeConsoleStreaming();
```

---

## Debugging

### Check Buffer Contents

```typescript
const logs = interceptor.getBufferedLogs();
console.table(logs.map((log) => ({
  time: new Date(log.timestamp).toLocaleTimeString(),
  level: log.level,
  message: log.message.substring(0, 50),
  source: log.source,
})));
```

### Monitor Events

```typescript
let eventCount = 0;
interceptor.addEventListener(() => {
  eventCount++;
  console.log(`Event #${eventCount}`);
});

// Check how many events were emitted
console.log('Total events:', eventCount);
```

### Compare Buffer vs Events

```typescript
let bufferedBefore = interceptor.getState().bufferedCount;

console.log('Test 1');
console.log('Test 2');
console.log('Test 3');

let bufferedAfter = interceptor.getState().bufferedCount;
console.log('New logs buffered:', bufferedAfter - bufferedBefore); // Should be 3
```

---

## TypeScript Types

```typescript
import type {
  ConsoleLogEntry,
  ConsoleLogEventListener,
  ConsoleInterceptorConfig,
  ConsoleInterceptorState,
} from '@/lib/console-interceptor/console-interceptor.types';

// Custom listener type
const myListener: ConsoleLogEventListener = (log: ConsoleLogEntry) => {
  if (log.level === 'error') {
    // Handle error
  }
};

// Config with all options
const config: ConsoleInterceptorConfig = {
  apiBaseUrl: 'http://192.168.5.12:8001',
  deviceId: 123,
  maxBatchSize: 50,
  enabled: true,
  captureLogLevels: ['log', 'warn', 'error'], // Only capture these levels
  excludeNamespaces: ['[Internal]'],
  maxMessageLength: 5000,
  debug: true,
};
```

---

## Common Patterns

### Pattern 1: Lazy Streaming

Only start streaming when needed:

```typescript
// Buffer always (even before admin connects)
interceptor.start();

// Start streaming only when admin opens console tab
function onAdminOpensConsole() {
  interceptor.startStreaming();
}

// Stop streaming when admin closes console tab
function onAdminClosesConsole() {
  interceptor.stopStreaming();
}
```

### Pattern 2: Selective Streaming

Stream only specific log levels:

```typescript
interceptor.addEventListener((log) => {
  // Only send errors and warnings
  if (log.level === 'error' || log.level === 'warn') {
    sendToBackend(log);
  }
});
```

### Pattern 3: Buffered + Real-time

Send historical logs first, then real-time:

```typescript
function startConsoleStreaming() {
  // 1. Send all buffered logs (historical)
  const historical = interceptor.getBufferedLogs();
  sendToBackend(historical, 'historical');

  // 2. Start real-time streaming
  interceptor.startStreaming();
}
```

---

## Error Handling

```typescript
try {
  interceptor.start();
} catch (error) {
  console.error('Failed to start console interceptor:', error);
  // Fallback: disable console interception
}

// Graceful shutdown
window.addEventListener('beforeunload', () => {
  try {
    interceptor.stop();
  } catch (error) {
    console.error('Failed to stop console interceptor:', error);
  }
});
```

---

## Performance Tips

1. **Batch logs before sending**
   - Don't send every single log immediately
   - Use debouncing or batching (50-100 logs or 100-500ms)

2. **Exclude noisy logs**
   - Use `excludeNamespaces` to filter out UI logs
   - Don't stream logs from third-party libraries

3. **Limit message length**
   - Use `maxMessageLength` to prevent huge logs
   - Default is 5000 characters

4. **Stream only when needed**
   - Don't start streaming on page load
   - Only stream when admin opens console tab

5. **Clean up listeners**
   - Remove event listeners when no longer needed
   - Prevent memory leaks

---

## Testing

### Unit Test Example

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ConsoleInterceptor } from './console-interceptor';

describe('ConsoleInterceptor', () => {
  let interceptor: ConsoleInterceptor;

  beforeEach(() => {
    interceptor = new ConsoleInterceptor({
      apiBaseUrl: 'http://test',
      deviceId: 123,
    });
    interceptor.start();
  });

  afterEach(() => {
    interceptor.stop();
  });

  it('should buffer logs', () => {
    console.log('Test 1');
    console.log('Test 2');

    const logs = interceptor.getBufferedLogs();
    expect(logs.length).toBe(2);
    expect(logs[0].message).toContain('Test 1');
  });

  it('should emit events when streaming', () => {
    let emitted = 0;
    interceptor.addEventListener(() => emitted++);

    console.log('Before streaming');
    expect(emitted).toBe(0);

    interceptor.startStreaming();
    console.log('During streaming');
    expect(emitted).toBe(1);

    interceptor.stopStreaming();
    console.log('After streaming');
    expect(emitted).toBe(1);
  });

  it('should maintain circular buffer', () => {
    for (let i = 0; i < 1100; i++) {
      console.log(`Log ${i}`);
    }

    const logs = interceptor.getBufferedLogs();
    expect(logs.length).toBe(1000);
    expect(logs[0].message).toContain('Log 100'); // Oldest
    expect(logs[999].message).toContain('Log 1099'); // Newest
  });
});
```

---

## Troubleshooting

### Logs not being buffered?

1. Check if interceptor is started: `interceptor.getState().isActive`
2. Check if logs are excluded: Review `excludeNamespaces` config
3. Check captured log levels: Review `captureLogLevels` config

### Events not being emitted?

1. Check if streaming: `interceptor.getState().isStreaming`
2. Check if listener is added: `interceptor.addEventListener(...)`
3. Start streaming: `interceptor.startStreaming()`

### Buffer full?

1. Check buffer size: `interceptor.getState().bufferedCount`
2. Max size is 1000 logs (FIFO)
3. Oldest logs are automatically removed

### Memory leak?

1. Remove event listeners when done: `interceptor.removeEventListener(...)`
2. Stop interceptor when done: `interceptor.stop()`
3. Clear buffer if needed: `interceptor.clearBuffer()`
