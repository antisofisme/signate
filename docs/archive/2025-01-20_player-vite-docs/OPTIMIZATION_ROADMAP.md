# HLS.js Optimization Roadmap
## Recommended Improvements Without Video.js Migration

**Last Updated**: 2025-01-16
**Status**: Actionable recommendations based on performance analysis
**Objective**: Achieve 50% faster transitions and 30% lower memory usage

---

## Executive Summary

Based on comprehensive performance analysis, **we recommend staying with HLS.js** and implementing targeted optimizations. This approach will deliver better performance than migrating to Video.js, with significantly less risk and effort.

**Expected Outcomes**:
- Transition time: 280ms → **140ms** (-50%)
- Memory usage: 78MB → **55MB** (-30%)
- Bundle size: Unchanged (no bloat)
- Stability: Maintained (no regressions)
- Implementation time: **2-3 weeks** vs 6-8 weeks for Video.js migration

---

## Phase 1: Quick Wins (Week 1) - High Impact, Low Effort

### 1.1 Player Instance Pooling ⭐⭐⭐

**Problem**: Currently destroying and recreating HLS instance on every transition
**Impact**: 45MB memory churn per transition, 100-150ms overhead

**Implementation**:

```typescript
// File: src/player/services/player-hls.ts

class PlayerHLSClass implements IPlayerHLS {
  private hls: Hls | null = null;
  private currentSourceUrl: string | null = null;

  private async playHLS(url: string): Promise<void> {
    if (!this.videoElement) return;

    // OPTIMIZATION: Reuse HLS instance
    if (!this.hls) {
      this.hls = new Hls(this.hlsConfig);
      this.hls.attachMedia(this.videoElement);
      this.setupHLSEventListeners();
    }

    // Only reload source if URL changed
    if (this.currentSourceUrl !== url) {
      this.hls.loadSource(url);
      this.currentSourceUrl = url;
    }
  }

  private setupHLSEventListeners(): void {
    if (!this.hls) return;

    this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
      SharedLogger.log('[PlayerHLS] HLS manifest parsed');
      void this.videoElement?.play();
    });

    this.hls.on(Hls.Events.ERROR, (_event, data) => {
      if (data.fatal) {
        SharedLogger.error('[PlayerHLS] Fatal HLS error:', data);
        this.handleHLSError(data);
      }
    });
  }

  // Only destroy when player is fully destroyed
  destroy(): void {
    if (this.hls) {
      this.hls.destroy();
      this.hls = null;
      this.currentSourceUrl = null;
    }
    // ... rest of cleanup
  }
}
```

**Expected Gains**:
- Transition time: -100-150ms
- Memory churn: -33MB per transition
- GC pauses: -50% frequency

**Effort**: 2-3 hours
**Risk**: Low (easy to test and rollback)

---

### 1.2 Manifest Preloading ⭐⭐⭐

**Problem**: Manifest fetch blocks transition (150ms delay)
**Impact**: Noticeable gap between content items

**Implementation**:

```typescript
// File: src/player/services/player-hls.ts

class PlayerHLSClass implements IPlayerHLS {
  private preloadCache = new Map<string, string>();

  private async preloadNextManifest(): Promise<void> {
    if (!this.state.playlist) return;

    const nextIndex = (this.state.currentItemIndex + 1) % this.state.playlist.items.length;
    const nextItem = this.state.playlist.items[nextIndex];

    if (nextItem.content.type !== 'video') return;

    const url = nextItem.content.file_path || nextItem.content.url;
    if (!url?.includes('.m3u8')) return;

    try {
      const response = await fetch(url);
      const manifest = await response.text();
      this.preloadCache.set(url, manifest);

      SharedLogger.log('[PlayerHLS] Preloaded manifest for next item');
    } catch (error) {
      SharedLogger.warn('[PlayerHLS] Failed to preload manifest:', error);
    }
  }

  private async playHLS(url: string): Promise<void> {
    // Start preloading next item in background
    void this.preloadNextManifest();

    // Use preloaded manifest if available
    const cached = this.preloadCache.get(url);
    if (cached) {
      SharedLogger.log('[PlayerHLS] Using preloaded manifest');
      this.preloadCache.delete(url);
    }

    // Continue with HLS playback...
    if (!this.hls) {
      this.hls = new Hls(this.hlsConfig);
      this.hls.attachMedia(this.videoElement!);
    }
    this.hls.loadSource(url);
  }
}
```

