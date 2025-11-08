/**
 * Shell Registration Module
 * Handles device registration and activation polling
 */

window.ShellRegistration = {
    retryTimeout: null, // Store retry timeout for cancellation
    isRegistering: false, // Prevent concurrent registrations
    pendingCode: null, // Store generated code for retry (avoid re-generating on each retry)

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
     * Get organization ID from localStorage (if previously activated)
     * Returns null for first-time registration
     */
    getOrganizationID: function() {
        const orgId = localStorage.getItem('organization_id');
        if (orgId) {
            console.log('[Shell/Registration] ✅ Found organization ID from previous activation:', orgId);
            return parseInt(orgId);
        }
        console.log('[Shell/Registration] 📌 No organization ID found (first-time registration)');
        return null;
    },


    /**
     * Register device to backend (No-PIN Flow)
     * Auto-displays 6-digit code, organization assigned by admin during activation
     *
     * Flow:
     * 1. First-time registration → No org_id, admin activates from their org
     * 2. Re-registration (after release) → Sends saved org_id, auto-assigns to same org
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
            // 🆕 NO-PIN FLOW: Get organization ID if previously activated (re-registration)
            const organizationId = this.getOrganizationID();

            // 🔑 Use existing code if retrying, otherwise generate new one
            if (!this.pendingCode) {
                this.pendingCode = this.generateActivationCode();
                console.log('[Shell/Registration] 🆕 Generated new activation code:', this.pendingCode);
            } else {
                console.log('[Shell/Registration] 🔄 Reusing existing code for retry:', this.pendingCode);
            }
            const code = this.pendingCode;

            // Detect platform (use ShellHeartbeat if available, otherwise detect here)
            const platform = window.ShellHeartbeat?.detectPlatform() || this.detectPlatformSimple();
            const deviceName = `${platform} - ${code}`;

            console.log('[Shell/Registration] 📡 Registering device with code:', code, 'platform:', platform, 'org_id:', organizationId || 'first-time');

            // 🆕 Send optional organization_id (for re-registration)
            const requestBody = {
                activation_code: code,
                device_name: deviceName,
                platform: platform,
                device_type: 'monitor'
            };

            // Only include organization_id if exists (re-registration)
            if (organizationId) {
                requestBody.organization_id = organizationId;
            }

            // Use APIClient for standardized response handling
            const data = await window.APIClient.post(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.REGISTER),
                requestBody
            );

            // ✅ SUCCESS - Server online, registration created
            console.log('[Shell/Registration] ✅ Registration successful');

            // 🔑 Save device token for authenticated API calls
            if (data.device_token) {
                localStorage.setItem('device_token', data.device_token);
                console.log('[Shell/Registration] 🔑 Device token saved for authenticated requests');
            }

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

            // Update UI (wrapped in try-catch to prevent UI errors from triggering retry)
            try {
                window.ShellUI.updateUI('pending', code);
            } catch (uiError) {
                console.error('[Shell/Registration] ⚠️ UI update failed (non-critical):', uiError);
                // Don't throw - UI error shouldn't trigger re-registration
            }

            // Show success toast (context-aware message)
            if (window.Toast) {
                if (organizationId) {
                    // Re-registration (device sudah punya organization)
                    window.Toast.success('Device Re-registered', 'Waiting for admin approval to re-activate device...', 5000);
                } else {
                    // First-time registration
                    window.Toast.success('Activation Code Generated', 'Enter this code in CMS to register device to your organization.', 5000);
                }
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

            // ⏳ Network error (server offline/unreachable)
            console.error('[Shell/Registration] ❌ Network error (server unreachable):', error.message);

            // Show WiFi offline icon
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('offline');
            }

            // Update UI with pending code (already generated at start of registerDevice)
            try {
                window.ShellUI.updateUI('pending', this.pendingCode);
            } catch (uiError) {
                console.error('[Shell/Registration] ⚠️ UI update failed:', uiError);
            }

            // Update UI status message
            const statusMessage = document.getElementById('status-message');
            if (statusMessage) {
                statusMessage.textContent = 'Server offline - Will retry when connection restored';
                statusMessage.style.color = '#f59e0b'; // Orange color for pending
            }

            // Show toast notification
            if (window.Toast) {
                window.Toast.warning('Server Offline', 'Cannot connect to server. Retrying when connection is restored.', 8000);
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

            // Schedule retry
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
