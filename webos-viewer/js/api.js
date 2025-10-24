/**
 * API Module
 * Handles all backend API communications
 */

import { API_BASE_URL, deviceId, deviceUUID, setDeviceId, setIsActivated } from './config.js';
import { getWebOSDeviceInfo, generateNumericCodeFromUUID, getDeviceInfo } from './webos-bridge.js';
import { updateDebug, showError } from './debug.js';
import { initLogger } from './logger.js';

// ========================================
// Device Registration
// ========================================

/**
 * Register webOS device with UUID (auto-registration)
 * @param {string} uuid - Device UUID
 * @returns {Promise<void>}
 */
export async function registerWebOSDevice(uuid) {
    try {
        // Get webOS device info
        const webOSInfo = getWebOSDeviceInfo();

        // Generate device name based on platform
        const deviceName = webOSInfo.platform === 'webOS'
            ? `${webOSInfo.modelName || 'webOS TV'} - ${uuid.substring(0, 8)}`
            : `Browser - ${uuid.substring(0, 8)}`;

        // Generate 6-digit numeric code from UUID
        const activationCode = generateNumericCodeFromUUID(uuid);
        console.log('🔢 Generated activation code from UUID:', activationCode);

        // Auto-register with UUID
        const response = await fetch(`${API_BASE_URL}/api/devices/monitor/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                activation_code: activationCode,  // 6-digit numeric code
                device_name: deviceName,
                device_uuid: uuid,
                platform: webOSInfo.platform || 'browser',
                model_name: webOSInfo.modelName || 'Unknown'
            })
        });

        if (!response.ok) {
            throw new Error(`Registration failed: ${response.status}`);
        }

        const data = await response.json();
        setDeviceId(data.id);

        // Save to localStorage (using webos_ prefix to differentiate)
        localStorage.setItem('webos_device_id', data.id);
        localStorage.setItem('webos_status', 'pending');

        // Initialize logger immediately after registration
        // This ensures logs are sent even during activation polling, errors, etc.
        initLogger(data.id);

        updateDebug('device-id', `Device ID: ${data.id}`);
        updateDebug('status', 'Registered. Waiting for approval...');

        console.log('✅ webOS device registered:', { deviceId: data.id, deviceUUID: uuid, deviceName });
        document.getElementById('status-message').textContent = '⏳ Menunggu persetujuan dari server...';
    } catch (error) {
        console.error('❌ Registration error:', error);
        document.getElementById('status-message').textContent = '❌ Gagal registrasi. Retry...';
        showError('Failed to register device. Retrying in 10 seconds...');
        setTimeout(() => registerWebOSDevice(uuid), 10000);
    }
}

// ========================================
// Heartbeat and Status
// ========================================

/**
 * Send heartbeat to backend
 * @returns {Promise<Object|null>}
 */
export async function sendHeartbeat() {
    if (!deviceId) return null;

    try {
        // Collect device information
        const deviceInfo = getDeviceInfo(deviceUUID);

        // Use Object.assign for WebOS TV compatibility (no spread operator)
        const payload = Object.assign(
            { device_id: parseInt(deviceId) },
            deviceInfo
        );

        const response = await fetch(`${API_BASE_URL}/api/devices/heartbeat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            console.log('💓 Heartbeat sent:', data.last_seen);
            updateDebug('status', `Online - Last heartbeat: ${new Date().toLocaleTimeString()}`);
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
 * Check activation status using heartbeat endpoint
 * @returns {Promise<Object|null>}
 */
export async function checkActivationStatus() {
    if (!deviceId) return null;

    try {
        // Get device info for heartbeat
        const deviceInfo = getDeviceInfo(deviceUUID);

        // Use Object.assign for WebOS TV compatibility (no spread operator)
        const payload = Object.assign(
            { device_id: parseInt(deviceId) },
            deviceInfo
        );

        const response = await fetch(`${API_BASE_URL}/api/devices/heartbeat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            return { error: true, status: response.status };
        }

        const data = await response.json();
        console.log('💓 Heartbeat response:', data);

        // Update localStorage with current status
        localStorage.setItem('webos_status', data.status);

        return data;
    } catch (error) {
        console.error('❌ Status check error:', error);
        return null;
    }
}

// ========================================
// Playlist Management
// ========================================

/**
 * Load playlist from backend
 * @returns {Promise<Array>}
 */
export async function loadPlaylist() {
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
        showError('Failed to load playlist. Retrying in 10 seconds...');
        throw error;
    }
}

/**
 * Refresh playlist from backend
 * @returns {Promise<Object>}
 */
export async function refreshPlaylist() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/playlist?device_id=${deviceId}`);

        if (!response.ok) {
            return { error: true, status: response.status };
        }

        const data = await response.json();
        const newPlaylist = data.playlist || [];

        return { playlist: newPlaylist };

    } catch (error) {
        console.error('Playlist refresh error:', error);
        return { error: true, message: error.message };
    }
}
