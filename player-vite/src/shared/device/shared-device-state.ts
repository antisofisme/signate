/**
 * Shared Device State
 * Centralized device state management with localStorage persistence
 *
 * @features
 * - Centralized device state management
 * - Automatic localStorage persistence
 * - Reactive event-driven updates via EventBus
 * - Device validation and error handling
 * - Atomic operations for complex state transitions
 * - Type-safe with TypeScript
 * - Preferences management
 * - Device Model integration
 *
 * @events_emitted
 * - **device:loaded** - Device set/updated (payload: Device)
 * - **device:restored** - Device loaded from localStorage (payload: Device)
 * - **device:status-changed** - Status updated (payload: {device, status})
 * - **device:heartbeat-sent** - Heartbeat timestamp updated (payload: Device)
 * - **device:cleared** - Device state cleared/logged out (no payload)
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { Device } from '@shared/models';
import type { DeviceData } from '@shared/models';
import type { DeviceState, DeviceStatus, ClearDeviceOptions } from './device-state.types';

/**
 * Shared Device State Class
 * Singleton pattern for centralized device state
 */
class SharedDeviceStateClass implements DeviceState {
  // Private state - Device model instance
  private currentDevice: Device | null = null;
  // ==========================================================================
  // DEVICE CORE DATA GETTERS
  // ==========================================================================

  /**
   * Get device ID from localStorage
   */
  getDeviceId(): string | null {
    return localStorage.getItem('device_id');
  }

  /**
   * Get device status from localStorage
   */
  getDeviceStatus(): DeviceStatus | null {
    const status = localStorage.getItem('device_status');
    return status as DeviceStatus | null;
  }

  /**
   * Get device activation code from localStorage
   */
  getDeviceCode(): string | null {
    return localStorage.getItem('device_code');
  }

  /**
   * Get organization ID from localStorage
   */
  getOrganizationId(): string | null {
    return localStorage.getItem('organization_id');
  }

  /**
   * Get organization PIN from localStorage (6-digit PIN for hard reset)
   */
  getOrganizationPin(): string | null {
    return localStorage.getItem('organization_pin');
  }

  /**
   * Get device JWT token from localStorage
   */
  getDeviceToken(): string | null {
    return localStorage.getItem('device_token');
  }

  /**
   * Get device name from localStorage
   */
  getDeviceName(): string | null {
    return localStorage.getItem('device_name');
  }

  /**
   * Get device platform from localStorage
   */
  getPlatform(): string | null {
    return localStorage.getItem('platform');
  }

  /**
   * Get code expiration timestamp from localStorage
   */
  getCodeExpiresAt(): string | null {
    return localStorage.getItem('code_expires_at');
  }

  // ==========================================================================
  // DEVICE CORE DATA SETTERS
  // ==========================================================================

  /**
   * Set device ID to localStorage (with logging)
   */
  setDeviceId(id: string | number): void {
    localStorage.setItem('device_id', String(id));
    SharedLogger.log(`[SharedDeviceState] Device ID set: ${id}`);
  }

  /**
   * Set device status to localStorage (with validation and logging)
   */
  setDeviceStatus(status: DeviceStatus): void {
    const validStatuses: DeviceStatus[] = ['pending', 'active', 'inactive'];
    if (!validStatuses.includes(status)) {
      SharedLogger.error(
        `[SharedDeviceState] Invalid status: ${status}. Valid: ${validStatuses.join(', ')}`
      );
      return;
    }
    localStorage.setItem('device_status', status);
    SharedLogger.log(`[SharedDeviceState] Device status set: ${status}`);
  }

  /**
   * Set device activation code to localStorage (with logging)
   */
  setDeviceCode(code: string): void {
    localStorage.setItem('device_code', code);
    SharedLogger.log(`[SharedDeviceState] Device code set: ${code}`);
  }

  /**
   * Set organization ID to localStorage (with logging)
   */
  setOrganizationId(orgId: string | number): void {
    localStorage.setItem('organization_id', String(orgId));
    SharedLogger.log(`[SharedDeviceState] Organization ID set: ${orgId}`);
  }

  /**
   * Set organization PIN to localStorage (with logging)
   * 6-digit PIN for device hard reset
   */
  setOrganizationPin(pin: string): void {
    localStorage.setItem('organization_pin', pin);
    SharedLogger.log(`[SharedDeviceState] Organization PIN set: ${pin}`);
  }

