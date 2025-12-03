/**
 * PWA Configuration
 * Feature flags and configuration for Progressive Web App functionality
 *
 * @features
 * - Master toggle for PWA functionality
 * - Rollout percentage for gradual deployment
 * - Device whitelist for testing
 * - Cache configuration
 */

/**
 * PWA Feature Configuration
 */
export const PWA_CONFIG = {
  /**
   * Master toggle for PWA functionality
   * Set to false to completely disable PWA Service Worker
   */
  ENABLED: true,

  /**
   * Rollout percentage (0-100)
   * 0 = disabled, 100 = all devices
   * Used for gradual rollout to production devices
   */
  ROLLOUT_PERCENTAGE: 100,

  /**
   * Device whitelist for testing
   * If not empty, only these device IDs can use PWA
   * Format: ['device-uuid-1', 'device-uuid-2']
   */
  DEVICE_WHITELIST: [] as string[],

  /**
   * Cache configuration
   */
  CACHE: {
    /** Name for the app shell cache */
    APP_SHELL_CACHE: 'signage-app-shell-v1',

    /** Name for static assets cache */
    STATIC_CACHE: 'signage-static-v1',

    /** Maximum entries in static cache */
    MAX_STATIC_ENTRIES: 100,

    /** Maximum age for static cache (30 days in seconds) */
    MAX_STATIC_AGE: 30 * 24 * 60 * 60,
  },

  /**
   * Offline configuration
   */
  OFFLINE: {
    /** Path to offline fallback page */
    FALLBACK_PAGE: '/offline.html',

    /** Enable offline analytics queuing */
    QUEUE_ANALYTICS: true,
  },

  /**
   * Update configuration
   */
  UPDATE: {
    /** How to handle updates: 'prompt' | 'autoUpdate' */
    REGISTER_TYPE: 'prompt' as 'prompt' | 'autoUpdate',

    /** Show update notification to user */
    SHOW_UPDATE_NOTIFICATION: true,

    /** Auto-update after this delay (ms) - only if REGISTER_TYPE is 'autoUpdate' */
    AUTO_UPDATE_DELAY: 5000,
  },
};

/**
 * Check if PWA should be enabled for this device
 * @param deviceId - Optional device ID for whitelist check
 * @returns true if PWA should be enabled
 */
export function isPWAEnabled(deviceId?: string): boolean {
  // Master toggle check
  if (!PWA_CONFIG.ENABLED) {
    return false;
  }

  // Whitelist check (if whitelist is not empty)
  if (PWA_CONFIG.DEVICE_WHITELIST.length > 0 && deviceId) {
    return PWA_CONFIG.DEVICE_WHITELIST.includes(deviceId);
  }

  // Rollout percentage check
  if (PWA_CONFIG.ROLLOUT_PERCENTAGE < 100) {
    // Use device ID or random for percentage check
    const hash = deviceId
      ? hashCode(deviceId)
      : Math.floor(Math.random() * 100);
    const percentage = Math.abs(hash) % 100;
    return percentage < PWA_CONFIG.ROLLOUT_PERCENTAGE;
  }

  return true;
}

/**
 * Simple hash function for device ID
 */
function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}

/**
 * Check if service workers are supported
 */
export function isServiceWorkerSupported(): boolean {
  return 'serviceWorker' in navigator;
}

/**
 * Check if running in secure context (required for SW)
 * Note: localhost is considered secure for development
 */
export function isSecureContext(): boolean {
  return (
    window.isSecureContext ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.protocol === 'file:'
  );
}

/**
 * Get PWA debug info
 */
export function getPWADebugInfo(): Record<string, unknown> {
  return {
    enabled: PWA_CONFIG.ENABLED,
    rolloutPercentage: PWA_CONFIG.ROLLOUT_PERCENTAGE,
    whitelistCount: PWA_CONFIG.DEVICE_WHITELIST.length,
    serviceWorkerSupported: isServiceWorkerSupported(),
    secureContext: isSecureContext(),
    protocol: window.location.protocol,
    hostname: window.location.hostname,
  };
}
