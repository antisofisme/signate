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
        state.originalConsole.log('[Shell] Browser Viewer Shell Starting...');
        state.originalConsole.log('='.repeat(60));

        // Initialize logger FIRST
        window.ShellLogger.init();

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
        console.log('[Shell] 🔍 DETAILED localStorage DEBUG:');
        console.log('[Shell] - device_id:', savedDeviceId);
        console.log('[Shell] - device_status:', savedStatus);
        console.log('[Shell] - device_code:', savedCode);
        console.log('[Shell] - hasDeviceId:', !!savedDeviceId);
        console.log('[Shell] - localStorage.length:', localStorage.length);
        console.log('[Shell] - All localStorage keys:', Object.keys(localStorage));
        state.originalConsole.log('='.repeat(60));

        if (savedDeviceId) {
            state.deviceId = savedDeviceId;
            state.deviceCode = savedCode;

            console.log('[Shell] Using saved device:', { deviceId: state.deviceId, status: savedStatus });

            // VERIFY status with backend before deciding what to show
            try {
                const verifyResponse = await fetch(`${state.API_BASE_URL}/api/devices/check-activation/${savedCode}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (verifyResponse.ok) {
                    const verifyData = await verifyResponse.json();
                    console.log('[Shell] 🔍 Backend verification:', verifyData);

                    if (verifyData.activated && verifyData.device_id) {
                        // Backend says activated - load player
                        console.log('[Shell] ✅ Backend confirmed ACTIVE - loading player');
                        state.deviceId = verifyData.device_id;
                        state.deviceName = verifyData.device_name;
                        state.isActivated = true;
                        localStorage.setItem('device_id', verifyData.device_id);
                        localStorage.setItem('device_status', 'active');
                        window.ShellRegistration.onActivated();
                        return; // Exit early
                    } else if (verifyData.message === 'Code not found or expired') {
                        // Code is invalid - clear localStorage and re-register
                        console.warn('[Shell] ⚠️ Saved code is invalid/expired - clearing localStorage');
                        localStorage.clear();
                        console.log('[Shell] 🔄 Reloading to register as new device...');
                        window.location.reload();
                        return; // Exit early
                    }
                }
            } catch (error) {
                console.warn('[Shell] Verification failed, using localStorage:', error);
            }

            // Backend verification failed or not activated - check localStorage
            if (savedStatus === 'active') {
                // Already activated
                console.log('[Shell] ⚠️ Device already ACTIVE - will load player');
                state.isActivated = true;
                window.ShellRegistration.onActivated();
            } else {
                // Still pending, start polling for activation
                console.log('[Shell] Device PENDING - showing activation screen');
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
            console.log('[Shell] ✨ No saved device - will register NEW device');
            await window.ShellRegistration.registerDevice();
        }

        // Network diagnostics will run ONLY after device activation
        // (No point running diagnostics sebelum device registered)

        console.log('[Shell] Initialization complete ✅');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.ShellInit.init());
} else {
    window.ShellInit.init();
}