  /**
   * Set device JWT token to localStorage (with logging)
   */
  setDeviceToken(token: string): void {
    localStorage.setItem('device_token', token);
    SharedLogger.log('[SharedDeviceState] Device token set');
  }

  /**
   * Set device name to localStorage (with logging)
   */
  setDeviceName(name: string): void {
    localStorage.setItem('device_name', name);
    SharedLogger.log(`[SharedDeviceState] Device name set: ${name}`);
  }

  /**
   * Set code expiration timestamp to localStorage (with logging)
   */
  setCodeExpiresAt(expiresAt: string): void {
    localStorage.setItem('code_expires_at', expiresAt);
    SharedLogger.log(`[SharedDeviceState] Code expires at: ${expiresAt}`);
  }

  /**
   * Set device platform to localStorage (with logging)
   */
  setPlatform(platform: string): void {
    localStorage.setItem('platform', platform);
    SharedLogger.log(`[SharedDeviceState] Platform set: ${platform}`);
  }

  // ==========================================================================
  // ATOMIC OPERATIONS (Complex state transitions)
  // ==========================================================================

  /**
   * Mark device as activated (atomic operation)
   * Sets device_id, status=active, and optional device_name + organization_id
   */
  markAsActivated(
    deviceId: string | number,
    deviceName: string | null = null,
    orgId: string | number | null = null
  ): void {
    this.setDeviceId(deviceId);
    this.setDeviceStatus('active');

    if (deviceName) {
      this.setDeviceName(deviceName);
    }

    if (orgId) {
      this.setOrganizationId(orgId);
    }

    SharedLogger.log('[SharedDeviceState] ✅ Device marked as activated', {
      deviceId,
      deviceName,
      orgId,
    });
  }

  /**
   * Clear device data from localStorage (atomic operation)
   */
  clearDeviceData({ preserveAuth = false }: ClearDeviceOptions = {}): void {
    const keysToRemove = ['device_id', 'device_code', 'device_name', 'device_status', 'platform'];

    if (preserveAuth) {
      // Preserve auth data for re-registration
      const preservedToken = this.getDeviceToken();
      const preservedOrgId = this.getOrganizationId();
      const preservedOrgPin = this.getOrganizationPin();

      SharedLogger.log('[SharedDeviceState] Clearing device data (preserving auth)...', {
        hasToken: !!preservedToken,
        hasOrgId: !!preservedOrgId,
        hasOrgPin: !!preservedOrgPin,
      });

      // Clear device-specific data
      keysToRemove.forEach((key) => localStorage.removeItem(key));

      // Restore auth data
      if (preservedToken) {
        this.setDeviceToken(preservedToken);
      }
      if (preservedOrgId) {
        this.setOrganizationId(preservedOrgId);
      }
      if (preservedOrgPin) {
        this.setOrganizationPin(preservedOrgPin);
      }

      SharedLogger.log('[SharedDeviceState] ✅ Device data cleared (auth preserved)');
    } else {
      // Clear everything including auth
      keysToRemove.forEach((key) => localStorage.removeItem(key));
      localStorage.removeItem('device_token');
      localStorage.removeItem('organization_id');
      localStorage.removeItem('organization_pin');

      SharedLogger.log('[SharedDeviceState] ✅ Device data cleared (including auth)');
    }
  }

  // ==========================================================================
  // VERIFICATION HELPERS (Cleaner boolean checks)
  // ==========================================================================

  /**
   * Check if device has an ID (is registered)
   */
  hasDeviceId(): boolean {
    return !!this.getDeviceId();
  }

  /**
   * Check if device is activated
   */
  isActivated(): boolean {
    return this.getDeviceStatus() === 'active';
  }

  /**
   * Check if device has auth token
   */
  hasDeviceToken(): boolean {
    return !!this.getDeviceToken();
  }

  // ==========================================================================
  // PREFERENCES & SETTINGS (Player-specific)
  // ==========================================================================

  /**
   * Get player preference from localStorage
   */
  getPreference<T = string>(key: string, defaultValue?: T): T {
    const value = localStorage.getItem(key);
    if (value === null) {
      return defaultValue as T;
    }

    // Try to parse JSON if it looks like JSON
    if (value.startsWith('{') || value.startsWith('[')) {
      try {
        return JSON.parse(value) as T;
      } catch {
        return value as T;
      }
    }

    return value as T;
  }

  /**
   * Set player preference to localStorage
   */
  setPreference(key: string, value: unknown): void {
    const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
    localStorage.setItem(key, stringValue);
    SharedLogger.log(`[SharedDeviceState] Preference set: ${key} = ${stringValue}`);
  }

