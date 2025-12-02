/**
 * Shell Display Settings
 * Detects and manages display configuration
 *
 * @features
 * - Get screen resolution
 * - Detect TV capabilities
 * - Get display orientation
 * - Detect HDR support
 * - Report to backend
 * - Auto-detect on initialization
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { SharedAPIClient } from '@shared/api/shared-api-client';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Display information
 */
export interface DisplayInfo {
  width: number;
  height: number;
  pixelRatio: number;
  orientation: 'portrait' | 'landscape';
  colorDepth: number;
  hdrSupported: boolean;
  refreshRate?: number;
  aspectRatio: string;
  platform: string;
  userAgent: string;
}

/**
 * TV capabilities
 */
export interface TVCapabilities {
  isTV: boolean;
  brand?: string;
  model?: string;
  platform?: 'webOS' | 'Tizen' | 'AndroidTV' | 'unknown';
  version?: string;
  features: string[];
}

/**
 * Shell Display Settings Class
 * Singleton pattern for display management
 */
class ShellDisplaySettingsClass {
  private displayInfo: DisplayInfo | null = null;
  private tvCapabilities: TVCapabilities | null = null;
  private initialized = false;

  /**
   * Initialize display settings
   */
  init(): void {
    if (this.initialized) {
      SharedLogger.warn('[DisplaySettings] Already initialized');
      return;
    }

    this.initialized = true;

    // Detect display info
    this.displayInfo = this.detectDisplayInfo();

    // Detect TV capabilities
    this.tvCapabilities = this.detectTVCapabilities();

    // Listen to orientation changes
    window.addEventListener('orientationchange', this.handleOrientationChange);
    window.addEventListener('resize', this.handleResize);

    // Listen to fullscreen changes (need to re-apply rotation on fullscreen enter/exit)
    document.addEventListener('fullscreenchange', this.handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', this.handleFullscreenChange);

    SharedLogger.log('[DisplaySettings] Initialized');
    SharedLogger.log('[DisplaySettings] Display:', this.displayInfo);
    SharedLogger.log('[DisplaySettings] TV:', this.tvCapabilities);
  }

  /**
   * Detect display information
   */
  private detectDisplayInfo(): DisplayInfo {
    const width = window.screen.width;
    const height = window.screen.height;
    const pixelRatio = window.devicePixelRatio || 1;
    const orientation = width > height ? 'landscape' : 'portrait';
    const colorDepth = window.screen.colorDepth;

    // Calculate aspect ratio
    const gcd = this.getGCD(width, height);
    const aspectRatio = `${width / gcd}:${height / gcd}`;

    // Detect HDR support
    const hdrSupported = this.detectHDRSupport();

    // Try to get refresh rate
    const refreshRate = this.detectRefreshRate();

    // Get platform
    const platform = this.detectPlatform();

    return {
      width,
      height,
      pixelRatio,
      orientation,
      colorDepth,
      hdrSupported,
      refreshRate,
      aspectRatio,
      platform,
      userAgent: navigator.userAgent,
    };
  }

  /**
   * Detect TV capabilities
   */
  private detectTVCapabilities(): TVCapabilities {
    const userAgent = navigator.userAgent.toLowerCase();
    const features: string[] = [];
    let isTV = false;
    let brand: string | undefined;
    let model: string | undefined;
    let platform: 'webOS' | 'Tizen' | 'AndroidTV' | 'unknown' = 'unknown';
    let version: string | undefined;

    // webOS TV
    // @ts-ignore
    if (typeof window.webOS !== 'undefined') {
      isTV = true;
      platform = 'webOS';
      brand = 'LG';

      // @ts-ignore
      if (window.webOS.platform) {
        // @ts-ignore
        model = window.webOS.platform.tv?.model;
        // @ts-ignore
        version = window.webOS.platform.tv?.version;
      }

      features.push('webOS');
    }
    // Tizen TV
    // @ts-ignore
    else if (typeof window.tizen !== 'undefined') {
      isTV = true;
      platform = 'Tizen';
      brand = 'Samsung';

      try {
        // @ts-ignore
        version = tizen.systeminfo?.getCapability('http://tizen.org/feature/platform.version');
      } catch (e) {
        // Ignore
      }

      features.push('Tizen');
    }
    // Android TV
    else if (userAgent.includes('android') && userAgent.includes('tv')) {
      isTV = true;
      platform = 'AndroidTV';
      features.push('AndroidTV');
    }
    // Generic TV detection
    else if (
      userAgent.includes('smart-tv') ||
      userAgent.includes('smarttv') ||
      userAgent.includes('googletv')
    ) {
      isTV = true;
      features.push('SmartTV');
    }

    // Additional features
    if ('requestFullscreen' in document.documentElement) {
      features.push('Fullscreen');
    }

    // @ts-ignore
    if (window.MediaSource) {
      features.push('MSE');
    }

    // @ts-ignore
    if (window.Hls) {
      features.push('HLS');
    }

    return {
      isTV,
      brand,
      model,
      platform,
      version,
      features,
    };
  }

  /**
   * Detect HDR support
   */
  private detectHDRSupport(): boolean {
    try {
      // Check for HDR media capabilities
      // @ts-ignore
      if (window.matchMedia && window.matchMedia('(dynamic-range: high)').matches) {
        return true;
      }

      // @ts-ignore
      if (window.screen?.luminance) {
        return true;
      }

      return false;
    } catch (error) {
      return false;
    }
  }

  /**
   * Detect refresh rate
   */
  private detectRefreshRate(): number | undefined {
    try {
      // Try to use requestAnimationFrame to estimate refresh rate
      let lastTime = performance.now();
      let frames = 0;
      let totalDelta = 0;

      const measureFrame = (time: number) => {
        const delta = time - lastTime;
        lastTime = time;
        totalDelta += delta;
        frames++;

        if (frames < 60) {
          requestAnimationFrame(measureFrame);
        } else {
          const avgFrameTime = totalDelta / frames;
          const refreshRate = Math.round(1000 / avgFrameTime);
          SharedLogger.log('[DisplaySettings] Detected refresh rate:', refreshRate);
        }
      };

      requestAnimationFrame(measureFrame);

      // Return common refresh rates
      // @ts-ignore
      return window.screen?.refreshRate || undefined;
    } catch (error) {
      return undefined;
    }
  }

  /**
   * Detect platform
   */
  private detectPlatform(): string {
    const userAgent = navigator.userAgent.toLowerCase();

    if (userAgent.includes('webos')) return 'webOS';
    if (userAgent.includes('tizen')) return 'Tizen';
    if (userAgent.includes('android')) return 'Android';
    if (userAgent.includes('iphone') || userAgent.includes('ipad')) return 'iOS';
    if (userAgent.includes('windows')) return 'Windows';
    if (userAgent.includes('mac')) return 'macOS';
    if (userAgent.includes('linux')) return 'Linux';

    return 'Unknown';
  }

  /**
   * Get Greatest Common Divisor (for aspect ratio)
   */
  private getGCD(a: number, b: number): number {
    return b === 0 ? a : this.getGCD(b, a % b);
  }

  /**
   * Handle orientation change
   */
  private handleOrientationChange = (): void => {
    SharedLogger.log('[DisplaySettings] Orientation changed');
    this.displayInfo = this.detectDisplayInfo();
    SharedEventBus.emit('display:orientation_change', this.displayInfo);

    // Re-apply rotation with new viewport dimensions
    this.applyRotation();
  };

  /**
   * Handle resize
   */
  private handleResize = (): void => {
    SharedLogger.log('[DisplaySettings] Window resized');
    this.displayInfo = this.detectDisplayInfo();
    SharedEventBus.emit('display:resize', this.displayInfo);

    // Re-apply rotation with new viewport dimensions
    this.applyRotation();
  };

  /**
   * Handle fullscreen change
   */
  private handleFullscreenChange = (): void => {
    SharedLogger.log('[DisplaySettings] Fullscreen state changed');
    this.displayInfo = this.detectDisplayInfo();

    // Small delay to ensure viewport dimensions are updated after fullscreen transition
    setTimeout(() => {
      this.applyRotation();
    }, 100);
  };

  /**
   * Get display info
   */
  getDisplayInfo(): DisplayInfo | null {
    return this.displayInfo;
  }

  /**
   * Get TV capabilities
   */
  getTVCapabilities(): TVCapabilities | null {
    return this.tvCapabilities;
  }

  /**
   * Check if running on TV
   */
  isTV(): boolean {
    return this.tvCapabilities?.isTV || false;
  }

  /**
   * Get screen resolution as string
   */
  getResolution(): string {
    if (!this.displayInfo) return 'unknown';
    return `${this.displayInfo.width}x${this.displayInfo.height}`;
  }

  /**
   * Get aspect ratio
   */
  getAspectRatio(): string {
    return this.displayInfo?.aspectRatio || 'unknown';
  }

  /**
   * Report display info to backend
   */
  async reportToBackend(): Promise<void> {
    try {
      const deviceId = SharedDeviceState.getDeviceId();
      if (!deviceId) {
        SharedLogger.warn('[DisplaySettings] No device ID, skipping report');
        return;
      }

      await SharedAPIClient.post('/api/client/display-info', {
        device_id: parseInt(deviceId, 10),
        display_info: this.displayInfo,
        tv_capabilities: this.tvCapabilities,
      });

      SharedLogger.log('[DisplaySettings] Display info reported to backend');
    } catch (error) {
      SharedLogger.error('[DisplaySettings] Failed to report display info:', error);
    }
  }

  /**
   * Get full system info (for debugging)
   */
  getSystemInfo(): {
    display: DisplayInfo | null;
    tv: TVCapabilities | null;
    navigator: {
      userAgent: string;
      platform: string;
      language: string;
      cookieEnabled: boolean;
      onLine: boolean;
    };
  } {
    return {
      display: this.displayInfo,
      tv: this.tvCapabilities,
      navigator: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
      },
    };
  }

