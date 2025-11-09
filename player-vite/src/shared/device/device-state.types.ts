/**
 * Device State Type Definitions
 */

import type { DeviceStatus } from '@shared/models';

export interface ClearDeviceOptions {
  preserveAuth?: boolean;
}

// Re-export DeviceStatus from models for convenience
export type { DeviceStatus };

export interface DeviceState {
  // Core getters
  getDeviceId(): string | null;
  getDeviceStatus(): DeviceStatus | null;
  getDeviceCode(): string | null;
  getOrganizationId(): string | null;
  getDeviceToken(): string | null;
  getDeviceName(): string | null;

  // Core setters
  setDeviceId(id: string | number): void;
  setDeviceStatus(status: DeviceStatus): void;
  setDeviceCode(code: string): void;
  setOrganizationId(orgId: string | number): void;
  setDeviceToken(token: string): void;
  setDeviceName(name: string): void;

  // Atomic operations
  markAsActivated(deviceId: string | number, deviceName?: string | null, orgId?: string | number | null): void;
  clearDeviceData(options?: ClearDeviceOptions): void;

  // Verification helpers
  hasDeviceId(): boolean;
  isActivated(): boolean;
  hasDeviceToken(): boolean;

  // Preferences
  getPreference<T = string>(key: string, defaultValue?: T): T;
  setPreference(key: string, value: unknown): void;
  removePreference(key: string): void;

  // Generic storage accessors
  get<T = string>(key: string, defaultValue?: T): T;
  set(key: string, value: unknown): void;
  remove(key: string): void;
}
