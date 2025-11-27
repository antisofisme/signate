# Performance Optimization Implementation Guide
**Player-Vite | Smart TV Digital Signage**

Quick reference for implementing performance optimizations from the comprehensive review.

---

## 🎯 Quick Start: Top 5 Optimizations (Highest ROI)

### 1. Strip Console Logs in Production (5 minutes)
**Impact:** -15-20 KB bundle, +5-10% runtime performance

```diff
// vite.config.ts
terserOptions: {
  compress: {
-   drop_console: false,
+   drop_console: import.meta.env.PROD, // Keep in dev, strip in prod
    drop_debugger: true,
  },
}
```

Add debug flag for staging:
```bash
# Development
npm run dev  # Console logs enabled

# Production
npm run build  # Console logs stripped

# Staging (with logs)
VITE_DEBUG=true npm run build
```

---

### 2. Lazy Load UI Popups (30 minutes)
**Impact:** -30-40 KB initial bundle, -50-100ms TTI

```typescript
// main.ts - BEFORE
import { DeviceInfoPopup, ConnectionLogPopup } from '@player/components';
DeviceInfoPopup.init();
ConnectionLogPopup.init();
```

```typescript
// main.ts - AFTER
// Lazy load on first use
let DeviceInfoPopupLoaded = false;
document.getElementById('device-info-btn')?.addEventListener('click', async () => {
  if (!DeviceInfoPopupLoaded) {
    const { DeviceInfoPopup } = await import('@player/components/device-info-popup');
    DeviceInfoPopup.init();
    DeviceInfoPopupLoaded = true;
  }
  DeviceInfoPopup.show();
});

let ConnectionLogPopupLoaded = false;
window.addEventListener('connection:log:show', async () => {
  if (!ConnectionLogPopupLoaded) {
    const { ConnectionLogPopup } = await import('@player/components/connection-log-popup');
    ConnectionLogPopup.init();
    ConnectionLogPopupLoaded = true;
  }
  ConnectionLogPopup.show();
});
```

---

### 3. Periodic Cache Cleanup (1 hour)
**Impact:** Stable 24/7 operation, prevents OOM crashes

