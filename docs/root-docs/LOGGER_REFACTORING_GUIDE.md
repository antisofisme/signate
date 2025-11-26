# Logger Refactoring Implementation Guide

## Quick Reference

**Estimated Effort**: 3-5 days
**Priority**: High (enables testing, improves maintainability)
**Breaking Changes**: Minimal (if done correctly)

---

## Phase 1: Dependency Injection (Day 1-2)

### Step 1.1: Define Interfaces

Create `/mnt/g/khoirul/signate/player-vite/src/shared/logger/interfaces.ts`:

```typescript
/**
 * Logger Interfaces - Dependency Abstractions
 */

/**
 * Storage interface for logger dependencies
 * Abstracts localStorage/sessionStorage/IndexedDB
 */
export interface LogStorage {
  getDeviceId(): string | null;
  getDeviceToken(): string | null;
  setItem(key: string, value: string): void;
  getItem(key: string): string | null;
  removeItem(key: string): void;
}

/**
 * Transport interface for sending logs to backend
 * Abstracts fetch/axios/WebSocket
 */
export interface LogTransport {
  /**
   * Send logs to backend
   * @param endpoint - Full URL endpoint
   * @param data - Log data to send
   * @param options - Optional request options
   * @returns Promise that resolves when logs are sent
   * @throws NetworkError if request fails
   */
  send(
    endpoint: string,
    data: unknown,
    options?: TransportOptions
  ): Promise<void>;
}

export interface TransportOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  timeout?: number;
}

/**
 * Event emitter interface for logger events
 * Allows components to react to logger state changes
 */
export interface LogEventEmitter {
  on(event: string, callback: (data?: unknown) => void): () => void;
  emit(event: string, data?: unknown): void;
}

/**
 * Logger configuration interface
 */
export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  maxBufferSize: number;
  flushInterval: number;
  apiBaseURL: string;
  endpoints: {
    logsBatch: string;
  };
}

export type LogLevel = 'debug' | 'log' | 'info' | 'warn' | 'error' | 'silent';
```

### Step 1.2: Implement Concrete Classes

Create `/mnt/g/khoirul/signate/player-vite/src/shared/logger/implementations/`:

#### `local-storage-adapter.ts`
```typescript
import type { LogStorage } from '../interfaces';

/**
 * LocalStorage implementation of LogStorage
 * Production implementation
 */
export class LocalStorageAdapter implements LogStorage {
  getDeviceId(): string | null {
    try {
      return localStorage.getItem('device_id');
    } catch (error) {
      console.warn('[LocalStorageAdapter] Failed to get device_id', error);
      return null;
    }
  }

  getDeviceToken(): string | null {
    try {
      return localStorage.getItem('device_token');
    } catch (error) {
      console.warn('[LocalStorageAdapter] Failed to get device_token', error);
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      console.warn(`[LocalStorageAdapter] Failed to set ${key}`, error);
    }
  }

  getItem(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn(`[LocalStorageAdapter] Failed to get ${key}`, error);
      return null;
    }
  }

  removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn(`[LocalStorageAdapter] Failed to remove ${key}`, error);
    }
  }
}
```

#### `fetch-transport.ts`
```typescript
import type { LogTransport, TransportOptions } from '../interfaces';

/**
 * Fetch-based implementation of LogTransport
 * Production implementation
 */
export class FetchTransport implements LogTransport {
  constructor(private readonly timeout: number = 30000) {}

  async send(
    endpoint: string,
    data: unknown,
    options?: TransportOptions
  ): Promise<void> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(endpoint, {
        method: options?.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        body: JSON.stringify(data),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }
}
```

#### `event-emitter.ts`
```typescript
import type { LogEventEmitter } from '../interfaces';

/**
 * Simple event emitter implementation
 */
export class SimpleEventEmitter implements LogEventEmitter {
  private listeners = new Map<string, Set<(data?: unknown) => void>>();

  on(event: string, callback: (data?: unknown) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  emit(event: string, data?: unknown): void {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[EventEmitter] Error in listener for ${event}:`, error);
      }
    });
  }

  removeAllListeners(event?: string): void {
    if (event) {
      this.listeners.delete(event);
    } else {
      this.listeners.clear();
    }
  }
}
```

### Step 1.3: Refactor SharedLogger

Update `shared-logger.ts`:

```typescript
import type {
  LogStorage,
  LogTransport,
  LogEventEmitter,
  LoggerConfig,
  LogLevel,
  LogEntry,
  Logger
} from './interfaces';
import { LocalStorageAdapter } from './implementations/local-storage-adapter';
import { FetchTransport } from './implementations/fetch-transport';
import { SimpleEventEmitter } from './implementations/event-emitter';

