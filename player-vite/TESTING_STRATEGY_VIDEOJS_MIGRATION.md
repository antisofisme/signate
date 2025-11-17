# Testing Strategy: Video.js Migration

## Executive Summary

This document outlines a comprehensive testing strategy for migrating from HLS.js to Video.js in the digital signage player. The critical focus is on ensuring race-free playback initialization, seamless content transitions, and robust error handling across all platforms (WebOS TV, modern browsers).

---

## 1. Test Framework Setup

### Tools & Dependencies

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@testing-library/dom": "^9.3.3",
    "msw": "^2.0.0",
    "happy-dom": "^12.10.3"
  }
}
```

### Test Structure

```
player-vite/
├── tests/
│   ├── unit/                      # Unit tests (Vitest)
│   │   ├── player-hls.test.ts
│   │   ├── player-playlist-sync.test.ts
│   │   ├── content-detection.test.ts
│   │   └── error-handlers.test.ts
│   ├── integration/               # Integration tests (Vitest + MSW)
│   │   ├── playlist-to-player.test.ts
│   │   ├── backend-integration.test.ts
│   │   ├── content-transitions.test.ts
│   │   └── widget-overlay.test.ts
│   ├── e2e/                       # End-to-end tests (Playwright)
│   │   ├── critical-path.spec.ts
│   │   ├── device-activation.spec.ts
│   │   ├── playlist-updates.spec.ts
│   │   ├── error-recovery.spec.ts
│   │   └── memory-leak.spec.ts
│   ├── regression/                # Regression tests
│   │   ├── waiting-content.spec.ts
│   │   ├── ui-components.spec.ts
│   │   ├── backend-compat.spec.ts
│   │   └── websocket-commands.spec.ts
│   ├── performance/               # Performance tests
│   │   ├── time-to-first-frame.spec.ts
│   │   ├── memory-usage.spec.ts
│   │   ├── cpu-usage.spec.ts
│   │   └── transition-smoothness.spec.ts
│   ├── device-specific/           # Cross-browser/platform tests
│   │   ├── webos-tv.spec.ts
│   │   ├── chrome.spec.ts
│   │   ├── firefox.spec.ts
│   │   └── safari.spec.ts
│   ├── fixtures/                  # Test data
│   │   ├── playlists/
│   │   ├── content/
│   │   └── mock-responses/
│   └── helpers/                   # Test utilities
│       ├── mock-backend.ts
│       ├── test-player.ts
│       └── assertions.ts
├── vitest.config.ts
└── playwright.config.ts
```

---

## 2. Unit Tests (Vitest)

### 2.1 PlayerHLS Class Tests

**File**: `tests/unit/player-hls.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PlayerHLS } from '@player/services/player-hls';
import videojs from 'video.js';

