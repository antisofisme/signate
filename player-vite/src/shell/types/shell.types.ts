/**
 * Shell Layer Type Definitions
 * Types for device registration, activation, and bootstrap
 */

export interface RegistrationResponse {
  success: boolean;
  device_id: number;
  code: string;
  organization_id: number | null;
  device_token?: string;
  message?: string;
}

export interface ActivationCheckResponse {
  activated: boolean;
  device_id?: number;
  device_name?: string;
  organization_id?: number;
  organization_pin?: string; // 6-digit PIN for hard reset
  expired?: boolean;
  message?: string;
}

export interface VerifyDeviceResponse {
  valid: boolean;
  device_id: number;
  device_name: string;
  device_status: 'pending' | 'active' | 'inactive';
  organization_id: number;
  message?: string;
}

export interface PlatformInfo {
  type: 'webOS' | 'Tizen' | 'Android TV' | 'Chrome' | 'Firefox' | 'Edge' | 'Safari' | 'Browser';
  userAgent: string;
}

export interface RetryConfig {
  maxRetries: number;
  currentRetry: number;
  nextDelay: number;
  elapsedTime: string;
}

export interface ShellRegistration {
  generateActivationCode(): string;
  registerDevice(): Promise<void>;
  getPendingCode(): string | null;
  setPendingCode(code: string | null): void;
  getRetryCount(): number;
  incrementRetryCount(): number;
  clearRetryCount(): void;
  calculateRetryDelay(retryCount: number): number;
  detectPlatform(): PlatformInfo;
}

export interface ShellActivationPoll {
  startPolling(): void;
  stopPolling(): void;
  checkActivation(): Promise<void>;
}

export interface ShellBootstrap {
  init(): Promise<void>;
  verifyDevice(): Promise<boolean>;
  startPlayer(): void;
}
