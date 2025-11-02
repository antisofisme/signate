# Player VanillaJS - Digital Signage Display

## Architecture

Offline-first HLS player untuk digital signage dengan **Clean Architecture (Flat)** menggunakan **Vanilla JavaScript**.

**Platforms:**
- Web (Modern browsers)
- WebOS TV (LG Smart TV)
- Chromium-based displays

## Tech Stack Decisions

### ✅ Framework & Platform
- **Vanilla JavaScript ES6+** (no framework)
- **HLS.js** (HTTP Live Streaming)
- **Progressive Web App (PWA)**

**Kenapa Vanilla JS?**
- ✅ Lightweight - No framework overhead (~50KB total)
- ✅ Fast startup - No hydration/initialization
- ✅ Universal compatibility - Works everywhere
- ✅ Long-term stability - No framework breaking changes
- ✅ Direct control - No abstraction layers

### ✅ Architecture
- **Flat Clean Architecture** (bukan deep layers)
- **Feature-based** organization (activation/, player/, sync/)
- Max 4 levels depth

### ✅ State Management
- **EventBus Pattern** (Pub/Sub)

**Kenapa EventBus?**
- ✅ Reactive updates without framework
- ✅ Decoupled components
- ✅ Simple implementation (~30 lines)
- ✅ No dependencies

### ✅ Offline Storage
- **IndexedDB** dengan schema terstruktur

**Kenapa IndexedDB?**
- ✅ Browser-native (no dependencies)
- ✅ Async API (non-blocking)
- ✅ Large storage (~50MB+)
- ✅ Structured data dengan indexes
- ✅ Perfect untuk offline HLS segments

### ✅ Environment Config
- **Single env.js** (centralized configuration)

**Kenapa env.js?**
- ✅ Simple - No build tools required
- ✅ Runtime config - Easy to change per deployment
- ✅ Git-friendly - .env.example as template

### ✅ Background Sync Strategy
- **Sequential Download** - 1 content at a time (tidak parallel)
- **Heartbeat** - Every 30 seconds
- **Check Update** - Every 15 minutes

## Structure (Clean Architecture - Flat)

```
player-vanillajs/
├── index.html                 # Entry point
├── player.html                # Player view (after activation)
├── service-worker.js          # PWA offline support
├── .env.example
├── js/
│   ├── main.js               # 🎯 Entry point (init all features)
│   ├── features/             # 🎯 FEATURE-BASED (Clean Architecture)
│   │   ├── activation/       # Device activation feature
│   │   │   ├── models/
│   │   │   │   ├── Device.js          # Device model
│   │   │   │   └── ActivationCode.js  # Activation code model
│   │   │   ├── services/
│   │   │   │   └── ActivationService.js  # API calls for activation
│   │   │   ├── state/
│   │   │   │   └── activationState.js    # State management
│   │   │   └── ui/
│   │   │       └── ActivationUI.js       # UI controller
│   │   ├── player/           # HLS player feature
│   │   │   ├── models/
│   │   │   │   ├── Playlist.js     # Playlist model
│   │   │   │   ├── Content.js      # Content/video model
│   │   │   │   └── Segment.js      # HLS segment model
│   │   │   ├── services/
│   │   │   │   ├── PlaylistService.js   # Playlist API
│   │   │   │   ├── HLSPlayerService.js  # HLS.js wrapper
│   │   │   │   └── PlaybackService.js   # Playback logic
│   │   │   ├── state/
│   │   │   │   └── playerState.js       # Player state
│   │   │   └── ui/
│   │   │       └── PlayerUI.js          # Player UI controller
│   │   └── sync/             # Background sync feature
│   │       ├── models/
│   │       │   ├── SyncStatus.js        # Sync status model
│   │       │   └── DownloadProgress.js  # Download progress
│   │       ├── services/
│   │       │   ├── SyncService.js       # Sync logic
│   │       │   ├── DownloadService.js   # Content download
│   │       │   └── HeartbeatService.js  # Heartbeat to server
│   │       ├── workers/      # Background tasks
│   │       │   ├── heartbeatWorker.js   # 30s heartbeat
│   │       │   └── syncWorker.js        # 15min sync check
│   │       └── state/
│   │           └── syncState.js         # Sync state
│   └── core/                 # 📦 SHARED/CORE
│       ├── config/
│       │   ├── env.js        # ⚠️ CENTRALIZED ENV
│       │   └── constants.js  # App constants
│       ├── api/
│       │   ├── client.js     # ⚠️ CENTRALIZED HTTP client
│       │   └── endpoints.js  # ⚠️ CENTRALIZED API routes
│       ├── storage/
│       │   ├── indexedDB.js  # IndexedDB wrapper
│       │   ├── schema.js     # Database schema
│       │   └── migrations.js # Schema migrations
│       ├── utils/
│       │   ├── logger.js     # Logging utility
│       │   ├── eventBus.js   # Pub/Sub pattern
│       │   └── helpers.js    # Helper functions
│       └── widgets/          # Reusable UI components
│           ├── loading.js
│           └── error.js
├── assets/
│   ├── images/
│   └── fonts/
└── README.md
```

