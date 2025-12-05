/**
 * Player Performance Metrics Service
 * Tracks advanced performance metrics for monitoring
 *
 * Phase 4: Performance Metrics Implementation
 *
 * @features
 * - FPS measurement via requestAnimationFrame
 * - Long tasks tracking via PerformanceObserver
 * - CPU pressure via Compute Pressure API (Chrome 125+)
 * - Time to First Byte (TTFB) measurement
 * - Page load time tracking
 */

import { SharedLogger } from '@shared/logger';

/**
 * Performance Metrics Interface
 */
export interface PerformanceMetrics {
  // Real-time metrics
  fps_current: number;
  long_tasks_count: number;

  // CPU pressure (Compute Pressure API)
  cpu_pressure: string | null;  // "nominal" | "fair" | "serious" | "critical" | null

  // Navigation timing
  ttfb_ms: number | null;
  page_load_time_ms: number | null;
  dom_content_loaded_ms: number | null;
}

/**
 * Player Performance Metrics Class
 * Singleton pattern for tracking performance metrics
 */
class PlayerPerformanceMetricsClass {
  // FPS tracking
  private fpsFrameCount = 0;
  private fpsLastTime = performance.now();
  private currentFps = 60;
  private fpsAnimationId: number | null = null;

  // Long tasks tracking
  private longTasksCount = 0;
  private longTaskObserver: PerformanceObserver | null = null;

  // CPU pressure tracking (Compute Pressure API)
  private cpuPressure: string | null = null;
  private pressureObserver: any = null;  // PressureObserver type not in TS yet

  // Navigation timing (cached on load)
  private ttfbMs: number | null = null;
  private pageLoadTimeMs: number | null = null;
  private domContentLoadedMs: number | null = null;

  // Initialization flag
  private initialized = false;

  /**
   * Initialize performance metrics tracking
   */
  initialize(): void {
    if (this.initialized) {
      SharedLogger.warn('[PerformanceMetrics] Already initialized');
      return;
    }

    SharedLogger.log('[PerformanceMetrics] 📊 Initializing performance metrics tracking');

    // Start FPS measurement
    this.startFpsMeasurement();

    // Start long tasks tracking
    this.startLongTasksTracking();

    // Start CPU pressure monitoring (if supported)
    this.startCpuPressureMonitoring();

    // Capture navigation timing (once)
    this.captureNavigationTiming();

    this.initialized = true;
    SharedLogger.log('[PerformanceMetrics] ✅ Performance metrics tracking initialized');
  }

  /**
   * Start FPS measurement using requestAnimationFrame
   */
  private startFpsMeasurement(): void {
    const measureFps = (timestamp: number): void => {
      this.fpsFrameCount++;

      const elapsed = timestamp - this.fpsLastTime;

      // Calculate FPS every second
      if (elapsed >= 1000) {
        this.currentFps = Math.round((this.fpsFrameCount * 1000) / elapsed);
        this.fpsFrameCount = 0;
        this.fpsLastTime = timestamp;
      }

      this.fpsAnimationId = requestAnimationFrame(measureFps);
    };

    this.fpsAnimationId = requestAnimationFrame(measureFps);
    SharedLogger.log('[PerformanceMetrics] 🎬 FPS measurement started');
  }

  /**
   * Stop FPS measurement
   */
  private stopFpsMeasurement(): void {
    if (this.fpsAnimationId !== null) {
      cancelAnimationFrame(this.fpsAnimationId);
      this.fpsAnimationId = null;
    }
  }