describe('PlayerHLS', () => {
  let videoElement: HTMLVideoElement;
  let player: typeof PlayerHLS;

  beforeEach(() => {
    // Setup DOM
    document.body.innerHTML = '<video id="test-video"></video>';
    videoElement = document.getElementById('test-video') as HTMLVideoElement;

    // Reset singleton state
    player = PlayerHLS;
    player.destroy();
  });

  describe('Initialization', () => {
    it('should initialize with video element', () => {
      expect(() => player.init(videoElement)).not.toThrow();
      expect(player.getState().isPlaying).toBe(false);
    });

    it('should throw if initialized twice without destroy', () => {
      player.init(videoElement);
      expect(() => player.init(videoElement)).toThrow(/already initialized/i);
    });

    it('should apply player configuration correctly', () => {
      player.init(videoElement);

      expect(videoElement.autoplay).toBe(true);
      expect(videoElement.muted).toBe(true);
      expect(videoElement.loop).toBe(false);
      expect(videoElement.controls).toBe(false);
    });

    it('should initialize Video.js instance', () => {
      const spy = vi.spyOn(videojs, 'default');
      player.init(videoElement);

      expect(spy).toHaveBeenCalledWith(videoElement, expect.any(Object));
    });
  });

  describe('Playlist Loading', () => {
    beforeEach(() => {
      player.init(videoElement);
    });

    it('should throw if video element not initialized', () => {
      player.destroy();
      expect(async () =>
        await player.loadPlaylist(mockPlaylist)
      ).rejects.toThrow(/not initialized/i);
    });

    it('should throw if playlist is empty', async () => {
      const emptyPlaylist = { id: 1, name: 'Empty', is_active: true, items: [] };

      await expect(player.loadPlaylist(emptyPlaylist))
        .rejects.toThrow(/playlist is empty/i);
    });

    it('should load valid playlist', async () => {
      const playlist = createMockPlaylist(3);

      await player.loadPlaylist(playlist);

      const state = player.getState();
      expect(state.playlist).toEqual(playlist);
      expect(state.currentItemIndex).toBe(0);
      expect(state.error).toBeNull();
    });

    it('should start playing first item automatically', async () => {
      const playlist = createMockPlaylist(3);
      const playSpy = vi.spyOn(player as any, 'playItem');

      await player.loadPlaylist(playlist);

      expect(playSpy).toHaveBeenCalledWith(0);
    });
  });

  describe('Content Type Detection', () => {
    beforeEach(() => {
      player.init(videoElement);
    });

    it('should detect HLS content (.m3u8)', async () => {
      const hlsItem = createMockPlaylistItem({
        content: { file_path: 'https://example.com/stream.m3u8', type: 'video' }
      });

      const playSpy = vi.spyOn(player as any, 'playHLS');
      await (player as any).playVideo(hlsItem);

      expect(playSpy).toHaveBeenCalledWith(hlsItem.content.file_path);
    });

    it('should detect direct video (MP4, WebM)', async () => {
      const mp4Item = createMockPlaylistItem({
        content: { file_path: 'https://example.com/video.mp4', type: 'video' }
      });

      const playSpy = vi.spyOn(player as any, 'playDirect');
      await (player as any).playVideo(mp4Item);

      expect(playSpy).toHaveBeenCalledWith(mp4Item.content.file_path);
    });

    it('should handle image content', async () => {
      const imageItem = createMockPlaylistItem({
        content: { file_path: 'https://example.com/image.jpg', type: 'image' }
      });

      await (player as any).playImage(imageItem);

      const imgElement = document.getElementById('temp-image');
      expect(imgElement).toBeTruthy();
      expect(imgElement?.getAttribute('src')).toBe(imageItem.content.file_path);
    });

    it('should handle URL content (iframe)', async () => {
      const urlItem = createMockPlaylistItem({
        content: { url: 'https://example.com', type: 'url' }
      });

      await (player as any).playURL(urlItem);

      const iframeElement = document.getElementById('temp-iframe');
      expect(iframeElement).toBeTruthy();
      expect(iframeElement?.getAttribute('src')).toBe(urlItem.content.url);
    });
  });

  describe('Playback Control', () => {
    beforeEach(async () => {
      player.init(videoElement);
      await player.loadPlaylist(createMockPlaylist(3));
    });

    it('should play/pause correctly', async () => {
      await player.play();
      expect(player.getState().isPlaying).toBe(true);

      player.pause();
      expect(player.getState().isPlaying).toBe(false);
    });

    it('should advance to next item', async () => {
      expect(player.getState().currentItemIndex).toBe(0);

      await player.next();
      expect(player.getState().currentItemIndex).toBe(1);

      await player.next();
      expect(player.getState().currentItemIndex).toBe(2);
    });

    it('should loop back to first item after last', async () => {
      await player.next(); // index 1
      await player.next(); // index 2
      await player.next(); // should loop to 0

      expect(player.getState().currentItemIndex).toBe(0);
    });

    it('should go to previous item', async () => {
      await player.next(); // index 1
      await player.previous(); // back to 0

      expect(player.getState().currentItemIndex).toBe(0);
    });

    it('should wrap to last item when going previous from first', async () => {
      await player.previous(); // should go to last item (2)

      expect(player.getState().currentItemIndex).toBe(2);
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      player.init(videoElement);
    });

    it('should handle Video.js fatal errors', async () => {
      const errorSpy = vi.fn();
      player.on('error', errorSpy);

      // Trigger fatal error
      const vjsPlayer = (player as any).vjsPlayer;
      vjsPlayer.error({ code: 4, message: 'Fatal error' });

      expect(errorSpy).toHaveBeenCalled();
    });

    it('should skip to next item on playback error', async () => {
      await player.loadPlaylist(createMockPlaylist(3));

      const nextSpy = vi.spyOn(player, 'next');

      // Simulate error
      videoElement.dispatchEvent(new Event('error'));

      expect(nextSpy).toHaveBeenCalled();
    });

    it('should recover from network errors', async () => {
      const playlist = createMockPlaylist(1, {
        content: { file_path: 'https://example.com/stream.m3u8', type: 'video' }
      });
      await player.loadPlaylist(playlist);

      // Simulate network error with Video.js
      const vjsPlayer = (player as any).vjsPlayer;
      const errorHandler = vi.spyOn(player as any, 'handleVideoJSError');

      vjsPlayer.trigger('error');

      expect(errorHandler).toHaveBeenCalled();
    });
  });

  describe('Cleanup', () => {
    it('should cleanup temporary elements on destroy', async () => {
      player.init(videoElement);
      const imageItem = createMockPlaylistItem({
        content: { file_path: 'image.jpg', type: 'image' }
      });

      await (player as any).playImage(imageItem);
      expect(document.getElementById('temp-image')).toBeTruthy();

      player.destroy();
      expect(document.getElementById('temp-image')).toBeFalsy();
    });

    it('should destroy Video.js instance', () => {
      player.init(videoElement);
      const vjsPlayer = (player as any).vjsPlayer;
      const disposeSpy = vi.spyOn(vjsPlayer, 'dispose');

      player.destroy();

      expect(disposeSpy).toHaveBeenCalled();
    });

    it('should clear timers', async () => {
      player.init(videoElement);
      const playlist = createMockPlaylist(1, {
        content: { file_path: 'image.jpg', type: 'image' }
      });
      await player.loadPlaylist(playlist);

      const clearTimeoutSpy = vi.spyOn(window, 'clearTimeout');
      player.destroy();

      expect(clearTimeoutSpy).toHaveBeenCalled();
    });
  });
});
```

### 2.2 Test Utilities

**File**: `tests/helpers/test-player.ts`

```typescript
import type { Playlist, PlaylistItem, ContentItem } from '@player/types/player.types';