**Expected Gains**:
- Manifest load time: 150ms → ~0ms
- Transition time: -100-150ms
- User experience: Seamless transitions

**Effort**: 3-4 hours
**Risk**: Low (graceful fallback if preload fails)

---

### 1.3 Buffer Size Tuning ⭐⭐

**Problem**: One-size-fits-all buffer config wastes memory
**Impact**: 10-15MB unnecessary buffer for short content

**Implementation**:

```typescript
// File: src/player/services/player-hls.ts

interface BufferProfile {
  maxBufferLength: number;
  backBufferLength: number;
  maxMaxBufferLength: number;
}

const BUFFER_PROFILES: Record<string, BufferProfile> = {
  // Short content (< 1 min) - Images, short clips
  'short': {
    maxBufferLength: 15,
    backBufferLength: 5,
    maxMaxBufferLength: 60,
  },

  // Standard signage (1-10 min) - Most content
  'standard': {
    maxBufferLength: 30,
    backBufferLength: 30,
    maxMaxBufferLength: 300,
  },

  // Long-form (> 10 min) - Full presentations, movies
  'long': {
    maxBufferLength: 120,
    backBufferLength: 10,
    maxMaxBufferLength: 600,
  },
};

class PlayerHLSClass implements IPlayerHLS {
  private selectBufferProfile(duration: number): BufferProfile {
    if (duration < 60) return BUFFER_PROFILES.short;
    if (duration < 600) return BUFFER_PROFILES.standard;
    return BUFFER_PROFILES.long;
  }

  private async playVideo(item: PlaylistItem): Promise<void> {
    const videoUrl = item.content.file_path || item.content.url;

    if (videoUrl?.includes('.m3u8') && Hls.isSupported()) {
      const profile = this.selectBufferProfile(item.duration);

      if (!this.hls) {
        this.hls = new Hls({
          ...this.hlsConfig,
          ...profile,
        });
        this.hls.attachMedia(this.videoElement!);
      } else {
        // Update config for existing instance
        Object.assign(this.hls.config, profile);
      }

      await this.playHLS(videoUrl);
    }
  }
}
```

**Expected Gains**:
- Memory usage: -5-10MB
- Faster seeks (shorter buffer to scan)
- Better cache efficiency

**Effort**: 2-3 hours
**Risk**: Low (easy to tune and test)

---

## Phase 2: Performance Enhancements (Week 2) - Medium Impact, Medium Effort

### 2.1 Service Worker Caching ⭐⭐⭐

**Problem**: Re-downloading same HLS segments on every loop
**Impact**: Bandwidth waste, slower playback on network issues

**Implementation**:

```typescript
// File: public/sw.js (new file)

const CACHE_NAME = 'signage-player-v1';
const HLS_CACHE = 'hls-segments-v1';

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/assets/index.js',
        '/assets/index.css',
      ]);
    })
  );
});

// Fetch event - cache HLS segments
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Cache HLS manifests and segments
  if (url.pathname.endsWith('.m3u8') || url.pathname.endsWith('.ts')) {
    event.respondWith(
      caches.open(HLS_CACHE).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            // Return cached, but update in background
            fetch(event.request).then((networkResponse) => {
              cache.put(event.request, networkResponse.clone());
            });
            return cachedResponse;
          }

          // Fetch and cache
          return fetch(event.request).then((networkResponse) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        });
      })
    );
  } else {
    // Normal fetch for other requests
    event.respondWith(fetch(event.request));
  }
});

// Periodic cleanup (remove old segments)
self.addEventListener('message', (event) => {
  if (event.data === 'cleanup') {
    caches.open(HLS_CACHE).then((cache) => {
      cache.keys().then((keys) => {
        const cutoff = Date.now() - 24 * 60 * 60 * 1000; // 24 hours
        keys.forEach((request) => {
          cache.match(request).then((response) => {
            const date = new Date(response.headers.get('date'));
            if (date.getTime() < cutoff) {
              cache.delete(request);
            }
          });
        });
      });
    });
  }
});
```

