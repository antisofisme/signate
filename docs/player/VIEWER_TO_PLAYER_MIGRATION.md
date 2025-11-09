# Viewer to Player-Flutter Migration Plan

**Date**: 2025-11-02
**Status**: 📋 Planning Phase
**Strategy**: Gradual Migration (Opsi A)

---

## 📊 Viewer Audit Summary

### Current Viewer (HTML/JS)
- **Location**: `viewer/` (running on port 8080)
- **Technology**: Vanilla JavaScript (ES6+), HLS.js, WebSocket
- **Total Code**: ~6,128 lines of JavaScript
  - Player modules: ~2,126 lines (10 files)
  - Shared modules: ~4,002 lines (9 files)
  - Shell integration: WebOS-specific code
- **Production Status**: ✅ **RUNNING** (WebOS TV, Browser, Monitor)

### Core Features Identified

| Feature | Files | Lines | Priority | Complexity |
|---------|-------|-------|----------|------------|
| **Activation System** | shell/activation.js | ~500 | 🔴 HIGH | Medium |
| **HLS Player** | player/hls-player.js, playback.js | ~800 | 🔴 HIGH | High |
| **API Client** | shared/api-client.js, player/api.js | ~600 | 🔴 HIGH | Low |
| **Cache Manager** | shared/cache-manager.js, player/cache.js | ~700 | 🟡 MEDIUM | Medium |
| **WebSocket** | shared/websocket-client.js, player/websocket-integration.js | ~400 | 🟡 MEDIUM | Medium |
| **Offline Detection** | shared/offline-detector.js | ~200 | 🟡 MEDIUM | Low |
| **Analytics** | shared/analytics-tracker.js | ~300 | 🟢 LOW | Low |
| **Language Manager** | shared/language-manager.js | ~200 | 🟢 LOW | Low |
| **Quality Selector** | player/quality-selector.js | ~300 | 🟢 LOW | Medium |
| **UI Components** | player/ui.js | ~500 | 🟡 MEDIUM | Low |

---

## 🎯 Migration Strategy: Gradual (Recommended)

### Phase 1: Foundation (Week 1-2) ✅ DONE
- ✅ Create player-flutter project scaffold
- ✅ Setup folder structure (flat clean architecture)
- ✅ Configure dependencies (Riverpod, Dio, SQLite, Video Player)
- ✅ Create core infrastructure (API client, Database, Config)

### Phase 2: Core Features (Week 3-4) 🔄 NEXT
**Priority**: Activation + API Communication

#### 2.1 Activation Feature (FLAT ARCHITECTURE)
**Migrate from**: `viewer/js/shell/activation.js`
**Migrate to**: `player-flutter/lib/features/activation/`

**Structure** (berdasarkan README):
```
features/activation/
├── models/          # Device, ActivationCode, ActivationStatus
├── services/        # ActivationService (API calls)
├── providers/       # Riverpod providers
└── screens/         # ActivationScreen, WaitingScreen
```

**Tasks**:
1. ✅ Create activation models
   - `lib/features/activation/models/device.dart`
   - `lib/features/activation/models/activation_code.dart`
   - `lib/features/activation/models/activation_status.dart`

2. ✅ Create activation service (API calls)
   - `lib/features/activation/services/activation_service.dart`
   - Methods:
     - `Future<ActivationCode> generateCode()`
     - `Future<Device> activateDevice(String code)`
     - `Stream<ActivationStatus> pollActivationStatus(String code)`

3. ✅ Create Riverpod providers
   - `lib/features/activation/providers/activation_provider.dart`
   - `lib/features/activation/providers/device_provider.dart`

4. ✅ Create activation UI screens
   - `lib/features/activation/screens/activation_screen.dart` (6-digit code input)
   - `lib/features/activation/screens/waiting_screen.dart` (waiting for approval)