## Key Principles

### 1. Centralized Configuration

**Single Source of Truth:**

```javascript
// js/core/config/env.js
window.ENV = {
  API_BASE_URL: 'http://192.168.5.12:8001',
  API_TIMEOUT: 30000,
  HEARTBEAT_INTERVAL: 30000,
  SYNC_CHECK_INTERVAL: 900000, // 15 minutes
  OFFLINE_CACHE_SIZE: 50 * 1024 * 1024, // 50MB
};
```

**Benefits:**
- ✅ No hardcoded URLs
- ✅ Easy environment switching
- ✅ Single file to update per deployment

### 2. Centralized API Endpoints

**Single Source for All Routes:**

```javascript
// js/core/api/endpoints.js
const API_V1 = '/api/v1';

export const API_ENDPOINTS = {
  DEVICES: {
    ACTIVATE: `${API_V1}/devices/activate`,
    HEARTBEAT: (code) => `${API_V1}/devices/${code}/heartbeat`,
  },
  PLAYLISTS: {
    GET: (deviceId) => `${API_V1}/playlists?device_id=${deviceId}`,
  },
  CONTENTS: {
    BY_ID: (id) => `${API_V1}/contents/${id}`,
    DOWNLOAD_URL: (id) => `${API_V1}/contents/${id}/download`,
  },
};
```

**Benefits:**
- ✅ No scattered API calls
- ✅ Easy to maintain
- ✅ Type-safe (with JSDoc)
- ✅ Backend changes = 1 file update

### 3. Feature-Based Organization

**Each feature is self-contained:**

```
features/activation/
  ├── models/      # Data structures
  ├── services/    # API calls & business logic
  ├── state/       # State management
  └── ui/          # UI controllers
```

**Benefits:**
- ✅ Easy to locate code
- ✅ Clear boundaries
- ✅ Scalable (add features without refactor)
- ✅ Team collaboration friendly

### 4. Separation of Concerns

**Models** = Data structures
**Services** = Business logic & API
**State** = State management
**UI** = DOM manipulation only

## Code Patterns & Examples

### 1. Models (Data Classes)

```javascript
// js/features/player/models/Playlist.js
export class Playlist {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.contents = data.contents || [];
    this.created_at = data.created_at;
    this.updated_at = data.updated_at;
  }

  // Validation
  validate() {
    return this.id && this.name && Array.isArray(this.contents);
  }

  // Business logic
  get totalDuration() {
    return this.contents.reduce((sum, content) => sum + content.duration, 0);
  }

  // Serialization
  toJSON() {
    return {
      id: this.id,
      name: this.name,
      contents: this.contents.map(c => c.toJSON()),
    };
  }
}
```

### 2. Services (API Calls)

```javascript
// js/features/player/services/PlaylistService.js
import { API_ENDPOINTS } from '@/core/api/endpoints.js';
import { apiClient } from '@/core/api/client.js';
import { Playlist } from '../models/Playlist.js';

export class PlaylistService {
  /**
   * Fetch playlist for device
   * @param {string} deviceId - Device ID
   * @returns {Promise<Playlist>}
   */
  async fetchPlaylist(deviceId) {
    try {
      const response = await apiClient.get(
        API_ENDPOINTS.PLAYLISTS.GET(deviceId)
      );
      return new Playlist(response.data);
    } catch (error) {
      console.error('Failed to fetch playlist:', error);
      throw error;
    }
  }

  /**
   * Cache playlist for offline use
   * @param {Playlist} playlist
   */
  async cachePlaylist(playlist) {
    const db = await window.DB.open();
    await db.playlists.put(playlist.toJSON());
  }
}
```