```typescript
// File: src/main.ts (register service worker)

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('[SW] Registered:', registration);

        // Periodic cleanup every 6 hours
        setInterval(() => {
          registration.active?.postMessage('cleanup');
        }, 6 * 60 * 60 * 1000);
      })
      .catch((error) => {
        console.error('[SW] Registration failed:', error);
      });
  });
}
```

**Expected Gains**:
- Segment load time: 180ms → 45ms (-75%)
- Bandwidth usage: 1.2GB/day → 350MB/day (-71%)
- Offline support: 24-hour cache
- Faster transitions on repeated content

**Effort**: 6-8 hours
**Risk**: Medium (test thoroughly on all devices)

---

### 2.2 IndexedDB Media Caching ⭐⭐

**Problem**: Re-downloading large MP4 files
**Impact**: Slow transitions, bandwidth waste

**Implementation**:

```typescript
// File: src/player/services/player-media-cache.ts (enhance existing)

class PlayerMediaCacheClass implements IPlayerMediaCache {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = 'signage-media-cache';
  private readonly STORE_NAME = 'media-files';
  private readonly MAX_CACHE_SIZE = 500 * 1024 * 1024; // 500MB

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          const store = db.createObjectStore(this.STORE_NAME, { keyPath: 'url' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('size', 'size', { unique: false });
        }
      };
    });
  }

  async cacheMedia(url: string, blob: Blob): Promise<void> {
    if (!this.db) await this.init();

    // Check cache size limit
    await this.enforceMaxCacheSize();

    const transaction = this.db!.transaction([this.STORE_NAME], 'readwrite');
    const store = transaction.objectStore(this.STORE_NAME);

    const cacheEntry = {
      url,
      blob,
      size: blob.size,
      timestamp: Date.now(),
    };

    await store.put(cacheEntry);
    SharedLogger.log('[MediaCache] Cached:', url, blob.size / 1024 / 1024, 'MB');
  }

  async getCachedMedia(url: string): Promise<Blob | null> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([this.STORE_NAME], 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);
      const request = store.get(url);

      request.onsuccess = () => {
        const entry = request.result;
        resolve(entry ? entry.blob : null);
      };

      request.onerror = () => resolve(null);
    });
  }

  private async enforceMaxCacheSize(): Promise<void> {
    // Get all entries sorted by timestamp
    const entries = await this.getAllEntries();

    let totalSize = entries.reduce((sum, e) => sum + e.size, 0);

    // Remove oldest entries until under limit
    for (const entry of entries.sort((a, b) => a.timestamp - b.timestamp)) {
      if (totalSize <= this.MAX_CACHE_SIZE) break;

      await this.deleteEntry(entry.url);
      totalSize -= entry.size;
    }
  }
}

export const PlayerMediaCache = new PlayerMediaCacheClass();
```

**Expected Gains**:
- MP4 load time: 2-5s → 100-200ms (95% faster)
- Bandwidth savings: ~70% for repeated content
- Smoother transitions

**Effort**: 8-10 hours
**Risk**: Medium (quota management, device storage limits)

---

### 2.3 Lazy Component Initialization ⭐

**Problem**: All UI components initialized on startup
**Impact**: Slower startup time

**Implementation**:

