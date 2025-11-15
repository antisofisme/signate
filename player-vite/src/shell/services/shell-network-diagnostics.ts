/**
 * Shell Network Diagnostics
 * Network diagnostics and performance testing utilities
 *
 * @features
 * - Speed test (download/upload)
 * - Ping test (latency measurement)
 * - Network quality assessment
 * - Report results to backend
 * - Configurable test parameters
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { config } from '@shared/config';
import { SharedAPIClient } from '@shared/api/shared-api-client';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Speed test result
 */
export interface SpeedTestResult {
  downloadSpeed: number; // Mbps
  uploadSpeed: number; // Mbps
  latency: number; // milliseconds
  jitter: number; // milliseconds
  packetLoss: number; // percentage
  timestamp: string;
  duration: number; // seconds
}

/**
 * Ping test result
 */
export interface PingTestResult {
  host: string;
  latency: number; // milliseconds
  success: boolean;
  timestamp: string;
}

/**
 * Network quality level
 */
export type NetworkQuality = 'excellent' | 'good' | 'fair' | 'poor' | 'offline';

/**
 * Network diagnostics options
 */
export interface DiagnosticsOptions {
  testDuration?: number; // seconds
  testFileSize?: number; // MB
  maxConcurrentRequests?: number;
  reportToBackend?: boolean;
}

/**
 * Shell Network Diagnostics Class
 * Singleton pattern for network testing
 */
class ShellNetworkDiagnosticsClass {
  private testInProgress = false;
  private readonly defaultTestDuration = 10; // seconds
  private readonly defaultTestFileSize = 1; // MB

  /**
   * Run speed test
   */
  async runSpeedTest(options?: DiagnosticsOptions): Promise<SpeedTestResult> {
    if (this.testInProgress) {
      throw new Error('Test already in progress');
    }

    this.testInProgress = true;

    const {
      testDuration = this.defaultTestDuration,
      testFileSize = this.defaultTestFileSize,
      reportToBackend = true,
    } = options || {};

    SharedLogger.log('[NetworkDiagnostics] Starting speed test...');
    SharedEventBus.emit('network:test:start', { type: 'speed' });

    try {
      const startTime = Date.now();

      // Run download test
      const downloadSpeed = await this.testDownloadSpeed(testDuration, testFileSize);

      // Run upload test
      const uploadSpeed = await this.testUploadSpeed(testDuration, testFileSize);

      // Run latency test
      const { latency, jitter } = await this.testLatency();

      // Calculate packet loss (simplified)
      const packetLoss = await this.testPacketLoss();

      const duration = (Date.now() - startTime) / 1000;

      const result: SpeedTestResult = {
        downloadSpeed,
        uploadSpeed,
        latency,
        jitter,
        packetLoss,
        timestamp: new Date().toISOString(),
        duration,
      };

      SharedLogger.log('[NetworkDiagnostics] Speed test completed:', result);
      SharedEventBus.emit('network:test:complete', { type: 'speed', result });

      // Report to backend
      if (reportToBackend) {
        await this.reportSpeedTest(result);
      }

      return result;
    } catch (error) {
      SharedLogger.error('[NetworkDiagnostics] Speed test failed:', error);
      SharedEventBus.emit('network:test:error', { type: 'speed', error });
      throw error;
    } finally {
      this.testInProgress = false;
    }
  }

  /**
   * Test download speed
   */
  private async testDownloadSpeed(duration: number, fileSizeMB: number): Promise<number> {
    const testUrl = `${config.api.baseURL}/api/speedtest/download?size=${fileSizeMB}`;
    const startTime = Date.now();
    let totalBytes = 0;
    const endTime = startTime + duration * 1000;

    try {
      while (Date.now() < endTime) {
        const response = await fetch(testUrl, {
          method: 'GET',
          cache: 'no-cache',
        });

        if (!response.ok) {
          throw new Error(`Download test failed: ${response.statusText}`);
        }

        const blob = await response.blob();
        totalBytes += blob.size;
      }

      const durationSeconds = (Date.now() - startTime) / 1000;
      const speedMbps = (totalBytes * 8) / (durationSeconds * 1000000);

      SharedLogger.log(`[NetworkDiagnostics] Download speed: ${speedMbps.toFixed(2)} Mbps`);
      return parseFloat(speedMbps.toFixed(2));
    } catch (error) {
      SharedLogger.error('[NetworkDiagnostics] Download test error:', error);
      return 0;
    }
  }

