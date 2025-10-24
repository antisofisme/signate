/**
 * Debug Module
 * Handles debug mode, keyboard shortcuts, and debug information display
 */

import {
    debugMode,
    isActivated,
    playlist,
    currentIndex,
    contentTimer,
    setDebugMode
} from './config.js';
import { toggleFullscreen } from './player.js';
import { resetMonitor } from './activation.js';

// ========================================
// Debug Information Display
// ========================================

/**
 * Toggle debug mode on/off
 */
export function toggleDebug() {
    const newDebugMode = !debugMode;
    setDebugMode(newDebugMode);
    const debugInfo = document.getElementById('debug-info');

    if (newDebugMode) {
        debugInfo.classList.add('visible');
    } else {
        debugInfo.classList.remove('visible');
    }
}

/**
 * Update debug information field
 * @param {string} field - Field name (without 'debug-' prefix)
 * @param {string} value - Value to display
 */
export function updateDebug(field, value) {
    const element = document.getElementById(`debug-${field}`);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Update all debug information
 * @param {Object} data - Debug data object
 */
export function updateAllDebugInfo(data) {
    if (data.deviceId !== undefined) {
        updateDebug('device-id', `Device ID: ${data.deviceId || '-'}`);
    }
    if (data.status !== undefined) {
        updateDebug('status', data.status);
    }
    if (data.playlistCount !== undefined) {
        updateDebug('playlist-count', `Playlist: ${data.playlistCount} items`);
    }
    if (data.currentIndex !== undefined) {
        updateDebug('current-index', `Current: ${data.currentIndex}`);
    }
    if (data.nextChange !== undefined) {
        updateDebug('next-change', `Next change: ${data.nextChange}`);
    }
}

// ========================================
// Keyboard Shortcuts
// ========================================

/**
 * Setup keyboard shortcuts for debugging and control
 */
export function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        handleKeyPress(e.key.toLowerCase());
    });
}

/**
 * Handle keyboard press
 * @param {string} key - Pressed key in lowercase
 */
export function handleKeyPress(key) {
    switch(key) {
        case 'c':
            // Clear cache and reload
            clearCacheAndReload();
            break;
        case 'd':
            // Toggle debug mode
            toggleDebug();
            break;
        case 'f':
            // Toggle fullscreen
            toggleFullscreen();
            break;
        case 'n':
            // Next content (only when activated)
            if (isActivated && playlist.length > 0) {
                skipToNext();
            }
            break;
        case 'r':
            // Reload playlist (only when activated)
            if (isActivated) {
                reloadPlaylist();
            }
            break;
        case 'x':
            // Reset monitor (only if NOT activated yet)
            if (!isActivated) {
                resetMonitor();
            }
            break;
    }
}

/**
 * Skip to next content
 */
export function skipToNext() {
    // This will be implemented by importing playContent from player.js
    // For now, we'll dispatch a custom event
    const event = new CustomEvent('skipToNext');
    document.dispatchEvent(event);
}

/**
 * Reload playlist and restart playback
 */
export function reloadPlaylist() {
    // This will be implemented by importing functions from app.js
    // For now, we'll dispatch a custom event
    const event = new CustomEvent('reloadPlaylist');
    document.dispatchEvent(event);
}

/**
 * Clear IndexedDB cache and reload page
 */
export function clearCacheAndReload() {
    console.log('🗑️  Clearing IndexedDB cache...');

    // Delete IndexedDB database
    const deleteRequest = indexedDB.deleteDatabase('signage-media-cache');

    deleteRequest.onsuccess = () => {
        console.log('✅ Cache cleared, reloading...');
        location.reload();
    };

    deleteRequest.onerror = () => {
        console.error('❌ Failed to clear cache');
        // Reload anyway
        location.reload();
    };

    deleteRequest.onblocked = () => {
        console.warn('⚠️  Cache deletion blocked, reloading anyway...');
        location.reload();
    };
}

// ========================================
// Debug Utilities
// ========================================

/**
 * Log debug message to console (only if debug mode is enabled)
 * @param {string} message - Message to log
 * @param {any} data - Optional data to log
 */
export function debugLog(message, data = null) {
    if (debugMode) {
        if (data !== null) {
            console.log(`[DEBUG] ${message}`, data);
        } else {
            console.log(`[DEBUG] ${message}`);
        }
    }
}

/**
 * Get current debug status summary
 * @returns {Object} Debug status object
 */
export function getDebugStatus() {
    return {
        debugMode,
        isActivated,
        playlistLength: playlist.length,
        currentIndex,
        hasContentTimer: !!contentTimer
    };
}
