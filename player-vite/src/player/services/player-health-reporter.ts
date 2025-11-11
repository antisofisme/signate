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

/**
 * Health Metrics Interface
 */
export interface HealthMetrics {
  // System metrics
  cpu_usage: number | null;
  memory_usage: number | null;
  memory_total_mb: number | null;
  memory_used_mb: number | null;
  disk_usage: number | null;
  disk_total_gb: number | null;
  disk_used_gb: number | null;

  // Network metrics
  network_latency_ms: number | null;
  network_download_mbps: number | null;
  network_upload_mbps: number | null;
  connection_quality: string;

  // Display metrics
  display_resolution: string;
  display_refresh_rate: number;
  gpu_usage: number | null;

  // Player metrics
  player_version: string;
  player_uptime_hours: number;
  content_errors_count: number;
  last_error_message: string | null;
  last_error_at: string | null;

  // Metadata
  metadata: {
    user_agent: string;
    platform: string;
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
      await SharedAPIClient.post(`/devices/${deviceId}/health`, metrics);

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
   */
  async collectMetrics(): Promise<HealthMetrics> {
    const metrics: HealthMetrics = {
      // System metrics
      cpu_usage: await this.getCPUUsage(),
      memory_usage: await this.getMemoryUsage(),
      memory_total_mb: await this.getMemoryTotal(),
      memory_used_mb: await this.getMemoryUsed(),
      disk_usage: await this.getDiskUsage(),
      disk_total_gb: await this.getDiskTotal(),
      disk_used_gb: await this.getDiskUsed(),

      // Network metrics
      network_latency_ms: await this.measureLatency(),
      network_download_mbps: await this.getDownloadSpeed(),
      network_upload_mbps: await this.getUploadSpeed(),
      connection_quality: await this.getConnectionQuality(),

      // Display metrics
      display_resolution: this.getDisplayResolution(),
      display_refresh_rate: this.getRefreshRate(),
      gpu_usage: await this.getGPUUsage(),

      // Player metrics
      player_version: this.getPlayerVersion(),
      player_uptime_hours: this.getUptimeHours(),
      content_errors_count: this.errorCount,
      last_error_message: this.lastError?.message ?? null,
      last_error_at: this.lastError?.timestamp ?? null,

      // Metadata
      metadata: {
        user_agent: navigator.userAgent,
        platform: this.detectPlatform(),
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
   * Get upload speed estimate
   */
  async getUploadSpeed(): Promise<number | null> {
    try {
      // Browser API doesn't provide upload speed
      // Estimate as 20% of download speed
      const downlink = (navigator as any).connection?.downlink;
      if (downlink) {
        return Math.round(downlink * 0.2 * 100) / 100;
      }
      return null;
    } catch (error) {
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
   * Get display refresh rate (estimated)
   */
  getRefreshRate(): number {
    // Most displays are 60Hz, some are 120Hz
    // Browser doesn't provide this info accurately
    return 60;
  }

  /**
   * Get GPU usage (not available in browser)
   */
  async getGPUUsage(): Promise<number | null> {
    // Browser doesn't provide GPU usage
    return null;
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