  /**
   * Apply screen rotation from device settings
   * Reads rotation value from SharedDeviceState and applies CSS transform
   * Handles width/height swap for 90/270 degree rotations
   *
   * For 90/270 rotation: Container is sized to swapped dimensions and centered
   * using translate transform combined with rotate transform.
   */
  applyRotation(): void {
    const rotation = SharedDeviceState.getScreenRotation();
    const playerContainer = document.getElementById('player-container');
    const playerVideo = document.getElementById('player-video');

    if (!playerContainer) {
      SharedLogger.warn('[DisplaySettings] Player container not found, cannot apply rotation');
      return;
    }

    // Get viewport dimensions
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    SharedLogger.log(`[DisplaySettings] Applying rotation: ${rotation}deg (viewport: ${vw}x${vh})`);

    // Reset all styles first
    playerContainer.style.cssText = '';
    if (playerVideo) {
      playerVideo.style.cssText = '';
    }

    if (rotation === 0) {
      // No rotation - standard fullscreen
      playerContainer.style.cssText = `
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #000;
      `;
      if (playerVideo) {
        playerVideo.style.cssText = `
          width: 100%;
          height: 100%;
          object-fit: contain;
        `;
      }
      SharedLogger.log('[DisplaySettings] ✅ No rotation applied');
      return;
    }

    if (rotation === 90 || rotation === 270) {
      // For 90/270 degrees:
      // 1. Container size = swapped dimensions (vh x vw)
      // 2. Position at center using translate
      // 3. Apply rotation

      // Calculate offset to center the rotated container
      const offsetX = (vw - vh) / 2;
      const offsetY = (vh - vw) / 2;

      playerContainer.style.cssText = `
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        width: ${vh}px;
        height: ${vw}px;
        background: #000;
        transform-origin: center center;
        transform: translate(${offsetX}px, ${offsetY}px) rotate(${rotation}deg);
      `;

      if (playerVideo) {
        playerVideo.style.cssText = `
          width: 100%;
          height: 100%;
          object-fit: contain;
        `;
      }

      SharedLogger.log(`[DisplaySettings] ✅ Applied ${rotation}deg rotation (container: ${vh}x${vw}, offset: ${offsetX},${offsetY})`);
    } else if (rotation === 180) {
      // For 180 degrees - no dimension swap needed
      playerContainer.style.cssText = `
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #000;
        transform-origin: center center;
        transform: rotate(180deg);
      `;

      if (playerVideo) {
        playerVideo.style.cssText = `
          width: 100%;
          height: 100%;
          object-fit: contain;
        `;
      }

      SharedLogger.log('[DisplaySettings] ✅ Applied 180deg rotation');
    }
  }