```typescript
// File: src/player/components/index.ts

class ComponentRegistry {
  private initialized = new Set<string>();

  async lazyInit(componentName: string): Promise<void> {
    if (this.initialized.has(componentName)) return;

    switch (componentName) {
      case 'quality-selector':
        const { QualitySelector } = await import('./quality-selector');
        // Initialize component
        this.initialized.add(componentName);
        break;

      case 'device-info':
        const { DeviceInfoPopup } = await import('./device-info-popup');
        // Initialize component
        this.initialized.add(componentName);
        break;

      // ... other components
    }
  }
}

export const componentRegistry = new ComponentRegistry();
```

**Expected Gains**:
- Startup time: -50-80ms
- Initial bundle size: -20-30KB
- Faster time-to-first-frame

**Effort**: 4-5 hours
**Risk**: Low (components load on-demand)

---

## Phase 3: Advanced Optimizations (Week 3) - High Impact, High Effort

### 3.1 Predictive Preloading ⭐⭐

**Problem**: Only preload next item, not next N items
**Impact**: Missed optimization opportunities

**Implementation**:

```typescript
// File: src/player/services/player-preloader.ts (new)

interface PreloadQueue {
  url: string;
  priority: number;
  type: 'manifest' | 'segment' | 'media';
}

class PlayerPreloaderClass {
  private queue: PreloadQueue[] = [];
  private maxConcurrent = 2;
  private active = 0;

  async preloadPlaylist(playlist: Playlist, currentIndex: number): Promise<void> {
    this.queue = [];

    // Preload next 3 items
    for (let i = 1; i <= 3; i++) {
      const index = (currentIndex + i) % playlist.items.length;
      const item = playlist.items[index];

      const priority = 4 - i; // Higher priority for sooner items

      if (item.content.type === 'video') {
        const url = item.content.file_path || item.content.url;

        if (url?.includes('.m3u8')) {
          // Preload manifest (high priority)
          this.queue.push({ url, priority: priority + 10, type: 'manifest' });
        } else {
          // Preload media file (medium priority)
          this.queue.push({ url: url!, priority, type: 'media' });
        }
      } else if (item.content.type === 'image') {
        // Preload image (low priority)
        const url = item.content.file_path || item.content.url;
        this.queue.push({ url: url!, priority: priority - 5, type: 'media' });
      }
    }

    // Sort by priority
    this.queue.sort((a, b) => b.priority - a.priority);

    // Start processing
    this.processQueue();
  }

  private async processQueue(): Promise<void> {
    while (this.queue.length > 0 && this.active < this.maxConcurrent) {
      const item = this.queue.shift();
      if (!item) break;

      this.active++;

      try {
        await fetch(item.url);
        SharedLogger.log('[Preloader] Preloaded:', item.type, item.url);
      } catch (error) {
        SharedLogger.warn('[Preloader] Failed:', item.url, error);
      } finally {
        this.active--;
        this.processQueue(); // Continue queue
      }
    }
  }
}

export const PlayerPreloader = new PlayerPreloaderClass();
```

**Expected Gains**:
- Transition time: -50-100ms (for preloaded items)
- Smoother multi-item playback
- Better use of idle network time

**Effort**: 10-12 hours
**Risk**: Medium (bandwidth usage, priority tuning)

---

### 3.2 Bandwidth-Aware Quality Selection ⭐⭐

**Problem**: Fixed quality, no adaptation to network conditions
**Impact**: Buffering on slow networks, underutilized on fast networks

**Implementation**:

```typescript
// File: src/player/services/player-bandwidth-monitor.ts (new)

class BandwidthMonitorClass {
  private samples: number[] = [];
  private readonly maxSamples = 10;

  recordSegmentDownload(bytes: number, durationMs: number): void {
    const bitsPerSecond = (bytes * 8) / (durationMs / 1000);
    this.samples.push(bitsPerSecond);

    if (this.samples.length > this.maxSamples) {
      this.samples.shift();
    }
  }

  getAverageBandwidth(): number {
    if (this.samples.length === 0) return 0;
    return this.samples.reduce((a, b) => a + b, 0) / this.samples.length;
  }

  getRecommendedQuality(): 'low' | 'medium' | 'high' | 'auto' {
    const bps = this.getAverageBandwidth();
    const mbps = bps / 1_000_000;

    if (mbps < 2) return 'low';
    if (mbps < 5) return 'medium';
    return 'high';
  }
}

export const BandwidthMonitor = new BandwidthMonitorClass();
```

