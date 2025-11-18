/**
 * Device Configuration Storage
 * Manages persistent device configuration in IndexedDB
 *
 * Supports TWO release flows:
 * 1. CMS Release (Soft): Clear tokens, KEEP org_id
 * 2. Hard Reset (Factory): Clear ALL data including org_id
 */

import { dbManager } from './indexed-db-manager';
import { SharedLogger } from '@shared/logger';

const STORE_NAME = 'device_config';
const CONFIG_KEY = 'config';

/**
 * Device configuration interface
 */
export interface DeviceConfig {
  organization_id: number | null;
  access_token: string | null;
  refresh_token: string | null;
  device_id: number | null;
  unique_code: string | null; // Unique code after activation
  activation_code: string | null; // Pending activation code (6-digit)
  token_expires_at: number | null;
  session_id: string | null; // Browser session ID for device fingerprint (persistent)
}

/**
 * Default empty config
 */
const DEFAULT_CONFIG: DeviceConfig = {
  organization_id: null,
  access_token: null,
  refresh_token: null,
  device_id: null,
  unique_code: null,
  activation_code: null,
  token_expires_at: null,
  session_id: null,
};

class DeviceConfigStorage {
  /**
   * Get device configuration
   */
  async getDeviceConfig(): Promise<DeviceConfig> {
    try {
      const data = await dbManager.get<{ key: string; config: DeviceConfig }>(
        STORE_NAME,
        CONFIG_KEY
      );

      if (data?.config) {
        SharedLogger.log('[DeviceConfig] Config loaded from IndexedDB');
        return data.config;
      }

      SharedLogger.log('[DeviceConfig] No config found, returning default');
      return { ...DEFAULT_CONFIG };
    } catch (error) {
      SharedLogger.error('[DeviceConfig] Failed to get config:', error);
      return { ...DEFAULT_CONFIG };
    }
  }

  /**
   * Set device configuration (partial update)
   */
  async setDeviceConfig(config: Partial<DeviceConfig>): Promise<void> {
    try {
      const currentConfig = await this.getDeviceConfig();
      const updatedConfig = { ...currentConfig, ...config };

      await dbManager.put(STORE_NAME, {
        key: CONFIG_KEY,
        config: updatedConfig,
      });

      SharedLogger.log('[DeviceConfig] Config updated:', Object.keys(config));
    } catch (error) {
      SharedLogger.error('[DeviceConfig] Failed to set config:', error);
      throw error;
    }
  }

  /**
   * Clear tokens but KEEP org_id
   * Used for CMS release (soft release)
   *
   * Flow:
   * 1. Admin releases device from CMS
   * 2. Player heartbeat gets 403
   * 3. Player calls clearTokens()
   * 4. Player requests new code WITH org_id
   * 5. Device re-registers to SAME organization
   */
  async clearTokens(): Promise<void> {
    try {
      await this.setDeviceConfig({
        access_token: null,
        refresh_token: null,
        device_id: null,
        token_expires_at: null,
        // Note: organization_id is NOT cleared
        // Note: unique_code is NOT cleared (will be regenerated anyway)
      });

      SharedLogger.log('[DeviceConfig] Tokens cleared, org_id preserved (CMS release)');
    } catch (error) {
      SharedLogger.error('[DeviceConfig] Failed to clear tokens:', error);
      throw error;
    }
  }

  /**
   * Clear ALL device configuration
   * Used for hard reset (factory reset)
   *
   * Flow:
   * 1. User clicks "Factory Reset" in player
   * 2. User enters password
   * 3. Player calls backend to validate password
   * 4. Backend validates and sets status='released'
   * 5. Player calls hardReset()
   * 6. Player requests new code WITHOUT org_id
   * 7. Device re-registers to GLOBAL pending
   */
  async hardReset(): Promise<void> {
    try {
      await dbManager.put(STORE_NAME, {
        key: CONFIG_KEY,
        config: { ...DEFAULT_CONFIG },
      });

      SharedLogger.log('[DeviceConfig] ALL data cleared (hard reset)');
    } catch (error) {
      SharedLogger.error('[DeviceConfig] Failed to hard reset:', error);
      throw error;
    }
  }

  /**
   * Check if device is configured
   */
  async isConfigured(): Promise<boolean> {
    const config = await this.getDeviceConfig();
    return config.device_id !== null && config.access_token !== null;
  }

  /**
   * Check if device has organization assigned
   */
  async hasOrganization(): Promise<boolean> {
    const config = await this.getDeviceConfig();
    return config.organization_id !== null;
  }

  /**
   * Get access token
   */
  async getAccessToken(): Promise<string | null> {
    const config = await this.getDeviceConfig();
    return config.access_token;
  }

  /**
   * Get device ID
   */
  async getDeviceId(): Promise<number | null> {
    const config = await this.getDeviceConfig();
    return config.device_id;
  }

  /**
   * Get organization ID
   */
  async getOrganizationId(): Promise<number | null> {
    const config = await this.getDeviceConfig();
    return config.organization_id;
  }

  /**
   * Get activation code (pending code before activation)
   */
  async getActivationCode(): Promise<string | null> {
    const config = await this.getDeviceConfig();
    return config.activation_code;
  }

  /**
   * Set activation code (when device registers)
   */
  async setActivationCode(code: string): Promise<void> {
    await this.setDeviceConfig({ activation_code: code });
    SharedLogger.log('[DeviceConfig] Activation code saved to IndexedDB:', code);
  }

  /**
   * Clear activation code (when device is activated)
   */
  async clearActivationCode(): Promise<void> {
    await this.setDeviceConfig({ activation_code: null });
    SharedLogger.log('[DeviceConfig] Activation code cleared from IndexedDB');
  }

  /**
   * Get session ID (for device fingerprint uniqueness across browsers)
   */
  async getSessionID(): Promise<string | null> {
    const config = await this.getDeviceConfig();
    return config.session_id;
  }

  /**
   * Set session ID (persistent in IndexedDB, survives cache clear)
   */
  async setSessionID(sessionId: string): Promise<void> {
    await this.setDeviceConfig({ session_id: sessionId });
    SharedLogger.log('[DeviceConfig] Session ID saved to IndexedDB:', sessionId);
  }

  /**
   * Check if token is expired
   */
  async isTokenExpired(): Promise<boolean> {
    const config = await this.getDeviceConfig();

    if (!config.token_expires_at) {
      return true;
    }

    return Date.now() >= config.token_expires_at;
  }

  /**
   * Debug: Print current config
   */
  async debugPrintConfig(): Promise<void> {
    const config = await this.getDeviceConfig();
    console.log('[DeviceConfig] Current configuration:', {
      has_org_id: config.organization_id !== null,
      has_token: config.access_token !== null,
      has_device_id: config.device_id !== null,
      has_unique_code: config.unique_code !== null,
      token_expired: config.token_expires_at ? Date.now() >= config.token_expires_at : true,
    });
  }
}

// Export singleton instance
export const deviceConfigStorage = new DeviceConfigStorage();

// Export class for testing
export { DeviceConfigStorage };
