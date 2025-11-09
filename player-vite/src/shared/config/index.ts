/**
 * Centralized Application Configuration
 * NO hardcoded values - all from environment variables
 *
 * Usage:
 *   import { config } from '@shared/config';
 *   const apiUrl = config.api.baseURL;
 */

import type { AppConfig } from './config.types';

/**
 * Parse environment variable as number
 */
function getEnvNumber(key: string, defaultValue: number): number {
  const value = import.meta.env[key];
  return value ? parseInt(value, 10) : defaultValue;
}

/**
 * Parse environment variable as boolean
 */
function getEnvBoolean(key: string, defaultValue: boolean): boolean {
  const value = import.meta.env[key];
  if (value === undefined) return defaultValue;
  return value === 'true' || value === '1';
}

/**
 * Parse environment variable as string
 */
function getEnvString(key: string, defaultValue: string): string {
  return import.meta.env[key] || defaultValue;
}

/**
 * Application Configuration Object
 * All values from environment variables
 */
export const config: AppConfig = {
  // API Configuration
  api: {
    baseURL: getEnvString('VITE_API_BASE_URL', 'http://192.168.5.12:8001'),
    wsBaseURL: getEnvString('VITE_WS_BASE_URL', 'ws://192.168.5.12:8001'),
    timeout: getEnvNumber('VITE_API_TIMEOUT', 30000),
  },

  // Device Configuration
  device: {
    heartbeatInterval: getEnvNumber('VITE_HEARTBEAT_INTERVAL', 30000),
    logSendInterval: getEnvNumber('VITE_LOG_SEND_INTERVAL', 30000),
    logBufferSize: getEnvNumber('VITE_LOG_BUFFER_SIZE', 50),
  },

  // Retry Configuration
  retry: {
    maxRetryCount: getEnvNumber('VITE_MAX_RETRY_COUNT', 20),
    initialRetryDelay: getEnvNumber('VITE_INITIAL_RETRY_DELAY', 5000),
    maxRetryDelay: getEnvNumber('VITE_MAX_RETRY_DELAY', 30000),
    backoffMultiplier: 1.5,
  },

  // Logging Configuration
  log: {
    level: (getEnvString('VITE_LOG_LEVEL', 'log') as AppConfig['log']['level']),
    enableConsole: getEnvBoolean('VITE_ENABLE_CONSOLE', true),
  },

  // Debug Configuration
  debug: {
    debugMode: getEnvBoolean('VITE_DEBUG_MODE', false),
    apiDebug: getEnvBoolean('VITE_API_DEBUG', false),
    wsDebug: getEnvBoolean('VITE_WS_DEBUG', false),
  },
};

/**
 * Freeze config to prevent runtime modifications
 */
Object.freeze(config);
Object.freeze(config.api);
Object.freeze(config.device);
Object.freeze(config.retry);
Object.freeze(config.log);
Object.freeze(config.debug);

// Log config in development (for debugging)
if (import.meta.env.DEV) {
  console.log('[Config] Loaded configuration:', config);
}
