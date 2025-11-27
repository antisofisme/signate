/**
 * E2E Test: Critical Path Sample
 * Demonstrates critical path testing approach
 *
 * NOTE: This is a sample test. Full implementation requires:
 * 1. Backend API endpoints for device activation
 * 2. Video.js migration completed
 * 3. Test data (videos, playlists) on test server
 */

import { test, expect } from '@playwright/test';
import {
  activateDevice,
  waitForPlayback,
  waitForContentTransition,
  createMockPlaylist,
} from './helpers';

test.describe('Sample Critical Path Test', () => {
  test.skip('should complete activation and playback flow', async ({ page }) => {
    // SKIP: This test requires full Video.js migration to be complete
    // It demonstrates the testing approach

    // 1. Navigate to player
    await page.goto('http://192.168.5.12:8080');

    // 2. Should show activation screen
    await expect(page.locator('[data-testid="activation-screen"]')).toBeVisible();

    // 3. Activate device
    await activateDevice(page);

    // 4. Wait for playback to start
    await waitForPlayback(page);

    // 5. Verify video element
    const video = page.locator('video');
    await expect(video).toBeVisible();

    // 6. Check playing state
    const isPlaying = await video.evaluate((v: HTMLVideoElement) => {
      return !v.paused && v.currentTime > 0;
    });
    expect(isPlaying).toBe(true);
  });

  test('should load test page successfully', async ({ page }) => {
    // Basic smoke test - verify player page loads
    await page.goto('http://192.168.5.12:8080');

    // Page should load without errors
    await expect(page).toHaveTitle(/Digital Signage Player/i);
  });

  test('should have video element in DOM', async ({ page }) => {
    await page.goto('http://192.168.5.12:8080');

    // Wait for app to initialize
    await page.waitForTimeout(2000);

    // Video element should exist
    const video = page.locator('video');
    await expect(video).toBeAttached({ timeout: 5000 });
  });
});