  /**
   * Remove player preference from localStorage
   */
  removePreference(key: string): void {
    localStorage.removeItem(key);
    SharedLogger.log(`[SharedDeviceState] Preference removed: ${key}`);
  }

  // ==========================================================================
  // GENERIC LOCALSTORAGE ACCESSORS (for migration compatibility)
  // ==========================================================================

  /**
   * Generic localStorage getter (use sparingly, prefer specific methods)
   */
  get<T = string>(key: string, defaultValue?: T): T {
    const value = localStorage.getItem(key);
    if (value === null) {
      return defaultValue as T;
    }
    return value as T;
  }

  /**
   * Generic localStorage setter (use sparingly, prefer specific methods)
   */
  set(key: string, value: unknown): void {
    const stringValue = String(value);
    localStorage.setItem(key, stringValue);
  }

  /**
   * Generic localStorage remover (use sparingly, prefer specific methods)
   */
  remove(key: string): void {
    localStorage.removeItem(key);
  }

  // ==========================================================================
  // DEVICE MODEL INTEGRATION (From player-vanillajs migration)
  // ==========================================================================

  /**
   * Get current device model instance
   */
  getDevice(): Device | null {
    return this.currentDevice;
  }

  /**
   * Set device (triggers device:loaded event)
   * @param deviceData - Device instance or plain object
   */
  setDevice(deviceData: Device | DeviceData): void {
    // Convert to Device model if plain object
    if (!(deviceData instanceof Device)) {
      this.currentDevice = new Device(deviceData);
    } else {
      this.currentDevice = deviceData;
    }

    // Validate device
    const validation = this.currentDevice.validate();
    if (!validation.valid) {
      SharedLogger.error('[SharedDeviceState] Invalid device data:', validation.errors);
    }

    // Save to localStorage
    this.currentDevice.saveToStorage();

    // Emit event for reactive UI updates
    SharedEventBus.emit('device:loaded', this.currentDevice);

    SharedLogger.log('[SharedDeviceState] Device set:', this.currentDevice.toJSON());
  }

  /**
   * Update device last_seen timestamp (heartbeat)
   */
  updateLastSeen(): void {
    if (!this.currentDevice) return;

    this.currentDevice.last_seen = new Date().toISOString();

    // Emit event
    SharedEventBus.emit('device:heartbeat-sent', this.currentDevice);
  }

  /**
   * Clear device (logout) - triggers device:cleared event
   */
  clearDevice(): void {
    this.currentDevice = null;

    // Clear localStorage (including device_token)
    const keysToRemove = [
      'device_id',
      'device_code',
      'device_name',
      'device_status',
      'organization_id',
      'organization_pin',
      'platform',
      'device_token',
    ];

    keysToRemove.forEach((key) => localStorage.removeItem(key));

    // Emit event
    SharedEventBus.emit('device:cleared');

    SharedLogger.log('[SharedDeviceState] Device cleared');
  }

  /**
   * Load device from localStorage (triggers device:restored event)
   */
  loadFromStorage(): Device | null {
    const device = Device.fromStorage();

    if (device) {
      this.currentDevice = device;

      // Emit event (without re-saving)
      SharedEventBus.emit('device:restored', device);

      SharedLogger.log('[SharedDeviceState] Device restored from storage');
    }

    return device;
  }

  /**
   * Check if device is registered
   */
  isRegistered(): boolean {
    return this.currentDevice !== null && this.currentDevice.id !== null;
  }

  /**
   * Check if device is active
   */
  isActive(): boolean {
    return this.currentDevice !== null && this.currentDevice.isActive();
  }

  /**
   * Check if device is online
   */
  isOnline(): boolean {
    return this.currentDevice !== null && this.currentDevice.isOnline();
  }

  /**
   * Override setDeviceStatus to emit event
   */
  setDeviceStatusWithEvent(status: DeviceStatus): void {
    if (!this.currentDevice) {
      SharedLogger.warn('[SharedDeviceState] No device loaded');
      return;
    }

    this.currentDevice.status = status;
    this.currentDevice.saveToStorage();

    // Also update localStorage directly for compatibility
    this.setDeviceStatus(status);

    // Emit event
    SharedEventBus.emit('device:status-changed', {
      device: this.currentDevice,
      status: status,
    });

    SharedLogger.log('[SharedDeviceState] Status changed:', status);
  }
}

// Export singleton instance
export const SharedDeviceState = new SharedDeviceStateClass();