**Mapping**:
```javascript
// viewer/js/shell/activation.js
window.ShellActivation = {
  generateActivationCode: async () => { ... },
  pollActivationStatus: async (code) => { ... },
  activateDevice: async (code) => { ... }
}
```
↓ Migrate to ↓
```dart
// player-flutter/lib/features/activation/services/activation_service.dart
class ActivationService {
  final ApiClient _api;

  Future<ActivationCode> generateCode();
  Future<Device> activateDevice(String code);
  Stream<ActivationStatus> pollActivationStatus(String code);
}

// player-flutter/lib/features/activation/providers/activation_provider.dart
final activationProvider = StateNotifierProvider<ActivationNotifier, ActivationState>((ref) {
  return ActivationNotifier(ref.read(activationServiceProvider));
});
```

#### 2.2 API Client Enhancement
**Migrate from**: `viewer/js/shared/api-client.js`
**Enhance**: `player-flutter/lib/core/network/api_client.dart`

**Tasks**:
1. Add response unwrapping (detect `{success, data, meta}` format)
2. Add request/response logging
3. Add retry logic with exponential backoff
4. Add network error handling
5. Add token management (if auth needed)

---

### Phase 3: Player & Playback (Week 5-6)
**Priority**: Video playback with HLS support

#### 3.1 HLS Player Feature (FLAT ARCHITECTURE)
**Migrate from**: `viewer/js/player/hls-player.js`, `playback.js`
**Migrate to**: `player-flutter/lib/features/player/`

**Structure** (berdasarkan README):
```
features/player/
├── models/          # Playlist, Content, Segment, QualityLevel
├── services/        # PlaylistService, PlayerService, HLSService
├── providers/       # PlayerProvider, PlaylistProvider
└── screens/         # PlayerScreen
```

**Tasks**:
1. ✅ Create player models
   - `lib/features/player/models/playlist.dart`
   - `lib/features/player/models/content.dart`
   - `lib/features/player/models/segment.dart`
   - `lib/features/player/models/quality_level.dart`

2. ✅ Integrate HLS video player
   - Package: `video_player` + `flutter_vlc_player` (fallback)
   - Setup HLS.js for web platform
   - `lib/features/player/services/hls_service.dart`

3. ✅ Create playlist & player services
   - `lib/features/player/services/playlist_service.dart`
     - `Future<Playlist> fetchPlaylist(String deviceId)`
   - `lib/features/player/services/player_service.dart`
     - `Future<void> playContent(Content content)`
     - `void pause()`, `void resume()`, `void skip()`

4. ✅ Create Riverpod providers
   - `lib/features/player/providers/playlist_provider.dart`
   - `lib/features/player/providers/player_provider.dart`

5. ✅ Create player UI
   - `lib/features/player/screens/player_screen.dart` (full-screen video)
   - Loading states, error handling
   - Auto-rotate playlist

6. ✅ Implement quality selection
   - Auto-detect based on bandwidth
   - Manual override via UI

**Key Features to Migrate**:
- HLS adaptive bitrate streaming
- Buffer management (30s buffer, 60s max)
- Quality auto-switching
- Error retry logic (3 retries with exponential backoff)
- Analytics tracking (quality changes, buffering events)

---

### Phase 4: Offline & Sync (Week 7-8)
**Priority**: Offline playback & background sync

#### 4.1 Sync & Cache Feature (FLAT ARCHITECTURE)
**Migrate from**: `viewer/js/shared/cache-manager.js`, `player/cache.js`
**Migrate to**: `player-flutter/lib/features/sync/`

**Structure** (berdasarkan README):
```
features/sync/
├── models/          # SyncStatus, DownloadProgress
├── services/        # SyncService, DownloadService, HeartbeatService
├── providers/       # SyncProvider, DownloadProvider
└── workers/         # BackgroundSyncWorker, HeartbeatWorker
```

**Tasks**:
1. ✅ Create sync models
   - `lib/features/sync/models/sync_status.dart`
   - `lib/features/sync/models/download_progress.dart`

2. ✅ Create download service (SQLite storage)
   - `lib/features/sync/services/download_service.dart`
   - Sequential download (1 content at a time) ⚠️ PENTING!
   - Store HLS segments to SQLite (use existing schema from `core/database/database.dart`)
   - Track download progress per content

