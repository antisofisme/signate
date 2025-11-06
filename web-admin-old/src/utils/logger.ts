/**
 * Logger Utility - Environment-based Logging
 *
 * Replaces console.log statements with environment-aware logging
 * - Development: Full logging enabled
 * - Production: Logging disabled (prevents console pollution)
 *
 * Usage:
 *   import logger from '@/utils/logger'
 *   logger.debug('Debug message', data)
 *   logger.info('Info message', data)
 *   logger.warn('Warning message', data)
 *   logger.error('Error message', error)
 */

/**
 * Log level types
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

/**
 * Logger interface
 */
export interface Logger {
  debug: (...args: unknown[]) => void
  info: (...args: unknown[]) => void
  warn: (...args: unknown[]) => void
  error: (...args: unknown[]) => void
  group: (label: string, callback: () => void) => void
  table: (data: unknown) => void
  time: (label: string) => void
  timeEnd: (label: string) => void
}

const isDevelopment: boolean = import.meta.env.DEV

const logger: Logger = {
  /**
   * Debug-level logging (verbose, for development only)
   */
  debug: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.log('[DEBUG]', ...args)
    }
  },

  /**
   * Info-level logging (general information)
   */
  info: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.info('[INFO]', ...args)
    }
  },

  /**
   * Warning-level logging (potential issues)
   */
  warn: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.warn('[WARN]', ...args)
    }
  },

  /**
   * Error-level logging (always logged, even in production)
   */
  error: (...args: unknown[]): void => {
    // Always log errors, even in production
    console.error('[ERROR]', ...args)
  },

  /**
   * Group logging for collapsible logs
   */
  group: (label: string, callback: () => void): void => {
    if (isDevelopment) {
      console.group(label)
      callback()
      console.groupEnd()
    }
  },

  /**
   * Table logging for structured data
   */
  table: (data: unknown): void => {
    if (isDevelopment) {
      console.table(data)
    }
  },

  /**
   * Time logging for performance measurement
   */
  time: (label: string): void => {
    if (isDevelopment) {
      console.time(label)
    }
  },

  /**
   * End time logging
   */
  timeEnd: (label: string): void => {
    if (isDevelopment) {
      console.timeEnd(label)
    }
  }
}

export default logger