/**
 * Shared Logger Class (Refactored with DI)
 */
class SharedLoggerClass implements Logger {
  private currentLevel: number;
  private enabled: boolean;
  private logBuffer: LogEntry[] = [];
  private flushInterval: number | null = null;

  // Store original console
  private originalConsole = {
    debug: console.debug.bind(console),
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
  };

  constructor(
    private readonly config: LoggerConfig,
    private readonly storage: LogStorage,
    private readonly transport: LogTransport,
    private readonly eventEmitter: LogEventEmitter
  ) {
    this.currentLevel = LOG_LEVELS[config.level];
    this.enabled = config.enableConsole;

    // Start periodic flush
    this.startPeriodicFlush();

    this.originalConsole.log('[SharedLogger] Initialized v3.0 - Level:', config.level);
  }

  // ... rest of the implementation (same as before, but use injected dependencies)

  async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const deviceId = this.storage.getDeviceId();
    if (!deviceId) return;

    const logsToSend = [...this.logBuffer];
    this.logBuffer = []; // Clear buffer

    try {
      const endpoint = `${this.config.apiBaseURL}${this.config.endpoints.logsBatch}`;
      const token = this.storage.getDeviceToken();

      await this.transport.send(endpoint, {
        device_id: parseInt(deviceId, 10),
        logs: logsToSend,
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      this.eventEmitter.emit('flush:success', { count: logsToSend.length });
    } catch (error) {
      // Add logs back to buffer
      this.logBuffer.unshift(...logsToSend);

      this.eventEmitter.emit('flush:error', {
        error: error instanceof Error ? error.message : String(error),
        count: logsToSend.length,
      });

      if (this.config.debugMode) {
        this.originalConsole.warn('[SharedLogger] Failed to send logs', error);
      }
    }
  }

  // ... other methods
}

/**
 * Factory function to create logger with dependencies
 */
export function createLogger(
  config?: Partial<LoggerConfig>,
  storage?: LogStorage,
  transport?: LogTransport,
  eventEmitter?: LogEventEmitter
): Logger {
  const defaultConfig: LoggerConfig = {
    level: 'log',
    enableConsole: true,
    maxBufferSize: 50,
    flushInterval: 30000,
    apiBaseURL: 'http://192.168.5.12:8001',
    endpoints: {
      logsBatch: '/api/client/logs/batch',
    },
  };

  const mergedConfig = { ...defaultConfig, ...config };

  return new SharedLoggerClass(
    mergedConfig,
    storage || new LocalStorageAdapter(),
    transport || new FetchTransport(30000),
    eventEmitter || new SimpleEventEmitter()
  );
}

/**
 * Default singleton instance (for production)
 */
export const SharedLogger = createLogger();

/**
 * Export for testing
 */
export { SharedLoggerClass };
```

### Step 1.4: Create Test Helpers

Create `/mnt/g/khoirul/signate/player-vite/src/shared/logger/test-helpers/`:

#### `mock-storage.ts`
```typescript
import type { LogStorage } from '../interfaces';

/**
 * Mock storage for testing
 */
export class MockStorage implements LogStorage {
  private store = new Map<string, string>();

  getDeviceId(): string | null {
    return this.store.get('device_id') || null;
  }

  getDeviceToken(): string | null {
    return this.store.get('device_token') || null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }

  getItem(key: string): string | null {
    return this.store.get(key) || null;
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  // Test helpers
  setDeviceId(id: string | null): void {
    if (id === null) {
      this.store.delete('device_id');
    } else {
      this.store.set('device_id', id);
    }
  }

  setDeviceToken(token: string | null): void {
    if (token === null) {
      this.store.delete('device_token');
    } else {
      this.store.set('device_token', token);
    }
  }

  clear(): void {
    this.store.clear();
  }
}
```

#### `mock-transport.ts`
```typescript
import type { LogTransport, TransportOptions } from '../interfaces';

/**
 * Mock transport for testing
 */
export class MockTransport implements LogTransport {
  public requests: Array<{
    endpoint: string;
    data: unknown;
    options?: TransportOptions;
  }> = [];