3. ✅ Create sync service
   - `lib/features/sync/services/sync_service.dart`
   - Check for playlist updates
   - Sync new content
   - Cleanup old content

4. ✅ Create heartbeat service
   - `lib/features/sync/services/heartbeat_service.dart`
   - Send heartbeat to backend every 30s
   - Update last_seen timestamp

5. ✅ Create background workers
   - `lib/features/sync/workers/background_sync_worker.dart`
     - Use WorkManager
     - Check updates every 15 minutes
   - `lib/features/sync/workers/heartbeat_worker.dart`
     - Send heartbeat every 30 seconds

6. ✅ Create Riverpod providers
   - `lib/features/sync/providers/sync_provider.dart`
   - `lib/features/sync/providers/download_provider.dart`

#### 4.2 Offline Detection & Connectivity
**Migrate from**: `viewer/js/shared/offline-detector.js`
**Migrate to**: `player-flutter/lib/core/` (shared service)

**Files to create**:
- `lib/core/services/connectivity_service.dart`
- `lib/core/providers/connectivity_provider.dart`

**Tasks**:
1. ✅ Monitor network connectivity (use `connectivity_plus` package)
2. ✅ Switch between online/offline mode
3. ✅ Queue API calls when offline
4. ✅ Auto-sync when online again
5. ✅ Provide connectivity state via Riverpod provider

**Note**: Ini shared service di `core/` karena dipakai oleh semua features (activation, player, sync)

---

### Phase 5: Advanced Features (Week 9-10)
**Priority**: WebSocket, Analytics, Language

#### 5.1 WebSocket Integration (CORE SERVICE)
**Migrate from**: `viewer/js/shared/websocket-client.js`, `player/websocket-integration.js`
**Migrate to**: `player-flutter/lib/core/` (shared service)

**Files to create**:
- `lib/core/services/websocket_service.dart`
- `lib/core/providers/websocket_provider.dart`

**Tasks**:
1. ✅ Setup WebSocket connection to backend
2. ✅ Handle real-time commands (skip, pause, reload)
3. ✅ Reconnection logic with exponential backoff
4. ✅ Heartbeat mechanism
5. ✅ Provide connection state via Riverpod provider

#### 5.2 Analytics Tracking (CORE SERVICE)
**Migrate from**: `viewer/js/shared/analytics-tracker.js`
**Migrate to**: `player-flutter/lib/core/` (shared service)

**Files to create**:
- `lib/core/services/analytics_service.dart`

**Tasks**:
1. ✅ Track playback events (play, pause, skip, error)
2. ✅ Track quality changes
3. ✅ Track buffering events
4. ✅ Send analytics to backend
5. ✅ Batch analytics for efficiency

#### 5.3 Language Manager (CORE SERVICE)
**Migrate from**: `viewer/js/shared/language-manager.js`
**Migrate to**: `player-flutter/lib/core/` (shared service)

**Files to create**:
- `lib/core/services/i18n_service.dart`
- `lib/core/l10n/` (translation files)
  - `lib/core/l10n/id.json` (Indonesian)
  - `lib/core/l10n/en.json` (English)

**Tasks**:
1. ✅ Support ID/EN languages
2. ✅ Load translations from JSON files
3. ✅ Switch language dynamically
4. ✅ Save language preference to SharedPreferences

**Note**: Semua ini shared services di `core/` karena dipakai across all features

---

### Phase 6: Testing & Deployment (Week 11-12)
**Priority**: Multi-platform testing

#### 6.1 Platform Testing
**Platforms**:
1. ✅ Android (native app)
2. ✅ iOS (native app)
3. ✅ Web (browser)
4. ⚠️ WebOS (requires special SDK)

**Tasks**:
1. Test on each platform
2. Fix platform-specific issues
3. Performance optimization
4. Memory leak checks

#### 6.2 Deployment
**Android/iOS**:
- Build APK/IPA
- Distribute via internal channels