Create new file: `src/shared/services/cache-manager.ts`
```typescript
import { SharedLogger } from '@shared/logger';
import { getPlayerMediaCache, getPlayerHLSCache } from './service-registry';
import { PlayerPlaylistSync } from '@player/services/player-playlist-sync';

interface CacheStats {
  mediaCacheMB: number;
  hlsCacheMB: number;
  totalMB: number;
  itemsCleaned: number;
}

class CacheManager {
  private cleanupInterval: number | null = null;
  private readonly CLEANUP_INTERVAL_MS = 3600000; // 1 hour
  private readonly MAX_MEDIA_CACHE_MB = 500;
  private readonly MAX_MEDIA_ITEMS = 50;
  private readonly MAX_HLS_CACHE_MB = 500;

  /**
   * Start periodic cache cleanup
   */
  start(): void {
    if (this.cleanupInterval !== null) {
      SharedLogger.warn('[CacheManager] Already running');
      return;
    }

    SharedLogger.log('[CacheManager] 🧹 Starting periodic cleanup (every 1 hour)');

    // Run cleanup immediately
    void this.performCleanup();

    // Then run periodically
    this.cleanupInterval = window.setInterval(() => {
      void this.performCleanup();
    }, this.CLEANUP_INTERVAL_MS);
  }

  /**
   * Stop periodic cleanup
   */
  stop(): void {
    if (this.cleanupInterval !== null) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
      SharedLogger.log('[CacheManager] Stopped');
    }
  }

  /**
   * Perform cache cleanup
   */
  async performCleanup(): Promise<CacheStats> {
    SharedLogger.log('[CacheManager] 🧹 Running cleanup...');

    const startTime = Date.now();
    let itemsCleaned = 0;

    // 1. Cleanup media cache (LRU)
    const PlayerMediaCache = getPlayerMediaCache();
    if (PlayerMediaCache) {
      const mediaStatsBefore = await PlayerMediaCache.getCacheStats();
      await PlayerMediaCache.cleanupOldCache(
        this.MAX_MEDIA_ITEMS,
        this.MAX_MEDIA_CACHE_MB
      );
      const mediaStatsAfter = await PlayerMediaCache.getCacheStats();
      itemsCleaned += mediaStatsBefore.totalItems - mediaStatsAfter.totalItems;
    }

    // 2. Cleanup HLS cache (keep only current playlist + 2 recent)
    const PlayerHLSCache = getPlayerHLSCache();
    if (PlayerHLSCache) {
      const allContent = await PlayerHLSCache.getAllCachedContent();

      // Calculate total HLS cache size
      let totalHLSSizeMB = 0;
      const contentSizes: Array<{ contentId: number; sizeMB: number; cachedAt: string }> = [];

      for (const content of allContent) {
        // Estimate: 10 segments per quality, 500 KB per segment
        const segmentCount = Object.values(content.segments).reduce(
          (sum, segments) => sum + segments.length,
          0
        );
        const sizeMB = (segmentCount * 500) / 1024;
        totalHLSSizeMB += sizeMB;

        contentSizes.push({
          contentId: content.contentId,
          sizeMB,
          cachedAt: content.cachedAt,
        });
      }

      SharedLogger.log('[CacheManager] HLS cache analysis:', {
        totalContentCount: allContent.length,
        totalSizeMB: totalHLSSizeMB.toFixed(2),
      });

      // If over limit, delete oldest (except current playlist)
      if (totalHLSSizeMB > this.MAX_HLS_CACHE_MB) {
        SharedLogger.warn(
          `[CacheManager] HLS cache over limit (${totalHLSSizeMB.toFixed(2)} MB > ${this.MAX_HLS_CACHE_MB} MB), cleaning...`
        );

        // Get current playlist content IDs
        const currentPlaylist = PlayerPlaylistSync.getCurrentPlaylist();
        const currentContentIds = new Set(
          currentPlaylist?.items.map(item => item.content_id) || []
        );

        // Sort by cachedAt (oldest first)
        contentSizes.sort(
          (a, b) => new Date(a.cachedAt).getTime() - new Date(b.cachedAt).getTime()
        );

        // Delete until under limit
        let remainingSizeMB = totalHLSSizeMB;
        for (const content of contentSizes) {
          // Keep current playlist content
          if (currentContentIds.has(content.contentId)) {
            continue;
          }

          // Delete if still over target (400 MB = 80% of limit)
          if (remainingSizeMB > this.MAX_HLS_CACHE_MB * 0.8) {
            await PlayerHLSCache.clearCache(content.contentId);
            remainingSizeMB -= content.sizeMB;
            itemsCleaned++;
            SharedLogger.log(
              `[CacheManager] Deleted HLS content ${content.contentId} (${content.sizeMB.toFixed(2)} MB)`
            );
          } else {
            break;
          }
        }
      }
    }

    const duration = Date.now() - startTime;
    const stats: CacheStats = {
      mediaCacheMB: 0,
      hlsCacheMB: 0,
      totalMB: 0,
      itemsCleaned,
    };

    SharedLogger.log('[CacheManager] ✅ Cleanup complete', {
      duration: `${duration}ms`,
      itemsCleaned,
    });

    return stats;
  }

  /**
   * Emergency cleanup (called when memory is high)
   */
  async emergencyCleanup(): Promise<void> {
    SharedLogger.warn('[CacheManager] ⚠️ EMERGENCY CLEANUP');

    // Clear all media cache
    const PlayerMediaCache = getPlayerMediaCache();
    if (PlayerMediaCache) {
      await PlayerMediaCache.clearCache();
      SharedLogger.log('[CacheManager] Media cache cleared');
    }

    // Keep only current playlist in HLS cache
    const PlayerHLSCache = getPlayerHLSCache();
    if (PlayerHLSCache) {
      const allContent = await PlayerHLSCache.getAllCachedContent();
      const currentPlaylist = PlayerPlaylistSync.getCurrentPlaylist();
      const currentContentIds = new Set(
        currentPlaylist?.items.map(item => item.content_id) || []
      );

      for (const content of allContent) {
        if (!currentContentIds.has(content.contentId)) {
          await PlayerHLSCache.clearCache(content.contentId);
        }
      }

      SharedLogger.log('[CacheManager] HLS cache pruned to current playlist only');
    }

    SharedLogger.log('[CacheManager] ✅ Emergency cleanup complete');
  }
}

export const cacheManager = new CacheManager();

// Make available globally
if (typeof window !== 'undefined') {
  (window as any).__cacheManager = cacheManager;
}
```

Add to main.ts:
```typescript
// main.ts
import { cacheManager } from '@shared/services/cache-manager';

// In initApp(), after bootstrap
await ShellBootstrap.init();

// Start cache manager AFTER activation
if (SharedDeviceState.getDeviceId()) {
  cacheManager.start();
}
```

---

### 4. Memory Monitoring (1 hour)
**Impact:** Auto-recovery from memory leaks, prevents crashes

