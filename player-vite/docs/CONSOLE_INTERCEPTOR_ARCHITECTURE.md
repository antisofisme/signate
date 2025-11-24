# Console Interceptor Architecture Analysis

## Executive Summary

This document provides a comprehensive architectural analysis for implementing a **Console Interceptor** in player-vite that captures browser console output and sends it to the backend without breaking existing functionality.

**Key Challenge**: Intercept native browser console methods while preserving the existing SharedLogger functionality and avoiding conflicts.

---

## 1. Existing Architecture Analysis

### 1.1 SharedLogger (Custom Application Logger)

**Location**: `/src/shared/logger/shared-logger.ts`

**Current Responsibilities**:
- Application-level logging with namespaces
- Log buffering and periodic flushing to backend
- Sensitive data redaction (tokens, passwords, etc.)
- Emoji prefixes and colored console output
- Console passthrough to original browser console
- Log level filtering (debug, log, info, warn, error)

**Key Implementation Details**:
```typescript
class SharedLoggerClass {
  // CRITICAL: Stores original console for passthrough
  private originalConsole = {
    debug: console.debug.bind(console),
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
  };

  // Buffers logs before sending to backend
  private logBuffer: LogEntry[] = [];

  // Auto-sends errors immediately, others on interval
  private bufferLog(level: LogLevel, message: string): void {
    // ...
    if (level === 'error') {
      void this.flush(); // Immediate send
    }
  }
}
```

**Backend Endpoint**: `POST /api/client/logs/batch`
- Sends buffered logs with device_id and device_token
- Auto-retries on failure (silent fail in dev mode)
- Periodic flush interval: `config.device.logSendInterval`

**Important Notes**:
- SharedLogger does NOT intercept browser console - it only provides application logging
- It uses `originalConsole` to passthrough to browser console
- No console method replacement occurs

### 1.2 SharedAPIClient (HTTP Client)

**Location**: `/src/shared/api/shared-api-client.ts`

**Features**:
- Type-safe fetch wrapper with auto-unwrapping
- Automatic JWT token injection from `localStorage.getItem('device_token')`
- Request timeout handling with AbortController
- Enhanced error handling with request IDs
- Debug mode for verbose logging

**Usage Pattern**:
```typescript
await SharedAPIClient.post('/api/client/logs/batch', {
  device_id: parseInt(deviceId, 10),
  logs: logsToSend,
});
```

### 1.3 SharedDeviceState (Device State Management)

**Location**: `/src/shared/device/shared-device-state.ts`

**Provides**:
- Device ID, token, organization data
- localStorage persistence
- Preferences management
- Device validation

**Relevant for Console Interceptor**:
```typescript
SharedDeviceState.getDeviceId();      // Get device ID for log sending
SharedDeviceState.getDeviceToken();   // Get auth token
SharedDeviceState.isActivated();      // Check if device is ready
```

### 1.4 ServiceRegistry (Service Management)

**Location**: `/src/shared/services/service-registry.ts`

**Pattern**: Centralized service registration to avoid global pollution

**Usage**:
```typescript
ServiceRegistry.register('ServiceName', ServiceInstance);
const service = ServiceRegistry.get<ServiceType>('ServiceName');
```

---

## 2. Console Interceptor Architecture Design

### 2.1 Module Structure

**Recommended Structure**:
```
player-vite/src/shared/logger/
├── index.ts                           # Barrel export
├── logger.types.ts                    # Existing types
├── shared-logger.ts                   # Existing logger
├── console-interceptor.ts             # NEW: Main interceptor
├── console-interceptor.types.ts       # NEW: Interceptor types
└── console-circular-replacer.ts       # NEW: Circular reference handler
```

**Why this structure?**:
- Keeps console interceptor in same domain as SharedLogger
- Avoids circular dependencies
- Clear separation of concerns
- Easy to test independently

### 2.2 TypeScript Interfaces & Types

**File**: `console-interceptor.types.ts`

