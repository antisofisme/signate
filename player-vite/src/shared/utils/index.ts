/**
 * Shared Utilities Barrel Export
 *
 * @description
 * Central export point for all utility functions and helpers.
 * Provides consistent import paths across the application.
 *
 * @usage
 * ```typescript
 * import { cn, performanceMonitor, detectPlatform } from '@/shared/utils';
 * ```
 */

// UI utilities
export { cn } from './cn';

// Performance monitoring
export {
  performanceMonitor,
  PerformanceMonitor,
  type CustomMark,
  type CustomTiming,
  type APICall,
  type PageLoadMetrics,
  type ResourceMetric,
  type MemoryUsage,
  type PerformanceMetrics,
  type Timer,
  type PerformanceStats,
  type PerformanceSummary,
} from './performance';

// Command reporting
export {
  reportCommandStatus,
  reportCommandRunning,
  reportCommandCompleted,
  reportCommandFailed,
  type CommandStatus,
} from './command-reporter';

// Device information
export {
  detectPlatform,
  getConnectionType,
  getConnectionSpeed,
  getConnectionRTT,
  getMemoryInfo,
  getStorageInfo,
  getDeviceInfo,
  type Platform,
} from './device-info';
