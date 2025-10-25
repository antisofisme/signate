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
            console.log('[Shell Commands] No device ID, skip command check');
            return;
        }

        try {
            // Poll for pending commands
            const response = await fetch(
                `${state.API_BASE_URL}/api/devices/${state.deviceId}/commands/pending`,
                {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                }
            );

            if (!response.ok) {
                console.error('[Shell Commands] Failed to fetch commands:', response.status);
                return;
            }

            const data = await response.json();

            if (!data.commands || data.commands.length === 0) {
                // No pending commands
                return;
            }

            console.log(`[Shell Commands] 📋 Found ${data.commands.length} pending command(s)`);

            // Process each command
            for (const command of data.commands) {
                await this.executeCommand(command);
            }

        } catch (error) {
            console.error('[Shell Commands] Error checking commands:', error);
        }
    },

    /**
     * Execute a single command
     */
    executeCommand: async function(command) {
        const state = window.ShellState;

        console.log(`[Shell Commands] 🔄 Executing command: ${command.command_type} (ID: ${command.id})`);
        console.log(`[Shell Commands] Reason: ${command.reason}`);

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

                default:
                    console.warn(`[Shell Commands] Unknown command type: ${command.command_type}`);
                    break;
            }

            // Mark command as executed in backend
            await this.markExecuted(command.id);

        } catch (error) {
            console.error(`[Shell Commands] Error executing command ${command.id}:`, error);
        }
    },

    /**
     * Execute RESET command (clear localStorage + cache, then reload)
     */
    executeReset: async function(command) {
        const state = window.ShellState;

        console.log('[Shell Commands] 🔄 RESET: Clearing all data...');

        // Clear localStorage
        console.log('[Shell Commands] Clearing localStorage...');
        localStorage.clear();

        // Delete IndexedDB cache
        console.log('[Shell Commands] Deleting IndexedDB cache...');
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    console.log('[Shell Commands] ✅ IndexedDB cache deleted successfully');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    console.error('[Shell Commands] ❌ Failed to delete IndexedDB cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    console.warn('[Shell Commands] ⚠️ IndexedDB deletion blocked');
                    resolve(); // Continue anyway
                };
            });
        } catch (error) {
            console.error('[Shell Commands] Error deleting IndexedDB:', error);
            // Continue anyway
        }

        // Mark as executed BEFORE reload
        await this.markExecuted(command.id);

        // Reload page to show activation screen
        console.log('[Shell Commands] 🔄 Reloading page...');
        window.location.reload();
    },

    /**
     * Execute REFRESH command (reload content cache only)
     */
    executeRefresh: async function(command) {
        console.log('[Shell Commands] 🔄 REFRESH: Reloading content cache...');

        // Delete IndexedDB cache only
        const dbName = 'signage_media_cache';
        try {
            await new Promise((resolve, reject) => {
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    console.log('[Shell Commands] ✅ Content cache cleared');
                    resolve();
                };

                deleteRequest.onerror = () => {
                    console.error('[Shell Commands] ❌ Failed to clear content cache');
                    reject(deleteRequest.error);
                };

                deleteRequest.onblocked = () => {
                    console.warn('[Shell Commands] ⚠️ Cache clearing blocked');
                    resolve();
                };
            });
        } catch (error) {
            console.error('[Shell Commands] Error clearing cache:', error);
        }

        // Notify player to reload content
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            console.log('[Shell Commands] Reloading player with fresh cache...');
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Execute RELOAD command (reload player only, keep cache)
     */
    executeReload: async function(command) {
        console.log('[Shell Commands] 🔄 RELOAD: Reloading player...');

        // Reload player iframe
        if (window.ShellUI && window.ShellUI.loadPlayer) {
            window.ShellUI.loadPlayer();
        }
    },

    /**
     * Mark command as executed in backend
     */
    markExecuted: async function(commandId) {
        const state = window.ShellState;

        try {
            const response = await fetch(
                `${state.API_BASE_URL}/api/devices/${state.deviceId}/commands/${commandId}/execute`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                }
            );

            if (response.ok) {
                console.log(`[Shell Commands] ✅ Command ${commandId} marked as executed`);
            } else {
                console.error(`[Shell Commands] ❌ Failed to mark command ${commandId} as executed:`, response.status);
            }
        } catch (error) {
            console.error(`[Shell Commands] Error marking command ${commandId} as executed:`, error);
        }
    }
};
