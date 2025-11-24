# Console Log Streaming - Implementation Documentation

**Status**: ✅ FULLY OPERATIONAL
**Last Updated**: 2025-01-13
**Version**: player-vite v2025-11-23T18:15:41.476Z

## Overview
 ℹ️ [Models/Segment] Segment model loaded
 ℹ️ [Models/Device] Device model loaded
 [Performance] Page load metrics recorded: Object
 ℹ️ [EventBus] Subscribed to 'connection:online' (namespace: offline-handler)
 ℹ️ [EventBus] Subscribed to 'connection:offline' (namespace: offline-handler)
 ℹ️ [EventBus] Subscribed to 'connection:restored' (namespace: offline-handler)
 ℹ️ [EventBus] Subscribed to 'connection:lost' (namespace: offline-handler)
 ℹ️ [OfflineHandler] Initialized - Online: true
 ℹ️ [I18nService] Service initialized
 ℹ️ [I18nService] Default translations loaded
 ℹ️ [SharedDeviceState] Preference set: player_language = en
 ℹ️ [EventBus] Emitted 'language:changed' (no listeners) Object
 ℹ️ [I18nService] Language changed to: en
 ℹ️ [TemplateProcessor] Service initialized
 ℹ️ [WidgetRenderer] Service initialized
 ℹ️ [PlayerWidgetRenderer] Service initialized
 ℹ️ [EventBus] Subscribed to 'widgets:update'
 ℹ️ [EventBus] Subscribed to 'variables:changed'
 ℹ️ [PlayerScheduleManager] Initializing...
 ℹ️ [PlayerUI] Initializing...
 ℹ️ [WaitingForContent] Initializing...
 ℹ️ [KeyboardHandler] Initialized
 ℹ️ [EventBus] Subscribed to 'fullscreen:enter' (namespace: fullscreen-handler)
 ℹ️ [EventBus] Subscribed to 'fullscreen:exit' (namespace: fullscreen-handler)
 ℹ️ [EventBus] Subscribed to 'fullscreen:toggle' (namespace: fullscreen-handler)
 ℹ️ [FullscreenHandler] Auto-enter disabled for browser (requires user gesture)
 ℹ️ [FullscreenHandler] Initialized - Auto-enter: true
 ℹ️ [ConnectionStatus] Ping interval started: 30000ms
 ℹ️ [ConnectionStatus] Initialized - Initial status: online
 ℹ️ [DisplaySettings] Initialized
 ℹ️ [DisplaySettings] Display: Object
 ℹ️ [DisplaySettings] TV: Object
 ℹ️ [DeviceControls] Initialized
 ℹ️ [DeviceControls] Capabilities: Object
 ℹ️ 🎬 Player-Vite Started
 ℹ️ 📋 Configuration loaded: Object
 ℹ️ 🔍 Initializing app...
 ℹ️ ✅ Containers found in DOM
 ℹ️ 🎨 Rendering activation screen...
 ℹ️ IndexedDB opened successfully
 ℹ️ [DeviceConfig] No config found, returning default
 ℹ️ [ShellActivationScreen] Rendering activation screen... Object
 ℹ️ [ShellActivationScreen] ✅ Activation screen rendered
 ℹ️ 🎮 Initializing UI components...
 ℹ️ [Toast] Initializing SharedToast...
 ℹ️ [Toast] ✅ Container initialized successfully
 ℹ️ [Fullscreen] Initializing Fullscreen Manager
 ℹ️ [Fullscreen] Enter button listener attached
 ℹ️ [Fullscreen] Exit button listener attached
 ℹ️ [Fullscreen] Fullscreen state changed: false
 ℹ️ [Fullscreen] Exiting fullscreen mode
 ℹ️ [Fullscreen] Fullscreen Manager initialized
 ℹ️ [HardReset] Initializing Hard Reset Handler
 ℹ️ [HardReset] Hard reset button listener attached
 ℹ️ [HardReset] Hard Reset Handler initialized
 ℹ️ [ClearCache] ✅ Initialized
 ℹ️ [DeviceInfoPopup] Initializing...
 ℹ️ [DeviceInfoPopup] ✅ Initialized
 ℹ️ 🔄 Initializing version checker...
 ℹ️ [ConnectionStatus] Ping interval started: 30000ms
 ℹ️ [ConnectionLogStorage] ✅ Initialized
 ℹ️ [VersionChecker] Initialized with build: 2025-11-23T17:14:06.020Z
 ℹ️ [VersionChecker] Polling started (every 30s)
 ℹ️ 📊 Initializing connection logging services...
 ℹ️ [ConnectionLogStorage] Added log: server - connected
 ℹ️ [ConnectionLogStorage] ✅ Initialized
 ℹ️ [ConnectionLogger] Upload scheduler started (every 5 minutes)
 ℹ️ [ConnectionLogger] Logged: server - connected (16ms)
 ℹ️ [ConnectionLogStorage] Added log: network - online
 ℹ️ [ConnectionLogger] Logged: network - online 
 ℹ️ [ConnectionLogger] ✅ Initialized
 ℹ️ [NetworkSpeedTest] ✅ Initialized (tests every 1 hour)
 ℹ️ [Main] ✅ Connection logging services initialized
 ℹ️ 🚀 Initializing ShellBootstrap...
 ℹ️ [ShellBootstrap] 🚀 Initializing player...
 ℹ️ [ShellBootstrap] Device state: Object
 ℹ️ [ShellBootstrap] Device active → Starting player context...
 ℹ️ [ShellBootstrap] 🎬 Starting player context...
 ℹ️ [PlayerVideoJS] ✅ Initialized successfully
 ℹ️ [ShellBootstrap] ✅ PlayerVideoJS initialized with video element
 ℹ️ 🔍 Initializing console interceptor...
 ℹ️ [EventBus] Subscribed to 'device:restored' (namespace: ConsoleInterceptor)
 ℹ️ [EventBus] Subscribed to 'device:loaded' (namespace: ConsoleInterceptor)
 ℹ️ [ConsoleInterceptor] Config (v2-faster-flush): Object
 [ConsoleInterceptor] Started
 ℹ️ [ConsoleInterceptor] ✅ Initialized and started Object
 ℹ️ [Main] ✅ Console interceptor initialized
 ℹ️ [ConnectionLogPopup] ✅ Initialized
 ℹ️ [PlayerMediaCache] ✅ IndexedDB initialized
 ℹ️ [ShellBootstrap] ✅ MediaCache initialized
 ℹ️ [PlayerBackgroundAudio] ✅ Initialized
 ℹ️ [ShellBootstrap] ✅ PlayerBackgroundAudio initialized
 ℹ️ [PlayerHLSCache] ✅ IndexedDB initialized
 ℹ️ [ShellBootstrap] ✅ HLS Cache initialized
 ℹ️ [ShellBootstrap] ℹ️ Running on HTTP - Service Worker disabled
 ℹ️ [ShellBootstrap] HLS streaming and caching enabled, offline playback requires HTTPS
 ℹ️ [CommandExecutor] Initializing...
 ℹ️ [CommandExecutor] Registered handler for 'play'
 ℹ️ [CommandExecutor] Registered handler for 'pause'
 ℹ️ [CommandExecutor] Registered handler for 'stop'
 ℹ️ [CommandExecutor] Registered handler for 'next'
 ℹ️ [CommandExecutor] Registered handler for 'previous'
 ℹ️ [CommandExecutor] Registered handler for 'seek'
 ℹ️ [CommandExecutor] Registered handler for 'set_volume'
 ℹ️ [CommandExecutor] Registered handler for 'load_playlist'
 ℹ️ [CommandExecutor] Registered handler for 'reload_playlist'
 ℹ️ [CommandExecutor] Registered handler for 'clear_cache'
 ℹ️ [CommandExecutor] Registered handler for 'reload_page'
 ℹ️ [CommandExecutor] Registered handler for 'clear_storage'
 ℹ️ [CommandExecutor] Registered handler for 'fullscreen'
 ℹ️ [CommandExecutor] Registered handler for 'exit_fullscreen'
 ℹ️ [CommandExecutor] Registered handler for 'get_status'
 ℹ️ [CommandExecutor] Registered handler for 'get_system_info'
 ℹ️ [CommandExecutor] Registered 16 default handlers
 ℹ️ [EventBus] Subscribed to 'command:received'
 ℹ️ [CommandExecutor] ✅ Initialized
 ℹ️ [ShellBootstrap] ✅ CommandExecutor initialized
 ℹ️ [WebSocket] No device token - skipping WebSocket connection (optional feature)
 ℹ️ [ShellBootstrap] ✅ WebSocket connected
 ℹ️ [PlayerPlaylistSync] 🔄 Starting playlist sync...
 ℹ️ [EventBus] Subscribed to 'schedule:changed'
 ℹ️ [PlayerPlaylistSync] 📥 Syncing playlist from backend...
 ℹ️ [ShellBootstrap] ✅ PlaylistSync started
 ℹ️ [PlayerHeartbeat] 💓 Starting heartbeat...
 ℹ️ [PlayerHeartbeat] 💓 Sending heartbeat... Object
 ℹ️ [ShellBootstrap] ✅ Heartbeat started
 [ServiceHelper] PlayerHealthReporter not available
