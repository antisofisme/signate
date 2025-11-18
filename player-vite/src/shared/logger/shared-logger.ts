/**
 * Shared Logger
 * Centralized logging with levels, filtering, and backend sync
 *
 * @features
 * - Multiple log levels (debug, log, info, warn, error)
 * - Emoji prefixes for visual distinction
 * - Namespace/category system for log grouping
 * - Console.group support for collapsible errors
 * - Smart object logging (summaries, not full dumps)
 * - Production/development mode support
 * - Enable/disable logging via config
 * - Automatic backend sync for errors
 * - Console passthrough for development
 * - Structured logging with timestamps
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import type { LogLevel, LogEntry, Logger } from './logger.types';

// Emoji prefixes for log levels (visual distinction)
const LOG_EMOJIS: Record<LogLevel, string> = {
  debug: '🔍',
  log: 'ℹ️',
  info: 'ℹ️',
  warn: '⚠️',
  error: '❌',
  silent: '',
};

// Success emoji for positive confirmations
const SUCCESS_EMOJI = '✅';

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
 * Namespace definitions for log categorization
 * Hierarchical structure for better organization
 */
export const LogNamespace = {
  SHELL: {
    BOOTSTRAP: '[Shell:Bootstrap]',
    ACTIVATION: '[Shell:Activation]',
    REGISTRATION: '[Shell:Registration]',
    NETWORK: '[Shell:Network]',
  },
  PLAYER: {
    VIDEOJS: '[Player:VideoJS]',
    PLAYLIST: '[Player:Playlist]',
    COMMANDS: '[Player:Commands]',
    CACHE: '[Player:Cache]',
    HEALTH: '[Player:Health]',
  },
  NETWORK: {
    HEARTBEAT: '[Network:Heartbeat]',
    SPEEDTEST: '[Network:SpeedTest]',
    CONNECTION: '[Network:Connection]',
  },
  DEVICE: {
    INFO: '[DeviceInfo]',
    FINGERPRINT: '[DeviceFingerprint]',
  },
  UI: {
    TOAST: '[Toast]',
    MODAL: '[Modal]',
    POPUP: '[Popup]',
  },
  STORAGE: {
    INDEXEDDB: '[Storage:IndexedDB]',
    CACHE: '[Storage:Cache]',
  },
} as const;

/**
 * Color scheme for namespaces (console CSS styling)
 * Maps namespace categories to colors for better visual distinction
 */
