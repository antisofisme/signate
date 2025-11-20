/**
 * Service Helper Utilities
 * Provides safe wrappers for service registry calls and common service patterns
 */

import { SharedLogger } from '@shared/logger';

/**
 * Safe service call - executes callback only if service is available
 * Returns result or default value if service not found
 *
 * @example
 * const result = safeServiceCall(
 *   () => getPlayerVideoJS(),
 *   (service) => service.play(),
 *   'PlayerVideoJS not available'
 * );
 */
export function safeServiceCall<T, R>(
  getService: () => T | undefined,
  callback: (service: T) => R,
  defaultValue: R
): R {
  const service = getService();
  if (service) {
    return callback(service);
  }
  return defaultValue;
}

/**
 * Safe async service call - executes async callback only if service is available
 *
 * @example
 * await safeServiceCallAsync(
 *   () => getPlayerVideoJS(),
 *   async (service) => await service.loadPlaylist(playlist),
 *   null
 * );
 */
export async function safeServiceCallAsync<T, R>(
  getService: () => T | undefined,
  callback: (service: T) => Promise<R>,
  defaultValue: R
): Promise<R> {
  const service = getService();
  if (service) {
    return await callback(service);
  }
  return defaultValue;
}

/**
 * Service action - executes void callback if service is available
 * Logs warning if service not found
 *
 * @example
 * serviceAction(
 *   () => getPlayerVideoJS(),
 *   (service) => service.pause(),
 *   'PlayerVideoJS'
 * );
 */
export function serviceAction<T>(
  getService: () => T | undefined,
  callback: (service: T) => void,
  serviceName: string
): void {
  const service = getService();
  if (service) {
    callback(service);
  } else {
    SharedLogger.warn(`[ServiceHelper] ${serviceName} not available`);
  }
}

/**
 * Async service action - executes async void callback if service is available
 *
 * @example
 * await serviceActionAsync(
 *   () => getPlayerPlaylistSync(),
 *   async (service) => await service.syncNow(),
 *   'PlayerPlaylistSync'
 * );
 */
export async function serviceActionAsync<T>(
  getService: () => T | undefined,
  callback: (service: T) => Promise<void>,
  serviceName: string
): Promise<void> {
  const service = getService();
  if (service) {
    await callback(service);
  } else {
    SharedLogger.warn(`[ServiceHelper] ${serviceName} not available`);
  }
}

/**
 * Conditional service call - only executes if condition is true and service available
 *
 * @example
 * conditionalServiceCall(
 *   shouldPlay,
 *   () => getPlayerVideoJS(),
 *   (service) => service.play()
 * );
 */
export function conditionalServiceCall<T>(
  condition: boolean,
  getService: () => T | undefined,
  callback: (service: T) => void
): void {
  if (!condition) return;

  const service = getService();
  if (service) {
    callback(service);
  }
}
