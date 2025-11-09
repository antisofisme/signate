/**
 * Shell Registration Module
 * Handles device registration and activation polling
 */

window.ShellRegistration = {
    retryTimeout: null, // Store retry timeout for cancellation
    isRegistering: false, // Prevent concurrent registrations

    // FIX 4: Add retry limit and backoff configuration
    MAX_RETRIES: 20,  // Maximum 20 retries = ~3.3 minutes
    INITIAL_RETRY_DELAY_MS: 5000,  // Start at 5 seconds
    MAX_RETRY_DELAY_MS: 30000,  // Cap at 30 seconds
    RETRY_BACKOFF_MULTIPLIER: 1.5,  // Exponential: 5s → 7.5s → 11.25s → ...

    /**
     * Generate 6-digit activation code
     */
    generateActivationCode: function() {
        return Math.floor(100000 + Math.random() * 900000).toString();
    },

    // FIX 3: Use localStorage for pendingCode persistence
    /**
     * Get pending code from localStorage
     */
    getPendingCode: function() {
        return localStorage.getItem('pending_activation_code');
    },

    /**
     * Set pending code in localStorage
     */
    setPendingCode: function(code) {
        if (code) {
            localStorage.setItem('pending_activation_code', code);
            SharedLogger.log('[Shell/Registration] Pending code saved to localStorage:', code);
        } else {
            localStorage.removeItem('pending_activation_code');
            SharedLogger.log('[Shell/Registration] Pending code cleared from localStorage');
        }
    },

    // FIX 4: Retry limit helpers
    /**
     * Get retry count from localStorage
     */
    getRetryCount: function() {
        const count = localStorage.getItem('registration_retry_count');
        return count ? parseInt(count) : 0;
    },

    /**
     * Increment retry count
     */
    incrementRetryCount: function() {
        const count = this.getRetryCount() + 1;
        localStorage.setItem('registration_retry_count', count.toString());
        return count;
    },

    /**
     * Clear retry count (on success or manual reset)
     */
    clearRetryCount: function() {
        localStorage.removeItem('registration_retry_count');
    },

    /**
     * Calculate next retry delay with exponential backoff
     */
    calculateRetryDelay: function(retryCount) {
        // Calculate exponential backoff: initialDelay * (multiplier ^ retryCount)
        const exponentialDelay = this.INITIAL_RETRY_DELAY_MS *
            Math.pow(this.RETRY_BACKOFF_MULTIPLIER, retryCount);

        // Cap at MAX_RETRY_DELAY_MS
        const cappedDelay = Math.min(exponentialDelay, this.MAX_RETRY_DELAY_MS);

        // Add jitter (+/- 20%) to prevent thundering herd
        const jitter = cappedDelay * 0.2 * (Math.random() * 2 - 1);
        const finalDelay = Math.max(1000, cappedDelay + jitter);

        return Math.floor(finalDelay);
    },

    /**
     * Calculate total elapsed time for retries
     * @private
     */
    _calculateElapsedTime: function(retryCount) {
        let totalMs = 0;
        for (let i = 0; i < retryCount; i++) {
            totalMs += this.calculateRetryDelay(i);
        }
        const seconds = Math.floor(totalMs / 1000);
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ${seconds % 60}s`;
    },

    /**
     * Simple platform detection (fallback if ShellHeartbeat not loaded)
     */
    detectPlatformSimple: function() {
        const ua = navigator.userAgent.toLowerCase();

        // TV platforms (CHECK FIRST!)
        if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
        if (ua.includes('tizen')) return 'Tizen';
        if (ua.includes('android tv')) return 'Android TV';

        // Desktop browsers (check after TV platforms)
        if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
        if (ua.includes('firefox')) return 'Firefox';
        if (ua.includes('chrome')) return 'Chrome';
        if (ua.includes('safari')) return 'Safari';

        return 'Browser';
    },

    /**
     * Register device to backend (No-PIN Flow)
     * Auto-displays 6-digit code, organization assigned by admin during activation
     *
     * 🔒 SECURITY FLOW:
     * 1. First-time registration → No device_token, admin activates from their org
     * 2. Re-registration (after release) → Sends device_token JWT, backend extracts org_id
     */
    registerDevice: async function() {
        const state = window.ShellState;

        // 🛡️ GUARD 1: Prevent concurrent registrations
        if (this.isRegistering) {
            SharedLogger.warn('[Shell/Registration] ⚠️ Registration already in progress, skipping...');
            return;
        }

        // 🛡️ GUARD 2: Check if already registered (using SharedDeviceState)
        const existingDeviceId = SharedDeviceState.getDeviceId();
        if (existingDeviceId) {
            SharedLogger.warn('[Shell/Registration] ⚠️ Device already registered (device_id exists), skipping registration');
            SharedLogger.log('[Shell/Registration] Existing device_id:', existingDeviceId);

            // FIX 3: Don't orphan the pending code - clear it since device is already registered
            const orphanedCode = this.getPendingCode();
            if (orphanedCode) {
                SharedLogger.warn('[Shell/Registration] ⚠️ Clearing orphaned pending code:', orphanedCode);
                this.setPendingCode(null);
            }

            return;
        }

        this.isRegistering = true;

        try {
            // 🔒 SECURITY: Get device_token using SharedDeviceState for re-registration
            const deviceToken = SharedDeviceState.getDeviceToken();

            // FIX 3: Check localStorage for existing pending code (survives page reload)
            let pendingCode = this.getPendingCode();
            if (!pendingCode) {
                pendingCode = this.generateActivationCode();
                this.setPendingCode(pendingCode);
                SharedLogger.log('[Shell/Registration] 🆕 Generated new activation code:', pendingCode);
            } else {
                SharedLogger.log('[Shell/Registration] 🔄 Reusing existing code for retry:', pendingCode);
            }
            const code = pendingCode;

            // Detect platform (use ShellHeartbeat if available, otherwise detect here)
            const platform = window.ShellHeartbeat?.detectPlatform() || this.detectPlatformSimple();
            const deviceName = `${platform} - ${code}`;

            SharedLogger.log('[Shell/Registration] 📡 Registering device with code:', code, 'platform:', platform, 'token:', deviceToken ? 'exists (re-registration)' : 'none (first-time)');

            // 🔒 SECURITY: Send device_token instead of organization_id
            // Backend extracts org_id from JWT token (prevents org hijacking)
            const requestBody = {
                activation_code: code,
                device_name: deviceName,
                platform: platform,
                device_type: 'monitor'
            };

            // Only include device_token if exists (re-registration)
            if (deviceToken) {
                requestBody.device_token = deviceToken;
            }

            // Use APIClient for standardized response handling
            const data = await window.SharedAPIClient.post(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.REGISTER),
                requestBody
            );

            // ✅ SUCCESS - Server online, registration created
            SharedLogger.log('[Shell/Registration] ✅ Registration successful');

            // ✅ Use Device model and deviceState (Phase 3)
            const device = new window.Device({
                id: data.id,
                code: code,
                name: deviceName,
                status: 'pending',
                organization_id: data.organization_id,
                platform: platform,
                device_token: data.device_token  // 🔑 Pass token to Device model
            });

            // Save device using state management (auto saves to localStorage including token)
            window.SharedDeviceState.setDevice(device);

            if (data.device_token) {
                SharedLogger.log('[Shell/Registration] 🔑 Device token saved via Device model');
            }

            // Update legacy state for backward compatibility
            state.deviceId = data.id;
            state.deviceCode = code;

            // FIX 3: Clear pending code from localStorage (registration succeeded)
            this.setPendingCode(null);

            SharedLogger.log('[Shell/Registration] ✅ Device registered with model', device.toJSON());

            // Show WiFi online icon (registration succeeded)
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('online');
            }

            // ✅ CANCEL any pending retry (registration succeeded)
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
                this.retryTimeout = null;
                SharedLogger.log('[Shell/Registration] ✅ Cancelled retry timeout (registration succeeded)');
            }

            // FIX 4: Clear retry count on success
            this.clearRetryCount();

            // Update UI (wrapped in try-catch to prevent UI errors from triggering retry)
            try {
                window.ShellUI.updateUI('pending', code);
            } catch (uiError) {
                SharedLogger.error('[Shell/Registration] ⚠️ UI update failed (non-critical):', uiError);
                // Don't throw - UI error shouldn't trigger re-registration
            }

            // Show success toast (context-aware message)
            if (window.SharedToast) {
                if (organizationId) {
                    // Re-registration (device sudah punya organization)
                    window.SharedToast.success('Device Re-registered', 'Waiting for admin approval to re-activate device...', 5000);
                } else {
                    // First-time registration
                    window.SharedToast.success('Activation Code Generated', 'Enter this code in CMS to register device to your organization.', 5000);
                }
            }

            // Start activation polling (wrapped in try-catch)
            try {
                if (window.ActivationPoll && window.ShellActivationPoll.startPolling) {
                    window.ShellActivationPoll.startPolling();
                }
            } catch (pollError) {
                SharedLogger.error('[Shell/Registration] ⚠️ Polling start failed (non-critical):', pollError);
                // Don't throw - polling error shouldn't trigger re-registration
            }

            // Reset flag AFTER all operations complete
            this.isRegistering = false;

        } catch (error) {
            // Reset flag first
            this.isRegistering = false;

            // ⏳ Network error (server offline/unreachable)
            SharedLogger.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

            // Show WiFi offline icon
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('offline');
            }

            // Update UI with pending code
            try {
                const pendingCode = this.getPendingCode();
                window.ShellUI.updateUI('pending', pendingCode);
            } catch (uiError) {
                SharedLogger.error('[Shell/Registration] ⚠️ UI update failed:', uiError);
            }

            // Update UI status message
            const statusMessage = document.getElementById('status-message');
            if (statusMessage) {
                statusMessage.textContent = 'Server offline - Will retry when connection restored';
                statusMessage.style.color = '#f59e0b'; // Orange color for pending
            }

            // Show toast notification
            if (window.SharedToast) {
                window.SharedToast.warning('Server Offline', 'Cannot connect to server. Retrying when connection is restored.', 8000);
            }

            // 🛡️ GUARD 3: Only retry if device NOT already registered
            // Check again before retry (maybe succeeded but response parsing failed)
            const deviceIdAfterError = SharedDeviceState.getDeviceId();
            if (deviceIdAfterError) {
                SharedLogger.warn('[Shell/Registration] ⚠️ Device already registered despite error, skipping retry');
                this.clearRetryCount();
                return;
            }

            // Cancel existing retry timeout
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
                this.retryTimeout = null;
            }

            // FIX 4: Check retry limit before scheduling next retry
            const currentRetry = this.getRetryCount();
            if (currentRetry >= this.MAX_RETRIES) {
                console.error('[Shell/Registration] ❌ Max retries exceeded!', {
                    maxRetries: this.MAX_RETRIES,
                    totalAttempts: currentRetry + 1,
                    elapsedTime: this._calculateElapsedTime(currentRetry)
                });

                // Show error message to user
                if (statusMessage) {
                    statusMessage.textContent = 'Unable to reach server. Check your network connection and refresh the page.';
                    statusMessage.style.color = '#ef4444';
                }

                // Show error toast
                if (window.SharedToast) {
                    window.SharedToast.error('Connection Failed', 'Unable to connect to server after multiple attempts. Please check your network and refresh the page.', 10000);
                }

                // Clear retry count for next manual attempt
                this.clearRetryCount();

                return;  // Stop retrying
            }

            // FIX 4: Calculate retry delay with exponential backoff
            const nextRetry = this.incrementRetryCount();
            const retryDelay = this.calculateRetryDelay(nextRetry - 1);  // -1 because we already incremented

            console.log('[Shell/Registration] 🔄 Scheduling retry', {
                attempt: nextRetry,
                maxRetries: this.MAX_RETRIES,
                delay: retryDelay,
                nextRetryTime: new Date(Date.now() + retryDelay).toLocaleTimeString()
            });

            // Update status message with retry countdown
            if (statusMessage) {
                const countdownSeconds = Math.floor(retryDelay / 1000);
                statusMessage.textContent = `Retrying in ${countdownSeconds} seconds...`;
            }

            // Schedule retry with exponential backoff
            this.retryTimeout = setTimeout(() => {
                SharedLogger.log('[Shell/Registration] 🔄 Retrying registration (attempt ' + nextRetry + ')...');
                this.registerDevice();
            }, retryDelay);
        }
    },

    /**
     * OLD POLLING SYSTEM - DEPRECATED
     * Replaced by ActivationPoll module for better separation of concerns
     * Kept for reference but no longer called
     */
    // checkActivation: async function() { ... },
    // startPolling: function() { ... },

    /**
     * Called when device becomes activated
     */
    onActivated: async function() {
        window.ShellUI.updateUI('active');
        window.ShellHeartbeat.start();

        // Initialize display settings (rotation, volume)
        await window.ShellDisplaySettings.init();

        // Run network diagnostics immediately after activation
        if (window.ShellNetworkDiagnostics) {
            // Run diagnostics now (device sudah punya ID, log akan terkirim)
            setTimeout(() => {
                window.ShellNetworkDiagnostics.runDiagnostics();
            }, 5000); // 5 detik setelah activation

            // Start periodic diagnostics (setiap 30 menit)
            if (window.ShellNetworkDiagnostics.startPeriodicDiagnostics) {
                window.ShellNetworkDiagnostics.startPeriodicDiagnostics();
            }
        }

        window.ShellUI.loadPlayer();
    }
};
