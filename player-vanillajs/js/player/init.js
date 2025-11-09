/**
 * Player Initialization Module
 * Main entry point for player iframe - orchestrates initialization
 */

window.PlayerInit = {
    // Store unsubscribe functions for cleanup
    eventUnsubscribers: [],

    /**
     * Initialize player
     */
    init: async function() {
        SharedLogger.log('='.repeat(60));
        SharedLogger.log('[Player/Init] Content Player Starting...');
        SharedLogger.log('='.repeat(60));

        try {
            // 1. Parse URL parameters (passed from Shell)
            const urlParams = new URLSearchParams(window.location.search);
            const deviceId = urlParams.get('deviceId');
            const volumeEnabled = urlParams.get('volume') === 'true';

            console.log('[Player/Init] URL Params:', {
                deviceId: deviceId,
                volumeEnabled: volumeEnabled
            });

            // 2. Validate deviceId
            if (!deviceId) {
                SharedLogger.error('[Player/Init] ❌ No deviceId provided in URL');
                window.PlayerUI.showError('⚠️ Configuration Error\n\nNo device ID provided');
                return;
            }

            // 3. Initialize OLD PlayerState (backward compatibility)
            // Some legacy code still uses window.PlayerState
            if (window.PlayerState) {
                window.PlayerState.deviceId = deviceId;
                window.PlayerState.API_BASE_URL = window.Config.API_BASE_URL;
                SharedLogger.log('[Player/Init] ✅ OLD PlayerState initialized (backward compatibility)');
            }

            // 4. Setup volume (mute if disabled by admin)
            const initialVolume = volumeEnabled ? 1.0 : 0.0;
            if (window.PlayerState) {
                window.PlayerState.setVolume(initialVolume);
                SharedLogger.log('[Player/Init] Volume set:', volumeEnabled ? 'Enabled (1.0)' : 'Muted (0.0)');
            }

            // 5. Setup event listeners for reactive updates (Phase 3)
            this.setupEventListeners();

            // 6. Load playlist from API
            SharedLogger.log('[Player/Init] 🔄 Loading playlist for device:', deviceId);
            await window.PlayerAPI.loadPlaylist();

            // 7. Setup periodic playlist check (check for updates every 60 seconds)
            setInterval(() => {
                if (window.PlayerAPI && window.PlayerAPI.checkPlaylistUpdate) {
                    window.PlayerAPI.checkPlaylistUpdate();
                }
            }, window.SharedENV?.PLAYLIST_CHECK_INTERVAL || 60000);

            // 8. Setup keyboard shortcuts (debug mode)
            this.setupKeyboardShortcuts();

            SharedLogger.log('[Player/Init] ✅ Player initialized successfully');
            SharedLogger.log('='.repeat(60));

        } catch (error) {
            SharedLogger.error('[Player/Init] ❌ Initialization failed:', error);
            window.PlayerUI.showError(`⚠️ Initialization Error\n\n${error.message}\n\nReloading in 10 seconds...`);

            // Retry initialization after configured interval
            setTimeout(() => {
                window.location.reload();
            }, window.SharedENV?.RETRY_INTERVAL || 10000);
        }
    },

    /**
     * Setup EventBus listeners for reactive state updates (Phase 3)
     * ✅ MEMORY LEAK FIX: Store unsubscribe functions for cleanup
     */
    setupEventListeners: function() {
        if (!window.eventBus) {
            SharedLogger.warn('[Player/Init] EventBus not available - skipping reactive listeners');
            return;
        }

        // Listen for playlist loaded
        // ✅ Store unsubscribe function returned by .on()
        const unsubPlaylistLoaded = window.eventBus.on('playlist:loaded', (data) => {
            console.log('[Player/Init] 📋 Playlist loaded event:', {
                contentCount: data.contentCount,
                totalDuration: data.totalDuration
            });
        });
        this.eventUnsubscribers.push(unsubPlaylistLoaded);

        // Listen for content changes
        const unsubIndexChanged = window.eventBus.on('player:index-changed', (data) => {
            console.log('[Player/Init] 🎬 Content changed:', {
                index: data.index,
                total: data.total,
                content: data.content ? data.content.name : 'unknown'
            });
        });
        this.eventUnsubscribers.push(unsubIndexChanged);

        // Listen for playback state changes
        const unsubPlaying = window.eventBus.on('player:playing', (data) => {
            SharedLogger.log('[Player/Init] ▶️ Playing:', data.content ? data.content.name : 'unknown');
        });
        this.eventUnsubscribers.push(unsubPlaying);

        const unsubPaused = window.eventBus.on('player:paused', (data) => {
            SharedLogger.log('[Player/Init] ⏸️ Paused:', data.content ? data.content.name : 'unknown');
        });
        this.eventUnsubscribers.push(unsubPaused);

        // Listen for content ended (auto advance)
        const unsubContentEnded = window.eventBus.on('player:content-ended', (data) => {
            SharedLogger.log('[Player/Init] ✅ Content ended, advancing to next...');
        });
        this.eventUnsubscribers.push(unsubContentEnded);

        // Listen for download progress
        const unsubDownloadProgress = window.eventBus.on('player:download-progress', (data) => {
            SharedLogger.log('[Player/Init] 📥 Download progress:', `${data.progress}%`);
        });
        this.eventUnsubscribers.push(unsubDownloadProgress);

        SharedLogger.log('[Player/Init] ✅ EventBus listeners registered:', this.eventUnsubscribers.length);
    },

    /**
     * Cleanup all event listeners
     * ✅ MEMORY LEAK FIX: Call all unsubscribe functions
     */
    cleanup: function() {
        SharedLogger.log('[Player/Init] 🧹 Cleaning up event listeners...');

        // Call all unsubscribe functions
        this.eventUnsubscribers.forEach(unsub => {
            if (typeof unsub === 'function') {
                unsub();
            }
        });

        // Clear array
        this.eventUnsubscribers = [];

        SharedLogger.log('[Player/Init] ✅ Event listeners cleaned up');
    },

    /**
     * Setup keyboard shortcuts for debugging
     */
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', (e) => {
            // Only in debug mode or localhost
            if (!window.location.hostname.includes('localhost') &&
                !window.location.hostname.includes('127.0.0.1')) {
                return;
            }

            const playlist = window.PlayerState ? window.PlayerState.getPlaylist() : null;

            switch(e.key) {
                case 'ArrowRight':
                case 'n':
                    // Next content
                    if (window.PlayerState) {
                        SharedLogger.log('[Player/Init] ⏭️ Keyboard: Next');
                        window.PlayerState.playNext();
                        const content = window.PlayerState.getCurrentContent();
                        if (content && window.PlayerPlayback) {
                            window.PlayerPlayback.playContent(window.PlayerState.getCurrentIndex());
                        }
                    }
                    e.preventDefault();
                    break;

                case 'ArrowLeft':
                case 'p':
                    // Previous content
                    if (window.PlayerState) {
                        SharedLogger.log('[Player/Init] ⏮️ Keyboard: Previous');
                        window.PlayerState.playPrevious();
                        const content = window.PlayerState.getCurrentContent();
                        if (content && window.PlayerPlayback) {
                            window.PlayerPlayback.playContent(window.PlayerState.getCurrentIndex());
                        }
                    }
                    e.preventDefault();
                    break;

                case 'r':
                    // Reload playlist
                    SharedLogger.log('[Player/Init] 🔄 Keyboard: Reload playlist');
                    if (window.PlayerAPI) {
                        window.PlayerAPI.loadPlaylist();
                    }
                    e.preventDefault();
                    break;

                case 'i':
                    // Show info
                    SharedLogger.log('[Player/Init] 📊 Keyboard: Toggle debug info');
                    const debugInfo = document.getElementById('player-info');
                    if (debugInfo) {
                        debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
                    }
                    e.preventDefault();
                    break;

                case 'd':
                    // Dump state
                    SharedLogger.log('[Player/Init] 🔍 Keyboard: Dump state');
                    if (window.PlayerState) {
                        console.log('Player State:', {
                            playlist: window.PlayerState.getPlaylist(),
                            currentIndex: window.PlayerState.getCurrentIndex(),
                            currentContent: window.PlayerState.getCurrentContent(),
                            isPlaying: window.PlayerState.isPlaying(),
                            volume: window.PlayerState.getVolume(),
                            downloadedIds: window.PlayerState.getDownloadedContentIds(),
                            downloadProgress: window.PlayerState.getDownloadProgress()
                        });
                    }
                    if (window.PlayerState) {
                        SharedLogger.log('OLD PlayerState:', window.PlayerState);
                    }
                    e.preventDefault();
                    break;
            }
        });

        SharedLogger.log('[Player/Init] ⌨️ Keyboard shortcuts enabled (debug mode):');
        SharedLogger.log('  → / n : Next content');
        SharedLogger.log('  ← / p : Previous content');
        SharedLogger.log('  r     : Reload playlist');
        SharedLogger.log('  i     : Toggle debug info');
        SharedLogger.log('  d     : Dump state to console');
    }
};

// Auto-initialize when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.PlayerInit.init();
    });
} else {
    // DOM already loaded
    window.PlayerInit.init();
}

// ✅ MEMORY LEAK FIX: Cleanup listeners before page unload
window.addEventListener('beforeunload', () => {
    if (window.PlayerInit && window.PlayerInit.cleanup) {
        window.PlayerInit.cleanup();
    }
});
