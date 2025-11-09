/**
 * Info Command
 *
 * @class InfoCommand
 * @extends BaseCommand
 * @description
 * Command to collect and return detailed device information.
 * Uses platform detection and metrics collection.
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
 * ```typescript
 * const cmd = new InfoCommand();
 * const result = await cmd.executeWithTimeout();
 * ```
 */

import { BaseCommand, CommandResult, WebOSWindow } from './base-command';

export interface DeviceInfo {
  device_id: string | null;
  device_code: string | null;
  activation_status: string | null;
  screen_width: number;
  screen_height: number;
  viewport_width: number;
  viewport_height: number;
  device_pixel_ratio: number;
  color_depth: number;
  pixel_depth: number;
  user_agent: string;
  platform: string;
  language: string;
  languages: readonly string[];
  online: boolean;
  connection_type: string | null;
  connection_speed: number | null;
  connection_rtt: number | null;
  memory: any;
  hardware_concurrency: number | null;
  storage: any;
  timestamp: string;
  webos_version?: string | null;
  webos_device_info?: any;
}

export interface InfoResult extends CommandResult {
  info: DeviceInfo;
}

export class InfoCommand extends BaseCommand {
  /**
   * Create info command instance
   */
  constructor() {
    super('Info');
  }

  /**
   * Execute info command (no parameters required)
   *
   * @returns Device information
   */
  async execute(): Promise<InfoResult> {
    this.log('Collecting device information...');

    const info: DeviceInfo = {
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
      platform: this.detectPlatform(),
      language: navigator.language,
      languages: navigator.languages,
      online: navigator.onLine,

      // Connection information
      connection_type: this.getConnectionType(),
      connection_speed: this.getConnectionSpeed(),
      connection_rtt: this.getConnectionRTT(),

      // Performance information
      memory: this.getMemoryInfo(),
      hardware_concurrency: navigator.hardwareConcurrency || null,

      // Storage information
      storage: await this.getStorageInfo(),

      // Timestamp
      timestamp: new Date().toISOString()
    };

    // WebOS specific info
    const win = window as WebOSWindow;
    if (win.webOS) {
      info.webos_version = win.webOS.platformVersion || null;
      info.webos_device_info = win.webOS.deviceInfo || null;
    }

    this.log('✅ Device info collected');
    return { success: true, info };
  }

  /**
   * Detect platform
   */
  private detectPlatform(): string {
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
   * Get connection type
   */
  private getConnectionType(): string | null {
    const connection = (navigator as any).connection;
    if (!connection) return null;
    return connection.effectiveType || connection.type || null;
  }

  /**
   * Get connection speed
   */
  private getConnectionSpeed(): number | null {
    const connection = (navigator as any).connection;
    if (!connection || !connection.downlink) return null;
    return connection.downlink;
  }

  /**
   * Get connection RTT
   */
  private getConnectionRTT(): number | null {
    const connection = (navigator as any).connection;
    if (!connection || !connection.rtt) return null;
    return connection.rtt;
  }

  /**
   * Get memory info
   */
  private getMemoryInfo(): any {
    const memory = (performance as any).memory;
    if (!memory) return null;

    return {
      used_js_heap_size: memory.usedJSHeapSize,
      total_js_heap_size: memory.totalJSHeapSize,
      js_heap_size_limit: memory.jsHeapSizeLimit,
      used_mb: Math.round(memory.usedJSHeapSize / 1024 / 1024),
      total_mb: Math.round(memory.totalJSHeapSize / 1024 / 1024),
      limit_mb: Math.round(memory.jsHeapSizeLimit / 1024 / 1024)
    };
  }

  /**
   * Get storage info
   */
  private async getStorageInfo(): Promise<any> {
    const storage: any = {
      localStorage: null,
      indexedDB: null,
      quota: null
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
          usage_mb: Math.round((estimate.usage || 0) / 1024 / 1024),
          quota_mb: Math.round((estimate.quota || 0) / 1024 / 1024),
          percent_used: Math.round(((estimate.usage || 0) / (estimate.quota || 1)) * 100)
        };
      } catch (e) {
        storage.quota = { error: 'Unable to estimate' };
      }
    }

    return storage;
  }
}
