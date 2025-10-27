/**
 * Player Configuration
 * Constants and global state for player
 */

// Global player state object
window.PlayerState = {
    // API Configuration (loaded from window.ENV)
    API_BASE_URL: window.ENV?.API_BASE_URL || 'http://localhost:8001',
    REFRESH_INTERVAL: window.ENV?.CONTENT_REFRESH_INTERVAL || 60000,   // Check for playlist updates every minute
    LOG_SEND_INTERVAL: 5000,   // 5 seconds
    LOG_BUFFER_SIZE: 20,
    
    // Player state
    deviceId: null,
    playlist: [],
    currentIndex: 0,
    volumeEnabled: true, // Volume setting from Shell
    
    // Timers
    contentTimer: null,
    refreshTimer: null,
    logSendInterval: null,
    
    // Logger state
    logBuffer: [],
    
    // Store original console methods
    originalConsole: {
        log: console.log,
        warn: console.warn,
        error: console.error,
        info: console.info
    },
    
    // Cache DB reference
    cacheDb: null
};
