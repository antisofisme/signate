/**
 * Player Capabilities Reporter Service
 * Reports device capabilities to backend ONCE on startup
 *
 * @features
 * - Sends static device info once (not repeatedly)
 * - Detects video/audio codec support
 * - Reports hardware info (CPU cores, memory)
 * - Detects WebGL version and GPU info
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { collectDeviceCapabilities, DeviceCapabilities } from '@shared/utils/device-capabilities';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * API Request payload for capabilities endpoint
 */
interface CapabilitiesPayload {
  screen_width: number;
  screen_height: number;
  device_pixel_ratio: number;
  display_refresh_rate: number;
  hardware_concurrency: number;
  device_memory_gb: number | null;
  codec_h264: boolean;
  codec_h265: boolean;
  codec_vp9: boolean;
  codec_av1: boolean;
  codec_aac: boolean;
  codec_opus: boolean;
  webgl_version: string;
  webgl_renderer: string | null;
  webgl_vendor: string | null;
  user_agent: string;
  platform: string;
  player_version: string;
}

/**
 * Player Capabilities Reporter Class
 * Singleton pattern for capabilities reporting
 */
class PlayerCapabilitiesReporterClass {
  private reported = false;
  private capabilities: DeviceCapabilities | null = null;

  /**
   * Report device capabilities to backend
   * Called ONCE on startup after device authentication
   */
  async report(): Promise<boolean> {
    if (this.reported) {
      SharedLogger.log('[CapabilitiesReporter] Already reported, skipping');
      return true;
    }

    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[CapabilitiesReporter] Cannot report - no device_id');
      return false;
    }

    try {
      SharedLogger.log('[CapabilitiesReporter] Collecting device capabilities...');

      // Get player version from config
      const playerVersion = config.player?.version || '1.0.0';

      // Collect all capabilities
      this.capabilities = await collectDeviceCapabilities(playerVersion);

      // Transform to API payload format (snake_case)
      const payload: CapabilitiesPayload = {
        screen_width: this.capabilities.screenWidth,
        screen_height: this.capabilities.screenHeight,
        device_pixel_ratio: this.capabilities.devicePixelRatio,
        display_refresh_rate: this.capabilities.displayRefreshRate,
        hardware_concurrency: this.capabilities.hardwareConcurrency,
        device_memory_gb: this.capabilities.deviceMemoryGB,
        codec_h264: this.capabilities.codecH264,
        codec_h265: this.capabilities.codecH265,
        codec_vp9: this.capabilities.codecVP9,
        codec_av1: this.capabilities.codecAV1,
        codec_aac: this.capabilities.codecAAC,
        codec_opus: this.capabilities.codecOpus,
        webgl_version: this.capabilities.webglVersion,
        webgl_renderer: this.capabilities.webglRenderer,
        webgl_vendor: this.capabilities.webglVendor,
        user_agent: this.capabilities.userAgent,
        platform: this.capabilities.platform,
        player_version: this.capabilities.playerVersion,
      };

      SharedLogger.log('[CapabilitiesReporter] Sending capabilities:', {
        screen: `${payload.screen_width}x${payload.screen_height}`,
        refreshRate: payload.display_refresh_rate,
        cpuCores: payload.hardware_concurrency,
        memory: payload.device_memory_gb,
        codecs: {
          h264: payload.codec_h264,
          h265: payload.codec_h265,
          vp9: payload.codec_vp9,
          av1: payload.codec_av1,
        },
        webgl: payload.webgl_version,
      });

      // Send to backend
      await SharedAPIClient.post(
        `${config.api.baseURL}/api/v1/devices/${deviceId}/capabilities`,
        payload
      );

      this.reported = true;
      SharedLogger.log('[CapabilitiesReporter] ✅ Capabilities reported successfully');
      return true;
    } catch (error) {
      SharedLogger.error('[CapabilitiesReporter] ❌ Failed to report capabilities:', error);
      return false;
    }
  }

  /**
   * Get last collected capabilities
   * Useful for displaying in Device Info Popup
   */
  getCapabilities(): DeviceCapabilities | null {
    return this.capabilities;
  }

  /**
   * Check if capabilities have been reported
   */
  hasReported(): boolean {
    return this.reported;
  }

  /**
   * Force re-report capabilities
   * Used when player version changes or device is reactivated
   */
  async forceReport(): Promise<boolean> {
    this.reported = false;
    this.capabilities = null;
    return this.report();
  }

  /**
   * Reset state (for testing or when device is deregistered)
   */
  reset(): void {
    this.reported = false;
    this.capabilities = null;
    SharedLogger.log('[CapabilitiesReporter] State reset');
  }
}

// Export singleton instance
export const PlayerCapabilitiesReporter = new PlayerCapabilitiesReporterClass();

// Register to ServiceRegistry for global access
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerCapabilitiesReporter', PlayerCapabilitiesReporter);
}
