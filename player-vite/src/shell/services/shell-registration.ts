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
import { deviceConfigStorage } from '@shared/storage';
import { getOrCreateDeviceUUID } from '@shared/utils/device-fingerprint';
import type { ShellRegistration as IShellRegistration, RegistrationResponse, PlatformInfo } from '@shell/types/shell.types';
import { ServiceRegistry } from '@shared/services/service-registry';
import { getShellBootstrap, getShellActivationPoll, getShellActivationScreen } from '@shared/services';

/**
 * Shell Registration Class
 * Singleton pattern for device registration
 */
class ShellRegistrationClass implements IShellRegistration {
  private retryTimeout: number | null = null;
  private isRegistering = false;
  private registrationQueue: Promise<void> = Promise.resolve();
  private queuedCount = 0;

  /**
   * Validate registration response structure
   * Ensures all required fields are present before accessing them
   */
  private validateRegistrationResponse(data: any): data is RegistrationResponse {
    if (!data) {
      SharedLogger.error('[ShellRegistration] Registration response is null or undefined');
      return false;
    }

    // Check required fields
    const requiredFields = ['device_id', 'unique_code', 'status'];
    const missingFields = requiredFields.filter(field => !(field in data) || data[field] === null || data[field] === undefined);

    if (missingFields.length > 0) {
      SharedLogger.error(`[ShellRegistration] Registration response missing required fields: ${missingFields.join(', ')}`);
      SharedLogger.error('[ShellRegistration] Received data:', data);
      return false;
    }

    return true;
  }

  /**
   * Generate 6-digit activation code
   */
  generateActivationCode(): string {
    return Math.floor(100000 + Math.random() * 900000).toString();
  }

  /**
   * Get pending code from IndexedDB (persistent across cache clears)
   */
  async getPendingCode(): Promise<string | null> {
    return await deviceConfigStorage.getActivationCode();
  }