export function createMockPlaylist(
  itemCount: number,
  itemOverrides: Partial<PlaylistItem> = {}
): Playlist {
  const items: PlaylistItem[] = [];

  for (let i = 0; i < itemCount; i++) {
    items.push(createMockPlaylistItem({
      id: i + 1,
      order: i,
      ...itemOverrides
    }));
  }

  return {
    id: 1,
    name: 'Test Playlist',
    is_active: true,
    items,
  };
}

export function createMockPlaylistItem(
  overrides: Partial<PlaylistItem> = {}
): PlaylistItem {
  const content: ContentItem = {
    id: 1,
    name: 'Test Content',
    type: 'video',
    file_path: 'https://example.com/video.mp4',
    url: null,
    thumbnail_path: null,
    metadata: null,
    ...overrides.content,
  };

  return {
    id: 1,
    content_id: content.id,
    duration: 10,
    order: 0,
    content,
    ...overrides,
  };
}
```

---

## 3. Integration Tests

### 3.1 Playlist Sync → Player Flow

**File**: `tests/integration/playlist-to-player.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PlayerPlaylistSync } from '@player/services/player-playlist-sync';
import { PlayerHLS } from '@player/services/player-hls';
import { setupMockBackend } from '../helpers/mock-backend';

describe('Playlist Sync → Player Integration', () => {
  let mockBackend: ReturnType<typeof setupMockBackend>;

  beforeEach(() => {
    mockBackend = setupMockBackend();
    document.body.innerHTML = '<video id="player-video"></video>';
  });

  it('should initialize player when playlist syncs', async () => {
    const videoElement = document.getElementById('player-video') as HTMLVideoElement;
    PlayerHLS.init(videoElement);

    // Mock backend returns playlist
    mockBackend.mockPlaylistResponse({
      playlist: createMockPlaylist(3),
      has_changes: true,
    });

    const loadPlaylistSpy = vi.spyOn(PlayerHLS, 'loadPlaylist');

    await PlayerPlaylistSync.syncNow();

    expect(loadPlaylistSpy).toHaveBeenCalled();
    expect(PlayerHLS.getState().playlist).toBeTruthy();
  });

  it('should handle race condition: sync before player init', async () => {
    // Start sync BEFORE player is initialized
    const syncPromise = PlayerPlaylistSync.syncNow();

    // Wait 100ms then initialize player
    await sleep(100);
    const videoElement = document.getElementById('player-video') as HTMLVideoElement;
    PlayerHLS.init(videoElement);

    // Sync should complete without errors
    await expect(syncPromise).resolves.not.toThrow();
  });

  it('should update player when playlist changes', async () => {
    const videoElement = document.getElementById('player-video') as HTMLVideoElement;
    PlayerHLS.init(videoElement);

    // Initial playlist
    mockBackend.mockPlaylistResponse({
      playlist: createMockPlaylist(3),
      has_changes: true,
    });
    await PlayerPlaylistSync.syncNow();

    const initialPlaylistId = PlayerHLS.getState().playlist?.id;

    // Updated playlist
    mockBackend.mockPlaylistResponse({
      playlist: { ...createMockPlaylist(5), id: 2 },
      has_changes: true,
    });
    await PlayerPlaylistSync.syncNow();

    expect(PlayerHLS.getState().playlist?.id).not.toBe(initialPlaylistId);
    expect(PlayerHLS.getState().playlist?.items.length).toBe(5);
  });

  it('should show waiting screen when playlist removed', async () => {
    const videoElement = document.getElementById('player-video') as HTMLVideoElement;
    PlayerHLS.init(videoElement);

    // Initial playlist
    mockBackend.mockPlaylistResponse({
      playlist: createMockPlaylist(3),
      has_changes: true,
    });
    await PlayerPlaylistSync.syncNow();

    // No playlist assigned
    mockBackend.mockPlaylistResponse({
      playlist: null,
      has_changes: true,
      message: 'No playlist assigned',
    });
    await PlayerPlaylistSync.syncNow();

    const waitingScreen = document.querySelector('[data-testid="waiting-for-content"]');
    expect(waitingScreen).toBeTruthy();
    expect(waitingScreen?.style.display).not.toBe('none');
  });
});
```

---

## 4. End-to-End Tests (Playwright)

### 4.1 Critical Path Test

**File**: `tests/e2e/critical-path.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Critical Path: Device Activation → Content Playback', () => {
  test('should complete full activation and playback flow', async ({ page }) => {
    // 1. Navigate to player
    await page.goto('http://192.168.5.12:8080');

    // 2. Should show activation screen
    await expect(page.locator('[data-testid="activation-screen"]')).toBeVisible();

    // 3. Enter activation code
    const activationCode = await getActivationCode(); // From backend API
    await page.fill('[data-testid="activation-input"]', activationCode);
    await page.click('[data-testid="activate-button"]');

    // 4. Wait for activation success
    await expect(page.locator('[data-testid="activation-success"]'))
      .toBeVisible({ timeout: 5000 });

    // 5. Should hide activation screen
    await expect(page.locator('[data-testid="activation-screen"]'))
      .toBeHidden({ timeout: 2000 });

    // 6. Should start playlist sync
    await page.waitForTimeout(1000);

    // 7. Video should start playing (check video element)
    const video = page.locator('video');
    await expect(video).toBeVisible({ timeout: 10000 });

    // 8. Verify video is playing
    const isPlaying = await video.evaluate((v: HTMLVideoElement) =>
      !v.paused && v.currentTime > 0
    );
    expect(isPlaying).toBe(true);

    // 9. Wait for first content to complete
    await waitForContentTransition(page);

    // 10. Verify second content started
    const secondContent = await video.evaluate((v: HTMLVideoElement) =>
      v.currentTime > 0 && v.currentTime < 5
    );
    expect(secondContent).toBe(true);
  });

  test('should handle race condition: playlist loads before Video.js ready', async ({ page }) => {
    // Inject delay in Video.js initialization
    await page.addInitScript(() => {
      const originalVideoJS = window.videojs;
      window.videojs = (...args: any[]) => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve(originalVideoJS(...args));
          }, 2000); // 2 second delay
        });
      };
    });

    await page.goto('http://192.168.5.12:8080');

    // Activate device
    const code = await getActivationCode();
    await page.fill('[data-testid="activation-input"]', code);
    await page.click('[data-testid="activate-button"]');

    // Should still work despite delay
    const video = page.locator('video');
    await expect(video).toBeVisible({ timeout: 15000 });

    const isPlaying = await video.evaluate((v: HTMLVideoElement) =>
      !v.paused && v.currentTime > 0
    );
    expect(isPlaying).toBe(true);
  });
});
```

### 4.2 Error Recovery Test

**File**: `tests/e2e/error-recovery.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Error Recovery', () => {
  test('should recover from network failure during playback', async ({ page, context }) => {
    await page.goto('http://192.168.5.12:8080');

    // Activate and start playback
    await activateDevice(page);
    await waitForPlayback(page);

    // Simulate network offline
    await context.setOffline(true);
    await page.waitForTimeout(5000);

    // Should show offline indicator
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();

    // Restore network
    await context.setOffline(false);
    await page.waitForTimeout(2000);

    // Should resume playback
    const video = page.locator('video');
    const isPlaying = await video.evaluate((v: HTMLVideoElement) =>
      !v.paused && v.currentTime > 0
    );
    expect(isPlaying).toBe(true);
  });

  test('should skip corrupted content and continue playlist', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Mock playlist with corrupted second item
    await page.route('**/api/v1/client/playlist*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          playlist: {
            id: 1,
            name: 'Test',
            is_active: true,
            items: [
              createValidItem(1),
              createCorruptedItem(2), // Corrupted
              createValidItem(3),
            ],
          },
          has_changes: true,
        }),
      });
    });

    // Reload playlist
    await page.evaluate(() => window.PlayerPlaylistSync.forceReload());

    // First item plays
    await waitForContentTransition(page);

    // Second item errors and skips
    await waitForContentTransition(page);

    // Third item plays successfully
    const video = page.locator('video');
    const isPlaying = await video.evaluate((v: HTMLVideoElement) =>
      !v.paused && v.currentTime > 0
    );
    expect(isPlaying).toBe(true);
  });

  test('should handle HLS stream errors gracefully', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Monitor console for Video.js errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Mock HLS content that will fail
    await page.route('**/stream.m3u8', (route) => {
      route.abort('failed');
    });

    // Wait for error handling
    await page.waitForTimeout(5000);

    // Should have logged error but continued
    expect(errors.some(e => e.includes('HLS') || e.includes('Video.js'))).toBe(true);

    // Should have moved to next item
    const currentIndex = await page.evaluate(() =>
      window.PlayerHLS.getState().currentItemIndex
    );
    expect(currentIndex).toBeGreaterThan(0);
  });
});
```

### 4.3 Memory Leak Detection

**File**: `tests/e2e/memory-leak.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Memory Leak Detection', () => {
  test('should not leak memory over 24-hour simulation', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Record initial memory
    const initialMemory = await getMemoryUsage(page);

    // Simulate 24 hours (100 playlist cycles at 2 min/cycle = ~3.3 hours compressed)
    const cycleCount = 100;
    const itemDuration = 2000; // 2 seconds per item (compressed time)

    for (let i = 0; i < cycleCount; i++) {
      // Wait for full playlist cycle
      await page.waitForTimeout(itemDuration * 5); // 5 items

      // Force garbage collection periodically
      if (i % 10 === 0) {
        await page.evaluate(() => {
          if (window.gc) window.gc();
        });

        // Check memory growth
        const currentMemory = await getMemoryUsage(page);
        const growth = (currentMemory - initialMemory) / initialMemory;

        // Alert if memory grew > 50%
        if (growth > 0.5) {
          console.warn(`Memory growth at cycle ${i}: ${(growth * 100).toFixed(2)}%`);
        }
      }
    }

    // Final memory check
    await page.evaluate(() => {
      if (window.gc) window.gc();
    });
    const finalMemory = await getMemoryUsage(page);
    const totalGrowth = (finalMemory - initialMemory) / initialMemory;

    // Memory should not grow more than 100% over 100 cycles
    expect(totalGrowth).toBeLessThan(1.0);
  });

  test('should cleanup Video.js instances on playlist change', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Track Video.js instance count
    const getPlayerCount = () => page.evaluate(() => {
      return document.querySelectorAll('.video-js').length;
    });

    const initialCount = await getPlayerCount();

    // Force 10 playlist reloads
    for (let i = 0; i < 10; i++) {
      await page.evaluate(() => window.PlayerPlaylistSync.forceReload());
      await page.waitForTimeout(1000);
    }

    const finalCount = await getPlayerCount();

    // Should only have 1 Video.js instance
    expect(finalCount).toBe(initialCount);
    expect(finalCount).toBe(1);
  });
});

