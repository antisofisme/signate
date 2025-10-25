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
     * Register device to backend
     */
    registerDevice: async function() {
        const state = window.ShellState;

        // 🛡️ GUARD 1: Prevent concurrent registrations
        if (this.isRegistering) {
            console.warn('[Shell] ⚠️ Registration already in progress, skipping...');
            return;
        }

        // 🛡️ GUARD 2: Check if already registered (localStorage check)
        const existingDeviceId = localStorage.getItem('device_id');
        if (existingDeviceId) {
            console.warn('[Shell] ⚠️ Device already registered (device_id exists in localStorage), skipping registration');
            console.log('[Shell] Existing device_id:', existingDeviceId);
            return;
        }

        this.isRegistering = true;

        try {
            const code = this.generateActivationCode();
            const deviceName = `Browser - ${code}`;

            console.log('[Shell] 📡 Registering device with code:', code);

            const response = await fetch(`${state.API_BASE_URL}/api/devices/monitor/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    activation_code: code,
                    device_name: deviceName
                })
            });

            if (!response.ok) {
                throw new Error(`Registration failed: ${response.status}`);
            }

            const data = await response.json();

            // Save to localStorage (PERSISTENT)
            localStorage.setItem('device_id', data.id);
            localStorage.setItem('device_code', code);
            localStorage.setItem('device_status', 'pending');

            state.deviceId = data.id;
            state.deviceCode = code;

            console.log('[Shell] Device registered ✅', { deviceId: state.deviceId, code });

            // ✅ CANCEL any pending retry (registration succeeded)
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
                this.retryTimeout = null;
                console.log('[Shell] ✅ Cancelled retry timeout (registration succeeded)');
            }

            // Update UI (wrapped in try-catch to prevent UI errors from triggering retry)
            try {
                window.ShellUI.updateUI('pending', code);
            } catch (uiError) {
                console.error('[Shell] ⚠️ UI update failed (non-critical):', uiError);
                // Don't throw - UI error shouldn't trigger re-registration
            }

            // Start activation polling (wrapped in try-catch)
            try {
                if (window.ActivationPoll && window.ActivationPoll.startPolling) {
                    window.ActivationPoll.startPolling();
                }
            } catch (pollError) {
                console.error('[Shell] ⚠️ Polling start failed (non-critical):', pollError);
                // Don't throw - polling error shouldn't trigger re-registration
            }

            // Reset flag AFTER all operations complete
            this.isRegistering = false;

        } catch (error) {
            console.error('[Shell] ❌ Registration failed:', error);

            // Reset flag
            this.isRegistering = false;

            // 🛡️ GUARD 3: Only retry if device NOT already registered
            // Check again before retry (maybe succeeded but response parsing failed)
            const deviceIdAfterError = localStorage.getItem('device_id');
            if (deviceIdAfterError) {
                console.warn('[Shell] ⚠️ Device already registered despite error, skipping retry');
                return;
            }

            // Cancel existing retry timeout
            if (this.retryTimeout) {
                clearTimeout(this.retryTimeout);
            }

            // Schedule retry with exponential backoff
            console.log('[Shell] 🔄 Scheduling retry in 10 seconds...');
            this.retryTimeout = setTimeout(() => {
                console.log('[Shell] 🔄 Retrying registration...');
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

        // Send pending network diagnostics (if any from before activation)
        if (window.ShellNetworkDiagnostics && window.ShellNetworkDiagnostics.sendPendingDiagnostics) {
            await window.ShellNetworkDiagnostics.sendPendingDiagnostics();
        }

        // Start periodic network diagnostics (every 30 minutes)
        if (window.ShellNetworkDiagnostics && window.ShellNetworkDiagnostics.startPeriodicDiagnostics) {
            window.ShellNetworkDiagnostics.startPeriodicDiagnostics();
        }

        window.ShellUI.loadPlayer();
    }
};
