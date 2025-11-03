/**
 * Shell Registration Module
 * Handles device registration and activation polling
 */

window.ShellRegistration = {
    retryTimeout: null, // Store retry timeout for cancellation
    isRegistering: false, // Prevent concurrent registrations
    pendingValidationTimeout: null, // Timeout for pending PIN validation retry

    /**
     * Generate 6-digit activation code
     */
    generateActivationCode: function() {
        return Math.floor(100000 + Math.random() * 900000).toString();
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
     * Get or prompt for Organization PIN (using modal)
     * NOTE: PIN is NOT saved to localStorage until validated by server
     */
    getOrganizationPIN: async function(errorMessage = null) {
        // Check localStorage first for validated PIN
        let orgPIN = localStorage.getItem('organization_pin');
        const pinValidated = localStorage.getItem('organization_pin_validated') === 'true';

        // If PIN exists AND validated, return it
        if (orgPIN && pinValidated) {
            console.log('[Shell/Registration] ✅ Using validated Organization PIN from localStorage');
            return orgPIN;
        }

        // Check for pending validation PIN
        const pendingPIN = localStorage.getItem('organization_pin_pending');
        if (pendingPIN) {
            console.log('[Shell/Registration] ⏳ Found pending validation PIN, will retry validation');
            return pendingPIN;
        }

        // No validated PIN - show modal to get new PIN
        console.log('[Shell/Registration] 📌 Organization PIN not found or not validated, showing modal...');

        try {
            // Show modal to get Organization PIN
            if (!window.OrganizationPINModal) {
                console.error('[Shell/Registration] ❌ OrganizationPINModal not loaded');
                throw new Error('Organization PIN modal not available');
            }

            // Pass error message and skipValidation=true for registration flow
            // Registration will validate PIN with device registration endpoint
            orgPIN = await window.OrganizationPINModal.show(errorMessage, true);

            if (!orgPIN || orgPIN.length < 8) {
                console.error('[Shell/Registration] ❌ Invalid organization PIN');
                throw new Error('Organization PIN is required');
            }

            console.log('[Shell/Registration] ✅ Organization PIN obtained from modal (not yet validated)');
        } catch (error) {
            console.error('[Shell/Registration] ❌ Failed to get Organization PIN:', error);
            throw new Error('Organization PIN is required');
        }

        return orgPIN;
    },

    /**
     * Save validated PIN to localStorage
     */
    savePINAsValidated: function(pin) {
        localStorage.setItem('organization_pin', pin);
        localStorage.setItem('organization_pin_validated', 'true');
        // Clear pending PIN if exists
        localStorage.removeItem('organization_pin_pending');
        console.log('[Shell/Registration] ✅ PIN saved as validated');
    },

    /**
     * Save PIN as pending validation (server offline)
     */
    savePINAsPending: function(pin) {
        localStorage.setItem('organization_pin_pending', pin);
        console.log('[Shell/Registration] ⏳ PIN saved as pending validation');
    },

    /**
     * Clear invalid PIN from storage
     */
    clearPIN: function() {
        localStorage.removeItem('organization_pin');
        localStorage.removeItem('organization_pin_validated');
        localStorage.removeItem('organization_pin_pending');
        console.log('[Shell/Registration] 🗑️ PIN cleared from storage');
    },

    /**
     * Validate pending PIN when server comes back online
     */
    validatePendingPIN: async function() {
        const pendingPIN = localStorage.getItem('organization_pin_pending');

        if (!pendingPIN) {
            console.log('[Shell/Registration] ℹ️ No pending PIN to validate');
            return;
        }

        console.log('[Shell/Registration] 🔄 Validating pending PIN...');

        // Cancel existing timeout
        if (this.pendingValidationTimeout) {
            clearTimeout(this.pendingValidationTimeout);
            this.pendingValidationTimeout = null;
        }

        // Try to register with pending PIN
        // This will trigger full registration flow which will validate PIN
        await this.registerDevice();
    },

    /**
     * Start background retry for pending PIN validation
     */
    startPendingValidationRetry: function() {
        // Cancel existing timeout
        if (this.pendingValidationTimeout) {
            clearTimeout(this.pendingValidationTimeout);
        }

        console.log('[Shell/Registration] ⏰ Starting background retry for pending PIN validation (every 10s)');

        this.pendingValidationTimeout = setTimeout(() => {
            this.validatePendingPIN();
        }, 10000); // Retry every 10 seconds
    },

    /**
     * Register device to backend
     * Handles 3 scenarios:
     * 1. Server online + PIN valid → Save PIN + device, show success
     * 2. Server online + PIN invalid → Clear PIN, show error modal, retry
     * 3. Server offline → Save PIN as pending, retry in background
     */
    registerDevice: async function() {
        const state = window.ShellState;

        // 🛡️ GUARD 1: Prevent concurrent registrations
        if (this.isRegistering) {
            console.warn('[Shell/Registration] ⚠️ Registration already in progress, skipping...');
            return;
        }

        // 🛡️ GUARD 2: Check if already registered (localStorage check)
        const existingDeviceId = localStorage.getItem('device_id');
        if (existingDeviceId) {
            console.warn('[Shell/Registration] ⚠️ Device already registered (device_id exists in localStorage), skipping registration');
            console.log('[Shell/Registration] Existing device_id:', existingDeviceId);
            return;
        }

        this.isRegistering = true;
        let orgPIN = null;

        try {
            // Get Organization PIN (show modal if not exists)
            orgPIN = await this.getOrganizationPIN();

            const code = this.generateActivationCode();

            // Detect platform (use ShellHeartbeat if available, otherwise detect here)
            const platform = window.ShellHeartbeat?.detectPlatform() || this.detectPlatformSimple();
            const deviceName = `${platform} - ${code}`;

            console.log('[Shell/Registration] 📡 Registering device with code:', code, 'platform:', platform, 'org PIN:', orgPIN);

            // Use APIClient for standardized response handling
            const data = await window.APIClient.post(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.REGISTER),
                {
                    organization_pin: orgPIN,
                    activation_code: code,
                    device_name: deviceName,
                    platform: platform
                }
            );

            // ✅ SCENARIO 1: SUCCESS - Server online + PIN valid
            console.log('[Shell/Registration] ✅ Registration successful - PIN valid');

            // Save PIN as validated (only after server confirms it's valid)
            this.savePINAsValidated(orgPIN);

            // ✅ Use Device model and deviceState (Phase 3)
            const device = new window.Device({
                id: data.id,
                code: code,
                name: deviceName,
                status: 'pending',
                organization_id: data.organization_id,
                platform: platform
            });

            // Save device using state management (auto saves to localStorage)
            window.deviceState.setDevice(device);

            // Update legacy state for backward compatibility
            state.deviceId = data.id;
            state.deviceCode = code;

            // Clear pending code (registration succeeded)
            this.pendingCode = null;

            console.log('[Shell/Registration] ✅ Device registered with model', device.toJSON());

            // Show WiFi online icon (registration succeeded)
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('online');
            }

            // ✅ CANCEL any pending retry (registration succeeded)
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
                this.retryTimeout = null;
                console.log('[Shell/Registration] ✅ Cancelled retry timeout (registration succeeded)');
            }

            // Cancel pending validation retry
            if (this.pendingValidationTimeout) {
                clearTimeout(this.pendingValidationTimeout);
                this.pendingValidationTimeout = null;
                console.log('[Shell/Registration] ✅ Cancelled pending validation timeout');
            }

            // Show success toast
            if (window.Toast) {
                window.Toast.success('Registration Successful', 'Device registered successfully. Waiting for admin activation...', 5000);
            }

            // Update UI (wrapped in try-catch to prevent UI errors from triggering retry)
            try {
                window.ShellUI.updateUI('pending', code);
            } catch (uiError) {
                console.error('[Shell/Registration] ⚠️ UI update failed (non-critical):', uiError);
                // Don't throw - UI error shouldn't trigger re-registration
            }

            // Start activation polling (wrapped in try-catch)
            try {
                if (window.ActivationPoll && window.ActivationPoll.startPolling) {
                    window.ActivationPoll.startPolling();
                }
            } catch (pollError) {
                console.error('[Shell/Registration] ⚠️ Polling start failed (non-critical):', pollError);
                // Don't throw - polling error shouldn't trigger re-registration
            }

            // Reset flag AFTER all operations complete
            this.isRegistering = false;

        } catch (error) {
            // Reset flag first
            this.isRegistering = false;

            // Check error type to distinguish between network error and invalid PIN
            const isNetworkError = !error.status || error.message?.includes('Failed to fetch') || error.message?.includes('Network');
            const isPINError = error.status === 404 || error.message?.includes('Invalid organization PIN');

            // ❌ SCENARIO 2: Server online + PIN INVALID
            if (isPINError) {
                console.error('[Shell/Registration] ❌ Invalid Organization PIN:', error.message);

                // Clear invalid PIN from storage
                this.clearPIN();

                // Show error toast
                if (window.Toast) {
                    window.Toast.error('Invalid PIN', 'Organization PIN is incorrect. Please try again.', 6000);
                }

                // Show modal again with error message
                setTimeout(async () => {
                    try {
                        const newPIN = await this.getOrganizationPIN('Invalid Organization PIN. Please enter correct PIN.');
                        if (newPIN) {
                            // User entered new PIN, retry registration
                            console.log('[Shell/Registration] 🔄 Retrying with new PIN...');
                            this.registerDevice();
                        }
                    } catch (modalError) {
                        console.error('[Shell/Registration] ❌ Failed to get new PIN:', modalError);
                    }
                }, 1000);

                return;
            }

            // ⏳ SCENARIO 3: Network error (server offline/unreachable)
            console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

            // Save PIN as pending validation (will be validated when server comes online)
            if (orgPIN) {
                this.savePINAsPending(orgPIN);
            }

            // Show WiFi offline icon
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('offline');
            }

            // 🎯 FIX: Display generated code even when offline
            // Store code for this registration attempt
            if (!this.pendingCode) {
                this.pendingCode = this.generateActivationCode();
                console.log('[Shell/Registration] 📋 Generated code for offline display:', this.pendingCode);
            }

            // Update UI with pending code (even though backend is unreachable)
            try {
                window.ShellUI.updateUI('pending', this.pendingCode);
            } catch (uiError) {
                console.error('[Shell/Registration] ⚠️ UI update failed:', uiError);
            }

            // Update UI status message
            const statusMessage = document.getElementById('status-message');
            if (statusMessage) {
                statusMessage.textContent = 'Server offline - PIN will be validated when online';
                statusMessage.style.color = '#f59e0b'; // Orange color for pending
            }

            // Show toast notification
            if (window.Toast) {
                window.Toast.warning('Server Offline', 'Cannot connect to server. PIN will be validated when server comes online.', 8000);
            }

            // 🛡️ GUARD 3: Only retry if device NOT already registered
            // Check again before retry (maybe succeeded but response parsing failed)
            const deviceIdAfterError = localStorage.getItem('device_id');
            if (deviceIdAfterError) {
                console.warn('[Shell/Registration] ⚠️ Device already registered despite error, skipping retry');
                return;
            }

            // Cancel existing retry timeout
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
            }

            // Schedule retry with exponential backoff
            console.log('[Shell/Registration] 🔄 Scheduling retry in 10 seconds...');
            this.retryTimeout = setTimeout(() => {
                console.log('[Shell/Registration] 🔄 Retrying registration...');
                this.registerDevice();
            }, 10000);

            // Also start pending validation retry in background
            this.startPendingValidationRetry();
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
