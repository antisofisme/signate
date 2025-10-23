/**
 * Activation Module
 * Handles device activation and polling logic
 */

import {
    POLL_INTERVAL,
    HEARTBEAT_INTERVAL,
    PLAYLIST_REFRESH_INTERVAL,
    deviceId,
    deviceUUID,
    isActivated,
    pollTimer,
    heartbeatTimer,
    playlistRefreshTimer,
    contentTimer,
    playlist,
    currentIndex,
    db,
    setPollTimer,
    setHeartbeatTimer,
    setPlaylistRefreshTimer,
    setIsActivated,
    setPlaylist,
    setCurrentIndex,
    setContentTimer,
    setDeviceId,
    setDeviceUUID
} from './config.js';
import { checkActivationStatus, sendHeartbeat, loadPlaylist, refreshPlaylist, registerWebOSDevice } from './api.js';
import { syncCacheWithPlaylist } from './cache.js';
import { playContent, enterFullscreen, exitFullscreen } from './player.js';
import { updateDebug, showError } from './debug.js';
import { getOrCreateDeviceUUID } from './webos-bridge.js';

// ========================================
// Polling and Activation
// ========================================

/**
 * Poll approval status
 */
export async function checkApprovalStatus() {
    if (!deviceId || isActivated) return;

    const data = await checkActivationStatus();

    if (!data) return;

    // Device was deleted, reset to registration mode
    if (data.error && data.status === 404) {
        console.log('⚠️ Device not found (404), re-registering...');
        document.getElementById('status-message').textContent = '🔄 Re-registering...';
        await resetToRegistration();
        return;
    }

    // Check if approved (activated)
    if (data.status === 'active' && !isActivated) {
        console.log('✅ Device approved! Switching to content player...');
        document.getElementById('status-message').textContent = '✅ Disetujui! Loading content...';
        setIsActivated(true);
        localStorage.setItem('webos_status', 'active');
        await onActivated();
    }
}

/**
 * Start polling for approval
 */
export function startPolling() {
    setPollTimer(setInterval(checkApprovalStatus, POLL_INTERVAL));
}

/**
 * Stop polling
 */
export function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        setPollTimer(null);
    }
}

// ========================================
// Heartbeat
// ========================================

/**
 * Start continuous heartbeat
 */
export function startHeartbeat() {
    // Send initial heartbeat immediately
    sendHeartbeat();

    // Set up periodic heartbeat
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
    }
    setHeartbeatTimer(setInterval(sendHeartbeat, HEARTBEAT_INTERVAL));
    console.log('🫀 Heartbeat started (every 30 seconds)');
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
// Playlist Refresh
// ========================================

/**
 * Start periodic playlist refresh
 */
export function startPlaylistRefresh() {
    // Refresh playlist every 10 seconds
    setPlaylistRefreshTimer(setInterval(async () => {
        await refreshPlaylistContent();
    }, PLAYLIST_REFRESH_INTERVAL));

    console.log('📡 Playlist auto-refresh started (every 10 seconds)');
}

/**
 * Stop playlist refresh
 */
export function stopPlaylistRefresh() {
    if (playlistRefreshTimer) {
        clearInterval(playlistRefreshTimer);
        setPlaylistRefreshTimer(null);
        console.log('Playlist auto-refresh stopped');
    }
}

/**
 * Refresh playlist content
 */
async function refreshPlaylistContent() {
    const result = await refreshPlaylist();

    if (result.error) {
        // Device was deleted, reset to registration mode
        if (result.status === 404) {
            await resetToRegistration();
        }
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
            if (contentTimer) {
                clearTimeout(contentTimer);
                setContentTimer(null);
            }
            updateDebug('status', 'No content assigned');
            return;
        }

        // If currently showing content is not in new playlist, restart from beginning
        const currentContentId = oldPlaylist[currentIndex]?.content_id;
        const stillExists = newPlaylist.some(item => item.content_id === currentContentId);

        if (!stillExists) {
            console.log('✨ Content changed, switching to new playlist...');

            // Clear timers
            if (contentTimer) {
                clearTimeout(contentTimer);
                setContentTimer(null);
            }

            // Restart playback from beginning
            setCurrentIndex(0);
            playContent(0);
        }
    }
}