### 3. State Management (EventBus)

```javascript
// js/core/utils/eventBus.js
class EventBus {
  constructor() {
    this.events = {};
  }

  /**
   * Subscribe to event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  }

  /**
   * Unsubscribe from event
   * @param {string} event - Event name
   * @param {Function} callback - Callback to remove
   */
  off(event, callback) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(cb => cb !== callback);
  }

  /**
   * Emit event
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(callback => callback(data));
  }
}

export const eventBus = new EventBus();
```

**Usage:**

```javascript
// js/features/player/state/playerState.js
import { eventBus } from '@/core/utils/eventBus.js';

export const playerState = {
  playlist: null,
  currentIndex: 0,
  isPlaying: false,
};

// Update state and notify listeners
export function setPlaylist(playlist) {
  playerState.playlist = playlist;
  eventBus.emit('playlist:loaded', playlist);
}

export function setCurrentIndex(index) {
  playerState.currentIndex = index;
  eventBus.emit('player:indexChanged', index);
}

// Subscribe to state changes
eventBus.on('playlist:loaded', (playlist) => {
  console.log('Playlist loaded:', playlist.name);
  // Update UI
});
```

### 4. Background Workers

```javascript
// js/features/sync/workers/heartbeatWorker.js
import { HeartbeatService } from '../services/HeartbeatService.js';
import { eventBus } from '@/core/utils/eventBus.js';

export class HeartbeatWorker {
  constructor(interval = 30000) {
    this.interval = interval;
    this.timer = null;
    this.isRunning = false;
  }

  /**
   * Start heartbeat worker
   */
  start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.timer = setInterval(() => this.sendHeartbeat(), this.interval);
    console.log('Heartbeat worker started');
  }

  /**
   * Stop heartbeat worker
   */
  stop() {
    if (!this.isRunning) return;
    
    clearInterval(this.timer);
    this.isRunning = false;
    console.log('Heartbeat worker stopped');
  }

  /**
   * Send heartbeat to server
   */
  async sendHeartbeat() {
    try {
      const result = await HeartbeatService.send();
      eventBus.emit('heartbeat:success', result);
    } catch (error) {
      console.error('Heartbeat failed:', error);
      eventBus.emit('heartbeat:failed', error);
    }
  }
}
```

### 5. IndexedDB with Schema

```javascript
// js/core/storage/schema.js
export const DB_NAME = 'signage_player';
export const DB_VERSION = 1;

export const SCHEMA = {
  devices: {
    keyPath: 'id',
    indexes: [
      { name: 'code', keyPath: 'code', unique: true },
      { name: 'last_seen', keyPath: 'last_seen' },
    ],
  },
  playlists: {
    keyPath: 'id',
    indexes: [
      { name: 'device_id', keyPath: 'device_id' },
      { name: 'updated_at', keyPath: 'updated_at' },
    ],
  },
  contents: {
    keyPath: 'id',
    indexes: [
      { name: 'playlist_id', keyPath: 'playlist_id' },
      { name: 'download_status', keyPath: 'download_status' },
    ],
  },
  segments: {
    keyPath: 'id',
    indexes: [
      { name: 'content_id', keyPath: 'content_id' },
      { name: 'sequence', keyPath: 'sequence' },
    ],
  },
};
```

```javascript
// js/core/storage/indexedDB.js
import { DB_NAME, DB_VERSION, SCHEMA } from './schema.js';

class IndexedDBManager {
  constructor() {
    this.db = null;
  }

  /**
   * Open database connection
   * @returns {Promise<IDBDatabase>}
   */
  async open() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        this.createStores(db);
      };
    });
  }

  /**
   * Create object stores based on schema
   */
  createStores(db) {
    Object.entries(SCHEMA).forEach(([storeName, config]) => {
      if (!db.objectStoreNames.contains(storeName)) {
        const store = db.createObjectStore(storeName, {
          keyPath: config.keyPath,
          autoIncrement: config.autoIncrement,
        });

        // Create indexes
        config.indexes?.forEach(index => {
          store.createIndex(index.name, index.keyPath, {
            unique: index.unique || false,
          });
        });
      }
    });
  }

  /**
   * Get data from store
   */
  async get(storeName, key) {
    const tx = this.db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Put data to store
   */
  async put(storeName, data) {
    const tx = this.db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Query by index
   */
  async getByIndex(storeName, indexName, value) {
    const tx = this.db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const index = store.index(indexName);
    return new Promise((resolve, reject) => {
      const request = index.get(value);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

export const dbManager = new IndexedDBManager();
```

