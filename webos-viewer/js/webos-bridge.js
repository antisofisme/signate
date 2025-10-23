/**
 * WebOS Bridge Module
 * Handles all webOS-specific APIs and device detection
 */

// ========================================
// UUID Generation and Management
// ========================================

/**
 * Generate UUID v4 (RFC 4122 compliant)
 * @returns {string} UUID string
 */
export function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Get or create permanent device UUID
 * @returns {string} Device UUID
 */
export function getOrCreateDeviceUUID() {
    let uuid = localStorage.getItem('device_uuid');
    if (!uuid) {
        uuid = generateUUID();
        localStorage.setItem('device_uuid', uuid);
        console.log('🆕 Generated new device UUID:', uuid);
    } else {
        console.log('✅ Using existing device UUID:', uuid);
    }
    return uuid;
}

/**
 * Generate 6-digit numeric code from UUID (for backend validation)
 * @param {string} uuid - Device UUID
 * @returns {string} 6-digit numeric code
 */
export function generateNumericCodeFromUUID(uuid) {
    // Remove hyphens and take first 8 hex chars
    const hexPart = uuid.replace(/-/g, '').substring(0, 8);
    // Convert hex to number and take last 6 digits
    const numericCode = parseInt(hexPart, 16) % 1000000;
    // Pad with zeros to ensure 6 digits
    return numericCode.toString().padStart(6, '0');
}

// ========================================
// WebOS Device Detection
// ========================================

/**
 * Check if running on webOS
 * @returns {boolean}
 */
export function isWebOSDevice() {
    return typeof window.webOS !== 'undefined';
}

/**
 * Get webOS device information
 * @returns {Object} Device info object
 */
export function getWebOSDeviceInfo() {
    const info = {};

    if (isWebOSDevice()) {
        console.log('🖥️  Running on webOS TV');

        if (window.webOS.deviceInfo) {
            info.platform = 'webOS';
            info.modelName = window.webOS.deviceInfo('modelName') || 'Unknown';
            info.firmwareVersion = window.webOS.deviceInfo('version') || 'Unknown';
            info.sdkVersion = window.webOS.deviceInfo('sdkVersion') || 'Unknown';
        }

        if (window.webOS.platform && window.webOS.platform.tv) {
            info.screenWidth = window.webOS.platform.tv.screenWidth || window.screen.width;
            info.screenHeight = window.webOS.platform.tv.screenHeight || window.screen.height;
        }
    } else {
        info.platform = 'browser';
        info.modelName = 'Browser';
    }

    return info;
}

// ========================================
// WebOS Service Calls
// ========================================

/**
 * Call webOS service (if available)
 * @param {string} service - Service URI
 * @param {Object} params - Service parameters
 * @returns {Promise<Object>}
 */
export function callWebOSService(service, params = {}) {
    return new Promise((resolve, reject) => {
        if (!isWebOSDevice() || !window.webOS.service) {
            reject(new Error('webOS service not available'));
            return;
        }

        window.webOS.service.request(service, {
            parameters: params,
            onSuccess: (result) => resolve(result),
            onFailure: (error) => reject(error)
        });
    });
}

/**
 * Get system information from webOS
 * @returns {Promise<Object>}
 */
export async function getWebOSSystemInfo() {
    try {
        const result = await callWebOSService('luna://com.webos.service.tv.systemproperty/getSystemInfo', {
            keys: ['modelName', 'firmwareVersion', 'UHD', 'sdkVersion']
        });
        return result;
    } catch (error) {
        console.warn('Could not get webOS system info:', error);
        return null;
    }
}

/**
 * Get network information from webOS
 * @returns {Promise<Object>}
 */
export async function getWebOSNetworkInfo() {
    try {
        const result = await callWebOSService('luna://com.webos.service.connectionmanager/getStatus', {});
        return result;
    } catch (error) {
        console.warn('Could not get webOS network info:', error);
        return null;
    }
}

// ========================================
// Device Information Collection
// ========================================

/**
 * Collect comprehensive device information
 * @param {string} deviceUUID - Device UUID
 * @returns {Object} Device information object
 */
export function getDeviceInfo(deviceUUID) {
    // Get webOS-specific info
    const webOSInfo = getWebOSDeviceInfo();

    const info = {
        device_uuid: deviceUUID,
        platform: webOSInfo.platform || 'browser',
        model_name: webOSInfo.modelName || 'Unknown',
        firmware_version: webOSInfo.firmwareVersion || 'N/A',
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