  public shouldFail = false;
  public failureError = new Error('Network error');

  async send(
    endpoint: string,
    data: unknown,
    options?: TransportOptions
  ): Promise<void> {
    this.requests.push({ endpoint, data, options });

    if (this.shouldFail) {
      throw this.failureError;
    }

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 10));
  }

  // Test helpers
  reset(): void {
    this.requests = [];
    this.shouldFail = false;
  }

  getLastRequest() {
    return this.requests[this.requests.length - 1];
  }

  getRequestCount(): number {
    return this.requests.length;
  }
}
```

#### `test-logger-factory.ts`
```typescript
import { createLogger } from '../shared-logger';
import { MockStorage } from './mock-storage';
import { MockTransport } from './mock-transport';
import { SimpleEventEmitter } from '../implementations/event-emitter';
import type { LoggerConfig } from '../interfaces';

/**
 * Create logger for testing with mocks
 */
export function createTestLogger(configOverrides?: Partial<LoggerConfig>) {
  const storage = new MockStorage();
  const transport = new MockTransport();
  const eventEmitter = new SimpleEventEmitter();

  const config: LoggerConfig = {
    level: 'debug',
    enableConsole: false, // Disable console in tests
    maxBufferSize: 50,
    flushInterval: 30000,
    apiBaseURL: 'http://test-api.local',
    endpoints: {
      logsBatch: '/api/logs',
    },
    ...configOverrides,
  };

  const logger = createLogger(config, storage, transport, eventEmitter);

  return {
    logger,
    mocks: { storage, transport, eventEmitter },
  };
}
```

---

## Phase 2: Unit Tests (Day 2-3)

### Step 2.1: Setup Testing Infrastructure

Install dependencies:
```bash
cd /mnt/g/khoirul/signate/player-vite
npm install -D vitest @vitest/ui @testing-library/react @testing-library/user-event
```

Create `vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
});
```

### Step 2.2: Write Unit Tests

Create `/mnt/g/khoirul/signate/player-vite/src/shared/logger/__tests__/shared-logger.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createTestLogger } from '../test-helpers/test-logger-factory';
import type { Logger } from '../interfaces';

