/**
 * Error Handler Utility
 * Centralized error handling with consistent logging and optional user notification
 */

import { SharedLogger } from '@shared/logger';
import { SharedToast } from '@shared/ui';

/**
 * Error handler options
 */
export interface ErrorHandlerOptions {
  /** Service/component name for logging context */
  context: string;
  /** Error message for logging */
  message: string;
  /** Show toast notification to user */
  showToast?: boolean;
  /** Toast message (defaults to message) */
  toastMessage?: string;
  /** Rethrow error after handling */
  rethrow?: boolean;
}

/**
 * Handle error with consistent logging and optional user notification
 *
 * @example
 * try {
 *   await riskyOperation();
 * } catch (error) {
 *   handleError(error, {
 *     context: 'PlayerVideoJS',
 *     message: 'Failed to load video',
 *     showToast: true
 *   });
 * }
 */
export function handleError(error: unknown, options: ErrorHandlerOptions): void {
  const { context, message, showToast, toastMessage, rethrow } = options;

  // Log error with context
  SharedLogger.error(`[${context}] ${message}:`, error);

  // Show toast if requested
  if (showToast) {
    SharedToast.error(toastMessage || message);
  }

  // Rethrow if requested
  if (rethrow) {
    throw error;
  }
}

/**
 * Async wrapper for error handling
 * Wraps async function with automatic error handling
 *
 * @example
 * const safeLoad = withErrorHandling(
 *   async () => await loadData(),
 *   {
 *     context: 'DataLoader',
 *     message: 'Failed to load data',
 *     showToast: true
 *   }
 * );
 */
export function withErrorHandling<T>(
  fn: () => Promise<T>,
  options: ErrorHandlerOptions
): () => Promise<T | null> {
  return async () => {
    try {
      return await fn();
    } catch (error) {
      handleError(error, options);
      return null;
    }
  };
}

/**
 * Sync wrapper for error handling
 * Wraps sync function with automatic error handling
 */
export function withErrorHandlingSync<T>(
  fn: () => T,
  options: ErrorHandlerOptions
): () => T | null {
  return () => {
    try {
      return fn();
    } catch (error) {
      handleError(error, options);
      return null;
    }
  };
}