```typescript
/**
 * Console Interceptor Type Definitions
 */

/**
 * Console method types that can be intercepted
 */
export type ConsoleMethod = 'log' | 'debug' | 'info' | 'warn' | 'error';

/**
 * Console log entry captured by interceptor
 */
export interface ConsoleLogEntry {
  /** Log level/method */
  level: ConsoleMethod;

  /** Serialized arguments (JSON-safe) */
  args: string[];

  /** Original arguments count */
  argsCount: number;

  /** Timestamp when logged */
  timestamp: string;

  /** Stack trace (for errors) */
  stackTrace?: string;

  /** Source location (file:line:column) */
  source?: string;

  /** Browser user agent */
  userAgent?: string;
}

/**
 * Console interceptor configuration
 */
export interface ConsoleInterceptorConfig {
  /** Enable/disable interceptor */
  enabled: boolean;

  /** Which console methods to intercept */
  methods: ConsoleMethod[];

  /** Maximum buffer size before forced flush */
  maxBufferSize: number;

  /** Auto-flush interval (ms) */
  flushInterval: number;

  /** Send errors immediately (skip buffering) */
  immediateErrorSend: boolean;

  /** Max argument string length (prevent huge payloads) */
  maxArgLength: number;

  /** Preserve original console behavior */
  preserveConsole: boolean;

  /** Capture stack traces for errors */
  captureStackTrace: boolean;

  /** Send to backend endpoint */
  backendEndpoint: string;

  /** Retry configuration */
  retry: {
    maxRetries: number;
    retryDelay: number;
    backoffMultiplier: number;
  };
}

/**
 * Serialization result for console arguments
 */
export interface SerializedArgs {
  /** JSON-safe string representations */
  serialized: string[];

  /** Whether any circular references were detected */
  hadCircularRefs: boolean;

  /** Whether any arguments were truncated */
  wasTruncated: boolean;
}

/**
 * Console interceptor interface
 */
export interface ConsoleInterceptor {
  /** Initialize interceptor and replace console methods */
  init(): void;

  /** Restore original console methods */
  restore(): void;

  /** Check if interceptor is active */
  isActive(): boolean;

  /** Manually flush buffered logs */
  flush(): Promise<void>;

  /** Get buffered logs */
  getBuffer(): ConsoleLogEntry[];

  /** Clear buffer */
  clearBuffer(): void;

  /** Update configuration */
  configure(config: Partial<ConsoleInterceptorConfig>): void;

  /** Enable/disable interceptor */
  enable(): void;
  disable(): void;
}
```

### 2.3 Circular Reference Handler

**File**: `console-circular-replacer.ts`

