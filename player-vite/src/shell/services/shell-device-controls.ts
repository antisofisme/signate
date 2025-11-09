/**
 * Shell Device Controls
 * Platform-specific device control utilities
 *
 * @features
 * - Volume control (if available)
 * - Brightness control (if available)
 * - Power management
 * - Platform-specific APIs (webOS, Tizen)
 * - Fallback for unsupported platforms
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';

/**
 * Volume level (0-100)
 */
export type VolumeLevel = number;

/**
 * Brightness level (0-100)
 */
export type BrightnessLevel = number;

/**
 * Device control capabilities
 */
export interface DeviceCapabilities {
  volumeControl: boolean;
  brightnessControl: boolean;
  powerManagement: boolean;
  platform: string;
}

/**
 * Shell Device Controls Class
 * Singleton pattern for device control management
 */
class ShellDeviceControlsClass {
  private initialized = false;
  private capabilities: DeviceCapabilities | null = null;
  private currentVolume = 50;
  private currentBrightness = 100;

  /**
   * Initialize device controls
   */
  init(): void {
    if (this.initialized) {
      SharedLogger.warn('[DeviceControls] Already initialized');
      return;
    }

    this.initialized = true;

    // Detect capabilities
    this.capabilities = this.detectCapabilities();

    // Initialize platform-specific APIs
    this.initializePlatformAPIs();

    SharedLogger.log('[DeviceControls] Initialized');
    SharedLogger.log('[DeviceControls] Capabilities:', this.capabilities);
  }

  /**
   * Detect device capabilities
   */
  private detectCapabilities(): DeviceCapabilities {
    let volumeControl = false;
    let brightnessControl = false;
    let powerManagement = false;
    let platform = 'unknown';

    // webOS TV
    // @ts-ignore
    if (typeof window.webOS !== 'undefined') {
      platform = 'webOS';
      volumeControl = true;
      brightnessControl = false; // webOS doesn't expose brightness control
      powerManagement = true;
    }
    // Tizen TV
    // @ts-ignore
    else if (typeof window.tizen !== 'undefined') {
      platform = 'Tizen';
      volumeControl = true;
      brightnessControl = false; // Tizen doesn't expose brightness control
      powerManagement = true;
    }
    // Android TV
    else if (navigator.userAgent.toLowerCase().includes('android')) {
      platform = 'Android';
      volumeControl = false; // Limited access
      brightnessControl = false; // Limited access
      powerManagement = false;
    }
    // Desktop browser
    else {
      platform = 'Desktop';
      volumeControl = false;
      brightnessControl = false;
      powerManagement = false;
    }

    return {
      volumeControl,
      brightnessControl,
      powerManagement,
      platform,
    };
  }

  /**
   * Initialize platform-specific APIs
   */
  private initializePlatformAPIs(): void {
    // webOS initialization
    // @ts-ignore
    if (typeof window.webOS !== 'undefined') {
      this.initWebOS();
    }

    // Tizen initialization
    // @ts-ignore
    if (typeof window.tizen !== 'undefined') {
      this.initTizen();
    }
  }

  /**
   * Initialize webOS TV APIs
   */
  private initWebOS(): void {
    SharedLogger.log('[DeviceControls] Initializing webOS APIs');

    try {
      // @ts-ignore
      if (window.webOS.service) {
        // Get current volume
        // @ts-ignore
        window.webOS.service.request('luna://com.webos.audio', {
          method: 'getVolume',
          onSuccess: (response: any) => {
            this.currentVolume = response.volume || 50;
            SharedLogger.log('[DeviceControls] Current volume:', this.currentVolume);
          },
          onFailure: (error: any) => {
            SharedLogger.error('[DeviceControls] Failed to get volume:', error);
          },
        });
      }
    } catch (error) {
      SharedLogger.error('[DeviceControls] webOS initialization error:', error);
    }
  }

  /**
   * Initialize Tizen TV APIs
   */
  private initTizen(): void {
    SharedLogger.log('[DeviceControls] Initializing Tizen APIs');

    try {
      // @ts-ignore
      if (window.tizen && window.tizen.tvaudiocontrol) {
        // Get current volume
        // @ts-ignore
        this.currentVolume = tizen.tvaudiocontrol.getVolume() || 50;
        SharedLogger.log('[DeviceControls] Current volume:', this.currentVolume);
      }
    } catch (error) {
      SharedLogger.error('[DeviceControls] Tizen initialization error:', error);
    }
  }

  /**
   * Set volume
   */
  async setVolume(level: VolumeLevel): Promise<boolean> {
    if (!this.capabilities?.volumeControl) {
      SharedLogger.warn('[DeviceControls] Volume control not supported');
      return false;
    }

    // Clamp value between 0-100
    const clampedLevel = Math.max(0, Math.min(100, level));

    try {
      // webOS
      // @ts-ignore
      if (typeof window.webOS !== 'undefined' && window.webOS.service) {
        // @ts-ignore
        window.webOS.service.request('luna://com.webos.audio', {
          method: 'setVolume',
          parameters: {
            volume: clampedLevel,
          },
          onSuccess: () => {
            this.currentVolume = clampedLevel;
            SharedEventBus.emit('device:volume_change', { volume: clampedLevel });
            SharedLogger.log('[DeviceControls] Volume set to:', clampedLevel);
          },
          onFailure: (error: any) => {
            SharedLogger.error('[DeviceControls] Failed to set volume:', error);
          },
        });
        return true;
      }

      // Tizen
      // @ts-ignore
      if (typeof window.tizen !== 'undefined' && window.tizen.tvaudiocontrol) {
        // @ts-ignore
        tizen.tvaudiocontrol.setVolume(clampedLevel);
        this.currentVolume = clampedLevel;
        SharedEventBus.emit('device:volume_change', { volume: clampedLevel });
        SharedLogger.log('[DeviceControls] Volume set to:', clampedLevel);
        return true;
      }

      return false;
    } catch (error) {
      SharedLogger.error('[DeviceControls] Set volume error:', error);
      return false;
    }
  }