  /**
   * Sync rotation from backend device settings
   * Fetches device info and updates local rotation preference
   */
  async syncRotationFromBackend(): Promise<void> {
    try {
      const deviceId = SharedDeviceState.getDeviceId();
      if (!deviceId) {
        SharedLogger.warn('[DisplaySettings] No device ID, skipping rotation sync');
        return;
      }

      // Fetch device info from backend using device ID (no auth required)
      const response = await SharedAPIClient.get(`/api/v1/devices/${deviceId}`);

      const device = (response as any).data?.data || (response as any).data;

      if (device && typeof device.rotation === 'number') {
        // Update local rotation preference
        SharedDeviceState.setScreenRotation(device.rotation);

        // Apply rotation immediately
        this.applyRotation();

        SharedLogger.log(`[DisplaySettings] Synced rotation from backend: ${device.rotation}deg`);
      }
    } catch (error) {
      SharedLogger.error('[DisplaySettings] Failed to sync rotation from backend:', error);
    }
  }

  /**
   * Cleanup event listeners
   */
  destroy(): void {
    window.removeEventListener('orientationchange', this.handleOrientationChange);
    window.removeEventListener('resize', this.handleResize);
    document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', this.handleFullscreenChange);
    this.initialized = false;
    SharedLogger.log('[DisplaySettings] Destroyed');
  }
}

// Export singleton instance
export const ShellDisplaySettings = new ShellDisplaySettingsClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellDisplaySettings: typeof ShellDisplaySettings;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellDisplaySettings', ShellDisplaySettings);
}

// Auto-initialize when module is imported
ShellDisplaySettings.init();