overrideMethod @ installHook.js:1
 ℹ️ [DeviceInfoPopup] Already initialized
 ℹ️ [ShellBootstrap] ✅ DeviceInfoPopup initialized
 ℹ️ [ShellBootstrap] 🎉 All player services initialized
 [SharedAPIClient] ✗ Error (6ms) Object
overrideMethod @ installHook.js:1
 [PlayerScheduleManager] Failed to sync schedules: Object
overrideMethod @ installHook.js:1
 ℹ️ [EventBus] Subscribed to 'device:online'
 ℹ️ [PlayerScheduleManager] Initialized
 ℹ️ [PlayerPlaylistSync] 📊 Sync response: Object
 ℹ️ [WaitingForContent] Hiding waiting screen
 ℹ️ [PlayerPlaylistSync] 📊 Device settings received: Object
 ℹ️ [PlayerVideoJS] 🔊 Volume set to 75%
 ℹ️ [SharedDeviceState] Preference set: screen_rotation = 180
 ℹ️ [DisplaySettings] Applied rotation: 180deg (viewport: 901x766)
 ℹ️ [PlayerPlaylistSync] ✅ Applied rotation: 180deg
 ℹ️ [PlayerBackgroundAudio] No background audio assigned
 ℹ️ [PlayerBackgroundAudio] 🛑 Stopped
 ℹ️ [PlayerPlaylistSync] Version check: Object
 ℹ️ [PlayerPlaylistSync] ✅ Playlist changed! Object
 ℹ️ [PlayerPlaylistSync] 📢 Notifying player about playlist change...
 ℹ️ [EventBus] Emitted 'playlist:changed' (no listeners) Object
 ℹ️ [PlayerVideoJS] Playlist loaded: Object
 ℹ️ [PlayerVideoJS] Playing item: Object
 ℹ️ [PlayerVideoJS] 🌐 Image from network (downloading in background): http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg
 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
 ℹ️ [PlayerVideoJS] 🌐 STREAMING image for 10 seconds
 ℹ️ [PlayerHeartbeat] ✅ Heartbeat sent successfully
 ℹ️ [PlayerMediaCache] 📥 Caching media: http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg
 [PlayerMediaCache] ❌ Failed to cache http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg: Object