## Sequential Download Strategy

**Why Sequential?**
- ✅ Predictable bandwidth usage
- ✅ Easier progress tracking
- ✅ Prevents parallel download conflicts
- ✅ Battery-friendly for devices

**Implementation:**

```javascript
// js/features/sync/services/DownloadService.js
export class DownloadService {
  constructor() {
    this.currentDownload = null;
    this.queue = [];
  }

  /**
   * Add content to download queue
   */
  async queueDownload(content) {
    this.queue.push(content);
    eventBus.emit('download:queued', content);
    
    if (!this.currentDownload) {
      await this.processQueue();
    }
  }

  /**
   * Process download queue sequentially
   */
  async processQueue() {
    while (this.queue.length > 0) {
      this.currentDownload = this.queue.shift();
      
      try {
        await this.downloadContent(this.currentDownload);
        eventBus.emit('download:completed', this.currentDownload);
      } catch (error) {
        console.error('Download failed:', error);
        eventBus.emit('download:failed', {
          content: this.currentDownload,
          error,
        });
      }
      
      this.currentDownload = null;
    }
  }

  /**
   * Download single content (HLS segments)
   */
  async downloadContent(content) {
    // 1. Fetch M3U8 playlist
    const playlist = await this.fetchM3U8(content.hls_url);
    
    // 2. Parse segments
    const segments = this.parseSegments(playlist);
    
    // 3. Download segments sequentially
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      const blob = await this.downloadSegment(segment.url);
      
      // Store in IndexedDB
      await dbManager.put('segments', {
        id: `${content.id}_${segment.sequence}`,
        content_id: content.id,
        sequence: segment.sequence,
        blob: blob,
        downloaded_at: new Date(),
      });
      
      // Emit progress
      const progress = ((i + 1) / segments.length) * 100;
      eventBus.emit('download:progress', {
        content_id: content.id,
        progress,
      });
    }
  }
}
```

## Background Tasks

### 1. Heartbeat (Every 30s)

```javascript
// js/features/sync/workers/heartbeatWorker.js
import { HeartbeatService } from '../services/HeartbeatService.js';

const heartbeatWorker = new HeartbeatWorker(30000); // 30 seconds

// Start when device is activated
eventBus.on('device:activated', () => {
  heartbeatWorker.start();
});

// Stop when device is deactivated
eventBus.on('device:deactivated', () => {
  heartbeatWorker.stop();
});
```

### 2. Sync Check (Every 15 minutes)

```javascript
// js/features/sync/workers/syncWorker.js
import { SyncService } from '../services/SyncService.js';

export class SyncWorker {
  constructor(interval = 900000) { // 15 minutes
    this.interval = interval;
    this.timer = null;
  }

  start() {
    this.timer = setInterval(() => this.checkUpdate(), this.interval);
  }

  async checkUpdate() {
    try {
      const hasUpdate = await SyncService.checkForUpdates();
      if (hasUpdate) {
        eventBus.emit('sync:updateAvailable');
      }
    } catch (error) {
      console.error('Sync check failed:', error);
    }
  }
}
```

## Migration from Old Structure