```typescript
/**
 * Circular Reference Replacer for JSON.stringify
 * Handles circular references in console arguments
 */

/**
 * Create a replacer function for JSON.stringify that handles circular references
 * @param maxDepth Maximum nesting depth (default: 10)
 * @param maxLength Maximum string length per value (default: 1000)
 */
export function createCircularReplacer(
  maxDepth: number = 10,
  maxLength: number = 1000
) {
  const seen = new WeakSet();
  let depth = 0;

  return function replacer(this: any, key: string, value: any): any {
    // Handle null/undefined
    if (value === null || value === undefined) {
      return value;
    }

    // Check max depth
    if (depth > maxDepth) {
      return '[Max Depth Exceeded]';
    }

    // Handle primitive types
    if (typeof value !== 'object') {
      // Truncate long strings
      if (typeof value === 'string' && value.length > maxLength) {
        return value.substring(0, maxLength) + '... [truncated]';
      }
      return value;
    }

    // Detect circular reference
    if (seen.has(value)) {
      return '[Circular Reference]';
    }

    // Mark as seen
    seen.add(value);
    depth++;

    // Handle special object types
    if (value instanceof Error) {
      return {
        name: value.name,
        message: value.message,
        stack: value.stack?.substring(0, maxLength),
      };
    }

    if (value instanceof Date) {
      return value.toISOString();
    }

    if (value instanceof RegExp) {
      return value.toString();
    }

    if (typeof value.toJSON === 'function') {
      return value.toJSON();
    }

    // Handle arrays and plain objects
    const result = Array.isArray(value) ? [] : {};

    try {
      for (const k in value) {
        if (Object.prototype.hasOwnProperty.call(value, k)) {
          (result as any)[k] = replacer.call(value, k, value[k]);
        }
      }
    } finally {
      depth--;
    }

    return result;
  };
}

/**
 * Safely serialize value to JSON string
 * Handles circular references and truncation
 */
export function safeJSONStringify(
  value: any,
  maxDepth: number = 10,
  maxLength: number = 1000
): { json: string; hadCircular: boolean; wasTruncated: boolean } {
  let hadCircular = false;
  let wasTruncated = false;

  try {
    const replacer = createCircularReplacer(maxDepth, maxLength);
    const json = JSON.stringify(value, replacer, 2);

    // Detect if circular refs or truncation occurred
    hadCircular = json.includes('[Circular Reference]');
    wasTruncated = json.includes('[truncated]') || json.includes('[Max Depth Exceeded]');

    return { json, hadCircular, wasTruncated };
  } catch (error) {
    // Fallback for non-serializable values
    return {
      json: String(value),
      hadCircular: false,
      wasTruncated: true,
    };
  }
}

/**
 * Serialize console arguments to JSON-safe strings
 */
export function serializeConsoleArgs(
  args: unknown[],
  maxArgLength: number = 10000
): SerializedArgs {
  let hadCircularRefs = false;
  let wasTruncated = false;

  const serialized = args.map((arg) => {
    // Handle primitive types directly
    if (arg === null) return 'null';
    if (arg === undefined) return 'undefined';
    if (typeof arg === 'string') {
      const truncated = arg.length > maxArgLength
        ? arg.substring(0, maxArgLength) + '... [truncated]'
        : arg;
      if (arg.length > maxArgLength) wasTruncated = true;
      return truncated;
    }
    if (typeof arg === 'number' || typeof arg === 'boolean') {
      return String(arg);
    }

    // Handle objects with circular ref detection
    const { json, hadCircular, wasTruncated: argTruncated } = safeJSONStringify(
      arg,
      10,
      maxArgLength
    );

    if (hadCircular) hadCircularRefs = true;
    if (argTruncated) wasTruncated = true;

    return json;
  });

  return {
    serialized,
    hadCircularRefs,
    wasTruncated,
  };
}
```

### 2.4 Main Console Interceptor Implementation

**File**: `console-interceptor.ts`

