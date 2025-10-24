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

        // Check if already registered
        const savedDeviceId = localStorage.getItem('device_id');
        const savedStatus = localStorage.getItem('device_status');
        const savedCode = localStorage.getItem('device_code');

        if (savedDeviceId) {
            state.deviceId = savedDeviceId;
            state.deviceCode = savedCode;

            console.log('[Shell] Using saved device:', { deviceId: state.deviceId, status: savedStatus });

            if (savedStatus === 'active') {
                // Already activated
                state.isActivated = true;
                window.ShellRegistration.onActivated();
            } else {
                // Still pending, start polling
                window.ShellUI.updateUI('pending', savedCode);
                window.ShellRegistration.startPolling();
            }
        } else {
            // New device, register
            await window.ShellRegistration.registerDevice();
        }

        console.log('[Shell] Initialization complete ✅');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.ShellInit.init());
} else {
    window.ShellInit.init();
}