  /**
   * Start long tasks tracking using PerformanceObserver
   * Long tasks are tasks that take > 50ms and can cause UI jank
   */
  private startLongTasksTracking(): void {
    try {
      if (!('PerformanceObserver' in window)) {
        SharedLogger.warn('[PerformanceMetrics] PerformanceObserver not supported');
        return;
      }

      this.longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.longTasksCount++;
          SharedLogger.warn(
            `[PerformanceMetrics] ⚠️ Long task detected: ${entry.duration.toFixed(0)}ms (total: ${this.longTasksCount})`
          );
        }
      });

      // 'longtask' type tracks tasks > 50ms
      this.longTaskObserver.observe({ type: 'longtask', buffered: true });
      SharedLogger.log('[PerformanceMetrics] 🕐 Long tasks tracking started');
    } catch (error) {
      SharedLogger.warn('[PerformanceMetrics] Long task tracking not supported:', error);
    }
  }

  /**
   * Stop long tasks tracking
   */
  private stopLongTasksTracking(): void {
    if (this.longTaskObserver) {
      this.longTaskObserver.disconnect();
      this.longTaskObserver = null;
    }
  }

  /**
   * Start CPU pressure monitoring using Compute Pressure API
   * Available in Chrome 125+, Edge 125+
   *
   * States: "nominal" | "fair" | "serious" | "critical"
   * - nominal: System running smoothly
   * - fair: Some thermal pressure, still usable
   * - serious: Noticeable performance impact
   * - critical: System may throttle heavily
   */
  private startCpuPressureMonitoring(): void {
    try {
      // Check if Compute Pressure API is available
      if (!('PressureObserver' in window)) {
        SharedLogger.log('[PerformanceMetrics] Compute Pressure API not supported, using fallback');
        return;
      }

      const PressureObserver = (window as any).PressureObserver;

      this.pressureObserver = new PressureObserver((records: any[]) => {
        if (records.length > 0) {
          const latestRecord = records[records.length - 1];
          this.cpuPressure = latestRecord.state;
          SharedLogger.log(`[PerformanceMetrics] 💻 CPU pressure: ${this.cpuPressure}`);
        }
      });

      // Observe CPU pressure with 1 second sample interval
      this.pressureObserver.observe('cpu', { sampleInterval: 1000 });
      SharedLogger.log('[PerformanceMetrics] 💻 CPU pressure monitoring started (Compute Pressure API)');
    } catch (error) {
      SharedLogger.log('[PerformanceMetrics] CPU pressure monitoring not available:', error);
    }
  }

  /**
   * Stop CPU pressure monitoring
   */
  private stopCpuPressureMonitoring(): void {
    if (this.pressureObserver) {
      try {
        this.pressureObserver.disconnect();
      } catch (error) {
        // Ignore errors during cleanup
      }
      this.pressureObserver = null;
    }
  }

  /**
   * Capture navigation timing metrics (called once on init)
   */
  private captureNavigationTiming(): void {
    try {
      // Wait for load event to complete
      if (document.readyState === 'complete') {
        this.measureNavigationTiming();
      } else {
        window.addEventListener('load', () => {
          // Small delay to ensure all timing data is available
          setTimeout(() => this.measureNavigationTiming(), 100);
        });
      }
    } catch (error) {
      SharedLogger.warn('[PerformanceMetrics] Navigation timing capture failed:', error);
    }
  }

  /**
   * Measure navigation timing metrics
   */
  private measureNavigationTiming(): void {
    try {
      const entries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];

      if (entries.length > 0) {
        const navTiming = entries[0];

        // Time to First Byte (TTFB)
        // responseStart - requestStart (or fetchStart for cached)
        this.ttfbMs = Math.round(navTiming.responseStart - navTiming.requestStart);
        if (this.ttfbMs < 0) {
          // For cached responses, use responseStart - fetchStart
          this.ttfbMs = Math.round(navTiming.responseStart - navTiming.fetchStart);
        }

        // DOM Content Loaded
        this.domContentLoadedMs = Math.round(
          navTiming.domContentLoadedEventEnd - navTiming.domContentLoadedEventStart
        );

        // Page Load Time (total time from navigation start to load complete)
        this.pageLoadTimeMs = Math.round(navTiming.loadEventEnd - navTiming.fetchStart);

        SharedLogger.log('[PerformanceMetrics] 📈 Navigation timing captured:', {
          ttfb_ms: this.ttfbMs,
          dom_content_loaded_ms: this.domContentLoadedMs,
          page_load_time_ms: this.pageLoadTimeMs,
        });
      }
    } catch (error) {
      SharedLogger.warn('[PerformanceMetrics] Failed to measure navigation timing:', error);
    }
  }

  /**
   * Get current FPS
   */
  getFps(): number {
    return this.currentFps;
  }

  /**
   * Get long tasks count
   */
  getLongTasksCount(): number {
    return this.longTasksCount;
  }

  /**
   * Get CPU pressure state
   * Returns: "nominal" | "fair" | "serious" | "critical" | null
   */
  getCpuPressure(): string | null {
    return this.cpuPressure;
  }

  /**
   * Get TTFB in milliseconds
   */
  getTtfbMs(): number | null {
    return this.ttfbMs;
  }

  /**
   * Get page load time in milliseconds
   */
  getPageLoadTimeMs(): number | null {
    return this.pageLoadTimeMs;
  }

  /**
   * Get all performance metrics
   */
  getMetrics(): PerformanceMetrics {
    return {
      fps_current: this.currentFps,
      long_tasks_count: this.longTasksCount,
      cpu_pressure: this.cpuPressure,
      ttfb_ms: this.ttfbMs,
      page_load_time_ms: this.pageLoadTimeMs,
      dom_content_loaded_ms: this.domContentLoadedMs,
    };
  }

  /**
   * Reset counters (for testing or session reset)
   */
  resetCounters(): void {
    this.longTasksCount = 0;
    SharedLogger.log('[PerformanceMetrics] ♻️ Counters reset');
  }

  /**
   * Get summary string for logging
   */
  getSummary(): string {
    const metrics = this.getMetrics();
    return `FPS: ${metrics.fps_current}, Long Tasks: ${metrics.long_tasks_count}, ` +
           `CPU: ${metrics.cpu_pressure || 'N/A'}, TTFB: ${metrics.ttfb_ms || 'N/A'}ms`;
  }

  /**
   * Stop all monitoring and cleanup
   */
  destroy(): void {
    this.stopFpsMeasurement();
    this.stopLongTasksTracking();
    this.stopCpuPressureMonitoring();
    this.initialized = false;
    SharedLogger.log('[PerformanceMetrics] 🗑️ Destroyed');
  }
}

// Export singleton instance
export const PlayerPerformanceMetrics = new PlayerPerformanceMetricsClass();

// Register to ServiceRegistry for global access
import { ServiceRegistry } from '@shared/services/service-registry';
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerPerformanceMetrics', PlayerPerformanceMetrics);
}