### Phase 1: Restructure (Week 1)
1. ✅ Create features/ folder structure
2. ✅ Create core/ folder structure
3. Move shell/* → features/activation/
4. Move player/* → features/player/
5. Move shared/* → core/utils/
6. Create core/config/ with centralized env.js
7. Create core/api/endpoints.js

### Phase 2: Models & Services (Week 2)
1. Create models/ in each feature
2. Extract services/ from existing code
3. Refactor API calls to use centralized endpoints
4. Add JSDoc types to all functions

### Phase 3: State & Workers (Week 3)
1. Implement EventBus for state management
2. Refactor state to use EventBus
3. Organize background workers
4. Document sequential download

### Phase 4: Storage & Docs (Week 4)
1. Structure IndexedDB with schema
2. Create migration system for DB versions
3. Add comprehensive JSDoc comments
4. Update this README with examples

## Development Workflow

### 1. Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd player-vanillajs

# Copy environment template
cp js/core/config/env.example.js js/core/config/env.js

# Edit env.js with your settings
nano js/core/config/env.js
```

### 2. Development Server

```bash
# Simple HTTP server (Python)
python3 -m http.server 8080

# Or use Node.js
npx serve -p 8080

# Or use PHP
php -S localhost:8080
```

Access: `http://localhost:8080`

### 3. Testing

**Manual Testing:**
1. Open browser DevTools
2. Go to Application → Storage → IndexedDB
3. Monitor network calls
4. Check console for errors

**Test Activation:**
1. Open `http://localhost:8080`
2. Enter 6-digit activation code
3. Verify device appears in CMS dashboard

**Test Player:**
1. Activate device
2. Assign playlist in CMS
3. Verify playlist loads
4. Check HLS playback

### 4. Debugging

```javascript
// Enable debug mode in env.js
window.ENV = {
  DEBUG: true, // Enable verbose logging
  API_BASE_URL: 'http://192.168.5.12:8001',
};

// Use logger
import { logger } from '@/core/utils/logger.js';
logger.debug('Player state:', playerState);
logger.info('Playlist loaded');
logger.error('Download failed', error);
```

## Deployment

### 1. Build for Production

```bash
# Minify JS (optional)
npm install -g terser
find js -name "*.js" -exec terser {} -o {}.min -c -m \;

# Or use build script
./build.sh
```

### 2. Deploy to Server

```bash
# Copy to server
scp -r * user@server:/path/to/player-vanillajs/

# Or use rsync
rsync -avz --exclude 'node_modules' . user@server:/path/to/player-vanillajs/
```

### 3. Configure for Production

```javascript
// js/core/config/env.js
window.ENV = {
  API_BASE_URL: 'https://api.yourdomain.com',
  DEBUG: false,
  HEARTBEAT_INTERVAL: 30000,
  SYNC_CHECK_INTERVAL: 900000,
};
```

### 4. Deploy to WebOS TV

```bash
# Package for WebOS (IPK)
cd webos-app
./package.sh

# Install to TV
ares-install com.signage.player_1.0.0_all.ipk -d <tv-name>
```

## API Integration

### Backend Endpoints Required

```
POST   /api/v1/devices/activate
POST   /api/v1/devices/{code}/heartbeat
GET    /api/v1/playlists?device_id={id}
GET    /api/v1/contents/{id}
GET    /api/v1/contents/{id}/download
```

### Authentication

```javascript
// Stored in localStorage after activation
localStorage.setItem('device_token', token);

// Used in API calls
headers: {
  'Authorization': `Bearer ${token}`,
}
```

## Performance Optimization

### 1. Lazy Loading

```javascript
// Load features on demand
async function loadFeature(name) {
  const module = await import(`./features/${name}/init.js`);
  return module.default;
}
```

### 2. IndexedDB Caching

```javascript
// Cache API responses
async function fetchWithCache(url) {
  const cached = await dbManager.get('cache', url);
  if (cached && !isExpired(cached)) {
    return cached.data;
  }
  
  const data = await fetch(url).then(r => r.json());
  await dbManager.put('cache', { url, data, timestamp: Date.now() });
  return data;
}
```

### 3. Service Worker Caching

```javascript
// service-worker.js
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

## Troubleshooting

### Issue: Activation fails
- Check API_BASE_URL in env.js
- Verify backend is running
- Check network tab in DevTools
- Verify activation code is valid

### Issue: HLS not playing
- Check HLS.js is loaded
- Verify content URL is accessible
- Check browser console for errors
- Test with different video

### Issue: Heartbeat not working
- Verify heartbeatWorker is started
- Check interval is correct (30000ms)
- Monitor network tab for heartbeat calls
- Check device token is valid

### Issue: Download not working
- Check DownloadService queue
- Verify IndexedDB is accessible
- Check storage quota
- Monitor download progress events

## Contributing

1. Follow Clean Architecture principles
2. Use JSDoc for all functions
3. Test on multiple browsers
4. Update README with changes

## License

MIT

---

**Status**: Production Ready ✅
**Version**: 1.0.0
**Last Updated**: 2025-11-02