Create new file: `src/shared/services/memory-monitor.ts`
```typescript
import { SharedLogger } from '@shared/logger';
import { cacheManager } from './cache-manager';

interface MemoryStats {
  usedMB: number;
  totalMB: number;
  limitMB: number;
  percentage: number;
}

class MemoryMonitor {
  private monitorInterval: number | null = null;
  private readonly MONITOR_INTERVAL_MS = 300000; // 5 minutes
  private readonly WARNING_THRESHOLD = 0.7; // 70%
  private readonly CRITICAL_THRESHOLD = 0.85; // 85%
  private readonly MAX_MEMORY_MB = 512; // Target for WebOS TV

  /**
   * Check if performance.memory API is available
   */
  private isMemoryAPIAvailable(): boolean {
    return 'memory' in performance && typeof (performance as any).memory !== 'undefined';
  }

  /**
   * Start periodic memory monitoring
   */
  start(): void {
    if (!this.isMemoryAPIAvailable()) {
      SharedLogger.warn('[MemoryMonitor] performance.memory API not available');
      return;
    }

    if (this.monitorInterval !== null) {
      SharedLogger.warn('[MemoryMonitor] Already running');
      return;
    }

    SharedLogger.log('[MemoryMonitor] 🔍 Starting memory monitoring (every 5 minutes)');

    // Check immediately
    this.checkMemory();

    // Then check periodically
    this.monitorInterval = window.setInterval(() => {
      this.checkMemory();
    }, this.MONITOR_INTERVAL_MS);
  }

  /**
   * Stop memory monitoring
   */
  stop(): void {
    if (this.monitorInterval !== null) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
      SharedLogger.log('[MemoryMonitor] Stopped');
    }
  }

  /**
   * Get current memory stats
   */
  getMemoryStats(): MemoryStats | null {
    if (!this.isMemoryAPIAvailable()) return null;

    const memory = (performance as any).memory;
    const usedMB = memory.usedJSHeapSize / 1024 / 1024;
    const totalMB = memory.totalJSHeapSize / 1024 / 1024;
    const limitMB = memory.jsHeapSizeLimit / 1024 / 1024;
    const percentage = usedMB / limitMB;

    return { usedMB, totalMB, limitMB, percentage };
  }

  /**
   * Check memory usage and take action if needed
   */
  private checkMemory(): void {
    const stats = this.getMemoryStats();
    if (!stats) return;

    SharedLogger.log('[MemoryMonitor] Memory usage:', {
      used: `${stats.usedMB.toFixed(2)} MB`,
      total: `${stats.totalMB.toFixed(2)} MB`,
      limit: `${stats.limitMB.toFixed(2)} MB`,
      percentage: `${(stats.percentage * 100).toFixed(1)}%`,
    });

    // Warning threshold (70%)
    if (stats.percentage > this.WARNING_THRESHOLD && stats.percentage < this.CRITICAL_THRESHOLD) {
      SharedLogger.warn('[MemoryMonitor] ⚠️ High memory usage, triggering cleanup...');
      void cacheManager.performCleanup();
    }

    // Critical threshold (85%)
    if (stats.percentage > this.CRITICAL_THRESHOLD) {
      SharedLogger.error('[MemoryMonitor] 🔴 CRITICAL memory usage, emergency cleanup...');
      void cacheManager.emergencyCleanup().then(() => {
        // Check again after cleanup
        const statsAfter = this.getMemoryStats();
        if (statsAfter && statsAfter.percentage > this.CRITICAL_THRESHOLD) {
          SharedLogger.error('[MemoryMonitor] 💥 Memory still critical after cleanup, reloading...');
          setTimeout(() => window.location.reload(), 1000);
        }
      });
    }
  }

  /**
   * Force memory check (for debugging)
   */
  checkNow(): MemoryStats | null {
    const stats = this.getMemoryStats();
    if (stats) {
      console.table({
        'Used (MB)': stats.usedMB.toFixed(2),
        'Total (MB)': stats.totalMB.toFixed(2),
        'Limit (MB)': stats.limitMB.toFixed(2),
        'Usage (%)': `${(stats.percentage * 100).toFixed(1)}%`,
      });
    }
    return stats;
  }
}

export const memoryMonitor = new MemoryMonitor();

// Make available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).__memoryMonitor = memoryMonitor;
}
```

Add to main.ts:
```typescript
// main.ts
import { memoryMonitor } from '@shared/services/memory-monitor';

// In initApp(), after bootstrap
await ShellBootstrap.init();

// Start memory monitor
if (SharedDeviceState.getDeviceId()) {
  memoryMonitor.start();
}
```