```typescript
/**
 * Console Interceptor
 * Intercepts browser console methods and sends logs to backend
 *
 * CRITICAL DESIGN NOTES:
 * - Does NOT conflict with SharedLogger (different layers)
 * - SharedLogger = Application logging (user-initiated)
 * - ConsoleInterceptor = Browser console capturing (all sources)
 * - Both can coexist without interference
 */

import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { SharedLogger } from './shared-logger';
import { serializeConsoleArgs } from './console-circular-replacer';
import type {
  ConsoleInterceptor,
  ConsoleInterceptorConfig,
  ConsoleLogEntry,
  ConsoleMethod,
  SerializedArgs,
} from './console-interceptor.types';

/**
 * Default configuration
 */
const DEFAULT_CONFIG: ConsoleInterceptorConfig = {
  enabled: true,
  methods: ['log', 'debug', 'info', 'warn', 'error'],
  maxBufferSize: 100,
  flushInterval: 30000, // 30 seconds
  immediateErrorSend: true,
  maxArgLength: 10000,
  preserveConsole: true,
  captureStackTrace: true,
  backendEndpoint: '/api/client/console-logs/batch',
  retry: {
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2,
  },
};

/**
 * Console Interceptor Class
 * Singleton pattern
 */
class ConsoleInterceptorClass implements ConsoleInterceptor {
  private config: ConsoleInterceptorConfig;
  private buffer: ConsoleLogEntry[] = [];
  private flushTimer: number | null = null;
  private isInitialized = false;

  // Store ORIGINAL browser console (before any interception)
  private originalConsole: Record<ConsoleMethod, typeof console.log>;

  constructor() {
    this.config = { ...DEFAULT_CONFIG };

    // Capture ORIGINAL console methods IMMEDIATELY (before anyone else)
    this.originalConsole = {
      log: console.log.bind(console),
      debug: console.debug.bind(console),
      info: console.info.bind(console),
      warn: console.warn.bind(console),
      error: console.error.bind(console),
    };

    // Note: Do NOT auto-init in constructor - wait for explicit init() call
    // This allows configuration before initialization
  }

  /**
   * Initialize interceptor and replace console methods
   */
  init(): void {
    if (this.isInitialized) {
      SharedLogger.warn('[ConsoleInterceptor] Already initialized');
      return;
    }

    if (!this.config.enabled) {
      SharedLogger.log('[ConsoleInterceptor] Disabled by config');
      return;
    }

    // Replace console methods
    this.config.methods.forEach((method) => {
      this.interceptMethod(method);
    });

    // Start periodic flush
    this.startPeriodicFlush();

    this.isInitialized = true;
    SharedLogger.log('[ConsoleInterceptor] ✅ Initialized', {
      methods: this.config.methods,
      flushInterval: this.config.flushInterval,
    });
  }

  /**
   * Intercept a specific console method
   */
  private interceptMethod(method: ConsoleMethod): void {
    const originalMethod = this.originalConsole[method];

    // Replace console method with our interceptor
    (console as any)[method] = (...args: unknown[]) => {
      // ALWAYS call original console first (preserve behavior)
      if (this.config.preserveConsole) {
        originalMethod(...args);
      }

      // Capture and buffer the log
      this.captureLog(method, args);
    };
  }

  /**
   * Capture console log entry
   */
  private captureLog(method: ConsoleMethod, args: unknown[]): void {
    try {
      // Serialize arguments (handle circular refs)
      const { serialized, hadCircularRefs, wasTruncated } = serializeConsoleArgs(
        args,
        this.config.maxArgLength
      );

      // Create log entry
      const entry: ConsoleLogEntry = {
        level: method,
        args: serialized,
        argsCount: args.length,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
      };

      // Capture stack trace for errors
      if (method === 'error' && this.config.captureStackTrace) {
        entry.stackTrace = this.captureStackTrace();
      }

      // Add to buffer
      this.buffer.push(entry);

      // Check buffer size
      if (this.buffer.length >= this.config.maxBufferSize) {
        void this.flush();
      }

      // Immediate send for errors
      if (method === 'error' && this.config.immediateErrorSend) {
        void this.flush();
      }

      // Log warnings if serialization issues occurred
      if (hadCircularRefs || wasTruncated) {
        SharedLogger.debug('[ConsoleInterceptor] Serialization issues', {
          hadCircularRefs,
          wasTruncated,
        });
      }
    } catch (error) {
      // Silent fail - don't break console if interceptor fails
      SharedLogger.error('[ConsoleInterceptor] Failed to capture log', error);
    }
  }

  /**
   * Capture current stack trace
   */
  private captureStackTrace(): string | undefined {
    try {
      const stack = new Error().stack;
      // Remove first 3 lines (Error creation + this function + captureLog)
      return stack?.split('\n').slice(3).join('\n');
    } catch {
      return undefined;
    }
  }

  /**
   * Flush buffered logs to backend
   */
  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      // Device not activated yet - clear buffer to prevent memory leak
      this.buffer = [];
      return;
    }

    const logsToSend = [...this.buffer];
    this.buffer = []; // Clear buffer immediately

    await this.sendWithRetry(logsToSend);
  }

  /**
   * Send logs to backend with retry logic
   */
  private async sendWithRetry(
    logs: ConsoleLogEntry[],
    attempt: number = 1
  ): Promise<void> {
    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) return;

    try {
      await SharedAPIClient.post(this.config.backendEndpoint, {
        device_id: parseInt(deviceId, 10),
        logs,
      });

      SharedLogger.debug('[ConsoleInterceptor] ✅ Sent logs', {
        count: logs.length,
        attempt,
      });
    } catch (error) {
      // Retry logic
      if (attempt < this.config.retry.maxRetries) {
        const delay = this.config.retry.retryDelay *
          Math.pow(this.config.retry.backoffMultiplier, attempt - 1);

        SharedLogger.warn('[ConsoleInterceptor] Retrying...', {
          attempt,
          delay,
        });

        await new Promise((resolve) => setTimeout(resolve, delay));
        await this.sendWithRetry(logs, attempt + 1);
      } else {
        // Max retries exceeded - silent fail
        SharedLogger.error('[ConsoleInterceptor] Failed to send logs', {
          attempts: attempt,
          error,
        });
      }
    }
  }

  /**
   * Start periodic flush timer
   */
  private startPeriodicFlush(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = window.setInterval(() => {
      if (this.buffer.length > 0) {
        void this.flush();
      }
    }, this.config.flushInterval);
  }

  /**
   * Stop periodic flush timer
   */
  private stopPeriodicFlush(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /**
   * Restore original console methods
   */
  restore(): void {
    if (!this.isInitialized) {
      return;
    }

    // Restore original console methods
    this.config.methods.forEach((method) => {
      (console as any)[method] = this.originalConsole[method];
    });

    // Stop flush timer
    this.stopPeriodicFlush();

    // Flush remaining logs
    void this.flush();

    this.isInitialized = false;
    SharedLogger.log('[ConsoleInterceptor] ✅ Restored original console');
  }

  /**
   * Check if interceptor is active
   */
  isActive(): boolean {
    return this.isInitialized;
  }

  /**
   * Get buffered logs
   */
  getBuffer(): ConsoleLogEntry[] {
    return [...this.buffer];
  }

  /**
   * Clear buffer
   */
  clearBuffer(): void {
    this.buffer = [];
    SharedLogger.log('[ConsoleInterceptor] Buffer cleared');
  }

  /**
   * Update configuration
   */
  configure(config: Partial<ConsoleInterceptorConfig>): void {
    const wasInitialized = this.isInitialized;

    // Restore if initialized
    if (wasInitialized) {
      this.restore();
    }

    // Update config
    this.config = { ...this.config, ...config };

    // Re-initialize if was active
    if (wasInitialized && this.config.enabled) {
      this.init();
    }

    SharedLogger.log('[ConsoleInterceptor] Configuration updated', config);
  }

  /**
   * Enable interceptor
   */
  enable(): void {
    this.config.enabled = true;
    if (!this.isInitialized) {
      this.init();
    }
  }

  /**
   * Disable interceptor
   */
  disable(): void {
    this.config.enabled = false;
    if (this.isInitialized) {
      this.restore();
    }
  }

  /**
   * Cleanup resources (call before unload)
   */
  destroy(): void {
    this.restore();
    this.clearBuffer();
  }
}

// Export singleton instance
export const ConsoleInterceptor = new ConsoleInterceptorClass();
```