  /**
   * Set pending code in IndexedDB (persistent)
   */
  async setPendingCode(code: string | null): Promise<void> {
    if (code) {
      await deviceConfigStorage.setActivationCode(code);
      SharedLogger.log('[ShellRegistration] Pending code saved to IndexedDB:', code);
    } else {
      await deviceConfigStorage.clearActivationCode();
      SharedLogger.log('[ShellRegistration] Pending code cleared from IndexedDB');
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
   * Register device to backend (internal implementation)
   * Auto-displays 6-digit code, organization assigned by admin during activation
   * @param forceRenew - Force request new code even if device exists (for expired code renewal)
   */
  private async _registerDeviceInternal(forceRenew = false): Promise<void> {
    SharedLogger.log('[ShellRegistration] 🎯 _registerDeviceInternal() called', { forceRenew });
    SharedLogger.log('[ShellRegistration] 🔍 DEBUG - forceRenew type:', typeof forceRenew);
    SharedLogger.log('[ShellRegistration] 🔍 DEBUG - forceRenew value:', forceRenew);
    SharedLogger.log('[ShellRegistration] 🔍 DEBUG - !forceRenew:', !forceRenew);

    // Guard 1: Prevent concurrent registrations
    if (this.isRegistering) {
      SharedLogger.warn('[ShellRegistration] Registration already in progress, skipping...');
      return;
    }

    // Guard 2: Check if already registered (skip if forceRenew=true)
    if (!forceRenew) {
      const existingDeviceId = SharedDeviceState.getDeviceId();
      SharedLogger.log('[ShellRegistration] Checking existing device_id:', existingDeviceId);

      if (existingDeviceId) {
        SharedLogger.warn('[ShellRegistration] Device already registered, skipping');
        SharedLogger.log('[ShellRegistration] Existing device_id:', existingDeviceId);
        return;
      }
    } else {
      SharedLogger.log('[ShellRegistration] ⚡ Force renew enabled, bypassing device_id check');
    }

    // Set registration flag
    this.isRegistering = true;
    SharedLogger.log('[ShellRegistration] ✅ Starting registration process...');

    try {
      // Get device UUID (fingerprint)
      const deviceUUID = getOrCreateDeviceUUID();
      SharedLogger.log('[ShellRegistration] Device UUID (fingerprint):', deviceUUID);

      // Guard 3: Check if device already exists with this fingerprint (skip if forceRenew=true)
      // This prevents race condition when cache is cleared but device is already registered
      SharedLogger.log('[ShellRegistration] 🔍 DEBUG - Before Guard 3 - forceRenew:', forceRenew);
      SharedLogger.log('[ShellRegistration] 🔍 DEBUG - Before Guard 3 - !forceRenew:', !forceRenew);
      if (!forceRenew) {
        SharedLogger.log('[ShellRegistration] ✅ Entering Guard 3 (!forceRenew is TRUE)');
        SharedLogger.log('[ShellRegistration] Checking for existing device with this fingerprint...');

        try {
          const existingCheck = await SharedAPIClient.get<any>(
            `${config.api.baseURL}/api/v1/devices/check-activation-by-uuid/${deviceUUID}`
          );

          if (existingCheck && existingCheck.device_id) {
            SharedLogger.log('[ShellRegistration] ✅ Found existing device!', existingCheck);

          // Restore device state
          SharedDeviceState.setDeviceId(existingCheck.device_id);
          SharedDeviceState.setDeviceCode(existingCheck.unique_code);
          SharedDeviceState.setDeviceStatus(existingCheck.status);

          if (existingCheck.device_name) {
            SharedDeviceState.setDeviceName(existingCheck.device_name);
          }

          if (existingCheck.organization_id) {
            SharedDeviceState.setOrganizationId(existingCheck.organization_id);
          }

          // Update UI with existing code
          if (getShellActivationScreen() && existingCheck.unique_code) {
            getShellActivationScreen().updateCode(existingCheck.unique_code);
          }

          // If device is active, start player mode
          if (existingCheck.status === 'active') {
            SharedLogger.log('[ShellRegistration] Device is already active → Starting player');
            // Trigger player mode
            if (getShellBootstrap()) {
              getShellBootstrap().startPlayer();
            }
            return;
          }

          // If device is pending, start polling
          if (existingCheck.status === 'pending') {
            SharedLogger.log('[ShellRegistration] Device is pending → Start polling');
            if (getShellActivationPoll()) {
              getShellActivationPoll().startPolling();
            }
          }

          return;
        }
      } catch (checkError) {
        SharedLogger.log('[ShellRegistration] No existing device found (expected for new device)');
      }
    } else {
      SharedLogger.log('[ShellRegistration] ⚡ Force renew enabled - skipping UUID check, will request new code');
    }

    // No existing device - proceed with registration
    SharedLogger.log('[ShellRegistration] 🔍 DEBUG - About to proceed with registration...');
    SharedLogger.log('[ShellRegistration] Proceeding with new device registration...');

    // Generate temporary activation code for first-time registration request
    // Backend will either accept this code OR return existing code for this device
    const activationCode = this.generateActivationCode();
    SharedLogger.log('[ShellRegistration] Generated temporary code for registration:', activationCode);
    SharedLogger.log('[ShellRegistration] Backend may return different code if device already exists');

    // Detect platform
    const platformInfo = this.detectPlatform();
    SharedLogger.log('[ShellRegistration] Platform detected:', platformInfo);

    // Check if device has organization (for CMS release scenario)
    const deviceConfig = await deviceConfigStorage.getDeviceConfig();
    const hasOrganization = deviceConfig.organization_id !== null;

    // Prepare request body
    const requestBody: any = {
      code: activationCode,
      platform: platformInfo.type,
      device_uuid: deviceUUID, // Send fingerprint for code persistence
    };

    // Include organization_id if exists (CMS release scenario)
    // If org_id exists → device will be assigned to SAME organization
    // If no org_id → device will go to GLOBAL pending list
    if (hasOrganization) {
      requestBody.organization_id = deviceConfig.organization_id;
      SharedLogger.log('[ShellRegistration] Including organization_id (CMS release):', deviceConfig.organization_id);
    } else {
      SharedLogger.log('[ShellRegistration] No organization_id (global pending or first registration)');
    }

    SharedLogger.log('[ShellRegistration] 📡 Sending registration request to backend...');
    SharedLogger.log('[ShellRegistration] Request URL:', `${config.api.baseURL}/api/v1/devices/request-code`);
    SharedLogger.log('[ShellRegistration] Request body:', requestBody);

    // Request activation code (register device)
    const data = await SharedAPIClient.post<RegistrationResponse>(
      `${config.api.baseURL}/api/v1/devices/request-code`,
      requestBody
    );

    SharedLogger.log('[ShellRegistration] 📥 Response received from backend:', data);

    // Validate response structure before accessing fields
    if (!this.validateRegistrationResponse(data)) {
      throw new Error('Invalid registration response structure from backend');
    }

    SharedLogger.log('[ShellRegistration] ✅ Registration successful:', data);

    // Check if backend returned different code (existing device reuse)
    if (data.unique_code !== activationCode) {
      SharedLogger.warn(
        `[ShellRegistration] Backend returned different code! Temp: ${activationCode}, Actual: ${data.unique_code}`
      );
      SharedLogger.log('[ShellRegistration] ✅ This is CORRECT - backend reused existing code for this device UUID');
      SharedLogger.log('[ShellRegistration] Code persistence is working!');
    } else {
      SharedLogger.log('[ShellRegistration] Backend accepted our generated code (new device)');
    }

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

    // Update UI with activation code from backend
    SharedLogger.log('[ShellRegistration] 🎯 Activation code from backend:', data.unique_code);
    if (getShellActivationScreen()) {
      SharedLogger.log('[ShellRegistration] Updating UI with backend code...');
      getShellActivationScreen().updateCode(data.unique_code);
      SharedLogger.log('[ShellRegistration] ✅ UI updated with code:', data.unique_code);
    } else {
      SharedLogger.error('[ShellRegistration] ❌ getShellActivationScreen() not available!');
    }

    // Start activation polling
    if (getShellActivationPoll()) {
      getShellActivationPoll().startPolling();
    }
    } catch (error) {
      SharedLogger.error('[ShellRegistration] ❌ Registration failed:', error);
      SharedLogger.error('[ShellRegistration] 🔍 DEBUG - Error details:', JSON.stringify(error));

      // Check if error is due to duplicate code (code already in use)
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isDuplicateCode = errorMessage.includes('already in use') || errorMessage.includes('duplicate');

      if (isDuplicateCode) {
        SharedLogger.warn('[ShellRegistration] ⚠️ Code collision detected, will retry with new random code...');
        // Don't increment retry count for duplicate code - just retry immediately
        this.retryTimeout = window.setTimeout(() => {
          void this.registerDevice();
        }, 1000); // Retry after 1 second with new random code
        return;
      }

      // Increment retry count for other errors
      const retryCount = this.incrementRetryCount();

      // Check if max retries exceeded
      if (retryCount >= config.retry.maxRetryCount) {
        SharedLogger.error(
          `[ShellRegistration] ⛔ Max retries (${config.retry.maxRetryCount}) exceeded - STOPPING`
        );
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
        void this._registerDeviceInternal();
      }, retryDelay);
    } finally {
      this.isRegistering = false;
    }
  }

  /**
   * Register device to backend (public method with queue)
   * Ensures serial execution to prevent race conditions
   * @param forceRenew - Force request new code even if device exists (for expired code renewal)
   */
  async registerDevice(forceRenew = false): Promise<void> {
    // Check if too many calls are queued (potential bug)
    if (this.queuedCount > 5) {
      SharedLogger.warn('[ShellRegistration] Too many queued registrations, rejecting new request');
      return;
    }

    this.queuedCount++;
    SharedLogger.log(`[ShellRegistration] Queueing registration (queue size: ${this.queuedCount})`);

    // Chain promise to queue for serial execution
    this.registrationQueue = this.registrationQueue
      .then(async () => {
        try {
          await this._registerDeviceInternal(forceRenew);
        } finally {
          this.queuedCount--;
          SharedLogger.log(`[ShellRegistration] Registration completed (queue size: ${this.queuedCount})`);
        }
      })
      .catch((error) => {
        this.queuedCount--;
        SharedLogger.error('[ShellRegistration] Queued registration failed:', error);
        throw error;
      });

    return this.registrationQueue;
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
  async reset(): Promise<void> {
    this.cancelRetry();
    this.clearRetryCount();
    this.isRegistering = false;
    SharedLogger.log('[ShellRegistration] Registration state reset');
  }
}

// Export singleton instance
export const ShellRegistration = new ShellRegistrationClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellRegistration', ShellRegistration);
}