overrideMethod @ installHook.js:1
 [PlayerVideoJS] Image background download failed: HTTP 404: Not Found
overrideMethod @ installHook.js:1
 ℹ️ [Fullscreen] Recalculating rotation for normal viewport...
 ℹ️ [Fullscreen] Reloading player for normal viewport size...
 ℹ️ [DisplaySettings] Detected refresh rate: 62
 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
 ℹ️ [PlayerVideoJS] Playing item: Object
 ℹ️ [PlayerVideoJS] 💾 Playing from cache (OFFLINE): http://192.168.5.12:8001/content/videos/2025/11/org_4/e804e41a-b36a-4fcf-bbf3-781f164ec221.mp4
 ℹ️ [PlayerVideoJS] 🔊 Volume: 75%
 ℹ️ [ConnectionLogStorage] Found 8 unsent logs
 ℹ️ [ConnectionLogger] Uploading 8 logs to server...
 ℹ️ [ConnectionLogStorage] Marked 8 logs as sent
 ℹ️ [ConnectionLogger] ✅ Uploaded 8 logs successfully
 [PlayerVideoJS] Failed to play video: Object
overrideMethod @ installHook.js:1
 ℹ️ [PlayerVideoJS] Playing item: Object
 ℹ️ [PlayerVideoJS] 💾 Image from cache (OFFLINE): http://192.168.5.12:8001/content/images/2025/11/org_4/365f134c-0379-48d8-a842-997a3b67be83.jpg
 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
 ℹ️ [PlayerVideoJS] 💾 OFFLINE image for 10 seconds
 ℹ️ [PlayerVideoJS] Ready to play
 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
 ℹ️ [PlayerVideoJS] Playing item: Object
 ℹ️ [PlayerVideoJS] 🌐 Image from network (downloading in background): http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png
 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
 ℹ️ [PlayerVideoJS] 🌐 STREAMING image for 10 seconds
 ℹ️ [PlayerMediaCache] 📥 Caching media: http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png
