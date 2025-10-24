/**
 * Shell Configuration
 * Constants and global state for shell
 */

// Global shell state object
window.ShellState = {
    // API Configuration
    API_BASE_URL: 'http://192.168.5.12:8001',
    HEARTBEAT_INTERVAL: 30000, // 30 seconds
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
