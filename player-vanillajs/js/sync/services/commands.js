/**
 * Shell Commands Module
 * Handles remote commands from backend (reset, refresh, reload)
 */

window.ShellCommands = {
    /**
     * Check for pending commands and execute them
     */
    checkAndExecute: async function() {
        // ✅ STATE MIGRATION: Get deviceId from deviceState, fallback to ShellState
        const device = window.SharedDeviceState ? window.SharedDeviceState.getDevice() : null;
        const deviceId = device ? device.id : window.ShellState?.deviceId;

        if (!deviceId) {
            SharedLogger.log('[Shell/Commands] No device ID, skip command check');
            return;
        }

        // ✅ STATE MIGRATION: Get API_BASE_URL from Config/ENV (config, not state)
        const apiBaseUrl = window.Config?.API_BASE_URL || window.SharedENV?.API_BASE_URL;
        if (!apiBaseUrl) {
            SharedLogger.error('[Shell/Commands] No API_BASE_URL configured');
            return;
        }

        try {
            // Use APIClient for standardized response handling
            const data = await window.SharedAPIClient.get(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.COMMANDS_PENDING(deviceId))
            );

            if (!data.commands || data.commands.length === 0) {
                // No pending commands
                return;
            }

            SharedLogger.log(`[Shell/Commands] 📋 Found ${data.commands.length} pending command(s)`);

            // Process each command
            for (const command of data.commands) {
                await this.executeCommand(command);
            }

        } catch (error) {
            SharedLogger.error('[Shell/Commands] Error checking commands:', error);
        }
    },

    /**
     * Execute a single command
     */
    executeCommand: async function(command) {
        SharedLogger.log(`[Shell/Commands] 🔄 Executing command: ${command.command_type} (ID: ${command.id})`);
        SharedLogger.log(`[Shell/Commands] Reason: ${command.reason}`);

        try {
            switch (command.command_type) {
                case 'reset':
                    await this.executeReset(command);
                    break;

                case 'refresh':
                    await this.executeRefresh(command);
                    break;

                case 'reload':
                    await this.executeReload(command);
                    break;

                case 'run_speed_test':
                    await this.executeSpeedTest(command);
                    break;

                default:
                    SharedLogger.warn(`[Shell/Commands] Unknown command type: ${command.command_type}`);
                    break;
            }

            // Mark command as executed in backend
            await this.markExecuted(command.id);

        } catch (error) {
            SharedLogger.error(`[Shell/Commands] Error executing command ${command.id}:`, error);
        }
    },

    /**
     * Execute RESET command (clear localStorage + cache, then reload)
     */
    executeReset: async function(command) {
        SharedLogger.log('[Shell/Commands] 🔄 RESET: Clearing all data...');

        // Clear localStorage
        SharedLogger.log('[Shell/Commands] Clearing localStorage...');
        localStorage.clear();

        // Delete IndexedDB cache
        SharedLogger.log('[Shell/Commands] Deleting IndexedDB cache...');
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    SharedLogger.log('[Shell/Commands] ✅ IndexedDB cache deleted successfully');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    SharedLogger.error('[Shell/Commands] ❌ Failed to delete IndexedDB cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    SharedLogger.warn('[Shell/Commands] ⚠️ IndexedDB deletion blocked');
                    resolve(); // Continue anyway
                };
            });
        } catch (error) {
            SharedLogger.error('[Shell/Commands] Error deleting IndexedDB:', error);
            // Continue anyway
        }

        // Mark as executed BEFORE reload
        await this.markExecuted(command.id);

        // Reload page to show activation screen
        SharedLogger.log('[Shell/Commands] 🔄 Reloading page...');
        window.location.reload();
    },

    /**
     * Execute REFRESH command (reload content cache only)
     */
    executeRefresh: async function(command) {
        SharedLogger.log('[Shell/Commands] 🔄 REFRESH: Reloading content cache...');

        // Delete IndexedDB cache only
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    SharedLogger.log('[Shell/Commands] ✅ Content cache cleared');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    SharedLogger.error('[Shell/Commands] ❌ Failed to clear content cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    SharedLogger.warn('[Shell/Commands] ⚠️ Cache clearing blocked');
                    resolve();
                };
            });
        } catch (error) {
            SharedLogger.error('[Shell/Commands] Error clearing cache:', error);
        }

        // Notify player to reload content
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            SharedLogger.log('[Shell/Commands] Reloading player with fresh cache...');
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Execute RELOAD command (reload player only, keep cache)
     */
    executeReload: async function(command) {
        SharedLogger.log('[Shell/Commands] 🔄 RELOAD: Reloading player...');

        // Reload player iframe
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Execute SPEED TEST command (manual trigger from web admin)
     */
    executeSpeedTest: async function(command) {
        SharedLogger.log('[Shell/Commands] 🌐 SPEED TEST: Running network diagnostics...');

        // Run network diagnostics
        if (window.ShellNetworkDiagnostics && window.ShellNetworkDiagnostics.runDiagnostics) {
            await window.ShellNetworkDiagnostics.runDiagnostics();
            SharedLogger.log('[Shell/Commands] ✅ Speed test completed - check logs for results');
        } else {
            SharedLogger.error('[Shell/Commands] ❌ Network diagnostics module not available');
        }
    },

    /**
     * Mark command as executed in backend
     */
    markExecuted: async function(commandId) {
        // ✅ STATE MIGRATION: Get deviceId from deviceState, fallback to ShellState
        const device = window.SharedDeviceState ? window.SharedDeviceState.getDevice() : null;
        const deviceId = device ? device.id : window.ShellState?.deviceId;

        if (!deviceId) {
            SharedLogger.warn('[Shell/Commands] No device ID, cannot mark command as executed');
            return;
        }

        // ✅ STATE MIGRATION: Get API_BASE_URL from Config/ENV (config, not state)
        const apiBaseUrl = window.Config?.API_BASE_URL || window.SharedENV?.API_BASE_URL;
        if (!apiBaseUrl) {
            SharedLogger.error('[Shell/Commands] No API_BASE_URL configured');
            return;
        }

        try {
            // Use APIClient for standardized response handling
            await window.SharedAPIClient.post(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.COMMANDS_EXECUTE(deviceId, commandId))
            );

            SharedLogger.log(`[Shell/Commands] ✅ Command ${commandId} marked as executed`);
        } catch (error) {
            SharedLogger.error(`[Shell/Commands] ❌ Error marking command ${commandId} as executed:`, error.message);
        }
    }
};
