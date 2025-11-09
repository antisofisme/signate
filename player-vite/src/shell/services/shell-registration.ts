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

      // Validate pending code format - should be pure numeric (6 digits)
      if (activationCode && !/^\d{6}$/.test(activationCode)) {
        SharedLogger.warn('[ShellRegistration] Invalid pending code format (contains letters), clearing:', activationCode);
        this.setPendingCode(null);
        activationCode = null;
      }

      if (!activationCode) {
        activationCode = this.generateActivationCode();
        this.setPendingCode(activationCode);
        SharedLogger.log('[ShellRegistration] Generated new activation code:', activationCode);

        // Update UI immediately with generated code (before API call)
        if (window.ShellActivationScreen) {
          SharedLogger.log('[ShellRegistration] Updating UI with generated code...');
          window.ShellActivationScreen.updateCode(activationCode);
        }
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

      // Request activation code (register device)
      const data = await SharedAPIClient.post<RegistrationResponse>(
        `${config.api.baseURL}/api/v1/devices/request-code`,
        requestBody
      );

      SharedLogger.log('[ShellRegistration] ✅ Registration successful:', data);

      // Store device data using SharedDeviceState
      SharedDeviceState.setDeviceId(data.device_id);
      SharedDeviceState.setDeviceCode(data.unique_code);
      SharedDeviceState.setDeviceStatus('pending');

      // Store expiration timestamp for countdown timer persistence
      if (data.expires_at) {
        SharedDeviceState.setCodeExpiresAt(data.expires_at);
      }

      if (data.organization_id) {
        SharedDeviceState.setOrganizationId(data.organization_id);
      }

      if (data.device_token) {
        SharedDeviceState.setDeviceToken(data.device_token);
      }

      // Clear retry count on success
      this.clearRetryCount();

      // Update UI with new activation code and start countdown
      SharedLogger.log('[ShellRegistration] 🎯 Activation code:', data.unique_code);
      if (window.ShellActivationScreen) {
        SharedLogger.log('[ShellRegistration] Updating UI with new code...');
        window.ShellActivationScreen.updateCode(data.unique_code);

        // Start countdown timer if expires_at is provided
        if (data.expires_at) {
          SharedLogger.log('[ShellRegistration] Starting countdown timer, expires at:', data.expires_at);
          window.ShellActivationScreen.startCountdown(data.expires_at);
        }

        SharedLogger.log('[ShellRegistration] ✅ UI updated with code:', data.unique_code);
      } else {
        SharedLogger.error('[ShellRegistration] ❌ window.ShellActivationScreen not available!');
      }

      // Start activation polling
      if (window.ShellActivationPoll) {
        window.ShellActivationPoll.startPolling();
      }
    } catch (error) {
      SharedLogger.error('[ShellRegistration] ❌ Registration failed:', error);

      // Check if error is due to duplicate code (code already in use)
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isDuplicateCode = errorMessage.includes('already in use') || errorMessage.includes('duplicate');

      if (isDuplicateCode) {
        SharedLogger.warn('[ShellRegistration] ⚠️ Code collision detected, generating new code...');
        // Clear pending code to force new code generation on retry
        this.setPendingCode(null);
        // Don't increment retry count for duplicate code - just retry immediately
        this.retryTimeout = window.setTimeout(() => {
          void this.registerDevice();
        }, 1000); // Retry after 1 second
        return;
      }

      // Increment retry count for other errors
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
