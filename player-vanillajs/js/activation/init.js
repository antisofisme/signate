/**
 * Shell Initialization Module
 * Main entry point for shell - orchestrates initialization
 */

window.ShellInit = {
    /**
     * Initialize shell
     */
    init: async function() {
        const state = window.ShellState;

        state.originalConsole.log('='.repeat(60));
        state.originalConsole.log('[Shell/Init] Browser Viewer Shell Starting...');
        state.originalConsole.log('='.repeat(60));

        // Initialize logger FIRST
        window.SharedLogger.init();

        // ✅ Restore device from localStorage using deviceState (Phase 3)
        const restoredDevice = window.SharedDeviceState.loadFromStorage();
        if (restoredDevice) {
            SharedLogger.log('[Shell/Init] ✅ Device restored from storage', restoredDevice.toJSON());
        }

        // Initialize WiFi status indicator
        if (window.ShellWiFiStatus && window.ShellWiFiStatus.init) {
            window.ShellWiFiStatus.init();
        }

        // ENSURE activation screen is visible by default (prevent player from showing prematurely)
        const activationScreen = document.getElementById('activation-screen');
        const playerContainer = document.getElementById('player-container');
        if (activationScreen) activationScreen.style.display = 'flex';
        if (playerContainer) playerContainer.style.display = 'none';

        // Check if already registered (using SharedDeviceState)
        const savedDeviceId = SharedDeviceState.getDeviceId();
        const savedStatus = SharedDeviceState.getDeviceStatus();
        const savedCode = SharedDeviceState.getDeviceCode();

        state.originalConsole.log('='.repeat(60));
        SharedLogger.log('[Shell/Init] 🔍 DETAILED localStorage DEBUG:');
        SharedLogger.log('[Shell/Init] - device_id:', savedDeviceId);
        SharedLogger.log('[Shell/Init] - device_status:', savedStatus);
        SharedLogger.log('[Shell/Init] - device_code:', savedCode);
        SharedLogger.log('[Shell/Init] - hasDeviceId:', SharedDeviceState.hasDeviceId());
        SharedLogger.log('[Shell/Init] - localStorage.length:', localStorage.length);
        SharedLogger.log('[Shell/Init] - All localStorage keys:', Object.keys(localStorage));
        state.originalConsole.log('='.repeat(60));

        if (savedDeviceId) {
            state.deviceId = savedDeviceId;
            state.deviceCode = savedCode;

            SharedLogger.log('[Shell/Init] Using saved device:', { deviceId: state.deviceId, status: savedStatus });

            // VERIFY status with backend before deciding what to show
            try {
                // ✅ USE APICLIENT: Standardized API calls with automatic error handling
                const verifyData = await window.SharedAPIClient.get(`${state.API_BASE_URL}/api/devices/check-activation/${savedCode}`);

                SharedLogger.log('[Shell/Init] 🔍 Backend verification:', verifyData);

                if (verifyData.activated && verifyData.device_id) {
                    // Backend says activated - load player
                    SharedLogger.log('[Shell/Init] ✅ Backend confirmed ACTIVE - loading player');
                    state.deviceId = verifyData.device_id;
                    state.deviceName = verifyData.device_name;
                    state.isActivated = true;

                    // Use SharedDeviceState for atomic activation
                    SharedDeviceState.markAsActivated(
                        verifyData.device_id,
                        verifyData.device_name,
                        verifyData.organization_id
                    );

                    window.ShellRegistration.onActivated();
                    return; // Exit early
                } else if (verifyData.expired && !verifyData.device_id) {
                    // Code expired AND device deleted - clear device data but KEEP token
                    SharedLogger.warn('[Shell/Init] ⚠️ Device code expired and deleted - clearing device data');

                    // Use SharedDeviceState atomic clear (preserves auth)
                    SharedDeviceState.clearDeviceData({ preserveAuth: true });

                    // ✅ Don't reload! Directly register new device with preserved token/org_id
                    SharedLogger.log('[Shell/Init] 🔄 Re-registering device with preserved token & org_id...');
                    await window.ShellRegistration.registerDevice();
                    return; // Exit early
                } else if (verifyData.expired && verifyData.device_id) {
                    // Code expired but device still exists (PENDING) - keep using it
                    SharedLogger.log('[Shell/Init] ⏳ Code expired but device still pending - continue polling');
                    // Fall through to pending logic below
                }
            } catch (error) {
                SharedLogger.warn('[Shell/Init] Verification failed, using localStorage:', error);
            }

            // Backend verification failed or not activated - check localStorage
            if (savedStatus === 'active') {
                // Already activated
                SharedLogger.log('[Shell/Init] ⚠️ Device already ACTIVE - will load player');
                state.isActivated = true;
                window.ShellRegistration.onActivated();
            } else {
                // Still pending, start polling for activation
                SharedLogger.log('[Shell/Init] Device PENDING - showing activation screen');
                window.ShellUI.updateUI('pending', savedCode);

                // Start activation polling to auto-detect when code is activated
                if (window.ActivationPoll && window.ShellActivationPoll.startPolling) {
                    window.ShellActivationPoll.startPolling();
                }

                // Legacy polling disabled - replaced with ActivationPoll
                // Old heartbeat-based polling caused 404 errors when device was replaced
                // if (window.ShellRegistration && window.ShellRegistration.startPolling) {
                //     window.ShellRegistration.startPolling();
                // }
            }
        } else {
            // New device, register
            SharedLogger.log('[Shell/Init] ✨ No saved device - will register NEW device');
            await window.ShellRegistration.registerDevice();
        }

        // Network diagnostics will run ONLY after device activation
        // (No point running diagnostics sebelum device registered)

        SharedLogger.log('[Shell/Init] ✅ Initialization complete');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.ShellInit.init());
} else {
    window.ShellInit.init();
}

