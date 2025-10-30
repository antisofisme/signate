/**
 * Shell Registration Module
 * Handles device registration and activation polling
 */

window.ShellRegistration = {
    retryTimeout: null, // Store retry timeout for cancellation
    isRegistering: false, // Prevent concurrent registrations

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
     */
    getOrganizationPIN: async function() {
        // Check localStorage first
        let orgPIN = localStorage.getItem('organization_pin');

        if (!orgPIN) {
            console.log('[Shell/Registration] 📌 Organization PIN not found, showing modal...');

            try {
                // Show modal to get Organization PIN
                if (!window.OrganizationPINModal) {
                    console.error('[Shell/Registration] ❌ OrganizationPINModal not loaded');
                    throw new Error('Organization PIN modal not available');
                }

                orgPIN = await window.OrganizationPINModal.show();

                if (!orgPIN || orgPIN.length < 8) {
                    console.error('[Shell/Registration] ❌ Invalid organization PIN');
                    throw new Error('Organization PIN is required');
                }

                console.log('[Shell/Registration] ✅ Organization PIN obtained from modal');
            } catch (error) {
                console.error('[Shell/Registration] ❌ Failed to get Organization PIN:', error);
                throw new Error('Organization PIN is required');
            }
        }

        return orgPIN;
    },

    /**
     * Register device to backend
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

        try {
            // Get Organization PIN (show modal if not exists)
            const orgPIN = await this.getOrganizationPIN();

            const code = this.generateActivationCode();

            // Detect platform (use ShellHeartbeat if available, otherwise detect here)
            const platform = window.ShellHeartbeat?.detectPlatform() || this.detectPlatformSimple();
            const deviceName = `${platform} - ${code}`;

            console.log('[Shell/Registration] 📡 Registering device with code:', code, 'platform:', platform, 'org PIN:', orgPIN);

            // Use APIClient for standardized response handling
            const data = await window.APIClient.post(
                `${state.API_BASE_URL}/api/devices/monitor/register`,
                {
                    organization_pin: orgPIN,
                    activation_code: code,
                    device_name: deviceName,
                    platform: platform
                }
            );

            // Save to localStorage (PERSISTENT)
            localStorage.setItem('device_id', data.id);
            localStorage.setItem('device_code', code);
            localStorage.setItem('device_status', 'pending');

            state.deviceId = data.id;
            state.deviceCode = code;

            // Clear pending code (registration succeeded)
            this.pendingCode = null;

            console.log('[Shell/Registration] ✅ Device registered', { deviceId: state.deviceId, code });

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
            // Network error (server down/unreachable)
            console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

            // Reset flag
            this.isRegistering = false;

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
                statusMessage.textContent = 'Cannot connect to server - Retrying...';
                statusMessage.style.color = '#ef4444'; // Red color
            }

            // Show toast notification
            if (window.Toast) {
                window.Toast.error('Connection Failed', 'Cannot connect to server. Retrying in 10 seconds...', 8000);
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