describe('SharedLogger', () => {
  let logger: Logger;
  let mocks: ReturnType<typeof createTestLogger>['mocks'];

  beforeEach(() => {
    const { logger: testLogger, mocks: testMocks } = createTestLogger();
    logger = testLogger;
    mocks = testMocks;

    // Set device_id for tests
    mocks.storage.setDeviceId('7650');
  });

  afterEach(() => {
    mocks.transport.reset();
    mocks.storage.clear();
  });

  describe('Log Buffering', () => {
    it('should buffer logs', () => {
      logger.log('Test message 1');
      logger.info('Test message 2');

      const buffer = logger.getBuffer();
      expect(buffer).toHaveLength(2);
      expect(buffer[0].message).toContain('Test message 1');
      expect(buffer[1].message).toContain('Test message 2');
    });

    it('should respect maxBufferSize', () => {
      const { logger: limitedLogger } = createTestLogger({
        maxBufferSize: 10,
      });

      for (let i = 0; i < 20; i++) {
        limitedLogger.log(`Message ${i}`);
      }

      const buffer = limitedLogger.getBuffer();
      expect(buffer).toHaveLength(10);
      expect(buffer[0].message).toContain('Message 10'); // Oldest kept
    });

    it('should clear buffer after successful flush', async () => {
      logger.log('Test message');
      expect(logger.getBuffer()).toHaveLength(1);

      await logger.flush();

      expect(logger.getBuffer()).toHaveLength(0);
    });
  });

  describe('Log Levels', () => {
    it('should filter logs by level', () => {
      const { logger: warnLogger } = createTestLogger({ level: 'warn' });

      warnLogger.debug('Debug message');
      warnLogger.info('Info message');
      warnLogger.warn('Warning message');
      warnLogger.error('Error message');

      const buffer = warnLogger.getBuffer();
      expect(buffer).toHaveLength(2); // Only warn and error
      expect(buffer[0].level).toBe('warn');
      expect(buffer[1].level).toBe('error');
    });

    it('should allow changing log level', () => {
      logger.setLevel('error');

      logger.info('Should be ignored');
      logger.error('Should be logged');

      const buffer = logger.getBuffer();
      expect(buffer).toHaveLength(1);
      expect(buffer[0].level).toBe('error');
    });
  });

  describe('Backend Sync', () => {
    it('should send logs to backend on flush', async () => {
      logger.log('Test log 1');
      logger.info('Test log 2');

      await logger.flush();

      expect(mocks.transport.getRequestCount()).toBe(1);

      const request = mocks.transport.getLastRequest();
      expect(request.endpoint).toBe('http://test-api.local/api/logs');
      expect(request.data).toMatchObject({
        device_id: 7650,
        logs: expect.arrayContaining([
          expect.objectContaining({ message: expect.stringContaining('Test log 1') }),
          expect.objectContaining({ message: expect.stringContaining('Test log 2') }),
        ]),
      });
    });

    it('should not send logs if device_id is missing', async () => {
      mocks.storage.setDeviceId(null);
      logger.log('Test log');

      await logger.flush();

      expect(mocks.transport.getRequestCount()).toBe(0);
    });

    it('should handle network errors gracefully', async () => {
      mocks.transport.shouldFail = true;
      logger.log('Test log');

      await logger.flush(); // Should not throw

      expect(mocks.transport.getRequestCount()).toBe(1);
      // Logs should be added back to buffer on failure
      expect(logger.getBuffer()).toHaveLength(1);
    });
  });

  describe('Sensitive Data Redaction', () => {
    it('should redact device_token', () => {
      const sensitiveData = {
        device_token: 'secret-token-12345678',
        message: 'Login successful',
      };

      logger.info('Auth', sensitiveData);

      const buffer = logger.getBuffer();
      expect(buffer[0].message).not.toContain('secret-token-12345678');
      expect(buffer[0].message).toContain('***REDACTED***');
    });

    it('should partially reveal long tokens', () => {
      const longToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';

      logger.info('JWT', { jwt: longToken });

      const buffer = logger.getBuffer();
      expect(buffer[0].message).toContain('eyJh...R8U');
      expect(buffer[0].message).not.toContain(longToken);
    });

    it('should redact multiple sensitive fields', () => {
      const data = {
        password: 'mypassword123',
        api_key: 'sk_live_abc123',
        username: 'john_doe', // Should not be redacted
      };

      logger.info('User data', data);

      const buffer = logger.getBuffer();
      expect(buffer[0].message).not.toContain('mypassword123');
      expect(buffer[0].message).not.toContain('sk_live_abc123');
      expect(buffer[0].message).toContain('john_doe'); // Public field
    });
  });

  describe('Event Emitter', () => {
    it('should emit flush:success event', async () => {
      const successCallback = vi.fn();
      mocks.eventEmitter.on('flush:success', successCallback);

      logger.log('Test log');
      await logger.flush();

      expect(successCallback).toHaveBeenCalledWith(
        expect.objectContaining({ count: 1 })
      );
    });

    it('should emit flush:error event on failure', async () => {
      const errorCallback = vi.fn();
      mocks.eventEmitter.on('flush:error', errorCallback);

      mocks.transport.shouldFail = true;
      logger.log('Test log');
      await logger.flush();

      expect(errorCallback).toHaveBeenCalledWith(
        expect.objectContaining({ error: expect.any(String) })
      );
    });
  });

  describe('Smart Object Formatting', () => {
    it('should format arrays concisely', () => {
      const largeArray = Array.from({ length: 100 }, (_, i) => i);

      logger.log('Large array', largeArray);

      const buffer = logger.getBuffer();
      expect(buffer[0].message).toContain('Array(100)');
      expect(buffer[0].message).not.toContain(JSON.stringify(largeArray));
    });

    it('should format objects with summaries', () => {
      const obj = {
        id: 123,
        name: 'Test Device',
        status: 'active',
        metadata: { /* large object */ },
      };

      logger.log('Device info', obj);

      const buffer = logger.getBuffer();
      expect(buffer[0].message).toContain('id: 123');
      expect(buffer[0].message).toContain('name: Test Device');
      expect(buffer[0].message).toContain('status: active');
    });
  });
});
```

Run tests:
```bash
npm run test
# or
npm run test:ui  # For Vitest UI
# or
npm run test:coverage  # For coverage report
```

---

## Phase 3: Integration with Existing Code (Day 3-4)

### Step 3.1: Update Config

Add to `config.types.ts`:

```typescript
export interface ApiConfig {
  baseURL: string;
  wsBaseURL: string;
  timeout: number;
  endpoints: {
    logsBatch: string;
    logsDevice: (deviceId: number) => string;
    connectionLogs: (deviceId: number) => string;
  };
}
```

Update `config/index.ts`:

```typescript
api: {
  baseURL: getEnvString('VITE_API_BASE_URL', 'http://192.168.5.12:8001'),
  wsBaseURL: getEnvString('VITE_WS_BASE_URL', 'ws://192.168.5.12:8001'),
  timeout: getEnvNumber('VITE_API_TIMEOUT', 30000),
  endpoints: {
    logsBatch: '/api/client/logs/batch',
    logsDevice: (deviceId: number) => `/devices/${deviceId}/logs`,
    connectionLogs: (deviceId: number) => `/devices/${deviceId}/connection-logs`,
  },
},
```

### Step 3.2: Update Logger Creation

In `shared/logger/index.ts`:

```typescript
import { createLogger } from './shared-logger';
import { config } from '@shared/config';