async function getMemoryUsage(page: Page): Promise<number> {
  const metrics = await page.evaluate(() => {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return 0;
  });
  return metrics;
}
```

---

## 5. Performance Tests

### 5.1 Time to First Frame

**File**: `tests/performance/time-to-first-frame.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Performance: Time to First Frame', () => {
  test('should start playback within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Wait for video to start playing
    const video = page.locator('video');
    await video.waitFor({ state: 'visible' });

    await video.evaluate((v: HTMLVideoElement) => {
      return new Promise((resolve) => {
        const checkPlaying = () => {
          if (!v.paused && v.currentTime > 0) {
            resolve(true);
          } else {
            requestAnimationFrame(checkPlaying);
          }
        };
        checkPlaying();
      });
    });

    const timeToFirstFrame = Date.now() - startTime;

    console.log(`Time to first frame: ${timeToFirstFrame}ms`);
    expect(timeToFirstFrame).toBeLessThan(3000); // 3 seconds threshold
  });

  test('should measure HLS vs direct video startup time', async ({ page }) => {
    const results: Record<string, number> = {};

    // Test HLS stream
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    const hlsStart = Date.now();
    await waitForPlayback(page);
    results.hls = Date.now() - hlsStart;

    // Reset and test MP4
    await page.reload();
    await activateDevice(page);

    const mp4Start = Date.now();
    await waitForPlayback(page);
    results.mp4 = Date.now() - mp4Start;

    console.log('Startup times:', results);

    // MP4 should be faster than HLS
    expect(results.mp4).toBeLessThan(results.hls);
  });
});
```

---

## 6. Device-Specific Tests

### 6.1 WebOS TV Tests

**File**: `tests/device-specific/webos-tv.spec.ts`

```typescript
import { test, expect, devices } from '@playwright/test';