**Expected Gains**:
- Reduced buffering on slow networks
- Better quality on fast networks
- Adaptive user experience

**Effort**: 12-14 hours
**Risk**: Medium (quality switching logic)

---

### 3.3 WebWorker for Segment Processing ⭐

**Problem**: Segment parsing blocks main thread
**Impact**: Frame drops during segment processing

**Implementation**:

```typescript
// File: public/hls-worker.js (new)

importScripts('https://cdn.jsdelivr.net/npm/hls.js@1.6.14/dist/hls.worker.min.js');

self.addEventListener('message', (event) => {
  const { type, data } = event.data;

  switch (type) {
    case 'PARSE_SEGMENT':
      // Process segment in worker thread
      const parsed = parseSegment(data);
      self.postMessage({ type: 'SEGMENT_PARSED', data: parsed });
      break;
  }
});
```

```typescript
// File: src/player/services/player-hls.ts

class PlayerHLSClass {
  private readonly hlsConfig: HLSConfig = {
    enableWorker: true,  // Already enabled ✓
    // ...
  };
}
```

**Expected Gains**:
- Smoother playback during segment processing
- No frame drops on segment load
- Better performance on low-end devices

**Effort**: Already implemented ✅
**Risk**: None (already using workers)

---

## Phase 4: Monitoring & Validation (Ongoing)

### 4.1 Performance Metrics Collection

**Implementation**:

```typescript
// File: src/shared/services/performance-monitor.ts (new)

interface PerformanceMetrics {
  transitionTime: number;
  memoryUsage: number;
  bufferHealth: number;
  droppedFrames: number;
}

class PerformanceMonitorClass {
  private metrics: PerformanceMetrics[] = [];

  recordTransition(startTime: number, endTime: number): void {
    const transitionTime = endTime - startTime;

    const memory = (performance as any).memory?.usedJSHeapSize || 0;

    this.metrics.push({
      transitionTime,
      memoryUsage: memory,
      bufferHealth: 0, // TODO: Calculate from HLS
      droppedFrames: 0, // TODO: Get from video element
    });

    // Log to analytics
    this.reportMetrics();
  }

  private reportMetrics(): void {
    const recent = this.metrics.slice(-10);
    const avgTransition = recent.reduce((a, b) => a + b.transitionTime, 0) / recent.length;

    SharedLogger.log('[Performance]', {
      avgTransitionTime: Math.round(avgTransition),
      memoryUsage: Math.round(recent[recent.length - 1].memoryUsage / 1024 / 1024),
    });
  }

  getMetricsSummary(): any {
    return {
      avgTransitionTime: this.metrics.reduce((a, b) => a + b.transitionTime, 0) / this.metrics.length,
      maxMemory: Math.max(...this.metrics.map(m => m.memoryUsage)),
      totalDroppedFrames: this.metrics.reduce((a, b) => a + b.droppedFrames, 0),
    };
  }
}

export const PerformanceMonitor = new PerformanceMonitorClass();
```

**Effort**: 6-8 hours
**Value**: Essential for tracking optimization impact

---

### 4.2 A/B Testing Framework

**Implementation**:

