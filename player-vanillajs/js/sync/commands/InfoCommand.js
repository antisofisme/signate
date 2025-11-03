/**
 * Info Command
 *
 * @class InfoCommand
 * @extends BaseCommand
 * @description
 * Command to collect and return detailed device information.
 * Uses DeviceInfo utility module for platform detection and metrics.
 *
 * @features
 * - Device identification (ID, code, activation status)
 * - Display capabilities (resolution, pixel ratio, color depth)
 * - Platform and browser information
 * - Network connection metrics
 * - Performance and memory information
 * - Storage usage statistics
 * - WebOS-specific information
 *
 * @usage
 * ```javascript
 * const cmd = new InfoCommand();
 * const result = await cmd.executeWithTimeout();
 * ```
 */

class InfoCommand extends BaseCommand {
  /**
   * Create info command instance
   */
  constructor() {
    super('Info');
  }

  /**
   * Execute info command (no parameters required)
   *
   * @param {Object} [parameters] - Command parameters (unused)
   * @returns {Promise<Object>} - Device information
   */
  async execute(parameters = {}) {
    this.log('Collecting device information...');

    const info = {
      // Basic device info
      device_id: localStorage.getItem('device_id'),
      device_code: localStorage.getItem('device_code'),
      activation_status: localStorage.getItem('device_status'),

      // Display information
      screen_width: window.screen.width,
      screen_height: window.screen.height,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      device_pixel_ratio: window.devicePixelRatio || 1,
      color_depth: window.screen.colorDepth,
      pixel_depth: window.screen.pixelDepth,

      // Platform information
      user_agent: navigator.userAgent,
      platform: this._detectPlatform(),
      language: navigator.language,
      languages: navigator.languages,
      online: navigator.onLine,

      // Connection information
      connection_type: this._getConnectionType(),
      connection_speed: this._getConnectionSpeed(),
      connection_rtt: this._getConnectionRTT(),

      // Performance information
      memory: this._getMemoryInfo(),
      hardware_concurrency: navigator.hardwareConcurrency || null,

      // Storage information
      storage: await this._getStorageInfo(),

      // Timestamp
      timestamp: new Date().toISOString()
    };

    // WebOS specific info
    if (window.webOS) {
      info.webos_version = window.webOS.platformVersion || null;
      info.webos_device_info = window.webOS.deviceInfo || null;
    }

    this.log('✅ Device info collected');
    return { success: true, info };
  }

  /**
   * Detect platform using DeviceInfo utility
   *
   * @returns {string} - Platform name
   * @private
   */
  _detectPlatform() {
    if (window.DeviceInfo && window.DeviceInfo.detectPlatform) {
      return window.DeviceInfo.detectPlatform();
    }

    // Fallback inline implementation
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
   * Get connection type using DeviceInfo utility
   *
   * @returns {string|null} - Connection type
   * @private
   */
  _getConnectionType() {
    if (window.DeviceInfo && window.DeviceInfo.getConnectionType) {
      return window.DeviceInfo.getConnectionType();
    }

    if (!navigator.connection) return null;
    return navigator.connection.effectiveType || navigator.connection.type || null;
  }

  /**
   * Get connection speed using DeviceInfo utility
   *
   * @returns {number|null} - Connection speed in Mbps
   * @private
   */
  _getConnectionSpeed() {
    if (window.DeviceInfo && window.DeviceInfo.getConnectionSpeed) {
      return window.DeviceInfo.getConnectionSpeed();
    }

    if (!navigator.connection || !navigator.connection.downlink) return null;
    return navigator.connection.downlink;
  }

  /**
   * Get connection RTT using DeviceInfo utility
   *
   * @returns {number|null} - Round trip time in ms
   * @private
   */
  _getConnectionRTT() {
    if (window.DeviceInfo && window.DeviceInfo.getConnectionRTT) {
      return window.DeviceInfo.getConnectionRTT();
    }

    if (!navigator.connection || !navigator.connection.rtt) return null;
    return navigator.connection.rtt;
  }

  /**
   * Get memory info using DeviceInfo utility
   *
   * @returns {Object|null} - Memory metrics
   * @private
   */
  _getMemoryInfo() {
    if (window.DeviceInfo && window.DeviceInfo.getMemoryInfo) {
      return window.DeviceInfo.getMemoryInfo();
    }

    if (!performance.memory) return null;

    return {
      used_js_heap_size: performance.memory.usedJSHeapSize,
      total_js_heap_size: performance.memory.totalJSHeapSize,
      js_heap_size_limit: performance.memory.jsHeapSizeLimit,
      used_mb: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
      total_mb: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
      limit_mb: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
    };
  }

  /**
   * Get storage info using DeviceInfo utility
   *
   * @returns {Promise<Object>} - Storage metrics
   * @private
   */
  async _getStorageInfo() {
    if (window.DeviceInfo && window.DeviceInfo.getStorageInfo) {
      return await window.DeviceInfo.getStorageInfo();
    }

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
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = InfoCommand;
}

// Export to window for vanilla JS
window.InfoCommand = InfoCommand;
