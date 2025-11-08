/**
 * Activation Polling Module
 *
 * Polls backend to check if pending activation code has been activated
 * This allows viewers to auto-connect when admin assigns pending device to inactive device
 */

window.ActivationPoll = {
    pollInterval: null,
    pollIntervalMs: 5000, // Check every 5 seconds

    /**
     * Start polling for activation status
     * Called when viewer is in pending state showing activation code
     */
    startPolling: function() {
        const state = window.ShellState;

        // Get activation code from localStorage or state
        const activationCode = localStorage.getItem('device_code') || state.activationCode || state.deviceCode;

        // Only poll if we have activation code but device is not activated yet
        if (!activationCode || state.isActivated) {
            console.log('[Shell/ActivationPoll] Skipping poll - no code or already activated');
            return;
        }

        // Store code for polling
        state.activationCode = activationCode;

        console.log(`[Activation Poll] 🔄 Starting activation polling for code: ${activationCode}`);

        // Clear existing interval if any
        this.stopPolling();

        // Check immediately
        this.checkActivation();

        // Then check every 5 seconds
        this.pollInterval = setInterval(() => {
            this.checkActivation();
        }, this.pollIntervalMs);
    },

    /**
     * Stop polling
     */
    stopPolling: function() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('[Shell/ActivationPoll] ⏹️ Stopped activation polling');
        }
    },

    /**
     * Check if activation code has been activated
     */
    checkActivation: async function() {
        const state = window.ShellState;

        if (!state.activationCode) {
            this.stopPolling();
            return;
        }

        try {
            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${state.API_BASE_URL}/api/devices/check-activation/${state.activationCode}`
            );
            console.log('[Shell/ActivationPoll] 📊 Activation status:', data);

            // Connection successful - show WiFi online and reset status message
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('online');
            }

            const statusMessage = document.getElementById('status-message');
            if (statusMessage && statusMessage.textContent.includes('Cannot connect')) {
                statusMessage.textContent = '⏳ Waiting for approval...';
                statusMessage.style.color = ''; // Reset color
            }

            // Handle expired code - clear localStorage and re-register
            if (data.expired) {
                console.warn('[Shell/ActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

                // Show toast notification
                if (window.Toast) {
                    window.Toast.warning('Activation Code Expired', 'Your activation code has expired. Restarting registration...', 5000);
                }

                // Stop polling
                this.stopPolling();

                // Clear localStorage
                localStorage.clear();

                // Delete IndexedDB cache
                const dbName = 'signage_media_cache';
                try {
                    await new Promise((resolve) => {
                        const deleteRequest = indexedDB.deleteDatabase(dbName);
                        deleteRequest.onsuccess = () => resolve();
                        deleteRequest.onerror = () => resolve();
                        deleteRequest.onblocked = () => resolve();
                    });
                } catch (error) {
                    console.error('[Shell/ActivationPoll] Error deleting cache:', error);
                }

                // Reload to show new activation screen
                console.log('[Shell/ActivationPoll] 🔄 Reloading to register as new device...');
                window.location.reload();
                return;
            }

            if (data.activated && data.device_id) {
                console.log(`[Activation Poll] ✅ Code activated! Device ID: ${data.device_id}, Name: ${data.device_name}`);

                // CRITICAL: Handle device ID change properly (Flow 2B: Replace scenario)
                // Old device_id might be different from new device_id
                const oldDeviceId = state.deviceId;
                const newDeviceId = data.device_id;

                if (oldDeviceId && oldDeviceId !== newDeviceId) {
                    console.warn(`[Activation Poll] ⚠️ Device ID changed: ${oldDeviceId} → ${newDeviceId} (Replace scenario)`);
                }

                // Step 1: Stop polling
                this.stopPolling();

                // Step 2: Stop old heartbeat (if running) and wait for pending requests
                if (window.ShellHeartbeat && window.ShellHeartbeat.stop) {
                    window.ShellHeartbeat.stop();
                    console.log('[Shell/ActivationPoll] Stopped old heartbeat, waiting for pending requests...');

                    // Wait 200ms for in-flight requests to complete
                    await new Promise(resolve => setTimeout(resolve, 200));
                }

                // Step 3: Update state with new device ID (atomic transition)
                state.deviceId = newDeviceId;
                state.deviceName = data.device_name;
                state.isActivated = true;

                // Step 4: ✅ Update device status using deviceState (Phase 3)
                try {
                    // Update device with active status
                    window.deviceState.setStatus('active');

                    // Also update legacy localStorage for backward compatibility
                    localStorage.setItem('device_id', newDeviceId);
                    localStorage.setItem('device_status', 'active');

                    // 🆕 Save organization_id for re-registration (if device gets released)
                    if (data.organization_id) {
                        localStorage.setItem('organization_id', data.organization_id);
                        console.log('[Shell/ActivationPoll] 🏢 Organization ID saved:', data.organization_id);
                    }

                    // Keep the activation code for reference
                    // device_code already exists from registration

                    console.log('[Shell/ActivationPoll] ✅ Device activated with model', {
                        device_id: newDeviceId,
                        status: 'active',
                        organization_id: data.organization_id,
                        model: window.deviceState.getDevice()?.toJSON()
                    });
                } catch (storageError) {
                    console.error('[Shell/ActivationPoll] ❌ CRITICAL: Failed to save to localStorage!', storageError);
                    console.error('[Shell/ActivationPoll] localStorage might be disabled or quota exceeded');
                }

                // Step 5: Show success message
                if (window.ShellUI && window.ShellUI.showActivationSuccess) {
                    window.ShellUI.showActivationSuccess(data.device_name);
                }

                // Show toast notification
                if (window.Toast) {
                    window.Toast.success('Device Activated!', `Successfully activated as: ${data.device_name}`, 5000);
                }

                // Step 6: Start heartbeat with NEW device_id
                if (window.ShellHeartbeat && window.ShellHeartbeat.start) {
                    window.ShellHeartbeat.start();
                    console.log(`[Activation Poll] Started heartbeat with device_id=${newDeviceId}`);
                }

                // Step 7: Check for pending commands (reload/reset) AFTER device ID update
                // This handles Flow 2B where backend queues reload command for new device
                if (window.ShellCommands) {
                    console.log('[Shell/ActivationPoll] Checking for pending commands after activation...');
                    await window.ShellCommands.checkAndExecute();
                }

                // Step 8: Load player
                if (window.ShellUI && window.ShellUI.loadPlayer) {
                    window.ShellUI.loadPlayer();
                }

                console.log('[Shell/ActivationPoll] 🎉 Viewer activated successfully via polling!');
            }
        } catch (error) {
            // Handle 404 - Device code not found or deleted
            if (error.status === 404) {
                console.warn('[Shell/ActivationPoll] ⚠️ Device code not found or deleted (404) - Auto-resetting viewer');

                // Show toast notification
                if (window.Toast) {
                    window.Toast.warning('Device Code Not Found', 'Your device code was deleted. Restarting registration...', 5000);
                }

                // Stop polling
                this.stopPolling();

                // Clear localStorage
                localStorage.clear();

                // Delete IndexedDB cache
                const dbName = 'signage_media_cache';
                try {
                    await new Promise((resolve) => {
                        const deleteRequest = indexedDB.deleteDatabase(dbName);
                        deleteRequest.onsuccess = () => resolve();
                        deleteRequest.onerror = () => resolve(); // Continue anyway
                        deleteRequest.onblocked = () => resolve(); // Continue anyway
                    });
                } catch (cacheError) {
                    console.error('[Shell/ActivationPoll] Error deleting cache:', cacheError);
                }

                // Reload to show new activation screen
                console.log('[Shell/ActivationPoll] 🔄 Reloading to register as new device...');
                window.location.reload();
                return;
            }

            // Network error (server down/unreachable)
            // Show alert and WiFi offline icon, but keep polling
            console.error('[Shell/ActivationPoll] ❌ Network error (server unreachable):', error.message);

            // Show WiFi offline icon
            if (window.ShellWiFiStatus) {
                window.ShellWiFiStatus.updateStatus('offline');
            }

            // Update UI status message (if available)
            const statusMessage = document.getElementById('status-message');
            if (statusMessage) {
                statusMessage.textContent = 'Cannot connect to server - Retrying...';
                statusMessage.style.color = '#ef4444'; // Red color
            }

            // Show toast notification
            if (window.Toast) {
                window.Toast.warning('Connection Lost', 'Cannot reach server during activation check. Retrying...', 6000);
            }

            // Continue polling - don't stop or clear localStorage
            console.log('[Shell/ActivationPoll] ⏳ Will retry in next poll cycle...');
        }
    }
};
