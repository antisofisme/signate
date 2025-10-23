/**
 * Activation Module
 * Manages activation screen display and status updates
 */

import {
    deviceId,
    activationCode,
    playlistRefreshTimer,
    contentTimer,
    setDeviceId,
    setActivationCode,
    setIsActivated,
    setPlaylist,
    setCurrentIndex,
    setPlaylistRefreshTimer,
    setContentTimer
} from './config.js';
import { stopPolling, stopHeartbeat } from './api.js';
import { exitFullscreen } from './player.js';

// ========================================
// Activation Screen Management
// ========================================

/**
 * Show activation screen
 */
export function showActivationScreen() {
    const activationScreen = document.getElementById('activation-screen');
    if (activationScreen) {
        activationScreen.style.display = 'flex';
    }

    const contentPlayer = document.getElementById('content-player');
    if (contentPlayer) {
        contentPlayer.classList.remove('active');
        contentPlayer.style.display = 'none';
    }
}

/**
 * Hide activation screen
 */
export function hideActivationScreen() {
    const activationScreen = document.getElementById('activation-screen');
    if (activationScreen) {
        activationScreen.style.display = 'none';
    }
}

/**
 * Update activation code display
 * @param {string} code - Activation code to display
 */
export function updateActivationCode(code) {
    const codeElement = document.getElementById('activation-code');
    if (codeElement) {
        codeElement.textContent = code;
    }
}

/**
 * Show content player
 */
export function showContentPlayer() {
    const contentPlayer = document.getElementById('content-player');
    if (contentPlayer) {
        contentPlayer.classList.add('active');
        contentPlayer.style.display = 'block';
    }
}

// ========================================
// Device Reset Functions
// ========================================

/**
 * Reset to registration mode (when device deleted or reset requested)
 * @returns {Promise<void>}
 */
export async function resetToRegistration() {
    console.log('❌ Resetting to registration mode...');

    // Exit fullscreen only if currently in fullscreen
    if (document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement) {
        exitFullscreen();
    }

    // Stop all timers
    stopPolling();
    stopHeartbeat();
    if (playlistRefreshTimer) {
        clearInterval(playlistRefreshTimer);
        setPlaylistRefreshTimer(null);
    }
    if (contentTimer) {
        clearTimeout(contentTimer);
        setContentTimer(null);
    }

    // Clear localStorage
    localStorage.clear();

    // Reset state variables
    setDeviceId(null);
    setActivationCode(null);
    setIsActivated(false);
    setPlaylist([]);
    setCurrentIndex(0);

    // Clear any playing content first
    const imagePlayer = document.getElementById('image-player');
    const videoPlayer = document.getElementById('video-player');
    if (videoPlayer) {
        videoPlayer.pause();
        videoPlayer.src = '';
    }
    if (imagePlayer) {
        imagePlayer.style.display = 'none';
    }
    if (videoPlayer) {
        videoPlayer.style.display = 'none';
    }

    // Reset UI - hide content player
    const contentPlayer = document.getElementById('content-player');
    if (contentPlayer) {
        contentPlayer.classList.remove('active');
        contentPlayer.style.display = 'none';
    }

    // Show activation screen
    showActivationScreen();

    // Small delay to ensure UI updates
    await new Promise(resolve => setTimeout(resolve, 100));
}

/**
 * Reset monitor (clear localStorage and reload page)
 * Used when user manually requests reset
 */
export function resetMonitor() {
    if (confirm('Reset monitor? This will clear saved data and generate a new activation code.')) {
        localStorage.removeItem('monitor_device_id');
        localStorage.removeItem('monitor_activation_code');
        localStorage.removeItem('monitor_status');
        location.reload();
    }
}

/**
 * Load saved device data from localStorage
 * @returns {Object|null} Saved device data or null if not found
 */
export function loadSavedDevice() {
    const savedDeviceId = localStorage.getItem('monitor_device_id');
    const savedActivationCode = localStorage.getItem('monitor_activation_code');
    const savedStatus = localStorage.getItem('monitor_status');

    if (savedDeviceId && savedActivationCode) {
        return {
            deviceId: savedDeviceId,
            activationCode: savedActivationCode,
            status: savedStatus
        };
    }

    return null;
}

/**
 * Apply saved device data to application state
 * @param {Object} savedData - Saved device data
 */
export function applySavedDevice(savedData) {
    setDeviceId(savedData.deviceId);
    setActivationCode(savedData.activationCode);
    updateActivationCode(savedData.activationCode);

    console.log('Using saved monitor:', savedData);
}
