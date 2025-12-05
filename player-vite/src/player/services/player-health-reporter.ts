/**
 * Player Health Reporter Service
 * Collects and reports device health metrics to backend
 *
 * @features
 * - Reports health metrics every 5 minutes
 * - Collects system metrics (CPU, memory, disk)
 * - Measures network metrics (latency, bandwidth)
 * - Reports display metrics (resolution, refresh rate)
 * - Tracks player metrics (version, uptime, errors)
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { PlayerBehavioralMetrics } from './player-behavioral-metrics';
import { PlayerPerformanceMetrics } from './player-performance-metrics';

/**
 * Health Metrics Interface
 *
 * OPTIMIZED (Phase 2):
 * - Static fields (player_version, user_agent, platform) now sent via /capabilities
 * - Only dynamic metrics sent in health report to reduce payload size
 *
 * ENHANCED (Phase 3):
 * - Added behavioral metrics (stalls, buffers, quality switches, etc.)
 *
 * ENHANCED (Phase 4):
 * - Added performance metrics (FPS, long tasks, CPU pressure, TTFB)
 */
export interface HealthMetrics {
  // System metrics (dynamic)
  cpu_usage: number | null;
  memory_usage: number | null;
  memory_total_mb: number | null;
  memory_used_mb: number | null;
  disk_usage: number | null;
  disk_total_gb: number | null;
  disk_used_gb: number | null;

  // Network metrics (dynamic)
  network_latency_ms: number | null;
  network_download_mbps: number | null;
  network_upload_mbps: number | null;
  dns_resolution_ms: number | null;  // Phase 5: DNS lookup time
  connection_quality: string;

  // Display metrics (semi-static - can change on monitor switch)
  display_resolution: string;
  display_refresh_rate: number;

  // Player metrics (dynamic)
  player_uptime_hours: number;
  content_errors_count: number;
  last_error_message: string | null;
  last_error_at: string | null;

  // Behavioral metrics (Phase 3)
  playback_stalls_count: number;
  buffer_underruns_count: number;
  time_to_first_playback_ms: number | null;
  content_play_count: number;
  quality_switches_count: number;
  content_load_failures_count: number;
  error_rate_percent: number;

  // Performance metrics (Phase 4)
  fps_current: number;
  long_tasks_count: number;
  cpu_pressure: string | null;
  ttfb_ms: number | null;
  page_load_time_ms: number | null;

  // Metadata (minimal - static fields now in /capabilities)
  metadata: {
    online: boolean;
    timestamp: string;
  };
}

/**
 * Player Health Reporter Class
 * Singleton pattern for health reporting
 */
class PlayerHealthReporterClass {
  private reportInterval: number | null = null;
  private running = false;
  private startTime = Date.now();
  private errorCount = 0;
  private lastError: { message: string; timestamp: string } | null = null;

  private readonly REPORT_INTERVAL = 5 * 60 * 1000; // 5 minutes

  /**
   * Start health monitoring
   */
  start(): void {
    if (this.running) {
      SharedLogger.warn('[HealthReporter] Already running');
      return;
    }

    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[HealthReporter] Cannot start - no device_id');
      return;
    }

    SharedLogger.log('[HealthReporter] 🏥 Starting health monitoring...');
    this.running = true;
    this.startTime = Date.now();

    // Initialize performance metrics tracking (Phase 4)
    PlayerPerformanceMetrics.initialize();

    // Report immediately
    void this.reportHealth();

    // Then report periodically
    this.reportInterval = window.setInterval(() => {
      void this.reportHealth();
    }, this.REPORT_INTERVAL);

