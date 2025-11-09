/**
 * Device Information Utilities
 *
 * @module device-info
 * @description
 * Provides helper functions to collect and format device information
 * including platform detection, connection metrics, memory, and storage info.
 *
 * @features
 * - Platform detection (WebOS, Tizen, Android TV, browsers)
 * - Network connection information
 * - Memory and performance metrics
 * - Storage usage statistics
 * - Hardware capabilities
 *
 * @usage
 * ```typescript
 * const platform = detectPlatform();
 * const connType = getConnectionType();
 * const memory = getMemoryInfo();
 * ```
 */

/**
 * Platform types
 */
export type Platform =
  | 'webOS'
  | 'Tizen'
  | 'Android TV'
  | 'Edge'
  | 'Firefox'
  | 'Chrome'
  | 'Safari'
  | 'Browser';

/**
 * Memory information
 */
interface MemoryInfo {
  used_js_heap_size: number;
  total_js_heap_size: number;
  js_heap_size_limit: number;
  used_mb: number;
  total_mb: number;
  limit_mb: number;
}

/**
 * Storage information
 */
interface StorageInfo {
  localStorage: {
    used_bytes?: number;
    used_kb?: number;
    error?: string;
  } | null;
  indexedDB: null;
  quota: {
    usage_bytes?: number;
    quota_bytes?: number;
    usage_mb?: number;
    quota_mb?: number;
    percent_used?: number;
    error?: string;
  } | null;
}

/**
 * Extended Navigator interface for connection API
 */
interface NavigatorConnection extends Navigator {
  connection?: {
    effectiveType?: string;
    type?: string;
    downlink?: number;
    rtt?: number;
  };
}

/**
 * Detect platform type from user agent
 *
 * @returns Platform name
 * @example
 * // Returns: 'webOS', 'Tizen', 'Android TV', 'Chrome', 'Firefox', etc.
 */
export function detectPlatform(): Platform {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
  if (ua.includes('tizen')) return 'Tizen';
  if (ua.includes('android tv')) return 'Android TV';
  if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
  if (ua.includes('firefox')) return 'Firefox';
  if (ua.includes('chrome')) return 'Chrome';
  if (ua.includes('safari')) return 'Safari';
  return 'Browser';
}

/**
 * Get network connection type
 *
 * @returns Connection type (4g, 3g, wifi, slow-2g, etc) or null
 */
export function getConnectionType(): string | null {
  const nav = navigator as NavigatorConnection;
  if (!nav.connection) return null;
  return nav.connection.effectiveType || nav.connection.type || null;
}

/**
 * Get network connection speed in Mbps
 *
 * @returns Downlink speed in Mbps or null
 */
export function getConnectionSpeed(): number | null {
  const nav = navigator as NavigatorConnection;
  if (!nav.connection || !nav.connection.downlink) return null;
  return nav.connection.downlink;
}

/**
 * Get network connection RTT (Round Trip Time)
 *
 * @returns RTT in milliseconds or null
 */
export function getConnectionRTT(): number | null {
  const nav = navigator as NavigatorConnection;
  if (!nav.connection || !nav.connection.rtt) return null;
  return nav.connection.rtt;
}

/**
 * Get JavaScript heap memory information
 *
 * @returns Memory metrics object or null if unavailable
 */
export function getMemoryInfo(): MemoryInfo | null {
  // @ts-ignore - performance.memory is non-standard
  if (!performance || !performance.memory) return null;

  // @ts-ignore - performance.memory is non-standard
  const memory = performance.memory;

  return {
    used_js_heap_size: memory.usedJSHeapSize,
    total_js_heap_size: memory.totalJSHeapSize,
    js_heap_size_limit: memory.jsHeapSizeLimit,
    used_mb: Math.round(memory.usedJSHeapSize / 1024 / 1024),
    total_mb: Math.round(memory.totalJSHeapSize / 1024 / 1024),
    limit_mb: Math.round(memory.jsHeapSizeLimit / 1024 / 1024),
  };
}

/**
 * Get storage information (localStorage, indexedDB quota)
 *
 * @returns Storage metrics object
 */
export async function getStorageInfo(): Promise<StorageInfo> {
  const storage: StorageInfo = {
    localStorage: null,
    indexedDB: null,
    quota: null,
  };

  // LocalStorage size
  try {
    let localStorageSize = 0;
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        localStorageSize += localStorage[key].length + key.length;
      }
    }
    storage.localStorage = {
      used_bytes: localStorageSize,
      used_kb: Math.round(localStorageSize / 1024),
    };
  } catch (e) {
    storage.localStorage = { error: 'Unable to access' };
  }

  // Storage quota (if available)
  if (navigator.storage && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate();
      storage.quota = {
        usage_bytes: estimate.usage,
        quota_bytes: estimate.quota,
        usage_mb: Math.round((estimate.usage || 0) / 1024 / 1024),
        quota_mb: Math.round((estimate.quota || 0) / 1024 / 1024),
        percent_used: Math.round(
          ((estimate.usage || 0) / (estimate.quota || 1)) * 100
        ),
      };
    } catch (e) {
      storage.quota = { error: 'Unable to estimate' };
    }
  }

  return storage;
}

/**
 * Get comprehensive device information
 *
 * @returns Object with all device information
 */
export async function getDeviceInfo() {
  return {
    platform: detectPlatform(),
    userAgent: navigator.userAgent,
    connection: {
      type: getConnectionType(),
      speed: getConnectionSpeed(),
      rtt: getConnectionRTT(),
    },
    memory: getMemoryInfo(),
    storage: await getStorageInfo(),
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      colorDepth: window.screen.colorDepth,
      pixelRatio: window.devicePixelRatio,
    },
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
    },
  };
}
