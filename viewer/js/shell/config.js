/**
 * Shell Configuration
 * Constants and global state for shell
 */

// Global shell state object
window.ShellState = {
    // API Configuration (loaded from window.ENV)
    API_BASE_URL: window.ENV?.API_BASE_URL || 'http://localhost:8001',
    HEARTBEAT_INTERVAL: window.ENV?.HEARTBEAT_INTERVAL || 30000, // 30 seconds
    LOG_SEND_INTERVAL: 5000,   // 5 seconds
    LOG_BUFFER_SIZE: 20,
    
    // Device state
    deviceId: null,
    deviceCode: null,
    isActivated: false,
    
    // Intervals
    heartbeatInterval: null,
    logSendInterval: null,
    
    // Logger state
    logBuffer: [],
    
    // Store original console methods
    originalConsole: {
        log: console.log,
        warn: console.warn,
        error: console.error,
        info: console.info
    }
};