---

## 3. Integration Points

### 3.1 Initialization Point

**File**: `/src/main.ts`

**Where to initialize**: EARLY in the initialization chain, but AFTER config is loaded

```typescript
// Import config first
import { config } from '@shared/config';

// Import interceptor
import { ConsoleInterceptor } from '@shared/logger';

// Initialize interceptor BEFORE other services
const initApp = async () => {
  // Initialize console interceptor FIRST (capture all console output)
  ConsoleInterceptor.init();

  // ... rest of initialization
  SharedLogger.log('🔍 Initializing app...');
  // ...
};
```

**Why this order?**:
1. Config loaded first (needed for interceptor config)
2. Interceptor initialized early (captures all subsequent console output)
3. SharedLogger can still use original console (via its own binding)

### 3.2 ServiceRegistry Integration

**Optional**: Register interceptor for easy access

```typescript
ServiceRegistry.register('ConsoleInterceptor', ConsoleInterceptor);
```

### 3.3 Configuration Integration

**File**: `config.types.ts` - Add to `AppConfig`

```typescript
export interface ConsoleInterceptorConfig {
  enabled: boolean;
  flushInterval: number;
  maxBufferSize: number;
  immediateErrorSend: boolean;
}

export interface AppConfig {
  // ... existing config
  consoleInterceptor: ConsoleInterceptorConfig;
}
```

**File**: `index.ts` - Add default values

```typescript
export const config: AppConfig = {
  // ... existing config
  consoleInterceptor: {
    enabled: true,
    flushInterval: 30000,
    maxBufferSize: 100,
    immediateErrorSend: true,
  },
};
```

---

## 4. Memory Management Strategy

### 4.1 Buffer Size Control

**Problem**: Unbounded buffer growth can cause memory leaks

