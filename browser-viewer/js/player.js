/**
 * Player Module
 * Manages content playback, scheduling, and transitions
 */

import {
    PRELOAD_TIME,
    playlist,
    currentIndex,
    currentContentElement,
    nextContentElement,
    contentTimer,
    currentBlobUrl,
    db,
    setCurrentIndex,
    setCurrentContentElement,
    setNextContentElement,
    setContentTimer,
    setCurrentBlobUrl
} from './config.js';
import { getCachedBlobUrl } from './cache.js';

// ========================================
// Content Playback
// ========================================

/**
 * Start playing playlist from beginning
 */
export function startPlaylist() {
    if (playlist.length === 0) {
        console.error('Playlist is empty');
        return;
    }

    setCurrentIndex(0);
    playContent(0);
}

/**
 * Play specific content by index
 * @param {number} index - Content index in playlist
 */
export async function playContent(index) {
    // Clear any existing timer first to prevent multiple timers
    if (contentTimer) {
        clearTimeout(contentTimer);
        setContentTimer(null);
    }

    if (index >= playlist.length) {
        index = 0; // Loop to start
    }

    const content = playlist[index];

    // If we're showing the same content again (single item playlist or looping)
    // and the element is already active, just reschedule
    if (currentIndex === index && currentContentElement && currentContentElement.classList.contains('active')) {
        console.log('Same content already showing, rescheduling...');

        // Schedule next content
        const duration = content.duration * 1000;

        // Preload next content
        const preloadTime = Math.max(duration - PRELOAD_TIME, 0);
        setTimeout(() => preloadNextContent(index + 1), preloadTime);

        // Schedule content change
        const timer = setTimeout(() => playContent(index + 1), duration);
        setContentTimer(timer);
        return;
    }

    setCurrentIndex(index);

    console.log('Playing content:', content);

    // Try to get content from cache first (offline mode)
    let contentUrl = content.url; // Fallback to streaming URL
    let useCache = false;

    if (db) {
        try {
            const cachedBlobUrl = await getCachedBlobUrl(content.content_id);
            if (cachedBlobUrl) {
                contentUrl = cachedBlobUrl;
                useCache = true;
                console.log(`📦 Using cached content (ID: ${content.content_id})`);
            } else {
                console.log(`📡 Content not cached, streaming (ID: ${content.content_id})`);
            }
        } catch (error) {
            console.error('Error getting cached content:', error);
            console.log('📡 Falling back to streaming');
        }
    }

    const isVideo = content.content_type === 'video';

    console.log('Content URL:', useCache ? '[Cached Blob]' : contentUrl);

    // DIRECT REPLACEMENT PATTERN (like old viewer - no crossfade, no flicker)
    const player = document.getElementById('content-player');

    // Revoke previous blob URL to prevent memory leak
    if (currentBlobUrl && useCache) {
        URL.revokeObjectURL(currentBlobUrl);
        setCurrentBlobUrl(null);
    }

    // Store new blob URL if using cache
    if (useCache) {
        setCurrentBlobUrl(contentUrl);
    }

    // Clear all content first (key pattern from old viewer)
    console.log('Clearing player (direct replacement)');
    player.innerHTML = '';

    if (isVideo) {
        console.log('Creating video element');
        const element = createVideoElement(contentUrl);

        // Add directly to player
        player.appendChild(element);
        setCurrentContentElement(element);

        // Play video
        element.play().catch(err => console.log('Video play error:', err));

        element.addEventListener('loadeddata', () => {
            console.log('Video loaded and playing');
        }, { once: true });

    } else {
        console.log('Creating image element');
        const element = createImageElement(contentUrl);

        // Add directly to player
        player.appendChild(element);
        setCurrentContentElement(element);

        element.addEventListener('load', () => {
            console.log('Image loaded successfully');
        }, { once: true });
    }

    // Schedule next content
    const duration = content.duration * 1000; // Convert to milliseconds

    // Preload next content
    const preloadTime = Math.max(duration - PRELOAD_TIME, 0);
    setTimeout(() => preloadNextContent(index + 1), preloadTime);

    // Schedule content change
    const timer = setTimeout(() => playContent(index + 1), duration);
    setContentTimer(timer);
}

/**
 * Preload next content for smooth transition
 * @param {number} index - Next content index
 */
export function preloadNextContent(index) {
    if (index >= playlist.length) {
        index = 0;
    }

    const content = playlist[index];
    const contentUrl = content.url; // Use URL from playlist
    const isVideo = content.content_type === 'video';

    // Preload in background
    if (isVideo) {
        const video = document.createElement('video');
        video.src = contentUrl;
        video.preload = 'auto';
        setNextContentElement(video);
    } else {
        const img = new Image();
        img.src = contentUrl;
        setNextContentElement(img);
    }

    console.log('Preloaded next content:', content);
}

/**
 * Stop player and clear all content
 */
export function stopPlayer() {
    // Clear timer
    if (contentTimer) {
        clearTimeout(contentTimer);
        setContentTimer(null);
    }

    // Clear player
    const player = document.getElementById('content-player');
    if (player) {
        player.innerHTML = '';
    }

    // Revoke blob URL
    if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
        setCurrentBlobUrl(null);
    }

    setCurrentContentElement(null);
    setNextContentElement(null);

    console.log('Player stopped');
}

// ========================================
// Content Element Creation
// ========================================

/**
 * Create image element for display
 * @param {string} url - Image URL
 * @returns {HTMLImageElement}
 */
export function createImageElement(url) {
    const img = document.createElement('img');
    img.src = url;
    img.className = 'content-item';
    return img;
}

/**
 * Create video element for playback
 * @param {string} url - Video URL
 * @returns {HTMLVideoElement}
 */
export function createVideoElement(url) {
    const video = document.createElement('video');
    video.src = url;
    video.className = 'content-item';
    video.autoplay = true;
    video.muted = true; // Muted autoplay for browser compatibility
    return video;
}

// ========================================
// Fullscreen Management
// ========================================

/**
 * Enter fullscreen mode
 */
export function enterFullscreen() {
    const elem = document.documentElement;

    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}

/**
 * Exit fullscreen mode
 */
export function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
}

/**
 * Toggle fullscreen mode
 */
export function toggleFullscreen() {
    if (!document.fullscreenElement) {
        enterFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// ========================================
// Error Handling
// ========================================

/**
 * Show error message to user
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