const NAMESPACE_COLORS: Record<string, string> = {
  // Shell (blue tones)
  Shell: 'color: #3b82f6; font-weight: bold',

  // Player (purple tones)
  Player: 'color: #a855f7; font-weight: bold',

  // Network (green tones)
  Network: 'color: #10b981; font-weight: bold',

  // Device (cyan tones)
  Device: 'color: #06b6d4; font-weight: bold',
  DeviceInfo: 'color: #06b6d4; font-weight: bold',
  DeviceFingerprint: 'color: #06b6d4; font-weight: bold',

  // UI (orange tones)
  Toast: 'color: #f97316; font-weight: bold',
  Modal: 'color: #f97316; font-weight: bold',
  Popup: 'color: #f97316; font-weight: bold',

  // Storage (yellow tones)
  Storage: 'color: #eab308; font-weight: bold',

  // Default
  default: 'color: #64748b; font-weight: bold',
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
   * Redact sensitive data from objects before logging
   * This prevents credential leakage in console logs
   */
  private redactSensitiveData(obj: any): any {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj !== 'object') return obj;

    // Handle arrays - redact each item
    if (Array.isArray(obj)) {
      return obj.map(item => this.redactSensitiveData(item));
    }

    // List of sensitive field names to redact
    const sensitiveFields = [
      'device_token',
      'token',
      'access_token',
      'refresh_token',
      'jwt',
      'password',
      'secret',
      'api_key',
      'apiKey',
      'authorization',
    ];

    // Create new object with redacted fields
    const redacted: any = {};
    for (const key in obj) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveFields.some(field => lowerKey.includes(field.toLowerCase()));

      if (isSensitive) {
        // Redact but show first/last 4 chars if string is long enough
        const value = obj[key];
        if (typeof value === 'string' && value.length > 16) {
          redacted[key] = `${value.substring(0, 4)}...${value.substring(value.length - 4)}`;
        } else {
          redacted[key] = '***REDACTED***';
        }
      } else if (typeof obj[key] === 'object') {
        // Recursively redact nested objects
        redacted[key] = this.redactSensitiveData(obj[key]);
      } else {
        redacted[key] = obj[key];
      }
    }

    return redacted;
  }

  /**
   * Smart object formatter - creates summaries instead of full dumps
   */
  private formatObject(obj: any): string {
    if (obj === null || obj === undefined) return String(obj);

    // Handle arrays
    if (Array.isArray(obj)) {
      if (obj.length === 0) return '[]';
      if (obj.length <= 3) return JSON.stringify(obj);
      return `Array(${obj.length}) [${obj.slice(0, 2).map(String).join(', ')}, ...]`;
    }

    // Handle common object types with smart summaries
    if (obj instanceof Error) {
      return `${obj.name}: ${obj.message}`;
    }

    if (obj instanceof Date) {
      return obj.toISOString();
    }

    // Handle plain objects - show only key info
    if (typeof obj === 'object') {
      const keys = Object.keys(obj);
      if (keys.length === 0) return '{}';

      // For objects with id, name, status - show summary
      const summary: string[] = [];
      if ('id' in obj) summary.push(`id: ${obj.id}`);
      if ('name' in obj) summary.push(`name: ${obj.name}`);
      if ('status' in obj) summary.push(`status: ${obj.status}`);
      if ('type' in obj) summary.push(`type: ${obj.type}`);

      if (summary.length > 0) {
        return `{${summary.join(', ')}}`;
      }

      // Otherwise show key count
      return `Object{${keys.slice(0, 3).join(', ')}${keys.length > 3 ? ', ...' : ''}}`;
    }

    return String(obj);
  }

  /**
   * Format log arguments to string with smart object handling
   * Automatically redacts sensitive data before formatting
   */
  private formatArgs(args: unknown[]): string {
    return args
      .map((arg) => {
        if (typeof arg === 'object' && arg !== null) {
          try {
            // Redact sensitive data first, then format
            const redacted = this.redactSensitiveData(arg);
            return this.formatObject(redacted);
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
   * Extract namespace from first argument and get its color
   */
  private getNamespaceColor(args: unknown[]): { namespace: string | null; color: string } {
    if (args.length === 0) return { namespace: null, color: NAMESPACE_COLORS.default };

    const firstArg = args[0];
    if (typeof firstArg !== 'string') return { namespace: null, color: NAMESPACE_COLORS.default };

    // Check if first arg matches namespace pattern [Category:Name] or [Name]
    const namespaceMatch = firstArg.match(/^\[([^\]]+)\]/);
    if (!namespaceMatch) return { namespace: null, color: NAMESPACE_COLORS.default };

    const namespace = namespaceMatch[1];

    // Extract category (before colon if exists)
    const category = namespace.includes(':') ? namespace.split(':')[0] : namespace;

    // Get color for category
    const color = NAMESPACE_COLORS[category] || NAMESPACE_COLORS[namespace] || NAMESPACE_COLORS.default;

    return { namespace: firstArg, color };
  }

  /**
   * Create log method for specific level with emoji prefix and colored namespace
   * Automatically redacts sensitive data before console output
   */
  private createLogMethod(level: LogLevel): (...args: unknown[]) => void {
    return (...args: unknown[]) => {
      // Get emoji prefix
      const emoji = LOG_EMOJIS[level];

      // Redact sensitive data from all arguments before console output
      const redactedArgs = args.map(arg =>
        (typeof arg === 'object' && arg !== null) ? this.redactSensitiveData(arg) : arg
      );

      // For errors, use console.group for collapsible stack traces
      if (level === 'error' && this.originalConsole[level]) {
        this.logErrorWithGroup(redactedArgs);
      } else {
        // Check for namespace in first argument
        const { namespace, color } = this.getNamespaceColor(redactedArgs);

        // Always passthrough to original console with emoji prefix and colored namespace
        if (level !== 'silent' && this.originalConsole[level]) {
          if (namespace) {
            // First arg is namespace - colorize it, then reset style for rest
            this.originalConsole[level](emoji, '%c' + namespace + '%c', color, '', ...redactedArgs.slice(1));
          } else {
            // No namespace - regular log
            this.originalConsole[level](emoji, ...redactedArgs);
          }
        }
      }

      // Check if should log at this level
      if (!this.shouldLog(level)) return;

      // Format and buffer (formatArgs already redacts, but using original args for consistency)
      const message = emoji + ' ' + this.formatArgs(args);
      this.bufferLog(level, message);
    };
  }

  /**
   * Log error with collapsible console.group
   */
  private logErrorWithGroup(args: unknown[]): void {
    const emoji = LOG_EMOJIS.error;

    // Check if first arg is Error object
    const hasError = args.some((arg) => arg instanceof Error);

    if (hasError) {
      // Use console.group for collapsible error details
      this.originalConsole.error('%c' + emoji + ' ERROR', 'font-weight: bold; color: #ff4444;', ...args);

      // Find and show stack trace in collapsed group
      args.forEach((arg) => {
        if (arg instanceof Error && arg.stack) {
          console.groupCollapsed('📋 Stack Trace (click to expand)');
          this.originalConsole.error(arg.stack);
          console.groupEnd();
        }
      });
    } else {
      // Regular error log with emoji
      this.originalConsole.error(emoji, ...args);
    }
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
   * Log success message with green checkmark emoji and colored namespace
   * Automatically redacts sensitive data before console output
   * Usage: SharedLogger.success('[Network:Heartbeat]', 'Sent successfully')
   */
  success(...args: unknown[]): void {
    // Redact sensitive data from all arguments before console output
    const redactedArgs = args.map(arg =>
      (typeof arg === 'object' && arg !== null) ? this.redactSensitiveData(arg) : arg
    );

    const { namespace, color } = this.getNamespaceColor(redactedArgs);

    if (this.originalConsole.log) {
      if (namespace) {
        // First arg is namespace - colorize it, then reset style for rest
        this.originalConsole.log(SUCCESS_EMOJI, '%c' + namespace + '%c', color, '', ...redactedArgs.slice(1));
      } else {
        // No namespace - regular log
        this.originalConsole.log(SUCCESS_EMOJI, ...redactedArgs);
      }
    }

    if (!this.shouldLog('info')) return;

    const message = SUCCESS_EMOJI + ' ' + this.formatArgs(args);
    this.bufferLog('info', message);
  }

  /**
   * Log with custom namespace for better categorization
   * Usage: SharedLogger.namespace('[Shell:Bootstrap]', 'Device activated')
   */
  namespace(ns: string, ...args: unknown[]): void {
    this.log(ns, ...args);
  }

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