  /**
   * Test upload speed
   */
  private async testUploadSpeed(duration: number, fileSizeMB: number): Promise<number> {
    const testUrl = `${config.api.baseURL}/api/speedtest/upload`;
    const startTime = Date.now();
    let totalBytes = 0;
    const endTime = startTime + duration * 1000;

    // Create test data
    const testData = new Uint8Array(fileSizeMB * 1024 * 1024);

    try {
      while (Date.now() < endTime) {
        const response = await fetch(testUrl, {
          method: 'POST',
          body: testData,
          cache: 'no-cache',
        });

        if (!response.ok) {
          throw new Error(`Upload test failed: ${response.statusText}`);
        }

        totalBytes += testData.length;
      }

      const durationSeconds = (Date.now() - startTime) / 1000;
      const speedMbps = (totalBytes * 8) / (durationSeconds * 1000000);

      SharedLogger.log(`[NetworkDiagnostics] Upload speed: ${speedMbps.toFixed(2)} Mbps`);
      return parseFloat(speedMbps.toFixed(2));
    } catch (error) {
      SharedLogger.error('[NetworkDiagnostics] Upload test error:', error);
      return 0;
    }
  }

  /**
   * Test latency and jitter
   */
  private async testLatency(samples = 10): Promise<{ latency: number; jitter: number }> {
    const pingUrl = `${config.api.baseURL}/api/health`;
    const latencies: number[] = [];

    for (let i = 0; i < samples; i++) {
      const result = await this.ping(pingUrl);
      if (result.success) {
        latencies.push(result.latency);
      }

      // Wait 100ms between pings
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    if (latencies.length === 0) {
      return { latency: 0, jitter: 0 };
    }

    // Calculate average latency
    const latency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length;

    // Calculate jitter (variance in latency)
    const jitter =
      latencies.reduce((sum, l) => sum + Math.abs(l - latency), 0) / latencies.length;

    return {
      latency: parseFloat(latency.toFixed(2)),
      jitter: parseFloat(jitter.toFixed(2)),
    };
  }

  /**
   * Test packet loss
   */
  private async testPacketLoss(samples = 20): Promise<number> {
    const pingUrl = `${config.api.baseURL}/api/health`;
    let successCount = 0;

    for (let i = 0; i < samples; i++) {
      const result = await this.ping(pingUrl);
      if (result.success) {
        successCount++;
      }

      // Wait 50ms between pings
      await new Promise((resolve) => setTimeout(resolve, 50));
    }

    const loss = ((samples - successCount) / samples) * 100;
    return parseFloat(loss.toFixed(2));
  }

  /**
   * Ping a URL
   */
  async ping(url: string, timeout = 5000): Promise<PingTestResult> {
    const startTime = Date.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-cache',
      });

      clearTimeout(timeoutId);

      const latency = Date.now() - startTime;

      return {
        host: url,
        latency,
        success: response.ok,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        host: url,
        latency: Date.now() - startTime,
        success: false,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Assess network quality based on metrics
   */
  assessNetworkQuality(result: SpeedTestResult): NetworkQuality {
    if (result.downloadSpeed === 0) {
      return 'offline';
    }

    if (result.downloadSpeed >= 10 && result.latency < 50 && result.packetLoss < 1) {
      return 'excellent';
    }

    if (result.downloadSpeed >= 5 && result.latency < 100 && result.packetLoss < 3) {
      return 'good';
    }

    if (result.downloadSpeed >= 2 && result.latency < 200 && result.packetLoss < 5) {
      return 'fair';
    }

    return 'poor';
  }

  /**
   * Report speed test to backend
   */
  private async reportSpeedTest(result: SpeedTestResult): Promise<void> {
    try {
      const deviceId = localStorage.getItem('device_id');
      if (!deviceId) {
        SharedLogger.warn('[NetworkDiagnostics] No device ID, skipping report');
        return;
      }

      await SharedAPIClient.post('/api/client/speedtest', {
        device_id: parseInt(deviceId, 10),
        download_speed: result.downloadSpeed,
        upload_speed: result.uploadSpeed,
        latency: result.latency,
        jitter: result.jitter,
        packet_loss: result.packetLoss,
        timestamp: result.timestamp,
      });

      SharedLogger.log('[NetworkDiagnostics] Speed test reported to backend');
    } catch (error) {
      SharedLogger.error('[NetworkDiagnostics] Failed to report speed test:', error);
    }
  }

  /**
   * Check if test is in progress
   */
  isTestInProgress(): boolean {
    return this.testInProgress;
  }

  /**
   * Get network info (for debugging)
   */
  getNetworkInfo(): {
    online: boolean;
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
  } {
    // @ts-ignore - navigator.connection is not standard
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

    return {
      online: navigator.onLine,
      effectiveType: connection?.effectiveType,
      downlink: connection?.downlink,
      rtt: connection?.rtt,
    };
  }
}

// Export singleton instance
export const ShellNetworkDiagnostics = new ShellNetworkDiagnosticsClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellNetworkDiagnostics: typeof ShellNetworkDiagnostics;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellNetworkDiagnostics', ShellNetworkDiagnostics);
}
