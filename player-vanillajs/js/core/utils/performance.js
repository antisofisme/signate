/**
 * Performance Monitoring Module
 *
 * @module PerformanceMonitor
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
 * ```javascript
 * // Track API call
 * PerformanceMonitor.startMark('api-fetch');
 * await fetch('/api/playlist');
 * PerformanceMonitor.endMark('api-fetch', 'API Call');
 *
 * // Get performance stats
 * const stats = PerformanceMonitor.getStats();
 * console.log('Page load time:', stats.pageLoad.total);
 *
 * // Monitor specific operation
 * const timer = PerformanceMonitor.startTimer('cache-sync');
 * await syncCacheWithPlaylist();
 * timer.end('Cache sync complete');
 * ```
 *
 * @version 1.0.0
 */

(function() {
  'use strict';

  /**
   * Performance Monitor class
   */
  class PerformanceMonitor {
    constructor() {
      /**
       * Custom marks registry
       * @type {Object.<string, {start: number, end?: number, duration?: number}>}
       */
      this.customMarks = {};

      /**
       * Performance metrics
       * @type {Object}
       */
      this.metrics = {
        pageLoad: {},
        apiCalls: [],
        resources: [],
        customTimings: []
      };

      // Start monitoring page load
      this.initPageLoadMonitoring();
    }

    /**
     * Initialize page load performance monitoring
     */
    initPageLoadMonitoring() {
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
            const lastEntry = entries[entries.length - 1];
            this.metrics.pageLoad.lcp = Math.round(lastEntry.renderTime || lastEntry.loadTime);
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
    recordPageLoadMetrics() {
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
        lcp: this.metrics.pageLoad.lcp || null
      };

      console.log('[Performance] Page load metrics recorded:', this.metrics.pageLoad);
    }

    /**
     * Get First Contentful Paint (FCP) timing
     * @returns {number|null}
     */
    getFirstContentfulPaint() {
      if (!performance || !performance.getEntriesByType) {
        return null;
      }

      const paintEntries = performance.getEntriesByType('paint');
      const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');

      return fcpEntry ? Math.round(fcpEntry.startTime) : null;
    }

    /**
     * Start performance mark
     * @param {string} name - Mark name
     * @returns {Object} Timer object with end() method
     */
    startMark(name) {
      const startTime = performance.now();

      this.customMarks[name] = {
        start: startTime
      };

      // Return timer object for convenience
      return {
        end: (label) => this.endMark(name, label)
      };
    }

    /**
     * End performance mark
     * @param {string} name - Mark name
     * @param {string} [label] - Optional label for logging
     * @returns {number} Duration in milliseconds
     */
    endMark(name, label) {
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
        timestamp: new Date().toISOString()
      });

      console.log(`[Performance] ${label || name}: ${duration}ms`);

      return duration;
    }

    /**
     * Measure time between two marks
     * @param {string} startMark - Start mark name
     * @param {string} endMark - End mark name
     * @param {string} measureName - Measurement name
     * @returns {number} Duration in milliseconds
     */
    measure(startMark, endMark, measureName) {
      if (!this.customMarks[startMark] || !this.customMarks[endMark]) {
        console.warn('[Performance] Marks not found for measurement');
        return 0;
      }

      const duration = this.customMarks[endMark].start - this.customMarks[startMark].start;

      this.metrics.customTimings.push({
        name: measureName,
        duration: Math.round(duration),
        timestamp: new Date().toISOString()
      });

      return Math.round(duration);
    }

    /**
     * Track API call performance
     * @param {string} url - API endpoint
     * @param {string} method - HTTP method
     * @param {number} duration - Call duration in ms
     * @param {number} status - HTTP status code
     */
    trackAPICall(url, method, duration, status) {
      this.metrics.apiCalls.push({
        url,
        method,
        duration: Math.round(duration),
        status,
        timestamp: new Date().toISOString()
      });

      // Keep only last 50 API calls to prevent memory growth
      if (this.metrics.apiCalls.length > 50) {
        this.metrics.apiCalls.shift();
      }
    }

    /**
     * Get resource loading metrics
     * @returns {Array} Resource timing entries
     */
    getResourceMetrics() {
      if (!performance || !performance.getEntriesByType) {
        return [];
      }

      const resources = performance.getEntriesByType('resource');

      return resources.map(resource => ({
        name: resource.name,
        type: resource.initiatorType,
        duration: Math.round(resource.duration),
        size: resource.transferSize || 0,
        cached: resource.transferSize === 0
      }));
    }

    /**
     * Get memory usage (if available)
     * @returns {Object|null}
     */
    getMemoryUsage() {
      if (!performance || !performance.memory) {
        return null;
      }

      return {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024), // MB
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024), // MB
        limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024) // MB
      };
    }

    /**
     * Get all performance statistics
     * @returns {Object}
     */
    getStats() {
      return {
        pageLoad: this.metrics.pageLoad,
        apiCalls: this.metrics.apiCalls,
        customTimings: this.metrics.customTimings,
        resources: this.getResourceMetrics(),
        memory: this.getMemoryUsage()
      };
    }

    /**
     * Get performance summary for reporting
     * @returns {Object}
     */
    getSummary() {
      const stats = this.getStats();

      const apiCallStats = this.metrics.apiCalls.length > 0 ? {
        count: this.metrics.apiCalls.length,
        avgDuration: Math.round(
          this.metrics.apiCalls.reduce((sum, call) => sum + call.duration, 0) /
          this.metrics.apiCalls.length
        ),
        slowest: Math.max(...this.metrics.apiCalls.map(call => call.duration))
      } : null;

      return {
        pageLoad: {
          total: stats.pageLoad.total || 0,
          domContentLoaded: stats.pageLoad.domContentLoaded || 0,
          fcp: stats.pageLoad.fcp || 0,
          lcp: stats.pageLoad.lcp || 0
        },
        apiCalls: apiCallStats,
        memory: stats.memory,
        resourceCount: stats.resources.length
      };
    }

    /**
     * Clear all metrics
     */
    clearMetrics() {
      this.customMarks = {};
      this.metrics = {
        pageLoad: this.metrics.pageLoad, // Keep page load metrics
        apiCalls: [],
        resources: [],
        customTimings: []
      };

      console.log('[Performance] Metrics cleared');
    }

    /**
     * Start a simple timer (convenience method)
     * @param {string} name - Timer name
     * @returns {Object} Timer object with end() method
     */
    startTimer(name) {
      return this.startMark(name);
    }
  }

  // Create singleton instance
  const performanceMonitor = new PerformanceMonitor();

  // Export for ES6 modules
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PerformanceMonitor: performanceMonitor };
  }

  // Expose to window (Vanilla JS pattern)
  window.PerformanceMonitor = performanceMonitor;

  console.log('[Performance] Performance monitor initialized');

})();
