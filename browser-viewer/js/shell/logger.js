/**
 * Shell Logger Module
 * Intercepts console logs and sends to backend
 * CRITICAL: Runs in shell, persists even if player crashes
 */

window.ShellLogger = {
    /**
     * Initialize logger - intercept all console.* calls
     */
    init: function() {
        const state = window.ShellState;
        
        console.log = (...args) => this.interceptLog('log', args);
        console.warn = (...args) => this.interceptLog('warn', args);
        console.error = (...args) => this.interceptLog('error', args);
        console.info = (...args) => this.interceptLog('info', args);

        // Start periodic send
        state.logSendInterval = setInterval(() => this.sendLogs(), state.LOG_SEND_INTERVAL);

        state.originalConsole.log('[Shell] Logger initialized ✅');
    },

    /**
     * Intercept log call
     */
    interceptLog: function(level, args) {
        const state = window.ShellState;
        
        // Call original console method
        state.originalConsole[level](...args);

        if (!state.deviceId) return; // Don't log before registration

        // Format message
        const message = args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');

        // Truncate long messages
        const truncated = message.length > 2000
            ? message.substring(0, 2000) + '... [truncated]'
            : message;

        // Add to buffer
        state.logBuffer.push({
            level: level,
            message: truncated,
            timestamp: new Date().toISOString(),
            source: 'browser-viewer'
        });

        // Send if buffer is full
        if (state.logBuffer.length >= state.LOG_BUFFER_SIZE) {
            this.sendLogs();
        }
    },

    /**
     * Send logs to backend
     */
    sendLogs: async function() {
        const state = window.ShellState;
        
        if (!state.deviceId || state.logBuffer.length === 0) return;

        const logsToSend = [...state.logBuffer];
        state.logBuffer = []; // Clear buffer

        try {
            const response = await fetch(`${state.API_BASE_URL}/api/client/logs/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: state.deviceId,
                    logs: logsToSend
                })
            });

            if (!response.ok) {
                state.originalConsole.warn('[Shell] Failed to send logs:', response.statusText);
            }
        } catch (error) {
            state.originalConsole.error('[Shell] Error sending logs:', error);
        }
    }
};