// ========================================
// Activation
// ========================================

/**
 * Monitor activated callback
 */
export async function onActivated() {
    console.log('Monitor activated!');
    updateDebug('status', 'Activated! Loading playlist...');

    // Save activated status to localStorage
    localStorage.setItem('monitor_status', 'active');

    stopPolling();

    // Start continuous heartbeat to maintain online status
    startHeartbeat();

    // Hide activation screen
    document.getElementById('activation-screen').style.display = 'none';

    // Show content player
    const contentPlayer = document.getElementById('content-player');
    if (contentPlayer) {
        contentPlayer.classList.add('active');
        contentPlayer.style.display = 'block';
    }

    // Enter fullscreen
    enterFullscreen();

    // Load and start playlist
    const loadedPlaylist = await loadPlaylist();
    setPlaylist(loadedPlaylist);

    updateDebug('playlist-count', `Playlist: ${loadedPlaylist.length} items`);
    updateDebug('status', 'Syncing offline cache...');

    // Sync cache with new playlist (download missing, remove unused)
    if (db) {
        await syncCacheWithPlaylist(loadedPlaylist);
        updateDebug('status', 'Cache synced, ready to play');
    } else {
        console.warn('⚠️  Cache not available, will stream content');
        updateDebug('status', 'Playing content (streaming mode)');
    }

    // Start playlist
    if (loadedPlaylist.length > 0) {
        setCurrentIndex(0);
        playContent(0);
    }

    // Start periodic playlist refresh to detect new content
    startPlaylistRefresh();
}

// ========================================
// Reset to Registration
// ========================================

/**
 * Reset to registration mode (when device deleted)
 */
export async function resetToRegistration() {
    console.log('❌ Device deleted from server, resetting to registration mode...');

    // Exit fullscreen only if currently in fullscreen
    if (document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement) {
        exitFullscreen();
    }

    // Stop all timers
    stopPolling();
    stopHeartbeat();
    stopPlaylistRefresh();

    if (contentTimer) {
        clearTimeout(contentTimer);
        setContentTimer(null);
    }

    // Clear device data but keep UUID
    localStorage.removeItem('webos_device_id');
    localStorage.removeItem('webos_status');

    // Reset state variables
    setDeviceId(null);
    setIsActivated(false);
    setPlaylist([]);
    setCurrentIndex(0);

    // Clear any playing content first
    const contentPlayer = document.getElementById('content-player');
    if (contentPlayer) {
        // Stop any video that might be playing
        const videos = contentPlayer.querySelectorAll('video');
        videos.forEach(video => {
            video.pause();
            video.src = '';
        });

        // Clear all content
        contentPlayer.innerHTML = '';
        contentPlayer.classList.remove('active');
        contentPlayer.style.display = 'none';
    }

    // Show activation screen with UUID
    const activationScreen = document.getElementById('activation-screen');
    if (activationScreen) {
        activationScreen.style.display = 'flex';
    }

    const uuidElement = document.getElementById('device-uuid');
    if (uuidElement) {
        uuidElement.textContent = deviceUUID;
    }

    const statusElement = document.getElementById('status-message');
    if (statusElement) {
        statusElement.textContent = '❌ Device dihapus dari server. Re-registering...';
    }

    // Small delay to ensure UI updates
    await new Promise(resolve => setTimeout(resolve, 100));

    // Re-register with same UUID
    await registerWebOSDevice(deviceUUID);
    startPolling();
}

/**
 * Reset monitor (clear localStorage and reload)
 */
export function resetMonitor() {
    if (confirm('Reset device? This will clear saved data but keep the same UUID.')) {
        localStorage.removeItem('webos_device_id');
        localStorage.removeItem('webos_status');
        // Keep device_uuid - permanent identifier
        location.reload();
    }
}