  /**
   * Get current volume
   */
  getVolume(): VolumeLevel {
    return this.currentVolume;
  }

  /**
   * Increase volume
   */
  async volumeUp(step = 5): Promise<boolean> {
    const newVolume = Math.min(100, this.currentVolume + step);
    return this.setVolume(newVolume);
  }

  /**
   * Decrease volume
   */
  async volumeDown(step = 5): Promise<boolean> {
    const newVolume = Math.max(0, this.currentVolume - step);
    return this.setVolume(newVolume);
  }

  /**
   * Mute/Unmute
   */
  async toggleMute(): Promise<boolean> {
    if (!this.capabilities?.volumeControl) {
      SharedLogger.warn('[DeviceControls] Volume control not supported');
      return false;
    }

    try {
      // webOS
      // @ts-ignore
      if (typeof window.webOS !== 'undefined' && window.webOS.service) {
        // @ts-ignore
        window.webOS.service.request('luna://com.webos.audio', {
          method: 'setMute',
          parameters: {
            mute: this.currentVolume > 0,
          },
          onSuccess: () => {
            SharedEventBus.emit('device:mute_toggle');
            SharedLogger.log('[DeviceControls] Mute toggled');
          },
        });
        return true;
      }

      // Tizen
      // @ts-ignore
      if (typeof window.tizen !== 'undefined' && window.tizen.tvaudiocontrol) {
        // @ts-ignore
        const isMuted = tizen.tvaudiocontrol.isMute();
        // @ts-ignore
        tizen.tvaudiocontrol.setMute(!isMuted);
        SharedEventBus.emit('device:mute_toggle');
        SharedLogger.log('[DeviceControls] Mute toggled');
        return true;
      }

      return false;
    } catch (error) {
      SharedLogger.error('[DeviceControls] Toggle mute error:', error);
      return false;
    }
  }

  /**
   * Set brightness (if supported)
   */
  async setBrightness(level: BrightnessLevel): Promise<boolean> {
    if (!this.capabilities?.brightnessControl) {
      SharedLogger.warn('[DeviceControls] Brightness control not supported');
      return false;
    }

    // Clamp value between 0-100
    // const clampedLevel = Math.max(0, Math.min(100, level));

    // Most TV platforms don't expose brightness control
    // This is a placeholder for future implementations
    SharedLogger.warn('[DeviceControls] Brightness control not implemented for this platform', level);
    return false;
  }

  /**
   * Get current brightness
   */
  getBrightness(): BrightnessLevel {
    return this.currentBrightness;
  }

  /**
   * Power off device (if supported)
   */
  async powerOff(): Promise<boolean> {
    if (!this.capabilities?.powerManagement) {
      SharedLogger.warn('[DeviceControls] Power management not supported');
      return false;
    }

    try {
      // webOS
      // @ts-ignore
      if (typeof window.webOS !== 'undefined' && window.webOS.service) {
        // @ts-ignore
        window.webOS.service.request('luna://com.webos.pmlogd', {
          method: 'powerOff',
          onSuccess: () => {
            SharedLogger.log('[DeviceControls] Power off requested');
          },
        });
        return true;
      }

      // Tizen
      // @ts-ignore
      if (typeof window.tizen !== 'undefined' && window.tizen.application) {
        // @ts-ignore
        tizen.application.getCurrentApplication().exit();
        SharedLogger.log('[DeviceControls] Application exit requested');
        return true;
      }

      return false;
    } catch (error) {
      SharedLogger.error('[DeviceControls] Power off error:', error);
      return false;
    }
  }

  /**
   * Get device capabilities
   */
  getCapabilities(): DeviceCapabilities | null {
    return this.capabilities;
  }

  /**
   * Check if volume control is available
   */
  hasVolumeControl(): boolean {
    return this.capabilities?.volumeControl || false;
  }

  /**
   * Check if brightness control is available
   */
  hasBrightnessControl(): boolean {
    return this.capabilities?.brightnessControl || false;
  }

  /**
   * Check if power management is available
   */
  hasPowerManagement(): boolean {
    return this.capabilities?.powerManagement || false;
  }

  /**
   * Cleanup
   */
  destroy(): void {
    this.initialized = false;
    SharedLogger.log('[DeviceControls] Destroyed');
  }
}

// Export singleton instance
export const ShellDeviceControls = new ShellDeviceControlsClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellDeviceControls: typeof ShellDeviceControls;
  }
}

if (typeof window !== 'undefined') {
  window.ShellDeviceControls = ShellDeviceControls;
}

// Auto-initialize when module is imported
ShellDeviceControls.init();
