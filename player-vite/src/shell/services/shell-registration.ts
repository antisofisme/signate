/**
 * Shell Registration Service
 * Handles device registration and activation code management
 *
 * @features
 * - 6-digit activation code generation
 * - Exponential backoff retry logic
 * - Platform detection
 * - Registration state management
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import type { ShellRegistration as IShellRegistration, RegistrationResponse, PlatformInfo } from '../types/shell.types';

/**
 * Shell Registration Class
 * Singleton pattern for device registration
 */
class ShellRegistrationClass implements IShellRegistration {
  private retryTimeout: number | null = null;
  private isRegistering = false;

  /**
   * Generate 6-digit activation code
   */
  generateActivationCode(): string {
    return Math.floor(100000 + Math.random() * 900000).toString();
  }

  /**
   * Get pending code from localStorage
   */
  getPendingCode(): string | null {
    return localStorage.getItem('pending_activation_code');
  }

  /**
   * Set pending code in localStorage
   */
  setPendingCode(code: string | null): void {
    if (code) {
      localStorage.setItem('pending_activation_code', code);
      SharedLogger.log('[ShellRegistration] Pending code saved:', code);
    } else {
      localStorage.removeItem('pending_activation_code');
      SharedLogger.log('[ShellRegistration] Pending code cleared');
    }
  }

  /**
   * Get retry count from localStorage
   */
  getRetryCount(): number {
    const count = localStorage.getItem('registration_retry_count');
    return count ? parseInt(count, 10) : 0;
  }

  /**
   * Increment retry count
   */
  incrementRetryCount(): number {
    const count = this.getRetryCount() + 1;
    localStorage.setItem('registration_retry_count', count.toString());
    return count;
  }

  /**
   * Clear retry count (on success or manual reset)
   */
  clearRetryCount(): void {
    localStorage.removeItem('registration_retry_count');
  }

  /**
   * Calculate next retry delay with exponential backoff
   */
  calculateRetryDelay(retryCount: number): number {
    // Calculate exponential backoff
    const exponentialDelay =
      config.retry.initialRetryDelay * Math.pow(config.retry.backoffMultiplier, retryCount);

    // Cap at max delay
    const cappedDelay = Math.min(exponentialDelay, config.retry.maxRetryDelay);

    // Add jitter (+/- 20%) to prevent thundering herd
    const jitter = cappedDelay * 0.2 * (Math.random() * 2 - 1);
    const finalDelay = Math.max(1000, cappedDelay + jitter);

    return Math.floor(finalDelay);
  }

  /**
   * Detect platform type from user agent
   */
  detectPlatform(): PlatformInfo {
    const ua = navigator.userAgent.toLowerCase();

    // TV platforms (check first!)
    if (ua.includes('webos') || ua.includes('web0s')) {
      return { type: 'webOS', userAgent: navigator.userAgent };
    }
    if (ua.includes('tizen')) {
      return { type: 'Tizen', userAgent: navigator.userAgent };
    }
    if (ua.includes('android tv')) {
      return { type: 'Android TV', userAgent: navigator.userAgent };
    }

    // Desktop browsers
    if (ua.includes('edg/') || ua.includes('edge')) {
      return { type: 'Edge', userAgent: navigator.userAgent };
    }
    if (ua.includes('firefox')) {
      return { type: 'Firefox', userAgent: navigator.userAgent };
    }
    if (ua.includes('chrome')) {
      return { type: 'Chrome', userAgent: navigator.userAgent };
    }
    if (ua.includes('safari')) {
      return { type: 'Safari', userAgent: navigator.userAgent };
    }

    return { type: 'Browser', userAgent: navigator.userAgent };
  }

