/**
 * Console Log Streamer
 *
 * Intercepts browser console logs and streams them to backend in real-time
 * - Buffers up to 1000 logs (FIFO)
 * - Uploads in batches (every 5s or when threshold reached)
 * - Sends all buffered logs immediately when CMS subscribes
 * - NO database storage (live streaming only)
 */

interface ConsoleLog {
  level: 'log' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: string;
  stack?: string;
}

interface ConsoleStreamerConfig {
  deviceId: number;
  apiUrl: string;
  maxBufferSize?: number;
  uploadInterval?: number;
  uploadThreshold?: number;
  enabled?: boolean;
}

export class ConsoleStreamer {
  private deviceId: number;
  private apiUrl: string;
  private maxBufferSize: number;
  private uploadInterval: number;
  private uploadThreshold: number;
  private enabled: boolean;

  private buffer: ConsoleLog[] = [];
  private uploadTimer: number | null = null;
  private isUploading = false;

  // Original console methods
  private originalConsole = {
    log: console.log,
    info: console.info,
    warn: console.warn,
    error: console.error,
  };

  constructor(config: ConsoleStreamerConfig) {
    this.deviceId = config.deviceId;
    this.apiUrl = config.apiUrl;
    this.maxBufferSize = config.maxBufferSize ?? 1000; // Max 1000 logs
    this.uploadInterval = config.uploadInterval ?? 5000; // Upload every 5s
    this.uploadThreshold = config.uploadThreshold ?? 100; // Upload when 100 logs buffered
    this.enabled = config.enabled ?? true;

    if (this.enabled) {
      this.interceptConsole();
      this.startUploadTimer();
      this.log('info', '[ConsoleStreamer] Initialized and intercepting console logs');
    }
  }

  /**
   * Intercept native console methods
   */
  private interceptConsole(): void {
    const self = this;

    // Intercept console.log
    console.log = function (...args: any[]) {
      self.originalConsole.log.apply(console, args);
      self.captureLog('log', args);
    };

    // Intercept console.info
    console.info = function (...args: any[]) {
      self.originalConsole.info.apply(console, args);
      self.captureLog('info', args);
    };

    // Intercept console.warn
    console.warn = function (...args: any[]) {
      self.originalConsole.warn.apply(console, args);
      self.captureLog('warn', args);
    };

    // Intercept console.error
    console.error = function (...args: any[]) {
      self.originalConsole.error.apply(console, args);
      self.captureLog('error', args);
    };

    // Intercept unhandled errors
    window.addEventListener('error', (event) => {
      self.captureLog('error', [event.message], event.error?.stack);
    });

    // Intercept unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      self.captureLog('error', [`Unhandled Promise Rejection: ${event.reason}`]);
    });
  }

  /**
   * Capture console log entry
   */
  private captureLog(level: ConsoleLog['level'], args: any[], stack?: string): void {
    if (!this.enabled) return;

    // Convert arguments to string
    const message = args
      .map((arg) => {
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg, null, 2);
          } catch {
            return String(arg);
          }
        }
        return String(arg);
      })
      .join(' ');

    // Create log entry
    const logEntry: ConsoleLog = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...(stack && { stack }),
    };

    // Add to buffer (FIFO - remove oldest if full)
    if (this.buffer.length >= this.maxBufferSize) {
      this.buffer.shift(); // Remove oldest
    }
    this.buffer.push(logEntry);

    // Upload immediately if threshold reached
    if (this.buffer.length >= this.uploadThreshold) {
      this.uploadLogs();
    }
  }

  /**
   * Start periodic upload timer
   */
  private startUploadTimer(): void {
    this.uploadTimer = window.setInterval(() => {
      if (this.buffer.length > 0) {
        this.uploadLogs();
      }
    }, this.uploadInterval);
  }

  /**
   * Stop upload timer
   */
  private stopUploadTimer(): void {
    if (this.uploadTimer !== null) {
      clearInterval(this.uploadTimer);
      this.uploadTimer = null;
    }
  }

  /**
   * Upload buffered logs to backend
   */
  private async uploadLogs(): Promise<void> {
    if (this.isUploading || this.buffer.length === 0) return;

    this.isUploading = true;

    // Take all buffered logs
    const logsToUpload = [...this.buffer];
    this.buffer = []; // Clear buffer

    try {
      const response = await fetch(
        `${this.apiUrl}/api/v1/devices/${this.deviceId}/console/upload`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(logsToUpload),
        }
      );

      if (!response.ok) {
        // Re-add to buffer if upload failed (keep last maxBufferSize)
        this.buffer = [...logsToUpload, ...this.buffer].slice(-this.maxBufferSize);
        this.log('error', `[ConsoleStreamer] Upload failed: ${response.status} ${response.statusText}`);
      } else {
        this.log('info', `[ConsoleStreamer] Uploaded ${logsToUpload.length} logs successfully`);
      }
    } catch (error) {
      // Re-add to buffer on network error
      this.buffer = [...logsToUpload, ...this.buffer].slice(-this.maxBufferSize);
      this.log('error', `[ConsoleStreamer] Upload error: ${error}`);
    } finally {
      this.isUploading = false;
    }
  }

  /**
   * Force immediate upload of all buffered logs
   * Called when CMS opens console modal
   */
  public async flushLogs(): Promise<void> {
    this.log('info', `[ConsoleStreamer] Flushing ${this.buffer.length} buffered logs`);
    await this.uploadLogs();
  }

  /**
   * Get current buffer size
   */
  public getBufferSize(): number {
    return this.buffer.length;
  }

  /**
   * Enable/disable console streaming
   */
  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (enabled) {
      this.log('info', '[ConsoleStreamer] Enabled');
    } else {
      this.log('info', '[ConsoleStreamer] Disabled');
    }
  }

  /**
   * Log using original console (bypass interception)
   */
  private log(level: 'log' | 'info' | 'warn' | 'error', ...args: any[]): void {
    this.originalConsole[level].apply(console, args);
  }

  /**
   * Restore original console methods and cleanup
   */
  public destroy(): void {
    this.stopUploadTimer();

    // Flush remaining logs
    if (this.buffer.length > 0) {
      this.uploadLogs();
    }

    // Restore original console
    console.log = this.originalConsole.log;
    console.info = this.originalConsole.info;
    console.warn = this.originalConsole.warn;
    console.error = this.originalConsole.error;

    this.log('info', '[ConsoleStreamer] Destroyed and console restored');
  }
}

// Singleton instance
let consoleStreamerInstance: ConsoleStreamer | null = null;

/**
 * Initialize global console streamer
 */
export function initConsoleStreamer(config: ConsoleStreamerConfig): ConsoleStreamer {
  if (consoleStreamerInstance) {
    console.warn('[ConsoleStreamer] Already initialized, destroying previous instance');
    consoleStreamerInstance.destroy();
  }

  consoleStreamerInstance = new ConsoleStreamer(config);
  return consoleStreamerInstance;
}

/**
 * Get console streamer instance
 */
export function getConsoleStreamer(): ConsoleStreamer | null {
  return consoleStreamerInstance;
}

/**
 * Destroy console streamer
 */
export function destroyConsoleStreamer(): void {
  if (consoleStreamerInstance) {
    consoleStreamerInstance.destroy();
    consoleStreamerInstance = null;
  }
}