Test in console:
```javascript
// Check memory manually
__memoryMonitor.checkNow()

// Check cache stats
__cacheManager.performCleanup()
```

---

### 5. Code Split Player Services (1 hour)
**Impact:** -40-60 KB initial bundle, faster activation screen

```typescript
// main.ts - BEFORE
import { PlayerPlaylistSync } from '@player/services';
void PlayerPlaylistSync; // Force evaluation
```

```typescript
// main.ts - AFTER
// Load player services ONLY after device is activated

async function startPlayerServices(): Promise<void> {
  SharedLogger.log('[Main] 🚀 Loading player services...');

  // Lazy load player services
  const [
    { PlayerHeartbeat },
    { PlayerPlaylistSync },
    { PlayerVideoJS },
  ] = await Promise.all([
    import('@player/services/player-heartbeat'),
    import('@player/services/player-playlist-sync'),
    import('@player/services/player-videojs'),
  ]);

  // Initialize video player
  const videoElement = document.getElementById('player-video') as HTMLVideoElement;
  if (videoElement) {
    PlayerVideoJS.init(videoElement);
  }

  // Start services
  PlayerHeartbeat.start();
  PlayerPlaylistSync.start();

  SharedLogger.log('[Main] ✅ Player services started');
}

// In ShellBootstrap.init() callback (after successful activation)
SharedEventBus.on('device:activated', () => {
  void startPlayerServices();
});
```

---

## 📦 Bundle Size Optimization

### Video.js Tree Shaking (2 hours)
**Impact:** -50-100 KB bundle size

```typescript
// Option 1: Import only core + http-streaming (recommended)
// player-videojs.ts
import videojs from 'video.js/dist/video.core.js';
import 'video.js/dist/video-js.css';
import '@videojs/http-streaming';

// Option 2: Custom Webpack build (advanced)
// Create custom-videojs.js:
import videojs from 'video.js/core';
import '@videojs/http-streaming';

// Exclude unused plugins
// - No DASH support (if not needed)
// - No Flash fallback
// - No TextTrack support

export default videojs;
```

Update vite.config.ts:
```typescript
resolve: {
  alias: {
    'video.js': path.resolve(__dirname, './src/lib/custom-videojs.js'),
  },
}
```

Test thoroughly - ensure HLS still works!

---

## 🚀 Startup Optimization

### Inline Critical CSS (30 minutes)
**Impact:** -50-100ms First Contentful Paint

```html
<!-- index.html -->
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- INLINE critical CSS for activation screen -->
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
      color: white;
      overflow: hidden;
    }

    #app {
      width: 100%;
      height: 100vh;
    }

    #shell-container {
      display: block;
      width: 100%;
      height: 100vh;
    }

    #player-container {
      display: none;
      width: 100%;
      height: 100vh;
      background: #000;
    }

    /* Activation screen critical styles */
    .activation-screen {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      padding: 2rem;
    }

    .activation-code {
      font-size: 4rem;
      font-weight: bold;
      letter-spacing: 0.5rem;
      margin: 2rem 0;
      color: #3b82f6;
    }
  </style>

  <!-- Load full CSS asynchronously -->
  <link rel="preload" href="/assets/index-ctjHUVhR.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/assets/index-ctjHUVhR.css"></noscript>

  <!-- Preconnect to API server -->
  <link rel="preconnect" href="https://api.zhmhotels.online">
  <link rel="dns-prefetch" href="https://api.zhmhotels.online">
</head>
```

---

### Predictive Preloading (1 hour)
**Impact:** Seamless transitions, better UX

```typescript
// player-videojs.ts - Add new method
async preloadNextItem(): Promise<void> {
  if (!this.state.playlist) return;

  const nextIndex = (this.state.currentItemIndex + 1) % this.state.playlist.items.length;
  const nextItem = this.state.playlist.items[nextIndex];

  if (!nextItem) return;

  SharedLogger.log('[PlayerVideoJS] 🔄 Preloading next item:', nextItem.content.name);

  // Preload based on content type
  if (nextItem.content.type === 'video') {
    const url = transformContentUrl(nextItem.content.file_path || nextItem.content.url || '');
    const isHLS = url.includes('.m3u8');

    if (isHLS) {
      const isCached = await getPlayerHLSCache()?.isHLSCached(nextItem.content_id);
      if (!isCached) {
        // Start caching in background (non-blocking)
        void getPlayerHLSCache()?.cacheHLSContent(nextItem.content_id, url);
      }
    } else {
      const isCached = await getPlayerMediaCache()?.isCached(url);
      if (!isCached) {
        void getPlayerMediaCache()?.cacheMedia(url, nextItem.content_id);
      }
    }
  } else if (nextItem.content.type === 'image' || nextItem.content.type === 'audio') {
    const url = transformContentUrl(nextItem.content.file_path || nextItem.content.url || '');
    const isCached = await getPlayerMediaCache()?.isCached(url);
    if (!isCached) {
      void getPlayerMediaCache()?.cacheMedia(url, nextItem.content_id);
    }
  }
}

// Call after current item starts playing
private setupEventListeners(): void {
  // ... existing code ...

  this.player.on('playing', () => {
    this.state.isPlaying = true;

    // Log playback start
    if (this.state.currentItem && this.state.playlist) {
      void PlayerPlaybackLogger.logPlaybackStart(
        this.state.currentItem,
        this.state.playlist.id
      );
    }

    // NEW: Preload next item (non-blocking)
    void this.preloadNextItem();
  });
}
```