    SharedLogger.log(`[HealthReporter] ✅ Health monitoring started (reports every ${this.REPORT_INTERVAL / 60000} minutes)`);
  }

  /**
   * Stop health monitoring
   */
  stop(): void {
    if (!this.running) {
      return;
    }

    if (this.reportInterval !== null) {
      clearInterval(this.reportInterval);
      this.reportInterval = null;
    }

    // Cleanup performance metrics (Phase 4)
    PlayerPerformanceMetrics.destroy();

    this.running = false;
    SharedLogger.log('[HealthReporter] ⏹️ Health monitoring stopped');
  }

  /**
   * Report health metrics to backend
   */
  async reportHealth(): Promise<void> {
    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[HealthReporter] Cannot report - no device_id');
      return;
    }

    try {
      SharedLogger.log('[HealthReporter] 📊 Collecting health metrics...');

      // Collect all metrics
      const metrics = await this.collectMetrics();

      // Send to backend
      await SharedAPIClient.post(`${config.api.baseURL}/api/v1/devices/${deviceId}/health`, metrics);

      SharedLogger.log('[HealthReporter] ✅ Health metrics reported successfully');
    } catch (error) {
      this.errorCount++;
      this.lastError = {
        message: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
      };
      SharedLogger.error('[HealthReporter] ❌ Failed to report health:', error);
    }
  }

  /**
   * Collect all health metrics
   *
   * OPTIMIZED (Phase 2):
   * - Removed player_version (now in /capabilities)
   * - Removed user_agent and platform from metadata (now in /capabilities)
   * - Payload reduced from ~19 fields to ~17 fields
   *
   * ENHANCED (Phase 3):
   * - Added behavioral metrics from PlayerBehavioralMetrics service
   *
   * ENHANCED (Phase 4):
   * - Added performance metrics from PlayerPerformanceMetrics service
   */
  async collectMetrics(): Promise<HealthMetrics> {
    // Get behavioral metrics (Phase 3)
    const behavioralMetrics = PlayerBehavioralMetrics.getMetrics();

    // Get performance metrics (Phase 4)
    const performanceMetrics = PlayerPerformanceMetrics.getMetrics();

    const metrics: HealthMetrics = {
      // System metrics (dynamic)
      // NOTE: cpu_usage now supplemented by cpu_pressure from Compute Pressure API
      cpu_usage: await this.getCPUUsage(),
      memory_usage: await this.getMemoryUsage(),
      memory_total_mb: await this.getMemoryTotal(),
      memory_used_mb: await this.getMemoryUsed(),
      disk_usage: await this.getDiskUsage(),
      disk_total_gb: await this.getDiskTotal(),
      disk_used_gb: await this.getDiskUsed(),

      // Network metrics (dynamic)
      network_latency_ms: await this.measureLatency(),
      network_download_mbps: await this.getDownloadSpeed(),
      network_upload_mbps: await this.getUploadSpeed(),
      dns_resolution_ms: this.getDnsResolutionTime(),  // Phase 5
      connection_quality: await this.getConnectionQuality(),

      // Display metrics (semi-static - can change on monitor switch)
      display_resolution: this.getDisplayResolution(),
      display_refresh_rate: await this.getRefreshRate(),

      // Player metrics (dynamic)
      // NOTE: player_version removed - now sent once via /capabilities
      player_uptime_hours: this.getUptimeHours(),
      content_errors_count: this.errorCount,
      last_error_message: this.lastError?.message ?? null,
      last_error_at: this.lastError?.timestamp ?? null,

      // Behavioral metrics (Phase 3)
      playback_stalls_count: behavioralMetrics.playback_stalls_count,
      buffer_underruns_count: behavioralMetrics.buffer_underruns_count,
      time_to_first_playback_ms: behavioralMetrics.time_to_first_playback_ms,
      content_play_count: behavioralMetrics.content_play_count,
      quality_switches_count: behavioralMetrics.quality_switches_count,
      content_load_failures_count: behavioralMetrics.content_load_failures_count,
      error_rate_percent: behavioralMetrics.error_rate_percent,

      // Performance metrics (Phase 4)
      fps_current: performanceMetrics.fps_current,
      long_tasks_count: performanceMetrics.long_tasks_count,
      cpu_pressure: performanceMetrics.cpu_pressure,
      ttfb_ms: performanceMetrics.ttfb_ms,
      page_load_time_ms: performanceMetrics.page_load_time_ms,

      // Metadata (minimal - static fields now in /capabilities)
      // NOTE: user_agent and platform removed - now sent once via /capabilities
      metadata: {
        online: navigator.onLine,
        timestamp: new Date().toISOString(),
      },
    };

    return metrics;
  }

  /**
   * Estimate CPU usage (browser limitation)
   */
  async getCPUUsage(): Promise<number | null> {
    try {
      const start = performance.now();
      let sum = 0;

      // CPU-intensive operation
      for (let i = 0; i < 1000000; i++) {
        sum += Math.sqrt(i);
      }

      const duration = performance.now() - start;

      // Estimate: faster = lower CPU usage, slower = higher CPU usage
      // Baseline: ~10ms on modern CPU = 10% usage
      const estimatedUsage = Math.min(100, (duration / 10) * 10);

      return Math.round(estimatedUsage * 100) / 100; // Round to 2 decimals
    } catch (error) {
      SharedLogger.error('[HealthReporter] Failed to get CPU usage:', error);
      return null;
    }
  }

  /**
   * Get memory usage percentage
   */
  async getMemoryUsage(): Promise<number | null> {
    try {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        const usage = (mem.usedJSHeapSize / mem.jsHeapSizeLimit) * 100;
        return Math.round(usage * 100) / 100;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get total memory in MB
   */
  async getMemoryTotal(): Promise<number | null> {
    try {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        return Math.round(mem.jsHeapSizeLimit / (1024 * 1024));
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get used memory in MB
   */
  async getMemoryUsed(): Promise<number | null> {
    try {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        return Math.round(mem.usedJSHeapSize / (1024 * 1024));
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get disk usage percentage
   */
  async getDiskUsage(): Promise<number | null> {
    try {
      if ('storage' in navigator && 'estimate' in (navigator as any).storage) {
        const estimate = await (navigator as any).storage.estimate();
        const usage = (estimate.usage / estimate.quota) * 100;
        return Math.round(usage * 100) / 100;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get total disk space in GB
   */
  async getDiskTotal(): Promise<number | null> {
    try {
      if ('storage' in navigator && 'estimate' in (navigator as any).storage) {
        const estimate = await (navigator as any).storage.estimate();
        return Math.round(estimate.quota / (1024 * 1024 * 1024));
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get used disk space in GB
   */
  async getDiskUsed(): Promise<number | null> {
    try {
      if ('storage' in navigator && 'estimate' in (navigator as any).storage) {
        const estimate = await (navigator as any).storage.estimate();
        return Math.round((estimate.usage / (1024 * 1024 * 1024)) * 100) / 100;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Measure network latency to backend
   */
  async measureLatency(): Promise<number | null> {
    try {
      const start = performance.now();

      // Ping health endpoint
      await fetch(`${config.api.baseURL}/health`, {
        method: 'HEAD',
        cache: 'no-cache',
      });

      const latency = Math.round(performance.now() - start);
      return latency;
    } catch (error) {
      SharedLogger.error('[HealthReporter] Failed to measure latency:', error);
      return null;
    }
  }

  /**
   * Get download speed estimate
   */
  async getDownloadSpeed(): Promise<number | null> {
    try {
      if ('connection' in navigator && (navigator as any).connection?.downlink) {
        return (navigator as any).connection.downlink; // Mbps
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get upload speed via real upload test
   *
   * Phase 5: Upgraded from fake estimate (20% of download) to real upload test
   * Sends 100KB payload to /api/v1/speed-test/upload and measures actual speed
   */
  async getUploadSpeed(): Promise<number | null> {
    try {
      // Generate 100KB test payload
      const TEST_SIZE_BYTES = 100 * 1024; // 100KB
      const testPayload = new ArrayBuffer(TEST_SIZE_BYTES);

      const startTime = performance.now();

      // POST to speed test endpoint
      const response = await fetch(`${config.api.baseURL}/api/v1/speed-test/upload`, {
        method: 'POST',
        body: testPayload,
        headers: {
          'Content-Type': 'application/octet-stream',
        },
      });

      if (!response.ok) {
        SharedLogger.warn('[HealthReporter] Upload speed test failed:', response.status);
        return this.getFallbackUploadSpeed();
      }

      const result = await response.json();

      // Server returns speed_mbps in response
      if (result.speed_mbps !== undefined) {
        SharedLogger.log(`[HealthReporter] 📤 Real upload speed: ${result.speed_mbps} Mbps`);
        return Math.round(result.speed_mbps * 100) / 100;
      }

      // Fallback: calculate client-side if server doesn't return speed
      const durationSeconds = (performance.now() - startTime) / 1000;
      const speedMbps = (TEST_SIZE_BYTES * 8) / (durationSeconds * 1_000_000);
      return Math.round(speedMbps * 100) / 100;
    } catch (error) {
      SharedLogger.warn('[HealthReporter] Upload speed test error, using fallback:', error);
      return this.getFallbackUploadSpeed();
    }
  }

  /**
   * Fallback upload speed estimate (20% of download)
   * Used when real upload test fails
   */
  private getFallbackUploadSpeed(): number | null {
    try {
      const downlink = (navigator as any).connection?.downlink;
      if (downlink) {
        return Math.round(downlink * 0.2 * 100) / 100;
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Get DNS resolution time using Resource Timing API
   *
   * Phase 5: Added DNS resolution measurement
   * Uses Navigation Timing API to get DNS lookup time from initial page load
   */
  getDnsResolutionTime(): number | null {
    try {
      // Get navigation timing for the initial page load
      const entries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];

      if (entries.length > 0) {
        const navTiming = entries[0];
        const dnsTime = navTiming.domainLookupEnd - navTiming.domainLookupStart;

        // DNS lookup time can be 0 if cached or same-origin
        if (dnsTime >= 0) {
          return Math.round(dnsTime);
        }
      }

      // Alternative: Check recent resource entries for DNS timing
      const resourceEntries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

      // Find the most recent API call to get fresh DNS timing
      const apiEntries = resourceEntries.filter((entry) =>
        entry.name.includes(config.api.baseURL) && entry.domainLookupEnd > 0
      );

      if (apiEntries.length > 0) {
        const latestEntry = apiEntries[apiEntries.length - 1];
        const dnsTime = latestEntry.domainLookupEnd - latestEntry.domainLookupStart;

        if (dnsTime >= 0) {
          return Math.round(dnsTime);
        }
      }

      return null;
    } catch (error) {
      SharedLogger.warn('[HealthReporter] Failed to get DNS resolution time:', error);
      return null;
    }
  }

  /**
   * Determine connection quality based on latency
   */
  async getConnectionQuality(): Promise<string> {
    try {
      const latency = await this.measureLatency();

      if (!latency) return 'unknown';
      if (latency < 50) return 'excellent';
      if (latency < 100) return 'good';
      if (latency < 200) return 'fair';
      if (latency < 500) return 'poor';
      return 'very_poor';
    } catch (error) {
      return 'unknown';
    }
  }

  /**
   * Get display resolution
   */
  getDisplayResolution(): string {
    return `${window.screen.width}x${window.screen.height}`;
  }

  /**
   * Get display refresh rate via requestAnimationFrame detection
   * Measures actual frame rate over 1 second and maps to common refresh rates
   */
  async getRefreshRate(): Promise<number> {
    return new Promise((resolve) => {
      let frameCount = 0;
      const startTime = performance.now();

      const countFrames = (timestamp: number): void => {
        frameCount++;
        if (timestamp - startTime < 1000) {
          requestAnimationFrame(countFrames);
        } else {
          // Map to common refresh rates
          const commonRates = [30, 48, 50, 60, 75, 90, 100, 120, 144, 165, 240];
          const closestRate = commonRates.reduce((prev, curr) =>
            Math.abs(curr - frameCount) < Math.abs(prev - frameCount) ? curr : prev
          );
          resolve(closestRate);
        }
      };

      requestAnimationFrame(countFrames);
    });
  }

  /**
   * Get player version
   */
  getPlayerVersion(): string {
    return config.player.version || '1.0.0';
  }

  /**
   * Get player uptime in hours
   */
  getUptimeHours(): number {
    const uptimeMs = Date.now() - this.startTime;
    const uptimeHours = Math.floor(uptimeMs / (1000 * 60 * 60));
    return uptimeHours;
  }

  /**
   * Detect platform type
   */
  detectPlatform(): string {
    const ua = navigator.userAgent.toLowerCase();

    // TV platforms
    if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
    if (ua.includes('tizen')) return 'Tizen';
    if (ua.includes('android tv')) return 'Android TV';

    // Desktop browsers
    if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
    if (ua.includes('firefox')) return 'Firefox';
    if (ua.includes('chrome')) return 'Chrome';
    if (ua.includes('safari')) return 'Safari';

    return 'Browser';
  }

  /**
   * Record error for health metrics
   */
  recordError(errorMessage: string): void {
    this.errorCount++;
    this.lastError = {
      message: errorMessage,
      timestamp: new Date().toISOString(),
    };
    SharedLogger.log(`[HealthReporter] 📝 Error recorded: ${errorMessage}`);
  }

  /**
   * Reset error count
   */
  resetErrors(): void {
    this.errorCount = 0;
    this.lastError = null;
    SharedLogger.log('[HealthReporter] Error count reset');
  }

  /**
   * Check if health reporter is running
   */
  isRunning(): boolean {
    return this.running;
  }
}

// Export singleton instance
export const PlayerHealthReporter = new PlayerHealthReporterClass();

// Register to ServiceRegistry for global access
import { ServiceRegistry } from '@shared/services/service-registry';
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerHealthReporter', PlayerHealthReporter);
}
