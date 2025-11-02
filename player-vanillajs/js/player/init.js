/**
 * Player Initialization Module
 * Main entry point for player iframe - orchestrates initialization
 */

window.PlayerInit = {
    /**
     * Initialize player
     */
    init: async function() {
        console.log('='.repeat(60));
        console.log('[Player/Init] Content Player Starting...');
        console.log('='.repeat(60));

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
                console.error('[Player/Init] ❌ No deviceId provided in URL');
                window.PlayerUI.showError('⚠️ Configuration Error\n\nNo device ID provided');
                return;
            }

            // 3. Initialize OLD PlayerState (backward compatibility)
            // Some legacy code still uses window.PlayerState
            if (window.PlayerState) {
                window.PlayerState.deviceId = deviceId;
                window.PlayerState.API_BASE_URL = window.Config.API_BASE_URL;
                console.log('[Player/Init] ✅ OLD PlayerState initialized (backward compatibility)');
            }

            // 4. Setup volume (mute if disabled by admin)
            const initialVolume = volumeEnabled ? 1.0 : 0.0;
            if (window.playerState) {
                window.playerState.setVolume(initialVolume);
                console.log('[Player/Init] Volume set:', volumeEnabled ? 'Enabled (1.0)' : 'Muted (0.0)');
            }

            // 5. Setup event listeners for reactive updates (Phase 3)
            this.setupEventListeners();

            // 6. Load playlist from API
            console.log('[Player/Init] 🔄 Loading playlist for device:', deviceId);
            await window.PlayerAPI.loadPlaylist();

            // 7. Setup periodic playlist check (check for updates every 60 seconds)
            setInterval(() => {
                if (window.PlayerAPI && window.PlayerAPI.checkPlaylistUpdate) {
                    window.PlayerAPI.checkPlaylistUpdate();
                }
            }, 60000);

            // 8. Setup keyboard shortcuts (debug mode)
            this.setupKeyboardShortcuts();

            console.log('[Player/Init] ✅ Player initialized successfully');
            console.log('='.repeat(60));

        } catch (error) {
            console.error('[Player/Init] ❌ Initialization failed:', error);
            window.PlayerUI.showError(`⚠️ Initialization Error\n\n${error.message}\n\nReloading in 10 seconds...`);

            // Retry initialization after 10 seconds
            setTimeout(() => {
                window.location.reload();
            }, 10000);
        }
    },

    /**
     * Setup EventBus listeners for reactive state updates (Phase 3)
     */
    setupEventListeners: function() {
        if (!window.eventBus) {
            console.warn('[Player/Init] EventBus not available - skipping reactive listeners');
            return;
        }

        // Listen for playlist loaded
        window.eventBus.on('playlist:loaded', (data) => {
            console.log('[Player/Init] 📋 Playlist loaded event:', {
                contentCount: data.contentCount,
                totalDuration: data.totalDuration
            });
        });

        // Listen for content changes
        window.eventBus.on('player:index-changed', (data) => {
            console.log('[Player/Init] 🎬 Content changed:', {
                index: data.index,
                total: data.total,
                content: data.content ? data.content.name : 'unknown'
            });
        });

        // Listen for playback state changes
        window.eventBus.on('player:playing', (data) => {
            console.log('[Player/Init] ▶️ Playing:', data.content ? data.content.name : 'unknown');
        });

        window.eventBus.on('player:paused', (data) => {
            console.log('[Player/Init] ⏸️ Paused:', data.content ? data.content.name : 'unknown');
        });

        // Listen for content ended (auto advance)
        window.eventBus.on('player:content-ended', (data) => {
            console.log('[Player/Init] ✅ Content ended, advancing to next...');
        });

        // Listen for download progress
        window.eventBus.on('player:download-progress', (data) => {
            console.log('[Player/Init] 📥 Download progress:', `${data.progress}%`);
        });

        console.log('[Player/Init] ✅ EventBus listeners registered');
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

            const playlist = window.playerState ? window.playerState.getPlaylist() : null;

            switch(e.key) {
                case 'ArrowRight':
                case 'n':
                    // Next content
                    if (window.playerState) {
                        console.log('[Player/Init] ⏭️ Keyboard: Next');
                        window.playerState.playNext();
                        const content = window.playerState.getCurrentContent();
                        if (content && window.PlayerPlayback) {
                            window.PlayerPlayback.playContent(window.playerState.getCurrentIndex());
                        }
                    }
                    e.preventDefault();
                    break;

                case 'ArrowLeft':
                case 'p':
                    // Previous content
                    if (window.playerState) {
                        console.log('[Player/Init] ⏮️ Keyboard: Previous');
                        window.playerState.playPrevious();
                        const content = window.playerState.getCurrentContent();
                        if (content && window.PlayerPlayback) {
                            window.PlayerPlayback.playContent(window.playerState.getCurrentIndex());
                        }
                    }
                    e.preventDefault();
                    break;

                case 'r':
                    // Reload playlist
                    console.log('[Player/Init] 🔄 Keyboard: Reload playlist');
                    if (window.PlayerAPI) {
                        window.PlayerAPI.loadPlaylist();
                    }
                    e.preventDefault();
                    break;

                case 'i':
                    // Show info
                    console.log('[Player/Init] 📊 Keyboard: Toggle debug info');
                    const debugInfo = document.getElementById('player-info');
                    if (debugInfo) {
                        debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
                    }
                    e.preventDefault();
                    break;

                case 'd':
                    // Dump state
                    console.log('[Player/Init] 🔍 Keyboard: Dump state');
                    if (window.playerState) {
                        console.log('Player State:', {
                            playlist: window.playerState.getPlaylist(),
                            currentIndex: window.playerState.getCurrentIndex(),
                            currentContent: window.playerState.getCurrentContent(),
                            isPlaying: window.playerState.isPlaying(),
                            volume: window.playerState.getVolume(),
                            downloadedIds: window.playerState.getDownloadedContentIds(),
                            downloadProgress: window.playerState.getDownloadProgress()
                        });
                    }
                    if (window.PlayerState) {
                        console.log('OLD PlayerState:', window.PlayerState);
                    }
                    e.preventDefault();
                    break;
            }
        });

        console.log('[Player/Init] ⌨️ Keyboard shortcuts enabled (debug mode):');
        console.log('  → / n : Next content');
        console.log('  ← / p : Previous content');
        console.log('  r     : Reload playlist');
        console.log('  i     : Toggle debug info');
        console.log('  d     : Dump state to console');
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
