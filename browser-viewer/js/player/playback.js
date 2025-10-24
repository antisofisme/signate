/**
 * Player Playback Module
 * Handles content playback (images and videos)
 */

window.PlayerPlayback = {
    /**
     * Play content at given index
     */
    playContent: async function(index) {
        const state = window.PlayerState;

        // Clear existing timer
        if (state.contentTimer) {
            clearTimeout(state.contentTimer);
            state.contentTimer = null;
        }

        if (index >= state.playlist.length) {
            index = 0; // Loop to start
        }

        const content = state.playlist[index];
        state.currentIndex = index;

        console.log('[Player] Playing:', content.title);

        // Check if content is cached (for debug info)
        let isCached = false;
        try {
            isCached = await window.PlayerCache.isContentCached(content.content_id);
        } catch (error) {
            console.error('[Player] Cache check error:', error);
        }

        // Update debug info
        window.PlayerUI.updateDebugInfo(content, index, isCached);

        // Clear existing content
        const display = document.getElementById('content-display');
        display.innerHTML = '';

        // Create content element
        if (content.content_type === 'video') {
            await this.playVideo(content);
        } else {
            await this.playImage(content);
        }

        // Schedule next content
        const duration = content.duration * 1000;
        state.contentTimer = setTimeout(() => this.playContent(index + 1), duration);
    },

    /**
     * Play image content
     */
    playImage: async function(content) {
        const state = window.PlayerState;
        const display = document.getElementById('content-display');

        const img = document.createElement('img');

        // Try to get cached blob URL first
        try {
            const blobUrl = await window.PlayerCache.getCachedBlobUrl(content.content_id);
            if (blobUrl) {
                img.src = blobUrl;
                console.log('[Player] Playing from cache ✅');
            } else {
                img.src = content.url;
                console.log('[Player] Streaming (not cached yet)');
            }
        } catch (error) {
            console.error('[Player] Cache error, falling back to streaming:', error);
            img.src = content.url;
        }

        img.alt = content.title;

        img.onerror = () => {
            console.error('[Player] Image load failed:', content.url);
            window.PlayerUI.showError(`Failed to load image: ${content.title}`);

            // Skip to next content
            setTimeout(() => this.playContent(state.currentIndex + 1), 3000);
        };

        img.onload = () => {
            console.log('[Player] Image loaded ✅');
            window.PlayerUI.hideError();

            // Detect orientation and apply class
            const isLandscape = img.naturalWidth > img.naturalHeight;
            img.className = isLandscape ? 'landscape' : 'portrait';
            console.log('[Player] Image orientation:', img.className, `(${img.naturalWidth}x${img.naturalHeight})`);
        };

        display.appendChild(img);
    },

    /**
     * Play video content
     */
    playVideo: async function(content) {
        const state = window.PlayerState;
        const display = document.getElementById('content-display');

        const video = document.createElement('video');

        // Try to get cached blob URL first
        try {
            const blobUrl = await window.PlayerCache.getCachedBlobUrl(content.content_id);
            if (blobUrl) {
                video.src = blobUrl;
                console.log('[Player] Playing from cache ✅');
            } else {
                video.src = content.url;
                console.log('[Player] Streaming (not cached yet)');
            }
        } catch (error) {
            console.error('[Player] Cache error, falling back to streaming:', error);
            video.src = content.url;
        }

        video.autoplay = true;
        // Apply volume setting from Shell (muted = opposite of volumeEnabled)
        video.muted = !state.volumeEnabled;

        console.log('[Player] Video volume:', state.volumeEnabled ? 'Enabled' : 'Muted');

        video.onerror = () => {
            console.error('[Player] Video load failed:', content.url);
            window.PlayerUI.showError(`Failed to load video: ${content.title}`);

            // Skip to next content
            setTimeout(() => this.playContent(state.currentIndex + 1), 3000);
        };

        video.onloadeddata = () => {
            console.log('[Player] Video loaded ✅');
            window.PlayerUI.hideError();

            // Detect orientation and apply class
            const isLandscape = video.videoWidth > video.videoHeight;
            video.className = isLandscape ? 'landscape' : 'portrait';
            console.log('[Player] Video orientation:', video.className, `(${video.videoWidth}x${video.videoHeight})`);
        };

        // Auto-advance when video ends (in case duration is wrong)
        video.onended = () => {
            console.log('[Player] Video ended, advancing...');
            this.playContent(state.currentIndex + 1);
        };

        display.appendChild(video);
    }
};
