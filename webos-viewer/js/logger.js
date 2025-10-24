/**
 * Logger Module
 * Intercepts console logs and sends them to backend for remote monitoring
 */

import { API_BASE_URL } from './config.js';

// ========================================
// Configuration
// ========================================

const LOG_BUFFER_SIZE = 20;  // Send logs when buffer reaches this size
const LOG_SEND_INTERVAL = 5000;  // Send logs every 5 seconds (faster real-time)
const MAX_MESSAGE_LENGTH = 2000;  // Truncate long messages

// ========================================
// State
// ========================================

let logBuffer = [];
let deviceId = null;
let sendInterval = null;

// Store original console methods
const originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error,
    info: console.info
};

// ========================================
// Logger Functions
// ========================================

/**
 * Initialize remote logger
 * @param {number} devId - Device ID from activation
 */
export function initLogger(devId) {
    deviceId = devId;
    
    // Intercept console methods
    console.log = (...args) => interceptLog('log', args);
    console.warn = (...args) => interceptLog('warn', args);
    console.error = (...args) => interceptLog('error', args);
    console.info = (...args) => interceptLog('info', args);
    
    // Start periodic send
    sendInterval = setInterval(sendLogs, LOG_SEND_INTERVAL);
    
    originalConsole.log('[Logger] Remote logging enabled');
}

/**
 * Stop remote logger
 */
export function stopLogger() {
    // Restore original console methods
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    console.error = originalConsole.error;
    console.info = originalConsole.info;
    
    // Stop periodic send
    if (sendInterval) {
        clearInterval(sendInterval);
        sendInterval = null;
    }
    
    // Send remaining logs
    sendLogs();
    
    originalConsole.log('[Logger] Remote logging disabled');
}

/**
 * Intercept console method
 * @param {string} level - Log level
 * @param {Array} args - Console arguments
 */
function interceptLog(level, args) {
    // Call original console method
    originalConsole[level](...args);
    
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
    const truncated = message.length > MAX_MESSAGE_LENGTH 
        ? message.substring(0, MAX_MESSAGE_LENGTH) + '... [truncated]'
        : message;
    
    // Add to buffer
    logBuffer.push({
        level: level,
        message: truncated,
        timestamp: new Date().toISOString(),
        source: 'webos-viewer'
    });
    
    // Send if buffer is full
    if (logBuffer.length >= LOG_BUFFER_SIZE) {
        sendLogs();
    }
}

/**
 * Send logs to backend
 */
async function sendLogs() {
    if (!deviceId || logBuffer.length === 0) {
        return;
    }
    
    const logsToSend = [...logBuffer];
    logBuffer = [];  // Clear buffer
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/logs/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: deviceId,
                logs: logsToSend
            })
        });
        
        if (!response.ok) {
            originalConsole.warn('[Logger] Failed to send logs:', response.statusText);
            // Don't re-add to buffer to avoid infinite loop
        }
    } catch (error) {
        originalConsole.error('[Logger] Error sending logs:', error);
        // Don't re-add to buffer
    }
}

/**
 * Manually log a message (bypasses console interception)
 * Useful for logging without showing in console
 * @param {string} level - Log level
 * @param {string} message - Log message
 */
export function logToBackend(level, message) {
    if (!deviceId) return;
    
    logBuffer.push({
        level: level,
        message: message,
        timestamp: new Date().toISOString(),
        source: 'webos-viewer'
    });
    
    if (logBuffer.length >= LOG_BUFFER_SIZE) {
        sendLogs();
    }
}