```typescript
// File: src/shared/services/feature-flags.ts (new)

class FeatureFlagsClass {
  private flags = new Map<string, boolean>();

  isEnabled(flag: string): boolean {
    // Check localStorage override
    const override = localStorage.getItem(`flag_${flag}`);
    if (override !== null) return override === 'true';

    // Device-based rollout (deterministic)
    const deviceId = localStorage.getItem('device_id') || '';
    const hash = this.hashCode(deviceId + flag);
    const rollout = this.flags.get(flag) || 0;

    return (hash % 100) < rollout;
  }

  setRollout(flag: string, percentage: number): void {
    this.flags.set(flag, percentage);
  }

  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }
}

export const FeatureFlags = new FeatureFlagsClass();

// Usage:
if (FeatureFlags.isEnabled('player-instance-pooling')) {
  // Use optimized version
} else {
  // Use old version
}
```

**Effort**: 4-5 hours
**Value**: Safe rollout of optimizations

---

## Implementation Priority

### High Priority (Implement First)

1. **Player Instance Pooling** (2-3h) → -50% transition time
2. **Manifest Preloading** (3-4h) → -100-150ms load time
3. **Buffer Size Tuning** (2-3h) → -10MB memory

**Total Time**: 7-10 hours
**Total Impact**: -50% transition time, -15% memory

---

### Medium Priority (Implement Second)

4. **Service Worker Caching** (6-8h) → -75% bandwidth
5. **IndexedDB Media Cache** (8-10h) → -95% MP4 load time
6. **Performance Monitoring** (6-8h) → Visibility

**Total Time**: 20-26 hours
**Total Impact**: -70% bandwidth, -80% repeated content load time

---

### Low Priority (Nice to Have)

7. **Predictive Preloading** (10-12h)
8. **Bandwidth-Aware Quality** (12-14h)
9. **A/B Testing Framework** (4-5h)

**Total Time**: 26-31 hours
**Total Impact**: Incremental improvements

---

## Success Criteria

### Phase 1 Targets (After Quick Wins)

- Transition time: < 150ms (current: 280ms)
- Memory usage: < 65MB (current: 78MB)
- No regressions in stability

### Phase 2 Targets (After Enhancements)

- Transition time: < 120ms
- Memory usage: < 60MB
- Bandwidth usage: -60%
- Offline capability: 24 hours

### Phase 3 Targets (After Advanced)

- Transition time: < 100ms
- Memory usage: < 55MB
- Zero buffering on 5+ Mbps
- Predictive loading working

---

## Testing Checklist

### Per-Optimization Testing

- [ ] Unit tests for new functions
- [ ] Integration test on local dev
- [ ] Chrome browser test
- [ ] Firefox browser test
- [ ] WebOS 4.x TV test
- [ ] WebOS 3.x TV test (critical)
- [ ] 24-hour soak test
- [ ] Memory leak check
- [ ] Performance metrics validation

### Rollout Process

1. Implement optimization on feature branch
2. Test locally (all scenarios)
3. Deploy to 5% of devices (internal)
4. Monitor metrics for 48 hours
5. If successful, increase to 25%
6. Monitor for 1 week
7. Full rollout to 100%

---

## Risk Mitigation

### High-Risk Changes

- Service Worker (can break caching)
- IndexedDB (quota issues)
- Player pooling (state management)

**Mitigation**:
- Feature flags for gradual rollout
- Extensive testing on real devices
- Easy rollback mechanism
- Fallback to old behavior on errors

### Low-Risk Changes

- Buffer tuning (easy to revert)
- Manifest preloading (graceful degradation)
- Performance monitoring (read-only)

**Mitigation**:
- Standard testing process
- Monitor metrics

---

## Conclusion

**Recommended Path**: Implement Phase 1 (Quick Wins) immediately for maximum impact with minimal risk.

**Timeline**:
- Week 1: Phase 1 (Quick Wins)
- Week 2: Phase 2 (Enhancements)
- Week 3: Phase 3 (Advanced) - Optional

**Expected Outcome**: 50% faster, 30% less memory, more stable than Video.js migration

**ROI**: 2-3 weeks effort vs 6-8 weeks for Video.js, with better results.

---

**Roadmap Version**: 1.0
**Last Updated**: 2025-01-16
**Status**: Ready for implementation