---

## 🧪 Testing & Validation

### Before/After Measurements

```bash
# 1. Measure bundle size
npm run build
du -sh dist/
ls -lh dist/assets/

# Expected before: 5.2 MB total, 274 KB JS gzipped
# Expected after: 4.5 MB total, 180 KB JS gzipped (-34%)

# 2. Test startup time (Chrome DevTools)
# Open: http://localhost:8080/
# Network tab → Disable cache → Hard reload
# Performance tab → Record → Reload

# Expected before: TTI ~600ms, FCP ~250ms
# Expected after: TTI ~400ms, FCP ~150ms

# 3. Test memory stability (24h test)
# Open console:
setInterval(() => {
  __memoryMonitor.checkNow();
}, 60000); // Check every minute

# Expected: Memory usage stable at 100-150 MB after 24h

# 4. Test cache efficiency
# Play playlist twice, check logs:
# First loop: Should see "🌐 STREAMING" messages
# Second loop: Should see "💾 OFFLINE" messages (100% cache hit)
```

### Performance Checklist

After implementing optimizations, verify:

- [ ] Bundle size reduced by 30%+ (274 KB → < 190 KB gzipped)
- [ ] TTI improved by 25%+ (600ms → < 450ms)
- [ ] FCP improved by 30%+ (250ms → < 180ms)
- [ ] Console logs stripped in production build
- [ ] Memory usage stable after 24h operation (< 200 MB)
- [ ] Cache cleanup runs every hour
- [ ] Emergency cleanup triggers at 85% memory
- [ ] Predictive preloading works (next item cached in background)
- [ ] Video playback remains smooth (no regressions)
- [ ] HLS streaming works correctly (cache-first, then network)

---

## 📚 Additional Resources

### Debug Tools (Browser Console)

```javascript
// Check memory usage
__memoryMonitor.checkNow()

// Trigger cache cleanup
__cacheManager.performCleanup()

// Check cache stats
__cacheManager.performCleanup().then(stats => console.table(stats))

// Check player state
window.ServiceRegistry.get('PlayerVideoJS').getState()

// Check current playlist
window.ServiceRegistry.get('PlayerPlaylistSync').getCurrentPlaylist()

// Force playlist reload
window.ServiceRegistry.get('PlayerPlaylistSync').forceReload()
```

### Build Commands

```bash
# Development (with console logs)
npm run dev

# Production (console logs stripped)
npm run build

# Production with debug logs (staging)
VITE_DEBUG=true npm run build

# Type check only
npm run type-check

# Bundle analysis (install first)
npm install -D rollup-plugin-visualizer
# Add to vite.config.ts: visualizer({ open: true })
npm run build
```

### Performance Monitoring URLs

```bash
# Local
http://192.168.5.12:8080/

# VPS Production
https://player.zhmhotels.online/

# Chrome DevTools
chrome://inspect
```

---

## 🎯 Success Criteria

**Phase 1 Complete When:**
- ✅ Bundle size < 190 KB gzipped
- ✅ TTI < 450ms
- ✅ FCP < 180ms
- ✅ Console logs stripped in production
- ✅ UI popups lazy loaded

**Phase 2 Complete When:**
- ✅ Memory monitoring active
- ✅ Cache cleanup runs automatically
- ✅ 24h stability test passes (memory < 200 MB)
- ✅ Predictive preloading implemented
- ✅ Critical CSS inlined

**Phase 3 Complete When:**
- ✅ Bundle size < 160 KB gzipped
- ✅ Video.js tree shaken
- ✅ Responsive images implemented
- ✅ WebOS 3.x support (async/await transpiled)

---

**Last Updated:** 2025-11-26
**Next Review:** After Phase 1 implementation (2 weeks)
