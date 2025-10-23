/**
 * Main Application Module
 * Orchestrates initialization, activation flow, and playlist management
 */

import {
    POLL_INTERVAL,
    HEARTBEAT_INTERVAL,
    PLAYLIST_REFRESH_INTERVAL,
    deviceId,
    isActivated,
    playlist,
    currentIndex,
    db,
    setDeviceId,
    setActivationCode,
    setIsActivated,
    setPlaylist,
    setCurrentIndex,
    setContentTimer,
    setPlaylistRefreshTimer
} from './config.js';
import { initMediaCache, syncCacheWithPlaylist } from './cache.js';
import {
    registerMonitor,
    checkActivationStatus,
    startPolling,
    stopPolling,
    fetchPlaylist,
    refreshPlaylist,
    startHeartbeat,
    stopHeartbeat
} from './api.js';
import {
    startPlaylist,
    playContent,
    enterFullscreen,
    showError,
    stopPlayer
} from './player.js';
import {
    showActivationScreen,
    hideActivationScreen,
    showContentPlayer,
    updateActivationCode,
    resetToRegistration,
    loadSavedDevice,
    applySavedDevice
} from './activation.js';
import { updateDebug, setupKeyboardShortcuts } from './debug.js';

// ========================================
// Application Initialization
// ========================================

/**
 * Initialize application
 */
export async function init() {
    updateDebug('status', 'Initializing...');

    // Initialize IndexedDB for offline caching
    try {
        await initMediaCache();
        console.log('📦 Media cache initialized');
    } catch (error) {
        console.error('❌ Failed to initialize media cache:', error);
        showError('Failed to initialize offline cache. Content may stream instead of cache.');
    }

    // Check if already registered (from localStorage)
    const savedDevice = loadSavedDevice();

    if (savedDevice) {
        // Use saved device
        applySavedDevice(savedDevice);

        updateDebug('device-id', `Device ID: ${savedDevice.deviceId}`);
        updateDebug('status', 'Using saved monitor...');

        // Check if already activated
        if (savedDevice.status === 'active') {
            // Already activated, start content player
            setIsActivated(true);
            await onActivated();
        } else {
            // Still pending, start polling for activation
            startPolling(pollActivationCallback, POLL_INTERVAL);
        }
    } else {
        // Register new monitor
        try {
            await registerMonitor();
            startPolling(pollActivationCallback, POLL_INTERVAL);
        } catch (error) {
            showError('Failed to register monitor. Retrying in 10 seconds...');
            setTimeout(init, 10000);
        }
    }

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    // Setup custom event listeners for debug commands
    setupCustomEventListeners();
}

// ========================================
// Activation Flow
// ========================================

/**
 * Callback for activation status polling
 */
async function pollActivationCallback() {
    const data = await checkActivationStatus();

    if (!data) return;

    // Handle device not found (deleted from server)
    if (data.status === 'not_found' || data.code === 404) {
        console.log('Device not found (404), re-registering...');
        stopPolling();
        localStorage.clear();
        setDeviceId(null);
        setActivationCode(null);
        setIsActivated(false);
        await registerMonitor();
        startPolling(pollActivationCallback, POLL_INTERVAL);
        return;
    }

    // Check if activated
    if (data.status === 'active' && !isActivated) {
        console.log('Device activated! Switching to content player...');
        setIsActivated(true);
        localStorage.setItem('monitor_status', 'active');
        await onActivated();
    }
}

/**
 * Handle monitor activation
 */
export async function onActivated() {
    console.log('Monitor activated!');
    updateDebug('status', 'Activated! Loading playlist...');

    // Save activated status to localStorage
    localStorage.setItem('monitor_status', 'active');

    stopPolling();

    // Start continuous heartbeat to maintain online status
    startHeartbeat(HEARTBEAT_INTERVAL);

    // Hide activation screen
    hideActivationScreen();

    // Show content player
    showContentPlayer();

    // Enter fullscreen
    enterFullscreen();

    // Load and start playlist
    await loadPlaylistAndStart();

    // Start periodic playlist refresh to detect new content
    startPlaylistRefresh();
}

