/**
 * App Module
 * Main application initialization and orchestration
 */

import { setDeviceId, setDeviceUUID, setIsActivated } from './config.js';
import { initMediaCache } from './cache.js';
import { getOrCreateDeviceUUID, getWebOSDeviceInfo } from './webos-bridge.js';
import { registerWebOSDevice } from './api.js';
import { startPolling, onActivated } from './activation.js';
import { updateDebug, setupKeyboardShortcuts, showError } from './debug.js';
import { initLogger } from './logger.js';

// ========================================
// Application Initialization
// ========================================

/**
 * Initialize the application
 */
export async function init() {
    updateDebug('status', 'Initializing...');

    // Get or create permanent device UUID (FIRST!)
    const uuid = getOrCreateDeviceUUID();
    setDeviceUUID(uuid);
    console.log('🔑 Device UUID:', uuid);

    // Display UUID on screen
    document.getElementById('device-uuid').textContent = uuid;

    // Get webOS device info if available
    const webOSInfo = getWebOSDeviceInfo();
    if (webOSInfo.platform === 'webOS') {
        console.log('📺 webOS TV Model:', webOSInfo.modelName);
        console.log('📱 Firmware:', webOSInfo.firmwareVersion);
    }

    // Initialize IndexedDB for offline caching
    try {
        await initMediaCache();
        console.log('📦 Media cache initialized');
    } catch (error) {
        console.error('❌ Failed to initialize media cache:', error);
        showError('Failed to initialize offline cache. Content may stream instead of cache.');
    }

    // Check if already registered (from localStorage)
    const savedDeviceId = localStorage.getItem('webos_device_id');
    const savedStatus = localStorage.getItem('webos_status');

    if (savedDeviceId) {
        // Use saved device
        setDeviceId(savedDeviceId);

        updateDebug('device-id', `Device ID: ${savedDeviceId}`);
        updateDebug('status', 'Using saved device...');

        // Initialize logger immediately (even before activation)
        initLogger(savedDeviceId);

        console.log('Using saved device:', { deviceId: savedDeviceId, deviceUUID: uuid, status: savedStatus });

        // Check if already activated
        if (savedStatus === 'active') {
            // Already activated, start content player
            setIsActivated(true);
            await onActivated();
        } else {
            // Still pending, start polling for approval
            document.getElementById('status-message').textContent = '⏳ Menunggu persetujuan dari server...';
            startPolling();
        }
    } else {
        // Register new device with UUID
        await registerWebOSDevice(uuid);
        startPolling();
    }

    setupKeyboardShortcuts();
}
