/**
 * Performance Information Utilities
 * Get system performance metrics
 */

export interface PerformanceInfo {
  uptime: number; // milliseconds
  memory: {
    used: number; // MB
    total: number; // MB
    limit: number; // MB
  } | null;
  fps: number;
  loadTime: number; // milliseconds
}

// Track startup time
const startupTime = Date.now();

/**
 * Get player uptime in milliseconds
 */
export function getUptime(): number {
  return Date.now() - startupTime;
}

/**
 * Format uptime to human readable string
 */
export function formatUptime(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Get memory usage (if supported)
 */
export function getMemoryInfo(): { used: number; total: number; limit: number } | null {
  // @ts-ignore - performance.memory is non-standard
  const memory = performance.memory;

  if (!memory) {
    return null;
  }

  return {
    used: Math.round(memory.usedJSHeapSize / 1048576 * 100) / 100, // MB
    total: Math.round(memory.totalJSHeapSize / 1048576 * 100) / 100, // MB
    limit: Math.round(memory.jsHeapSizeLimit / 1048576 * 100) / 100 // MB
  };
}

/**
 * Get current FPS (simplified - tracks last second)
 */
let lastFrameTime = performance.now();
let frameCount = 0;
let currentFPS = 0; // Start at 0, will be calculated after first second
let fpsInitialized = false;

export function trackFPS(): void {
  const now = performance.now();
  frameCount++;

  if (now - lastFrameTime >= 1000) {
    currentFPS = Math.round(frameCount * 1000 / (now - lastFrameTime));
    frameCount = 0;
    lastFrameTime = now;
    fpsInitialized = true;
  }

  requestAnimationFrame(trackFPS);
}

export function isFPSInitialized(): boolean {
  return fpsInitialized;
}

export function getCurrentFPS(): number {
  return currentFPS;
}

/**
 * Get page load time
 */
export function getLoadTime(): number {
  const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

  if (!perfData) {
    return 0;
  }

  return Math.round(perfData.loadEventEnd - perfData.fetchStart);
}

/**
 * Get performance info
 */
export function getPerformanceInfo(): PerformanceInfo {
  return {
    uptime: getUptime(),
    memory: getMemoryInfo(),
    fps: getCurrentFPS(),
    loadTime: getLoadTime()
  };
}

/**
 * Check WebGL support
 */
export function hasWebGLSupport(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
}

/**
 * Check Service Worker support and status (async version)
 */
export async function getServiceWorkerStatusAsync(): Promise<string> {
  if (!('serviceWorker' in navigator)) {
    return 'Not supported';
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();

    if (!registration) {
      return 'Not registered';
    }

    if (registration.active) {
      return 'Active';
    } else if (registration.installing) {
      return 'Installing';
    } else if (registration.waiting) {
      return 'Waiting';
    }

    return 'Registered';
  } catch (error) {
    return 'Error';
  }
}

/**
 * Check Service Worker support and status (sync version - cached)
 */
let cachedSWStatus: string = 'Checking...';

export function getServiceWorkerStatus(): string {
  // Return cached value, update async in background
  if (cachedSWStatus === 'Checking...' && 'serviceWorker' in navigator) {
    getServiceWorkerStatusAsync().then(status => {
      cachedSWStatus = status;
    });
  }
  return cachedSWStatus;
}

// Initialize SW status on load
if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  getServiceWorkerStatusAsync().then(status => {
    cachedSWStatus = status;
  });
}

/**
 * Get battery status (if supported)
 */
export async function getBatteryInfo(): Promise<{ level: number; charging: boolean } | null> {
  try {
    // @ts-ignore - navigator.getBattery is experimental
    if (!navigator.getBattery) {
      return null;
    }

    // @ts-ignore
    const battery = await navigator.getBattery();

    return {
      level: Math.round(battery.level * 100),
      charging: battery.charging
    };
  } catch (error) {
    return null;
  }
}

// Start FPS tracking
if (typeof window !== 'undefined') {
  trackFPS();
}
