/**
 * Debug Module
 * Handles debug information display and keyboard shortcuts
 */

import { debugMode, isActivated, playlist, currentIndex, contentTimer, setDebugMode, setContentTimer } from './config.js';
import { toggleFullscreen } from './player.js';
import { playContent } from './player.js';
import { loadPlaylist } from './api.js';
import { resetMonitor } from './activation.js';
import { setPlaylist, setCurrentIndex } from './config.js';

// ========================================
// Debug Information Display
// ========================================

/**
 * Update debug info
 * @param {string} field - Field name (e.g., 'status', 'device-id')
 * @param {string} value - Value to display
 */
export function updateDebug(field, value) {
    const element = document.getElementById(`debug-${field}`);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Toggle debug mode
 */
export function toggleDebug() {
    setDebugMode(!debugMode);
    const debugInfo = document.getElementById('debug-info');

    if (debugMode) {
        debugInfo.classList.add('visible');
    } else {
        debugInfo.classList.remove('visible');
    }
}

// ========================================
// Error Messages
// ========================================

/**
 * Show error message
 * @param {string} message - Error message to display
 */
export function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.classList.add('visible');

    setTimeout(() => {
        errorDiv.classList.remove('visible');
    }, 5000);
}

// ========================================
// Keyboard Shortcuts
// ========================================

/**
 * Setup keyboard shortcuts
 */
export function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        switch(e.key.toLowerCase()) {
            case 'd':
                // Toggle debug info
                toggleDebug();
                break;
            case 'f':
                // Toggle fullscreen
                toggleFullscreen();
                break;
            case 'n':
                // Next content (if activated)
                if (isActivated && playlist.length > 0) {
                    clearTimeout(contentTimer);
                    playContent(currentIndex + 1);
                }
                break;
            case 'r':
                // Reload playlist (if activated)
                if (isActivated) {
                    loadPlaylist().then((loadedPlaylist) => {
                        setPlaylist(loadedPlaylist);
                        clearTimeout(contentTimer);
                        setContentTimer(null);
                        setCurrentIndex(0);
                        playContent(0);
                    });
                }
                break;
            case 'x':
                // Reset monitor (only if NOT activated yet)
                if (!isActivated) {
                    resetMonitor();
                }
                break;
        }
    });
}
