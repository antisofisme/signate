/**
 * Performance Monitoring Module
 *
 * @module performance
 * @description
 * Lightweight performance monitoring for tracking page load, API calls, and resource timing.
 * Uses browser Performance API for accurate measurements.
 *
 * @features
 * - Page load timing (FCP, LCP, DOMContentLoaded)
 * - API call tracking
 * - Resource loading metrics
 * - Custom performance marks
 * - Memory usage monitoring
 * - Performance metrics reporting
 *
 * @usage
 * ```typescript
 * // Track API call
 * performanceMonitor.startMark('api-fetch');
 * await fetch('/api/playlist');
 * performanceMonitor.endMark('api-fetch', 'API Call');
 *
 * // Get performance stats
 * const stats = performanceMonitor.getStats();
 * console.log('Page load time:', stats.pageLoad.total);
 *
 * // Monitor specific operation
 * const timer = performanceMonitor.startTimer('cache-sync');
 * await syncCacheWithPlaylist();
 * timer.end('Cache sync complete');
 * ```
 *
 * @version 2.0.0 (TypeScript)
 */

interface CustomMark {
  start: number;
  end?: number;
  duration?: number;
}

interface CustomTiming {
  name: string;
  label: string;
  duration: number;
  timestamp: string;
}

interface APICall {
  url: string;
  method: string;
  duration: number;
  status: number;
  timestamp: string;
}

interface PageLoadMetrics {
  dns?: number;
  tcp?: number;
  request?: number;
  response?: number;
  domProcessing?: number;
  domContentLoaded?: number;
  total?: number;
  fcp?: number | null;
  lcp?: number | null;
}

interface ResourceMetric {
  name: string;
  type: string;
  duration: number;
  size: number;
  cached: boolean;
}

interface MemoryUsage {
  used: number; // MB
  total: number; // MB
  limit: number; // MB
}

interface PerformanceMetrics {
  pageLoad: PageLoadMetrics;
  apiCalls: APICall[];
  resources: ResourceMetric[];
  customTimings: CustomTiming[];
}

interface Timer {
  end: (label?: string) => number;
}

interface PerformanceStats {
  pageLoad: PageLoadMetrics;
  apiCalls: APICall[];
  customTimings: CustomTiming[];
  resources: ResourceMetric[];
  memory: MemoryUsage | null;
}

interface PerformanceSummary {
  pageLoad: {
    total: number;
    domContentLoaded: number;
    fcp: number;
    lcp: number;
  };
  apiCalls: {
    count: number;
    avgDuration: number;
    slowest: number;
  } | null;
  memory: MemoryUsage | null;
  resourceCount: number;
}

/**
 * Performance Monitor class
 */
class PerformanceMonitor {
  private customMarks: Record<string, CustomMark> = {};
  private metrics: PerformanceMetrics = {
    pageLoad: {},
    apiCalls: [],
    resources: [],
    customTimings: [],
  };

  constructor() {
    // Start monitoring page load
    this.initPageLoadMonitoring();
  }

