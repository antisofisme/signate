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
        window.ShellLogger.init();

        // ✅ Restore device from localStorage using deviceState (Phase 3)
        const restoredDevice = window.deviceState.loadFromStorage();
        if (restoredDevice) {
            console.log('[Shell/Init] ✅ Device restored from storage', restoredDevice.toJSON());
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

        // Check if already registered
        const savedDeviceId = localStorage.getItem('device_id');
        const savedStatus = localStorage.getItem('device_status');
        const savedCode = localStorage.getItem('device_code');

        state.originalConsole.log('='.repeat(60));
        console.log('[Shell/Init] 🔍 DETAILED localStorage DEBUG:');
        console.log('[Shell/Init] - device_id:', savedDeviceId);
        console.log('[Shell/Init] - device_status:', savedStatus);
        console.log('[Shell/Init] - device_code:', savedCode);
        console.log('[Shell/Init] - hasDeviceId:', !!savedDeviceId);
        console.log('[Shell/Init] - localStorage.length:', localStorage.length);
        console.log('[Shell/Init] - All localStorage keys:', Object.keys(localStorage));
        state.originalConsole.log('='.repeat(60));

        if (savedDeviceId) {
            state.deviceId = savedDeviceId;
            state.deviceCode = savedCode;

            console.log('[Shell/Init] Using saved device:', { deviceId: state.deviceId, status: savedStatus });

            // VERIFY status with backend before deciding what to show
            try {
                // ✅ USE APICLIENT: Standardized API calls with automatic error handling
                const verifyData = await window.APIClient.get(`${state.API_BASE_URL}/api/devices/check-activation/${savedCode}`);

                console.log('[Shell/Init] 🔍 Backend verification:', verifyData);

                if (verifyData.activated && verifyData.device_id) {
                    // Backend says activated - load player
                    console.log('[Shell/Init] ✅ Backend confirmed ACTIVE - loading player');
                    state.deviceId = verifyData.device_id;
                    state.deviceName = verifyData.device_name;
                    state.isActivated = true;
                    localStorage.setItem('device_id', verifyData.device_id);
                    localStorage.setItem('device_status', 'active');
                    window.ShellRegistration.onActivated();
                    return; // Exit early
                } else if (verifyData.expired && !verifyData.device_id) {
                    // Code expired AND device deleted - clear and re-register
                    console.warn('[Shell/Init] ⚠️ Device code expired and deleted - clearing localStorage');
                    window.clearLocalStoragePreservePIN();
                    console.log('[Shell/Init] 🔄 Reloading to register as new device...');
                    window.location.reload();
                    return; // Exit early
                } else if (verifyData.expired && verifyData.device_id) {
                    // Code expired but device still exists (PENDING) - keep using it
                    console.log('[Shell/Init] ⏳ Code expired but device still pending - continue polling');
                    // Fall through to pending logic below
                }
            } catch (error) {
                console.warn('[Shell/Init] Verification failed, using localStorage:', error);
            }

            // Backend verification failed or not activated - check localStorage
            if (savedStatus === 'active') {
                // Already activated
                console.log('[Shell/Init] ⚠️ Device already ACTIVE - will load player');
                state.isActivated = true;
                window.ShellRegistration.onActivated();
            } else {
                // Still pending, start polling for activation
                console.log('[Shell/Init] Device PENDING - showing activation screen');
                window.ShellUI.updateUI('pending', savedCode);

                // Start activation polling to auto-detect when code is activated
                if (window.ActivationPoll && window.ActivationPoll.startPolling) {
                    window.ActivationPoll.startPolling();
                }

                // Legacy polling disabled - replaced with ActivationPoll
                // Old heartbeat-based polling caused 404 errors when device was replaced
                // if (window.ShellRegistration && window.ShellRegistration.startPolling) {
                //     window.ShellRegistration.startPolling();
                // }
            }
        } else {
            // New device, register
            console.log('[Shell/Init] ✨ No saved device - will register NEW device');
            await window.ShellRegistration.registerDevice();
        }

        // Network diagnostics will run ONLY after device activation
        // (No point running diagnostics sebelum device registered)

        console.log('[Shell/Init] ✅ Initialization complete');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.ShellInit.init());
} else {
    window.ShellInit.init();
}

