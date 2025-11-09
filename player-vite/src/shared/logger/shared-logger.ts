/**
 * Shared Logger
 * Centralized logging with levels, filtering, and backend sync
 *
 * @features
 * - Multiple log levels (debug, log, info, warn, error)
 * - Enable/disable logging via config
 * - Automatic backend sync for errors
 * - Console passthrough for development
 * - Structured logging with timestamps
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import type { LogLevel, LogEntry, Logger } from './logger.types';

// Log levels (higher number = more important)
const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  log: 1,
  info: 2,
  warn: 3,
  error: 4,
  silent: 999,
};

/**
 * Shared Logger Class
 * Singleton pattern for centralized logging
 */
class SharedLoggerClass implements Logger {
  private currentLevel: number;
  private enabled: boolean;
  private logBuffer: LogEntry[] = [];
  private readonly maxBufferSize: number;
  private flushInterval: number | null = null;

  // Store original console for passthrough
  private originalConsole = {
    debug: console.debug.bind(console),
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
  };

  constructor() {
    // Initialize from config
    this.currentLevel = LOG_LEVELS[config.log.level];
    this.enabled = config.log.enableConsole;
    this.maxBufferSize = config.device.logBufferSize;

    // Start periodic flush
    this.startPeriodicFlush();

    this.originalConsole.log('[SharedLogger] Initialized - Level:', config.log.level);
  }

  /**
   * Check if log level should be displayed
   */
  private shouldLog(level: LogLevel): boolean {
    if (!this.enabled) return false;
    return LOG_LEVELS[level] >= this.currentLevel;
  }

  /**
   * Format log arguments to string
   */
  private formatArgs(args: unknown[]): string {
    return args
      .map((arg) => {
        if (typeof arg === 'object' && arg !== null) {
          try {
            return JSON.stringify(arg, null, 2);
          } catch (e) {
            return String(arg);
          }
        }
        return String(arg);
      })
      .join(' ');
  }

  /**
   * Add log entry to buffer
   */
  private bufferLog(level: LogLevel, message: string): void {
    this.logBuffer.push({
      level,
      message,
      timestamp: new Date().toISOString(),
      source: 'player',
    });

    // Keep buffer size manageable
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
    }

    // Auto-send errors to backend
    if (level === 'error') {
      void this.flush();
    }
  }

  /**
   * Send buffered logs to backend
   */
  async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const deviceId = localStorage.getItem('device_id');
    if (!deviceId) return;

    const logsToSend = [...this.logBuffer];
    this.logBuffer = []; // Clear buffer

    try {
      const response = await fetch(`${config.api.baseURL}/api/client/logs/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('device_token') || ''}`,
        },
        body: JSON.stringify({
          device_id: parseInt(deviceId, 10),
          logs: logsToSend,
        }),
      });

      if (!response.ok) {
        // Silent fail in dev mode - backend might not be running
        if (config.debug.debugMode) {
          this.originalConsole.warn('[SharedLogger] Failed to send logs:', response.statusText);
        }
      }
    } catch (error) {
      // Silent fail - backend might not be available (development mode)
      // Only log in debug mode to avoid console spam
      if (config.debug.debugMode) {
        this.originalConsole.warn('[SharedLogger] Backend unavailable, logs not sent');
      }
    }
  }

  /**
   * Create log method for specific level
   */
  private createLogMethod(level: LogLevel): (...args: unknown[]) => void {
    return (...args: unknown[]) => {
      // Always passthrough to original console (for development)
      // Skip 'silent' level as it has no console method
      if (level !== 'silent' && this.originalConsole[level]) {
        this.originalConsole[level](...args);
      }

      // Check if should log at this level
      if (!this.shouldLog(level)) return;

      // Format and buffer
      const message = this.formatArgs(args);
      this.bufferLog(level, message);
    };
  }

  /**
   * Start periodic log flush
   */
  private startPeriodicFlush(): void {
    if (this.flushInterval !== null) {
      clearInterval(this.flushInterval);
    }

    this.flushInterval = window.setInterval(() => {
      if (this.logBuffer.length > 0) {
        void this.flush();
      }
    }, config.device.logSendInterval);
  }

  /**
   * Stop periodic log flush
   */
  private stopPeriodicFlush(): void {
    if (this.flushInterval !== null) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
  }

  // Public API
  debug = this.createLogMethod('debug');
  log = this.createLogMethod('log');
  info = this.createLogMethod('info');
  warn = this.createLogMethod('warn');
  error = this.createLogMethod('error');

  /**
   * Set minimum log level
   */
  setLevel(level: LogLevel): void {
    if (LOG_LEVELS[level] === undefined) {
      this.originalConsole.warn('[SharedLogger] Invalid log level:', level);
      return;
    }
    this.currentLevel = LOG_LEVELS[level];
    this.originalConsole.log('[SharedLogger] Log level set to:', level);

    // Save to localStorage
    localStorage.setItem('LOG_LEVEL', level);
  }

  /**
   * Get current log level
   */
  getLevel(): LogLevel {
    for (const [name, value] of Object.entries(LOG_LEVELS)) {
      if (value === this.currentLevel) return name as LogLevel;
    }
    return 'log';
  }

  /**
   * Enable logging
   */
  enable(): void {
    this.enabled = true;
    localStorage.setItem('LOGGING_ENABLED', 'true');
    this.originalConsole.log('[SharedLogger] Logging enabled');
  }

  /**
   * Disable logging (only original console will work)
   */
  disable(): void {
    this.enabled = false;
    localStorage.setItem('LOGGING_ENABLED', 'false');
    this.originalConsole.log('[SharedLogger] Logging disabled');
  }

  /**
   * Check if logging is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Get buffered logs
   */
  getBuffer(): LogEntry[] {
    return [...this.logBuffer];
  }

  /**
   * Clear log buffer
   */
  clearBuffer(): void {
    this.logBuffer = [];
    this.originalConsole.log('[SharedLogger] Buffer cleared');
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopPeriodicFlush();
    this.clearBuffer();
  }
}

// Export singleton instance
export const SharedLogger = new SharedLoggerClass();