installHook.js:1 [PlayerMediaCache] ❌ Failed to cache http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png: Object
overrideMethod @ installHook.js:1
installHook.js:1 [PlayerVideoJS] Image background download failed: HTTP 404: Not Found
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [NetworkSpeedTest] 🚀 Starting speed test... (auto)
shared-logger.ts:419 ℹ️ [PlayerHeartbeat] 💓 Sending heartbeat... Object
shared-logger.ts:419 ℹ️ [ConnectionStatus] Ping interval started: 30000ms
shared-logger.ts:419 ℹ️ [ConnectionLogStorage] Added log: server - connected
shared-logger.ts:419 ℹ️ [PlayerHeartbeat] ✅ Heartbeat sent successfully
shared-logger.ts:419 ℹ️ [ConnectionLogger] Logged: server - connected (17ms)
installHook.js:1 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 Image from cache (OFFLINE): http://192.168.5.12:8001/content/images/2025/11/org_4/a313c2a7-c96f-40c1-8629-4e2b744a0e60.gif
shared-logger.ts:419 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 OFFLINE image for 10 seconds
shared-logger.ts:419 ℹ️ [NetworkSpeedTest] ✅ Test completed in 5852ms: Download: 73.22 Mbps, Upload: 83.20 Mbps, Latency: 10ms
shared-logger.ts:419 ℹ️ [ConnectionLogStorage] Added log: speed_test - tested
shared-logger.ts:419 ℹ️ [ConnectionLogger] Logged: speed_test - tested (10ms)
installHook.js:1 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🌐 Image from network (downloading in background): http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg
shared-logger.ts:419 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🌐 STREAMING image for 10 seconds
shared-logger.ts:419 ℹ️ [PlayerMediaCache] 📥 Caching media: http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg
installHook.js:1 [PlayerMediaCache] ❌ Failed to cache http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg: Object
overrideMethod @ installHook.js:1
installHook.js:1 [PlayerVideoJS] Image background download failed: HTTP 404: Not Found
overrideMethod @ installHook.js:1
installHook.js:1 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 Playing from cache (OFFLINE): http://192.168.5.12:8001/content/videos/2025/11/org_4/e804e41a-b36a-4fcf-bbf3-781f164ec221.mp4
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🔊 Volume: 75%
installHook.js:1 [PlayerVideoJS] Failed to play video: Object
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 Image from cache (OFFLINE): http://192.168.5.12:8001/content/images/2025/11/org_4/365f134c-0379-48d8-a842-997a3b67be83.jpg
shared-logger.ts:419 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 OFFLINE image for 10 seconds
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Ready to play
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] 📥 Syncing playlist from backend...
shared-logger.ts:419 ℹ️ [PlayerHeartbeat] 💓 Sending heartbeat... Object
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] 📊 Sync response: Object
shared-logger.ts:419 ℹ️ [WaitingForContent] Hiding waiting screen
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] 📊 Device settings received: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🔊 Volume set to 75%
shared-logger.ts:419 ℹ️ [SharedDeviceState] Preference set: screen_rotation = 180
shared-logger.ts:419 ℹ️ [DisplaySettings] Applied rotation: 180deg (viewport: 901x766)
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] ✅ Applied rotation: 180deg
shared-logger.ts:419 ℹ️ [PlayerBackgroundAudio] No background audio assigned
shared-logger.ts:419 ℹ️ [PlayerBackgroundAudio] 🛑 Stopped
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] Version check: Object
shared-logger.ts:419 ℹ️ [PlayerPlaylistSync] No playlist changes detected
shared-logger.ts:419 ℹ️ [PlayerHeartbeat] ✅ Heartbeat sent successfully
shared-logger.ts:419 ℹ️ [ConnectionStatus] Ping interval started: 30000ms
shared-logger.ts:419 ℹ️ [ConnectionLogStorage] Added log: server - connected
shared-logger.ts:419 ℹ️ [ConnectionLogger] Logged: server - connected (7ms)
installHook.js:1 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
(anonymous) @ shared-logger.ts:402
(anonymous) @ player-playback-logger.ts:122
(anonymous) @ index-DGQDmUe4.js:1
d @ index-DGQDmUe4.js:1
logPlaybackEnd @ player-playback-logger.ts:120
(anonymous) @ player-videojs.ts:425
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🌐 Image from network (downloading in background): http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png
shared-logger.ts:419 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 🌐 STREAMING image for 10 seconds
shared-logger.ts:419 ℹ️ [PlayerMediaCache] 📥 Caching media: http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png
installHook.js:1 [PlayerMediaCache] ❌ Failed to cache http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png: Object
overrideMethod @ installHook.js:1
logErrorWithGroup @ shared-logger.ts:469
(anonymous) @ shared-logger.ts:399
(anonymous) @ player-media-cache.ts:107
o @ index-DGQDmUe4.js:1
installHook.js:1 [PlayerVideoJS] Image background download failed: HTTP 404: Not Found
overrideMethod @ installHook.js:1
(anonymous) @ shared-logger.ts:402
(anonymous) @ player-videojs.ts:401
installHook.js:1 [PlaybackLogger] No active playback log to end
overrideMethod @ installHook.js:1
shared-logger.ts:419 ℹ️ [PlayerVideoJS] Playing item: Object
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 Image from cache (OFFLINE): http://192.168.5.12:8001/content/images/2025/11/org_4/a313c2a7-c96f-40c1-8629-4e2b744a0e60.gif
shared-logger.ts:419 ℹ️ [PlaybackLogger] No device token - skipping playback logging (optional feature)
shared-logger.ts:419 ℹ️ [PlayerVideoJS] 💾 OFFLINE image for 10 seconds
