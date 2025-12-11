/**
 * Device Model
 *
 * Represents a registered signage display device with validation,
 * computed properties, and localStorage integration.
 *
 * @features
 * - 6-digit activation code validation
 * - Online/offline status based on heartbeat (last_seen < 5 minutes)
 * - Device age calculation
 * - localStorage persistence
 * - Status lifecycle: pending → active → inactive
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';

/**
 * Device status enumeration
 */
export type DeviceStatus = 'pending' | 'active' | 'inactive' | 'released';

/**
 * Device data interface
 */
export interface DeviceData {
  id?: number | null;
  code?: string | null;
  name?: string | null;
  status?: DeviceStatus;
  organization_id?: number | null;
  platform?: string;
  device_token?: string | null;
  last_seen?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * Device storage interface
 */
export interface DeviceStorage {
  device_id: number | null;
  device_code: string | null;
  device_name: string | null;
  device_status: DeviceStatus;
  organization_id: number | null;
  platform: string;
  device_token: string | null;
}

/**
 * Validation result interface
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Device Model Class
 */
export class Device {
  id: number | null;
  code: string | null;
  name: string | null;
  status: DeviceStatus;
  organization_id: number | null;
  platform: string;
  device_token: string | null;
  last_seen: string | null;
  created_at: string | null;
  updated_at: string | null;

  constructor(data: DeviceData = {}) {
    this.id = data.id ?? null;
    this.code = data.code ?? null;
    this.name = data.name ?? null;
    this.status = data.status ?? 'pending';
    this.organization_id = data.organization_id ?? null;
    this.platform = data.platform ?? 'Browser';
    this.device_token = data.device_token ?? null;
    this.last_seen = data.last_seen ?? null;
    this.created_at = data.created_at ?? null;
    this.updated_at = data.updated_at ?? null;
  }

  /**
   * Validate device data
   */
  validate(): ValidationResult {
    const errors: string[] = [];

    if (!this.code || this.code.length !== 6) {
      errors.push('Activation code must be 6 digits');
    }

    if (!this.name || this.name.trim().length === 0) {
      errors.push('Device name is required');
    }

    if (!['pending', 'active', 'inactive'].includes(this.status)) {
      errors.push('Invalid device status');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Check if device is active
   */
  isActive(): boolean {
    return this.status === 'active';
  }

  /**
   * Check if device is online (last_seen within 5 minutes)
   */
  isOnline(): boolean {
    if (!this.last_seen) return false;

    const lastSeenDate = new Date(this.last_seen);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastSeenDate.getTime()) / 1000 / 60;

    return diffMinutes < 5;
  }

  /**
   * Get device age in days
   */
  getAgeInDays(): number {
    if (!this.created_at) return 0;

    const createdDate = new Date(this.created_at);
    const now = new Date();
    const diffDays = Math.floor(
      (now.getTime() - createdDate.getTime()) / 1000 / 60 / 60 / 24
    );

    return diffDays;
  }

  /**
   * Convert to plain object for API calls
   */
  toJSON(): DeviceData {
    return {
      id: this.id,
      code: this.code,
      name: this.name,
      status: this.status,
      organization_id: this.organization_id,
      platform: this.platform,
      last_seen: this.last_seen,
      created_at: this.created_at,
      updated_at: this.updated_at,
    };
  }

  /**
   * Convert to localStorage format
   */
  toStorage(): DeviceStorage {
    return {
      device_id: this.id,
      device_code: this.code,
      device_name: this.name,
      device_status: this.status,
      organization_id: this.organization_id,
      platform: this.platform,
      device_token: this.device_token,
    };
  }

  /**
   * Load from SharedDeviceState (localStorage abstraction)
   */
  static fromStorage(): Device | null {
    const id = SharedDeviceState.getDeviceId();
    const code = SharedDeviceState.getDeviceCode();
    const name = SharedDeviceState.getDeviceName();
    const status = SharedDeviceState.getDeviceStatus() as DeviceStatus;
    const organization_id = SharedDeviceState.getOrganizationId();
    const platform = SharedDeviceState.getPlatform();
    const device_token = SharedDeviceState.getDeviceToken();

    if (!id) return null;

    return new Device({
      id: parseInt(id),
      code,
      name,
      status,
      organization_id: organization_id ? parseInt(organization_id) : null,
      platform: platform || 'Browser',
      device_token,
    });
  }

  /**
   * Save to SharedDeviceState (localStorage abstraction)
   */
  saveToStorage(): void {
    if (this.id) SharedDeviceState.setDeviceId(this.id);
    if (this.code) SharedDeviceState.setDeviceCode(this.code);
    if (this.name) SharedDeviceState.setDeviceName(this.name);
    if (this.status) SharedDeviceState.setDeviceStatus(this.status);
    if (this.organization_id) SharedDeviceState.setOrganizationId(this.organization_id);
    if (this.platform) SharedDeviceState.setPlatform(this.platform);
    if (this.device_token) SharedDeviceState.setDeviceToken(this.device_token);
  }
}

SharedLogger.log('[Models/Device] Device model loaded');