**Solution**:
```typescript
// Auto-flush when buffer reaches limit
if (this.buffer.length >= this.config.maxBufferSize) {
  void this.flush();
}

// Periodic flush to prevent accumulation
setInterval(() => this.flush(), this.config.flushInterval);
```

### 4.2 Argument Truncation

**Problem**: Large objects (DOM nodes, large arrays) can consume memory

**Solution**:
```typescript
// Truncate long strings
const maxArgLength = 10000;

// Limit object depth
const maxDepth = 10;

// Use circular replacer to prevent infinite recursion
```

### 4.3 Cleanup on Device Deactivation

**Pattern**:
```typescript
// When device is deactivated/reset
SharedEventBus.on('device:cleared', () => {
  ConsoleInterceptor.clearBuffer();
});
```

---

## 5. Error Handling Approach

### 5.1 Silent Failures

**Principle**: Console interceptor MUST NOT break the application

```typescript
private captureLog(method: ConsoleMethod, args: unknown[]): void {
  try {
    // ... capture logic
  } catch (error) {
    // SILENT FAIL - only log to SharedLogger
    SharedLogger.error('[ConsoleInterceptor] Failed to capture', error);
    // DO NOT throw or break console
  }
}
```

### 5.2 Retry Logic

**Pattern**: Exponential backoff for network failures

```typescript
const delay = retryDelay * Math.pow(backoffMultiplier, attempt - 1);
// Attempt 1: 1000ms
// Attempt 2: 2000ms
// Attempt 3: 4000ms
```

### 5.3 Fallback Serialization

**Pattern**: If JSON.stringify fails, fallback to String()

```typescript
try {
  json = JSON.stringify(value, circularReplacer);
} catch {
  json = String(value); // Fallback
}
```

---

## 6. Configuration Design

### 6.1 Runtime Configuration

**Via localStorage**:
```typescript
// Enable/disable at runtime
localStorage.setItem('CONSOLE_INTERCEPTOR_ENABLED', 'true');

// Change flush interval
localStorage.setItem('CONSOLE_INTERCEPTOR_FLUSH_INTERVAL', '60000');
```

**Via URL parameters**:
```typescript
// Disable for debugging
?console_interceptor=false

// Verbose mode
?console_interceptor_debug=true
```

### 6.2 Development vs Production

**Pattern**: Different configs for different environments

```typescript
const config = {
  consoleInterceptor: {
    enabled: import.meta.env.PROD, // Only in production
    flushInterval: import.meta.env.PROD ? 30000 : 60000,
    immediateErrorSend: true,
  },
};
```

---

## 7. Conflict Avoidance with SharedLogger

### 7.1 No Conflicts by Design

**Why they don't conflict**:

1. **Different Layers**:
   - SharedLogger: Application-level logging (explicit calls)
   - ConsoleInterceptor: Browser-level capturing (all console output)

2. **Different Bindings**:
   - SharedLogger binds to `originalConsole` in constructor (BEFORE interception)
   - ConsoleInterceptor binds to `console.*` AFTER SharedLogger initialized
   - Both use different captured references

3. **Flow Diagram**:
```
User code: console.log("test")
         ↓
ConsoleInterceptor intercept ← captures
         ↓
ConsoleInterceptor calls originalConsole.log() ← actually displays
         ↓
(no infinite loop because originalConsole is original browser console)
```

```
User code: SharedLogger.log("test")
         ↓
SharedLogger internal logic
         ↓
SharedLogger.originalConsole.log() ← uses its own binding
         ↓
(bypasses ConsoleInterceptor entirely)
```

### 7.2 Initialization Order

**Critical**: SharedLogger BEFORE ConsoleInterceptor

```typescript
// SharedLogger class instantiated early (in shared-logger.ts)
export const SharedLogger = new SharedLoggerClass();

// Later in main.ts:
import { SharedLogger } from '@shared/logger'; // ← SharedLogger captures console
import { ConsoleInterceptor } from '@shared/logger'; // ← Interceptor NOT yet active

const initApp = async () => {
  // NOW activate interceptor
  ConsoleInterceptor.init(); // ← Replaces console methods
};
```