  /**
   * Register device to backend
   * Auto-displays 6-digit code, organization assigned by admin during activation
   */
  async registerDevice(): Promise<void> {
    // Guard 1: Prevent concurrent registrations
    if (this.isRegistering) {
      SharedLogger.warn('[ShellRegistration] Registration already in progress, skipping...');
      return;
    }

    // Guard 2: Check if already registered
    const existingDeviceId = SharedDeviceState.getDeviceId();
    if (existingDeviceId) {
      SharedLogger.warn('[ShellRegistration] Device already registered, skipping');
      SharedLogger.log('[ShellRegistration] Existing device_id:', existingDeviceId);

      // Clear orphaned pending code
      const orphanedCode = this.getPendingCode();
      if (orphanedCode) {
        SharedLogger.warn('[ShellRegistration] Clearing orphaned pending code:', orphanedCode);
        this.setPendingCode(null);
      }

      return;
    }

    // Set registration flag
    this.isRegistering = true;

    try {
      // Use existing pending code or generate new one
      let activationCode = this.getPendingCode();

      if (!activationCode) {
        activationCode = this.generateActivationCode();
        this.setPendingCode(activationCode);
        SharedLogger.log('[ShellRegistration] Generated new activation code:', activationCode);
      } else {
        SharedLogger.log('[ShellRegistration] Using existing pending code:', activationCode);
      }

      // Detect platform
      const platformInfo = this.detectPlatform();
      SharedLogger.log('[ShellRegistration] Platform detected:', platformInfo);

      // Prepare request body
      const requestBody = {
        code: activationCode,
        platform: platformInfo.type,
      };

      SharedLogger.log('[ShellRegistration] Registering device...');

      // Register device
      const data = await SharedAPIClient.post<RegistrationResponse>(
        `${config.api.baseURL}/api/devices/register`,
        requestBody
      );

      SharedLogger.log('[ShellRegistration] ✅ Registration successful:', data);

      // Store device data using SharedDeviceState
      SharedDeviceState.setDeviceId(data.device_id);
      SharedDeviceState.setDeviceCode(data.code);
      SharedDeviceState.setDeviceStatus('pending');

      if (data.organization_id) {
        SharedDeviceState.setOrganizationId(data.organization_id);
      }

      if (data.device_token) {
        SharedDeviceState.setDeviceToken(data.device_token);
      }

      // Clear retry count on success
      this.clearRetryCount();

      // UI update would go here
      SharedLogger.log('[ShellRegistration] 🎯 Activation code:', data.code);

      // Start activation polling
      if (window.ShellActivationPoll) {
        window.ShellActivationPoll.startPolling();
      }
    } catch (error) {
      SharedLogger.error('[ShellRegistration] ❌ Registration failed:', error);

      // Increment retry count
      const retryCount = this.incrementRetryCount();

      // Check if max retries exceeded
      if (retryCount >= config.retry.maxRetryCount) {
        SharedLogger.error(
          `[ShellRegistration] ⛔ Max retries (${config.retry.maxRetryCount}) exceeded - STOPPING`
        );
        // Clear pending code to force new code on manual retry
        this.setPendingCode(null);
        this.clearRetryCount();
        return;
      }

      // Calculate retry delay
      const retryDelay = this.calculateRetryDelay(retryCount);
      const retrySeconds = Math.floor(retryDelay / 1000);

      SharedLogger.warn(
        `[ShellRegistration] ⏳ Retry ${retryCount}/${config.retry.maxRetryCount} in ${retrySeconds}s...`
      );

      // Schedule retry
      this.retryTimeout = window.setTimeout(() => {
        void this.registerDevice();
      }, retryDelay);
    } finally {
      this.isRegistering = false;
    }
  }

  /**
   * Cancel pending retry
   */
  cancelRetry(): void {
    if (this.retryTimeout !== null) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = null;
      SharedLogger.log('[ShellRegistration] Retry cancelled');
    }
  }

  /**
   * Reset registration state
   */
  reset(): void {
    this.cancelRetry();
    this.setPendingCode(null);
    this.clearRetryCount();
    this.isRegistering = false;
    SharedLogger.log('[ShellRegistration] Registration state reset');
  }
}

// Export singleton instance
export const ShellRegistration = new ShellRegistrationClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.ShellRegistration = ShellRegistration;
}