// ========================================
// Playlist Management
// ========================================

/**
 * Load playlist and start playback
 */
export async function loadPlaylistAndStart() {
    try {
        const newPlaylist = await fetchPlaylist();
        setPlaylist(newPlaylist);

        updateDebug('playlist-count', `Playlist: ${newPlaylist.length} items`);
        updateDebug('status', 'Syncing offline cache...');

        console.log('Playlist loaded:', newPlaylist);

        // Sync cache with new playlist (download missing, remove unused)
        if (db) {
            await syncCacheWithPlaylist(newPlaylist);
            updateDebug('status', 'Cache synced, ready to play');
        } else {
            console.warn('⚠️  Cache not available, will stream content');
            updateDebug('status', 'Playing content (streaming mode)');
        }

        // Start playback
        if (newPlaylist.length > 0) {
            startPlaylist();
        } else {
            showError('Playlist is empty');
        }

    } catch (error) {
        console.error('Playlist load error:', error);
        showError('Failed to load playlist. Retrying in 10 seconds...');
        setTimeout(loadPlaylistAndStart, 10000);
    }
}

/**
 * Refresh playlist and handle updates
 */
async function handlePlaylistRefresh() {
    const result = await refreshPlaylist();

    // Device was deleted, reset to registration mode
    if (result.status === 404) {
        await resetToRegistration();
        return;
    }

    if (result.status !== 200 || !result.playlist) {
        console.error('Playlist refresh failed:', result.error);
        return;
    }

    const newPlaylist = result.playlist;

    // Check if playlist changed
    if (JSON.stringify(newPlaylist) !== JSON.stringify(playlist)) {
        console.log('✨ Playlist updated! Reloading content...');
        console.log('Old playlist:', playlist.length, 'items');
        console.log('New playlist:', newPlaylist.length, 'items');

        // Save old playlist before updating (important for comparison!)
        const oldPlaylist = playlist;

        // Update playlist
        setPlaylist(newPlaylist);
        updateDebug('playlist-count', `Playlist: ${newPlaylist.length} items`);

        // Sync cache with updated playlist
        if (db) {
            console.log('🔄 Syncing cache with updated playlist...');
            await syncCacheWithPlaylist(newPlaylist);
        }

        // If playlist is empty, stop playing
        if (newPlaylist.length === 0) {
            console.log('Playlist is empty, stopping playback');
            stopPlayer();
            setContentTimer(null);
            updateDebug('status', 'No content assigned');
            return;
        }

        // If currently showing content is not in new playlist, restart from beginning
        const currentContentId = oldPlaylist[currentIndex]?.content_id;
        const stillExists = newPlaylist.some(item => item.content_id === currentContentId);

        if (!stillExists) {
            console.log('✨ Content changed, switching to new playlist...');
            setCurrentIndex(0);
            playContent(0);
        }
    }
}

/**
 * Start periodic playlist refresh
 */
function startPlaylistRefresh() {
    const timer = setInterval(() => {
        handlePlaylistRefresh();
    }, PLAYLIST_REFRESH_INTERVAL);

    setPlaylistRefreshTimer(timer);
    console.log(`📡 Playlist auto-refresh started (every ${PLAYLIST_REFRESH_INTERVAL / 1000} seconds)`);
}

// ========================================
// Custom Event Handlers
// ========================================

/**
 * Setup custom event listeners for inter-module communication
 */
function setupCustomEventListeners() {
    // Handle skip to next content
    document.addEventListener('skipToNext', () => {
        if (isActivated && playlist.length > 0) {
            setContentTimer(null);
            playContent(currentIndex + 1);
        }
    });

    // Handle reload playlist
    document.addEventListener('reloadPlaylist', async () => {
        if (isActivated) {
            await loadPlaylistAndStart();
        }
    });
}

// ========================================
// Export for global access (if needed)
// ========================================

// Make init available globally for inline script execution
window.initApp = init;
