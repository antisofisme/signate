/**
 * Shell Registration Module
 * Handles device registration and activation polling
 */

window.ShellRegistration = {
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
        
        try {
            const code = this.generateActivationCode();
            const deviceName = `Browser - ${code}`;

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

            window.ShellUI.updateUI('pending', code);
            this.startPolling();

        } catch (error) {
            console.error('[Shell] Registration error:', error);
            setTimeout(() => this.registerDevice(), 10000); // Retry in 10s
        }
    },

    /**
     * Poll for activation status
     */
    checkActivation: async function() {
        const state = window.ShellState;
        
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

            if (!response.ok) {
                console.error('[Shell] Heartbeat failed:', response.status);
                return;
            }

            const data = await response.json();

            if (data.status === 'active' && !state.isActivated) {
                // Device just got activated!
                localStorage.setItem('device_status', 'active');
                state.isActivated = true;

                console.log('[Shell] Device activated! ✅');

                this.onActivated();
            }

        } catch (error) {
            console.error('[Shell] Activation check error:', error);
        }
    },

    /**
     * Start polling for activation
     */
    startPolling: function() {
        const state = window.ShellState;
        
        // Poll every 3 seconds until activated
        const pollingInterval = setInterval(() => {
            if (state.isActivated) {
                clearInterval(pollingInterval);
            } else {
                this.checkActivation();
            }
        }, 3000);
    },

    /**
     * Called when device becomes activated
     */
    onActivated: async function() {
        window.ShellUI.updateUI('active');
        window.ShellHeartbeat.start();

        // Initialize display settings (rotation, volume)
        await window.ShellDisplaySettings.init();

        window.ShellUI.loadPlayer();
    }
};