**Web**:
- Build for web: `flutter build web`
- Deploy to port 8080 (replace viewer)

**WebOS**:
- Package as IPK (WebOS app)
- Test on LG TV

---

## 🔄 Coexistence Strategy

During migration, **both systems will run in parallel**:

### Option 1: Port-based (Recommended)
- **Viewer (HTML/JS)**: Port 8080 (production)
- **Player (Flutter Web)**: Port 8081 (staging/testing)
- Devices can switch between ports via config
- Gradual rollout: Test devices use 8081, production uses 8080

### Option 2: Path-based
- **Viewer (HTML/JS)**: http://server:8080/viewer/
- **Player (Flutter Web)**: http://server:8080/player/
- Nginx routes based on path

---

## 📋 Migration Checklist

### ✅ Completed
- [x] Project scaffold created
- [x] Folder structure defined
- [x] Dependencies configured
- [x] Core infrastructure (API client, Database, Config)
- [x] Migration plan documented

### 🔄 In Progress
- [ ] Activation feature implementation
- [ ] API client enhancement

### ⏳ Pending
- [ ] HLS player implementation
- [ ] Cache & offline sync
- [ ] WebSocket integration
- [ ] Analytics tracking
- [ ] Language management
- [ ] Platform testing
- [ ] Deployment

---

## 🚨 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| HLS playback issues on Flutter Web | High | Medium | Test early, use multiple player packages |
| WebOS compatibility | High | High | Keep HTML/JS viewer as fallback |
| Performance on low-end devices | Medium | Medium | Optimize, test on real devices |
| SQLite storage limits | Medium | Low | Implement auto-cleanup, limit cache size |
| Background sync battery drain | Medium | Medium | Use WorkManager, optimize intervals |

---

## 📦 Deliverables

### Phase 2 Deliverables (Next):
1. ✅ Activation feature fully working
2. ✅ Device can register with 6-digit code
3. ✅ Device waits for admin approval
4. ✅ API communication working
5. ✅ State management with Riverpod
6. ✅ UI matching design

### Phase 3 Deliverables:
1. ✅ HLS video playback working
2. ✅ Adaptive quality switching
3. ✅ Playlist support
4. ✅ Error handling & retry

### Phase 4 Deliverables:
1. ✅ Offline playback from cache
2. ✅ Background content sync
3. ✅ Sequential download (1 by 1)
4. ✅ Heartbeat & update check

---

## 🎯 Success Criteria

**Migration is successful when**:
1. ✅ All viewer features replicated in player-flutter
2. ✅ Performance equal or better than HTML/JS viewer
3. ✅ Works on all target platforms (Android, iOS, Web, WebOS)
4. ✅ No production downtime during migration
5. ✅ Admin can switch devices between viewer/player
6. ✅ Offline playback working reliably
7. ✅ Battery consumption acceptable

---

## 🔄 Rollback Plan

If migration fails:
1. Keep viewer (HTML/JS) running on port 8080
2. Mark player-flutter as "beta"
3. Allow selective device testing
4. Full rollback: Revert to viewer only

---

## 📅 Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Foundation | Week 1-2 | ✅ DONE |
| Phase 2: Core Features | Week 3-4 | 🔄 NEXT |
| Phase 3: Player & Playback | Week 5-6 | ⏳ Pending |
| Phase 4: Offline & Sync | Week 7-8 | ⏳ Pending |
| Phase 5: Advanced Features | Week 9-10 | ⏳ Pending |
| Phase 6: Testing & Deployment | Week 11-12 | ⏳ Pending |

**Total Estimated Time**: 12 weeks (3 months)

---

## 🚀 Next Steps

1. **Start Phase 2**: Implement activation feature in player-flutter
2. **Setup development workflow**: Hot reload, debugging
3. **Create first screens**: Activation page, waiting screen
4. **Test on Android emulator**: Verify basic flow
5. **Parallel testing**: Keep viewer running for production

**Ready to begin Phase 2?** Let's start with activation feature! 🎯
