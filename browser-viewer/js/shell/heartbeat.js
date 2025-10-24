/**
 * Shell Heartbeat Module
 * Sends periodic heartbeat to keep device online
 */

window.ShellHeartbeat = {
    /**
     * Start heartbeat loop (keep device online)
     */
    start: function() {
        const state = window.ShellState;
        
        state.heartbeatInterval = setInterval(async () => {
            if (!state.deviceId) return;

            try {
                const response = await fetch(`${state.API_BASE_URL}/api/devices/heartbeat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: parseInt(state.deviceId),
                        device_type: 'monitor'
                    })
                });

                if (response.ok) {
                    console.log('[Shell] Heartbeat sent ✅');
                }
            } catch (error) {
                console.error('[Shell] Heartbeat error:', error);
            }
        }, state.HEARTBEAT_INTERVAL);
    },

    /**
     * Stop heartbeat
     */
    stop: function() {
        const state = window.ShellState;
        
        if (state.heartbeatInterval) {
            clearInterval(state.heartbeatInterval);
            state.heartbeatInterval = null;
        }
    }
};