  /**
   * Initialize page load performance monitoring
   */
  private initPageLoadMonitoring(): void {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        this.recordPageLoadMetrics();
      });
    } else {
      this.recordPageLoadMetrics();
    }

    // Monitor LCP (Largest Contentful Paint)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          this.metrics.pageLoad.lcp = Math.round(
            lastEntry.renderTime || lastEntry.loadTime
          );
        });

        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (error) {
        console.warn('[Performance] LCP monitoring not supported:', error);
      }
    }
  }

  /**
   * Record page load metrics from Navigation Timing API
   */
  private recordPageLoadMetrics(): void {
    if (!performance || !performance.timing) {
      console.warn('[Performance] Navigation Timing API not available');
      return;
    }

    const timing = performance.timing;
    const navigationStart = timing.navigationStart;

    this.metrics.pageLoad = {
      // DNS lookup
      dns: timing.domainLookupEnd - timing.domainLookupStart,

      // TCP connection
      tcp: timing.connectEnd - timing.connectStart,

      // Request + Response
      request: timing.responseStart - timing.requestStart,
      response: timing.responseEnd - timing.responseStart,

      // DOM processing
      domProcessing: timing.domComplete - timing.domLoading,
      domContentLoaded: timing.domContentLoadedEventEnd - navigationStart,

      // Page load complete
      total: timing.loadEventEnd - navigationStart,

      // First paint metrics (if available)
      fcp: this.getFirstContentfulPaint(),
      lcp: this.metrics.pageLoad.lcp || null,
    };

    console.log('[Performance] Page load metrics recorded:', this.metrics.pageLoad);
  }

  /**
   * Get First Contentful Paint (FCP) timing
   */
  private getFirstContentfulPaint(): number | null {
    if (!performance || !performance.getEntriesByType) {
      return null;
    }

    const paintEntries = performance.getEntriesByType('paint');
    const fcpEntry = paintEntries.find(
      (entry) => entry.name === 'first-contentful-paint'
    );

    return fcpEntry ? Math.round(fcpEntry.startTime) : null;
  }

  /**
   * Start performance mark
   * @param name - Mark name
   * @returns Timer object with end() method
   */
  startMark(name: string): Timer {
    const startTime = performance.now();

    this.customMarks[name] = {
      start: startTime,
    };

    // Return timer object for convenience
    return {
      end: (label?: string) => this.endMark(name, label),
    };
  }

  /**
   * End performance mark
   * @param name - Mark name
   * @param label - Optional label for logging
   * @returns Duration in milliseconds
   */
  endMark(name: string, label?: string): number {
    if (!this.customMarks[name]) {
      console.warn(`[Performance] Mark "${name}" not found`);
      return 0;
    }

    const endTime = performance.now();
    const duration = Math.round(endTime - this.customMarks[name].start);

    this.customMarks[name].end = endTime;
    this.customMarks[name].duration = duration;

    // Record to metrics
    this.metrics.customTimings.push({
      name,
      label: label || name,
      duration,
      timestamp: new Date().toISOString(),
    });

    console.log(`[Performance] ${label || name}: ${duration}ms`);

    return duration;
  }

  /**
   * Measure time between two marks
   * @param startMark - Start mark name
   * @param endMark - End mark name
   * @param measureName - Measurement name
   * @returns Duration in milliseconds
   */
  measure(startMark: string, endMark: string, measureName: string): number {
    if (!this.customMarks[startMark] || !this.customMarks[endMark]) {
      console.warn('[Performance] Marks not found for measurement');
      return 0;
    }

    const duration =
      this.customMarks[endMark].start - this.customMarks[startMark].start;

    this.metrics.customTimings.push({
      name: measureName,
      label: measureName,
      duration: Math.round(duration),
      timestamp: new Date().toISOString(),
    });

    return Math.round(duration);
  }

  /**
   * Track API call performance
   * @param url - API endpoint
   * @param method - HTTP method
   * @param duration - Call duration in ms
   * @param status - HTTP status code
   */
  trackAPICall(url: string, method: string, duration: number, status: number): void {
    this.metrics.apiCalls.push({
      url,
      method,
      duration: Math.round(duration),
      status,
      timestamp: new Date().toISOString(),
    });

    // Keep only last 50 API calls to prevent memory growth
    if (this.metrics.apiCalls.length > 50) {
      this.metrics.apiCalls.shift();
    }
  }

  /**
   * Get resource loading metrics
   * @returns Resource timing entries
   */
  getResourceMetrics(): ResourceMetric[] {
    if (!performance || !performance.getEntriesByType) {
      return [];
    }

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

    return resources.map((resource) => ({
      name: resource.name,
      type: resource.initiatorType,
      duration: Math.round(resource.duration),
      size: resource.transferSize || 0,
      cached: resource.transferSize === 0,
    }));
  }

  /**
   * Get memory usage (if available)
   * @returns Memory metrics or null
   */
  getMemoryUsage(): MemoryUsage | null {
    // @ts-ignore - performance.memory is non-standard
    if (!performance || !performance.memory) {
      return null;
    }

    // @ts-ignore - performance.memory is non-standard
    const memory = performance.memory;

    return {
      used: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
      total: Math.round(memory.totalJSHeapSize / 1024 / 1024), // MB
      limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024), // MB
    };
  }

  /**
   * Get all performance statistics
   * @returns Performance stats object
   */
  getStats(): PerformanceStats {
    return {
      pageLoad: this.metrics.pageLoad,
      apiCalls: this.metrics.apiCalls,
      customTimings: this.metrics.customTimings,
      resources: this.getResourceMetrics(),
      memory: this.getMemoryUsage(),
    };
  }

  /**
   * Get performance summary for reporting
   * @returns Performance summary object
   */
  getSummary(): PerformanceSummary {
    const stats = this.getStats();

    const apiCallStats =
      this.metrics.apiCalls.length > 0
        ? {
            count: this.metrics.apiCalls.length,
            avgDuration: Math.round(
              this.metrics.apiCalls.reduce((sum, call) => sum + call.duration, 0) /
                this.metrics.apiCalls.length
            ),
            slowest: Math.max(...this.metrics.apiCalls.map((call) => call.duration)),
          }
        : null;

    return {
      pageLoad: {
        total: stats.pageLoad.total || 0,
        domContentLoaded: stats.pageLoad.domContentLoaded || 0,
        fcp: stats.pageLoad.fcp || 0,
        lcp: stats.pageLoad.lcp || 0,
      },
      apiCalls: apiCallStats,
      memory: stats.memory,
      resourceCount: stats.resources.length,
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.customMarks = {};
    this.metrics = {
      pageLoad: this.metrics.pageLoad, // Keep page load metrics
      apiCalls: [],
      resources: [],
      customTimings: [],
    };

    console.log('[Performance] Metrics cleared');
  }

  /**
   * Start a simple timer (convenience method)
   * @param name - Timer name
   * @returns Timer object with end() method
   */
  startTimer(name: string): Timer {
    return this.startMark(name);
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export class for testing or custom instances
export { PerformanceMonitor };

// Export types
export type {
  CustomMark,
  CustomTiming,
  APICall,
  PageLoadMetrics,
  ResourceMetric,
  MemoryUsage,
  PerformanceMetrics,
  Timer,
  PerformanceStats,
  PerformanceSummary,
};