// Create singleton with production config
export const SharedLogger = createLogger({
  level: config.log.level,
  enableConsole: config.log.enableConsole,
  maxBufferSize: config.device.logBufferSize,
  flushInterval: config.device.logSendInterval,
  apiBaseURL: config.api.baseURL,
  endpoints: {
    logsBatch: config.api.endpoints.logsBatch,
  },
});

export { LogNamespace } from './shared-logger';
export type { LogLevel, LogEntry, Logger } from './interfaces';
export { createTestLogger } from './test-helpers/test-logger-factory';
```

### Step 3.3: No Breaking Changes!

The existing code continues to work:

```typescript
// Still works!
import { SharedLogger } from '@shared/logger';

SharedLogger.log('[Shell:Bootstrap]', 'Device activated');
SharedLogger.error('[API]', 'Failed to fetch', error);
```

---

## Phase 4: Add Plugin System (Day 4-5)

### Step 4.1: Plugin Interface

Add to `interfaces.ts`:

```typescript
export interface LoggerPlugin {
  name: string;
  version: string;
  install(logger: Logger): void;
  uninstall?(logger: Logger): void;
}
```

### Step 4.2: Update Logger to Support Plugins

```typescript
class SharedLoggerClass implements Logger {
  private plugins: LoggerPlugin[] = [];

  use(plugin: LoggerPlugin): void {
    if (this.plugins.some(p => p.name === plugin.name)) {
      throw new Error(`Plugin ${plugin.name} already installed`);
    }

    plugin.install(this);
    this.plugins.push(plugin);

    this.originalConsole.log(`[SharedLogger] Plugin installed: ${plugin.name} v${plugin.version}`);
  }

  removePlugin(name: string): void {
    const plugin = this.plugins.find(p => p.name === name);
    if (!plugin) return;

    plugin.uninstall?.(this);
    this.plugins = this.plugins.filter(p => p.name !== name);

    this.originalConsole.log(`[SharedLogger] Plugin removed: ${name}`);
  }
}
```

### Step 4.3: Create Sample Plugins

#### Compression Plugin

```typescript
import type { LoggerPlugin, Logger } from '../interfaces';
import pako from 'pako'; // npm install pako

export class CompressionPlugin implements LoggerPlugin {
  name = 'compression';
  version = '1.0.0';

  install(logger: Logger): void {
    const originalFlush = logger.flush.bind(logger);

    logger.flush = async () => {
      const logs = logger.getBuffer();

      if (logs.length === 0) return;

      // Compress logs
      const compressed = pako.gzip(JSON.stringify(logs));

      // Send compressed (override transport temporarily)
      // ... implementation
    };
  }