**Result**: SharedLogger always has clean reference to browser console

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test circular reference handling**:
```typescript
const circular: any = { a: 1 };
circular.self = circular;

const { json, hadCircular } = safeJSONStringify(circular);
expect(hadCircular).toBe(true);
expect(json).toContain('[Circular Reference]');
```

**Test buffer limits**:
```typescript
// Fill buffer to max
for (let i = 0; i < 101; i++) {
  console.log(`test ${i}`);
}

// Should auto-flush at 100
expect(ConsoleInterceptor.getBuffer().length).toBeLessThan(100);
```

### 8.2 Integration Tests

**Test non-interference with SharedLogger**:
```typescript
const sharedLogs = SharedLogger.getBuffer();
const consoleLogs = ConsoleInterceptor.getBuffer();

SharedLogger.log('app log');
console.log('browser log');

// SharedLogger should NOT appear in console interceptor buffer
expect(consoleLogs.some(l => l.args.includes('app log'))).toBe(false);
```

---

## 9. Performance Considerations

### 9.1 Serialization Cost

**Optimization**: Defer serialization for batch processing

```typescript
// Instead of serializing immediately:
this.buffer.push({ level, args }); // Store raw args

// Serialize only when flushing:
const serialized = this.buffer.map(entry => serializeEntry(entry));
```

**Trade-off**: Higher memory usage but faster console operations

### 9.2 Flush Strategy

**Hybrid approach**:
- Errors: Immediate send (critical)
- Warnings: Buffer for 10s (important)
- Logs/Info/Debug: Buffer for 30s (bulk)

```typescript
const flushIntervals = {
  error: 0,      // Immediate
  warn: 10000,   // 10s
  log: 30000,    // 30s
};
```

---

## 10. Backend Integration Requirements

### 10.1 New Endpoint Needed

**Endpoint**: `POST /api/client/console-logs/batch`

**Request Body**:
```typescript
{
  device_id: number,
  logs: ConsoleLogEntry[]
}
```

**Response**:
```typescript
{
  success: true,
  data: {
    received: number,
    stored: number
  }
}
```

### 10.2 Database Schema

**New Table**: `console_logs`

```sql
CREATE TABLE console_logs (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  level VARCHAR(10) NOT NULL,
  args TEXT[] NOT NULL,
  args_count INTEGER NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  stack_trace TEXT,
  source VARCHAR(500),
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_console_logs_device ON console_logs(device_id);
CREATE INDEX idx_console_logs_level ON console_logs(level);
CREATE INDEX idx_console_logs_timestamp ON console_logs(timestamp);
```

---

## 11. Deployment Checklist

- [ ] Create `console-interceptor.types.ts`
- [ ] Create `console-circular-replacer.ts`
- [ ] Create `console-interceptor.ts`
- [ ] Update `shared/logger/index.ts` exports
- [ ] Add config to `config.types.ts`
- [ ] Initialize in `main.ts`
- [ ] Create backend endpoint
- [ ] Run database migration
- [ ] Test on local device
- [ ] Test on production device
- [ ] Monitor backend logs for payload size
- [ ] Verify no performance degradation

---

## 12. Future Enhancements

1. **Smart Sampling**: Only send 1 in N logs for high-frequency sources
2. **Source Mapping**: Map minified stack traces to source code
3. **Log Aggregation**: Group similar logs to reduce payload size
4. **Client-Side Search**: IndexedDB cache for offline log viewing
5. **Performance Metrics**: Track console.log frequency and patterns
6. **A/B Testing**: Enable/disable per device group

---

## Conclusion

The Console Interceptor can be implemented without conflicts by following these principles:

1. **Separate layers**: SharedLogger (app) vs ConsoleInterceptor (browser)
2. **Proper initialization order**: SharedLogger before interceptor
3. **Independent console bindings**: Each service captures its own reference
4. **Silent failures**: Never break console functionality
5. **Memory management**: Buffer limits and periodic flushing
6. **Type safety**: Full TypeScript coverage
7. **Performance**: Lazy serialization and smart batching

**Estimated Complexity**: Medium (2-3 days development + testing)

**Risk Level**: Low (well-isolated, fail-safe design)

**Maintenance**: Low (minimal dependencies, clear interfaces)
