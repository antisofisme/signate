/**
 * Network Speed Test Service
 * Measures download/upload speed automatically every hour
 *
 * @features
 * - Automatic speed test every 1 hour
 * - Manual trigger support (from CMS)
 * - Logs results to ConnectionLogger
 * - Lightweight test using HEAD requests
 */

import { SharedLogger } from '@shared/logger';
import { config } from '@shared/config';
import { ConnectionLogger } from './connection-logger';

interface SpeedTestResult {
  downloadSpeedMbps: number;
  uploadSpeedMbps: number;
  latencyMs: number;
  timestamp: number;
}

class NetworkSpeedTestClass {
  private testInterval: number | null = null;
  private readonly TEST_INTERVAL_MS = 60 * 60 * 1000; // 1 hour
  private isTesting: boolean = false;

  /**
   * Initialize speed test service
   */
  init(): void {
    // Run first test after 30 seconds (quick initial test)
    setTimeout(() => {
      this.runSpeedTest();
    }, 30 * 1000);

    // Then test every hour
    this.testInterval = window.setInterval(() => {
      this.runSpeedTest();
    }, this.TEST_INTERVAL_MS);

    SharedLogger.log('[NetworkSpeedTest] ✅ Initialized (tests every 1 hour)');
  }

  /**
   * Run speed test (can be called manually)
   */
  async runSpeedTest(trigger: 'auto' | 'manual' = 'auto'): Promise<SpeedTestResult | null> {
    if (this.isTesting) {
      SharedLogger.warn('[NetworkSpeedTest] Test already in progress');
      return null;
    }

    this.isTesting = true;
    SharedLogger.log('[NetworkSpeedTest] 🚀 Starting speed test...', `(${trigger})`);

    try {
      const startTime = Date.now();

      // 1. Test latency
      const latency = await this.testLatency();

      // 2. Test download speed
      const downloadSpeed = await this.testDownloadSpeed();

      // 3. Test upload speed (optional - can be heavy)
      const uploadSpeed = await this.testUploadSpeed();

      const result: SpeedTestResult = {
        downloadSpeedMbps: downloadSpeed,
        uploadSpeedMbps: uploadSpeed,
        latencyMs: latency,
        timestamp: Date.now()
      };

      const duration = Date.now() - startTime;
      SharedLogger.log(
        `[NetworkSpeedTest] ✅ Test completed in ${duration}ms:`,
        `Download: ${downloadSpeed.toFixed(2)} Mbps,`,
        `Upload: ${uploadSpeed.toFixed(2)} Mbps,`,
        `Latency: ${latency}ms`
      );

      // Log to ConnectionLogger
      await ConnectionLogger.log({
        eventType: 'speed_test',
        status: 'tested',
        latencyMs: latency,
        downloadSpeedMbps: downloadSpeed,
        uploadSpeedMbps: uploadSpeed,
        metadata: {
          testDurationMs: duration,
          testMethod: 'cloudflare',
          trigger: trigger
        }
      });

      // Force upload immediately for manual tests (so CMS can see results right away)
      if (trigger === 'manual') {
        SharedLogger.log('[NetworkSpeedTest] Manual test - forcing immediate upload');
        await ConnectionLogger.forceUpload();
      }

      this.isTesting = false;
      return result;
    } catch (error) {
      SharedLogger.error('[NetworkSpeedTest] Test failed:', error);

      // Log error
      await ConnectionLogger.log({
        eventType: 'speed_test',
        status: 'tested',
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        metadata: {
          testFailed: true
        }
      });

      this.isTesting = false;
      return null;
    }
  }

  /**
   * Test latency using ping to API server
   */
  private async testLatency(): Promise<number> {
    const samples: number[] = [];
    const PING_COUNT = 3;

    for (let i = 0; i < PING_COUNT; i++) {
      const startTime = performance.now();

      try {
        await fetch(`${config.api.baseURL}/health`, {
          method: 'HEAD',
          cache: 'no-cache'
        });

        const latency = performance.now() - startTime;
        samples.push(latency);
      } catch (error) {
        SharedLogger.warn(`[NetworkSpeedTest] Ping ${i + 1} failed:`, error);
      }

      // Wait 100ms between pings
      if (i < PING_COUNT - 1) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    if (samples.length === 0) {
      throw new Error('All ping attempts failed');
    }

    // Return average latency
    const avgLatency = samples.reduce((a, b) => a + b, 0) / samples.length;
    return Math.round(avgLatency);
  }

  /**
   * Test download speed
   * Downloads data and measures speed (adaptive size based on connection)
   */
  private async testDownloadSpeed(): Promise<number> {
    try {
      // Test with progressively larger payloads
      const testSizes = [
        { size: 1, duration: 0.5 },   // 1MB for 0.5s
        { size: 5, duration: 1.5 },   // 5MB for 1.5s
        { size: 10, duration: 2.0 }   // 10MB for 2s
      ];

      let bestSpeed = 0;

      for (const test of testSizes) {
        const testUrl = `https://speed.cloudflare.com/__down?bytes=${test.size * 1024 * 1024}`;
        const startTime = performance.now();

        const response = await fetch(testUrl, {
          method: 'GET',
          cache: 'no-cache'
        });

        if (!response.ok) continue;

        // Read response body
        const reader = response.body?.getReader();
        if (!reader) continue;

        let bytesDownloaded = 0;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          bytesDownloaded += value?.length || 0;

          // Stop if taking too long
          if (performance.now() - startTime > test.duration * 1000) {
            reader.cancel();
            break;
          }
        }

        const durationSec = (performance.now() - startTime) / 1000;
        const speedMbps = (bytesDownloaded * 8) / (durationSec * 1_000_000);

        bestSpeed = Math.max(bestSpeed, speedMbps);

        // If speed is good, try larger test
        if (speedMbps < 50) break;
      }

      return Math.max(bestSpeed, 0.01);
    } catch (error) {
      SharedLogger.warn('[NetworkSpeedTest] Download test failed:', error);
      return 0;
    }
  }

