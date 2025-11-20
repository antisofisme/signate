/**
 * E2E Test Helpers
 * Playwright utility functions for player testing
 */

import { Page, expect } from '@playwright/test';

/**
 * Get activation code from backend
 */
export async function getActivationCode(): Promise<string> {
  // In real tests, this would call the backend API to generate a code
  // For now, return a mock code
  return '123456';
}

/**
 * Activate device with code
 */
export async function activateDevice(page: Page): Promise<void> {
  const code = await getActivationCode();

  await page.waitForSelector('[data-testid="activation-screen"]', {
    timeout: 5000,
  });

  await page.fill('[data-testid="activation-input"]', code);
  await page.click('[data-testid="activate-button"]');

  await expect(page.locator('[data-testid="activation-success"]')).toBeVisible({
    timeout: 5000,
  });

  await expect(page.locator('[data-testid="activation-screen"]')).toBeHidden({
    timeout: 2000,
  });
}

/**
 * Wait for video playback to start
 */
export async function waitForPlayback(page: Page): Promise<void> {
  const video = page.locator('video');
  await video.waitFor({ state: 'visible', timeout: 10000 });

  await video.evaluate((v: HTMLVideoElement) => {
    return new Promise<void>((resolve) => {
      const checkPlaying = () => {
        if (!v.paused && v.currentTime > 0) {
          resolve();
        } else {
          requestAnimationFrame(checkPlaying);
        }
      };
      checkPlaying();
    });
  });
}

/**
 * Wait for content transition (detect currentTime reset)
 */
export async function waitForContentTransition(
  page: Page,
  timeout = 30000
): Promise<void> {
  const video = page.locator('video');

  const startTime = await video.evaluate((v: HTMLVideoElement) => v.currentTime);

  await video.evaluate(
    (v: HTMLVideoElement, [initialTime, maxWait]) => {
      return new Promise<void>((resolve, reject) => {
        const startCheck = Date.now();

        const checkTransition = () => {
          // Content transitioned if currentTime reset to near 0
          if (v.currentTime < initialTime && v.currentTime < 5) {
            resolve();
            return;
          }

          // Timeout check
          if (Date.now() - startCheck > maxWait) {
            reject(new Error('Content transition timeout'));
            return;
          }

          requestAnimationFrame(checkTransition);
        };

        checkTransition();
      });
    },
    [startTime, timeout]
  );
}

/**
 * Get memory usage from page
 */
export async function getMemoryUsage(page: Page): Promise<number> {
  return await page.evaluate(() => {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return 0;
  });
}

/**
 * Create mock playlist for testing
 */
export function createMockPlaylist(itemCount: number) {
  const items = [];

  for (let i = 0; i < itemCount; i++) {
    items.push({
      id: i + 1,
      content_id: i + 100,
      duration: 10,
      order: i,
      content: {
        id: i + 100,
        name: `Test Content ${i + 1}`,
        type: 'video',
        file_path: `http://192.168.5.12:8001/uploads/videos/test${i + 1}.mp4`,
        url: null,
        thumbnail_path: null,
        metadata: null,
      },
    });
  }

  return {
    id: 1,
    name: 'Test Playlist',
    is_active: true,
    items,
  };
}

/**
 * Create valid playlist item
 */
export function createValidItem(id: number) {
  return {
    id,
    content_id: id + 100,
    duration: 10,
    order: id - 1,
    content: {
      id: id + 100,
      name: `Valid Content ${id}`,
      type: 'video',
      file_path: `http://192.168.5.12:8001/uploads/videos/valid${id}.mp4`,
      url: null,
      thumbnail_path: null,
      metadata: null,
    },
  };
}

/**
 * Create corrupted playlist item (404)
 */
export function createCorruptedItem(id: number) {
  return {
    id,
    content_id: id + 100,
    duration: 10,
    order: id - 1,
    content: {
      id: id + 100,
      name: `Corrupted Content ${id}`,
      type: 'video',
      file_path: 'http://192.168.5.12:8001/uploads/videos/nonexistent.mp4',
      url: null,
      thumbnail_path: null,
      metadata: null,
    },
  };
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
