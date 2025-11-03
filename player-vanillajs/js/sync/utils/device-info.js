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
 * ```javascript
 * const platform = DeviceInfo.detectPlatform();
 * const connType = DeviceInfo.getConnectionType();
 * const memory = DeviceInfo.getMemoryInfo();
 * ```
 */

const DeviceInfo = {
  /**
   * Detect platform type from user agent
   *
   * @returns {string} Platform name
   * @example
   * // Returns: 'webOS', 'Tizen', 'Android TV', 'Chrome', 'Firefox', etc.
   */
  detectPlatform: function() {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
    if (ua.includes('tizen')) return 'Tizen';
    if (ua.includes('android tv')) return 'Android TV';
    if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
    if (ua.includes('firefox')) return 'Firefox';
    if (ua.includes('chrome')) return 'Chrome';
    if (ua.includes('safari')) return 'Safari';
    return 'Browser';
  },

  /**
   * Get network connection type
   *
   * @returns {string|null} Connection type (4g, 3g, wifi, slow-2g, etc)
   */
  getConnectionType: function() {
    if (!navigator.connection) return null;
    return navigator.connection.effectiveType || navigator.connection.type || null;
  },

  /**
   * Get network connection speed in Mbps
   *
   * @returns {number|null} Downlink speed in Mbps
   */
  getConnectionSpeed: function() {
    if (!navigator.connection || !navigator.connection.downlink) return null;
    return navigator.connection.downlink;
  },

  /**
   * Get network connection RTT (Round Trip Time)
   *
   * @returns {number|null} RTT in milliseconds
   */
  getConnectionRTT: function() {
    if (!navigator.connection || !navigator.connection.rtt) return null;
    return navigator.connection.rtt;
  },

  /**
   * Get JavaScript heap memory information
   *
   * @returns {Object|null} Memory metrics object or null if unavailable
   */
  getMemoryInfo: function() {
    if (!performance.memory) return null;

    return {
      used_js_heap_size: performance.memory.usedJSHeapSize,
      total_js_heap_size: performance.memory.totalJSHeapSize,
      js_heap_size_limit: performance.memory.jsHeapSizeLimit,
      used_mb: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
      total_mb: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
      limit_mb: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
    };
  },

  /**
   * Get storage information (localStorage, indexedDB quota)
   *
   * @returns {Promise<Object>} Storage metrics object
   */
  getStorageInfo: async function() {
    const storage = {
      localStorage: null,
      indexedDB: null,
      quota: null
    };

    // LocalStorage size
    try {
      let localStorageSize = 0;
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          localStorageSize += localStorage[key].length + key.length;
        }
      }
      storage.localStorage = {
        used_bytes: localStorageSize,
        used_kb: Math.round(localStorageSize / 1024)
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
          usage_mb: Math.round(estimate.usage / 1024 / 1024),
          quota_mb: Math.round(estimate.quota / 1024 / 1024),
          percent_used: Math.round((estimate.usage / estimate.quota) * 100)
        };
      } catch (e) {
        storage.quota = { error: 'Unable to estimate' };
      }
    }

    return storage;
  }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DeviceInfo;
}

// Export to window for vanilla JS
window.DeviceInfo = DeviceInfo;
