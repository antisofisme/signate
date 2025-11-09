/**
 * Player Playback Module
 * Handles content playback (images and videos)
 */

window.PlayerPlayback = {
    /**
     * Play content at given index
     */
    playContent: async function(index) {
        // ✅ STATE MIGRATION: Use NEW playerState, fallback to OLD
        const state = window.PlayerState; // Keep for contentTimer (runtime state)

        // Clear existing timer (still use PlayerState for runtime state)
        if (state && state.contentTimer) {
            clearTimeout(state.contentTimer);
            state.contentTimer = null;
        }

        // ✅ STATE MIGRATION: Get playlist from playerState
        const playlistObj = window.PlayerState ? window.PlayerState.getPlaylist() : null;
        const playlist = playlistObj ? (playlistObj.contents || playlistObj) : state?.playlist;

        // ✅ NULL CHECK: Ensure playlist exists and has content
        if (!playlist || playlist.length === 0) {
            SharedLogger.error('[Player/Playback] No playlist available');
            if (window.PlayerUI) {
                window.PlayerUI.showWaiting('⏳ Waiting for content...');
            }
            return;
        }

        // Loop to start if index out of bounds
        if (index >= playlist.length) {
            index = 0;
        }

        const content = playlist[index];

        // ✅ NULL CHECK: Ensure content exists
        if (!content) {
            SharedLogger.error('[Player/Playback] Content not found at index:', index);
            return;
        }

        // ✅ STATE MIGRATION: Use PlayerState.setCurrentIndex() for reactive updates
        if (window.PlayerState && window.PlayerState.setCurrentIndex) {
            window.PlayerState.setCurrentIndex(index);
        } else if (state) {
            // Fallback to OLD pattern
            state.currentIndex = index;
        }

        SharedLogger.log('[Player/Playback] Playing:', content.title || content.name);

        // Check if content is cached (for debug info)
        let isCached = false;
        try {
            isCached = await window.PlayerCache.isContentCached(content.content_id);
        } catch (error) {
            SharedLogger.error('[Player] Cache check error:', error);
        }

        // Update debug info
        if (window.PlayerUI && window.PlayerUI.updateDebugInfo) {
            window.PlayerUI.updateDebugInfo(content, index, isCached);
        }

        // Clear existing content
        const display = document.getElementById('content-display');

        // ✅ NULL CHECK: Ensure display element exists
        if (!display) {
            SharedLogger.error('[Player/Playback] content-display element not found');
            return;
        }

        display.innerHTML = '';

        // Create content element
        if (content.content_type === 'video') {
            await this.playVideo(content);
        } else {
            await this.playImage(content);
        }

        // Schedule next content
        const duration = content.duration * 1000;
        if (state) {
            state.contentTimer = setTimeout(() => this.playContent(index + 1), duration);
        }
    },

    /**
     * Play image content
     */
    playImage: async function(content) {
        const display = document.getElementById('content-display');

        // ✅ NULL CHECK: Ensure display element exists
        if (!display) {
            SharedLogger.error('[Player/Playback] content-display element not found');
            return;
        }

        // ✅ NULL CHECK: Ensure content has URL
        if (!content || !content.url) {
            SharedLogger.error('[Player/Playback] Invalid image content:', content);
            return;
        }

        const img = document.createElement('img');

        // Try to get cached blob URL first
        try {
            const blobUrl = await window.PlayerCache.getCachedBlobUrl(content.content_id);
            if (blobUrl) {
                img.src = blobUrl;
                SharedLogger.log('[Player] Playing from cache ✅');
            } else {
                img.src = content.url;
                SharedLogger.log('[Player] Streaming (not cached yet)');
            }
        } catch (error) {
            SharedLogger.error('[Player] Cache error, falling back to streaming:', error);
            img.src = content.url;
        }

        img.alt = content.title;

        img.onerror = () => {
            SharedLogger.error('[Player] Image load failed:', content.url);
            if (window.PlayerUI) {
                window.PlayerUI.showError(`Failed to load image: ${content.title || 'Unknown'}`);
            }

            // Skip to next content
            // ✅ STATE MIGRATION: Get current index from playerState
            const currentIndex = window.PlayerState ? window.PlayerState.getCurrentIndex() : window.PlayerState?.currentIndex || 0;
            setTimeout(() => this.playContent(currentIndex + 1), 3000);
        };

        img.onload = () => {
            SharedLogger.log('[Player] Image loaded ✅');
            window.PlayerUI.hideError();

            // Detect orientation and apply class
            const isLandscape = img.naturalWidth > img.naturalHeight;
            img.className = isLandscape ? 'landscape' : 'portrait';
            SharedLogger.log('[Player] Image orientation:', img.className, `(${img.naturalWidth}x${img.naturalHeight})`);
        };

        display.appendChild(img);
    },

    /**
     * Play video content with optional segment timing
     */
    playVideo: async function(content) {
        const display = document.getElementById('content-display');

        // ✅ NULL CHECK: Ensure display element exists
        if (!display) {
            SharedLogger.error('[Player/Playback] content-display element not found');
            return;
        }

        // ✅ NULL CHECK: Ensure content has URL
        if (!content || !content.url) {
            SharedLogger.error('[Player/Playback] Invalid video content:', content);
            return;
        }

        const video = document.createElement('video');

        // Try to get cached blob URL first
        try {
            const blobUrl = await window.PlayerCache.getCachedBlobUrl(content.content_id);
            if (blobUrl) {
                video.src = blobUrl;
                SharedLogger.log('[Player] Playing from cache ✅');
            } else {
                video.src = content.url;
                SharedLogger.log('[Player] Streaming (not cached yet)');
            }
        } catch (error) {
            SharedLogger.error('[Player] Cache error, falling back to streaming:', error);
            video.src = content.url;
        }

        video.autoplay = true;

        // ✅ STATE MIGRATION: Get volume from playerState
        const volume = window.PlayerState ? window.PlayerState.getVolume() : (window.PlayerState?.volumeEnabled ? 1.0 : 0.0);
        const volumeEnabled = volume > 0;
        video.muted = !volumeEnabled;

        SharedLogger.log('[Player] Video volume:', volumeEnabled ? `Enabled (${volume})` : 'Muted');

        // Video segment timing
        const startTime = content.video_start_time || 0;
        const endTime = content.video_end_time; // null or undefined = play to end

        if (startTime > 0) {
            SharedLogger.log(`[Player] Video segment: ${startTime}s - ${endTime ? endTime + 's' : 'end'}`);
        }

        video.onerror = () => {
            SharedLogger.error('[Player] Video load failed:', content.url);
            if (window.PlayerUI) {
                window.PlayerUI.showError(`Failed to load video: ${content.title || 'Unknown'}`);
            }

            // Skip to next content
            // ✅ STATE MIGRATION: Get current index from playerState
            const currentIndex = window.PlayerState ? window.PlayerState.getCurrentIndex() : window.PlayerState?.currentIndex || 0;
            setTimeout(() => this.playContent(currentIndex + 1), 3000);
        };

        video.onloadeddata = async () => {
            SharedLogger.log('[Player] Video loaded ✅');
            window.PlayerUI.hideError();

            // Detect orientation and apply class
            const isLandscape = video.videoWidth > video.videoHeight;
            video.className = isLandscape ? 'landscape' : 'portrait';
            SharedLogger.log('[Player] Video orientation:', video.className, `(${video.videoWidth}x${video.videoHeight})`);

            // Explicitly play video first (required for modern browsers)
            try {
                await video.play();
                SharedLogger.log('[Player] Video playback started ✅');

                // AFTER video is playing, seek to start time if specified
                // This prevents freeze issues when setting currentTime before play
                if (startTime > 0) {
                    video.currentTime = startTime;
                    SharedLogger.log('[Player] Seeking to start time:', startTime + 's');
                }
            } catch (error) {
                SharedLogger.error('[Player] Video playback failed:', error);
                // Try to play without promise (fallback)
                video.play().catch(e => {
                    SharedLogger.error('[Player] Video play fallback also failed:', e);
                    if (window.PlayerUI) {
                        window.PlayerUI.showError(`Failed to play video: ${content.title || 'Unknown'}`);
                    }
                    // Skip to next content after 3 seconds
                    // ✅ STATE MIGRATION: Get current index from playerState
                    const currentIndex = window.PlayerState ? window.PlayerState.getCurrentIndex() : window.PlayerState?.currentIndex || 0;
                    setTimeout(() => this.playContent(currentIndex + 1), 3000);
                });
            }
        };

        // Monitor playback time for custom end time
        if (endTime && endTime > startTime) {
            video.ontimeupdate = () => {
                if (video.currentTime >= endTime) {
                    SharedLogger.log('[Player] Reached end time:', endTime + 's');
                    // ✅ STATE MIGRATION: Use playNext() for reactive state update
                    if (window.PlayerState && window.PlayerState.playNext) {
                        window.PlayerState.playNext();
                        const nextContent = window.PlayerState.getCurrentContent();
                        if (nextContent) {
                            this.playContent(window.PlayerState.getCurrentIndex());
                        }
                    } else {
                        // Fallback
                        const currentIndex = window.PlayerState?.currentIndex || 0;
                        this.playContent(currentIndex + 1);
                    }
                }
            };
        }

        // Auto-advance when video ends naturally (for videos without end time)
        video.onended = () => {
            SharedLogger.log('[Player] Video ended, advancing...');
            // ✅ STATE MIGRATION: Use playNext() for reactive state update
            if (window.PlayerState && window.PlayerState.playNext) {
                window.PlayerState.playNext();
                const nextContent = window.PlayerState.getCurrentContent();
                if (nextContent) {
                    this.playContent(window.PlayerState.getCurrentIndex());
                }
            } else {
                // Fallback
                const currentIndex = window.PlayerState?.currentIndex || 0;
                this.playContent(currentIndex + 1);
            }
        };

        display.appendChild(video);
    }
};
