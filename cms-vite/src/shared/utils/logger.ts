/**
 * Production-Safe Logger
 *
 * Features:
 * - Debug logs only in development (tree-shaken in production)
 * - Structured logging with timestamps
 * - No sensitive data in production
 * - Type-safe log levels
 *
 * Usage:
 * ```ts
 * import { logger } from '@/shared/utils/logger';
 *
 * logger.debug('Fetching data', { url, params });
 * logger.info('User logged in', { userId });
 * logger.warn('Rate limit approaching', { remaining: 5 });
 * logger.error('API request failed', error, { endpoint: '/api/users' });
 * ```
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  component?: string;
  action?: string;
  [key: string]: any;
}

class Logger {
  private isDev = import.meta.env.DEV;
  private isProd = import.meta.env.PROD;

  /**
   * Format log message with timestamp and context
   */
  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` | ${JSON.stringify(context)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`;
  }

  /**
   * Debug logs - only in development
   * Automatically tree-shaken in production builds
   */
  debug(message: string, data?: any) {
    if (this.isDev) {
      console.log(`[DEBUG] ${message}`, data || '');
    }
  }

  /**
   * Info logs - shown in all environments
   * Use for important non-error events
   */
  info(message: string, context?: LogContext) {
    if (this.isDev) {
      console.info(this.formatMessage('info', message, context));
    } else {
      // In production, only log without context to avoid data leaks
      console.info(`[INFO] ${message}`);
    }
  }

  /**
   * Warning logs - shown in all environments
   * Use for recoverable issues
   */
  warn(message: string, context?: LogContext) {
    if (this.isDev) {
      console.warn(this.formatMessage('warn', message, context));
    } else {
      // In production, only log without sensitive context
      console.warn(`[WARN] ${message}`);
    }
  }

  /**
   * Error logs - shown in all environments
   * Use for exceptions and failures
   */
  error(message: string, error?: Error | unknown, context?: LogContext) {
    const errorMessage = this.isDev
      ? this.formatMessage('error', message, context)
      : `[ERROR] ${message}`;

    console.error(errorMessage, error || '');

    // In production, you might want to send to error tracking service
    if (this.isProd && error instanceof Error) {
      // TODO: Send to error tracking (Sentry, LogRocket, etc.)
      // trackError(error, { message, ...context });
    }
  }

  /**
   * Group multiple related logs together
   * Only shown in development
   */
  group(label: string, callback: () => void) {
    if (this.isDev) {
      console.group(label);
      callback();
      console.groupEnd();
    }
  }

  /**
   * Log a table of data
   * Only shown in development
   */
  table(data: any) {
    if (this.isDev) {
      console.table(data);
    }
  }

  /**
   * Start a timer
   * Only shown in development
   */
  time(label: string) {
    if (this.isDev) {
      console.time(label);
    }
  }

  /**
   * End a timer and log elapsed time
   * Only shown in development
   */
  timeEnd(label: string) {
    if (this.isDev) {
      console.timeEnd(label);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export type for external use
export type { LogLevel, LogContext };
