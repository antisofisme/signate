/**
 * Shell Commands Module
 * Handles remote commands from backend (reset, refresh, reload)
 */

window.ShellCommands = {
    /**
     * Check for pending commands and execute them
     */
    checkAndExecute: async function() {
        const state = window.ShellState;

        if (!state.deviceId) {
            console.log('[Shell/Commands] No device ID, skip command check');
            return;
        }

        try {
            // Add Authorization header with JWT token
            const headers = window.TokenManager.addAuthHeader({
                'Content-Type': 'application/json'
            });

            // Poll for pending commands
            const response = await fetch(
                `${state.API_BASE_URL}/api/devices/${state.deviceId}/commands/pending`,
                {
                    method: 'GET',
                    headers: await headers
                }
            );

            if (!response.ok) {
                // Handle 401 silently - token will be refreshed on next heartbeat
                if (response.status === 401) {
                    console.warn('[Shell/Commands] Unauthorized - token may be expired');
                    return;
                }
                console.error('[Shell/Commands] Failed to fetch commands:', response.status);
                return;
            }

            const data = await response.json();

            if (!data.commands || data.commands.length === 0) {
                // No pending commands
                return;
            }

            console.log(`[Shell/Commands] 📋 Found ${data.commands.length} pending command(s)`);

            // Process each command
            for (const command of data.commands) {
                await this.executeCommand(command);
            }

        } catch (error) {
            console.error('[Shell/Commands] Error checking commands:', error);
        }
    },

    /**
     * Execute a single command
     */
    executeCommand: async function(command) {
        const state = window.ShellState;

        console.log(`[Shell/Commands] 🔄 Executing command: ${command.command_type} (ID: ${command.id})`);
        console.log(`[Shell/Commands] Reason: ${command.reason}`);

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
                    console.warn(`[Shell/Commands] Unknown command type: ${command.command_type}`);
                    break;
            }

            // Mark command as executed in backend
            await this.markExecuted(command.id);

        } catch (error) {
            console.error(`[Shell/Commands] Error executing command ${command.id}:`, error);
        }
    },

    /**
     * Execute RESET command (clear localStorage + cache, then reload)
     */
    executeReset: async function(command) {
        const state = window.ShellState;

        console.log('[Shell/Commands] 🔄 RESET: Clearing all data...');

        // Clear localStorage
        console.log('[Shell/Commands] Clearing localStorage...');
        localStorage.clear();

        // Delete IndexedDB cache
        console.log('[Shell/Commands] Deleting IndexedDB cache...');
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    console.log('[Shell/Commands] ✅ IndexedDB cache deleted successfully');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    console.error('[Shell/Commands] ❌ Failed to delete IndexedDB cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    console.warn('[Shell/Commands] ⚠️ IndexedDB deletion blocked');
                    resolve(); // Continue anyway
                };
            });
        } catch (error) {
            console.error('[Shell/Commands] Error deleting IndexedDB:', error);
            // Continue anyway
        }

        // Mark as executed BEFORE reload
        await this.markExecuted(command.id);

        // Reload page to show activation screen
        console.log('[Shell/Commands] 🔄 Reloading page...');
        window.location.reload();
    },

    /**
     * Execute REFRESH command (reload content cache only)
     */
    executeRefresh: async function(command) {
        console.log('[Shell/Commands] 🔄 REFRESH: Reloading content cache...');

        // Delete IndexedDB cache only
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    console.log('[Shell/Commands] ✅ Content cache cleared');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    console.error('[Shell/Commands] ❌ Failed to clear content cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    console.warn('[Shell/Commands] ⚠️ Cache clearing blocked');
                    resolve();
                };
            });
        } catch (error) {
            console.error('[Shell/Commands] Error clearing cache:', error);
        }

        // Notify player to reload content
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            console.log('[Shell/Commands] Reloading player with fresh cache...');
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Execute RELOAD command (reload player only, keep cache)
     */
    executeReload: async function(command) {
        console.log('[Shell/Commands] 🔄 RELOAD: Reloading player...');

        // Reload player iframe
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Execute SPEED TEST command (manual trigger from web admin)
     */
    executeSpeedTest: async function(command) {
        console.log('[Shell/Commands] 🌐 SPEED TEST: Running network diagnostics...');

        // Run network diagnostics
        if (window.ShellNetworkDiagnostics && window.ShellNetworkDiagnostics.runDiagnostics) {
            await window.ShellNetworkDiagnostics.runDiagnostics();
            console.log('[Shell/Commands] ✅ Speed test completed - check logs for results');
        } else {
            console.error('[Shell/Commands] ❌ Network diagnostics module not available');
        }
    },

    /**
     * Mark command as executed in backend
     */
    markExecuted: async function(commandId) {
        const state = window.ShellState;

        try {
            // Add Authorization header with JWT token
            const headers = window.TokenManager.addAuthHeader({
                'Content-Type': 'application/json'
            });

            const response = await fetch(
                `${state.API_BASE_URL}/api/devices/${state.deviceId}/commands/${commandId}/execute`,
                {
                    method: 'POST',
                    headers: await headers
                }
            );

            if (response.ok) {
                console.log(`[Shell/Commands] ✅ Command ${commandId} marked as executed`);
            } else {
                console.error(`[Shell/Commands] ❌ Failed to mark command ${commandId} as executed:`, response.status);
            }
        } catch (error) {
            console.error(`[Shell/Commands] Error marking command ${commandId} as executed:`, error);
        }
    }
};