  /**
   * Test upload speed with progressively larger payloads
   * Uses Cloudflare upload endpoint for accurate measurement
   */
  private async testUploadSpeed(): Promise<number> {
    try {
      // Test with progressively larger payloads
      const testSizes = [
        { size: 1, duration: 1.0 },   // 1MB for 1s
        { size: 5, duration: 2.0 },   // 5MB for 2s
        { size: 10, duration: 3.0 }   // 10MB for 3s
      ];

      let bestSpeed = 0;

      for (const test of testSizes) {
        const testUrl = `https://speed.cloudflare.com/__up`;

        // Generate random data of specified size
        const dataSize = test.size * 1024 * 1024; // Convert MB to bytes
        const uploadData = new Uint8Array(dataSize);

        // Fill with random data (faster than crypto.getRandomValues for large sizes)
        for (let i = 0; i < uploadData.length; i += 1024) {
          const chunk = Math.min(1024, uploadData.length - i);
          const randomChunk = new Uint8Array(chunk);
          crypto.getRandomValues(randomChunk);
          uploadData.set(randomChunk, i);
        }

        const startTime = performance.now();

        try {
          const response = await fetch(testUrl, {
            method: 'POST',
            body: uploadData,
            cache: 'no-cache',
            signal: AbortSignal.timeout(test.duration * 1000)
          });

          if (!response.ok) continue;

          const durationSec = (performance.now() - startTime) / 1000;
          const speedMbps = (dataSize * 8) / (durationSec * 1_000_000);

          bestSpeed = Math.max(bestSpeed, speedMbps);

          // If upload is slow, don't try larger sizes
          if (speedMbps < 50) break;
        } catch (error: any) {
          // Timeout or network error - use partial data if available
          const durationSec = (performance.now() - startTime) / 1000;
          if (durationSec > 0.1) { // At least 100ms of upload
            const speedMbps = (dataSize * 8) / (durationSec * 1_000_000);
            bestSpeed = Math.max(bestSpeed, speedMbps);
          }
          break;
        }
      }

      return Math.max(bestSpeed, 0.01);
    } catch (error) {
      SharedLogger.warn('[NetworkSpeedTest] Upload test failed:', error);
      return 0;
    }
  }

  /**
   * Manual trigger (called from CMS or manually)
   */
  async triggerManualTest(): Promise<SpeedTestResult | null> {
    SharedLogger.log('[NetworkSpeedTest] Manual test triggered');
    return await this.runSpeedTest('manual');
  }

  /**
   * Stop automatic testing
   */
  stop(): void {
    if (this.testInterval) {
      clearInterval(this.testInterval);
      this.testInterval = null;
      SharedLogger.log('[NetworkSpeedTest] Stopped');
    }
  }

  /**
   * Get last test result from logs
   */
  async getLastTestResult(): Promise<SpeedTestResult | null> {
    try {
      const logs = await ConnectionLogger.getLogs(1, 'speed_test');
      if (logs.length > 0) {
        const log = logs[0];
        return {
          downloadSpeedMbps: log.downloadSpeedMbps || 0,
          uploadSpeedMbps: log.uploadSpeedMbps || 0,
          latencyMs: log.latencyMs || 0,
          timestamp: log.timestamp
        };
      }
      return null;
    } catch (error) {
      SharedLogger.error('[NetworkSpeedTest] Failed to get last result:', error);
      return null;
    }
  }
}

// Export singleton instance
export const NetworkSpeedTest = new NetworkSpeedTestClass();

// Make available globally for manual testing
if (typeof window !== 'undefined') {
  (window as any).NetworkSpeedTest = NetworkSpeedTest;
}