  uninstall(logger: Logger): void {
    // Restore original flush
  }
}
```

#### Analytics Plugin

```typescript
export class AnalyticsPlugin implements LoggerPlugin {
  name = 'analytics';
  version = '1.0.0';

  install(logger: Logger): void {
    const originalError = logger.error.bind(logger);

    logger.error = (...args: unknown[]) => {
      // Track error in analytics
      this.trackError(args);

      // Call original
      originalError(...args);
    };
  }

  private trackError(args: unknown[]): void {
    // Send to Google Analytics, Mixpanel, etc.
    console.log('[Analytics] Error tracked:', args);
  }
}
```

#### Sampling Plugin

```typescript
export class SamplingPlugin implements LoggerPlugin {
  name = 'sampling';
  version = '1.0.0';

  constructor(private sampleRate: number = 0.1) {}

  install(logger: Logger): void {
    const originalLog = logger.log.bind(logger);

    logger.log = (...args: unknown[]) => {
      // Sample only 10% of logs
      if (Math.random() <= this.sampleRate) {
        originalLog(...args);
      }
    };
  }
}
```

---

## Migration Checklist

### Pre-Migration
- [ ] Review current logger usage across codebase
- [ ] Identify all log call sites
- [ ] Document any custom log patterns
- [ ] Backup current implementation

### Phase 1: DI Implementation
- [ ] Create interfaces (`interfaces.ts`)
- [ ] Implement concrete classes (LocalStorage, FetchTransport, etc.)
- [ ] Refactor SharedLogger to use DI
- [ ] Create factory function
- [ ] Create test helpers (MockStorage, MockTransport)
- [ ] Test manually (no breaking changes)

### Phase 2: Testing
- [ ] Setup Vitest
- [ ] Write unit tests for buffering
- [ ] Write unit tests for redaction
- [ ] Write unit tests for level filtering
- [ ] Write unit tests for backend sync
- [ ] Write tests for event emitter
- [ ] Achieve 80%+ coverage

### Phase 3: Integration
- [ ] Update config types
- [ ] Update config values
- [ ] Update logger exports
- [ ] Test in development
- [ ] Test in staging
- [ ] Verify no breaking changes

### Phase 4: Plugins (Optional)
- [ ] Add plugin interface
- [ ] Update logger to support plugins
- [ ] Create compression plugin
- [ ] Create analytics plugin
- [ ] Create sampling plugin
- [ ] Document plugin API

### Post-Migration
- [ ] Update documentation
- [ ] Update README
- [ ] Create migration guide for team
- [ ] Monitor logs in production
- [ ] Collect feedback

---

## Validation Steps

After each phase, validate:

1. **No Breaking Changes**
   ```typescript
   // This should still work
   SharedLogger.log('[Test]', 'Message');
   ```

2. **Tests Pass**
   ```bash
   npm run test
   ```

3. **Type Safety**
   ```bash
   npm run type-check
   ```

4. **Console Output**
   - Open browser DevTools
   - Verify logs still appear with colors
   - Verify namespaces are styled correctly

5. **Backend Sync**
   - Check network tab
   - Verify POST to `/api/client/logs/batch`
   - Verify payload structure

---

## Rollback Plan

If issues occur:

1. **Revert to v2.0**
   ```bash
   git checkout HEAD^ -- src/shared/logger/
   ```

2. **Keep tests** (they'll still be valuable)

3. **Document issues** for future attempt

---

## Success Metrics

After migration:

- [ ] 80%+ test coverage
- [ ] No production errors
- [ ] Same or better performance
- [ ] Easier to test new features
- [ ] Plugin system functional
- [ ] Documentation complete

---

## Timeline

**Day 1**: DI implementation (interfaces, concrete classes, refactor)
**Day 2**: Testing setup and unit tests
**Day 3**: Integration and validation
**Day 4**: Plugin system (optional)
**Day 5**: Documentation and deployment

**Total**: 3-5 days (depending on scope)

---

## Support

If you need help during migration:

1. Check this guide
2. Review code examples
3. Run tests to validate changes
4. Check original implementation for reference

Good luck! 🚀