test.use({
  ...devices['Desktop Chrome'],
  userAgent: 'Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.36 Chrome/79.0.3945.79 Safari/537.36 WebAppManager',
});

test.describe('WebOS TV Compatibility', () => {
  test('should detect WebOS platform', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');

    const isWebOS = await page.evaluate(() => {
      return navigator.userAgent.includes('Web0S');
    });

    expect(isWebOS).toBe(true);
  });

  test('should use native HLS playback on WebOS', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Check if using native HLS (no Video.js HLS tech)
    const usesNativeHLS = await page.evaluate(() => {
      const video = document.querySelector('video');
      return video?.canPlayType('application/x-mpegURL') === 'probably';
    });

    expect(usesNativeHLS).toBe(true);
  });

  test('should handle WebOS-specific video formats', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');

    const supportedFormats = await page.evaluate(() => {
      const video = document.createElement('video');
      return {
        mp4: video.canPlayType('video/mp4'),
        webm: video.canPlayType('video/webm'),
        hls: video.canPlayType('application/x-mpegURL'),
      };
    });

    expect(supportedFormats.mp4).toBeTruthy();
    expect(supportedFormats.hls).toBeTruthy();
  });
});
```

---

## 7. Regression Tests

### 7.1 Waiting for Content Screen

**File**: `tests/regression/waiting-content.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Regression: Waiting for Content', () => {
  test('should show waiting screen when no playlist assigned', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Mock empty playlist response
    await page.route('**/api/v1/client/playlist*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          playlist: null,
          has_changes: false,
          message: 'No playlist assigned',
        }),
      });
    });

    // Force sync
    await page.evaluate(() => window.PlayerPlaylistSync.forceReload());
    await page.waitForTimeout(1000);

    // Waiting screen should be visible
    const waitingScreen = page.locator('[data-testid="waiting-for-content"]');
    await expect(waitingScreen).toBeVisible();

    // Should show correct message
    await expect(waitingScreen.locator('text=Waiting for content')).toBeVisible();
  });

  test('should hide waiting screen when playlist assigned', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');
    await activateDevice(page);

    // Initially no playlist
    await page.route('**/api/v1/client/playlist*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ playlist: null, has_changes: false }),
      });
    });

    await page.evaluate(() => window.PlayerPlaylistSync.forceReload());
    await page.waitForTimeout(500);

    const waitingScreen = page.locator('[data-testid="waiting-for-content"]');
    await expect(waitingScreen).toBeVisible();

    // Now assign playlist
    await page.unroute('**/api/v1/client/playlist*');
    await page.route('**/api/v1/client/playlist*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          playlist: createMockPlaylist(3),
          has_changes: true,
        }),
      });
    });

    await page.evaluate(() => window.PlayerPlaylistSync.forceReload());
    await page.waitForTimeout(1000);

    // Waiting screen should be hidden
    await expect(waitingScreen).toBeHidden();

    // Video should be playing
    const video = page.locator('video');
    await expect(video).toBeVisible();
  });
});
```

---

## 8. Test Data Scenarios

### 8.1 Test Playlists

**File**: `tests/fixtures/playlists/mixed-content.json`

```json
{
  "id": 1,
  "name": "Mixed Content Playlist",
  "is_active": true,
  "items": [
    {
      "id": 1,
      "content_id": 101,
      "duration": 15,
      "order": 0,
      "content": {
        "id": 101,
        "name": "Welcome Video",
        "type": "video",
        "file_path": "http://192.168.5.12:8001/uploads/videos/welcome.mp4",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    },
    {
      "id": 2,
      "content_id": 102,
      "duration": 10,
      "order": 1,
      "content": {
        "id": 102,
        "name": "Company Logo",
        "type": "image",
        "file_path": "http://192.168.5.12:8001/uploads/images/logo.png",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    },
    {
      "id": 3,
      "content_id": 103,
      "duration": 30,
      "order": 2,
      "content": {
        "id": 103,
        "name": "Live Stream",
        "type": "video",
        "file_path": "http://192.168.5.12:8001/uploads/streams/live.m3u8",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    },
    {
      "id": 4,
      "content_id": 104,
      "duration": 20,
      "order": 3,
      "content": {
        "id": 104,
        "name": "Promotional Banner",
        "type": "image",
        "file_path": "http://192.168.5.12:8001/uploads/images/promo.jpg",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    },
    {
      "id": 5,
      "content_id": 105,
      "duration": 25,
      "order": 4,
      "content": {
        "id": 105,
        "name": "Product Demo",
        "type": "video",
        "file_path": "http://192.168.5.12:8001/uploads/videos/demo.webm",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    }
  ]
}
```

### 8.2 Error Scenarios

**File**: `tests/fixtures/playlists/error-scenarios.json`

```json
{
  "empty_playlist": {
    "playlist": {
      "id": 1,
      "name": "Empty",
      "is_active": true,
      "items": []
    },
    "has_changes": true
  },
  "no_playlist": {
    "playlist": null,
    "has_changes": false,
    "message": "No playlist assigned to device"
  },
  "corrupted_item": {
    "playlist": {
      "id": 2,
      "name": "Corrupted Item",
      "is_active": true,
      "items": [
        {
          "id": 1,
          "content_id": 201,
          "duration": 10,
          "order": 0,
          "content": {
            "id": 201,
            "name": "404 Video",
            "type": "video",
            "file_path": "http://192.168.5.12:8001/uploads/videos/nonexistent.mp4",
            "url": null,
            "thumbnail_path": null,
            "metadata": null
          }
        }
      ]
    },
    "has_changes": true
  }
}
```

---

## 9. Success Criteria

### 9.1 Unit Tests
- ✅ All PlayerHLS methods have 100% test coverage
- ✅ Video.js initialization is race-condition free
- ✅ Content type detection is accurate
- ✅ Error handlers prevent crashes

### 9.2 Integration Tests
- ✅ Playlist sync → Player flow works without errors
- ✅ No race conditions between sync and initialization
- ✅ Playlist updates trigger correct player reloads
- ✅ Widget overlays render correctly with all content types

### 9.3 E2E Tests
- ✅ Critical path (activation → playback) completes in < 10 seconds
- ✅ All error recovery scenarios handled gracefully
- ✅ Memory usage remains stable over 24-hour simulation
- ✅ Content transitions are smooth (no flicker/delay)

### 9.4 Performance Tests
- ✅ Time to first frame < 3 seconds (95th percentile)
- ✅ Memory usage < 200 MB after 24 hours
- ✅ CPU usage < 30% during playback
- ✅ Playlist transitions < 500ms

### 9.5 Device-Specific Tests
- ✅ WebOS TV: Native HLS playback works
- ✅ Chrome/Firefox: Video.js HLS works
- ✅ Safari: Native HLS fallback works
- ✅ All browsers: MP4/WebM playback works

### 9.6 Regression Tests
- ✅ WaitingForContent screen behavior unchanged
- ✅ UI components render correctly
- ✅ Backend integration unchanged
- ✅ WebSocket commands work as before

---

## 10. CI/CD Integration

### 10.1 GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Start mock backend
        run: npm run test:backend &

      - name: Run integration tests
        run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run performance tests
        run: npm run test:performance

      - name: Analyze results
        run: node scripts/analyze-performance.js
```

### 10.2 NPM Scripts

```json
{
  "scripts": {
    "test": "npm run test:unit && npm run test:integration && npm run test:e2e",
    "test:unit": "vitest run --coverage",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:performance": "playwright test --grep @performance",
    "test:regression": "playwright test --grep @regression",
    "test:watch": "vitest watch",
    "test:debug": "vitest --inspect-brk --no-file-parallelism"
  }
}
```

---

## 11. Reporting & Metrics

### 11.1 Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| PlayerHLS | 95%+ |
| PlayerPlaylistSync | 90%+ |
| Content Detection | 100% |
| Error Handlers | 90%+ |
| Overall | 85%+ |

### 11.2 Performance Benchmarks

| Metric | Target | Threshold |
|--------|--------|-----------|
| Time to First Frame | < 2s | < 3s |
| Memory (24h) | < 150 MB | < 200 MB |
| CPU Usage | < 20% | < 30% |
| Transition Time | < 300ms | < 500ms |

### 11.3 Test Execution Time

| Suite | Target | Threshold |
|-------|--------|-----------|
| Unit Tests | < 30s | < 60s |
| Integration Tests | < 2min | < 5min |
| E2E Tests | < 10min | < 15min |
| Full Suite | < 15min | < 25min |

---

## 12. Migration Checklist

- [ ] Setup test infrastructure (Vitest, Playwright, MSW)
- [ ] Write unit tests for PlayerHLS class
- [ ] Write integration tests for sync → player flow
- [ ] Write E2E critical path test
- [ ] Write error recovery tests
- [ ] Write memory leak detection test
- [ ] Write performance tests
- [ ] Write device-specific tests (WebOS, Chrome, Firefox, Safari)
- [ ] Write regression tests
- [ ] Setup CI/CD pipeline
- [ ] Achieve 85%+ test coverage
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Migration deployed to staging
- [ ] Soak test (24 hours) on staging
- [ ] Migration deployed to production

---

## Conclusion

This comprehensive testing strategy ensures the Video.js migration is robust, performant, and free of race conditions. By covering unit, integration, E2E, performance, and device-specific scenarios, we can confidently deploy the new player implementation across all platforms.

**Key Focus Areas:**
1. Race-condition prevention (PlayerHLS initialization before use)
2. Memory leak detection (long-running playlist tests)
3. Error recovery (network failures, corrupted content)
4. Cross-platform compatibility (WebOS TV, browsers)
5. Performance benchmarks (time to first frame, CPU, memory)

All test suites should be run in CI/CD before merging to main branch.
