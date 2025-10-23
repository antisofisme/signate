/**
 * API Module
 * Handles all API communication with the backend server
 */

import {
    API_BASE_URL,
    deviceId,
    activationCode,
    isActivated,
    pollTimer,
    heartbeatTimer,
    setDeviceId,
    setActivationCode,
    setIsActivated,
    setPollTimer,
    setHeartbeatTimer
} from './config.js';

// ========================================
// Device Registration & Activation
// ========================================

/**
 * Generate 6-digit activation code
 * @returns {string} 6-digit activation code
 */
export function generateActivationCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

/**
 * Register monitor with backend
 * @returns {Promise<void>}
 */
export async function registerMonitor() {
    try {
        const code = generateActivationCode();
        setActivationCode(code);
        document.getElementById('activation-code').textContent = code;

        const response = await fetch(`${API_BASE_URL}/api/devices/monitor/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                activation_code: code,
                device_name: `Monitor-${code}`
            })
        });

        if (!response.ok) {
            throw new Error(`Registration failed: ${response.status}`);
        }

        const data = await response.json();
        setDeviceId(data.id);

        // Save to localStorage
        localStorage.setItem('monitor_device_id', data.id);
        localStorage.setItem('monitor_activation_code', code);
        localStorage.setItem('monitor_status', 'pending');

        console.log('Monitor registered:', data);
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

/**
 * Check activation status using heartbeat endpoint
 * @returns {Promise<Object|null>} Status data or null on error
 */
export async function checkActivationStatus() {
    if (!deviceId || isActivated) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/devices/heartbeat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: parseInt(deviceId)
            })
        });

        if (!response.ok) {
            // Device might be deleted, return error status
            if (response.status === 404) {
                return { status: 'not_found', code: 404 };
            }
            console.error('Heartbeat failed:', response.status);
            return null;
        }

        const data = await response.json();
        console.log('Heartbeat response:', data);

        // Update localStorage with current status
        localStorage.setItem('monitor_status', data.status);

        return data;
    } catch (error) {
        console.error('Status check error:', error);
        return null;
    }
}

/**
 * Start polling for activation status
 * @param {Function} callback - Callback function when status changes
 * @param {number} interval - Poll interval in milliseconds
 */
export function startPolling(callback, interval) {
    const timer = setInterval(callback, interval);
    setPollTimer(timer);
}

/**
 * Stop polling for activation status
 */
export function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        setPollTimer(null);
    }
}

// ========================================
// Device Information Collection
// ========================================

/**
 * Collect device information for heartbeat
 * @returns {Object} Device information object
 */
export function getDeviceInfo() {
    const info = {
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        device_pixel_ratio: window.devicePixelRatio || 1,
        user_agent: navigator.userAgent
    };

    // Get connection information if available
    if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        info.connection_type = connection.effectiveType || connection.type || 'unknown';

        // Calculate speed in Mbps (downlink is in Mbps already)
        if (connection.downlink) {
            info.connection_speed = connection.downlink;
        }
    }

    return info;
}

// ========================================
// Heartbeat Management
// ========================================

/**
 * Send heartbeat to backend
 * @returns {Promise<Object|null>} Heartbeat response or null on error
 */
export async function sendHeartbeat() {
    if (!deviceId) return null;

    try {
        // Collect device information
        const deviceInfo = getDeviceInfo();

        const response = await fetch(`${API_BASE_URL}/api/devices/heartbeat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: parseInt(deviceId),
                ...deviceInfo
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('💓 Heartbeat sent:', data.last_seen);
            return data;
        } else {
            console.error('Heartbeat failed:', response.status);
            return null;
        }
    } catch (error) {
        console.error('❌ Heartbeat error:', error);
        return null;
    }
}

/**
 * Start continuous heartbeat
 * @param {number} interval - Heartbeat interval in milliseconds
 */
export function startHeartbeat(interval) {
    // Send initial heartbeat immediately
    sendHeartbeat();

    // Set up periodic heartbeat
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
    }
    const timer = setInterval(sendHeartbeat, interval);
    setHeartbeatTimer(timer);
    console.log(`🫀 Heartbeat started (every ${interval / 1000} seconds)`);
}

/**
 * Stop heartbeat
 */
export function stopHeartbeat() {
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        setHeartbeatTimer(null);
        console.log('Heartbeat stopped');
    }
}

// ========================================
// Playlist Management
// ========================================

/**
 * Load playlist from backend
 * @returns {Promise<Array>} Playlist array
 */
export async function fetchPlaylist() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/playlist?device_id=${deviceId}`);

        if (!response.ok) {
            throw new Error(`Playlist load failed: ${response.status}`);
        }

        const data = await response.json();

        // Extract playlist array from response
        const playlist = data.playlist || [];

        console.log('Playlist loaded:', playlist);
        return playlist;

    } catch (error) {
        console.error('Playlist load error:', error);
        throw error;
    }
}

/**
 * Refresh playlist from backend
 * @returns {Promise<Object>} Response object with playlist and status code
 */
export async function refreshPlaylist() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/playlist?device_id=${deviceId}`);

        if (!response.ok) {
            return {
                status: response.status,
                playlist: null,
                error: `Playlist refresh failed: ${response.status}`
            };
        }

        const data = await response.json();
        const playlist = data.playlist || [];

        return { status: 200, playlist };

    } catch (error) {
        console.error('Playlist refresh error:', error);
        return {
            status: 0,
            playlist: null,
            error: error.message
        };
    }
}
